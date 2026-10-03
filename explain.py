"""Explain my plan: every decision that shapes the plan, what in the athlete's own data led to it, and the evidence behind the rule.

Each entry is {"title", "decision", "because", "evidence"}: what was decided, the athlete's own numbers behind it, and where the
rule comes from (a study named in PRINCIPLES.md, a coaching convention, or this project's own choice, said plainly).
"""
import datetime as dt
import json

import assess
import db
import engine


def _goal_seconds(text):
    try:
        parts = [int(x) for x in str(text).split(":")]
    except ValueError:
        return None
    return sum(x * 60 ** i for i, x in enumerate(reversed(parts))) if parts else None


def build(c, prof, races, L, today=None):
    today = today or dt.date.today()
    mon = today - dt.timedelta(days=today.weekday())
    D = lambda m: engine.dist(engine.half(m), c["units"])
    goal = engine.goal_race(races, mon)
    gm = goal["miles"] if goal else None
    gtype = "general" if gm is None else "ultra" if gm > 30 else "marathon" if gm >= 20 else "half" if gm >= 10 else "short"
    wk = db.rows("SELECT * FROM weeks WHERE monday=?", (mon.isoformat(),))
    s = json.loads(wk[0]["summary"]) if wk else None
    resp = db.get("response") or {}
    out = []
    add = lambda title, decision, because, evidence: out.append({"title": title, "decision": decision, "because": because, "evidence": evidence})

    # ---- what the plan is aiming at
    if goal:
        wtr = (goal["date"] - mon).days // 7 + 1
        phase = ("race week" if wtr <= 1 else "taper" if wtr <= 3 and gtype in ("marathon", "ultra") or wtr == 2 else
                 "race-specific phase" if wtr <= L["specific_weeks"] else "general phase")
        add("What the plan is built toward", f"{goal['name']}, {wtr} weeks away. You are in the {phase}.",
            f"The last {L['specific_weeks']} weeks before a race of this length are race-specific; before that the work is general: volume first, then threshold.",
            "World-class distance runners build volume before intensity and general work before specific work (Haugen and colleagues, 2022). "
            "The length of the specific phase is this project's choice.")
    else:
        add("What the plan is built toward", "No goal race is set, so the plan builds general fitness.",
            "Add a goal race (Races & status) and the plan gains a race-specific phase, a taper and race-day advice.", "This project's choice.")

    # ---- the ceiling
    if prof:
        add("Your peak week", f"{D(L['peak_miles'])} a week at most; {D(L['base_cap_miles'])} before the race-specific phase.",
            f"It is {L['peak_why']}. Your last 8 weeks averaged {D(prof['recent8'])}; the most you have held for 8 weeks in 3 years is {D(prof['best8_3y'])}"
            + (f", and without breaking down afterwards {D(prof['proven8_3y'])} (3 years) and {D(prof['proven8_all'])} (ever)." if prof.get("proven8_all") else "."),
            "Previous injury is the strongest predictor of the next one (Hulme and colleagues, 2017; Desai and colleagues, 2021), so a block that ended in a "
            "breakdown does not set the ceiling. The rule itself is this project's inference; no study tests it directly.")
        proven = L.get("proven_miles") or 0
        add("How fast the miles build", f"{c['weekly_increase']:.0%} a week up to {D(proven)}, then {c['weekly_increase'] / 2:.1%}; level for three weeks after a week without running.",
            f"{D(proven)} is the most you have held for 8 weeks in the last year. You have gone {prof.get('weeks_unbroken', 0)} weeks without a week off running.",
            "Week-to-week mileage change did not predict injury in 5,205 runners (Schuster Brandt Frandsen and colleagues, 2025), but jumps of 20 to 60% did in runners "
            "preparing for a half marathon (Damsted and colleagues, 2019). A break of 7 days or more cost marathon runners 5 to 8% (Feely and colleagues, 2022). "
            "The 6% and 3% are this project's choices.")

    # ---- this week
    if s:
        names = {"build": "a building week", "down": "a down week", "taper": "a taper week", "race": "race week", "tuneup": "a tune-up race week",
                 "postrace": "a recovery week after a race", "recover": "a recovery week", "return": "a return week after a break"}
        add("This week", f"{names.get(s['mode'], s['mode']).capitalize()}: {engine.dist(s['total'], c['units'])}.",
            " ".join(s["why"]) or "Nothing unusual this week.",
            "Warning signs: " + ("; ".join(s["flags"]) if s["flags"] else "none this week") + ". "
            f"{c['flags_to_back_off']} or more turn the week into a recovery week (this project's choice).")

    # ---- the long run
    add("The long run", f"Up to {D(L['long_run_cap_specific'])} in the race-specific phase, {D(L['long_run_cap_base'])} before it, and never more than 10% beyond your longest run of the last 30 days.",
        "The cap scales from your peak week and your goal distance. Except for an ultra it also stops at about three hours at your easy pace.",
        "A run more than 10% longer than the longest of the previous 30 days went with 64% more overuse injuries (Schuster Brandt Frandsen and colleagues, 2025). "
        "The three-hour limit is a coaching convention.")

    # ---- hard sessions
    n = max(2, min(int(c["run_days"]), 6, 7 - len(c.get("blocked_days") or [])))
    em = resp.get("emphasis") or {}
    add("Hard sessions each week", ("Two, plus the long run" if n >= 5 else "One, plus the long run") + f", on {n} running days. Hard days are never back to back."
        + (" Before the race-specific phase, every other week has one, with the second day run easy." if em.get("kind") == "miles" and n >= 5 else ""),
        em.get("text") or "There is not enough history yet to tell whether you respond more to miles or to hard running.",
        "The fastest marathon runners train more, almost all of it easy (Muniz-Pumares and colleagues, 2024). People differ in how they respond to the same training "
        "(Hecksteden and colleagues, 2015), and those who do not respond to one dose respond to more (Montero and Lundby, 2017). The comparison of your own blocks is an "
        "association in one person's history, built on your watch's fitness estimate, which is approximate (Carrier and colleagues, 2025).")

    kinds = {"marathon": "threshold, marathon pace midweek and in some long runs, and faster intervals every third week",
             "half": "threshold and half marathon pace", "short": "threshold, and intervals at 5K and 10K pace",
             "ultra": "threshold in short blocks, long runs run easy, and back-to-back weekend runs", "general": "threshold, with a steady finish or an aerobic run by heart rate"}
    add("Which sessions", f"For your goal: {kinds[gtype]}.",
        "Each session grows by one step from the biggest you did in the last three weeks, so the next one is always within reach of the last.",
        "Threshold work in a high-volume, mostly easy week is the pattern of the most successful distance programmes (Casado and colleagues, 2023). "
        "The step sizes are this project's choice.")

    # ---- taper
    tp_ = resp.get("taper") or {}
    if goal:
        depth = (35 if gtype in ("marathon", "ultra", "half") else 30) + round(100 * (L.get("taper_shift") or 0))
        add("Your taper", (f"Three weeks: distance down 20%, then {depth}%, then race week." if gtype in ("marathon", "ultra")
                           else f"Distance down {depth}% the week before, then race week.") + " The fast running stays in, in smaller amounts.",
            tp_.get("text") or "There are not enough races in your history yet to learn your own taper.",
            "A two-week taper with volume cut by 41 to 60% and intensity kept gave the largest gains across trials (Bosquet and colleagues, 2007). In 158,000 "
            "recreational marathon runners, three weeks of steadily falling volume went with a 2.6% faster time than a minimal taper (Smyth and Lawlor, 2021).")

    # ---- recovery rhythm
    age = engine.age_on(c.get("birth_date"), mon) if c.get("birth_date") else None
    every = min(c["build_weeks_before_down"], 2) if age and age >= 50 else c["build_weeks_before_down"]
    add("Down weeks", f"After {every} full weeks, a week at 75%.",
        (f"You are {age}. " if age else "Your date of birth is not set. ") + ("From 50 the down week comes every third week." if age and age >= 50 else "From 50 it would come every third week."),
        "A coaching convention; recovery slows with age (Tanaka and Seals, 2008, for the decline in performance), but no trial fixes the rhythm.")
    add("Day-to-day tuning", "Each morning the day's fast paces are eased, or the session becomes an easy run, if your recovery signs are poor. Easy runs are left alone.",
        f"The signs are last night's sleep, three nights of sleep, your 7-day heart-rate variability and resting heart rate against your own normal range, and unusually heavy days on your feet. "
        f"A sign counts when HRV falls under {c['hrv_drop_fraction']:.0%} of your normal, resting heart rate rises {c['rhr_rise_bpm']} bpm, or 7 nights average under {c['sleep_7night_min_h']:g} hours.",
        "HRV and resting heart rate are read as 7-day trends against your own range (Plews and colleagues, 2012, 2013). Training guided this way gives small gains and "
        "fewer non-responders (Düking and colleagues, 2021). One short night reduces endurance performance (Craven and colleagues, 2022).")

    # ---- sex
    sex = c.get("sex")
    add("Sex", {"M": "The plan structure is the same for everyone. For you, long-race notes press the patient start.",
                "F": "The plan structure is the same for everyone. For you, a warning about a jump in run length also describes bone stress pain."}
        .get(sex, "Not set, so no sex-specific advice is given. The plan structure is the same for everyone."),
        "Men slow more in the second half of a marathon; bone stress injuries are about twice as common in women.",
        "Deaner and colleagues (2015); Hollander and colleagues (2021). Across the menstrual cycle the average effect on performance is trivial and individual "
        "(McNulty and colleagues, 2020), so training is not planned by cycle phase.")

    # ---- what stands between you and the goal
    if goal and s and wk:
        now_s, full_s = assess.projection({"tp": wk[0]["tp"], "endurance": s["endurance"]}, c, goal["miles"])
        gs = _goal_seconds(goal.get("goal_time")) if goal.get("goal_time") else None
        parts = sorted((s.get("endurance_parts") or {}).items(), key=lambda kv: kv[1])
        weakest = f" The part of your endurance furthest from full is {parts[0][0]} ({parts[0][1]:.0%} of what the plan looks for)." if parts else ""
        gap = ""
        if gs:
            gap = (f" Your goal is {engine.hms(gs)}: " + (f"{engine.hms(now_s - gs)} to find." if now_s > gs else "your current fitness already predicts it."))
            if now_s > gs:
                speed_gap, end_gap = full_s - gs, now_s - full_s
                gap += (" Most of that is endurance, not speed: with full endurance your current speed predicts " + engine.hms(full_s) + "."
                        if end_gap > max(speed_gap, 0) else " Most of that is speed: even with full endurance your current threshold predicts " + engine.hms(full_s) + ".")
        add("What stands between you and your goal", f"Today's fitness predicts {engine.hms(now_s)}; with the endurance the plan builds, {engine.hms(full_s)}.{gap}",
            f"The prediction comes from your threshold pace and how well your recent training supports holding pace over the distance.{weakest}",
            "Marathon time is set by aerobic capacity, the fraction of it that can be held, and running economy (Joyner and Coyle, 2008), and by how well those hold up late "
            "in the race (Jones, 2024). Faster runners hold a higher fraction of their critical speed, 93% at 2:30 against 79% at 6:00 (Smyth and Muniz-Pumares, 2020), "
            "and what separates them in training is volume, most of it easy (Doherty and colleagues, 2020; Muniz-Pumares and colleagues, 2024). Runners who start "
            "faster than they can sustain are the ones who hit the wall (Smyth, 2021).")
    return out
