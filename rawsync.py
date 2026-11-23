"""Everything else Garmin keeps for each day, saved whole.

The sleep, HRV and resting heart rate the planner reads are three numbers out of much larger daily records: sleep stages, stress,
Body Battery, breathing, blood oxygen, Training Readiness, Training Status, VO2max and the all-day heart rate. This keeps each
record as Garmin sent it (compressed, in the garmin_raw table), so a later question can be answered from the data already held and
Garmin is not asked again.

  - It fills gaps only: a day and kind not yet held, or held from before the day ended (a day is not finished until the next morning).
    Today is never read: the ordinary sync already has it. With no gap it makes no request to Garmin at all.
  - It runs in its own background thread, started by the scheduler, never inside the sync job. It stops between requests the moment a
    sync starts and carries on when the sync is over, so it can never delay the plan, the watch, the message or a "sync now".
  - The newest days come first and it works backwards until 240 days in a row hold no sleep or daily record: that is where the
    account's wearable history begins. It survives a restart and never needs an answer from you.
  - A kind that Garmin refuses five times running (a watch that does not record it) is left out from then on. When Garmin limits the
    requests it rests for an hour.
  - Requests use the same human-paced, retrying call as every other Garmin read.
"""
import datetime as dt
import json
import time
import zlib

import db
import garmin
import recovery
from log import log

# (kind, client method). Each takes the day as "YYYY-MM-DD".
KINDS = (("stats", "get_stats"), ("sleep", "get_sleep_data"), ("hrv", "get_hrv_data"), ("rhr", "get_rhr_day"),
         ("stress", "get_stress_data"), ("respiration", "get_respiration_data"), ("spo2", "get_spo2_data"),
         ("heart_rates", "get_heart_rates"), ("readiness", "get_training_readiness"), ("status", "get_training_status"),
         ("max_metrics", "get_max_metrics"), ("intensity", "get_intensity_minutes_data"), ("floors", "get_floors"))
BATTERY_DAYS = 28            # Body Battery is read for a run of days in one request
EMPTY_STOP = 240             # days in a row with no sleep and no daily record: the start of the wearable history
FAILS_OFF = 5                # refusals in a row before a kind is left out
SLICE_S = 30 * 60            # how long one slice may run
REST_S = 3600                # how long it rests after Garmin limits the requests


def _pack(x):
    return zlib.compress(json.dumps(x, separators=(",", ":")).encode(), 6)


def unpack(blob):
    return json.loads(zlib.decompress(blob))


def _empty(x):
    if not x:
        return True
    if isinstance(x, dict):
        return all(v in (None, [], {}, "") for v in x.values())
    return False


def _real(kind, x):
    """Does a stats or sleep record hold a day the watch measured? For dates with no wearable data Garmin sends back an empty shell with
    the right keys and no values, which must not count as a day, or the walk back through history never reaches its start."""
    if not isinstance(x, dict):
        return False
    if kind == "stats":
        return bool((x.get("totalSteps") or 0) > 0 or x.get("restingHeartRate"))
    if kind == "sleep":
        return bool((x.get("dailySleepDTO") or {}).get("sleepTimeSeconds"))
    return True


def repair():
    """Once, on a database filled before this fix: take out the empty shells that were stored for every day back to 1943 (the walk back
    through history never stopped, and Garmin was asked for about 30,000 days), put sleep and HRV back among the kinds read (five failures on
    those impossible dates had switched them off, so nothing since 12 November was read), and record where the real history starts."""
    if db.get("raw_repaired") == 1:
        return
    first, shells = None, []
    with db.connect() as c:
        for r in c.execute("SELECT date,kind,body FROM garmin_raw WHERE kind IN ('stats','sleep') AND body IS NOT NULL ORDER BY date"):
            if _real(r["kind"], unpack(r["body"])):
                first = first or r["date"]
            else:
                shells.append((r["date"], r["kind"]))
        if first:
            c.execute("DELETE FROM garmin_raw WHERE date<?", (first,))
        c.executemany("UPDATE garmin_raw SET body=NULL WHERE date=? AND kind=?", [s for s in shells if s[0] >= (first or "")])
    state = db.get("raw_history") or {}
    state["off"] = [k for k in (state.get("off") or []) if k not in ("sleep", "hrv")]
    if first:
        state["first"], state["done"] = first, True
    db.put("raw_history", state)
    db.put("raw_repaired", 1)
    log.info("Garmin history repaired: real data starts %s, %d empty days dropped", first, len(shells))


