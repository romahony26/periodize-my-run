"""Two more ways of estimating a marathon time from the runner's own data, to set beside the forecast (principle 116).

A systematic review of marathon prediction equations found none good enough to rely on alone, so the forecast made from
threshold pace and endurance is shown with two estimates that use different evidence:

  - critical speed, from the fastest 3, 6, 12 and 20 minutes of the last 16 weeks, and the fraction of it marathoners hold
    (Smyth and Muniz-Pumares, 2020);
  - training itself: the weekly distance and average pace of the last 8 weeks (Tanda, 2011).

Both read only what the watch already recorded. Neither changes the plan.
"""
import datetime as dt
import math

import assess

MI = 1609.344
MARATHON_M = 42195.0
CS_WEEKS = 16                               # how far back the fastest efforts are taken from (Smyth and Muniz-Pumares, 2020)
CS_DURATIONS = (180, 360, 720, 1200)        # seconds: the efforts the line is fitted through
# the fraction of critical speed held for a marathon, by finish time: 93% at 2:30 and 79% at 6:00 (Smyth and Muniz-Pumares, 2020).
# The straight line between the two is this project's reading. [P]
FRACTION_AT = ((2.5 * 3600, 0.93), (6.0 * 3600, 0.79))
TANDA_WEEKS = 8                             # Tanda's window
TANDA_RANGE_S = (2 * 3600 + 47 * 60, 3 * 3600 + 36 * 60)    # the finish times of the runners the equation was fitted to
TANDA_MIN_RUNS = 16                         # this project's floor for the 8 weeks to say anything: two runs a week [C]


def fraction(seconds):
    """Share of critical speed held for a marathon run in `seconds`."""
    (t0, f0), (t1, f1) = FRACTION_AT
    return f0 + (f1 - f0) * (min(max(seconds, t0), t1) - t0) / (t1 - t0)


def critical_speed(today, runs=None):
    """Critical speed in metres a second from the fastest efforts of the last 16 weeks, or None when there are too few.

    The fastest distance covered in each duration is taken across all runs, and a straight line of distance against time is fitted:
    its slope is the critical speed. It can only be as fast as the hardest running in the window, so a spell without a race or an
    all-out session reads low."""
    runs = runs if runs is not None else assess.load_runs(today - dt.timedelta(weeks=CS_WEEKS), today + dt.timedelta(days=1))
    best = {}
    for r in runs:
        if r.get("glitch"):
            continue
        for k, v in (r.get("best_dur") or {}).items():
            if v and int(k) in CS_DURATIONS and v > best.get(int(k), (0, None))[0]:
                best[int(k)] = (v, r["date"])
    if len(best) < 3:
        return None
    pts = sorted((t, m) for t, (m, _) in best.items())
    mt, mm = sum(t for t, _ in pts) / len(pts), sum(m for _, m in pts) / len(pts)
    den = sum((t - mt) ** 2 for t, _ in pts)
    cs = sum((t - mt) * (m - mm) for t, m in pts) / den
    if cs <= 0:
        return None
    return {"speed": cs, "reserve_m": mm - cs * mt, "efforts": [{"seconds": t, "metres": best[t][0], "date": best[t][1].isoformat()} for t in sorted(best)]}


def marathon_from_cs(cs):
    """Marathon seconds for a critical speed: the time whose own fraction of critical speed gives that time."""
    t = MARATHON_M / (cs * 0.88)
    for _ in range(30):
        t = MARATHON_M / (cs * fraction(t))
    return t


def from_training(today, runs=None):
    """Tanda's equation: marathon pace (s/km) = 17.1 + 140.0 x exp(-0.0053 x K) + 0.55 x P, with K the mean weekly distance in km and
    P the mean training pace in s/km over 8 weeks. None when the 8 weeks hold too little running."""
    runs = runs if runs is not None else assess.load_runs(today - dt.timedelta(weeks=TANDA_WEEKS), today + dt.timedelta(days=1))
    runs = [r for r in runs if r["date"] > today - dt.timedelta(weeks=TANDA_WEEKS) and r.get("timer_s") and r.get("dist_m")]
    if len(runs) < TANDA_MIN_RUNS:
        return None
    km = sum(r["dist_m"] for r in runs) / 1000
    secs = sum(r["timer_s"] for r in runs)
    k, p = km / TANDA_WEEKS, secs / km
    t = tanda_seconds(k, p)
    return {"seconds": t, "weekly_km": k, "pace_s_km": p, "runs": len(runs), "in_range": TANDA_RANGE_S[0] <= t <= TANDA_RANGE_S[1]}


MEAN_PACE_OVER_GOAL = 1.16      # mean training pace as a multiple of goal marathon pace: four fifths easy, one fifth at goal pace [C]


def tanda_seconds(weekly_km, pace_s_km):
    return (17.1 + 140.0 * math.exp(-0.0053 * weekly_km) + 0.55 * pace_s_km) * MARATHON_M / 1000


def training_for(goal_s, planned_weekly_km=None):
    """What Tanda's equation says about a goal time: the weekly distance that goes with it, and what the planned weeks are worth.

    Both assume a mean training pace of 1.16 x goal marathon pace. The equation was fitted to 22 runners, so these are
    signposts, not targets."""
    p = MEAN_PACE_OVER_GOAL * goal_s / (MARATHON_M / 1000)
    x = (goal_s / (MARATHON_M / 1000) - 17.1 - 0.55 * p) / 140.0
    return {"pace_s_km": p, "weekly_km": -math.log(x) / 0.0053 if 0 < x < 1 else None,
            "planned_km": planned_weekly_km, "planned_s": tanda_seconds(planned_weekly_km, p) if planned_weekly_km else None}


def marathon(today, model_s, tp):
    """The three estimates of a marathon run today, and the middle one. `model_s` is the app's own estimate, `tp` threshold speed (m/s)."""
    runs = assess.load_runs(today - dt.timedelta(weeks=CS_WEEKS), today + dt.timedelta(days=1))      # one read serves both
    cs, tr = critical_speed(today, runs), from_training(today, runs)
    out = {"model": model_s, "cs": None, "training": tr}
    if cs:
        # threshold speed is a little below critical speed in a runner who has raced lately, so a critical speed slower than
        # threshold means the window holds no all-out running [C]
        out["cs"] = dict(cs, seconds=marathon_from_cs(cs["speed"]), low=cs["speed"] < tp)
    have = sorted(x for x in (model_s, out["cs"] and out["cs"]["seconds"], tr and tr["seconds"]) if x)
    out["middle"] = have[len(have) // 2] if len(have) % 2 else (have[len(have) // 2 - 1] + have[len(have) // 2]) / 2
    out["count"] = len(have)
    return out
