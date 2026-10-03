"""A race's course: its elevation profile, an even-effort pacing plan over it, and weekly climb targets for hilly goals.

  - The profile is distance and elevation every 100 m, read from a GPX file in the browser. Elevation is smoothed over 300 m,
    because GPX elevation is noisy and noise reads as climbing.
  - Pacing is even effort: every stretch is run at the same energy cost, using Minetti's measured cost of running on a gradient
    (Minetti et al. 2002), the same curve the app uses for grade-adjusted pace. Uphill miles come out slower, downhill miles faster,
    and the total is the target time. It does not model fatigue, walking, footing, wind or heat.
  - Climb targets are specificity, a coaching principle rather than a research finding: by three weeks out, your weekly climb per
    mile matches the race's. The ramp starts sixteen weeks out from wherever you are now.
"""
import json

import db
from assess import MI
from fitrun import effort

STEP = 100.0
HILLY_M_PER_MILE = 16.0        # about 10 m per km: below this a course is treated as flat for training purposes


def clean(points):
    """Validate [[metres along, elevation], ...] and return an even 100 m profile with smoothed elevation."""
    try:
        pts = [(float(p[0]), float(p[1])) for p in points]
    except (TypeError, ValueError, IndexError) as e:
        raise ValueError("The course must be a list of distance and elevation pairs.") from e
    if not 20 <= len(pts) <= 20000:
        raise ValueError("The course has too few or too many points.")
    if any(not (0 <= d <= 500_000 and -500 <= e <= 9000) for d, e in pts) or any(b[0] < a[0] for a, b in zip(pts, pts[1:], strict=False)):
        raise ValueError("The course has distances or elevations that are not possible.")
    total = pts[-1][0]
    if total < 1000:
        raise ValueError("The course is shorter than a kilometre.")
    out, k = [], 0
    n = int(total // STEP)
    for i in range(n + 1):
        d = i * STEP
        while k + 1 < len(pts) - 1 and pts[k + 1][0] < d:
            k += 1
        (d0, e0), (d1, e1) = pts[k], pts[k + 1]
        f = (d - d0) / (d1 - d0) if d1 > d0 else 0.0
        out.append(e0 + min(max(f, 0.0), 1.0) * (e1 - e0))
    sm = [sum(out[max(0, i - 1):i + 2]) / len(out[max(0, i - 1):i + 2]) for i in range(len(out))]
    return [round(x, 1) for x in sm]


def climb(profile):
    return round(sum(max(b - a, 0) for a, b in zip(profile, profile[1:], strict=False)))


def pacing(profile, race_miles, target_s, units="mi"):
    """Even-effort splits. The profile is stretched to the official race distance."""
    n = len(profile) - 1
    seg = race_miles * MI / n                        # metres each profile step stands for
    scale = seg / STEP
    cost = [effort((profile[i + 1] - profile[i]) / STEP) for i in range(n)]
    total_cost = sum(cost)
    per = MI if units == "mi" else 1000.0
    rows, t = [], 0.0
    count = int(race_miles * MI / per + 0.999)
    for k in range(count):
        a, b = k * per, min((k + 1) * per, race_miles * MI)
        secs = up = down = 0.0
        j = int(a // seg)
        while j < n and j * seg < b - 1e-6:
            part = (min((j + 1) * seg, b) - max(j * seg, a)) / seg
            secs += part * cost[j] / total_cost * target_s
            dz = (profile[j + 1] - profile[j]) * part * scale
            up, down = up + max(dz, 0), down + max(-dz, 0)
            j += 1
        t += secs
        length = (b - a) / per
        rows.append({"n": k + 1, "len": round(length, 2), "split_s": round(secs), "pace_s": round(secs / length) if length > 0.05 else None,
                     "cum_s": round(t), "up_m": round(up), "down_m": round(down)})
    flat = target_s / (race_miles * MI / per)
    return {"rows": rows, "flat_pace_s": round(flat), "climb_m": round(climb(profile) * scale), "target_s": round(target_s), "units": units,
            "slowest": max((r for r in rows if r["pace_s"]), key=lambda r: r["pace_s"])["n"], "fastest": min((r for r in rows if r["pace_s"]), key=lambda r: r["pace_s"])["n"]}


def climb_target(race, weeks_to_race, week_miles, long_miles, today):
    """Weekly and long-run climb targets toward a hilly goal race, or None if the race is flat or its climb is not known."""
    import datetime as dt
    if not race or not race.get("climb_m") or not race.get("miles") or race["climb_m"] / race["miles"] < HILLY_M_PER_MILE:
        return None
    since = (today - dt.timedelta(days=28)).isoformat()
    r = db.rows("SELECT SUM(ascent_m) a, SUM(dist_m) m FROM activities WHERE sport='running' AND date>=? AND date<?", (since, today.isoformat()))[0]
    now = (r["a"] or 0) / ((r["m"] or 0) / MI) if r["m"] else 0.0
    goal = race["climb_m"] / race["miles"]
    progress = min(max((16 - (weeks_to_race or 99)) / 13, 0.0), 1.0)
    ratio = max(now + (goal - now) * progress, min(now, goal))
    mon = today - dt.timedelta(days=today.weekday())
    done = db.rows("SELECT SUM(ascent_m) a FROM activities WHERE sport='running' AND date>=? AND date<=?", (mon.isoformat(), today.isoformat()))[0]["a"] or 0
    return {"race": race["name"], "race_per_mile": round(goal), "now_per_mile": round(now), "target_per_mile": round(ratio), "week_m": round(week_miles * ratio / 10) * 10,
            "long_m": round(long_miles * ratio / 10) * 10, "done_m": round(done), "progress": round(progress, 2), "weeks_to_race": weeks_to_race}


def profile_of(race):
    return json.loads(race["course"]) if race.get("course") else None
