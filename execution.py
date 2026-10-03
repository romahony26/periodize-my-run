"""How closely each planned session was carried out: an execution score from 0 to 100.

The method comes from the training-load literature rather than from weights of the app's own:

  - Intensity is split into three zones at the two thresholds: below the first (easy), between them (moderate), above the second (hard).
  - Time in each zone is weighted 1, 2 and 3. That is Lucia's TRIMP (Lucia et al. 2003), a published and widely used measure of
    training load. It says a minute of hard running costs three times a minute of easy running.
  - The score is how far the session run departed from the session planned, zone by zone, in those weighted minutes, as a share
    of the planned load. Too much counts the same as too little, because the best-known finding on this subject (Foster et al.
    2001) is that athletes run their easy days harder than intended and their hard days easier, and both are departures.

      score = 100 x (1 - sum over zones of weight x |minutes run - minutes planned| / planned load), never below 0

What is still the app's own judgement: where the zone boundaries sit without a laboratory test (88% and 102% of threshold speed,
or 82% and 89% of maximum heart rate), and a tolerance of one minute per zone for GPS noise. The combined score is not itself a
validated instrument; it is a direct use of a validated load measure.
"""
import datetime as dt
import json

import assess
import db
import engine
import insights
from assess import MI, ZONES
from fitrun import BIN, HR_LO, HR_STEP

WEIGHTS = (1, 2, 3)                 # Lucia's TRIMP coefficients for zones 1, 2, 3
SPEED_CUTS = (0.88, 1.02)           # fractions of threshold speed: below = zone 1, above the second = zone 3
HR_CUTS = (0.82, 0.89)              # fractions of maximum heart rate
ZONE_OF = {"easy": 0, "steady": 0, "mp": 1, "hmp": 1, "threshold": 1, "10k": 2, "5k": 2}
NAMES = ("Easy (zone 1)", "Moderate (zone 2)", "Hard (zone 3)")
TOLERANCE_S = 60


def planned_zones(steps, tp, hrmax):
    """Seconds the session asks for in each zone, and whether it is prescribed by heart rate."""
    z, by_hr = [0.0, 0.0, 0.0], False
    mid = lambda name: tp * sum(ZONES[name]) / 2
    for st in steps or []:
        if st[0] == "d":
            name = st[2] or "threshold"                     # a race: counted at threshold effort
            z[ZONE_OF[name]] += st[1] * MI / mid(name)
        elif st[0] == "r":
            z[ZONE_OF[st[3]]] += st[1] * st[2]
            z[0] += st[1] * st[4]
        elif st[0] == "rd":
            z[ZONE_OF[st[3]]] += st[1] * st[2] / mid(st[3])
            z[0] += st[1] * st[4] / mid("easy")
        elif st[0] == "h":
            by_hr = True
            bpm = (st[2] + st[3]) / 2
            zone = 0 if bpm < HR_CUTS[0] * hrmax else 1 if bpm <= HR_CUTS[1] * hrmax else 2
            z[zone] += st[1] * MI / (tp * (0.80, 0.93, 1.05)[zone])
        elif st[0] == "max":
            z[2] += st[1] / (tp * 1.1)
        elif st[0] == "strides":
            z[0] += st[1] * 80                              # strides are too short to register as hard running
    return z, by_hr


def actual_zones(runs, tp, hrmax, by_hr):
    """Seconds actually run in each zone, from pace (or from heart rate when the session was prescribed by heart rate)."""
    z = [0.0, 0.0, 0.0]
    for r in runs:
        hs, ss = r.get("hr_sec"), r.get("sec_by_speed")
        indoor = (r.get("sub_sport") or "") in ("treadmill", "indoor_running")     # belt distance from a wrist is a guess, so pace is not trusted
        if (by_hr or indoor) and hs and len(hs) >= 20 and sum(hs) >= 300:
            for i, v in enumerate(hs):
                bpm = HR_LO + (i + 0.5) * HR_STEP
                z[0 if bpm < HR_CUTS[0] * hrmax else 1 if bpm <= HR_CUTS[1] * hrmax else 2] += v
        elif ss:
            for i, v in enumerate(ss):
                sp = (i + 0.5) * BIN
                if sp >= 1.5:                               # walking and standing are not running time
                    z[0 if sp < SPEED_CUTS[0] * tp else 1 if sp <= SPEED_CUTS[1] * tp else 2] += v
        else:
            z[0] += r.get("timer_s") or 0                    # no detail: all that is known is the duration
    return z


def load(z):
    """Lucia's TRIMP: minutes in each zone times 1, 2, 3."""
    return sum(w * s / 60 for w, s in zip(WEIGHTS, z, strict=True))


