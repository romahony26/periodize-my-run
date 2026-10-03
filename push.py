"""Keep the Garmin Connect calendar in step with the plan, so the watch always has the coming days.

Each planned run becomes a structured workout scheduled on its date. A day is
only re-sent when its content changes (a replan, a moved session, or today's
pace adjustment). Only workouts this app created are ever deleted.
"""
import datetime as dt
import hashlib
import json

import db
import engine
import garmin
from assess import MI, ZONES
from log import log

RUNNING = {"sportTypeId": 1, "sportTypeKey": "running", "displayOrder": 1}
STEP = {"warmup": 1, "cooldown": 2, "interval": 3, "recovery": 4}
NO_TARGET = {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target", "displayOrder": 1}
PACE = {"workoutTargetTypeId": 6, "workoutTargetTypeKey": "pace.zone", "displayOrder": 6}
HEART = {"workoutTargetTypeId": 4, "workoutTargetTypeKey": "heart.rate.zone", "displayOrder": 4}


def _target(zone, tp, c, slow):
    if zone is None or (zone in ("easy", "steady") and c["easy_target"] != "pace"):
        return None
    lo, hi = engine.zone_speeds(tp, zone, slow)
    if lo == hi:
        lo, hi = lo * (1 - c["pace_window"]), hi * (1 + c["pace_window"])
    return lo, hi


def _step(order, kind, cond, value, target):
    cid = 2 if cond == "time" else 3
    s = {"type": "ExecutableStepDTO", "stepOrder": order, "stepType": {"stepTypeId": STEP[kind], "stepTypeKey": kind, "displayOrder": STEP[kind]},
         "endCondition": {"conditionTypeId": cid, "conditionTypeKey": cond, "displayOrder": cid, "displayable": True},
         "endConditionValue": round(float(value), 1), "targetType": PACE if target else NO_TARGET}
    if target:
        s["targetValueOne"], s["targetValueTwo"] = round(target[0], 3), round(target[1], 3)
    return s


def _repeat(order, n, children):
    return {"type": "RepeatGroupDTO", "stepOrder": order, "stepType": {"stepTypeId": 6, "stepTypeKey": "repeat", "displayOrder": 6},
            "numberOfIterations": n, "smartRepeat": False, "endConditionValue": float(n), "workoutSteps": children,
            "endCondition": {"conditionTypeId": 7, "conditionTypeKey": "iterations", "displayOrder": 7, "displayable": False}}


def workout(day, tp, c, slow=0.0):
    """Garmin workout JSON for one planned day, or None for a rest day."""
    src = day.get("steps")
    if not src:
        return None
    steps, order, secs = [], 0, 0.0
    easy_v = tp * sum(ZONES["easy"]) / 2
    for i, st in enumerate(src):
        order += 1
        if st[0] == "d":
            _, miles, zone = st
            edge = len(src) > 1 and zone == "easy"
            kind = ("warmup" if i == 0 else "cooldown" if i == len(src) - 1 else "recovery") if edge else "interval"
            steps.append(_step(order, kind, "distance", miles * MI, _target(zone, tp, c, slow)))
            secs += miles * MI / (tp * sum(ZONES[zone]) / 2 if zone else easy_v)
        elif st[0] == "r":
            _, n, work, zone, rec = st
            steps.append(_repeat(order, n, [_step(order + 1, "interval", "time", work, _target(zone, tp, c, slow)),
                                            _step(order + 2, "recovery", "time", rec, None)]))
            order += 2
            secs += n * (work + rec)
        elif st[0] == "strides":
            steps.append(_repeat(order, st[1], [_step(order + 1, "interval", "time", 20, None), _step(order + 2, "recovery", "time", 60, None)]))
            order += 2
            secs += st[1] * 80
        elif st[0] == "h":
            s = _step(order, "interval", "distance", st[1] * MI, None)
            s["targetType"], s["targetValueOne"], s["targetValueTwo"] = HEART, float(st[2]), float(st[3])
            steps.append(s)
            secs += st[1] * MI / (tp * 0.86)
        elif st[0] == "max":
            steps.append(_step(order, "interval", "distance", st[1], None))
            secs += st[1] / (tp * 1.12)
        elif st[0] == "rest":
            s = _step(order, "recovery", "time", st[1], None)
            s["stepType"] = {"stepTypeId": 5, "stepTypeKey": "rest", "displayOrder": 5}
            steps.append(s)
            secs += st[1]
        elif st[0] == "rd":
            _, n, work_m, zone, rec_m = st
            steps.append(_repeat(order, n, [_step(order + 1, "interval", "distance", work_m, _target(zone, tp, c, slow)),
                                            _step(order + 2, "recovery", "distance", rec_m, None)]))
            order += 2
            secs += n * (work_m / (tp * ZONES[zone][0]) + rec_m / easy_v)
    text = engine.describe(day, tp, c["units"], slow)
    if slow:
        text = f"Paces eased {slow:.1%} today for recovery. " + text
    if day.get("note"):
        text += " " + day["note"]
    return {"workoutName": f"PZ {day['label']} {engine.dist(day['miles'], c['units'])}"[:60], "description": text[:1000], "sportType": RUNNING,
            "estimatedDurationInSecs": int(secs), "workoutSegments": [{"segmentOrder": 1, "sportType": RUNNING, "workoutSteps": steps}]}


STRENGTH_SPORT = {"sportTypeId": 5, "sportTypeKey": "strength_training", "displayOrder": 5}
STRENGTH = {
    "Strength A": "Squat or leg press; single-leg deadlift; calf raises (straight and bent knee); side plank. 3 sets of 5-8 controlled reps, well short of failure.",
    "Strength B": "Split squat or step-up; hip thrust; hamstring curl or bridge walk-outs, 3 sets of 5-8 controlled reps, well short of failure. Then plyometrics: "
                  "pogo hops 3 x 20, skipping for height 3 x 20 m, bounding 3 x 20 m, quick and light, full recovery between.",
}


def strength_workout(name):
    if name not in STRENGTH:
        return None
    step = {"type": "ExecutableStepDTO", "stepOrder": 1, "stepType": {"stepTypeId": 3, "stepTypeKey": "interval", "displayOrder": 3},
            "endCondition": {"conditionTypeId": 1, "conditionTypeKey": "lap.button", "displayOrder": 1, "displayable": True},
            "targetType": NO_TARGET, "description": STRENGTH[name][:200]}
    return {"workoutName": f"PZ {name}", "description": STRENGTH[name], "sportType": STRENGTH_SPORT, "estimatedDurationInSecs": 1500,
            "workoutSegments": [{"segmentOrder": 1, "sportType": STRENGTH_SPORT, "workoutSteps": [step]}]}


def _upsert(date, w, old_id, old_hash, id_col, hash_col, dry_run, counts):
    """Make one calendar entry match `w` (None = nothing should be there). counts = [sent, removed, same]."""
    h = hashlib.sha256(json.dumps(w, sort_keys=True).encode()).hexdigest() if w else None
    if h == old_hash and (old_id or not w):
        counts[2] += 1
        return
    if dry_run:
        counts[0] += bool(w)
        return
    g = garmin.client()
    if old_id:
        try:
            garmin.call(f"delete workout {old_id}", g.delete_workout, old_id)
            counts[1] += 1
        except garmin.GaveUp:
            raise
        except Exception as e:
            log.warning("Could not delete workout %s (%s); continuing", old_id, type(e).__name__)
        db.run(f"UPDATE plan SET {id_col}=NULL, {hash_col}=NULL WHERE date=?", (date,))  # nosec B608
    if not w:
        return
    try:
        wid = (garmin.call(f"upload {w['workoutName']}", g.upload_workout, w) or {}).get("workoutId")
        if not wid:
            raise RuntimeError("no workoutId returned")
        db.run(f"UPDATE plan SET {id_col}=? WHERE date=?", (str(wid), date))   # recorded before scheduling so it is never orphaned  # nosec B608
        garmin.call(f"schedule {wid} on {date}", g.schedule_workout, wid, date)
        db.run(f"UPDATE plan SET {hash_col}=? WHERE date=?", (h, date))  # nosec B608
        counts[0] += 1
        log.info("Scheduled on %s: %s", date, w["workoutName"])
    except garmin.GaveUp:
        raise
    except Exception as e:
        log.error("%s: sending workout failed: %s", date, type(e).__name__)


def on_calendar(start, end):
    """{(date, workoutId)} of every workout on the Garmin calendar from start to end, or None if Garmin could not be read."""
    g, out = garmin.client(), set()
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        cal = garmin.call(f"read calendar {y}-{m:02d}", g.get_scheduled_workouts, y, m)
        if not isinstance(cal, dict) or not isinstance(cal.get("calendarItems"), list):
            return None
        for it in cal["calendarItems"]:
            if not isinstance(it, dict):
                return None
            if it.get("itemType") != "workout":
                continue
            if it.get("workoutId") is None or not it.get("date"):
                return None     # a shape we do not recognise: better to trust our records than resend everything
            out.add((str(it["date"])[:10], str(it["workoutId"])))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def _drop_missing(rows, start, end):
    """Forget the record of any workout that is no longer on the Garmin calendar (deleted in Garmin Connect, or never landed),
    so it is sent again. If the calendar cannot be read, nothing is forgotten."""
    if not any(r["garmin_id"] or r["strength_id"] for r in rows):
        return rows
    try:
        there = on_calendar(start, end)
    except garmin.GaveUp:
        raise
    except Exception as e:
        log.warning("Could not read the Garmin calendar to check it (%s); sending changes only", type(e).__name__)
        return rows
    if there is None:
        log.warning("The Garmin calendar came back in an unexpected shape; sending changes only")
        return rows
    out, missing = [], 0
    for r in rows:
        r = dict(r)
        for id_col, hash_col in (("garmin_id", "pushed_hash"), ("strength_id", "strength_hash")):
            if r[id_col] and (r["date"], str(r[id_col])) not in there:
                missing += 1
                r[hash_col] = None      # different from any real hash, so _upsert replaces it
        out.append(r)
    if missing:
        log.info("Garmin calendar check: %d workout(s) missing, sending again", missing)
    return out


def sync_calendar(c, dry_run=False):
    """Make Garmin match the plan for the next `push_days` days. Returns (sent, removed, unchanged)."""
    today = dt.date.today()
    end = today + dt.timedelta(days=int(c["push_days"]) - 1)
    rows = db.rows("SELECT * FROM plan WHERE date>=? AND date<=? ORDER BY date", (today.isoformat(), end.isoformat()))
    tps = {r["monday"]: r["tp"] for r in db.rows("SELECT monday,tp FROM weeks")}
    counts = [0, 0, 0]
    if not dry_run:
        rows = _drop_missing(rows, today, end)
    for r in rows:
        d = dt.date.fromisoformat(r["date"])
        tp = tps.get((d - dt.timedelta(days=d.weekday())).isoformat())
        adj = json.loads(r["adjust"]) if r["adjust"] else {}
        day = engine.as_run(dict(r, steps=json.loads(r["steps"]) if r["steps"] else None), adj)
        slow = adj.get("slow", 0.0)
        _upsert(r["date"], workout(day, tp, c, slow) if tp else None, r["garmin_id"], r["pushed_hash"], "garmin_id", "pushed_hash", dry_run, counts)
        sw = strength_workout(r["strength"]) if c["strength"] and c["push_strength"] else None
        _upsert(r["date"], sw, r["strength_id"], r["strength_hash"], "strength_id", "strength_hash", dry_run, counts)
    log.info("Garmin calendar%s: %d sent, %d replaced or removed, %d unchanged", " (preview)" if dry_run else "", *counts)
    return tuple(counts)
