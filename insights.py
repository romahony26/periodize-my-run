"""Things worth knowing that the plan itself does not show: load and form, single-run spikes, aerobic drift, fuelling, shoes.

Sources, where there is one:
  - Load is Lucia's TRIMP (minutes in three zones weighted 1, 2, 3), the same measure the execution score uses.
  - Fitness and fatigue are Banister's impulse-response model in its usual simplified form: running averages of daily load
    that fade over 42 and 7 days. Form is fitness minus fatigue. The 42 and 7 are the conventional values, not fitted to the athlete.
  - Spike warning: Frandsen and colleagues (2025, 5,200 runners): a run more than 10% longer than the longest run of the previous
    30 days went with more overuse injuries. The same study found no link with week-to-week mileage change, so there is no weekly warning.
  - Fuelling: Jeukendrup (2014): about 30 g of carbohydrate an hour for 1-2 hours, up to 60 g for 2-3 hours, up to 90 g beyond 2.5 hours.
  - Aerobic drift under 5% is a common coaching rule of thumb, not a research threshold.
"""
import datetime as dt
import math
import re

import assess
import db
from assess import MI

FIT_DAYS, FAT_DAYS = 42, 7
SPIKE = 1.10


def treadmill(r):
    return (r.get("sub_sport") or "") in ("treadmill", "indoor_running") or "treadmill" in (r.get("name") or "").lower()


def run_load(r, tp, hrmax):
    import execution       # imported here because execution imports this module
    return execution.load(execution.actual_zones([r], tp, hrmax, False))


def form(today, tp, hrmax, show=120):
    """Daily load, fitness, fatigue and form for the last `show` days."""
    start = today - dt.timedelta(days=show + 3 * FIT_DAYS)
    by = {}
    for r in assess.load_runs(start, today + dt.timedelta(days=1)):
        by[r["date"]] = by.get(r["date"], 0.0) + run_load(r, tp, hrmax)
    if not by:
        return None
    kf, ka = 1 - math.exp(-1 / FIT_DAYS), 1 - math.exp(-1 / FAT_DAYS)
    fit = fat = 0.0
    out, d = [], start
    while d <= today:
        form_today = fit - fat                 # form going into the day: yesterday's fitness minus yesterday's fatigue
        x = by.get(d, 0.0)
        fit, fat = fit + kf * (x - fit), fat + ka * (x - fat)
        if d > today - dt.timedelta(days=show):
            out.append({"date": d.isoformat(), "load": round(x), "fitness": round(fit, 1), "fatigue": round(fat, 1), "form": round(form_today, 1)})
        d += dt.timedelta(days=1)
    now = out[-1]
    wk = lambda a, b: sum(x["load"] for x in out[len(out) - b:len(out) - a] or [])
    return {"days": out, "fitness": now["fitness"], "fatigue": now["fatigue"], "form": round(now["fitness"] - now["fatigue"], 1),
            "week": wk(0, 7), "prev_week": wk(7, 14), "fitness_4w_ago": out[-29]["fitness"] if len(out) > 29 else None}


def spikes(today, units="mi"):
    """Runs, done or planned this week, more than 10% longer than the longest run of the 30 days before them."""
    out = []
    u = (lambda m: f"{m:.1f} mi") if units == "mi" else (lambda m: f"{m * 1.609344:.1f} km")
    runs = db.rows("SELECT date, dist_m FROM activities WHERE sport='running' AND dist_m>0 AND date>=? ORDER BY date", ((today - dt.timedelta(days=45)).isoformat(),))
    mi = [(dt.date.fromisoformat(r["date"]), r["dist_m"] / MI) for r in runs]

    def longest(day):
        return max([m for d, m in mi if day - dt.timedelta(days=30) <= d < day], default=0.0)

    for d, m in mi:
        ref = longest(d)
        if d >= today - dt.timedelta(days=6) and ref >= 3 and m > SPIKE * ref:
            out.append({"kind": "spike", "date": d.isoformat(), "text": f"Your run on {d:%a %-d %b} was {u(m)}, {100 * (m / ref - 1):.0f}% longer than your longest run in the 30 days before it ({u(ref)}). "
                        "A jump of more than 10% in a single run is linked with more overuse injuries. Keep the next few days easy."})
    ref = longest(today)
    for p in db.rows("SELECT date, miles, label FROM plan WHERE date>=? AND date<? AND miles>0 ORDER BY date", (today.isoformat(), (today + dt.timedelta(days=7)).isoformat())):
        if ref >= 3 and p["miles"] > SPIKE * ref:
            d = dt.date.fromisoformat(p["date"])
            out.append({"kind": "planned", "date": p["date"], "text": f"{p['label']} on {d:%a %-d %b} is planned at {u(p['miles'])}, {100 * (p['miles'] / ref - 1):.0f}% longer than your longest run in the last 30 days ({u(ref)}). "
                        f"Staying within 10% would be {u(SPIKE * ref)}."})
            break
    return out


