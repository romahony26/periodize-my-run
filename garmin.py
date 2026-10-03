"""Garmin Connect: login, download history, download recent detail and health data.

Uses the unofficial `garminconnect` library. Requests are spaced at a human
pace, failures are retried with backoff, and everything is cached, so an
interrupted run resumes where it stopped. The password is used once to get
login tokens and is never stored or logged.
"""
import contextlib
import datetime as dt
import glob
import io
import json
import os
import random
import time
import zipfile

import db
import fitrun
import vault
from log import log

TOKENS = os.path.join(db.HOME, "tokens")
FIT_DIR = os.path.join(db.HOME, "fit")
_pending = {}     # login waiting for a two-step code
_session = {}


class GaveUp(Exception):
    """Garmin kept refusing; stop this run and try again later."""


def has_tokens():
    return vault.has("garmin_tokens")


def _migrate():
    """Move tokens from the old plain file into the vault, then delete the file."""
    for f in glob.glob(os.path.join(TOKENS, "*.json")):
        if not vault.has("garmin_tokens"):
            with open(f) as fh:
                vault.put("garmin_tokens", fh.read())
        os.remove(f)
    if os.path.isdir(TOKENS) and not os.listdir(TOKENS):
        os.rmdir(TOKENS)


def start_login(email, password):
    """Sign in to Garmin once. The password goes straight to Garmin, is exchanged for tokens, and is never stored or logged.

    Garmin offers no sign-in for personal apps that avoids typing the password (its official API is for approved companies only),
    so this is the closest equivalent: one exchange, then only revocable tokens, kept encrypted.
    Returns 'ok' or 'needs_mfa'.
    """
    from garminconnect import Garmin
    g = Garmin(email, password, return_on_mfa=True)
    status, state = g.login()
    if status == "needs_mfa":
        _pending["g"], _pending["state"] = g, state
        log.info("Garmin login: two-step code requested")
        return "needs_mfa"
    return _finish(g)


def finish_mfa(code):
    g = _pending.pop("g")
    g.resume_login(_pending.pop("state"), code)
    return _finish(g)


def _finish(g=None):
    if g is not None:
        vault.put("garmin_tokens", g.client.dumps())
        g.password = None
    _session.clear()
    g = client()
    db.put("garmin_name", g.get_full_name())
    with db.connect() as c:      # start in the units the athlete uses on Garmin, unless they have already chosen
        chosen = c.execute("SELECT 1 FROM settings WHERE key='units'").fetchone()
    if not chosen:
        db.put("units", "km" if str(getattr(g, "unit_system", "")).lower().startswith("metric") else "mi")
    log.info("Garmin login succeeded; tokens stored encrypted")
    return "ok"


def disconnect():
    vault.put("garmin_tokens", None)
    _session.clear()
    db.put("garmin_name", None)
    log.info("Garmin disconnected; tokens deleted")


def save_tokens():
    """Garmin refreshes tokens as they are used; keep the stored copy current."""
    g = _session.get("g")
    if g is not None:
        with contextlib.suppress(Exception):
            vault.put("garmin_tokens", g.client.dumps())


def client():
    if "g" not in _session:
        from garminconnect import Garmin
        _migrate()
        tokens = vault.get("garmin_tokens")
        if not tokens:
            raise RuntimeError("Garmin is not connected.")
        g = Garmin()
        g.login(tokens)          # the library accepts the token data itself, so nothing is written to disk
        _session["g"] = g
        if not db.get("garmin_name"):
            with contextlib.suppress(Exception):   # the name is only for display
                db.put("garmin_name", g.get_full_name())
        log.info("Garmin session ready (stored tokens)")
    return _session["g"]


