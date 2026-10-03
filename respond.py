"""How this athlete has responded to training, worked out from their whole history. Nothing is entered by hand.

Two questions, each answered only when there is enough history, and each allowed to move the plan only inside the range the
research supports:

  - Taper: before the athlete's best races, was the last week cut deeply or lightly? The research average is a two-week taper with
    volume cut by 41-60% (Bosquet and colleagues, 2007) and, for recreational marathon runners, up to three weeks of steadily
    falling volume (Smyth and Lawlor, 2021). The athlete's own record chooses a point inside that range.
  - Volume or intensity: over eight-week blocks, did fitness rise more with more miles or with more hard running? People differ
    in how they respond to the same training (Hecksteden and colleagues, 2015), and those who do not respond to one dose respond to
    a larger one (Montero and Lundby, 2017).

Both are associations in one person's history, not experiments: a deep taper may simply mark the races that mattered, and fitness
estimates from a watch are approximate. So each result carries its sample size, and stays "not clear" unless the pattern is strong.
"""
import datetime as dt

import db
import equiv

MI = 1609.344
MIN_RACES, MIN_BLOCKS = 6, 10
TAPER_STEP = 0.05          # how far the athlete's own record may move the taper, either way
CLEAR = 0.40               # rank correlation needed before a pattern is called clear


