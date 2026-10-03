"""Where runs and recovery data come from, and where workouts go: one place, so other watch brands can sit beside Garmin.

The rest of the app asks the active source four things: is it connected, fetch what is new, can it send workouts, and send them.
Three sources:

  - garmin: the full connection (runs, sleep, heart-rate variability, resting heart rate, steps, and workouts sent to the watch).
  - fitfolder: .fit files from a folder you choose (exports from COROS, Polar, Suunto, Wahoo or any watch, or a folder a sync app
    fills). Runs only: no sleep or heart-rate variability, and nothing is sent to the watch.
  - coros: runs from COROS through COROS's unofficial web interface. Checked against one real COROS account (Europe) and
    stand-in data, off unless chosen, and it sends nothing to the watch.
"""
import datetime as dt
import hashlib
import json
import os

import db
import fitrun
import garmin
from log import log

GaveUp = garmin.GaveUp
SOURCES = ("garmin", "fitfolder", "coros")
NAMES = {"garmin": "Garmin", "fitfolder": "FIT files from a folder", "coros": "COROS"}


def name():
    s = db.get("watch_source") or "garmin"
    return s if s in SOURCES else "garmin"


def connected():
    s = name()
    if s == "garmin":
        return garmin.has_tokens()
    if s == "fitfolder":
        f = db.get("fit_folder")
        return bool(f and os.path.isdir(f))
    import coros
    return coros.connected()


def can_push():
    """Only Garmin can receive workouts. Sending to COROS is not attempted: its workout format could not be checked without a watch."""
    return name() == "garmin" and garmin.has_tokens()


def has_recovery_data():
    return name() == "garmin"


def sync(kind, progress=lambda m: None, detail_weeks=26):
    """Fetch whatever is new from the active source. kind: setup | daily | readiness."""
    s = name()
    if s == "garmin":
        if kind in ("setup", "daily"):
            garmin.sync_summaries(full=(kind == "setup"), progress=progress)
        return
    if kind == "readiness":
        return                       # no recovery data from these sources
    if s == "fitfolder":
        import_folder(db.get("fit_folder"), progress)
    else:
        import coros
        coros.sync(full=(kind == "setup"), progress=progress)


def sync_rest(kind, c, progress=lambda m: None):
    """The Garmin-only extras after the run list: run detail, sleep and HRV, steps, VO2max, profile."""
    if name() != "garmin":
        return
    if kind in ("setup", "daily"):
        if not db.get("vo2max_backfilled") and kind == "daily":
            garmin.backfill_vo2max(progress)
        progress("Downloading recent runs")
        garmin.sync_details(c["detail_weeks"], progress)
        progress("Downloading sleep, HRV and heart rate")
        garmin.sync_daily(63 if kind == "setup" or db.rows("SELECT 1 FROM daily WHERE steps IS NOT NULL LIMIT 1") == [] else 10, progress)
        garmin.sync_extras()
        garmin.sync_activity_steps(63 if db.rows("SELECT 1 FROM activities WHERE steps IS NOT NULL LIMIT 1") == [] else 10)
    if kind == "readiness":
        garmin.sync_daily(2, progress)


def save():
    if name() == "garmin":
        garmin.save_tokens()


# ---------------------------------------------------------------- shared: one FIT file into the activity list
def import_fit(path, aid, name_=None):
    """Read one .fit file and add it as an activity, with its second-by-second detail. Returns True if it was new."""
    if db.rows("SELECT 1 FROM activities WHERE id=?", (aid,)):
        return False
    d = fitrun.parse(path)
    if d.get("error") or not d.get("start"):
        log.warning("FIT file %s could not be read (%s)", os.path.basename(path), (d.get("error") or "no start time")[:80])
        return False
    try:
        start = dt.datetime.fromisoformat(str(d["start"]))
    except ValueError:
        return False
    local = (start.astimezone() if start.tzinfo else start).date().isoformat()
    sport = "running" if "run" in str(d.get("sport") or "").lower() else str(d.get("sport") or "other").lower()
    best = d.get("best_dist") or {}
    with db.connect() as c:
        c.execute("INSERT OR IGNORE INTO activities(id,start,date,sport,name,dist_m,timer_s,avg_hr,max_hr,ascent_m,best5k,best10k,detail) "
                  "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  (aid, str(d["start"]), local, sport, name_ or ("Run" if sport == "running" else sport.title()), d.get("dist_m"), d.get("timer_s"),
                   d.get("avg_hr"), d.get("max_hr"), d.get("ascent_m"), best.get("5000"), best.get("10000"), json.dumps(d)))
    return True


def import_folder(folder, progress=lambda m: None):
    """Every .fit file in the folder (and its subfolders) not seen before. Files are identified by their content, so renaming
    or moving one does not import it twice."""
    if not folder or not os.path.isdir(folder):
        log.warning("FIT folder is not set or not found")
        return 0
    new, seen = 0, 0
    for root, _dirs, files in os.walk(folder):
        for f in sorted(files):
            if not f.lower().endswith(".fit"):
                continue
            path = os.path.join(root, f)
            try:
                if os.path.getsize(path) > 50 * 1024 * 1024:
                    continue
                with open(path, "rb") as fh:
                    aid = "fit-" + hashlib.sha256(fh.read()).hexdigest()[:20]
            except OSError:
                continue
            seen += 1
            if import_fit(path, aid, os.path.splitext(f)[0][:80]):
                new += 1
            if seen % 25 == 0:
                progress(f"FIT files: {seen} read, {new} new")
    log.info("FIT folder: %d files read, %d new activities", seen, new)
    return new