def drift(series):
    """Aerobic drift for a steady run: how much pace per heartbeat fell from the first half to the second, as a percentage.

    The first 10 minutes are left out (heart rate is still rising). None unless there are 40 minutes of running with heart rate after that.
    `series` is [[seconds, metres per second, heart rate], ...].
    """
    pts = [s for s in series or [] if s[0] >= 600 and s[1] and s[1] > 1.5 and s[2]]
    if len(pts) < 60 or pts[-1][0] - pts[0][0] < 2400:
        return None
    half = len(pts) // 2
    eff = lambda xs: (sum(x[1] for x in xs) / len(xs)) / (sum(x[2] for x in xs) / len(xs))
    a, b = eff(pts[:half]), eff(pts[half:])
    return round(100 * (a / b - 1), 1)


def drift_history(today, weeks=16, min_minutes=70, limit=10):
    """Aerobic drift on each long steady run."""
    plan = {r["date"]: r["type"] for r in db.rows("SELECT date,type FROM plan WHERE date>=?", ((today - dt.timedelta(weeks=weeks)).isoformat(),))}
    out = []
    for r in assess.load_runs(today - dt.timedelta(weeks=weeks), today + dt.timedelta(days=1)):
        if (r.get("timer_s") or 0) < min_minutes * 60 or plan.get(r["date"].isoformat()) in ("Key", "Race") or treadmill(r) or r.get("sub_sport") == "trail":
            continue
        d = drift(r.get("series"))
        if d is not None:
            out.append({"date": r["date"].isoformat(), "mi": round(r["mi"], 1), "minutes": round(r["timer_s"] / 60), "drift": d})
    return out[-limit:]


def fuel(minutes, per_hour=None, gel_g=25, race=False):
    """A fuelling outline for a run of `minutes`. None for runs under 75 minutes, which need none."""
    if minutes < 75:
        return None
    guide = 30 if minutes <= 120 else 60 if minutes <= 150 else 90
    g = per_hour or (30 if minutes <= 120 else 60)
    first = 30
    total = g * (minutes - first) / 60
    n = max(1, round(total / gel_g))
    gap = max(15, round((minutes - first - 10) / n / 5) * 5) if n > 1 else None
    return {"minutes": round(minutes), "per_hour": g, "guide": guide, "total_g": round(n * gel_g), "gels": n, "gel_g": gel_g, "first_min": first, "every_min": gap, "race": race,
            "text": f"{g} g of carbohydrate an hour: {n} gel{'s' if n != 1 else ''} of {gel_g} g, the first at {first} minutes" + (f", then one every {gap} minutes" if gap else "") + ". Take each with water."}


def note_carbs(note):
    m = re.search(r"(\d{2,3}) g of carbohydrate an hour", note or "")
    return int(m.group(1)) if m else None


def shoes(units="mi"):
    """Each pair of shoes with the miles run in it. A pair counts the runs from its start date until the next pair's start date."""
    rows = db.rows("SELECT * FROM shoes ORDER BY start")
    out = []
    for i, s in enumerate(rows):
        end = s["retired"] or (rows[i + 1]["start"] if i + 1 < len(rows) else "9999")
        m = db.rows("SELECT SUM(dist_m) m, COUNT(*) n FROM activities WHERE sport='running' AND date>=? AND date<?", (s["start"], end))[0]
        miles = (s["start_miles"] or 0) + (m["m"] or 0) / MI
        k = 1 if units == "mi" else 1.609344
        out.append({"id": s["id"], "name": s["name"], "start": s["start"], "retired": s["retired"], "current": i == len(rows) - 1 and not s["retired"],
                    "dist": round(miles * k), "runs": m["n"], "alert": round(s["alert_miles"] * k) if s["alert_miles"] else None,
                    "over": bool(s["alert_miles"] and miles >= s["alert_miles"])})
    return out[::-1]


def warnings(today, units="mi"):
    out = spikes(today, units)
    for s in shoes(units):
        if s["current"] and s["over"]:
            out.append({"kind": "shoes", "date": today.isoformat(), "text": f"{s['name']} have passed the {s['alert']} {units} you set as their limit ({s['dist']} {units})."})
    return out