def _rank(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2
        i = j + 1
    return r


def spearman(xs, ys):
    """Rank correlation, -1 to 1. None with fewer than 4 pairs or no spread."""
    if len(xs) < 4:
        return None
    a, b = _rank(xs), _rank(ys)
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    va, vb = sum((x - ma) ** 2 for x in a), sum((y - mb) ** 2 for y in b)
    if not va or not vb:
        return None
    return sum((x - ma) * (y - mb) for x, y in zip(a, b, strict=True)) / (va * vb) ** 0.5


def _daily(runs):
    out = {}
    for r in runs:
        d = dt.date.fromisoformat(r["date"])
        out[d] = out.get(d, 0.0) + (r["dist_m"] or 0) / MI
    return out


def taper(runs, races):
    """The athlete's tapers before past races, set against how well each race went.

    `races` is [{date, dist_m, time_s}] of counted road results of 15 km or more. How well a race went is its performance index
    as a fraction of the best index within a year either side, so a race is judged against the athlete's level at the time.
    """
    day = _daily(runs)
    rows = []
    for r in races:
        d = dt.date.fromisoformat(r["date"])
        miles = lambda a, b: sum(v for k, v in day.items() if d - dt.timedelta(days=a) <= k < d - dt.timedelta(days=b))   # noqa: B023
        usual = miles(63, 21) / 6
        if usual < 10:
            continue
        near = [equiv.index(x["dist_m"], x["time_s"]) for x in races if abs((dt.date.fromisoformat(x["date"]) - d).days) <= 365]
        rows.append({"date": r["date"], "last_week": miles(7, 0) / usual, "week_before": miles(14, 7) / usual,
                     "level": equiv.index(r["dist_m"], r["time_s"]) / max(near)})
    out = {"races": len(rows), "shift": 0.0, "clear": False}
    if len(rows) < MIN_RACES:
        out["text"] = (f"Not enough races yet to learn your taper ({len(rows)} of the {MIN_RACES} needed, of 15 km or more with training before them). "
                       "The plan uses the research average.")
        return out
    cuts = sorted(x["last_week"] for x in rows)
    mid = (cuts[len(cuts) // 2] + cuts[(len(cuts) - 1) // 2]) / 2
    deep, light = [x for x in rows if x["last_week"] <= mid], [x for x in rows if x["last_week"] > mid]
    avg = lambda xs, k: sum(x[k] for x in xs) / len(xs)
    rho = spearman([x["last_week"] for x in rows], [x["level"] for x in rows])
    gap = 100 * (avg(deep, "level") - avg(light, "level"))
    out.update({"rho": round(rho, 2) if rho is not None else None, "usual_cut": round(100 * (1 - mid)), "gap_pct": round(gap, 1),
                "deep_cut": round(100 * (1 - avg(deep, "last_week"))), "light_cut": round(100 * (1 - avg(light, "last_week")))})
    if rho is not None and abs(rho) >= CLEAR and len(deep) >= 3 and len(light) >= 3:
        out["clear"] = True
        out["shift"] = -TAPER_STEP if rho > 0 else TAPER_STEP        # raced better after lighter last weeks: cut less; after deeper: cut more
        better = "lighter" if rho > 0 else "deeper"
        out["text"] = (f"Across {len(rows)} races you raced better after a {better} taper: the last week was cut by about {out['deep_cut']}% before one half of them "
                       f"and {out['light_cut']}% before the other, and the {better} half were {abs(gap):.1f}% closer to your best level of the time. "
                       f"Your taper is moved {int(TAPER_STEP * 100)} points that way, inside the range the research supports.")
    else:
        out["text"] = (f"Across {len(rows)} races, how deeply you cut the last week (typically about {out['usual_cut']}%) shows no clear link with how well you raced. "
                       "The plan uses the research average.")
    return out


def blocks(runs, hrmax, weeks=8):
    """Eight-week blocks across the history: miles a week, hard runs a week, and the change in the watch's fitness estimate."""
    if not hrmax:
        return []
    fit = [(dt.date.fromisoformat(r["date"]), r["vo2max"]) for r in runs if r["vo2max"]]
    if len(fit) < 60:
        return []
    med = lambda xs: sorted(xs)[len(xs) // 2]
    out, start, end = [], fit[0][0] + dt.timedelta(days=21), fit[-1][0]
    span = dt.timedelta(weeks=weeks)
    while start + span <= end:
        stop = start + span
        inside = [r for r in runs if start.isoformat() <= r["date"] < stop.isoformat()]
        before = [v for d, v in fit if start - dt.timedelta(days=21) <= d < start]
        after = [v for d, v in fit if stop - dt.timedelta(days=21) <= d < stop]
        if len(inside) >= 2 * weeks and len(before) >= 3 and len(after) >= 3:
            hard = sum(1 for r in inside if r["avg_hr"] and r["avg_hr"] >= 0.82 * hrmax and (r["timer_s"] or 0) >= 1200)
            out.append({"start": start.isoformat(), "miles": sum((r["dist_m"] or 0) for r in inside) / MI / weeks, "hard": hard / weeks,
                        "from": med(before), "gain": med(after) - med(before)})
        start = stop
    return out


def emphasis(runs, hrmax):
    """Whether fitness has risen more with more miles or with more hard running."""
    bl = blocks(runs, hrmax)
    out = {"blocks": len(bl), "kind": None, "clear": False}
    if len(bl) < MIN_BLOCKS:
        out["text"] = (f"Not enough history yet to tell whether you respond more to miles or to hard running ({len(bl)} of the {MIN_BLOCKS} eight-week blocks needed, "
                       "each with a fitness estimate from your watch).")
        return out
    # a block that starts from a low level gains more whatever is done (regression to the mean), so the starting level is taken out first
    lv, gn = [b["from"] for b in bl], [b["gain"] for b in bl]
    ml, mg = sum(lv) / len(lv), sum(gn) / len(gn)
    var = sum((x - ml) ** 2 for x in lv)
    slope = sum((x - ml) * (g - mg) for x, g in zip(lv, gn, strict=True)) / var if var else 0.0
    resid = [g - mg - slope * (x - ml) for x, g in zip(lv, gn, strict=True)]
    rv, rh = spearman([b["miles"] for b in bl], resid), spearman([b["hard"] for b in bl], resid)
    out.update({"rho_miles": round(rv, 2) if rv is not None else None, "rho_hard": round(rh, 2) if rh is not None else None})
    rv, rh = rv or 0.0, rh or 0.0
    if rv >= CLEAR and rv - rh >= 0.15:
        out.update(kind="miles", clear=True, text=f"Across {len(bl)} eight-week blocks, your fitness rose more in the blocks with more miles "
                   f"(rank correlation {rv:.2f}) than in those with more hard runs ({rh:.2f}). The plan leans on easy volume for you.")
    elif rh >= CLEAR and rh - rv >= 0.15:
        out.update(kind="hard", clear=True, text=f"Across {len(bl)} eight-week blocks, your fitness rose more in the blocks with more hard runs "
                   f"(rank correlation {rh:.2f}) than in those with more miles ({rv:.2f}). The plan keeps both weekly sessions for you.")
    else:
        out["text"] = (f"Across {len(bl)} eight-week blocks, neither more miles (rank correlation {rv:.2f}) nor more hard runs ({rh:.2f}) stands out as what "
                       "raises your fitness. The plan uses the usual balance.")
    return out


def derive(hrmax):
    """Work both out from the stored history and keep them."""
    runs = db.rows("SELECT date,dist_m,timer_s,avg_hr,vo2max FROM activities WHERE sport='running' AND date!='' AND dist_m>0 ORDER BY date")
    races = [dict(r) for r in db.rows("SELECT date,dist_m,time_s FROM results WHERE hidden=0 AND counts=1 AND dist_m>=15000 AND time_s>0 AND date!='' ORDER BY date")]
    out = {"taper": taper(runs, races), "emphasis": emphasis(runs, hrmax), "as_of": dt.date.today().isoformat()}
    db.put("response", out)
    return out
