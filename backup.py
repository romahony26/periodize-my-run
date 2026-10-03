"""Backups: nightly on this computer, thinned out as they age.

Retention is the standard "grandfather-father-son" scheme:
  - every day for the last 7 days,
  - the last backup of each of the last 4 weeks,
  - the last backup of each of the last 3 months.
Anything older or in between is deleted. No separate weekly or monthly job is needed: a daily backup is simply kept longer
when it is the last of its week or month.

The other half of good practice is a copy somewhere else (the "3-2-1" rule: three copies, two kinds of storage, one off-site).
For that, Download backup gives a copy with every login secret removed, and tools/pull_backup.py fetches one each day from
another computer into a folder a sync app uploads (Google Drive for desktop, iCloud Drive and the like).
"""
import datetime as dt
import io
import json
import os
import re
import sqlite3
import tempfile
import zipfile

import db
from log import log

DIR = os.path.join(db.HOME, "backups")
DAILY, WEEKLY, MONTHLY = 7, 4, 3
NAME = re.compile(r"^(?:periodize|config|plan|data)-(\d{4}-\d{2}-\d{2})(-\d{6}(-pre)?)?\.(db|zip|json)$")
SECRETS = ("app_password", "secret_key", "notify_url", "allowed_hosts", "vault", "always_login", "sessions")   # never copied into a backup, never overwritten by a restore


def keep(names, today=None):
    """Which backups to keep, from their names. Pure function: the same rule is used here and by tools/pull_backup.py."""
    today = today or dt.date.today()
    by_day = {}
    def when(n):              # date, then time made; the nightly has no time in its name and counts as the start of its day
        m = NAME.match(n)
        return (m.group(1), (m.group(2) or "-000000")[1:7]) if m else ("", "")
    for n in sorted(names, key=when):
        m = NAME.match(n)
        if m and not m.group(3):                               # a restore's safety copy never takes the day's place
            by_day[dt.date.fromisoformat(m.group(1))] = n      # the latest backup of each day
    days = sorted(by_day, reverse=True)
    kept = set(days[:DAILY])
    weeks, months = {}, {}
    for d in days:                                             # newest first, so the first seen is the last of its week or month
        weeks.setdefault(d.isocalendar()[:2], d)
        months.setdefault((d.year, d.month), d)
    kept |= set(list(weeks.values())[:WEEKLY]) | set(list(months.values())[:MONTHLY])
    out = {by_day[d] for d in kept}
    # everything from today (the nightly, any made by hand, a restore's safety copy) is kept until tomorrow's thinning, so a
    # backup you have just made, or are about to restore from, is never removed from under you
    out |= {n for n in names if NAME.match(n) and NAME.match(n).group(1) == today.isoformat()}
    return out


def prune():
    names = [f for f in os.listdir(DIR) if NAME.match(f)] if os.path.isdir(DIR) else []
    good = keep(names)
    gone = [n for n in names if n not in good]
    for n in gone:
        os.unlink(os.path.join(DIR, n))
    if gone:
        log.info("Backups thinned: %d removed, %d kept", len(gone), len(good))
    return gone


def make(tag=""):
    os.makedirs(DIR, mode=0o700, exist_ok=True)
    name = f"periodize-{dt.date.today().isoformat()}{'-' + tag if tag else ''}.db"
    path = os.path.join(DIR, name)
    dst = sqlite3.connect(path)
    try:
        with db.connect() as src:
            src.backup(dst)
        dst.execute("PRAGMA journal_mode=DELETE")
        dst.commit()
    finally:
        dst.close()
    os.chmod(path, 0o600)
    prune()
    log.info("Backup made: %s", name)
    return name


def nightly():
    """Make today's backup if there is not one yet. Safe to call often."""
    today = dt.date.today().isoformat()
    if any(NAME.match(f) and NAME.match(f).group(1) == today and "-pre" not in f for f in (os.listdir(DIR) if os.path.isdir(DIR) else [])):
        return None
    return make()