def call(what, fn, *args, **kw):
    """One Garmin request with human-paced spacing, retries and backoff."""
    c = db.cfg()
    for attempt in range(1, c["retries"] + 1):
        t = random.uniform(c["pause_min_s"], c["pause_max_s"])   # noqa: S311 - timing jitter, not security
        if random.random() < c["long_pause_chance"]:   # noqa: S311
            t += random.uniform(c["long_pause_min_s"], c["long_pause_max_s"])   # noqa: S311
        time.sleep(t)
        try:
            out = fn(*args, **kw)
            log.debug("ok: %s", what)
            return out
        except Exception as e:
            name = type(e).__name__
            limited = "TooManyRequests" in name or "429" in str(e)
            if "Authentication" in name:
                _session.clear()
                log.error("%s: Garmin rejected the stored login (%s). Log in again.", what, name)
                raise
            if attempt == c["retries"]:
                log.error("%s: failed after %d attempts (%s)", what, attempt, name)
                if limited:
                    raise GaveUp(f"rate limited on: {what}") from e
                raise
            wait = (c["rate_limit_wait_s"] if limited else c["error_wait_s"]) * 2 ** (attempt - 1) * random.uniform(0.8, 1.3)   # noqa: S311
            log.warning("%s: %s on attempt %d; waiting %.0f s", what, "rate limited" if limited else name, attempt, wait)
            time.sleep(wait)
    return None


def sync_extras():
    """Small things read once a day: the watch's threshold estimate, and sex and date of birth for age grading (unless already set)."""
    g = client()
    with contextlib.suppress(Exception):
        lt = (call("threshold estimate", g.get_lactate_threshold) or {}).get("speed_and_heart_rate") or {}
        v = lt.get("speed")
        if v:
            v = v * 10 if v < 1.5 else v          # Garmin reports this speed in tenths
            if 2.0 < v < 7.0:
                db.put("garmin_lt", {"speed": v, "hr": lt.get("heartRate"), "date": (lt.get("calendarDate") or "")[:10]})
    c = db.cfg()
    if not c.get("sex") or not c.get("birth_date"):
        with contextlib.suppress(Exception):
            u = (call("profile", g.get_user_profile) or {}).get("userData") or {}
            sex = {"MALE": "M", "FEMALE": "F"}.get(str(u.get("gender") or "").upper())
            if sex and not c.get("sex"):
                db.put("sex", sex)
            if u.get("birthDate") and not c.get("birth_date"):
                db.put("birth_date", u["birthDate"][:10])


def _sport(a):
    key = ((a.get("activityType") or {}).get("typeKey") or "").lower()
    return "running" if "run" in key else key   # running, trail_running, treadmill_running, ultra_run, virtual_run ...


def _gap(a):
    """Garmin's grade-adjusted speed over actual speed, when Garmin gives it (recent activities only)."""
    g, v = a.get("avgGradeAdjustedSpeed"), a.get("averageSpeed")
    return round(g / v, 4) if g and v and 0.9 < g / v < 1.4 else None


def sync_summaries(full=False, progress=lambda m: None):
    """Activity list for all time (full) or until a page of already-known activities is reached."""
    g, start, new = client(), 0, 0
    known = {r["id"] for r in db.rows("SELECT id FROM activities")}
    while True:
        page = call(f"list activities {start}-{start + 99}", g.get_activities, start, 100) or []
        if not page:
            break
        fresh = 0
        with db.connect() as c:
            for a in page:
                aid = str(a.get("activityId"))
                if aid in known:
                    continue
                local = (a.get("startTimeLocal") or "")[:10]
                c.execute("INSERT OR IGNORE INTO activities(id,start,date,sport,name,dist_m,timer_s,avg_hr,max_hr,ascent_m,best5k,best10k,steps,vo2max,gap_ratio,training_effect,garmin_load) "
                          "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                          (aid, a.get("startTimeGMT"), local, _sport(a), a.get("activityName"), a.get("distance"),
                           a.get("movingDuration") or a.get("duration"), a.get("averageHR"), a.get("maxHR"), a.get("elevationGain"),
                           a.get("fastestSplit_5000"), a.get("fastestSplit_10000"), a.get("steps"), a.get("vO2MaxValue"), _gap(a), a.get("aerobicTrainingEffect"), a.get("activityTrainingLoad")))
                fresh += 1
        new += fresh
        start += len(page)
        progress(f"Activity history: {start} read, {new} new")
        if len(page) < 100 or (not full and fresh == 0):
            break
    log.info("Activity list synced: %d new", new)
    return new


