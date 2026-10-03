"""Copy a backup of a Periodize running on another computer (a Raspberry Pi, say) into a folder on this one, once a day.

Point it at a folder that a sync app uploads, such as Google Drive for desktop or iCloud Drive, and the backups reach the cloud
with no Google Cloud project and no sign-in inside Periodize: the sync app holds the login.

    python tools/pull_backup.py pi@raspberrypi.local                 # into Google Drive for desktop's "My Drive/Periodize backups"
    python tools/pull_backup.py pi@raspberrypi.local --to ~/Backups  # or any folder

Each copy is the same file as Download backup: the database with every login secret removed, plus the plan. Copies are thinned
like the app's own backups: daily for 7 days, weekly for 4 weeks, monthly for 3 months. Safe to run often: it replaces today's copy.
Needs key-based ssh to the other computer (no password prompt).
"""
import argparse
import datetime as dt
import glob
import os
import shlex
import subprocess  # nosec B404 - runs ssh with fixed arguments
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backup import NAME, keep  # noqa: E402

EXPORT = "import backup, sys; sys.stdout.buffer.write(backup.portable())"


def google_drive():
    """Google Drive for desktop's My Drive folder on a Mac, or None if it is not installed and signed in."""
    for d in sorted(glob.glob(os.path.expanduser("~/Library/CloudStorage/GoogleDrive-*"))):
        for name in os.listdir(d):
            if not name.startswith(".") and os.path.isdir(os.path.join(d, name)) and name not in ("Shared drives", ".shortcut-targets-by-id"):
                return os.path.join(d, name)
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("host", help="ssh destination, e.g. pi@raspberrypi.local")
    ap.add_argument("--to", help="folder to copy into (default: Google Drive for desktop, My Drive/Periodize backups)")
    ap.add_argument("--app", default="/opt/periodize", help="where Periodize is installed there")
    ap.add_argument("--user", default="dietpi", help="the user Periodize runs as there")
    a = ap.parse_args()
    to = os.path.expanduser(a.to) if a.to else None
    if not to:
        root = google_drive()
        if not root:
            print("Google Drive for desktop is not installed or not signed in yet; nothing copied.")
            return 0
        to = os.path.join(root, "Periodize backups")
    os.makedirs(to, exist_ok=True)
    cmd = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", a.host,
           f"cd {shlex.quote(a.app)} && sudo -u {shlex.quote(a.user)} -H {shlex.quote(a.app + '/.venv/bin/python')} -c {shlex.quote(EXPORT)}"]
    r = subprocess.run(cmd, capture_output=True, timeout=600)  # noqa: S603  # nosec B603 - fixed program, arguments quoted
    if r.returncode != 0 or not r.stdout:
        print("Could not fetch a backup:", r.stderr.decode(errors="replace").strip()[-300:])
        return 1
    name = f"periodize-{dt.date.today().isoformat()}.zip"
    tmp = os.path.join(to, "." + name + ".part")
    with open(tmp, "wb") as f:
        f.write(r.stdout)
    try:
        with zipfile.ZipFile(tmp) as z:
            if "periodize.db" not in z.namelist() or z.testzip() is not None:
                raise zipfile.BadZipFile("incomplete")
    except zipfile.BadZipFile:
        os.unlink(tmp)
        print("The backup arrived damaged; the previous copies are untouched.")
        return 1
    os.replace(tmp, os.path.join(to, name))
    names = [f for f in os.listdir(to) if NAME.match(f)]
    good = keep(names)
    for n in names:
        if n not in good:
            os.unlink(os.path.join(to, n))
    print(f"{dt.datetime.now():%Y-%m-%d %H:%M} copied {name} ({len(r.stdout) // 1024} KB) to {to}; {len(good)} kept")
    return 0


if __name__ == "__main__":
    sys.exit(main())