def portable():
    """A zip of the database with every login secret removed, plus the plan as JSON. For downloading and for off-site copies."""
    fd, tmp = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        dst = sqlite3.connect(tmp)
        try:
            with db.connect() as src:
                src.backup(dst)
            dst.execute("PRAGMA journal_mode=DELETE")     # one plain file, so the removals below are really in it
            dst.execute(f"DELETE FROM settings WHERE key IN ({','.join('?' * len(SECRETS))})", SECRETS)  # nosec B608
            dst.commit()
            dst.execute("VACUUM")
        finally:
            dst.close()
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(tmp, "periodize.db")
            z.writestr("plan.json", json.dumps(db.rows("SELECT date,type,label,miles,steps,strength,note,source FROM plan ORDER BY date"), indent=1))
            z.writestr("README.txt", "Periodize My Run backup. To restore: stop the app, copy periodize.db into ~/.periodize-my-run/, start the app and connect Garmin again.\n"
                                     "Garmin login tokens and the app password are not included.\n")
    finally:
        os.unlink(tmp)
    return buf.getvalue()


# ---------------------------------------------------------------- parts of a backup, for partial restores
INTERNAL = ("profile", "model", "readiness", "forecast_log", "altitude_trust", "notified", "drive_last", "setup_done", "garmin_name", "vo2max_backfilled", "aero_peak_hr", "jitter_seed", "readiness_log", "terms_accepted")


def _tables(con, names):
    con.row_factory = sqlite3.Row
    return {t: [dict(r) for r in con.execute(f"SELECT * FROM {t}")] for t in names}  # nosec B608 - fixed table names


def config(con=None):
    """Settings (no secrets, nothing the app recalculates), races, sick/injured/holiday periods, entered results and Aerobic tests."""
    own = con is None
    con = con or db._open()
    try:
        con.row_factory = sqlite3.Row
        settings = dict(db.DEFAULTS)      # every setting as it stood, including those left at their default
        settings.update({r["key"]: json.loads(r["value"]) for r in con.execute("SELECT key,value FROM settings") if r["key"] not in SECRETS + INTERNAL})
        out = _tables(con, ("races", "status", "aerobic_tests"))
        out["results"] = [dict(r) for r in con.execute("SELECT * FROM results WHERE source IN ('log','entered') OR hidden=1")]
        return {"kind": "periodize-config", "version": db.SCHEMA_VERSION, "made": dt.datetime.now().isoformat(timespec="seconds"), "settings": settings, **out}
    finally:
        if own:
            con.close()


def plan(con=None):
    """The planned days and weeks, and the athlete's own moves."""
    own = con is None
    con = con or db._open()
    try:
        out = _tables(con, ("plan", "weeks", "moves"))
        for p in out["plan"]:
            for k in ("garmin_id", "pushed_hash", "strength_id", "strength_hash"):   # tied to one device's sync state
                p.pop(k, None)
        return {"kind": "periodize-plan", "version": db.SCHEMA_VERSION, "made": dt.datetime.now().isoformat(timespec="seconds"), **out}
    finally:
        if own:
            con.close()


def _insert(con, table, rows):
    cols = {r[1] for r in con.execute(f"PRAGMA table_info({table})")}  # nosec B608 - fixed table names
    for r in rows:
        keys = [k for k in r if k in cols]
        con.execute(f"INSERT OR REPLACE INTO {table}({','.join(keys)}) VALUES({','.join('?' * len(keys))})", [r[k] for k in keys])  # nosec B608


