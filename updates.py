"""Updates from the app: see when a new version is out, install it, or go back to an earlier one.

  - Checking asks GitHub for the project's version tags (vX.Y.Z), once a day at a random time. Nothing about you is sent. While
    the project is private on GitHub, the answer is "not found" and nothing happens.
  - Installing downloads that version's source from GitHub over HTTPS and checks it before use: unpacked with the safe "data"
    filter (no file may land outside its folder or be a link out), the version in its CHANGELOG must be the one asked for, every
    Python file must compile, and its library list must be the same as the one installed (a version that needs new libraries is
    installed with the installer instead). It is kept as a folder in the data folder, because on a Raspberry Pi the service may
    write nowhere else, and the app restarts into it.
  - Going back switches to any version installed this way, or to the version the installer put in place. Nothing is deleted, and
    a backup is made before every switch. The database only ever gains columns, so an earlier version can still read it.

The installed copy stays where the installer put it; a small check when the app starts (`launch`) runs the chosen version instead.
"""
import datetime as dt
import io
import os
import py_compile
import re
import shutil
import sys
import tarfile
import tempfile
import threading
import time

import requests

import db
from log import log

REPO = "romahony26/periodize-my-run"
TAGS = f"https://api.github.com/repos/{REPO}/tags"
ARCHIVE = "https://codeload.github.com/" + REPO + "/tar.gz/refs/tags/v{v}"
HERE = os.path.dirname(os.path.abspath(__file__))
VERSIONS = os.path.join(db.HOME, "versions")
POINTER = os.path.join(VERSIONS, "current")
MAX_ARCHIVE = 30 * 1024 * 1024
VERSION_RE = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}(-beta\.\d{1,3})?$")      # 2.9.0 is a release; 2.9.1-beta.2 is a beta
FIRST_UPDATABLE = "2.4.0"      # earlier versions have no updater, so switching to one would leave no way back from the app


def vkey(v):
    """Sort key: 2.9.0-beta.1 < 2.9.0-beta.2 < 2.9.0 < 2.9.1-beta.1."""
    core, _, beta = v.partition("-beta.")
    return (*(int(x) for x in core.split(".")), 0 if beta else 1, int(beta or 0))


def is_beta(v):
    return "-beta." in v


def channel():
    """Which versions to offer: "stable" (releases only, the default) or "beta" (releases and betas)."""
    return "beta" if db.get("update_channel") == "beta" else "stable"


def running_version():
    with open(os.path.join(HERE, "CHANGELOG.md"), encoding="utf-8") as f:
        for line in f:
            if line.startswith("## "):
                return line[3:].split(" - ")[0].strip()
    return "0.0.0"


def base_version():
    """The version the installer put in place (the code beside the launcher)."""
    base = os.environ.get("PERIODIZE_BASE_DIR") or HERE
    with open(os.path.join(base, "CHANGELOG.md"), encoding="utf-8") as f:
        for line in f:
            if line.startswith("## "):
                return line[3:].split(" - ")[0].strip()
    return "0.0.0"


# ---------------------------------------------------------------- choosing the version to run, at start-up
def chosen_dir():
    """The folder of the version to run, or None for the installed one."""
    try:
        with open(POINTER, encoding="utf-8") as f:
            v = f.read().strip()
    except OSError:
        return None
    d = os.path.join(VERSIONS, v)
    return d if VERSION_RE.match(v) and os.path.isfile(os.path.join(d, "web.py")) else None


def launch(argv):
    """Called first thing by the installed web.py: if another version was chosen, run that instead. Never loops."""
    if os.environ.get("PERIODIZE_LAUNCHED"):
        return
    d = chosen_dir()
    if not d or os.path.realpath(d) == os.path.realpath(HERE):
        return
    os.environ["PERIODIZE_LAUNCHED"] = "1"
    os.environ["PERIODIZE_BASE_DIR"] = HERE
    os.execv(sys.executable, [sys.executable, os.path.join(d, "web.py"), *argv])   # noqa: S606  # nosec B606 - our own interpreter and file


def restart_soon(delay=1.5):
    """Restart in place after the reply has gone out: the new process reads the chosen version at start-up."""
    def go():
        time.sleep(delay)
        base = os.environ.get("PERIODIZE_BASE_DIR") or HERE
        env = {k: v for k, v in os.environ.items() if k not in ("PERIODIZE_LAUNCHED", "PERIODIZE_BASE_DIR")}
        log.info("Restarting into the chosen version")
        os.execve(sys.executable, [sys.executable, os.path.join(base, "web.py"), *sys.argv[1:]], env)   # noqa: S606  # nosec B606
    threading.Thread(target=go, daemon=True).start()


