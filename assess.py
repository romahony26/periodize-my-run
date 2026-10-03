"""Work out where the athlete is from the eight weeks before a given Monday.

Plain arithmetic on stored run summaries and health values. No AI, no network.
"""
import datetime as dt
import json
import math
import statistics

import db
import equiv
from fitrun import BIN, HR_LO, HR_STEP

MI = 1609.344
WINDOW_WEEKS = 8

# Threshold speed implied by a best effort: (kind, key, factor on the effort's speed). Rules of thumb.
EFFORT_TO_THRESHOLD = [("dur", "3600", 1.00), ("dur", "1800", 0.97), ("dur", "1200", 0.95),
                       ("dist", "5000", 0.926), ("dist", "10000", 0.966), ("dist", "16093", 1.00), ("dist", "21097", 1.03)]
# Training speeds as a fraction of threshold speed
ZONES = {"easy": (0.76, 0.81), "steady": (0.82, 0.86), "mp": (0.94, 0.94), "hmp": (0.985, 0.985),
         "threshold": (0.99, 1.01), "10k": (1.035, 1.035), "5k": (1.08, 1.08)}
RACE_FACTOR = [(4.0, 1.08), (7.0, 1.035), (11.0, 1.00), (14.0, 0.985), (99.0, 0.94)]   # race miles up to -> fraction of threshold speed
MP_BAND = (0.91, 0.97)
T_FLOOR = 0.97


def race_factor(miles):
    if miles > 30:   # ultra: marathon speed faded with distance. Rough, and blind to terrain.
        return 0.94 * (26.2 / miles) ** 0.12
    return next(f for lim, f in RACE_FACTOR if miles <= lim)


def band(run, lo, hi, what="m_by_speed"):
    h = run.get(what)
    return sum(x for i, x in enumerate(h) if lo <= (i + 0.5) * BIN < hi) if h else 0.0


def hr_band(run, lo, hi):
    """(seconds, metres) of a run with heart rate in [lo, hi). Metres are grade-adjusted (what the running was worth on the flat) when the run's altitude is trustworthy."""
    s = run.get("hr_sec")
    m = run.get("hr_gap") if run.get("gap_ok") and run.get("hr_gap") else run.get("hr_m")
    if not s or len(s) < 20:
        return 0.0, 0.0
    idx = [i for i in range(len(s)) if lo <= HR_LO + i * HR_STEP < hi]
    return sum(s[i] for i in idx), sum(m[i] for i in idx)


def hr_speed_line(runs, hrmax):
    """The athlete's own straight line of speed against heart rate, from steady running at 65-92% of maximum.

    Below threshold, speed rises close to linearly with heart rate. Fitting that line to the athlete's own runs and reading it at
    threshold heart rate gives a threshold speed with no constant borrowed from anyone else.
    Needs at least three 5-bpm heart rate steps with 5 minutes of running each.
    """
    sec, met = {}, {}
    for r in runs:
        s = r.get("hr_sec")
        m = r.get("hr_gap") if r.get("gap_ok") and r.get("hr_gap") else r.get("hr_m")
        if not s or len(s) < 20:
            continue
        for i in range(len(s)):
            hr = HR_LO + i * HR_STEP + HR_STEP / 2
            if 0.65 * hrmax <= hr <= 0.92 * hrmax:
                sec[hr] = sec.get(hr, 0) + s[i]
                met[hr] = met.get(hr, 0) + m[i]
    pts = [(hr, met[hr] / sec[hr], sec[hr]) for hr in sorted(sec) if sec[hr] >= 300]
    if len(pts) < 3:
        return None
    w = sum(p[2] for p in pts)
    mx, my = sum(p[0] * p[2] for p in pts) / w, sum(p[1] * p[2] for p in pts) / w
    sxx = sum(p[2] * (p[0] - mx) ** 2 for p in pts)
    if sxx <= 0:
        return None
    slope = sum(p[2] * (p[0] - mx) * (p[1] - my) for p in pts) / sxx
    if slope <= 0:
        return None
    return {"at": lambda hr: my + slope * (hr - mx), "points": len(pts), "minutes": w / 60, "slope": slope}


