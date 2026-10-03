"""Age grading: a race time as a percentage of the world-best standard for that age, sex and distance.

The standards are Alan Jones's 2025 road running tables (public domain, CC0), bundled in agegrade.json. They cover road
distances from a mile to 200 km and ages 5 to 100. Between table distances the standard is interpolated on a log scale.
"""
import datetime as dt
import functools
import json
import math
import os


@functools.cache
def _tables():
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "agegrade.json"), encoding="utf-8") as f:
        return json.load(f)


def age_on(birth, day):
    b, d = dt.date.fromisoformat(birth), dt.date.fromisoformat(day) if isinstance(day, str) else day
    return d.year - b.year - ((d.month, d.day) < (b.month, b.day))


def standard(sex, age, dist_m):
    """World-best standard in seconds, or None outside the tables."""
    t = _tables()
    row = t.get(sex, {}).get(str(int(age)))
    km = dist_m / 1000
    if not row or km < t["km"][0] * 0.99 or km > t["km"][-1] * 1.01:
        return None
    ks = t["km"]
    for i in range(len(ks) - 1):
        if ks[i] <= km <= ks[i + 1]:
            f = (math.log(km) - math.log(ks[i])) / (math.log(ks[i + 1]) - math.log(ks[i]))
            return math.exp(math.log(row[i]) + f * (math.log(row[i + 1]) - math.log(row[i])))
    return row[0] if km < ks[0] else row[-1]


def grade(sex, birth, day, dist_m, time_s):
    """Age grade as a percentage, or None if the athlete's sex or date of birth is not known or the distance is outside the tables."""
    if sex not in ("M", "F") or not birth or not time_s:
        return None
    try:
        s = standard(sex, age_on(birth, day), dist_m)
    except ValueError:
        return None
    return round(100 * s / time_s, 1) if s else None
