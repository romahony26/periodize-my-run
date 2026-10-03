"""EXPERIMENTAL: runs from a COROS account, through COROS's unofficial web interface (the one its Training Hub website uses).

Written without a COROS watch to test against and tested only with stand-in data, so it may not work at all, and COROS can change
or block this interface at any time. COROS offers no public interface for personal apps. What it does:

  - Sign in once with your COROS email and password. COROS expects the password as an MD5 hash; the hash is sent once and never
    stored. Only the access token COROS returns is kept, encrypted in the vault.
  - List your activities, download each new run as a .fit file, and read it the same way as any other FIT file.
  - Nothing is ever sent to your COROS account or watch.

The interface follows the open-source projects that read COROS data the same way; if COROS replies in a shape this code does not
recognise, it stops and logs the problem instead of guessing.
"""
import hashlib
import os
import tempfile

import requests

import db
import vault
from log import log

BASE = "https://teamapi.coros.com"
RUN_TYPES = {100, 101, 102, 103}       # outdoor run, indoor run, trail run, track run
TIMEOUT = 30


class Unrecognised(Exception):
    """COROS replied in a shape this code does not know."""


def connected():
    return bool((vault.get("coros") or {}).get("token"))


def _ok(r):
    try:
        j = r.json()
    except ValueError:
        raise Unrecognised(f"not JSON (HTTP {r.status_code})") from None
    if not isinstance(j, dict) or str(j.get("result")) != "0000":
        raise Unrecognised(f"result {str(j.get('result') if isinstance(j, dict) else '?')[:20]}: {str(j.get('message') if isinstance(j, dict) else '')[:80]}")
    return j.get("data") or {}


def login(email, password):
    """Sign in once; keep only the token."""
    if not email or not password:
        raise ValueError("Enter your COROS email and password.")
    h = hashlib.md5(usedforsecurity=False)       # COROS's own site sends this hash; it is a protocol detail, not protection, and is never stored
    h.update(password.encode())
    pwd = h.hexdigest()
    r = requests.post(f"{BASE}/account/login", json={"account": email, "accountType": 2, "pwd": pwd}, timeout=TIMEOUT)
    data = _ok(r)
    token = data.get("accessToken")
    if not token:
        raise Unrecognised("no access token in the reply")
    vault.put("coros", {"token": token, "user": str(data.get("userId") or "")})
    db.put("watch_source", "coros")
    log.info("COROS (experimental) connected; token stored encrypted")
    return "ok"


def disconnect():
    vault.put("coros", None)
    if db.get("watch_source") == "coros":
        db.put("watch_source", "garmin")
    log.info("COROS disconnected; token deleted")


def _head():
    t = (vault.get("coros") or {}).get("token")
    if not t:
        raise Unrecognised("not connected")
    return {"accesstoken": t}


def activities(page, size=50):
    r = requests.get(f"{BASE}/activity/query", params={"size": size, "pageNumber": page, "modeList": ""}, headers=_head(), timeout=TIMEOUT)
    data = _ok(r)
    items = data.get("dataList")
    if not isinstance(items, list):
        raise Unrecognised("no activity list in the reply")
    return items


def download(label_id, sport_type):
    r = requests.post(f"{BASE}/activity/detail/download", params={"labelId": label_id, "sportType": sport_type, "fileType": 4},
                      headers=_head(), timeout=TIMEOUT)
    url = _ok(r).get("fileUrl")
    if not url or not str(url).startswith("https://"):
        raise Unrecognised("no https file address in the reply")
    f = requests.get(url, timeout=120)
    if f.status_code != 200 or len(f.content) > 50 * 1024 * 1024:
        raise Unrecognised(f"file download failed (HTTP {f.status_code})")
    return f.content


def sync(full=False, progress=lambda m: None):
    """New runs from COROS. Stops at the first page with nothing new, unless `full`."""
    import watch
    new, page = 0, 1
    try:
        while page <= 200:
            items = activities(page)
            if not items:
                break
            fresh = 0
            for a in items:
                try:
                    label, st = str(a["labelId"]), int(a["sportType"])
                except (KeyError, TypeError, ValueError):
                    raise Unrecognised("an activity without labelId or sportType") from None
                if st not in RUN_TYPES or db.rows("SELECT 1 FROM activities WHERE id=?", ("coros-" + label,)):
                    continue
                raw = download(label, st)
                fd, tmp = tempfile.mkstemp(suffix=".fit")
                try:
                    with os.fdopen(fd, "wb") as fh:
                        fh.write(raw)
                    if watch.import_fit(tmp, "coros-" + label, str(a.get("name") or "COROS run")[:80]):
                        fresh += 1
                finally:
                    os.unlink(tmp)
            new += fresh
            progress(f"COROS: page {page}, {new} new runs")
            if not full and fresh == 0:
                break
            page += 1
    except Unrecognised as e:
        log.error("COROS (experimental) stopped: %s. Nothing was guessed; the runs already read are kept.", e)
    except requests.RequestException as e:
        log.error("COROS (experimental) could not be reached: %s", type(e).__name__)
    log.info("COROS (experimental): %d new runs", new)
    return new
