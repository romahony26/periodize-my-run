"""Things worth knowing that the plan itself does not show: load and form, single-run spikes, aerobic drift, fuelling, shoes.

Sources, where there is one:
  - Load is Lucia's TRIMP (minutes in three zones weighted 1, 2, 3), the same measure the execution score uses.
  - Fitness and fatigue are Banister's impulse-response model in its usual simplified form: running averages of daily load
    that fade over 42 and 7 days. Form is fitness minus fatigue. The 42 and 7 are the conventional values, not fitted to the athlete.
  - Spike warning: Frandsen and colleagues (2025, 5,200 runners): a run more than 10% longer than the longest run of the previous
    30 days went with more overuse injuries. The same study found no link with week-to-week mileage change, so there is no weekly warning.
  - Fuelling: Jeukendrup (2014): about 30 g of carbohydrate an hour for 1-2 hours, up to 60 g for 2-3 hours, up to 90 g beyond 2.5 hours.
  - Aerobic drift under 5% is a common coaching rule of thumb, not a research threshold.
  - Run timing: Leota and colleagues (2025, 14,689 people): hard exercise ending within 4 hours of sleep went with later, shorter sleep
    and lower overnight HRV. Sargent and colleagues (2014): early training cuts sleep. Bone stress injury by sex: Hollander and colleagues (2021).
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


WARM_WBGT = 18      # above this, heat raises heart-rate drift by itself, so the run is left out of the durability trend
LATE_H = 4           # Leota and colleagues (2025): hard exercise ending within 4 hours of sleep went with later, shorter sleep and lower overnight HRV
EARLY = 7 * 60       # a run starting before 07:00 counts as early


def _clock(minutes):
    return f"{int(minutes) // 60 % 24:02d}:{int(minutes) % 60:02d}"


def _median(xs):
    xs = sorted(xs)
    return (xs[len(xs) // 2] + xs[(len(xs) - 1) // 2]) / 2 if xs else None


def timing(today, hrmax=None, short_sleep_h=6.0):
    """When the athlete runs, and what that does to sleep. Feedback only: nothing here changes the plan.

    Returns {"usual", "parts", "notes": [text], "watch": text or None}, or None with fewer than 8 runs with a start time in 16 weeks.
    """
    since = today - dt.timedelta(weeks=16)
    plan = {r["date"]: r["type"] for r in db.rows("SELECT date,type FROM plan WHERE date>=?", (since.isoformat(),))}
    nights = {r["date"]: r for r in db.rows("SELECT date,sleep_h,hrv,sleep_start FROM daily WHERE date>=?", (since.isoformat(),))}
    runs = []
    for r in db.rows("SELECT start,date,timer_s,avg_hr FROM activities WHERE sport='running' AND dist_m>0 AND date>=? AND start IS NOT NULL ORDER BY start", (since.isoformat(),)):
        try:
            t = dt.datetime.fromisoformat(str(r["start"]))
        except ValueError:
            continue
        t = (t if t.tzinfo else t.replace(tzinfo=dt.UTC)).astimezone().replace(tzinfo=None)      # stored in GMT; shown in local time
        secs = r["timer_s"] or 0
        hard = plan.get(r["date"]) in ("Key", "Race") or secs >= 5400 or bool(hrmax and r["avg_hr"] and r["avg_hr"] >= 0.80 * hrmax and secs >= 1200)
        runs.append({"day": t.date(), "start": t.hour * 60 + t.minute, "end": t + dt.timedelta(seconds=secs), "hard": hard})
    if len(runs) < 8:
        return None
    last8 = [r for r in runs if r["day"] > today - dt.timedelta(weeks=8)] or runs
    share = lambda f: round(100 * sum(1 for r in last8 if f(r["start"])) / len(last8))
    out = {"usual": _clock(_median([r["start"] for r in last8])), "notes": [], "watch": None,
           "parts": {"morning": share(lambda m: m < 9 * 60), "day": share(lambda m: 9 * 60 <= m < 17 * 60), "evening": share(lambda m: m >= 17 * 60)}}

    # a shift in the usual time: reported, not judged (no study has tested what such a shift means)
    cut = today - dt.timedelta(weeks=4)
    now, before = [r["start"] for r in runs if r["day"] > cut], [r["start"] for r in runs if r["day"] <= cut]
    if len(now) >= 6 and len(before) >= 6 and abs(_median(now) - _median(before)) >= 60:
        d = _median(now) - _median(before)
        out["notes"].append(f"Over the last four weeks your runs have started about {abs(d) / 60:.1f} hours {'later' if d > 0 else 'earlier'} than in the three months before "
                            f"({_clock(_median(now))} against {_clock(_median(before))}). This is shown as a pattern only: no study has tested what such a shift means.")

    # hard runs close to sleep, measured against the athlete's own nights
    known = []
    for n in nights.values():
        if n["sleep_start"]:
            h, m = map(int, n["sleep_start"].split(":"))
            known.append(h * 60 + m + (1440 if h < 15 else 0))       # minutes after midnight of the evening before; past midnight runs on
    usual_bed = _median(known) if len(known) >= 5 else None

    def gap_h(r):
        n = nights.get((r["day"] + dt.timedelta(days=1)).isoformat())       # Garmin files a night under the morning it ends
        bed = usual_bed
        if n and n["sleep_start"]:
            h, m = map(int, n["sleep_start"].split(":"))
            bed = h * 60 + m + (1440 if h < 15 else 0)
        if bed is None:
            return None
        return (dt.datetime.combine(r["day"], dt.time()) + dt.timedelta(minutes=bed) - r["end"]).total_seconds() / 3600

    late, other = [], []
    for r in runs:
        n, g = nights.get((r["day"] + dt.timedelta(days=1)).isoformat()), gap_h(r)
        if g is None or not n or not n["sleep_h"]:
            continue
        (late if r["hard"] and 0 <= g < LATE_H else other).append(n)
    if len(late) >= 3 and len(other) >= 8:
        ds = 60 * (sum(n["sleep_h"] for n in late) / len(late) - sum(n["sleep_h"] for n in other) / len(other))
        text = (f"After hard runs that ended within {LATE_H} hours of sleep ({len(late)} nights) you slept {abs(ds):.0f} minutes "
                f"{'less' if ds < 0 else 'more'} than after your other runs")
        hl, ho = [n["hrv"] for n in late if n["hrv"]], [n["hrv"] for n in other if n["hrv"]]
        if len(hl) >= 3 and len(ho) >= 8:
            dh = sum(hl) / len(hl) - sum(ho) / len(ho)
            text += f", and overnight HRV was {abs(dh):.0f} ms {'lower' if dh < 0 else 'higher'}"
        out["notes"].append(text + ". In a study of 14,689 people, hard exercise ending within four hours of sleep went with later, shorter sleep and lower HRV; "
                                   "easy running in the evening did not.")
    y = [r for r in runs if r["day"] == today - dt.timedelta(days=1) and r["hard"]]
    if y and (g := gap_h(y[-1])) is not None and 0 <= g < LATE_H:
        out["watch"] = (f"Yesterday's hard run ended about {g:.1f} hours before you slept. Hard running within four hours of sleep is linked with shorter sleep "
                        "and lower overnight HRV, so read this morning's numbers with that in mind.")

    # early runs after a short night
    early = [r for r in runs if r["day"] > cut and r["start"] < EARLY]
    short = [r for r in early if (nights.get(r["day"].isoformat()) or {"sleep_h": None})["sleep_h"] and nights[r["day"].isoformat()]["sleep_h"] < short_sleep_h]
    if len(short) >= 2:
        out["notes"].append(f"{len(short)} of your {len(early)} runs before {_clock(EARLY)} in the last four weeks came after under {short_sleep_h:g} hours of sleep. "
                            "Early training cuts sleep unless bedtime moves earlier with it, and short sleep slows recovery.")
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
            out.append({"date": r["date"].isoformat(), "mi": round(r["mi"], 1), "minutes": round(r["timer_s"] / 60), "drift": d,
                        "warm": bool(r.get("wx") and r["wx"].get("wbgt", 0) > WARM_WBGT)})
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


def warnings(today, units="mi", sex=None, hrmax=None):
    out = spikes(today, units)
    if sex == "F" and any(w["kind"] == "spike" for w in out):
        out.append({"kind": "bone", "date": today.isoformat(), "text": "Bone stress injuries are about twice as common in women runners as in men. "
                    "Pain on a bone that sharpens as a run goes on, or that you can press with one finger, is a reason to stop and have it looked at."})
    t = timing(today, hrmax)
    if t and t["watch"]:
        out.append({"kind": "timing", "date": today.isoformat(), "text": t["watch"]})
    for s in shoes(units):
        if s["current"] and s["over"]:
            out.append({"kind": "shoes", "date": today.isoformat(), "text": f"{s['name']} have passed the {s['alert']} {units} you set as their limit ({s['dist']} {units})."})
    return out
