"""The planning rules: next week's training, daily pace adjustment, sick and injured handling.

Fixed rules, no AI. Distances are miles internally; text is rendered in the
athlete's units. A day's session is a list of steps:
  ("d", miles, zone)                 run a distance in a zone (zone None = no target)
  ("r", reps, work_s, zone, rec_s)   repeats by time
  ("strides", n)
  ("h", miles, lo_bpm, hi_bpm)       run a distance holding a heart rate range (pace floats)
  ("rest", seconds)                  stand or walk (every session has a minute of it after the warm-up)
  ("rd", reps, work_m, zone, rec_m)  repeats by distance, jogging the recovery
  ("max", metres)                    all out
"""
import datetime as dt
import statistics

import db
from assess import MI, ZONES, mean, projection

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
T_LADDER = [(15, 5, 3, 1), (18, 6, 3, 1), (20, 4, 5, 1), (25, 5, 5, 1), (30, 3, 10, 2), (36, 3, 12, 2), (40, 2, 20, 3)]   # total min, reps, min, rec min
MP_LONG_LADDER = [8, 10, 12, 14]
QUALITY = {"mp", "hmp", "threshold", "10k", "5k"}
ZONE_NAME = {"easy": "easy", "steady": "steady", "mp": "marathon pace", "hmp": "half marathon pace", "threshold": "threshold",
             "10k": "10K pace", "5k": "5K pace"}


def half(x):
    return round(x * 2) / 2


# ---------------------------------------------------------------- rendering
def pace(v, units="mi"):
    s = round((MI if units == "mi" else 1000) / v)
    return f"{s // 60}:{s % 60:02d}"


def hms(s):
    s = round(s)
    return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60}:{s % 60:02d}"


def dist(miles, units="mi"):
    if units == "mi":
        return f"{round(miles, 1):g} mi"
    return f"{half(miles * 1.609344):g} km"


def zone_speeds(tp, name, slow=0.0):
    lo, hi = ZONES[name]
    f = 1 - slow if name in QUALITY else 1.0
    return tp * lo * f, tp * hi * f


def zone_pace(tp, name, units="mi", slow=0.0):
    lo, hi = zone_speeds(tp, name, slow)
    u = "/" + units
    return pace(lo, units) + u if lo == hi else f"{pace(hi, units)}–{pace(lo, units)}{u}"


ABBR = {"threshold": "threshold", "10k": "10K pace", "5k": "5K pace", "mp": "MP", "hmp": "HMP", "steady": "steady", "easy": "easy"}


WARMUP_REST_S = 60


def warmup_rest(day):
    """A session's steps with a minute's rest between the warm-up and the hard part."""
    steps = list(day["steps"])
    if len(steps) > 1 and tuple(steps[0][::2]) == ("d", "easy"):
        nxt = steps[1]
        if nxt[0] in ("r", "rd", "h") or (nxt[0] == "d" and nxt[2] in QUALITY):
            steps.insert(1, ("rest", WARMUP_REST_S))
    return steps


def short(day, units="mi"):
    """A few words for the calendar: the heart of the session, without paces."""
    steps = day.get("steps") or []
    if not steps:
        return ""
    hs = [s for s in steps if s[0] == "h"]
    for s in steps:
        if s[0] == "r":
            m = s[2] / 60
            return f"{s[1]} × {m:g} min {ABBR[s[3]]}"
        if s[0] == "rd":
            return f"{s[1]} × {s[2]} m {ABBR[s[3]]}"
    if len(hs) > 1:
        return f"{len(hs)} stages by heart rate" + (" + 500 m hard" if any(s[0] == "max" for s in steps) else "")
    if hs:
        return f"{dist(hs[0][1], units)} at {hs[0][2]}–{hs[0][3]} bpm"
    for s in steps:
        if s[0] == "d" and s[2] in ("mp", "hmp"):
            return f"{dist(s[1], units)} at {ABBR[s[2]]}"
    ds = [s for s in steps if s[0] == "d"]
    if any(s[2] is None for s in ds):
        return "race"
    st = [s for s in ds if s[2] == "steady"]
    if st:
        return "steady" if len(ds) == 1 else f"last {dist(st[0][1], units)} steady"
    return "easy" + (" + strides" if any(s[0] == "strides" for s in steps) else "")