def _held():
    """({(date, kind): when it was read}, {dates with a sleep or daily record that holds something})."""
    got, full = {}, set()
    for r in db.rows("SELECT date,kind,got,body IS NOT NULL AS has FROM garmin_raw"):
        got[(r["date"], r["kind"])] = r["got"]
        if r["has"] and r["kind"] in ("stats", "sleep"):
            full.add(r["date"])
    return got, full


def _final(held, day, kind):
    """Was this read after the day was over, so that nothing more will be added to it?"""
    g = held.get((day.isoformat(), kind))
    return bool(g) and g[:10] > day.isoformat()


def _kinds(off):
    return [k for k, _ in KINDS if k not in off] + ([] if "body_battery" in off else ["body_battery"])


def _store(rows):
    now = dt.datetime.now().isoformat(timespec="seconds")
    with db.connect() as c:
        for day, kind, x in rows:
            c.execute("INSERT OR REPLACE INTO garmin_raw(date,kind,body,got) VALUES(?,?,?,?)",
                      (day, kind, None if _empty(x) or not _real(kind, x) else _pack(x), now))
    return now


def _battery(g, start, end):
    """Body Battery for start..end in one request, as rows for every day in it."""
    have = {}
    for rec in garmin.call(f"body battery {start}", g.get_body_battery, start.isoformat(), end.isoformat()) or []:
        if rec.get("date"):
            have[rec["date"]] = rec
    days = [start + dt.timedelta(days=i) for i in range((end - start).days + 1)]
    return [(d.isoformat(), "body_battery", have.get(d.isoformat())) for d in days]


def paused(now=None):
    until = db.get("raw_pause_until")
    return bool(until) and (now or dt.datetime.now()) < dt.datetime.fromisoformat(until)


def has_gaps(today=None):
    """Is there anything to read? Cheap: it asks the database, not Garmin."""
    today = today or dt.date.today()
    state = db.get("raw_history") or {}
    if not state.get("done") or not state.get("first"):
        return True
    held, _ = _held()
    off, lo = set(state.get("off") or []), dt.date.fromisoformat(state["first"])
    day = today - dt.timedelta(days=1)
    while day >= lo:
        if any(not _final(held, day, k) for k in _kinds(off)):
            return True
        day -= dt.timedelta(days=1)
    return False


def run(budget_s=SLICE_S, today=None, stop=lambda: False):
    """One slice, newest day first, filling gaps only. `stop` is asked between requests. Returns (days read, finished)."""
    today = today or dt.date.today()
    repair()
    state = db.get("raw_history") or {}
    done = bool(state.get("done"))
    g = garmin.client()
    held, full = _held()
    off, fails, empty_run, n, t0 = set(state.get("off") or []), {}, 0, 0, time.monotonic()
    lo = dt.date.fromisoformat(state["first"]) if done and state.get("first") else None
    finished, day = done, today
    for i in range(1, 36500):
        day = today - dt.timedelta(days=i)
        if lo and day < lo:
            break
        if stop() or time.monotonic() - t0 > budget_s:
            finished = done
            break
        key = day.isoformat()
        rows = []
        try:
            for kind, method in KINDS:
                if kind in off or _final(held, day, kind):
                    continue
                if stop():
                    raise _Stop
                try:
                    rows.append((key, kind, garmin.call(f"{kind} {key}", getattr(g, method), key)))
                    fails[kind] = 0
                except garmin.GaveUp:
                    raise
                except Exception as e:
                    fails[kind] = fails.get(kind, 0) + 1
                    log.error("%s %s failed: %s", kind, key, type(e).__name__)
                    if fails[kind] >= FAILS_OFF:
                        off.add(kind)
                        log.warning("Garmin gives no %s for this account; leaving it out", kind)
            if "body_battery" not in off and not _final(held, day, "body_battery"):
                if stop():
                    raise _Stop
                try:
                    rows += _battery(g, day - dt.timedelta(days=BATTERY_DAYS - 1), day)
                except garmin.GaveUp:
                    raise
                except Exception as e:
                    log.error("body battery %s failed: %s", key, type(e).__name__)
        except _Stop:
            if rows:
                _store(rows)
            _save(off, held, day, done, full)
            return n, False
        except garmin.GaveUp:
            _store(rows)
            db.put("raw_pause_until", (dt.datetime.now() + dt.timedelta(seconds=REST_S)).isoformat(timespec="seconds"))
            _save(off, held, day, done, full)
            log.warning("Garmin history paused for an hour (rate limited)")
            return n, False
        if rows:
            now = _store(rows)
            n += 1
            for r in rows:
                held[(r[0], r[1])] = now
            if any(r[1] in ("stats", "sleep") and _real(r[1], r[2]) for r in rows):
                full.add(key)
        empty_run = 0 if key in full else empty_run + 1 if (key, "stats") in held else empty_run
        if not done and empty_run >= EMPTY_STOP:
            finished = True
            log.info("Garmin history complete: back to %s", min(full) if full else None)
            break
    _save(off, held, day, finished, full)
    return n, finished


