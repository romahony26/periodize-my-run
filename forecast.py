"""Race-day forecast: where the athlete is likely to be on race day, not where they are today.

It moves every week with what was actually done. Three things from the athlete's own data drive it:
  - current fitness (race index from threshold speed),
  - their proven level: the best they have shown in the last three years, put on a common footing across distances,
  - how much of a plan they realistically complete, from their history and then from this plan as it unfolds.
One value is a general rule, not learned: fitness closes the gap to the proven level with a time constant of TAU weeks of training done.
"""
import datetime as dt
import math

import assess
import db
import profile
import equiv

TAU = 10.0            # weeks of completed training to close about 63% of the gap to the proven level
TAPER_WEEKS = 2
MI = 1609.344


def completion_history(today, weeks=104):
    """Share of intended training the athlete has historically delivered.

    Each past week is compared with the median of the six weeks before it: a week at or above that level counts as 100%,
    a missed or cut week as its fraction. The average over two years is their realistic completion rate.
    """
    runs = db.rows("SELECT date, dist_m FROM activities WHERE sport='running' AND date>=? AND date<?",
                   ((today - dt.timedelta(weeks=weeks + 8)).isoformat(), (today - dt.timedelta(days=today.weekday())).isoformat()))
    wk = list(profile.weekly_miles(runs).values())
    ratios = []
    for i in range(6, len(wk)):
        ref = sorted(wk[i - 6:i])[3]
        if ref >= 5:
            ratios.append(min(wk[i] / ref, 1.0))
    return (sum(ratios) / len(ratios), len(ratios)) if len(ratios) >= 12 else (None, len(ratios))


def completion_plan(today):
    """Share of this app's plan actually run so far (distance done on planned days / distance planned), and the days it rests on."""
    r = db.rows("SELECT p.date, p.miles, (SELECT SUM(dist_m) FROM activities a WHERE a.sport='running' AND a.date=p.date) m "
                "FROM plan p WHERE p.date<? AND p.miles>0 AND p.label NOT LIKE 'Holiday%'", (today.isoformat(),))
    planned = sum(x["miles"] for x in r)
    done = sum(min((x["m"] or 0) / MI, x["miles"] * 1.1) for x in r)
    return (min(done / planned, 1.0), len(r)) if planned else (None, 0)


def expected_completion(today):
    """History first; this plan's own record takes over as it accumulates (full weight after 8 weeks of planned days)."""
    hist, n_hist = completion_history(today)
    plan, n_plan = completion_plan(today)
    base = hist if hist is not None else 0.85
    w = min(n_plan / 48, 1.0) if plan is not None else 0.0
    chosen = db.get("forecast_completion")       # the athlete may fix the assumption themselves
    value = float(chosen) if chosen else base * (1 - w) + (plan or 0) * w
    return {"value": value, "chosen": bool(chosen), "history": hist, "history_weeks": n_hist, "plan": plan, "plan_days": n_plan, "plan_weight": w}


def proven_index(today, slope, d_ref, years=3):
    """Best level shown in race results in the last `years`, each moved to the reference distance using the athlete's own distance profile."""
    best = None
    for r in db.rows("SELECT * FROM results WHERE hidden=0 AND date>=?", ((today - dt.timedelta(days=365 * years)).isoformat(),)):
        v = equiv.index(r["dist_m"], r["time_s"]) - slope * math.log(r["dist_m"] / d_ref)
        if best is None or v > best[0]:
            best = (v, r["name"].split(" · ")[0], r["date"])
    return best


def forecast(tp, endurance, c, race, today=None):
    """Central forecast for a race, with what full completion and a poor run of training would give."""
    today = today or dt.date.today()
    day = dt.date.fromisoformat(race["date"]) if isinstance(race["date"], str) else race["date"]
    miles = race["miles"]
    weeks = max(((day - today).days / 7) - TAPER_WEEKS, 0)
    slope = ((db.get("model") or {}).get("distance_slope") or {}).get("value", 0.0)
    cur = equiv.from_threshold(tp)
    d_ref = tp * 3600
    pv = proven_index(today, slope, d_ref)
    top = max(pv[0], cur) if pv else cur
    comp = expected_completion(today)

    def at(share):
        done = weeks * share
        v = cur + (top - cur) * (1 - math.exp(-done / TAU))
        end = min(1.0, endurance + (1 - endurance) * min(done / 12, 1.0) * min(share / 0.85, 1.0))
        return assess.race_time(v, miles, end, c, slope)[0], v

    central, v_c = at(comp["value"])
    out = {"seconds": central, "index": v_c, "all": at(1.0)[0], "poor": at(max(comp["value"] - 0.2, 0.3))[0], "poor_share": max(comp["value"] - 0.2, 0.3),
           "completion": comp, "weeks": weeks, "current_index": cur, "proven": {"index": top, "from": pv[1] if pv and pv[0] >= cur else None, "date": pv[2] if pv and pv[0] >= cur else None}}
    return out