def usable(run, c):
    """Can this run's pace at a heart rate be compared with others? Road runs: yes if flat, or if the hills can be adjusted for. Trail and treadmill runs: no."""
    if (run.get("sub_sport") or "") in ("treadmill", "indoor_running"):
        return False
    if run.get("sub_sport") == "trail" or "trail" in (run.get("name") or "").lower():
        return False      # rough ground, walking and very long days slow a trail run in ways gradient alone does not explain
    if run.get("gap_ok") and run.get("hr_gap"):
        return True
    return run["ascent_m"] is None or run["ascent_m"] / (run["dist_m"] / 1000) < c["hilly_m_per_km"]


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def offrun_steps(start, end):
    """{date: steps taken outside runs} for days that have a step count. Everyday walking is training load the plan does not schedule."""
    run = {r["date"]: r["s"] or 0 for r in db.rows("SELECT date, SUM(steps) s FROM activities WHERE sport='running' AND date>=? AND date<? GROUP BY date",
                                                   (start.isoformat(), end.isoformat()))}
    return {r["date"]: max(r["steps"] - run.get(r["date"], 0), 0)
            for r in db.rows("SELECT date, steps FROM daily WHERE steps IS NOT NULL AND date>=? AND date<?", (start.isoformat(), end.isoformat()))}


def steps_summary(day, c):
    """Steps outside runs: the 7 days before `day` against the 7 weeks before that."""
    s = offrun_steps(day - dt.timedelta(days=57), day)
    week = [s[k] for k in ((day - dt.timedelta(days=i)).isoformat() for i in range(1, 8)) if k in s]
    base = [s[k] for k in ((day - dt.timedelta(days=i)).isoformat() for i in range(8, 57)) if k in s]
    if len(week) < 4 or len(base) < 14:
        return None
    return {"week": sum(week) / len(week), "base": statistics.median(base), "sd": statistics.pstdev(base),
            "yesterday": s.get((day - dt.timedelta(days=1)).isoformat())}


def race_evidence(monday, weeks=26):
    """Threshold speed implied by the athlete's own races in the last half year, faded for time since.

    The fade depends on their data: 0.15% a week if weekly running since the race has stayed at 80% or more of the level before it,
    0.5% a week if it has dropped below that.
    """
    out = []
    since = monday - dt.timedelta(weeks=weeks)
    for r in db.rows("SELECT * FROM results WHERE hidden=0 AND date>=? AND date<?", (since.isoformat(), monday.isoformat())):
        day = dt.date.fromisoformat(r["date"])
        wk = (monday - day).days / 7

        def miles(a, b):
            m = db.rows("SELECT SUM(dist_m) m FROM activities WHERE sport='running' AND date>=? AND date<?", (a.isoformat(), b.isoformat()))[0]["m"] or 0
            return m / MI / max((b - a).days / 7, 1)

        before, after = miles(day - dt.timedelta(days=28), day), miles(day + dt.timedelta(days=1), monday)
        kept = after >= 0.8 * before if before else True
        fade = (0.0015 if kept else 0.005) * max(wk - 2, 0)
        v = equiv.threshold_speed(equiv.index(r["dist_m"], r["time_s"])) * (1 - fade)
        out.append((v, f"your {r['name'].split(' · ')[0]} {wk:.0f} weeks ago, faded {fade:.1%} ({'training kept up' if kept else 'training dropped'} since)", day))
    return out


def load_runs(start, end):
    out = []
    trust = db.get("altitude_trust") or {}
    for r in db.rows("SELECT * FROM activities WHERE sport='running' AND date>=? AND date<? AND dist_m>0 ORDER BY start", (start.isoformat(), end.isoformat())):
        d = json.loads(r["detail"]) if r["detail"] else {}
        if d.get("error"):
            d = {}
        # grade adjustment only where the altitude is believable: a trusted watch, and this run's own loop check (if it has one) passes
        if d.get("gap_ok") and (not trust.get(d.get("device"), {}).get("trusted", True) or (d.get("loop_alt_err") or 0) > 20):
            d["gap_ok"] = False
        d.update({"id": r["id"], "date": dt.date.fromisoformat(r["date"]), "name": r["name"], "mi": r["dist_m"] / MI,
                  "dist_m": d.get("dist_m") or r["dist_m"], "timer_s": d.get("timer_s") or r["timer_s"],
                  "ascent_m": d.get("ascent_m") if d.get("ascent_m") is not None else r["ascent_m"],
                  "avg_hr": d.get("avg_hr") or r["avg_hr"], "best5k": r["best5k"], "best10k": r["best10k"],
                  "start_utc": r["start"], "max_hr_sum": r["max_hr"], "training_effect": r["training_effect"], "garmin_load": r["garmin_load"]})
        out.append(d)
    return out


def detraining(days_off):
    """Share of threshold fitness lost after `days_off` days without running.

    Aerobic fitness holds for the first week or so, then falls: trained runners lose roughly 4-14% of their aerobic capacity over
    two to four weeks without training, and recent gains go first (Mujika and Padilla, 2000). The values here (nothing for 10
    days, then 0.35% a day, at most 12%) are this project's middle-of-the-range reading of that. [P]
    """
    return min(max(days_off - 10, 0) * 0.0035, 0.12)


