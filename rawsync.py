"""Everything else Garmin keeps for each day, saved whole.

The sleep, HRV and resting heart rate the planner reads are three numbers out of much larger daily records: sleep stages, stress,
Body Battery, breathing, blood oxygen, Training Readiness, Training Status, VO2max and the all-day heart rate. This keeps each
record as Garmin sent it (compressed, in the garmin_raw table), so a later question can be answered from the data already held and
Garmin is not asked again.

  - The newest days come first and the run works backwards, in time-boxed slices after the daily sync, so it finishes by itself,
    survives a restart and never needs an answer from you. Days and kinds already held are skipped.
  - It stops once 240 days in a row hold no sleep or daily record: that is where the account's wearable history begins.
  - A kind that Garmin refuses five times running (a watch that does not record it) is left out from then on.
  - The last two days are read again each day, because a day is not finished until the next morning.
  - Requests use the same human-paced, retrying call as every other Garmin read.
"""
import datetime as dt
import json
import time
import zlib

import db
import garmin
from log import log

# (kind, client method). Each takes the day as "YYYY-MM-DD".
KINDS = (("stats", "get_stats"), ("sleep", "get_sleep_data"), ("hrv", "get_hrv_data"), ("rhr", "get_rhr_day"),
         ("stress", "get_stress_data"), ("respiration", "get_respiration_data"), ("spo2", "get_spo2_data"),
         ("heart_rates", "get_heart_rates"), ("readiness", "get_training_readiness"), ("status", "get_training_status"),
         ("max_metrics", "get_max_metrics"), ("intensity", "get_intensity_minutes_data"), ("floors", "get_floors"))
BATTERY_DAYS = 28            # Body Battery is read for a run of days in one request
EMPTY_STOP = 240             # days in a row with no sleep and no daily record: the start of the wearable history
FAILS_OFF = 5                # refusals in a row before a kind is left out
RECENT = 2                   # days that are read again, because they were not finished when last read
SLICE_S = 45 * 60            # how long one slice may run


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


def _held():
    """({(date, kind): date it was read}, {dates with a sleep or daily record that holds something})."""
    got, full = {}, set()
    for r in db.rows("SELECT date,kind,got,body IS NOT NULL AS has FROM garmin_raw"):
        got[(r["date"], r["kind"])] = r["got"]
        if r["has"] and r["kind"] in ("stats", "sleep"):
            full.add(r["date"])
    return got, full


def _store(rows):
    now = dt.datetime.now().isoformat(timespec="seconds")
    with db.connect() as c:
        for day, kind, x in rows:
            c.execute("INSERT OR REPLACE INTO garmin_raw(date,kind,body,got) VALUES(?,?,?,?)", (day, kind, None if _empty(x) else _pack(x), now))
    return now


def _battery(g, start, end):
    """Body Battery for start..end in one request, as rows for every day in it."""
    have = {}
    for rec in garmin.call(f"body battery {start}", g.get_body_battery, start.isoformat(), end.isoformat()) or []:
        if rec.get("date"):
            have[rec["date"]] = rec
    days = [start + dt.timedelta(days=i) for i in range((end - start).days + 1)]
    return [(d.isoformat(), "body_battery", have.get(d.isoformat())) for d in days]


def run(budget_s=SLICE_S, today=None):
    """One slice, newest day first. Returns (days read, finished)."""
    today = today or dt.date.today()
    state = db.get("raw_history") or {}
    done = bool(state.get("done"))
    g = garmin.client()
    held, full = _held()
    off, fails, empty_run, n, t0 = set(state.get("off") or []), {}, 0, 0, time.monotonic()
    finished, day = done, today
    for i in range(36500):
        day = today - dt.timedelta(days=i)
        if done and i > RECENT:
            break
        if time.monotonic() - t0 > budget_s:
            finished = False
            break
        key = day.isoformat()
        stale = i <= RECENT
        todo = [(k, m) for k, m in KINDS if k not in off and ((key, k) not in held or (stale and (held[(key, k)] or "")[:10] <= key))]
        rows = []
        try:
            for kind, method in todo:
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
            if "body_battery" not in off and (stale and i == 0 or ((key, "body_battery") not in held and day.toordinal() % BATTERY_DAYS == 0)):
                span = RECENT if i == 0 else BATTERY_DAYS - 1
                try:
                    rows += _battery(g, day - dt.timedelta(days=span), day)
                except garmin.GaveUp:
                    raise
                except Exception as e:
                    log.error("body battery %s failed: %s", key, type(e).__name__)
        except garmin.GaveUp:
            _store(rows)
            _save(off, held, day, False)
            log.warning("Garmin history paused (rate limited); it carries on at the next sync")
            return n, False
        if rows:
            now = _store(rows)
            n += 1
            for r in rows:
                held[(r[0], r[1])] = now
            if any(r[1] in ("stats", "sleep") and not _empty(r[2]) for r in rows):
                full.add(key)
        empty_run = 0 if key in full else empty_run + 1 if (key, "stats") in held else empty_run
        if not done and empty_run >= EMPTY_STOP:
            finished = True
            log.info("Garmin history complete: back to %s", min(full) if full else None)
            break
    _save(off, held, day, finished, full)
    return n, finished


def _save(off, held, day, finished, full=None):
    full = full if full is not None else _held()[1]
    db.put("raw_history", {"off": sorted(off), "done": bool(finished), "first": min(full) if full else None,
                           "days": len({d for d, _ in held}), "reading": day.isoformat()})


def status():
    """What the Settings page says about it: None until it has started."""
    s = db.get("raw_history")
    if not s:
        return None
    return {"done": bool(s.get("done")), "back_to": s.get("first"), "days": s.get("days", 0), "reading": s.get("reading")}
