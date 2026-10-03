"""SQLite storage. One file, ~/.periodize-my-run/periodize.db (override with PERIODIZE_HOME)."""
import contextlib
import json
import os
import sqlite3

HOME = os.path.expanduser(os.environ.get("PERIODIZE_HOME", "~/.periodize-my-run"))
OLD_HOME = os.path.expanduser("~/.periodize")        # the folder's name before the app was renamed Periodize My Run


def _move_old_home():
    """Move the data folder from its old name, once, if this install has data there and nothing at the new name yet."""
    if "PERIODIZE_HOME" in os.environ or os.path.exists(HOME) or not os.path.isdir(OLD_HOME):
        return
    with contextlib.suppress(OSError):        # a sandboxed service cannot rename in the home folder; the installer does it instead
        os.rename(OLD_HOME, HOME)


_move_old_home()
SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS activities (
  id TEXT PRIMARY KEY, start TEXT, date TEXT, sport TEXT, name TEXT, dist_m REAL, timer_s REAL,
  avg_hr REAL, max_hr REAL, ascent_m REAL, best5k REAL, best10k REAL, detail TEXT);
CREATE INDEX IF NOT EXISTS activities_date ON activities(date);
CREATE TABLE IF NOT EXISTS daily (date TEXT PRIMARY KEY, rhr REAL, sleep_h REAL, hrv REAL, weight_kg REAL);
CREATE TABLE IF NOT EXISTS plan (
  date TEXT PRIMARY KEY, type TEXT, label TEXT, miles REAL, steps TEXT, strength TEXT, note TEXT,
  source TEXT DEFAULT 'auto', garmin_id TEXT, pushed_hash TEXT, adjust TEXT);
