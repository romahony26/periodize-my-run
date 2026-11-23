"""Recovery from the watch's own health records: last night, the habits behind it, an illness watch, and what to do today and tonight.

Everything here is read from data the app already holds (the `daily` table, filled from Garmin), so nothing is asked of the runner.
The evidence and the limits of each measure are in PRINCIPLES.md section 9 (principles 118 to 123) and in the research report
"Periodize recovery tracking". In short: sleep length, timing and regularity, resting heart rate, overnight HRV and breathing rate are
used; Body Battery, Garmin's stress score and the sleep stages are shown or left out, never used to change a decision, because no
independent study validates them.

`parse_night` and `store` are shared by the ordinary sync and by the fill from the raw records. `illness` is a pure function the
readiness check calls. `report` builds the whole Recovery page.
"""
import datetime as dt
import statistics
from statistics import mean

import db

COLS = ("resp", "sleep_stress", "awake_s", "deep_s", "rem_s", "awake_n", "bb_gain", "sleep_end", "need_min", "avg_stress")
HRV_NIGHTS = 28            # nights of HRV before its normal range means anything (as in engine.readiness)
BASE_DAYS = 60
ILLNESS_NEED = 2           # of resting heart rate, breathing rate and HRV moving the wrong way over 3 nights  [P]
RHR_UP = 3                 # beats above the runner's normal over 3 nights                                    [P]
Z_UP = 1.0                 # spreads above (breathing) or below (HRV) the runner's normal                      [P]
SD_REGULAR, SD_IRREGULAR = 45, 60    # minutes of bedtime spread: regular under, irregular over             [P]
NEED_MIN_H, NEED_MAX_H, NEED_DEFAULT_H = 7.0, 9.0, 8.0   # the 7 to 9 hour consensus (Walsh and colleagues, 2021); default where the runner has no history
LATE_H = 4                 # a run that ends within 4 hours of falling asleep (Leota and colleagues, 2025)
DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def _clock(ms):
    """'HH:MM' from the local-time milliseconds Garmin stores (the wall clock, stored as if it were GMT), or None."""
    return dt.datetime.fromtimestamp(ms / 1000, dt.UTC).strftime("%H:%M") if isinstance(ms, (int, float)) and ms > 0 else None


def parse_night(sleep, stats=None):
    """The recovery fields of one night from Garmin's sleep record (and the day's summary, for stress). Missing values are None."""
    sleep = sleep or {}
    dto = sleep.get("dailySleepDTO") or {}
    need = (dto.get("sleepNeed") or {}).get("actual")
    stress = (stats or {}).get("averageStressLevel")
    return {"resp": dto.get("averageRespirationValue") or None,
            "sleep_stress": dto.get("avgSleepStress") or None,
            "awake_s": dto.get("awakeSleepSeconds"), "deep_s": dto.get("deepSleepSeconds"), "rem_s": dto.get("remSleepSeconds"),
            "awake_n": dto.get("awakeCount"), "bb_gain": sleep.get("bodyBatteryChange"),
            "sleep_end": _clock(dto.get("sleepEndTimestampLocal")), "need_min": need if isinstance(need, (int, float)) and need > 0 else None,
            "avg_stress": stress if isinstance(stress, (int, float)) and stress >= 0 else None}


_KEEP = {k: f"UPDATE daily SET {k}=COALESCE({k},?) WHERE date=?" for k in COLS}      # fixed statements, one per column: no SQL is built from data
_SET = {k: f"UPDATE daily SET {k}=? WHERE date=?" for k in COLS}


def store(c, day, fields, replace=False):
    """Write the parsed fields into `daily`. A value already held is kept unless `replace`; nothing is written for an empty record."""
    new = {k: v for k, v in fields.items() if k in COLS and v is not None}
    if not new:
        return False
    c.execute("INSERT OR IGNORE INTO daily(date) VALUES(?)", (day,))
    for k, v in new.items():
        c.execute((_SET if replace else _KEEP)[k], (v, day))
    return True


# ---------------------------------------------------------------- the measures

