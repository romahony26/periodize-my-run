"""Trends: is each part of fitness going up, down or holding, over the window that suits it?

Fitness is read as three separate things, because races of different lengths lean on them differently:
  - speed: the threshold estimate, which mostly decides 5K and 10K;
  - endurance base: weekly volume, long runs and race-pace miles toward the goal ("race-specific endurance"), which matters more
    as the distance grows;
  - durability: how far pace per heartbeat fades late in long steady runs (aerobic drift), which matters most for the marathon
    and longer (Jones 2024; Hunter and Muniz-Pumares 2025; Smyth and colleagues 2022).

Each is judged over its own window, because aerobic change takes weeks to show and day-to-day readings are noise:
  speed over 6 weeks (steady within 1%, about the smallest change in race speed that matters); endurance base over 4 weeks
  (steady within 5 points); durability over the last six long runs, three against three (steady within 1.5 points); steps,
  heart-rate variability, resting heart rate and sleep as 7-day averages against the athlete's own 60-day normal. The windows
  follow the research; the steady bands are this project's choice.

The weekly history is rebuilt by re-running the weekly assessment for each past Monday on the data that existed then, so the
trend reaches back before the app was installed. It is cached and only missing weeks are worked out.
"""
import datetime as dt
import statistics

import assess
import db
import engine
import heat
import equiv
import insights

WEEKS = 26


def _monday(day):
    return day - dt.timedelta(days=day.weekday())


def history(c, L, today, weeks=WEEKS):
    """{monday: {"tp", "endurance", "parts"}} for the last `weeks` Mondays, cached. Missing weeks are worked out in date order."""
    cache = dict(db.get("trend_history") or {})
    mon = _monday(today)
    mondays = [mon - dt.timedelta(weeks=k) for k in range(weeks, -1, -1)]
    changed, prev = False, None
    for m in mondays:
        key = m.isoformat()
        if key in cache and m < mon:
            prev = cache[key]["tp"]
            continue
        try:
            st = assess.assess(c, L, m, prev)
        except Exception:      # noqa: BLE001 - one bad week must not stop the others
            st = None
        if st:
            cache[key] = {"tp": st["tp"], "endurance": st["endurance"], "parts": st["endurance_parts"]}
            prev = st["tp"]
            changed = True
    keep = {k: v for k, v in cache.items() if k >= mondays[0].isoformat()}
    if changed or len(keep) != len(cache):
        db.put("trend_history", keep)
    return dict(sorted(keep.items()))


def direction(now, then, band, higher_is_better=True):
    """'rising', 'falling' or 'steady' for the athlete: rising always means getting better."""
    if now is None or then is None:
        return None
    d = now - then
    if abs(d) < band:
        return "steady"
    return "rising" if (d > 0) == higher_is_better else "falling"


def speed(c, hist):
    rows = [{"date": k, "v": v["tp"], "pace": engine.pace(v["tp"], c["units"])} for k, v in hist.items() if v.get("tp")]
    now, then = (rows[-1]["v"], rows[-7]["v"]) if len(rows) >= 7 else (None, None)
    pct = (now / then - 1) * 100 if now and then else None
    return {"kind": "speed", "title": "Threshold pace", "rows": rows, "window": "6 weeks",
            "dir": direction(pct, 0.0, 1.0) if pct is not None else None, "change": round(pct, 1) if pct is not None else None,
            "text": "Speed: your threshold estimate each week. It mostly decides 5K and 10K. Judged over 6 weeks, because aerobic change "
                    "takes that long to show; within 1% it counts as steady."}


def base(hist):
    rows = [{"date": k, "v": round(v["endurance"] * 100)} for k, v in hist.items() if v.get("endurance") is not None]
    now, then = (rows[-1]["v"], rows[-5]["v"]) if len(rows) >= 5 else (None, None)
    return {"kind": "base", "title": "Race-specific endurance", "rows": rows, "window": "4 weeks",
            "dir": direction(now, then, 5), "change": (now - then) if now is not None and then is not None else None,
            "text": "Endurance base: long runs, race-pace miles and weekly volume toward your goal, as a share of a full build. It matters "
                    "more the longer the race. Judged over 4 weeks; within 5 points it counts as steady."}


def durability(today):
    runs = insights.drift_history(today, weeks=WEEKS, min_minutes=70, limit=30)
    rows = [{"date": r["date"], "v": r["drift"], "mi": r["mi"], "warm": r.get("warm", False)} for r in runs]
    cool = [r for r in rows if not r["warm"]]         # warm runs drift more whatever the fitness, so they are shown but not compared
    if len(cool) >= 6:
        now, then = statistics.mean(r["v"] for r in cool[-3:]), statistics.mean(r["v"] for r in cool[-6:-3])
    else:
        now = then = None
    return {"kind": "durability", "title": "Aerobic drift on long runs", "rows": rows, "window": "last 6 long runs",
            "dir": direction(now, then, 1.5, higher_is_better=False), "change": round(now - then, 1) if now is not None else None,
            "text": "Durability: how far your pace per heartbeat fades in the second half of long steady runs. Less is better, and it "
                    "matters most for the marathon and longer. The last three long runs are compared with the three before; within "
                    "1.5 points it counts as steady. Heat raises drift by itself, so with weather switched on, runs done in warm conditions "
                    "(above 18 °C WBGT) are left out of the comparison. Hills raise it too."}