def score(p, runs, tp, L):
    """Execution score for one planned day. `runs` are that day's runs (from assess.load_runs)."""
    steps = json.loads(p["steps"]) if p["steps"] else None
    if not steps or p["type"] == "Rest" or not tp:
        return None
    plan, by_hr = planned_zones(steps, tp, L["hrmax"])
    if not runs:
        return {"score": 0, "verdict": "Missed", "planned_load": round(load(plan)), "load": 0,
                "parts": [{"name": n, "planned_min": round(plan[i] / 60), "min": 0, "weight": WEIGHTS[i]} for i, n in enumerate(NAMES) if plan[i] >= 30]}
    got = actual_zones(runs, tp, L["hrmax"], by_hr)
    diff = [max(abs(a - b) - TOLERANCE_S, 0) for a, b in zip(got, plan, strict=True)]
    dev = sum(w * x for w, x in zip(WEIGHTS, diff, strict=True)) / max(sum(w * x for w, x in zip(WEIGHTS, plan, strict=True)), 1)
    total = round(100 * max(0.0, 1 - dev))
    denom = max(sum(w * x for w, x in zip(WEIGHTS, plan, strict=True)), 1)
    lost = [round(100 * WEIGHTS[i] * diff[i] / denom) for i in range(3)]
    over, under = [got[i] - plan[i] > TOLERANCE_S for i in range(3)], [plan[i] - got[i] > TOLERANCE_S for i in range(3)]
    if not any(over) and not any(under):
        cause = "You ran it as planned."
    elif (over[2] and under[1]) or (over[1] and under[0] and plan[1] == 0 and plan[2] == 0 and not over[0]):
        cause = "The faster running was quicker than the planned pace range, so those minutes counted as harder than the session asked for." if plan[1] or plan[2] else \
            "Part of this easy run was faster than easy pace."
    elif (over[1] or over[2]) and plan[1] == 0 and plan[2] == 0:
        cause = "Part of this easy run was faster than easy pace."
    elif under[1] or under[2]:
        cause = "Less of the faster running was done than planned: the reps were shorter, fewer, or slower than the planned pace range."
    elif over[0]:
        cause = "The run was longer than planned."
    elif under[0]:
        cause = "The run was shorter than planned."
    else:
        cause = "More fast running was done than planned."
    worst = max(range(3), key=lambda i: WEIGHTS[i] * diff[i])
    note = ""
    if diff[worst] > 0:
        way = "more" if got[worst] > plan[worst] else "less"
        note = f"{abs(got[worst] - plan[worst]) / 60:.0f} min {way} {NAMES[worst].split(' (')[0].lower()} running than planned"
    return {"score": total, "verdict": "On target" if total >= 85 else "Close" if total >= 65 else "Off target", "note": note, "by": "heart rate" if by_hr else "pace",
            "planned_load": round(load(plan)), "load": round(load(got)), "cause": cause,
            "parts": [{"name": n, "planned_min": round(plan[i] / 60), "min": round(got[i] / 60), "weight": WEIGHTS[i], "lost": lost[i]} for i, n in enumerate(NAMES) if plan[i] >= 30 or got[i] >= 60]}


def run_detail(r, tp, hrmax, units):
    """Everything worth showing about one run."""
    z = actual_zones([r], tp, hrmax, False) if tp else [0, 0, 0]
    t = r.get("timer_s") or 0
    per = MI if units == "mi" else 1000
    return {"id": r["id"], "name": r.get("name") or "Run", "start_utc": r.get("start_utc"), "dist": engine.dist(round(r["dist_m"] / MI, 2), units) if units == "mi" else f"{r['dist_m'] / 1000:.2f} km",
            "time_s": round(t), "pace": engine.pace(r["dist_m"] / t, units) + "/" + units if t else "", "avg_hr": round(r["avg_hr"]) if r.get("avg_hr") else None,
            "max_hr": round(r.get("max_hr") or r.get("max_hr_sum") or 0) or None, "climb_m": r.get("climb_m") if r.get("gap_ok") else None,
            "flat_pace": engine.pace(r["dist_m"] * r["gap_ratio"] / t, units) + "/" + units if t and r.get("gap_ok") and r.get("gap_ratio") else None,
            "training_effect": r.get("training_effect"), "garmin_load": round(r["garmin_load"]) if r.get("garmin_load") else None,
            "load": round(load(z)), "zones_min": [round(x / 60) for x in z],
            "treadmill": insights.treadmill(r), "drift": None if insights.treadmill(r) else insights.drift(r.get("series")),
            "series": [[s[0], round(per / s[1]) if s[1] and s[1] > 1.2 else None, s[2]] for s in (r.get("series") or [])],     # [seconds, pace in s per unit, heart rate]
            "track": r.get("track") or [], "laps": [[round(x[0]), round(x[1]), x[2]] for x in (r.get("laps") or [])[:60]]}