def sync_activity_steps(days):
    """Step counts of recent activities, so steps taken outside runs can be worked out. One request."""
    today = dt.date.today()
    acts = call("activity steps", client().get_activities_by_date, (today - dt.timedelta(days=days)).isoformat(), today.isoformat()) or []
    with db.connect() as c:
        for a in acts:
            c.execute("UPDATE activities SET steps=COALESCE(?,steps), vo2max=COALESCE(?,vo2max), gap_ratio=COALESCE(?,gap_ratio), "
                      "training_effect=COALESCE(?,training_effect), garmin_load=COALESCE(?,garmin_load) WHERE id=?",
                      (a.get("steps"), a.get("vO2MaxValue"), _gap(a), a.get("aerobicTrainingEffect"), a.get("activityTrainingLoad"), str(a.get("activityId"))))


def backfill_vo2max(progress=lambda m: None):
    """One-off: Garmin's VO2max estimate for every past activity (about one request per 100 activities)."""
    g, start = client(), 0
    while True:
        page = call(f"activity history {start}", g.get_activities, start, 100) or []
        with db.connect() as c:
            for a in page:
                if a.get("vO2MaxValue"):
                    c.execute("UPDATE activities SET vo2max=? WHERE id=?", (a["vO2MaxValue"], str(a.get("activityId"))))
        start += len(page)
        progress(f"VO2max history: {start} activities read")
        if len(page) < 100:
            break
    db.put("vo2max_backfilled", True)


def sync_details(weeks, progress=lambda m: None):
    """Second-by-second detail (FIT files) for runs in the last `weeks` weeks that do not have it yet."""
    g = client()
    os.makedirs(FIT_DIR, exist_ok=True)
    since = (dt.date.today() - dt.timedelta(weeks=weeks)).isoformat()
    todo = db.rows("SELECT id,date FROM activities WHERE sport='running' AND date>=? AND detail IS NULL ORDER BY date DESC", (since,))
    for i, r in enumerate(todo, 1):
        path = os.path.join(FIT_DIR, r["id"] + ".fit")
        try:
            if not os.path.exists(path):
                raw = call(f"download activity {r['id']}", g.download_activity, r["id"], dl_fmt=g.ActivityDownloadFormat.ORIGINAL)
                with zipfile.ZipFile(io.BytesIO(raw)) as z:
                    names = [n for n in z.namelist() if n.lower().endswith(".fit")]
                    if not names:
                        db.run("UPDATE activities SET detail=? WHERE id=?", (json.dumps({"error": "no FIT file"}), r["id"]))
                        continue
                    with open(path, "wb") as f:
                        f.write(z.read(names[0]))
            d = fitrun.parse(path)
            db.run("UPDATE activities SET detail=? WHERE id=?", (json.dumps(d), r["id"]))
            log.info("Activity %s (%s): detail stored%s", r["id"], r["date"], f", parse error {d['error']}" if d.get("error") else "")
        except GaveUp:
            raise
        except Exception as e:
            log.error("Activity %s failed: %s", r["id"], type(e).__name__)
        progress(f"Run detail: {i} of {len(todo)}")
    return len(todo)