def _vals(rows, today, key, a, b):
    """Values of `key` from `a` to `b` days ago (0 = this morning), skipping nights with none."""
    return [v for v in ((rows.get((today - dt.timedelta(days=i)).isoformat()) or {}).get(key) for i in range(a, b)) if v]


def _normal(rows, today, key, floor, skip, need=14):
    """(average, spread) over the 60 days before the last `skip` days, or None with too few nights."""
    base = _vals(rows, today, key, skip, skip + BASE_DAYS)
    return (mean(base), max(statistics.pstdev(base), floor)) if len(base) >= need else None


def illness(rows, today):
    """Is the body doing what it does at the start of an illness? Two of three signs, over the last three nights, each against the
    runner's own normal: resting heart rate up, overnight breathing rate up, HRV down. Resting heart rate and breathing rate rose
    before symptoms in wearable studies (Mishra and colleagues, 2020; Renteria and colleagues, 2024), and one sign alone is not
    specific, so two are needed. It is a prompt to be careful, never a diagnosis. Returns {"on", "signs", "reason", "needs"}."""
    signs = []
    r3, n = _vals(rows, today, "rhr", 0, 3), _normal(rows, today, "rhr", 1.5, 3)
    if n and len(r3) >= 2 and mean(r3) - n[0] >= RHR_UP:
        signs.append(f"resting heart rate {mean(r3):.0f}, {mean(r3) - n[0]:.0f} above your normal {n[0]:.0f}")
    b3, n = _vals(rows, today, "resp", 0, 3), _normal(rows, today, "resp", 0.4, 3)
    if n and len(b3) >= 2 and (mean(b3) - n[0]) / n[1] >= Z_UP:
        signs.append(f"breathing rate {mean(b3):.1f} a minute asleep, up from your normal {n[0]:.1f}")
    h3, n = _vals(rows, today, "hrv", 0, 3), _normal(rows, today, "hrv", 3.0, 3, HRV_NIGHTS)
    if n and len(h3) >= 2 and (mean(h3) - n[0]) / n[1] <= -Z_UP:
        signs.append(f"HRV {mean(h3):.0f}, below your normal range (about {n[0] - n[1]:.0f} to {n[0] + n[1]:.0f})")
    on = len(signs) >= ILLNESS_NEED
    return {"on": on, "signs": signs, "needs": ILLNESS_NEED,
            "reason": ("the last three nights look like the start of an illness: " + "; ".join(signs)) if on else ""}


def _mins(hhmm):
    """Minutes after 18:00 for a clock time, so that 23:30 and 01:30 sit two hours apart and not 22."""
    h, m = (int(x) for x in hhmm.split(":"))
    return (h * 60 + m - 18 * 60) % 1440


def _hhmm(m):
    m = int(round(m)) % 1440
    return f"{((m + 18 * 60) // 60) % 24:02d}:{(m + 18 * 60) % 60:02d}"


def _sd(xs):
    return statistics.pstdev(xs) if len(xs) >= 2 else 0.0


def need_hours(rows, today):
    """(hours, source): the runner's own sleep need, taken as the median of the nights they slept well (sleep score 80 or more) over the
    last 120 days, held between 7 and 9 hours; 8 hours where there are fewer than 20 such nights [P]."""
    good = [r["sleep_h"] for d, r in rows.items() if r.get("sleep_h") and (r.get("sleep_score") or 0) >= 80 and d < today.isoformat()]
    if len(good) >= 20:
        return min(max(statistics.median(good), NEED_MIN_H), NEED_MAX_H), "your own well-slept nights"
    return NEED_DEFAULT_H, "the 7 to 9 hour consensus"


