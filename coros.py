"""Runs from a COROS account, through COROS's unofficial web interface (the one its Training Hub website uses).

Checked against one real COROS account (Europe: sign-in, the activity list, the .fit download, reading the file) and stand-in data;
COROS can change or block this interface at any time. COROS offers no public interface for personal apps. What it does:

  - Sign in once with your COROS email and password. COROS expects the password as an MD5 hash; the hash is sent once and never
    stored. Only the access token COROS returns is kept, encrypted in the vault.
  - List your activities, download each new run as a .fit file, and read it the same way as any other FIT file.
  - Nothing is ever sent to your COROS account or watch.

The interface follows the open-source projects that read COROS data the same way; if COROS replies in a shape this code does not
recognise, it stops and logs the problem instead of guessing.
"""
import datetime
import hashlib
import os
import tempfile

import requests

import db
import vault
from log import log

BASES = ["https://teameuapi.coros.com", "https://teamapi.coros.com", "https://teamcnapi.coros.com"]     # Europe, USA, China: a token only works on its own region's server
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
    """Sign in once; keep only the token and the regional server that accepted it."""
    if not email or not password:
        raise ValueError("Enter your COROS email and password.")
    h = hashlib.md5(usedforsecurity=False)       # COROS's own site sends this hash; it is a protocol detail, not protection, and is never stored
    h.update(password.encode())
    pwd = h.hexdigest()
    last = Unrecognised("no COROS server accepted the sign-in")
    for base in BASES:
        try:
            data = _ok(requests.post(f"{base}/account/login", json={"account": email, "accountType": 2, "pwd": pwd}, timeout=TIMEOUT))
            token = data.get("accessToken")
            if not token:
                raise Unrecognised("no access token in the reply")
            _ok(requests.get(f"{base}/activity/query", params=_query(1, 1), headers={"accesstoken": token}, timeout=TIMEOUT))     # does this region accept the token?
        except (Unrecognised, requests.RequestException) as e:
            last = e if isinstance(e, Unrecognised) else Unrecognised(type(e).__name__)
            continue
        vault.put("coros", {"token": token, "user": str(data.get("userId") or ""), "base": base})
        db.put("watch_source", "coros")
        log.info("COROS connected through %s; token stored encrypted", base.split("//")[1])
        return "ok"
    raise last


def disconnect():
    vault.put("coros", None)
    if db.get("watch_source") == "coros":
        db.put("watch_source", "garmin")
    log.info("COROS disconnected; token deleted")


def _base():
    return (vault.get("coros") or {}).get("base") or BASES[0]


def _head():
    t = (vault.get("coros") or {}).get("token")
    if not t:
        raise Unrecognised("not connected")
    return {"accesstoken": t}


def _query(page, size):
    # COROS wants a date range as well as the page
    return {"size": size, "pageNumber": page, "modeList": "", "startDay": "20100101", "endDay": datetime.date.today().strftime("%Y%m%d")}


def activities(page, size=50):
    r = requests.get(f"{_base()}/activity/query", params=_query(page, size), headers=_head(), timeout=TIMEOUT)
    data = _ok(r)
    items = data.get("dataList")
    if not isinstance(items, list):
        raise Unrecognised("no activity list in the reply")
    return items


def download(label_id, sport_type):
    r = requests.post(f"{_base()}/activity/detail/download", params={"labelId": label_id, "sportType": sport_type, "fileType": 4},
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
        log.error("COROS stopped: %s. Nothing was guessed; the runs already read are kept.", e)
    except requests.RequestException as e:
        log.error("COROS could not be reached: %s", type(e).__name__)
    log.info("COROS: %d new runs", new)
    return new
