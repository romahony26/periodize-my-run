"""Race results: found in the athlete's history, or entered by hand, each with its race index."""
import csv
import datetime as dt
import io
import json
import re

import db
import equiv

NEAR_BEST = 0.94   # a run at a race distance counts as a race if its race index is within 6% of the best around that time


def detect():
    """Find likely races: runs of a standard race distance, run close to the athlete's best of that period.

    Garmin's own "race" label is used when the athlete has set it. Otherwise this is a guess, and results can be removed in the app.
    """
    runs = db.rows("SELECT id,date,name,dist_m,timer_s FROM activities WHERE sport='running' AND dist_m>4900 AND timer_s>0 ORDER BY date")
    cands = []
    for r in runs:
        rd = equiv.race_distance(r["dist_m"])
        if rd:
            cands.append((r, rd, equiv.index(rd[1], r["timer_s"] * rd[1] / r["dist_m"])))
    known = {r["activity_id"] for r in db.rows("SELECT activity_id FROM results WHERE activity_id IS NOT NULL")}
    logged = [(dt.date.fromisoformat(r["date"]), r["dist_m"]) for r in db.rows("SELECT date,dist_m FROM results WHERE source IN ('log','entered') AND dist_m IS NOT NULL")]
    new = 0
    for r, (name, official), v in cands:
        if r["id"] in known:
            continue
        if any(abs((dt.date.fromisoformat(r["date"]) - d).days) <= 1 and abs(m - official) / official < 0.06 for d, m in logged):
            continue      # already in the athlete's own log, with the official time
        day = dt.date.fromisoformat(r["date"])
        era = [x[2] for x in cands if abs((dt.date.fromisoformat(x[0]["date"]) - day).days) <= 365]
        if v >= NEAR_BEST * max(era):
            db.run("INSERT OR IGNORE INTO results(date,name,dist_m,time_s,source,activity_id) VALUES(?,?,?,?,?,?)",
                   (r["date"], f"{name}" + (f" · {r['name']}" if r["name"] else ""), official, r["timer_s"] * official / r["dist_m"], "found", r["id"]))
            new += 1
    # ultras: anything clearly longer than a marathon. Kept as a result, but not counted toward fitness numbers (terrain and distance vary too much).
    for r in db.rows("SELECT id,date,name,dist_m,timer_s FROM activities WHERE sport='running' AND dist_m>43500 AND timer_s>0"):
        if r["id"] not in known and not any(abs((dt.date.fromisoformat(r["date"]) - d).days) <= 1 and abs(m - r["dist_m"]) / r["dist_m"] < 0.1 for d, m in logged):
            db.run("INSERT OR IGNORE INTO results(date,name,dist_m,time_s,source,activity_id,counts) VALUES(?,?,?,?,?,?,0)",
                   (r["date"], f"Ultra {r['dist_m'] / 1000:.0f} km" + (f" · {r['name']}" if r["name"] else ""), r["dist_m"], r["timer_s"], "found", r["id"]))
            new += 1
    return new


def _course_factor(r, trust):
    """How much harder the course was than flat (1.03 = 3% harder), from the run's own altitude when the watch can be trusted. None if unknown."""
    acts = db.rows("SELECT detail FROM activities WHERE id=? AND detail IS NOT NULL", (r["activity_id"],)) if r["activity_id"] else \
        db.rows("SELECT detail FROM activities WHERE sport='running' AND date=? AND detail IS NOT NULL AND ABS(dist_m-?)<?*0.06", (r["date"], r["dist_m"], r["dist_m"]))
    for a in acts:
        d = json.loads(a["detail"])
        if d.get("gap_ok") and d.get("gap_ratio") and trust.get(d.get("device"), {}).get("trusted", True) and (d.get("loop_alt_err") or 0) <= 20:
            return min(max(d["gap_ratio"], 0.97), 1.20)
    return None


