"""Evidence that the aerobic training is working: a faster pace at the same heart rate.

Three views of the same thing, all from the athlete's own runs:
  - Aerobic test results: pace over 2400 m at each fixed heart rate, test by test.
  - Pace at each heart rate month by month, from ordinary runs, so progress shows between tests too.
  - The relationship between race paces as distance doubles (a long-standing coaching rule of thumb).
"""
import datetime as dt
import json

import assess
import db
import engine

MI = 1609.344
DOUBLING_GOOD, DOUBLING_LOOSE = 16, 20      # seconds per mile slower each time the distance doubles (a coaching rule of thumb)


def read_tests():
    """Find completed Aerobic tests: on a day the plan had one, take the run's 2400 m laps in order."""
    hrmax = None
    for p in db.rows("SELECT date FROM plan WHERE label='Aerobic test' AND date<=? AND date NOT IN (SELECT date FROM aerobic_tests)", (dt.date.today().isoformat(),)):
        for a in db.rows("SELECT id, detail FROM activities WHERE sport='running' AND date=? AND detail IS NOT NULL", (p["date"],)):
            d = json.loads(a["detail"])
            laps = [x for x in (d.get("laps") or []) if (2300 <= x[0] <= 2500 or 1560 <= x[0] <= 1660) and x[2]]
            laps = laps[1:] if len(laps) >= 2 and laps[0][2] < laps[1][2] - 12 else laps      # drop a warm-up mile well below the first stage
            if len(laps) >= 3:
                if d.get("max_hr"):
                    db.put("aero_peak_hr", {"date": p["date"], "bpm": d["max_hr"]})
                stages = [{"hr": round(x[2]), "s_per_mi": round(x[1] / x[0] * MI)} for x in laps]
                db.run("INSERT OR REPLACE INTO aerobic_tests(date,stages,source,activity_id) VALUES(?,?,?,?)", (p["date"], json.dumps(stages), "watch", a["id"]))
                hrmax = True
    return bool(hrmax)


def tests(units="mi"):
    out = []
    k = 1.0 if units == "mi" else 1 / 1.609344
    for r in db.rows("SELECT * FROM aerobic_tests ORDER BY date"):
        out.append({"date": r["date"], "source": r["source"], "stages": [{"hr": s["hr"], "pace": _fmt(s["s_per_mi"] * k), "s": s["s_per_mi"] * k} for s in json.loads(r["stages"])]})
    for i, t in enumerate(out):
        if i:
            prev = {s["hr"]: s["s"] for s in out[i - 1]["stages"]}
            d = [s["s"] - _near(prev, s["hr"]) for s in t["stages"] if _near(prev, s["hr"]) is not None]
            t["change"] = round(sum(d) / len(d)) if d else None
    return out


def _near(prev, hr):
    c = [(abs(h - hr), s) for h, s in prev.items() if abs(h - hr) <= 3]
    return min(c)[1] if c else None


def _fmt(s):
    s = round(s)
    return f"{s // 60}:{s % 60:02d}"


def monthly(L, c, today, months=6):
    """Pace at each test heart rate, month by month, from every flat run that has detail. No test needed."""
    stages = engine.hr_levels(L["hrmax"])["stages"][:4]
    start = (today.replace(day=1) - dt.timedelta(days=31 * (months - 1))).replace(day=1)
    runs = [r for r in assess.load_runs(start, today + dt.timedelta(days=1))
            if r.get("hr_sec") and assess.usable(r, c)]
    per = MI if c["units"] == "mi" else 1000
    rows, m = [], start
    while m <= today:
        nxt = (m + dt.timedelta(days=32)).replace(day=1)
        mr = [r for r in runs if m <= r["date"] < nxt]
        cells = []
        for hr in stages:
            t = [assess.hr_band(r, hr - 5, hr + 5) for r in mr]
            sec, met = (sum(x) for x in zip(*t, strict=True)) if t else (0, 0)
            cells.append({"hr": hr, "pace": _fmt(per / (met / sec)) if sec >= 1200 else None, "s": per / (met / sec) if sec >= 1200 else None, "min": round(sec / 60)})
        rows.append({"month": m.isoformat()[:7], "cells": cells, "runs": len(mr)})
        m = nxt
    # change at each heart rate: latest month with data against the earliest
    change = []
    for i, hr in enumerate(stages):
        have = [r["cells"][i]["s"] for r in rows if r["cells"][i]["s"]]
        change.append({"hr": hr, "s": round(have[-1] - have[0]) if len(have) >= 2 else None})
    return {"stages": stages, "rows": rows, "change": change}


def relationship(units="mi"):
    """How much the athlete slows as the race distance doubles, from their best result at each distance in the last three years.

    Paces are flat-equivalent where the course's hills are known from a trusted watch; otherwise they are as raced, and the row says so.
    """
    import math

    import results
    since = (dt.date.today() - dt.timedelta(days=3 * 365)).isoformat()
    best = {}
    for r in results.listing():
        if r["date"] < since:
            continue
        name = r["name"].split(" · ")[0]
        s = r["flat_s"] / (r["dist_m"] / MI)
        if name not in best or s < best[name]["s"]:
            best[name] = {"name": name, "dist_m": r["dist_m"], "s": s, "date": r["date"], "adjusted": r["course"] is not None, "course": r["course"]}
    order = sorted(best.values(), key=lambda x: x["dist_m"])
    if len(order) < 2:
        return None
    base = order[0]
    k = 1.0 if units == "mi" else 1 / 1.609344
    rows = []
    for x in order:
        doubles = math.log2(x["dist_m"] / base["dist_m"])
        rows.append({"name": x["name"], "date": x["date"], "pace": _fmt(x["s"] * k), "target": _fmt((base["s"] + DOUBLING_GOOD * doubles) * k),
                     "gap": round((x["s"] - base["s"] - DOUBLING_GOOD * doubles) * k), "adjusted": x["adjusted"], "course": x["course"]})
    last = order[-1]
    per = (last["s"] - base["s"]) / math.log2(last["dist_m"] / base["dist_m"])
    verdict = "tight" if per <= DOUBLING_GOOD else "a little loose" if per <= DOUBLING_LOOSE else "loose"
    return {"rows": rows, "per_doubling": round(per), "verdict": verdict, "from": base["name"], "to": last["name"],
            "adjusted": sum(1 for x in order if x["adjusted"]), "of": len(order)}


def maybe_raise_lthr(L):
    """Move the aerobic-run heart rate up 5 once the athlete has run 10 miles at the current level in one run (a coaching convention), up to marathon heart rate."""
    hl = engine.hr_levels(L["hrmax"])
    cur = db.get("aero_lthr") or hl["start_lthr"]
    today = dt.date.today()
    for r in assess.load_runs(today - dt.timedelta(days=21), today + dt.timedelta(days=1)):
        if assess.hr_band(r, cur, cur + 10)[1] / MI >= 9.5 and cur + 5 <= hl["top_lthr"]:
            db.put("aero_lthr", cur + 5)
            return cur + 5
    if db.get("aero_lthr") is None:
        db.put("aero_lthr", cur)
    return None