def describe(day, tp, units="mi", slow=0.0):
    """Readable session text from the steps, with paces for today's fitness (and today's adjustment)."""
    parts = []
    for st in day.get("steps") or []:
        if st[0] == "d":
            z = st[2]
            parts.append(f"{dist(st[1], units)}" + (f" {ZONE_NAME[z]} ({zone_pace(tp, z, units, slow)})" if z else " race"))
        elif st[0] == "r":
            _, n, work, z, rec = st
            w = f"{work // 60:g} min" if work % 60 == 0 else f"{work / 60:g} min"
            parts.append(f"{n} x {w} at {ZONE_NAME[z]} ({zone_pace(tp, z, units, slow)}), {rec // 60:g} min jog" if rec % 60 == 0
                         else f"{n} x {w} at {ZONE_NAME[z]} ({zone_pace(tp, z, units, slow)}), {rec} s jog")
        elif st[0] == "strides":
            parts.append(f"{st[1]} x 20 s strides")
        elif st[0] == "h":
            d = "2400 m" if abs(st[1] - STAGE_MI) < 0.01 else dist(st[1], units)
            parts.append(f"{d} at {st[2]}–{st[3]} bpm")
        elif st[0] == "rest":
            parts.append(f"{st[1]} s rest")
        elif st[0] == "max":
            parts.append(f"{st[1]} m all out")
        elif st[0] == "rd":
            parts.append(f"{st[1]} x {st[2]} m at {ZONE_NAME[st[3]]} ({zone_pace(tp, st[3], units, slow)}) with {st[4]} m easy between, without stopping")
    return "; ".join(parts)


STAGE_MI = 2400 / MI


def hr_levels(hrmax):
    """Working heart rates as offsets from maximum (coaching conventions): marathon about 15-20 below, easy about 50 below, and the test stages between."""
    stages = [int(round((hrmax - o) / 5) * 5) for o in (55, 45, 35, 25, 15)]
    return {"stages": stages, "easy_max": hrmax - 50, "marathon": hrmax - 18, "start_lthr": int(round((hrmax - 38) / 5) * 5), "top_lthr": hrmax - 23}


# ---------------------------------------------------------------- weekly plan
def goal_race(races, monday):
    a = [r for r in races if r["priority"] == "A" and r["date"] >= monday]
    return min(a, key=lambda r: r["date"]) if a else None