# ---------------------------------------------------------------- checking
def check():
    """Ask GitHub for the newest version. Saves and returns the update state."""
    st = dict(db.get("update_info") or {})
    st["checked"] = dt.datetime.now().isoformat(timespec="minutes")
    st["channel"] = ch = channel()
    try:
        r = requests.get(TAGS, params={"per_page": 50}, timeout=20, headers={"Accept": "application/vnd.github+json"}, allow_redirects=True)
        if r.status_code == 404:
            st.update({"status": "not public", "latest": None})
        elif r.status_code != 200 or not isinstance(r.json(), list):
            st.update({"status": f"GitHub answered {r.status_code}"})
        else:
            vs = sorted({t["name"][1:] for t in r.json() if isinstance(t, dict) and isinstance(t.get("name"), str)
                         and t["name"].startswith("v") and VERSION_RE.match(t["name"][1:]) and vkey(t["name"][1:]) >= vkey(FIRST_UPDATABLE)
                         and (ch == "beta" or not is_beta(t["name"][1:]))}, key=vkey)
            st.update({"status": "ok", "latest": vs[-1] if vs else None, "available": vs[-15:]})
    except (requests.RequestException, ValueError) as e:
        st.update({"status": f"could not reach GitHub ({type(e).__name__})"})
    db.put("update_info", st)
    log.info("Update check: %s%s", st["status"], f", newest {st['latest']}" if st.get("latest") else "")
    return st


def state():
    st = dict(db.get("update_info") or {})
    now = running_version()
    latest = st.get("latest") if st.get("channel", "stable") == channel() else None      # an answer for the other channel is not an answer
    newer = bool(latest and vkey(latest) > vkey(now))
    return {"running": now, "base": base_version(), "latest": latest, "channel": channel(), "beta": is_beta(now), "newer": newer, "status": st.get("status"), "checked": st.get("checked"),
            "dismissed": newer and db.get("update_dismissed") == latest, "installed": installed(), "available": st.get("available") or []}


def installed():
    try:
        return sorted((v for v in os.listdir(VERSIONS) if VERSION_RE.match(v) and os.path.isfile(os.path.join(VERSIONS, v, "web.py"))), key=vkey)
    except OSError:
        return []


# ---------------------------------------------------------------- installing and switching
def _fetch(v):
    r = requests.get(ARCHIVE.format(v=v), timeout=120, stream=True)
    if r.status_code != 200:
        raise ValueError(f"Version {v} could not be downloaded (GitHub answered {r.status_code}).")
    buf = io.BytesIO()
    for chunk in r.iter_content(1 << 16):
        buf.write(chunk)
        if buf.tell() > MAX_ARCHIVE:
            raise ValueError("The download is too large to be this app.")
    return buf.getvalue()


def _unpack(raw, dest):
    """Unpack safely: the data filter refuses absolute paths, '..', links out and device files."""
    try:
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as t:
            members = t.getmembers()
            tops = {m.name.split("/")[0] for m in members}
            if len(tops) != 1 or not tops.pop().strip("./"):
                raise ValueError("The download is not laid out as expected.")
            t.extractall(dest, filter="data")   # nosec B202 - the "data" filter blocks traversal, links out and special files
    except tarfile.TarError as e:
        raise ValueError(f"The download was refused as unsafe or damaged ({type(e).__name__}).") from None
    return os.path.join(dest, members[0].name.split("/")[0])


def _verify(src, v):
    if not os.path.isfile(os.path.join(src, "web.py")):
        raise ValueError("The download does not contain the app.")
    with open(os.path.join(src, "CHANGELOG.md"), encoding="utf-8") as f:
        first = next((ln for ln in f if ln.startswith("## ")), "")
    if first[3:].split(" - ")[0].strip() != v:
        raise ValueError(f"The download says it is not version {v}.")
    with open(os.path.join(src, "requirements.lock"), encoding="utf-8") as a, open(os.path.join(HERE, "requirements.lock"), encoding="utf-8") as b:
        if a.read() != b.read():
            raise ValueError(f"Version {v} needs different libraries, so it cannot be installed from the app. Update with the installer instead (see the README).")
    for root, _dirs, files in os.walk(src):
        for f in files:
            if f.endswith(".py"):
                py_compile.compile(os.path.join(root, f), doraise=True)


def install(v):
    """Download, check and keep version `v`, then choose it. The caller restarts the app."""
    if not isinstance(v, str) or not VERSION_RE.match(v):
        raise ValueError("Not a version number.")
    if vkey(v) < vkey(FIRST_UPDATABLE):
        raise ValueError(f"Versions before {FIRST_UPDATABLE} cannot be installed from the app.")
    import backup
    backup.make(dt.datetime.now().strftime("%H%M%S") + "-pre")
    os.makedirs(VERSIONS, mode=0o700, exist_ok=True)
    target = os.path.join(VERSIONS, v)
    if not os.path.isfile(os.path.join(target, "web.py")):
        with tempfile.TemporaryDirectory(dir=VERSIONS) as tmp:
            src = _unpack(_fetch(v), tmp)
            _verify(src, v)
            if os.path.exists(target):
                shutil.rmtree(target)
            shutil.move(src, target)
    choose(v)
    log.info("Version %s installed from GitHub and chosen", v)


def choose(v):
    """Run version `v` from the next start: one installed by the updater, or the installed (base) version."""
    import backup
    if v == base_version():
        if os.path.exists(POINTER):
            backup.make(dt.datetime.now().strftime("%H%M%S") + "-pre")
            os.remove(POINTER)
        log.info("Going back to the installed version %s", v)
        return
    if v not in installed():
        raise ValueError("That version is not installed.")
    backup.make(dt.datetime.now().strftime("%H%M%S") + "-pre")
    os.makedirs(VERSIONS, mode=0o700, exist_ok=True)
    tmp = POINTER + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(v)
    os.replace(tmp, POINTER)
    log.info("Version %s chosen", v)