CREATE TABLE IF NOT EXISTS weeks (monday TEXT PRIMARY KEY, mode TEXT, target REAL, why TEXT, tp REAL, final INTEGER, summary TEXT);
CREATE TABLE IF NOT EXISTS races (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, date TEXT, miles REAL, priority TEXT, goal_time TEXT);
CREATE TABLE IF NOT EXISTS status (id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT, start TEXT, end TEXT, note TEXT);
CREATE TABLE IF NOT EXISTS moves (id INTEGER PRIMARY KEY AUTOINCREMENT, a TEXT, b TEXT);
CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT, started TEXT, finished TEXT, ok INTEGER, message TEXT);
"""

DEFAULTS = {
    "units": "km", "long_day": 6, "run_days": 6, "strength": True,
    "run_time": "06:30", "push_enabled": True, "push_days": 21, "easy_target": "none", "pace_window": 0.015,
    "hrmax": None, "weekly_increase": 0.06, "build_weeks_before_down": 3, "min_miles": 8, "blocked_days": [], "week_start": 0, "forecast_completion": None, "auto_backup": True, "aero_test": False, "aero_format": "original", "aero_test_weeks": 6, "aero_runs": False, "aero_lthr": None, "weeks_ahead": 3, "push_strength": True, "seed_threshold": None, "notify_url": "",
    "min_easy_run_miles": 3.5, "max_easy_run_miles": 10, "race_carbs_g_per_h": 60, "map_tiles": False, "heat_adjust": False, "update_check": True, "gel_carbs_g": 25, "sex": None, "birth_date": None,
    "threshold_hr_fraction": 0.89, "hilly_m_per_km": 12, "max_weekly_gain": 0.015, "max_weekly_loss": 0.005,
    "max_endurance_penalty": 0.05, "rhr_rise_bpm": 2, "hrv_drop_fraction": 0.90, "sleep_7night_min_h": 6.0,
    "easy_pace_drop_fraction": 0.03, "steps_week_ratio": 1.3, "steps_week_min_extra": 3000, "steps_day_ratio": 1.5, "steps_day_min_extra": 8000, "flags_to_back_off": 2, "detail_weeks": 26, "daily_adjust": True,
    "pause_min_s": 2.0, "pause_max_s": 6.0, "long_pause_chance": 0.08, "long_pause_min_s": 10.0, "long_pause_max_s": 25.0,
    "retries": 4, "error_wait_s": 15, "rate_limit_wait_s": 120,
}


SCHEMA_VERSION = 18
# Upgrades applied in order to an older database: {version reached: [SQL statements]}.
MIGRATIONS = {
    2: ["CREATE TABLE IF NOT EXISTS moves (id INTEGER PRIMARY KEY AUTOINCREMENT, a TEXT, b TEXT)"],
    3: ["ALTER TABLE plan ADD COLUMN strength_id TEXT", "ALTER TABLE plan ADD COLUMN strength_hash TEXT"],
    4: ["ALTER TABLE daily ADD COLUMN steps INTEGER", "ALTER TABLE activities ADD COLUMN steps INTEGER"],
    5: ["ALTER TABLE activities ADD COLUMN vo2max REAL",
        "CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, name TEXT, dist_m REAL, time_s REAL, "
        "source TEXT, activity_id TEXT UNIQUE, hidden INTEGER DEFAULT 0)"],
    6: ["ALTER TABLE status ADD COLUMN mode TEXT"],
    8: ["ALTER TABLE results ADD COLUMN note TEXT", "ALTER TABLE results ADD COLUMN weight_kg REAL", "ALTER TABLE results ADD COLUMN counts INTEGER DEFAULT 1"],
    9: ["ALTER TABLE activities ADD COLUMN gap_ratio REAL"],
    10: ["ALTER TABLE plan ADD COLUMN gcal_id TEXT", "ALTER TABLE plan ADD COLUMN gcal_hash TEXT"],
    12: ["ALTER TABLE daily ADD COLUMN sleep_score INTEGER"],
    13: ["ALTER TABLE activities ADD COLUMN training_effect REAL", "ALTER TABLE activities ADD COLUMN garmin_load REAL"],
    14: ["CREATE TABLE IF NOT EXISTS feel (date TEXT PRIMARY KEY, rpe INTEGER, sore INTEGER, note TEXT, source TEXT)",
         "CREATE TABLE IF NOT EXISTS shoes (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, start TEXT, start_miles REAL, alert_miles REAL, retired TEXT)"],
    15: ["ALTER TABLE races ADD COLUMN course TEXT", "ALTER TABLE races ADD COLUMN climb_m REAL"],
    16: ["ALTER TABLE hadd_tests RENAME TO aerobic_tests", "UPDATE OR REPLACE settings SET key='aero_' || substr(key, 6) WHERE key LIKE 'hadd\\_%' ESCAPE '\\'",
         "UPDATE plan SET label='Aerobic test' WHERE label='Hadd test'"],
    17: ["DELETE FROM settings WHERE key IN ('google','google_state','drive_backup','drive_last','drive_auth','drive_device_until','calendar_sync')",
         "UPDATE settings SET value=json_remove(value,'$.google','$.drive') WHERE key='vault' AND json_valid(value)",
         "ALTER TABLE plan DROP COLUMN gcal_id", "ALTER TABLE plan DROP COLUMN gcal_hash"],
    11: ["DROP TABLE IF EXISTS chat", "DROP TABLE IF EXISTS overrides", "DELETE FROM settings WHERE key IN ('anthropic_key','coach_model')"],
    18: ["ALTER TABLE daily ADD COLUMN sleep_start TEXT"],
    7: ["CREATE TABLE IF NOT EXISTS aerobic_tests (date TEXT PRIMARY KEY, stages TEXT, source TEXT, activity_id TEXT)"],
}
_ready = False


def _open():
    global _ready
    path = os.path.join(HOME, "periodize.db")
    if not _ready:
        os.makedirs(HOME, mode=0o700, exist_ok=True)
        os.chmod(HOME, 0o700)  # nosemgrep: insecure-file-permissions - owner-only on a directory is the strictest setting
    c = sqlite3.connect(path, timeout=30)
    c.row_factory = sqlite3.Row
    if not _ready:
        c.execute("PRAGMA journal_mode=WAL")
        c.executescript(SCHEMA)
        v = c.execute("PRAGMA user_version").fetchone()[0]
        for target in sorted(MIGRATIONS):
            if v < target:
                for sql in MIGRATIONS[target]:
                    try:
                        c.execute(sql)
                    except sqlite3.OperationalError as e:   # a fresh database already has the column
                        if not any(x in str(e) for x in ("duplicate column", "no such table", "already another table", "no such column")):
                            raise
        c.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
        c.commit()
        os.chmod(path, 0o600)   # health data: readable by this user only
        _ready = True
    return c


@contextlib.contextmanager
def connect():
    """A connection that commits on success, rolls back on error, and is always closed."""
    c = _open()
    try:
        yield c
        c.commit()
    except BaseException:
        c.rollback()
        raise
    finally:
        c.close()


def get(key, default=None):
    with connect() as c:
        r = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    if r is None:
        return DEFAULTS.get(key, default)
    return json.loads(r["value"])


def put(key, value):
    with connect() as c:
        c.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, json.dumps(value)))


def cfg():
    """All settings as one dict (defaults overlaid with stored values)."""
    out = dict(DEFAULTS)
    with connect() as c:
        for r in c.execute("SELECT key,value FROM settings"):
            out[r["key"]] = json.loads(r["value"])
    return out


def rows(sql, args=()):
    with connect() as c:
        return [dict(r) for r in c.execute(sql, args)]


def run(sql, args=()):
    with connect() as c:
        cur = c.execute(sql, args)
        return cur.lastrowid