class _Stop(Exception):
    pass


def _save(off, held, day, finished, full=None):
    full = full if full is not None else _held()[1]
    db.put("raw_history", {"off": sorted(off), "done": bool(finished), "first": min(full) if full else None,
                           "days": len({d for d, _ in held}), "reading": day.isoformat()})


def fill_daily(today=None):
    """Copy the sleep, resting heart rate, HRV and steps already held in garmin_raw into the daily table, for days it lacks them.
    It asks Garmin for nothing. The last three days are left to the ordinary sync, and a value already in daily is never replaced.
    Returns the number of days changed."""
    today = today or dt.date.today()
    cutoff = (today - dt.timedelta(days=3)).isoformat()
    mine = {"stats", "sleep", "hrv"}
    body = {}
    for r in db.rows("SELECT date,kind,body FROM garmin_raw WHERE body IS NOT NULL AND date<=?", (cutoff,)):
        if r["kind"] in mine:
            body[(r["date"], r["kind"])] = unpack(r["body"])
    have = {r["date"]: r for r in db.rows("SELECT * FROM daily")}
    n = 0
    with db.connect() as c:
        for day in sorted({d for d, _ in body}):
            stats, sleep, hrv = (body.get((day, k)) or {} for k in ("stats", "sleep", "hrv"))
            dto = sleep.get("dailySleepDTO") or {}
            secs, ms = dto.get("sleepTimeSeconds"), dto.get("sleepStartTimestampLocal")
            new = {"rhr": stats.get("restingHeartRate"),
                   "sleep_h": round(secs / 3600, 2) if secs else None,
                   "hrv": (hrv.get("hrvSummary") or {}).get("lastNightAvg"),
                   "sleep_score": ((dto.get("sleepScores") or {}).get("overall") or {}).get("value"),
                   "sleep_start": dt.datetime.fromtimestamp(ms / 1000, dt.UTC).strftime("%H:%M") if isinstance(ms, (int, float)) and ms > 0 else None,
                   "steps": stats.get("totalSteps")}
            old = have.get(day) or {}
            add = {k: v for k, v in new.items() if v is not None and old.get(k) is None}
            extra = {k: v for k, v in recovery.parse_night(sleep, stats).items() if v is not None and old.get(k) is None}
            if not add and not extra:
                continue
            c.execute("INSERT OR IGNORE INTO daily(date) VALUES(?)", (day,))
            if add:
                c.execute("UPDATE daily SET rhr=COALESCE(rhr,?), sleep_h=COALESCE(sleep_h,?), hrv=COALESCE(hrv,?), sleep_score=COALESCE(sleep_score,?), "
                          "sleep_start=COALESCE(sleep_start,?), steps=COALESCE(steps,?) WHERE date=?", (*new.values(), day))
            recovery.store(c, day, extra)
            n += 1
    if n:
        log.info("Daily records filled from the Garmin data already held: %d days", n)
    return n


def status():
    """What the Settings page says about it: None until it has started."""
    s = db.get("raw_history")
    if not s:
        return None
    return {"done": bool(s.get("done")), "back_to": s.get("first"), "days": s.get("days", 0), "reading": s.get("reading")}