def sync_daily(days, progress=lambda m: None):
    """Resting heart rate, sleep, overnight HRV and weight. Days already stored are skipped, except the last three."""
    g, today = client(), dt.date.today()
    have = {r["date"] for r in db.rows("SELECT date FROM daily")}
    dates = [today - dt.timedelta(days=i) for i in range(days, -1, -1)]
    no_steps = {r["date"] for r in db.rows("SELECT date FROM daily WHERE steps IS NULL")}
    no_score = {r["date"] for r in db.rows("SELECT date FROM daily WHERE sleep_score IS NULL AND sleep_h IS NOT NULL")}
    no_start = {r["date"] for r in db.rows("SELECT date FROM daily WHERE sleep_start IS NULL AND sleep_h IS NOT NULL")}
    todo = [d for d in dates if d.isoformat() not in have or d.isoformat() in no_steps or d.isoformat() in no_score or d.isoformat() in no_start or (today - d).days <= 2]
    stats, scores, starts = {}, {}, {}

    def get_sleep(day):
        x = g.get_sleep_data(day) or {}
        scores[day] = (((x.get("dailySleepDTO") or {}).get("sleepScores") or {}).get("overall") or {}).get("value")
        ms = (x.get("dailySleepDTO") or {}).get("sleepStartTimestampLocal")       # local wall-clock time, stored as if it were GMT
        starts[day] = dt.datetime.fromtimestamp(ms / 1000, dt.UTC).strftime("%H:%M") if isinstance(ms, (int, float)) and ms > 0 else ""    # "" = asked, none given: not asked again
        return x


    def get_stats(day):
        stats[day] = g.get_stats(day) or {}
        return stats[day]

    picks = (("rhr", "stats", get_stats, lambda x: (x or {}).get("restingHeartRate")),
             ("sleep_h", "sleep", get_sleep,
              lambda x: (lambda s: round(s / 3600, 2) if s else None)(((x or {}).get("dailySleepDTO") or {}).get("sleepTimeSeconds"))),
             ("hrv", "hrv", g.get_hrv_data, lambda x: ((x or {}).get("hrvSummary") or {}).get("lastNightAvg")))
    for i, d in enumerate(todo, 1):
        key, row = d.isoformat(), {}
        old = key in have and (today - d).days > 2        # backfill of an older day: fetch only what is missing
        wanted = [p for p in picks if not old or (p[0] == "rhr" and key in no_steps) or (p[0] == "sleep_h" and (key in no_score or key in no_start))]
        for field, what, fn, pick in wanted:
            try:
                row[field] = pick(call(f"{what} {key}", fn, key))
            except GaveUp:
                raise
            except Exception as e:
                log.error("%s %s failed: %s", what, key, type(e).__name__)
        with db.connect() as c:
            c.execute("INSERT INTO daily(date,rhr,sleep_h,hrv) VALUES(?,?,?,?) ON CONFLICT(date) DO UPDATE SET "
                      "rhr=COALESCE(excluded.rhr,rhr), sleep_h=COALESCE(excluded.sleep_h,sleep_h), hrv=COALESCE(excluded.hrv,hrv)",
                      (key, row.get("rhr"), row.get("sleep_h"), row.get("hrv")))
            if scores.get(key) is not None:
                c.execute("UPDATE daily SET sleep_score=? WHERE date=?", (scores[key], key))
            if starts.get(key) is not None:
                c.execute("UPDATE daily SET sleep_start=? WHERE date=?", (starts[key], key))
            if (stats.get(key) or {}).get("totalSteps") is not None:
                c.execute("UPDATE daily SET steps=? WHERE date=?", (stats[key]["totalSteps"], key))
        progress(f"Health data: {i} of {len(todo)} days")
    try:
        body = call("weight", g.get_body_composition, dates[0].isoformat(), today.isoformat())
        with db.connect() as c:
            for w in (body or {}).get("dateWeightList") or []:
                if w.get("calendarDate") and w.get("weight"):
                    c.execute("INSERT INTO daily(date,weight_kg) VALUES(?,?) ON CONFLICT(date) DO UPDATE SET weight_kg=excluded.weight_kg",
                              (w["calendarDate"], round(w["weight"] / 1000, 2)))
    except GaveUp:
        raise
    except Exception as e:
        log.error("weight failed: %s", type(e).__name__)
    log.info("Health data synced: %d days fetched", len(todo))
    return len(todo)