def steps(today):
    s = assess.offrun_steps(today - dt.timedelta(weeks=WEEKS, days=60), today)
    rows = []
    for k in range(WEEKS, -1, -1):
        end = _monday(today) - dt.timedelta(weeks=k) + dt.timedelta(days=7)
        vals = [s[d] for d in ((end - dt.timedelta(days=i)).isoformat() for i in range(1, 8)) if d in s]
        if len(vals) >= 4:
            rows.append({"date": (end - dt.timedelta(days=7)).isoformat(), "v": round(statistics.mean(vals))})
    sp = assess.steps_summary(today, db.cfg())
    d = None
    if sp:
        d = "steady" if abs(sp["week"] - sp["base"]) < max(sp["sd"], 0.1 * sp["base"]) else ("higher" if sp["week"] > sp["base"] else "lower")
    return {"kind": "steps", "title": "Steps outside your runs", "rows": rows, "window": "7 days against your normal",
            "dir": d, "normal": round(sp["base"]) if sp else None,
            "text": "Average steps a day outside your runs, week by week. A week well above your normal adds load the plan does not "
                    "schedule; this compares the last 7 days with your 60-day normal."}


def recovery(today, days=84):
    """7-day averages of HRV, resting heart rate and sleep, each with the athlete's normal range from the 60 days before the last week."""
    rows = {r["date"]: r for r in db.rows("SELECT date,hrv,rhr,sleep_h FROM daily WHERE date>=?", ((today - dt.timedelta(days=days + 70)).isoformat(),))}

    def series(key):
        out = []
        for i in range(days, -1, -1):
            d = today - dt.timedelta(days=i)
            vals = [rows[x][key] for x in ((d - dt.timedelta(days=j)).isoformat() for j in range(7)) if x in rows and rows[x][key]]
            if len(vals) >= 4:
                out.append({"date": d.isoformat(), "v": round(statistics.mean(vals), 1)})
        base = [rows[x][key] for x in ((today - dt.timedelta(days=j)).isoformat() for j in range(7, 67)) if x in rows and rows[x][key]]
        normal = (round(statistics.mean(base), 1), round(statistics.pstdev(base), 1)) if len(base) >= 14 else None
        return out, normal

    res = {}
    for key, label, better_high, unit in (("hrv", "Heart-rate variability (7-day)", True, "ms"), ("rhr", "Resting heart rate (7-day)", False, "bpm"),
                                          ("sleep_h", "Sleep (7-day)", True, "h")):
        out, normal = series(key)
        d = None
        if out and normal:
            m, sd = normal
            band = 0.5 * max(sd, 0.1 if key == "sleep_h" else 1.0)
            d = direction(out[-1]["v"], m, band, better_high)
        res[key] = {"label": label, "rows": out, "normal": normal, "dir": d, "unit": unit}
    return res


def prediction_change(c, hist, distances):
    """Predicted time for each distance now and 6 weeks ago, from the weekly history. Negative seconds = faster now."""
    ks = list(hist)
    if len(ks) < 7:
        return {}
    now, then = hist[ks[-1]], hist[ks[-7]]
    out = {}
    for name, dm in distances:
        a = assess.projection({"tp": now["tp"], "endurance": now["endurance"]}, c, dm / assess.MI)[0]
        b = assess.projection({"tp": then["tp"], "endurance": then["endurance"]}, c, dm / assess.MI)[0]
        out[name] = round(a - b)
    return out


def all_distances():
    return equiv.DISTANCES + [("50K", 50000.0)]


def race_check(c, L, today, years=3, limit=12):
    """How close the predictions are to your actual races.

    For each race in the last `years` years, the prediction is rebuilt from what was known on the Monday before it (runs, earlier
    races, the watch's estimate), with today's rules, and set against the actual time (adjusted to a flat course where that is
    known, since predictions are for flat courses). Positive error = the prediction was slower than you ran (pessimistic).
    Each race is worked out once and kept."""
    import results
    cache = dict(db.get("race_check") or {})
    since = (today - dt.timedelta(days=365 * years)).isoformat()
    rows, changed = [], False
    for r in results.listing(c["units"]):
        if r["date"] < since or not r["counts"] or not r.get("flat_s") or not r.get("dist_m"):
            continue
        key = f"{r['date']}|{round(r['dist_m'])}|{round(r['flat_s'])}"
        if key not in cache:
            day = dt.date.fromisoformat(r["date"])
            try:
                st = assess.assess(c, L, _monday(day), None)
            except Exception:      # noqa: BLE001 - one race must not stop the others
                st = None
            cache[key] = round(assess.projection({"tp": st["tp"], "endurance": st["endurance"]}, c, r["dist_m"] / assess.MI)[0]) if st else None
            changed = True
        pred = cache[key]
        if pred:
            # predictions are for neutral weather, so the race is too: its time is reduced by what the day's weather cost
            w = heat.on_day(r["date"], r.get("activity_id"))
            actual = r["flat_s"] * (1 - w["pct"] / 100) if w and w.get("pct") else r["flat_s"]
            rows.append({"date": r["date"], "name": r["name"].split(" · ")[-1] if " · " in r["name"] else r["name"], "distance": r["name"].split(" · ")[0],
                         "predicted": engine.hms(pred), "actual": engine.hms(actual), "error": round((pred - actual) / actual * 100, 1),
                         "weather": heat.words(w, c["units"]) if w else ""})
        if len(rows) >= limit:
            break
    if changed:
        db.put("race_check", cache)
    if not rows:
        return None
    errs = [x["error"] for x in rows]
    return {"rows": rows, "mean_abs": round(statistics.mean(abs(e) for e in errs), 1), "bias": round(statistics.mean(errs), 1), "n": len(rows)}