def assess(c, L, monday, prev_tp=None):
    """c: settings, L: personal limits, monday: first day of the week being planned."""
    R = load_runs(monday - dt.timedelta(weeks=WINDOW_WEEKS), monday)
    daily = {r["date"]: r for r in db.rows("SELECT * FROM daily WHERE date>=?", ((monday - dt.timedelta(days=60)).isoformat(),))}

    # ---- threshold speed ----
    cands = []
    for r in R:
        if r.get("glitch") or (r.get("sub_sport") or "") in ("treadmill", "indoor_running"):
            continue      # a treadmill's distance on a wrist watch is a guess
        for kind, key, f in EFFORT_TO_THRESHOLD:
            if kind == "dur":
                m = (r.get("best_dur") or {}).get(key)
                v = m / int(key) if m else None
            else:
                s = (r.get("best_dist") or {}).get(key) or (r.get("best5k") if key == "5000" else r.get("best10k") if key == "10000" else None)
                v = int(key) / s if s else None
            if v:
                cands.append((v * f, f"best {int(key) // 60} min" if kind == "dur" else f"best {int(key) / 1000:g} km", r["date"]))
    flat = [r for r in R if usable(r, c)]
    recent = [r for r in flat if r["date"] >= monday - dt.timedelta(days=28)]
    fit = hr_speed_line(recent, L["hrmax"])
    hr_v = fit["at"](c["threshold_hr_fraction"] * L["hrmax"]) if fit else None
    if hr_v:
        cands.append((hr_v * c.get("threshold_correction", 1.0),
                      f"your pace-to-heart-rate line over the last 28 days ({fit['minutes']:.0f} min across {fit['points']} heart rates), read at {c['threshold_hr_fraction'] * L['hrmax']:.0f} bpm", None))
    for ev in race_evidence(monday):
        cands.append(ev)
    glt = db.get("garmin_lt")       # the watch's own threshold estimate counts while it is fresh (six weeks)
    if glt and glt.get("speed") and glt.get("date"):
        when = dt.date.fromisoformat(glt["date"][:10])
        if 0 <= (monday - when).days <= 42:
            cands.append((glt["speed"], "your watch's own threshold estimate", when))
    if cands:
        raw, why, when = max(cands, key=lambda x: x[0])
        why = why + (f" on {when:%-d %b}" if when else "")
    else:
        raw, why = prev_tp, "no evidence; carried forward"
    if raw is None:
        return None
    seed = prev_tp or raw
    tp = min(max(raw, seed * (1 - c["max_weekly_loss"])), seed * (1 + c["max_weekly_gain"]))
    last = max((r["date"] for r in R if r["mi"] >= 1), default=None)
    off = (monday - last).days - 1 if last else WINDOW_WEEKS * 7
    fade = detraining(off) - detraining(off - 7)     # this week's share of the loss, so a long break adds up week by week
    if fade > 0:
        tp = min(tp, seed * (1 - fade))
        why = f"no running for {off} days: fitness eased {fade:.1%} this week, as aerobic fitness fades during a break"

    for r in R:
        r["t_min"] = band(r, T_FLOOR * tp, 99, "sec_by_speed") / 60
        r["mp_mi"] = band(r, MP_BAND[0] * tp, MP_BAND[1] * tp) / MI
        r["fast_mi"] = band(r, MP_BAND[0] * tp, 99) / MI
    weeks = []
    for k in range(WINDOW_WEEKS, 0, -1):
        ws = monday - dt.timedelta(weeks=k)
        wr = [r for r in R if ws <= r["date"] < ws + dt.timedelta(days=7)]
        weeks.append({"start": ws, "mi": sum(r["mi"] for r in wr), "runs": len(wr), "long": max([r["mi"] for r in wr], default=0.0),
                      "fast_mi": sum(r["fast_mi"] for r in wr), "t_min": sum(r["t_min"] for r in wr)})

    def since(days):
        return [r for r in R if r["date"] >= monday - dt.timedelta(days=days)]

    r21 = since(21)
    lthr = c.get("aero_lthr")
    lthr = int(lthr // 5 * 5) if lthr else None
    long_min = 0.7 * L["long_run_cap_specific"]
    mp_longs = [r for r in since(35) if r["mi"] >= long_min and r["mp_mi"] >= 5]
    st = {"monday": monday, "n_runs": len(R), "weeks": weeks, "tp": tp, "tp_raw": raw, "tp_why": why, "tp_prev": seed,
          "longest_30d": max([r["mi"] for r in since(30)], default=0.0), "longest_10d": max([r["mi"] for r in since(10)], default=0.0),
          "prev_t_min": max([r["t_min"] for r in r21], default=0.0),
          "prev_mp_mid": max([r["mp_mi"] for r in r21 if r["mi"] < long_min], default=0.0),
          "prev_mp_long": max([r["mp_mi"] for r in mp_longs], default=0.0),
          "prev_lthr_mi": max([hr_band(r, lthr, lthr + 10)[1] / MI for r in r21], default=0.0) if lthr else 0.0,
          "last_mp_long": max([r["date"] for r in mp_longs], default=None)}

    # ---- specific endurance (used for the marathon and half marathon projection) ----
    longs = sum(1 for r in R if r["mi"] >= 0.75 * L["long_run_cap_specific"])
    parts = {"long runs": min(longs / 4, 1), "miles at race pace or faster": min(sum(w["fast_mi"] for w in weeks) / L["peak_miles"], 1),
             "weekly miles": min((mean([w["mi"] for w in weeks]) or 0) / L["peak_miles"], 1)}
    st["endurance"], st["endurance_parts"] = sum(parts.values()) / len(parts), parts

    # ---- recovery ----
    def vals(key, a, b):
        return [v for v in ((daily.get((monday - dt.timedelta(days=i)).isoformat()) or {}).get(key) for i in range(a, b)) if v]

    flags, health = [], {}
    rhr7, base = mean(vals("rhr", 1, 8)), vals("rhr", 8, 57)
    if rhr7 and len(base) >= 14:
        b = statistics.median(base)
        health["rhr"] = (rhr7, b)
        if rhr7 - b >= c["rhr_rise_bpm"]:
            flags.append(f"resting heart rate {rhr7:.0f}, {rhr7 - b:.0f} above your normal of {b:.0f}")
    hrv7, base = mean(vals("hrv", 1, 8)), vals("hrv", 8, 57)
    if hrv7 and len(base) >= 14:
        b = mean(base)
        health["hrv"] = (hrv7, b)
        if hrv7 < b * c["hrv_drop_fraction"]:
            flags.append(f"overnight HRV {hrv7:.0f}, below your normal of {b:.0f}")
    sl7 = mean(vals("sleep_h", 1, 8))
    if sl7:
        health["sleep"] = sl7
        if sl7 < c["sleep_7night_min_h"]:
            flags.append(f"sleep averaged {sl7:.1f} h over the last 7 nights")
    w = vals("weight_kg", 1, 8)
    if w:
        health["weight_kg"] = mean(w)
    sp = steps_summary(monday, c)
    if sp:
        health["steps"] = (sp["week"], sp["base"])
        if sp["week"] >= sp["base"] + max(sp["sd"], 1500):   # a whole week a standard deviation above this athlete's normal
            flags.append(f"you have been on your feet much more than usual outside your runs ({sp['week']:,.0f} steps a day against a normal {sp['base']:,.0f})")
    elo, ehi = L["easy_hr_band"]

    def easy_v(rs):
        t = [hr_band(r, elo, ehi) for r in rs]
        s, m = (sum(x) for x in zip(*t, strict=True)) if t else (0, 0)
        return m / s if s >= 1200 else None

    now = easy_v([r for r in flat if r["date"] >= monday - dt.timedelta(days=14)])
    before = easy_v([r for r in flat if r["date"] < monday - dt.timedelta(days=14)])
    if now and before:
        health["easy_pace"] = (now, before)
        if now < before * (1 - c["easy_pace_drop_fraction"]):
            flags.append(f"easy pace at {elo}–{ehi} bpm has slowed by more than 3% in two weeks")
    st["flags"], st["health"] = flags, health
    return st


def race_time(v_ref, miles, endurance, c, slope):
    """(time with the current endurance, time with endurance fully built) for an athlete whose race index at an hour's racing is v_ref.

    `slope` is the athlete's own profile: the index shifts by that much per unit of ln(distance) away from the distance they cover in an hour.
    """
    d_ref = equiv.threshold_speed(v_ref) * 3600

    def at(m):
        return equiv.predict(v_ref + slope * math.log(m * MI / d_ref), m * MI)

    if miles <= 30:
        full = at(miles)
    else:   # ultra: the athlete's marathon speed, faded with distance. Rough, and blind to terrain.
        full = miles * MI / (26.219 * MI / at(26.219) * (26.219 / miles) ** 0.12)
    pen = c["max_endurance_penalty"] * (1 - endurance) * (1.0 if miles >= 20 else 0.4 if miles >= 10 else 0.0)
    return full * (1 + pen), full


def projection(st, c, miles):
    """Predicted time in seconds for a race of `miles` if run today, and at the same speed with endurance built."""
    slope = ((db.get("model") or {}).get("distance_slope") or {}).get("value", 0.0)
    return race_time(equiv.from_threshold(st["tp"]), miles, st["endurance"], c, slope)