def restore_config(data):
    """Put back settings, races, status periods, entered results and Aerobic tests. Training data, the plan and connections are untouched."""
    if not isinstance(data, dict) or data.get("kind") != "periodize-config" or not isinstance(data.get("settings"), dict):
        raise ValueError("That is not a Periodize My Run settings backup.")
    allowed = set(db.DEFAULTS) | {"hrmax", "peak_miles_override"}
    with db.connect() as con:
        for k, v in data["settings"].items():
            if k in allowed and k not in SECRETS:        # only known settings: a backup cannot introduce anything else
                con.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k, json.dumps(v)))
        for t in ("races", "status", "aerobic_tests"):
            con.execute(f"DELETE FROM {t}")  # nosec B608
            _insert(con, t, [r for r in data.get(t, []) if isinstance(r, dict)])
        con.execute("DELETE FROM results WHERE source IN ('log','entered')")
        _insert(con, "results", [r for r in data.get("results", []) if isinstance(r, dict)])
    log.info("Settings and races restored from a backup made %s", data.get("made"))


def restore_plan(data):
    """Put back the planned days from today on, the weeks and the athlete's moves. Past days and everything else are untouched."""
    if not isinstance(data, dict) or data.get("kind") != "periodize-plan" or not isinstance(data.get("plan"), list):
        raise ValueError("That is not a Periodize My Run plan backup.")
    today = dt.date.today().isoformat()
    with db.connect() as con:
        con.execute("DELETE FROM plan WHERE date>=? AND garmin_id IS NULL AND strength_id IS NULL", (today,))
        for p in data["plan"]:
            if isinstance(p, dict) and str(p.get("date", "")) >= today:
                keep_ids = con.execute("SELECT garmin_id,pushed_hash,strength_id,strength_hash FROM plan WHERE date=?", (p["date"],)).fetchone()
                _insert(con, "plan", [p])
                if keep_ids:      # keep this computer's sync state so the watch is updated, not duplicated
                    con.execute("UPDATE plan SET garmin_id=?,pushed_hash=NULL,strength_id=?,strength_hash=NULL WHERE date=?",
                                (keep_ids[0], keep_ids[2], p["date"]))
        _insert(con, "weeks", [w for w in data.get("weeks", []) if isinstance(w, dict)])
        con.execute("DELETE FROM moves")
        _insert(con, "moves", [m for m in data.get("moves", []) if isinstance(m, dict) and str(m.get("a", "")) >= today])
    log.info("Plan restored from a backup made %s", data.get("made"))


def _open_backup(path):
    try:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("That backup is damaged.")
        need = {"settings", "activities", "plan", "races"}
        if not need <= {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}:
            raise ValueError("That file is not a Periodize My Run backup.")
        return con
    except sqlite3.DatabaseError:
        raise ValueError("That backup is damaged.") from None


def restore_from(path, what="full"):
    """Restore from a database backup file. what: full | config | plan. The state just before is saved first, so it can be undone."""
    if what not in ("full", "config", "plan"):
        raise ValueError("Choose what to restore.")
    src = _open_backup(path)
    try:
        make(dt.datetime.now().strftime("%H%M%S") + "-pre")
        if what == "config":
            restore_config(config(src))
        elif what == "plan":
            restore_plan(plan(src))
        else:
            with db.connect() as live:      # connections and this computer's own secrets survive a full restore
                mine = {r["key"]: r["value"] for r in live.execute("SELECT key,value FROM settings") if r["key"] in SECRETS}
                src.backup(live)
                for k, v in mine.items():
                    live.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k, v))
    finally:
        src.close()
    db._ready = False        # re-run upgrades in case the backup is from an older version
    with db.connect():
        pass
    log.info("Restored (%s) from %s", what, os.path.basename(path))


def restore(name, what="full"):
    """Restore from a backup on this computer."""
    if not NAME.match(name or "") or not name.endswith(".db") or not os.path.exists(os.path.join(DIR, name)):
        raise ValueError("No such backup.")
    restore_from(os.path.join(DIR, name), what)
    return name


def listing():
    if not os.path.isdir(DIR):
        return []
    out = []
    for f in sorted((f for f in os.listdir(DIR) if NAME.match(f)), reverse=True):
        p = os.path.join(DIR, f)
        out.append({"name": f, "size_kb": round(os.path.getsize(p) / 1024), "made": dt.datetime.fromtimestamp(os.path.getmtime(p)).isoformat(timespec="minutes")})
    return out
