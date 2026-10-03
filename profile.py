"""Describe the athlete from their whole Garmin history, and derive personal limits.

Works from the activity list alone (one row per activity), so it can use
every year on the account without downloading every file.
"""
import datetime as dt

import db

MI = 1609.344


def weekly_miles(runs):
    """{monday: miles} for every week from the first run to the last."""
    out = {}
    for r in runs:
        d = dt.date.fromisoformat(r["date"])
        out.setdefault(d - dt.timedelta(days=d.weekday()), 0.0)
        out[d - dt.timedelta(days=d.weekday())] += (r["dist_m"] or 0) / MI
    if not out:
        return {}
    m, last = min(out), max(out)
    while m <= last:
        out.setdefault(m, 0.0)
        m += dt.timedelta(days=7)
    return dict(sorted(out.items()))


def best_block(wk, since, n=8):
    vals = [v for k, v in wk.items() if k >= since]
    return max((sum(vals[i:i + n]) / n for i in range(max(len(vals) - n + 1, 1))), default=0.0) if vals else 0.0


def derive(today=None):
    today = today or dt.date.today()
    runs = db.rows("SELECT * FROM activities WHERE sport='running' AND date!='' AND dist_m>0 ORDER BY date")
    if not runs:
        return None
    wk = weekly_miles(runs)
    y1, y3 = today - dt.timedelta(days=365), today - dt.timedelta(days=3 * 365)
    recent = [v for k, v in wk.items() if today - dt.timedelta(weeks=8) <= k < today - dt.timedelta(days=today.weekday())]
    recent8 = sum(recent) / len(recent) if recent else 0.0
    best8_3y = best_block(wk, y3)
    best8_all = best_block(wk, dt.date.min)

    # maximum heart rate from the last three years, ignoring one-off sensor spikes
    peaks = sorted((r["max_hr"] for r in runs if r["max_hr"] and r["date"] >= y3.isoformat() and (r["timer_s"] or 0) > 900 and r["max_hr"] < 215), reverse=True)
    need = max(8, round(0.012 * len(peaks)))   # a level reached on about 1 run in 80; wrist sensors spike higher than that now and then
    hrmax = round(peaks[need - 1]) if len(peaks) >= need else (round(peaks[-1]) if peaks else None)

    def best(lo, hi, since=None):
        c = [r for r in runs if lo <= (r["dist_m"] or 0) <= hi and r["timer_s"] and (since is None or r["date"] >= since.isoformat())]
        b = min(c, key=lambda r: r["timer_s"] / r["dist_m"], default=None)
        return {"time_s": b["timer_s"] * ((lo + hi) / 2) / b["dist_m"] if False else b["timer_s"], "date": b["date"], "dist_m": b["dist_m"]} if b else None

    def best_split(col, since=None):
        c = [r for r in runs if r[col] and (since is None or r["date"] >= since.isoformat())]
        b = min(c, key=lambda r: r[col], default=None)
        return {"time_s": b[col], "date": b["date"]} if b else None

    bests = {
        "5k": {"all": best_split("best5k"), "year": best_split("best5k", y1)},
        "10k": {"all": best_split("best10k"), "year": best_split("best10k", y1)},
        "half": {"all": best(21000, 21600), "year": best(21000, 21600, y1)},
        "marathon": {"all": best(42000, 43000), "year": best(42000, 43000, y1)},
    }
    dates = [dt.date.fromisoformat(r["date"]) for r in runs]
    gaps = [(a, b) for a, b in zip(dates, dates[1:], strict=False) if (b - a).days >= 14 and b >= y3]
    prof = {
        "first_run": runs[0]["date"], "runs": len(runs), "miles": sum((r["dist_m"] or 0) for r in runs) / MI,
        "years": (today - dates[0]).days / 365.25, "recent8": recent8, "best8_3y": best8_3y, "best8_all": best8_all,
        "longest_year": max(((r["dist_m"] or 0) / MI for r in runs if r["date"] >= y1.isoformat()), default=0.0),
        "runs_per_week": sum(1 for r in runs if r["date"] >= (today - dt.timedelta(weeks=8)).isoformat()) / 8,
        "hrmax_observed": hrmax, "bests": bests,
        "layoffs_3y": [{"from": a.isoformat(), "to": b.isoformat(), "days": (b - a).days} for a, b in gaps],
    }
    db.put("profile", prof)
    return prof


def limits(prof, c, goal_miles):
    """Personal planning limits from history. Rules of thumb; every value can be overridden in settings."""
    peak = max(prof["best8_3y"] * 1.10, prof["recent8"] * 1.25, 20)
    peak = min(round(peak / 5) * 5, 90)
    if goal_miles is None or goal_miles < 10:
        long_spec, spec_weeks = min(max(0.30 * peak, 8), 16), 10
    elif goal_miles < 20:
        long_spec, spec_weeks = min(max(0.33 * peak, 10), 15), 12
    elif goal_miles <= 30:
        long_spec, spec_weeks = min(max(0.42 * peak, 16), 22), 18
    else:   # ultra: longer long runs, run easy
        long_spec, spec_weeks = min(max(0.45 * peak, 18), 28), 16
    hr = c.get("hrmax") or prof.get("hrmax_observed") or 185
    return {
        "peak_miles": c.get("peak_miles_override") or peak, "base_cap_miles": round(0.9 * (c.get("peak_miles_override") or peak)),
        "long_run_cap_specific": round(long_spec), "long_run_cap_base": round(long_spec) - 3, "long_run_floor": max(round(0.45 * long_spec), 5),
        "specific_weeks": spec_weeks, "hrmax": hr, "easy_hr_max": round(0.76 * hr), "steady_hr_max": round(0.82 * hr),
        "threshold_hr_cap": round(0.89 * hr), "marathon_hr_band": [round(0.825 * hr / 5) * 5, round(0.875 * hr / 5) * 5],
        "easy_hr_band": [round(0.72 * hr / 5) * 5, round(0.775 * hr / 5) * 5],
    }