def regularity(rows, today, nights=28):
    """Bedtime and wake time habits over the last `nights`: typical times, spread, and how far weekend nights sit from weekday nights."""
    ons, wks, wend, wday = [], [], [], []
    for i in range(nights):
        d = today - dt.timedelta(days=i)
        r = rows.get(d.isoformat()) or {}
        if r.get("sleep_start"):
            m = _mins(r["sleep_start"])
            ons.append(m)
            (wend if d.weekday() in (5, 6) else wday).append(m)      # the night that ends on a Saturday or Sunday morning is a free-day night
        if r.get("sleep_end"):
            wks.append(_mins(r["sleep_end"]))
    if len(ons) < 7:
        return None
    sd = _sd(ons[:14])
    shift = (mean(wend) - mean(wday)) if len(wend) >= 3 and len(wday) >= 8 else None
    return {"typical_bed": _hhmm(statistics.median(ons)), "typical_wake": _hhmm(statistics.median(wks)) if len(wks) >= 7 else None,
            "bed_sd_min": round(sd), "wake_sd_min": round(_sd(wks[:14])) if len(wks) >= 7 else None,
            "weekend_shift_min": round(shift) if shift is not None else None,
            "label": "regular" if sd < SD_REGULAR else "irregular" if sd >= SD_IRREGULAR else "mixed", "nights": len(ons)}


def weekday_pattern(rows, today, weeks=8):
    """Average sleep and HRV by the weekday the night ends on, over the last `weeks` weeks (a dip on one day is usually a habit)."""
    out = []
    for wd in range(7):
        days = [today - dt.timedelta(days=i) for i in range(weeks * 7) if (today - dt.timedelta(days=i)).weekday() == wd]
        s = [r["sleep_h"] for d in days if (r := rows.get(d.isoformat())) and r.get("sleep_h")]
        h = [r["hrv"] for d in days if (r := rows.get(d.isoformat())) and r.get("hrv")]
        out.append({"d": DAYS[wd], "sleep_h": round(mean(s), 1) if len(s) >= 3 else None, "hrv": round(mean(h)) if len(h) >= 3 else None})
    return out


def late_runs(today, rows, hrmax, days=150):
    """The runner's own late hard runs against the rest: the sleep of nights that began within 4 hours of a hard run's end.
    A hard run is one Garmin rates 3.5 or more for aerobic effect, or one averaging 80% of maximum heart rate or more.
    Needs at least 3 such nights and 10 others; None otherwise."""
    since = (today - dt.timedelta(days=days)).isoformat()
    runs = db.rows("SELECT start,timer_s,avg_hr,training_effect FROM activities WHERE sport='running' AND date>=? AND timer_s>=1800", (since,))
    late = set()
    for a in runs:
        if not ((a["training_effect"] or 0) >= 3.5 or (hrmax and (a["avg_hr"] or 0) >= 0.8 * hrmax)):
            continue
        try:
            end = dt.datetime.fromisoformat(a["start"]) + dt.timedelta(seconds=a["timer_s"] or 0)
        except (TypeError, ValueError):
            continue
        for night in (end.date(), end.date() + dt.timedelta(days=1)):    # the night after it ends on this date or the next, by when sleep starts
            r = rows.get(night.isoformat()) or {}
            if r.get("sleep_start") and r.get("sleep_h"):
                h, m = (int(x) for x in r["sleep_start"].split(":"))
                onset = dt.datetime.combine(night, dt.time(h, m)) - (dt.timedelta(days=1) if h >= 12 else dt.timedelta())
                if dt.timedelta() <= onset - end <= dt.timedelta(hours=LATE_H):
                    late.add(night.isoformat())
    a = [r["sleep_h"] for d, r in rows.items() if d in late and r.get("sleep_h")]
    b = [r["sleep_h"] for d, r in rows.items() if d not in late and d >= since and r.get("sleep_h")]
    if len(a) < 3 or len(b) < 10:
        return None
    return {"n": len(a), "late_h": round(mean(a), 1), "other_h": round(mean(b), 1), "diff_min": round((mean(a) - mean(b)) * 60)}


def after_long(today, rows, miles=10, days=240):
    """How the runner's own resting heart rate recovers after a long run: for each run of `miles` or more, the mornings until it is back within
    1 beat of the 60-day normal (up to 4). Returns the median, and None with fewer than 4 long runs that have the readings."""
    since = (today - dt.timedelta(days=days)).isoformat()
    runs = db.rows("SELECT date FROM activities WHERE sport='running' AND dist_m>=? AND date>=? ORDER BY date", (miles * 1609.34, since))
    took = []
    for a in runs:
        d0 = dt.date.fromisoformat(a["date"])
        if d0 > today - dt.timedelta(days=4):
            continue
        base = _normal(rows, d0, "rhr", 1.0, 0, 21)
        nxt = [(rows.get((d0 + dt.timedelta(days=k)).isoformat()) or {}).get("rhr") for k in (1, 2, 3, 4)]
        if not base or sum(x is not None for x in nxt) < 3:
            continue
        back = next((k for k, x in enumerate(nxt, 1) if x is not None and x - base[0] <= 1.0), 5)
        took.append(back)
    if len(took) < 4:
        return None
    return {"n": len(took), "median_days": statistics.median(took), "slow": sum(1 for t in took if t >= 4)}