def plan(st, c, L, races):
    mon, tp = st["monday"], st["tp"]
    goal = goal_race(races, mon)
    gm = goal["miles"] if goal else None
    gtype = "general" if gm is None else "ultra" if gm > 30 else "marathon" if gm >= 20 else "half" if gm >= 10 else "short"
    wtr = (goal["date"] - mon).days // 7 + 1 if goal else None
    week_end = mon + dt.timedelta(days=7)
    this_races = sorted([r for r in races if mon <= r["date"] < week_end], key=lambda r: r["date"])
    last_races = [r for r in races if mon - dt.timedelta(days=7) <= r["date"] < mon]
    specific = wtr is not None and wtr <= L["specific_weeks"]
    wk = [w["mi"] for w in st["weeks"]]
    last4 = wk[-4:]
    ref = mean(last4) or 0.0
    why = []

    # ---- kind of week ----
    full, peak6 = 0, max(wk[-6:] or [0])
    for m in reversed(wk):
        if peak6 and m >= 0.85 * peak6:
            full += 1
        else:
            break
    prior3 = mean(wk[-4:-1]) or 0.0
    taper_weeks = (2, 3) if gtype in ("marathon", "ultra") else (2,) if gtype == "half" else ()
    if this_races and this_races[-1]["priority"] == "A":
        mode = "race"
    elif wtr in taper_weeks:
        mode = "taper"
    elif this_races:
        mode = "tuneup"
    elif last_races or st["longest_10d"] >= 26:
        mode = "postrace"
        why.append("Recovery week: you raced or ran very long in the last 10 days.")
    elif len(st["flags"]) >= c["flags_to_back_off"]:
        mode = "recover"
        why.append("Recovery week: " + "; ".join(st["flags"]) + ".")
    elif prior3 > 8 and wk[-1] < 0.5 * prior3:
        mode = "return"
        why.append(f"Return week: last week was well below your recent level ({dist(half(wk[-1]), c['units'])} against {dist(half(prior3), c['units'])}). "
                   "Missed sessions are not made up.")
    elif full >= c["build_weeks_before_down"]:
        mode = "down"
        why.append(f"Down week: {full} full weeks in a row.")
    else:
        mode = "build"

    # ---- weekly miles ----
    cap = L["peak_miles"] if specific else L["base_cap_miles"]
    quality_new = st["prev_t_min"] < 8
    if mode == "build":
        grow = 1.0 if quality_new else 1 + c["weekly_increase"]
        target = min(max(ref, 0.92 * max(last4 or [0])) * grow, cap)
        why.append("Volume held level because fast running is being reintroduced; one change at a time." if quality_new
                   else f"Volume is at your cap for this phase ({dist(cap, c['units'])})." if target >= cap
                   else f"Volume up {c['weekly_increase']:.0%} on your recent level.")
    else:
        target = {"down": 0.75 * (mean(wk[-full:]) if full else ref), "recover": 0.70 * ref, "return": 0.80 * prior3,
                  "postrace": min(0.5 * ref, 25), "tuneup": 0.75 * ref,
                  "taper": (0.80 if wtr == 3 else 0.65) * max(ref, 0.9 * max(wk[-6:] or [0])), "race": 0.4 * ref}[mode]
    target = max(target, c["min_miles"])

    # ---- layout ----
    # Offsets are days after the long run (0 = long run day). Days the athlete cannot run are never used.
    Ld = c["long_day"]
    blocked = {(d - Ld) % 7 for d in c.get("blocked_days") or []} - {0}
    n = max(2, min(int(c["run_days"]), 6, 7 - len(blocked)))
    hard = [0]

    def pick(prefs):
        for o in prefs:
            if o not in blocked and o not in hard and all(abs(o - h) != 1 and abs(o - h) != 6 for h in hard):
                hard.append(o)
                return o
        return None

    k1o = pick([3, 2, 4])
    two_keys = n >= 5
    k2o = pick([5, 4, 2]) if two_keys and k1o is not None else None
    two_keys = k2o is not None
    key1 = (Ld + k1o) % 7 if k1o is not None else None
    key2 = (Ld + k2o) % 7 if k2o is not None else None
    free = [o for o in (2, 4, 6, 5, 3, 1) if o not in blocked and o not in hard]
    easy_slots = [(Ld + o) % 7 for o in free[:max(n - len(hard), 0)]]
    hard_ok = mode in ("build", "down", "taper", "tuneup")
    done = {"t_min": 0, "mp_mid": 0, "mp_long": 0, "lthr_mi": 0}
    t_prev = st["prev_t_min"]
    week_no = mon.isocalendar()[1]

    # threshold session
    t_cap = 40 if gtype in ("marathon", "half") else 30   # shorter for 5K/10K and ultra goals
    step = next((s for s in T_LADDER if s[0] > t_prev + 1), T_LADDER[-1])
    if mode in ("down", "taper") or t_prev > 45:
        step = T_LADDER[min(max(T_LADDER.index(step) - 2, 0), 4)]
    while step[0] > t_cap:
        step = T_LADDER[T_LADDER.index(step) - 1]
    t_min, t_n, t_rep, t_rec = step

    def threshold_day():
        done["t_min"] = t_min
        why.append(f"Threshold: {t_min} minutes in total (your biggest session in the last 3 weeks had {t_prev:.0f} minutes at threshold or faster).")
        return "Threshold", [("d", 2, "easy"), ("r", t_n, t_rep * 60, "threshold", t_rec * 60), ("d", 2, "easy")], half(4 + t_min * 60 * tp / MI)

    def interval_day(zone, reps, work, rec):
        return "Intervals", [("d", 2, "easy"), ("r", reps, work, zone, rec), ("d", 2, "easy")], half(4 + reps * (work * tp * ZONES[zone][0] + rec * tp * 0.7) / MI)

    # marathon-pace long run
    mp_long = 0
    since_long = (mon - st["last_mp_long"]).days if st["last_mp_long"] else 99
    if gtype == "marathon" and mode == "build" and specific and wtr >= 4 and since_long >= 13 and st["prev_mp_mid"] >= 5:
        mp_long = next((m for m in MP_LONG_LADDER if m > st["prev_mp_long"] + 0.5), MP_LONG_LADDER[-1])
        if wtr <= 5:
            mp_long = min(mp_long, 6)

    # long run
    lr_cap = L["long_run_cap_specific"] if specific else L["long_run_cap_base"]
    safe = max(st["longest_30d"] * 1.10, L["long_run_floor"])
    if mode in ("build", "down", "taper", "tuneup"):
        lr = min(lr_cap, safe, max((0.38 if mode == "build" else 0.33) * target, L["long_run_floor"]))
        if mp_long:
            lr = min(max(mp_long + 5, 0.75 * lr_cap), safe, lr_cap)
            mp_long = max(min(mp_long, lr - 4), 0)
        if st["longest_30d"] * 1.10 < lr_cap and lr >= safe - 0.25 and mode == "build":
            why.append(f"Long run limited to 10% beyond your longest run of the last 30 days ({dist(half(st['longest_30d']), c['units'])}).")
    else:
        lr = min(0.30 * target, {"recover": 12, "postrace": 8}.get(mode, safe), lr_cap)
    lr = half(lr)
    if mp_long:
        long_day = ("Long run with marathon pace", [("d", 3, "easy"), ("d", mp_long, "mp"), ("d", lr - mp_long - 3, "easy")], lr)
        done["mp_long"] = mp_long
        why.append(f"Marathon-pace long run this week ({dist(mp_long, c['units'])} at pace), so the second session is dropped.")
    elif hard_ok and not quality_new and gtype != "ultra":
        long_day = ("Long run", [("d", lr, "steady")], lr)
    else:
        long_day = ("Long run", [("d", lr, "easy")], lr)

    # first key session: race-specific work
    k1 = half(min(max(0.21 * target, 5), 14))
    mp_ready = t_prev >= 15 or st["prev_mp_mid"] >= 3
    # before the race-specific phase, the midweek session is a heart-rate aerobic run rather than race-pace work
    aero_ok = bool(c.get("aero_runs", True)) and two_keys and mode == "build" and not specific and not quality_new
    one_key_threshold = not two_keys and week_no % 2 == 1
    if not hard_ok:
        key1_day = ("Easy", [("d", k1, "easy")], k1)
    elif mode == "tuneup":
        key1_day = ("Sharpener", [("d", half(k1 / 2), "easy"), ("r", 3, 180, "threshold", 60), ("d", max(half(k1 / 2) - 1.5, 1), "easy")], k1)
    elif one_key_threshold and not quality_new or (not two_keys and quality_new):
        key1_day = threshold_day()
    elif gtype == "marathon" and mode in ("build", "taper") and mp_ready and not aero_ok:
        m = min(max(round(st["prev_mp_mid"]) + 1, 4), 8 if specific else 6)
        if mode == "taper":
            m = max(m - (2 if wtr == 3 else 4), 3)
        k1 = max(k1, m + 4)
        a = half((k1 - m) / 2)
        key1_day = ("Marathon pace", [("d", a, "easy"), ("d", m, "mp"), ("d", k1 - m - a, "easy")], k1)
        done["mp_mid"] = m
        why.append(f"Marathon pace midweek: {dist(m, c['units'])} (your longest midweek block in the last 3 weeks was {dist(half(st['prev_mp_mid']), c['units'])}).")
    elif gtype == "half" and specific and mode in ("build", "taper") and mp_ready:
        m = min(max(3 + (L["specific_weeks"] - wtr) // 2, 3), 6) - (2 if mode == "taper" else 0)
        k1 = max(k1, m + 4)
        a = half((k1 - m) / 2)
        key1_day = ("Half marathon pace", [("d", a, "easy"), ("d", m, "hmp"), ("d", k1 - m - a, "easy")], k1)
    elif gtype in ("short", "general") and mode in ("build", "taper") and t_prev >= 15:
        key1_day = interval_day("5k", 8 if specific else 6, 120, 120) if week_no % 2 == 0 else interval_day("10k", 6 if specific else 5, 210, 120)
        why.append("Faster intervals: race-pace work for a shorter goal race.")
    else:
        fin = min(max(round(0.25 * k1), 2), 4) if mode == "build" else 2
        key1_day = ("Steady finish", [("d", k1 - fin, "easy"), ("d", fin, "steady")], k1)

    # heart-rate aerobic run: hold a heart rate below threshold, let the pace come to you
    hl = hr_levels(L["hrmax"])
    lthr = c.get("aero_lthr") or hl["start_lthr"]
    if aero_ok and key1_day[0] == "Steady finish":
        m_ = min(max(round(st.get("prev_lthr_mi", 0)) + 1, 5), 10)
        key1_day = ("Aerobic run by heart rate", [("d", 1.5, "easy"), ("h", m_, lthr, lthr + 5), ("d", 1, "easy")], m_ + 2.5)
        done["lthr_mi"] = m_
        why.append(f"Aerobic run by heart rate: {dist(m_, c['units'])} at {lthr}–{lthr + 5} bpm. Hold the heart rate and let the pace float; slow down rather than let it rise. "
                   "The heart rate moves up 5 only when you can run 10 miles there without the pace fading.")

    # second key session
    key2_day = None
    if two_keys and hard_ok and not mp_long and mode != "tuneup":
        if gtype == "marathon" and week_no % 3 == 0 and t_prev >= 18 and mode == "build":
            key2_day = interval_day("10k", 6 if specific else 5, 210, 120)
            why.append("Faster intervals this week: every third week, once threshold work is established.")
        elif week_no % 3 == 1 and mode == "build" and not specific and t_prev >= 18:
            n200 = min(15 + 5 * int(st.get("prev_200s", 0) >= 15) + 5 * int(st.get("prev_200s", 0) >= 20), 25)
            key2_day = ("200s", [("d", 2, "easy"), ("rd", n200, 200, "5k", 200), ("d", 1.5, "easy")], half(3.5 + n200 * 400 / MI))
            why.append("200s: quick but relaxed running with equal easy running between, to practise moving fast without hard effort. Keep the gap between fast and easy; do not race it.")
        else:
            key2_day = threshold_day()
    # the monthly Aerobic test replaces the second session (or the first, with one session a week): rested, flat, windless if possible
    test_due = c.get("aero_test", True) and mode in ("build", "down") and (mon.toordinal() // 7) % max(int(c.get("aero_test_weeks", 4)), 2) == 0
    if test_due and target >= 15:
        short = c.get("aero_format", "short") != "original"
        if short:
            # the athlete's shorter version: one-mile stages run continuously, then 500 m all out (which also checks maximum heart rate)
            stg = hl["stages"][:4] if L["peak_miles"] >= 25 else hl["stages"][:3]
            steps_ = [("d", 1, "easy")] + [("h", 1, bpm - 2, bpm + 2) for bpm in stg] + [("max", 500), ("d", 0.5, "easy")]
            test_day = ("Aerobic test", steps_, half(1.5 + len(stg) + 500 / MI + 0.2))
            how = f"one mile at each of {', '.join(str(x) for x in stg)} bpm without stopping, then 500 m all out"
        else:
            stg = hl["stages"] if L["peak_miles"] >= 40 else hl["stages"][1:] if L["peak_miles"] >= 25 else hl["stages"][1:4]
            steps_ = [("d", 1.5 if len(stg) > 3 else 1, "easy")]
            for i, bpm in enumerate(stg):
                steps_ += [("h", STAGE_MI, bpm - 2, bpm + 2)] + ([("rest", 90)] if i < len(stg) - 1 else [])
            steps_.append(("d", 1 if len(stg) > 3 else 0.5, "easy"))
            test_day = ("Aerobic test", steps_, half((2.5 if len(stg) > 3 else 1.5) + len(stg) * STAGE_MI + 0.24))
            how = f"{len(stg)} stages of 2400 m at rising heart rates, 90 s rest between"
        if two_keys:
            key2_day = test_day
        else:
            key1_day = test_day
        done["t_min"] = 0
        why.append(f"Aerobic test this week: {how}. Ease up to each heart rate and hold it; never start fast and slow down. "
                   "Compare the paces with last time: the same heart rate, faster, is the proof the training is working.")

    # ---- assemble ----
    week = {i: {"type": "Rest", "label": "Rest", "miles": 0, "steps": None} for i in range(7)}
    week[Ld] = {"type": "Long", "label": long_day[0], "steps": long_day[1], "miles": long_day[2]}
    if key1 is not None:
        week[key1] = {"type": "Key" if key1_day[0] != "Easy" else "Easy", "label": key1_day[0], "steps": key1_day[1], "miles": key1_day[2]}
    slots = list(easy_slots)
    if two_keys:
        if key2_day:
            week[key2] = {"type": "Key", "label": key2_day[0], "steps": key2_day[1], "miles": key2_day[2]}
        else:
            slots.append(key2)
    # ultra goals: a medium run the day before the long run in the specific phase (tired-legs practice)
    b2b = (Ld + 6) % 7
    if gtype == "ultra" and specific and mode == "build" and b2b in slots and lr >= 14:
        m = half(min(0.4 * lr, 12))
        week[b2b] = {"type": "Easy", "label": "Back-to-back: medium easy", "steps": [("d", m, "easy")], "miles": m}
        slots.remove(b2b)
        why.append("Back-to-back weekend: a medium easy run the day before the long run, to practise running on tired legs.")
    rem = max(target - sum(d["miles"] for d in week.values()), 0)
    while len(slots) > 1 and rem / len(slots) < c["min_easy_run_miles"]:
        slots.pop()
    each = min(half(rem / len(slots)), c["max_easy_run_miles"]) if slots else 0
    strides_day = slots[0] if slots else None
    for s in slots:
        if each <= 0:
            continue
        st_ = [("d", each, "easy")] + ([("strides", 6)] if s == strides_day and mode not in ("recover", "postrace", "return") else [])
        week[s] = {"type": "Easy", "label": "Easy + strides" if len(st_) > 1 else "Easy", "steps": st_, "miles": each}

    # races in this week override the layout around them
    for r in this_races:
        i = r["date"].weekday()
        now_s, full_s = projection(st, c, r["miles"])
        a_race = r["priority"] == "A"
        note = (f"Predicted {hms(now_s)}. Start at {pace(r['miles'] * MI / now_s, c['units'])}/{c['units']} and no faster for the first half."
                + (f" Fuel: {c['race_carbs_g_per_h']} g of carbohydrate an hour." if r["miles"] >= 13 else ""))
        wu = 0 if r["miles"] >= 20 else 2
        week[i] = {"type": "Race", "label": r["name"], "note": note, "miles": round(r["miles"] + (wu + 1 if wu else 0), 3),
                   "steps": ([("d", wu, "easy")] if wu else []) + [("d", r["miles"], None)] + ([("d", 1, "easy")] if wu else [])}
        for back in range(1, i + 1):
            j = i - back
            if a_race:
                opts = {1: ("Easy + strides", [("d", 3, "easy"), ("strides", 4)], 3), 2: ("Rest", None, 0), 3: ("Easy", [("d", 4, "easy")], 4),
                        4: ("Sharpener", [("d", 1.5, "easy"), ("d", 2, "mp" if r["miles"] >= 20 else "hmp" if r["miles"] >= 10 else "10k"), ("d", 1.5, "easy")], 5),
                        5: ("Easy", [("d", 4, "easy")], 4), 6: ("Rest", None, 0)}
                lab, stp, mi_ = opts[back]
                if back not in ({1, 3, 4, 5} if n >= 5 else {1, 3, 4} if n == 4 else {1, 4}):
                    lab, stp, mi_ = "Rest", None, 0   # fewer running days: keep the shakeout and the sharpener
                week[j] = {"type": "Rest" if stp is None else "Key" if lab == "Sharpener" else "Easy", "label": lab, "steps": stp, "miles": mi_}
            elif back == 1:
                week[j] = {"type": "Easy", "label": "Easy + strides", "steps": [("d", 3, "easy"), ("strides", 4)], "miles": 3}
            elif back == 2 and week[j]["type"] in ("Key", "Long"):
                week[j] = {"type": "Easy", "label": "Easy", "steps": [("d", 4, "easy")], "miles": 4}
        for j in range(i + 1, 7):
            week[j] = {"type": "Rest", "label": "Rest", "steps": None, "miles": 0} if a_race or j == i + 1 else \
                {"type": "Easy", "label": "Easy", "steps": [("d", 4, "easy")], "miles": 4}

    strength = {(Ld + 1) % 7: "Strength A", (key1 + 1) % 7 if key1 is not None else (Ld + 4) % 7: "Strength B"} if c["strength"] and mode != "race" and (wtr is None or wtr > 2) else {}
    days = []
    for i in range(7):
        d = week[i]
        d.update({"date": mon + dt.timedelta(days=i), "strength": strength.get(i, ""), "note": d.get("note", "")})
        if d["steps"]:
            d["steps"] = [x for x in d["steps"] if x[0] != "d" or x[1] > 0]
            d["steps"] = warmup_rest(d) if d["type"] == "Key" and d["label"] != "Aerobic test" else d["steps"]
        days.append(d)
    fuel = None
    if gtype in ("marathon", "half", "ultra") and wtr is not None:
        fuel = 30 if wtr > 27 else 45 if wtr > 18 else 60 if wtr > 10 else 70
        long_i = next((i for i in range(7) if days[i]["type"] == "Long"), None)
        if long_i is not None and days[long_i]["miles"] >= 12:
            days[long_i]["note"] = f"Fuel practice: {fuel} g of carbohydrate an hour."
    return {"mode": mode, "weeks_to_race": wtr, "goal": goal, "gtype": gtype, "target": target, "total": sum(d["miles"] for d in days),
            "days": days, "why": why, "done": done, "long": max((d["miles"] for d in days), default=0)}


def project(st, pl):
    """State for the following week, assuming this week's plan is run as written."""
    d, nxt = pl["done"], dict(st)
    nxt["monday"] = st["monday"] + dt.timedelta(days=7)
    fast = d["mp_mid"] + d["mp_long"] + d["t_min"] * 60 * st["tp"] / MI
    nxt["weeks"] = st["weeks"][1:] + [{"start": st["monday"], "mi": pl["total"], "runs": sum(1 for x in pl["days"] if x["miles"]),
                                       "long": pl["long"], "fast_mi": fast, "t_min": d["t_min"]}]
    nxt["longest_30d"], nxt["longest_10d"] = max(st["longest_30d"], pl["long"]), pl["long"]
    nxt["prev_t_min"] = max(st["prev_t_min"], d["t_min"])
    nxt["prev_mp_mid"] = max(st["prev_mp_mid"], d["mp_mid"])
    nxt["prev_lthr_mi"] = max(st.get("prev_lthr_mi", 0), d.get("lthr_mi", 0))
    if d["mp_long"]:
        nxt["prev_mp_long"], nxt["last_mp_long"] = max(st["prev_mp_long"], d["mp_long"]), st["monday"] + dt.timedelta(days=6)
    return nxt


# ---------------------------------------------------------------- sick / injured
HOLIDAY_MODES = {
    "rest": "No running",
    "easy": "Easy runs only",
    "easy_long": "Easy runs and the long run",
    "sessions": "Sessions only",
    "sessions_long": "Sessions and the long run",
    "normal": "Train as normal",
}


def _holiday(d, mode):
    """Reshape one planned day for a holiday, according to how the athlete wants to run while away."""
    note = f"Holiday: {HOLIDAY_MODES[mode].lower()}."
    rest = {"type": "Rest", "label": "Holiday", "steps": None, "miles": 0, "strength": "", "note": note}
    if mode == "normal" or d["type"] == "Race":
        return
    d["strength"] = ""
    if mode == "rest":
        d.update(rest)
    elif d["type"] == "Easy":
        d.update(rest) if mode in ("sessions", "sessions_long") else d.update({"note": note})
    elif d["type"] == "Key":
        if mode in ("easy", "easy_long"):
            mi_ = max(half(min(d["miles"], 8) * 0.8), 3)
            d.update({"type": "Easy", "label": "Easy", "steps": [("d", mi_, "easy")], "miles": mi_, "note": note})
        else:
            d["note"] = note
    elif d["type"] == "Long":
        if mode in ("easy_long", "sessions_long"):
            d["note"] = note
        elif mode == "easy":
            mi_ = max(half(min(d["miles"] * 0.6, 8)), 3)
            d.update({"type": "Easy", "label": "Easy", "steps": [("d", mi_, "easy")], "miles": mi_, "note": note})
        else:
            d.update(rest)


def apply_status(days, statuses):
    """Overlay sick, injured and holiday periods on planned days.

    Sick or injured: rest while unwell, then easy running for a return period. Holiday: the athlete's chosen way of running while away.
    """
    for d in days:
        for s in statuses:
            start = dt.date.fromisoformat(s["start"])
            end = dt.date.fromisoformat(s["end"]) if s["end"] else None
            if s["kind"] == "holiday":
                if d["date"] >= start and (end is None or d["date"] <= end):
                    _holiday(d, s.get("mode") if s.get("mode") in HOLIDAY_MODES else "easy")
                continue
            word = "Sick" if s["kind"] == "sick" else "Injured"
            if d["date"] >= start and (end is None or d["date"] <= end):
                d.update({"type": "Rest", "label": f"{word}: no running", "steps": None, "miles": 0, "strength": "",
                          "note": "Rest until you are well." if s["kind"] == "sick" else "No running until it is pain-free to walk briskly and hop. See a clinician if it is not improving."})
            elif end and d["date"] > end:
                off = (end - start).days + 1
                back = min(off, 7) if s["kind"] == "sick" else min(2 * off, 14)
                k = (d["date"] - end).days
                if k <= back and d["type"] != "Rest":
                    mi_ = max(half(min(d["miles"], 10) * (0.5 + 0.4 * k / back)), 2)
                    d.update({"type": "Easy", "label": "Return: easy", "steps": [("d", mi_, "easy")], "miles": mi_,
                              "note": f"Day {k} of {back} back after being {word.lower()}. Easy only; stop if symptoms return."})
    return days


# ---------------------------------------------------------------- daily readiness
def _z(value, base, floor):
    """How unusual `value` is against the athlete's own recent values, in standard deviations."""
    if value is None or len(base) < 14:
        return None, None
    m = mean(base)
    return (value - m) / max(statistics.pstdev(base), floor), m


def readiness(today, c, learn=True):
    """How recovered the athlete is this morning, and how much to ease today's fast running.

    Each marker is read over the window the research supports (see PRINCIPLES.md):
      - Sleep: last night on its own. A single short night does reduce endurance performance the next day (Lopes et al. 2023;
        Craven et al. 2022). A run of short nights also counts, as a 3-night average, because sleep debt builds.
      - HRV and resting heart rate: a 7-day average against the athlete's own 60-day normal range. One night's reading is too noisy
        to act on (Plews et al. 2012, 2013); a shift of half the athlete's normal spread is the smallest change treated as real.
    """
    rows = {r["date"]: r for r in db.rows("SELECT * FROM daily WHERE date>=?", ((today - dt.timedelta(days=68)).isoformat(),))}
    now = rows.get(today.isoformat()) or {}

    def vals(key, a, b):
        """Values from `a` to `b` days ago (0 = this morning)."""
        return [v for v in ((rows.get((today - dt.timedelta(days=i)).isoformat()) or {}).get(key) for i in range(a, b)) if v]

    def normal(key, sd_floor, skip):
        """(average, spread) over the 60 days before the last `skip` days, or None with under two weeks of data."""
        base = vals(key, skip, skip + 60)
        return (mean(base), max(statistics.pstdev(base), sd_floor)) if len(base) >= 14 else None

    sleep, score, hrv, rhr = now.get("sleep_h"), now.get("sleep_score"), now.get("hrv"), now.get("rhr")
    if sleep is None and hrv is None and score is None and not vals("hrv", 1, 4):
        return {"level": "unknown", "slow": 0.0, "points": 0, "reasons": ["No sleep or HRV data for the last few nights. Sync your watch."],
                "sleep_h": None, "sleep_score": None, "hrv": None, "rhr": rhr, "fresh": None, "normal": {}, "week": {}}
    pts, reasons, lost, norm, week = 0, [], 0.0, {}, {}

    # ---- HRV and resting heart rate: 7-day average against the normal range
    n, recent = normal("hrv", 3.0, 7), vals("hrv", 0, 7)
    if n and len(recent) >= 4:
        base, sd = n
        m7 = mean(recent)
        z = (m7 - base) / sd
        norm["hrv"], week["hrv"] = round(base), round(m7)
        lost += min(max(-z, 0) * 16, 30)
        if z <= -1:
            pts += 2
            reasons.append(f"your 7-day HRV is {m7:.0f}, below your normal range (about {base - sd:.0f}–{base + sd:.0f})")
        elif z <= -0.5:
            pts += 1
            reasons.append(f"your 7-day HRV is {m7:.0f}, drifting below your normal {base:.0f}")
    n, recent = normal("rhr", 1.5, 7), vals("rhr", 0, 7)
    if n and len(recent) >= 4:
        base, m7 = n[0], mean(recent)
        norm["rhr"], week["rhr"] = round(base), round(m7)
        lost += min(max(m7 - base, 0) * 4, 20)
        if m7 - base >= 5:
            pts += 2
            reasons.append(f"your 7-day resting heart rate is {m7:.0f}, {m7 - base:.0f} above your normal")
        elif m7 - base >= 3:
            pts += 1
            reasons.append(f"your 7-day resting heart rate is {m7:.0f}, {m7 - base:.0f} above your normal")

    # ---- sleep: last night on its own, and the last three nights together
    sp = 0
    n = normal("sleep_h", 0.5, 1)
    if sleep is not None:
        short = (n[0] - sleep) if n else 0.0
        if n:
            norm["sleep_h"] = round(n[0], 1)
            lost += min(max(short, 0) * 12, 25)
        if sleep < 5 or short >= 2:
            sp += 2
            lost += 8 if sleep < 5 else 0
            reasons.append(f"only {sleep:.1f} h of sleep last night" + (f", against your normal {n[0]:.1f}" if n else ""))
        elif short >= 1:
            sp += 1
            reasons.append(f"{sleep:.1f} h of sleep last night, an hour or more under your normal {n[0]:.1f}")
    n3, last3 = normal("sleep_h", 0.5, 3), vals("sleep_h", 0, 3)
    if n3 and len(last3) >= 2:
        week["sleep_h"] = round(mean(last3), 1)
        lost += min(max(n3[0] - mean(last3), 0) * 8, 15)
        if n3[0] - mean(last3) >= 1.0 and sp < 2:
            sp += 1
            reasons.append(f"you have averaged {mean(last3):.1f} h of sleep over 3 nights, an hour or more under your normal {n3[0]:.1f}")
    n = normal("sleep_score", 6.0, 1)
    if n and score:
        base, sd = n
        norm["sleep_score"] = round(base)
        lost += min(max(base - score, 0) * 0.6, 20)
        if base - score >= 2 * sd:
            sp += 2
            reasons.append(f"last night's sleep score was {score:.0f}, far below your normal {base:.0f}")
        elif base - score >= sd and sp == 0:
            sp += 1
            reasons.append(f"last night's sleep score was {score:.0f}, below your normal {base:.0f}")
    pts += min(sp, 2)                # length, score and the 3-night average all describe sleep, so sleep counts for at most 2
    per = ((db.get("model") or {}).get("slow_per_point") or {}).get("value", 0.012) if learn else 0.012
    return {"level": "green" if pts == 0 else "amber" if pts <= 2 else "red", "slow": min(pts, 4) * per, "points": pts,
            "reasons": reasons or ["Last night's sleep was normal for you, and your 7-day HRV and resting heart rate are in your normal range."],
            "sleep_h": sleep, "sleep_score": score, "hrv": hrv, "rhr": rhr, "fresh": round(max(35, 100 - lost)), "normal": norm, "week": week}
