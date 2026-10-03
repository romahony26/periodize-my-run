"""Learn the model's settings from the athlete's own data, instead of using fixed values.

Each value is learned only when there is enough data; otherwise the general
default is used, and the app says which is which on the "How it works" page.
Runs after every sync, so the model keeps moving with the athlete.
"""
import datetime as dt
import json
import math
import statistics

import assess
import db
import engine
import profile
import results
import equiv

DEFAULTS = {"threshold_correction": 1.0, "distance_slope": 0.0, "slow_per_point": 0.012}


def distance_slope(today):
    """How the athlete's race index changes with race distance: index points per doubling... per unit of ln(distance).

    Negative = relatively better at short races. Compared within each calendar year, so changes in fitness between years do not distort it.
    """
    res = [r for r in results.listing() if r["date"] >= (today - dt.timedelta(days=4 * 365)).isoformat()]
    by_year = {}
    for r in res:
        by_year.setdefault(r["date"][:4], []).append((math.log(r["dist_m"]), r["index"]))
    sxx = sxy = 0.0
    n = 0
    for pts in by_year.values():
        if len({round(x, 2) for x, _ in pts}) < 2:
            continue
        mx, my = statistics.mean(x for x, _ in pts), statistics.mean(y for _, y in pts)
        sxx += sum((x - mx) ** 2 for x, _ in pts)
        sxy += sum((x - mx) * (y - my) for x, y in pts)
        n += len(pts)
    if n < 4 or sxx < 0.5:
        return None, n
    return max(min(sxy / sxx, 0.5), -3.0), n


def threshold_correction(today, c, L):
    """How the athlete's races compare with their pace-to-heart-rate line: race threshold speed over the line's prediction.

    1.0 means the line predicts their racing exactly. Learned from the four weeks before each of their own races; 1.0 until then.
    """
    ks = []
    for r in results.listing():
        day = dt.date.fromisoformat(r["date"])
        if (today - day).days > 400:
            continue
        fit = assess.hr_speed_line([x for x in assess.load_runs(day - dt.timedelta(days=28), day) if assess.usable(x, c)], L["hrmax"])
        if fit and fit["minutes"] >= 60:
            ks.append(equiv.threshold_speed(r["index"]) / fit["at"](c["threshold_hr_fraction"] * L["hrmax"]))
    if not ks:
        return None, 0
    return max(min(statistics.median(ks), 1.15), 0.90), len(ks)


def slow_per_point(today, c, L):
    """How much slower the athlete actually runs per heartbeat on mornings with poor recovery, per readiness point."""
    lo, hi = L["easy_hr_band"]
    runs = assess.load_runs(today - dt.timedelta(days=182), today)
    eff = []
    for x in runs:
        s, m = assess.hr_band(x, lo, hi)
        if s >= 600 and assess.usable(x, c):
            eff.append((x["date"], m / s))
    rel = []
    for d, e in eff:
        near = [v for dd, v in eff if abs((dd - d).days) <= 21 and dd != d]
        if len(near) >= 5:
            pts = engine.readiness(d, c, learn=False)
            if pts["level"] != "unknown":
                rel.append((pts["points"], e / statistics.median(near) - 1))
    poor = [(p, r) for p, r in rel if p >= 1]
    good = [r for p, r in rel if p == 0]
    if len(poor) < 8 or len(good) < 20:
        return None, len(poor)
    drop = statistics.mean(good) - statistics.mean(r for _, r in poor)
    return max(min(drop / statistics.mean(p for p, _ in poor), 0.025), 0.006), len(poor)


def altitude_trust():
    """Which watches' altitude can be trusted, learned from the athlete's own loop runs.

    On a run that finishes where it started, the altitude should read the same at both ends. A healthy sensor is within a few metres;
    a failing one is tens of metres out. A device is distrusted when its typical error over five or more loop runs exceeds 15 m.
    Grade adjustment is only applied to runs from trusted devices.
    """
    err = {}
    for r in db.rows("SELECT detail FROM activities WHERE detail IS NOT NULL"):
        d = json.loads(r["detail"])
        if d.get("device") and d.get("loop_alt_err") is not None:
            err.setdefault(d["device"], []).append(d["loop_alt_err"])
    out = {dev: {"median": round(statistics.median(v), 1), "runs": len(v), "trusted": not (len(v) >= 5 and statistics.median(v) > 15)} for dev, v in err.items()}
    db.put("altitude_trust", out)
    return out


def run(today=None):
    """Recalculate every learned value and store it."""
    today = today or dt.date.today()
    c = db.cfg()
    prof = db.get("profile") or profile.derive()
    if not prof:
        return None
    rs = db.rows("SELECT * FROM races WHERE priority='A' AND date>=? ORDER BY date LIMIT 1", (today.isoformat(),))
    L = profile.limits(prof, c, rs[0]["miles"] if rs else None)
    altitude_trust()
    model = {"updated": today.isoformat()}
    for key, (val, n) in (("distance_slope", distance_slope(today)), ("threshold_correction", threshold_correction(today, c, L)),
                          ("slow_per_point", slow_per_point(today, c, L))):
        model[key] = {"value": val if val is not None else DEFAULTS[key], "learned": val is not None, "n": n}
    db.put("model", model)
    return model


def value(key):
    m = (db.get("model") or {}).get(key)
    return m["value"] if m else DEFAULTS[key]