# ---------------------------------------------------------------- the page

def _night(rows, today):
    """The most recent night with sleep recorded, today's or yesterday's."""
    for i in (0, 1):
        d = today - dt.timedelta(days=i)
        r = rows.get(d.isoformat()) or {}
        if r.get("sleep_h"):
            return d, r
    return None, None


def _r5(m):
    return int(round(m / 5.0)) * 5


def alarm_plan(rows, today, need_h, awake_min, plan_for=None, nights=3):
    """When to be asleep and when to set the alarm for tonight and the next two mornings, easing toward a steady schedule [P].

    The runner's wake time barely moves with their bedtime (in one runner's history it stayed at about 08:00 to 08:30 whether they fell asleep
    at 23:30 or after 01:30), so bedtime is the lever and the alarm is the anchor. The target alarm is the runner's own weekday wake time
    over the last 28 nights, on a 15-minute step and no later than 09:00, with weekends 30 minutes later: it never asks a late riser to
    get up earlier, because an earlier alarm without an earlier bedtime only cut their sleep. Sleep-by is the alarm less the need and the
    usual time awake in the night. From the median of the last seven bedtimes it steps 30 minutes earlier for tonight and 15 more each
    night, never past the target; the alarm is the later of the target and the wake time that gives the full need from that bedtime,
    held at the runner's usual wake time. Nothing here moves the bed-by earlier than the target, and with fewer than 7 nights it says nothing.
    `plan_for(date)` returns the session planned for a morning, or None."""
    ons, wkd, wke = [], [], []
    for i in range(28):
        d = today - dt.timedelta(days=i)
        r = rows.get(d.isoformat()) or {}
        if i < 7 and r.get("sleep_start"):
            ons.append(_mins(r["sleep_start"]))
        if r.get("sleep_end"):
            (wke if d.weekday() in (5, 6) else wkd).append(_mins(r["sleep_end"]))
    if len(ons) < 5 or len(wkd) < 5:
        return None
    recent = statistics.median(ons)
    typ_wkd = statistics.median(wkd)
    typ_wke = statistics.median(wke) if len(wke) >= 3 else typ_wkd + 30
    tgt_wkd = min(round(typ_wkd / 15) * 15, _mins("09:00"))
    gap = round(need_h * 60) + round(awake_min)
    out = []
    for i in range(nights):
        morning = today + dt.timedelta(days=i + 1)
        weekend = morning.weekday() in (5, 6)
        tgt_wake = tgt_wkd + 30 if weekend else tgt_wkd
        typ = max(typ_wke if weekend else typ_wkd, tgt_wake)
        tgt_bed = tgt_wake - gap
        bed = max(tgt_bed, recent - 30 - 15 * i)
        wake = tgt_wake if bed <= tgt_bed else max(tgt_wake, min(typ, bed + gap))
        s = plan_for(morning) if plan_for else None
        out.append({"date": morning.isoformat(), "day": DAYS[morning.weekday()], "bed_by": _hhmm(_r5(bed)), "alarm": _hhmm(_r5(wake)),
                    "hours": round((wake - bed - awake_min) / 60, 1), "at_target": bed <= tgt_bed, "session": s})
    return {"nights": out, "recent_bed": _hhmm(_r5(recent)), "target_alarm": _hhmm(_r5(tgt_wkd)), "target_alarm_weekend": _hhmm(_r5(tgt_wkd + 30)),
            "target_bed": _hhmm(_r5(tgt_wkd - gap)), "typical_wake": _hhmm(_r5(typ_wkd))}