def listing(units="mi", everything=False):
    """Results that count toward the fitness model (road and track races with a time). `everything` adds cross-country, trail and paced runs.

    Where the course's hills are known from a trusted watch, the index and pace are for the flat-equivalent time.
    """
    out = []
    trust = db.get("altitude_trust") or {}
    per = equiv.MI if units == "mi" else 1000
    for r in db.rows("SELECT * FROM results WHERE hidden=0 AND time_s IS NOT NULL AND (?=1 OR COALESCE(counts,1)=1) ORDER BY date DESC", (int(everything),)):
        f = _course_factor(r, trust) if (r["counts"] is None or r["counts"]) else None
        flat = r["time_s"] / f if f else r["time_s"]
        s = round(flat / (r["dist_m"] / per))
        out.append({"id": r["id"], "date": r["date"], "name": r["name"], "dist_m": r["dist_m"], "time_s": r["time_s"], "flat_s": flat, "course": round((f - 1) * 100, 1) if f else None,
                    "pace": f"{s // 60}:{s % 60:02d}/{units}", "index": round(equiv.index(r["dist_m"], flat), 1), "source": r["source"],
                    "note": r["note"] or "", "weight_kg": r["weight_kg"], "counts": 1 if r["counts"] is None else r["counts"]})
    return out


# ---------------------------------------------------------------- importing a race log
DIST_WORDS = [(r"^(1/2|half)", 21097.5), (r"^mar", 42195.0), (r"^26\.2", 42195.0), (r"^(\d{3,5})\s*m\b", "m"), (r"^(\d+(?:\.\d+)?)\s*k(m)?\b", "km"),
              (r"^(\d+(?:\.\d+)?)\s*m(i|ile|iles)?\b(?!\w)", "mi")]   # metres (3000m) are tried before miles (10M)
OFF_ROAD = re.compile(r"\bxc\b|cross.?country|trail|\bimra\b|mountain|fell", re.I)
PACED = re.compile(r"^\s*pacing\s*$|\bpacer for\b|\bas a pacer\b", re.I)


def _seconds(text):
    p = [x for x in re.split(r"[:.]", (text or "").strip()) if x != ""]
    if len(p) < 2 or not all(x.isdigit() for x in p[:3]):
        return None
    p = [int(x) for x in p[:3]]
    return p[0] * 3600 + p[1] * 60 + p[2] if len(p) == 3 else p[0] * 60 + p[1]


def _distance(length, miles):
    """Metres from the event name ('5K', '10M', '1/2 Mar', '3000m'), falling back to a miles column."""
    t = (length or "").strip().lower()
    for pat, kind in DIST_WORDS:
        m = re.match(pat, t)
        if m:
            if kind == "km":
                return float(m.group(1)) * 1000
            if kind == "mi":
                return float(m.group(1)) * equiv.MI
            if kind == "m":
                return float(m.group(1))
            return kind
    try:
        return float(miles) * equiv.MI if miles and float(miles) > 0 else None
    except ValueError:
        return None