def day(date, c, L):
    """One day in full: the plan, the score, and each run with its charts."""
    d = dt.date.fromisoformat(date)
    tp = (db.rows("SELECT tp FROM weeks WHERE monday=?", ((d - dt.timedelta(days=d.weekday())).isoformat(),)) or [{"tp": None}])[0]["tp"]
    tp = tp or (db.rows("SELECT tp FROM weeks ORDER BY ABS(julianday(monday)-julianday(?)) LIMIT 1", (date,)) or [{"tp": None}])[0]["tp"]
    runs = assess.load_runs(d, d + dt.timedelta(days=1))
    p = db.rows("SELECT * FROM plan WHERE date=?", (date,))
    out = {"date": date, "dow": engine.DAYS[d.weekday()], "plan": None, "score": None, "runs": [run_detail(r, tp, L["hrmax"], c["units"]) for r in runs], "units": c["units"]}
    if p:
        p = p[0]
        slow = (json.loads(p["adjust"]) if p["adjust"] else {}).get("slow", 0.0)
        pd = dict(p, steps=json.loads(p["steps"]) if p["steps"] else None)
        out["plan"] = {"type": p["type"], "label": p["label"], "dist": engine.dist(p["miles"], c["units"]) if p["miles"] else "", "eased": slow,
                       "text": engine.describe(pd, tp, c["units"], slow) if tp and pd["steps"] else "", "note": p["note"] or ""}
        out["score"] = score(p, runs, tp, L)
        if out["score"] and tp:
            u = c["units"]
            if out["score"].get("by") == "heart rate":
                a, b = round(HR_CUTS[0] * L["hrmax"]), round(HR_CUTS[1] * L["hrmax"])
                out["score"]["zones"] = [f"Easy: under {a} bpm", f"Moderate: {a} to {b} bpm", f"Hard: over {b} bpm"]
            else:
                a, b = engine.pace(SPEED_CUTS[0] * tp, u), engine.pace(SPEED_CUTS[1] * tp, u)
                out["score"]["zones"] = [f"Easy: slower than {a}/{u}", f"Moderate: {a} to {b}/{u}", f"Hard: faster than {b}/{u}"]
    return out


def history(c, L, weeks=12):
    """Every scored session in the last `weeks`, newest first, with weekly averages."""
    today = dt.date.today()
    start = today - dt.timedelta(weeks=weeks)
    tps = {r["monday"]: r["tp"] for r in db.rows("SELECT monday,tp FROM weeks")}
    runs = {}
    for r in assess.load_runs(start, today + dt.timedelta(days=1)):
        runs.setdefault(r["date"].isoformat(), []).append(r)
    out = []
    moved = db.get("reshuffled") or {}
    for p in db.rows("SELECT * FROM plan WHERE date>=? AND date<=? ORDER BY date DESC", (start.isoformat(), today.isoformat())):
        d = dt.date.fromisoformat(p["date"])
        tp = tps.get((d - dt.timedelta(days=d.weekday())).isoformat())
        rs = runs.get(p["date"], [])
        if d == today and not rs:
            continue                 # today counts as soon as its run is in; until then it is not a missed day
        s = score(p, rs, tp, L)
        pd = dict(p, steps=json.loads(p["steps"]) if p["steps"] else None)
        done = None
        if rs:
            m, t = sum(r["dist_m"] for r in rs), sum(r["timer_s"] or 0 for r in rs)
            done = {"dist": engine.dist(round(m / MI, 1), c["units"]), "pace": engine.pace(m / t, c["units"]) + "/" + c["units"] if t else "", "id": max(rs, key=lambda r: r["dist_m"])["id"]}
        to = moved.get(p["date"])
        if s and s["verdict"] == "Missed" and to:
            s = None                 # moved to a later day, where it will be scored
        if s is None and not rs and not to:
            continue
        slow = (json.loads(p["adjust"]) if p["adjust"] else {}).get("slow", 0.0)
        out.append({"date": p["date"], "dow": engine.DAYS[d.weekday()], "type": p["type"], "label": p["label"], "dist": engine.dist(p["miles"], c["units"]) if p["miles"] else "",
                    "short": engine.short(pd, c["units"]), "eased": slow, "done": done, "score": s, "unplanned": s is None and bool(rs), "moved_to": to if s is None else None})
    wk = {}
    for x in out:
        if x["score"]:
            d = dt.date.fromisoformat(x["date"])
            wk.setdefault((d - dt.timedelta(days=d.weekday())).isoformat(), []).append(x["score"]["score"])
    scored = [x["score"]["score"] for x in out if x["score"]]
    return {"sessions": out, "weeks": [{"week": k, "avg": round(sum(v) / len(v)), "n": len(v)} for k, v in sorted(wk.items())],
            "average": round(sum(scored) / len(scored)) if scored else None, "count": len(scored)}