def _tomorrow(today):
    p = db.rows("SELECT date,type,label,miles FROM plan WHERE date=?", ((today + dt.timedelta(days=1)).isoformat(),))
    return p[0] if p else None


def report(today=None, c=None):
    """Everything on the Recovery page. Cheap: it reads the database and the readiness check, never Garmin."""
    import engine
    today = today or dt.date.today()
    c = c or db.cfg()
    rows = {r["date"]: dict(r) for r in db.rows("SELECT * FROM daily WHERE date>=?", ((today - dt.timedelta(days=150)).isoformat(),))}
    rd = engine.readiness(today, c, learn=False)
    nd, night = _night(rows, today)
    need, src = need_hours(rows, today)
    reg = regularity(rows, today)
    last7 = [r["sleep_h"] for i in range(7) if (r := rows.get((today - dt.timedelta(days=i)).isoformat())) and r.get("sleep_h")]
    short = round(sum(max(need - h, 0) for h in last7), 1) if len(last7) >= 4 else None
    garmin_need = [r["need_min"] for i in range(7) if (r := rows.get((today - dt.timedelta(days=i)).isoformat())) and r.get("need_min")]
    ill = illness(rows, today)
    hrmax = (db.get("profile") or {}).get("hrmax") or c.get("hrmax")
    late, aft = late_runs(today, rows, hrmax), after_long(today, rows)
    tm = _tomorrow(today)
    keyed = bool(tm and tm["type"] in ("Key", "Long", "Race"))
    awake = [r["awake_s"] for r in rows.values() if r.get("awake_s") is not None][-14:]
    tonight = plan = None
    aw_min = round(mean(awake) / 60) if awake else 20

    def plan_for(d):
        p = db.rows("SELECT type,label FROM plan WHERE date=?", (d.isoformat(),))
        return p[0]["label"] if p and p[0]["type"] in ("Key", "Long", "Race") else None
    if reg and reg["typical_wake"]:
        plan = alarm_plan(rows, today, need, aw_min, plan_for)
    if plan:
        n0 = plan["nights"][0]
        tonight = {"bed_by": n0["bed_by"], "wake": n0["alarm"], "need_h": round(need, 1), "key": keyed, "session": tm["label"] if keyed else None}
    norm = rd.get("normal") or {}
    series = []
    for i in range(41, -1, -1):
        d = today - dt.timedelta(days=i)
        r = rows.get(d.isoformat()) or {}
        series.append([int(dt.datetime.combine(d, dt.time(12)).timestamp() * 1000) // 86400000, r.get("sleep_h"), r.get("hrv"), r.get("rhr"), r.get("resp"),
                       r.get("sleep_score"), r.get("bb_gain"), d.isoformat()])
    out = {"date": today.isoformat(), "level": rd["level"], "slow": rd.get("slow", 0), "reasons": rd.get("reasons", []), "points": rd.get("points", 0),
           "night_date": nd.isoformat() if nd else None, "night": None, "need_h": round(need, 1), "need_source": src,
           "garmin_need_h": round(statistics.median(garmin_need) / 60, 1) if garmin_need else None,
           "week": {"avg_h": round(mean(last7), 1) if last7 else None, "short_h": short, "nights": len(last7)},
           "norm": {"hrv": norm.get("hrv"), "rhr": norm.get("rhr"), "sleep_h": norm.get("sleep_h"), "resp": None},
           "regularity": reg, "illness": ill, "late_runs": late, "after_long": aft, "pattern": weekday_pattern(rows, today), "tonight": tonight, "alarms": plan, "series": series}
    n = _normal(rows, today, "resp", 0.4, 7)
    if n:
        out["norm"]["resp"] = round(n[0], 1)
    if night:
        aw = night.get("awake_s")
        out["night"] = {"sleep_h": night["sleep_h"], "score": night.get("sleep_score"), "bed": night.get("sleep_start") or None, "wake": night.get("sleep_end") or None,
                        "awake_min": round(aw / 60) if aw is not None else None, "awake_n": night.get("awake_n"), "hrv": night.get("hrv"), "rhr": night.get("rhr"),
                        "resp": night.get("resp"), "bb_gain": night.get("bb_gain"), "sleep_stress": night.get("sleep_stress"),
                        "deep_min": round(night["deep_s"] / 60) if night.get("deep_s") is not None else None,
                        "rem_min": round(night["rem_s"] / 60) if night.get("rem_s") is not None else None,
                        "vs_need_min": round((night["sleep_h"] - need) * 60)}
    out["actions"] = actions(out, tm)
    return out