def _date(text):
    for fmt in ("%d %b %Y", "%d %B %Y", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d %b %y"):
        try:
            return dt.datetime.strptime(text.strip(), fmt).date()
        except ValueError:
            continue
    return None


def import_csv(text):
    """Read a race log. Columns are matched by name, so the order and extra columns do not matter.

    Needs a date and either an event name or a miles column. Official times replace times found in Garmin for the same race.
    Cross-country, trail and paced races are kept with their notes but do not count toward the fitness model. DNF and DNS rows keep their notes.
    """
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        return {"added": 0, "updated": 0, "skipped": 0}
    head = [h.strip().lower() for h in rows[0]]

    def col(*names):
        for n in names:
            for i, h in enumerate(head):
                if h == n or h.startswith(n):
                    return i
        return None

    ci = {"date": col("date"), "length": col("length", "distance", "event", "race distance"), "miles": col("miles"), "time": col("time", "result", "finish"),
          "loc": col("location", "race", "name"), "note": col("comment", "notes", "note", "lessons"), "weight": col("weight")}
    if ci["date"] is None or (ci["length"] is None and ci["miles"] is None):
        raise ValueError("The file needs a Date column and a Length (or Miles) column.")
    get = lambda r, k: (r[ci[k]].strip() if ci[k] is not None and ci[k] < len(r) else "")
    added = updated = skipped = 0
    for r in rows[1:]:
        day = _date(get(r, "date"))
        if not day:
            skipped += bool(any(x.strip() for x in r[1:]))
            continue
        dist_m, secs = _distance(get(r, "length"), get(r, "miles")), _seconds(get(r, "time"))
        note, loc, length = get(r, "note"), get(r, "loc"), get(r, "length")
        name = f"{length} · {loc}" if loc else length
        try:
            weight = float(get(r, "weight")) if get(r, "weight") else None
        except ValueError:
            weight = None
        if not secs or not dist_m:           # DNF / DNS: keep the lesson, no time
            if note:
                db.run("DELETE FROM results WHERE date=? AND time_s IS NULL", (day.isoformat(),))
                db.run("INSERT INTO results(date,name,dist_m,time_s,source,note,weight_kg,counts) VALUES(?,?,?,NULL,'log',?,?,0)",
                       (day.isoformat(), f"{name} ({get(r, 'time') or 'no time'})", dist_m, note, weight))
                added += 1
            else:
                skipped += 1
            continue
        counts = 0 if OFF_ROAD.search(name + " " + note[:60]) or PACED.search(note) else 1
        near = [x for x in db.rows("SELECT * FROM results WHERE date BETWEEN ? AND ? AND time_s IS NOT NULL",
                                   ((day - dt.timedelta(days=1)).isoformat(), (day + dt.timedelta(days=1)).isoformat()))
                if abs(x["dist_m"] - dist_m) / dist_m < 0.06]
        if near:
            db.run("UPDATE results SET date=?,name=?,dist_m=?,time_s=?,source='log',note=?,weight_kg=?,counts=?,hidden=0 WHERE id=?",
                   (day.isoformat(), name, dist_m, secs, note, weight, counts, near[0]["id"]))
            updated += 1
        else:
            db.run("INSERT INTO results(date,name,dist_m,time_s,source,note,weight_kg,counts) VALUES(?,?,?,?,'log',?,?,?)", (day.isoformat(), name, dist_m, secs, note, weight, counts))
            added += 1
    return {"added": added, "updated": updated, "skipped": skipped}


def _fastest(xs):
    return min(xs, key=lambda x: x["time_s"], default=None)


def _brief(x):
    return {"time_s": round(x["time_s"]), "date": x["date"], "race": x["name"].split(" · ")[-1], "official": x["source"] in ("log", "entered")} if x else None


def bests(today=None):
    """Personal bests by distance from the athlete's race results.

    Times from the athlete's own log or entered by hand are official and take priority. A faster time that exists only on the
    watch is shown beside it, not as the best, because watch distance is not a measured course.
    """
    today = today or dt.date.today()
    year = (today - dt.timedelta(days=365)).isoformat()
    rows = db.rows("SELECT * FROM results WHERE hidden=0 AND time_s IS NOT NULL AND COALESCE(counts,1)=1")
    out = []
    for name, metres in equiv.DISTANCES:
        rs = [r for r in rows if abs(r["dist_m"] - metres) / metres < 0.012]
        if not rs:
            continue
        official = [r for r in rs if r["source"] in ("log", "entered")]
        best = _fastest(official) or _fastest(rs)
        limit = best["time_s"] - 0.5
        watch = _fastest([x for x in rs if x["source"] == "found" and x["time_s"] < limit]) if official else None
        out.append({"name": name, "best": _brief(best), "watch": _brief(watch), "year": _brief(_fastest([x for x in rs if x["date"] >= year]))})
    return out