def actions(r, tm):
    """Up to five instructions in order of how much they matter. Each is {"title", "body", "kind"}; the wording is direct and gives its numbers."""
    a = []
    ill = r["illness"]
    if ill["on"]:
        a.append({"kind": "red", "title": "Take today easy and watch for symptoms",
                  "body": "The last three nights look like the start of an illness: " + "; ".join(ill["signs"]) + ". Run easy or rest today, and no hard session until these settle. "
                          "If you have a fever, chest symptoms or body aches, do not run."})
    if r["level"] == "red" and not ill["on"]:
        a.append({"kind": "red", "title": "Recovery is poor this morning", "body": "; ".join(r["reasons"][:3]).capitalize() + ". Today's fast running is eased, and the session turns easy if the signs stay."})
    elif r["level"] == "amber" and not ill["on"]:
        a.append({"kind": "amber", "title": "Recovery is below normal this morning", "body": "; ".join(r["reasons"][:3]).capitalize() + ". Fast running is eased a little today."})
    wk = r["week"]
    if wk["short_h"] is not None and wk["short_h"] >= 3:
        t = r["tonight"]
        a.append({"kind": "amber", "title": f"You are {wk['short_h']:g} hours short on sleep this week",
                  "body": f"Your last {wk['nights']} nights averaged {wk['avg_h']:g} h against a need of about {r['need_h']:g} h ({r['need_source']}). Short sleep slows endurance running from a single night, mostly by making it feel harder, so the fix is more sleep opportunity, not more training."
                          + (f" Tonight, be asleep by {t['bed_by']} and set the alarm for {t['wake']}." if t else "")})
    elif r["tonight"] and r["tonight"]["key"]:
        t = r["tonight"]
        a.append({"kind": "info", "title": f"Protect tonight's sleep: {t['session']} tomorrow",
                  "body": f"Be asleep by {t['bed_by']} for {t['need_h']:g} h before a {t['wake']} alarm. Extra sleep before a key day is the best-supported way to improve how a hard run goes."})
    g = r["regularity"]
    if g and g["label"] == "irregular":
        a.append({"kind": "amber", "title": "Your bedtime moves around",
                  "body": f"Over the last 14 nights it has varied by about {g['bed_sd_min']} minutes either side of {g['typical_bed']}. Regular sleep timing predicts health outcomes at least as well as sleep length; keep it within 30 minutes on training days."})
    if g and g["weekend_shift_min"] is not None and abs(g["weekend_shift_min"]) >= 60:
        a.append({"kind": "info", "title": "Weekend nights shift your body clock",
                  "body": f"You fall asleep about {abs(g['weekend_shift_min'])} minutes {'later' if g['weekend_shift_min'] > 0 else 'earlier'} on weekend nights than on weekday nights, which can leave Monday's sleep and HRV worse. Check the weekday table below."})
    lr = r["late_runs"]
    if lr and lr["diff_min"] <= -18:
        a.append({"kind": "info", "title": "Late hard runs cost you sleep",
                  "body": f"On the {lr['n']} nights that followed a hard run ending within 4 hours of sleep you slept {lr['late_h']:g} h, against {lr['other_h']:g} h on other nights. Move hard runs earlier, or follow them with a longer wind-down."})
    al = r["after_long"]
    if al and al["median_days"] >= 3:
        a.append({"kind": "info", "title": "You take about " + f"{al['median_days']:g}" + " mornings to recover from a long run",
                  "body": f"After your {al['n']} long runs, your resting heart rate took a median of {al['median_days']:g} mornings to return to normal. Keep the days after a long run easy and do not stack a hard session on it."})
    if not a:
        a.append({"kind": "green", "title": "Recovery looks good", "body": "Sleep, resting heart rate and HRV are all near your normal. Train as planned."})
    return a[:5]
