"""The pipeline (download, assess, plan, adjust, send) and the scheduler that keeps it running."""
import datetime as dt
import hashlib
import json
import secrets
import threading
import time
import traceback

import assess
import backup
import calibrate
import db
import engine
import execution
import garmin
import aerobic
import profile
import push
import results
import trends
import vault
from log import log, scrub

_lock = threading.Lock()
status = {"running": None, "progress": "", "error": None}


def races():
    out = db.rows("SELECT * FROM races ORDER BY date")
    for r in out:
        r["date"] = dt.date.fromisoformat(r["date"])
    return out


def context():
    c = db.cfg()
    c["threshold_correction"] = calibrate.value("threshold_correction")
    prof = db.get("profile") or profile.derive()
    rs = races()
    goal = engine.goal_race(rs, dt.date.today())
    return c, prof, rs, profile.limits(prof, c, goal["miles"] if goal else None) if prof else None


def _store_week(monday, st, pl, final, c, today):
    summary = {"mode": pl["mode"], "target": pl["target"], "total": pl["total"], "weeks_to_race": pl["weeks_to_race"], "why": pl["why"],
               "flags": st["flags"], "health": st["health"], "endurance": st["endurance"], "endurance_parts": st["endurance_parts"],
               "tp_why": st["tp_why"], "tp_raw": st["tp_raw"], "tp_prev": st["tp_prev"],
               "weeks": [dict(w, start=w["start"].isoformat()) for w in st["weeks"]]}
    db.run("INSERT INTO weeks(monday,mode,target,why,tp,final,summary) VALUES(?,?,?,?,?,?,?) ON CONFLICT(monday) DO UPDATE SET "
           "mode=excluded.mode,target=excluded.target,why=excluded.why,tp=excluded.tp,final=excluded.final,summary=excluded.summary",
           (monday.isoformat(), pl["mode"], pl["target"], json.dumps(pl["why"]), st["tp"], int(final), json.dumps(summary)))
    days = engine.apply_status([dict(d) for d in pl["days"]], db.rows("SELECT * FROM status"))
    with db.connect() as con:
        for d in days:
            if d["date"] < today:
                continue
            con.execute("INSERT INTO plan(date,type,label,miles,steps,strength,note,source,adjust) VALUES(?,?,?,?,?,?,?,'auto',NULL) "
                        "ON CONFLICT(date) DO UPDATE SET type=excluded.type,label=excluded.label,miles=excluded.miles,steps=excluded.steps,"
                        "strength=excluded.strength,note=excluded.note,source='auto',adjust=NULL",
                        (d["date"].isoformat(), d["type"], d["label"], d["miles"], json.dumps(d["steps"]) if d["steps"] else None, d["strength"], d["note"]))


def swap(a, b):
    """Swap the sessions of two dates."""
    ra, rb = db.rows("SELECT * FROM plan WHERE date=?", (a,)), db.rows("SELECT * FROM plan WHERE date=?", (b,))
    if not ra or not rb:
        return False
    cols = ("type", "label", "miles", "steps", "note")
    with db.connect() as con:
        for src, dst in ((ra[0], b), (rb[0], a)):
            con.execute("UPDATE plan SET type=?,label=?,miles=?,steps=?,note=?,source='moved',adjust=NULL WHERE date=?", tuple(src[k] for k in cols) + (dst,))
    return True


def replay_moves(today):
    """After a replan, put the athlete's own rearrangements back (those still in the future)."""
    db.run("DELETE FROM moves WHERE a<? OR b<?", (today.isoformat(), today.isoformat()))
    for m in db.rows("SELECT * FROM moves ORDER BY id"):
        swap(m["a"], m["b"])


def safe_url(url):
    """Is this an address the app may post to? http(s) only, and never this computer or a cloud metadata address.

    Stops the notification setting being used to make the app call its own or other local services (server-side request forgery).
    Home-network addresses are allowed, because people run their own notification servers there.
    """
    import ipaddress
    import socket
    from urllib.parse import urlsplit
    try:
        parts = urlsplit(url)
        if parts.scheme not in ("https", "http") or not parts.hostname or parts.username or parts.password:
            return False
        for info in socket.getaddrinfo(parts.hostname, parts.port or (443 if parts.scheme == "https" else 80), proto=socket.IPPROTO_TCP):
            ip = ipaddress.ip_address(info[4][0].split("%")[0])
            ip = getattr(ip, "ipv4_mapped", None) or ip          # ::ffff:127.0.0.1 is 127.0.0.1
            if ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_unspecified or ip.is_reserved:
                return False
        return True
    except (ValueError, OSError):
        return False


def notify(text):
    """Optional: POST a short plain-text message to an address the athlete chose (for example an ntfy topic)."""
    url = vault.get("notify_url")
    if not url:
        return
    if not safe_url(url):
        log.warning("Notification address refused: it must be http(s) and must not point at this computer")
        return
    try:
        import requests
        requests.post(url, data=text.encode(), headers={"Title": "Periodize My Run", "Content-Type": "text/plain; charset=utf-8"}, timeout=15, allow_redirects=False)
        log.info("Notification sent")
    except Exception as e:
        log.warning("Notification failed: %s", type(e).__name__)


def today_message():
    c, today = db.cfg(), dt.date.today()
    r = db.rows("SELECT * FROM plan WHERE date=?", (today.isoformat(),))
    if not r:
        return None
    r = r[0]
    wk = db.rows("SELECT tp FROM weeks WHERE monday=?", ((today - dt.timedelta(days=today.weekday())).isoformat(),))
    adj = json.loads(r["adjust"]) if r["adjust"] else {}
    day = engine.as_run(dict(r, steps=json.loads(r["steps"]) if r["steps"] else None), adj)
    text = engine.describe(day, wk[0]["tp"], c["units"], adj.get("slow", 0.0)) if wk and day["steps"] else ""
    rd = db.get("readiness") or {}
    out = f"Today: {day['label']}" + (f" {engine.dist(r['miles'], c['units'])}" if r["miles"] else "") + (f"\n{text}" if text else "")
    if adj.get("easy"):
        out += "\n" + adj["advice"] + " " + "; ".join(adj.get("reasons", []))
    elif adj.get("slow"):
        out += f"\nPaces eased {adj['slow']:.1%}: " + "; ".join(adj.get("reasons", []))
    elif rd.get("level") in ("green", "amber"):
        out += "\nRecovery: " + "; ".join(rd.get("reasons", []))
    return out


def replan(force=False):
    """Plan the current week from actual data, and the following week provisionally."""
    c, prof, rs, L = context()
    if not prof:
        return
    today = dt.date.today()
    mon = today - dt.timedelta(days=today.weekday())
    prev = db.rows("SELECT tp FROM weeks WHERE monday<? AND final=1 ORDER BY monday DESC LIMIT 1", (mon.isoformat(),))
    st = assess.assess(c, L, mon, prev[0]["tp"] if prev else None)
    if st is None:   # no running in the last eight weeks: start from the athlete's recent race, or a cautious guess
        st = assess.assess(c, L, mon, c.get("seed_threshold") or assess.MI / 540)
    if st is None:
        log.warning("Not enough running data in the last eight weeks to plan from")
        return
    pl = engine.plan(st, c, L, rs)
    cur = db.rows("SELECT final FROM weeks WHERE monday=?", (mon.isoformat(),))
    if force or not cur or not cur[0]["final"]:
        _store_week(mon, st, pl, True, c, today)
        log.info("Week of %s planned from your data: %s week, %s, threshold %s/%s", mon, pl["mode"], engine.dist(pl["total"], c["units"]),
                 engine.pace(st["tp"], c["units"]), c["units"])
    # the following weeks are provisional: each assumes the one before goes to plan, and all are redone at every weekly review
    ahead = max(int(c["weeks_ahead"]), -(-int(c["push_days"]) // 7))   # always plan far enough ahead to fill the watch
    for k in range(1, ahead + 1):
        st = engine.project(st, pl)
        pl = engine.plan(st, c, L, rs)
        _store_week(mon + dt.timedelta(weeks=k), st, pl, False, c, today)
        log.info("Week of %s planned provisionally: %s week, %s", mon + dt.timedelta(weeks=k), pl["mode"], engine.dist(pl["total"], c["units"]))
    season, n = [], 0                     # an outline of every week to the goal race, each assuming the one before goes to plan
    while pl.get("goal") and n < 60:
        st = engine.project(st, pl)
        pl = engine.plan(st, c, L, rs)
        n += 1
        season.append({"monday": st["monday"].isoformat(), "mode": pl["mode"], "total": pl["total"], "long": pl["long"]})
        if pl["mode"] == "race" and pl["goal"] and pl["goal"]["date"] < st["monday"] + dt.timedelta(days=7):
            break
    db.put("season", season)
    beyond = (mon + dt.timedelta(weeks=ahead + 1)).isoformat()
    db.run("DELETE FROM plan WHERE date>=? AND garmin_id IS NULL AND strength_id IS NULL", (beyond,))
    db.run("DELETE FROM weeks WHERE monday>=?", (beyond,))
    replay_moves(today)


def reshuffle(today=None):
    """A session missed earlier this week is moved to the first later day that keeps a day of easy running or rest either side of every hard day.

    It replaces that day's easy run. If no day fits, the session is dropped: cramming it in costs more than it gains.
    Hard days are never placed back to back; that spacing is standard coaching practice, not a research threshold.
    """
    today = today or dt.date.today()
    mon = today - dt.timedelta(days=today.weekday())
    c, prof, rs, L = context()
    wk = db.rows("SELECT tp FROM weeks WHERE monday=?", (mon.isoformat(),))
    if not L or not wk:
        return []
    tp, hard = wk[0]["tp"], ("Key", "Long", "Race")
    plan = {dt.date.fromisoformat(r["date"]): r for r in db.rows("SELECT * FROM plan WHERE date>=? AND date<?", (mon.isoformat(), (mon + dt.timedelta(days=7)).isoformat()))}
    runs = {}
    for r in assess.load_runs(mon, today):
        runs.setdefault(r["date"], []).append(r)
    ran = lambda d: sum(r["mi"] for r in runs.get(d, [])) >= 1
    off = [(dt.date.fromisoformat(s["start"]), dt.date.fromisoformat(s["end"]) if s["end"] else dt.date.max) for s in db.rows("SELECT start,end FROM status")]
    moved = {k: v for k, v in (db.get("reshuffled") or {}).items() if k >= mon.isoformat()}
    out = []
    for i in range((today - mon).days):
        d = mon + dt.timedelta(days=i)
        p = plan.get(d)
        if not p or p["type"] != "Key" or not p["steps"] or ran(d) or any(a <= d <= b for a, b in off):
            continue
        k = d.isoformat()
        if k in moved and (moved[k] is None or (plan.get(dt.date.fromisoformat(moved[k])) or {}).get("source") == "reshuffled"):
            continue
        elsewhere = any((plan.get(e) or {}).get("type") not in hard and (execution.score(p, rr, tp, L) or {}).get("score", 0) >= 65 for e, rr in runs.items() if e != d)
        if elsewhere:
            moved[k] = None           # the session was run on another day; nothing to move
            continue

        def is_hard(e):
            q = plan.get(e)
            return bool(q) and q["type"] in hard and (e >= today or ran(e))

        target = None
        for jx in range((today - mon).days, 7):
            e = mon + dt.timedelta(days=jx)
            q = plan.get(e)
            if q and q["type"] == "Easy" and q["source"] != "moved" and e.weekday() not in (c.get("blocked_days") or []) \
                    and not is_hard(e - dt.timedelta(days=1)) and not is_hard(e + dt.timedelta(days=1)) and not any(a <= e <= b for a, b in off):
                target = e
                break
        moved[k] = target.isoformat() if target else None
        if target:
            db.run("UPDATE plan SET type=?,label=?,miles=?,steps=?,note=?,source='reshuffled',adjust=NULL WHERE date=?",
                   (p["type"], p["label"], p["miles"], p["steps"], f"Moved from {d:%A}, which was missed.", target.isoformat()))
            plan[target] = dict(plan[target], type=p["type"], source="reshuffled")
            log.info("Missed session on %s (%s) moved to %s", d, p["label"], target)
            out.append((k, target.isoformat()))
        else:
            log.info("Missed session on %s (%s) dropped: no later day this week keeps hard days apart", d, p["label"])
    db.put("reshuffled", moved)
    return out


def adjust():
    """Today's readiness, and today's pace adjustment."""
    c = db.cfg()
    today = dt.date.today()
    r = engine.readiness(today, c)
    r["date"] = today.isoformat()
    db.put("readiness", r)
    hist = {k: v for k, v in (db.get("readiness_log") or {}).items() if k >= (today - dt.timedelta(days=14)).isoformat()}
    if r["level"] != "unknown":
        hist[today.isoformat()] = r["points"]
    db.put("readiness_log", hist)
    db.run("UPDATE plan SET adjust=NULL WHERE date>?", (today.isoformat(),))
    row = db.rows("SELECT * FROM plan WHERE date=?", (today.isoformat(),))
    if row and c["daily_adjust"]:
        steps = json.loads(row[0]["steps"]) if row[0]["steps"] else []
        fast = row[0]["type"] != "Race" and any((s[0] == "d" and s[2] in engine.QUALITY) or s[0] == "r" for s in steps)
        adj = {"slow": r["slow"], "reasons": r["reasons"], "level": r["level"]} if fast and r["slow"] > 0 else None
        # a bad morning, or a warning sign three mornings running, turns the session into an easy run: when signs persist, the
        # trials of readiness-guided training swapped hard days for easy ones rather than only slowing them
        run3 = all(hist.get((today - dt.timedelta(days=i)).isoformat(), 0) >= 1 for i in range(3))
        if adj and (r["level"] == "red" or run3):
            adj.update({"easy": True, "slow": 0.0, "advice": "Changed to an easy run today because " +
                        ("several warning signs agree." if r["level"] == "red" else "a warning sign has lasted three mornings.") +
                        " The session comes back once you have recovered."})
        db.run("UPDATE plan SET adjust=? WHERE date=?", (json.dumps(adj) if adj else None, today.isoformat()))
    log.info("Readiness today: %s (%s)", r["level"], "; ".join(r["reasons"]))
    return r


def _progress(m):
    status["progress"] = m


def run(kind):
    """Run one job now (blocking). kind: setup | daily | replan | readiness | push."""
    if not _lock.acquire(blocking=False):
        return False
    status.update({"running": kind, "progress": "Starting", "error": None})
    jid = db.run("INSERT INTO jobs(kind,started) VALUES(?,?)", (kind, dt.datetime.now().isoformat(timespec="seconds")))
    log.info("=== %s started ===", kind)
    ok, msg = True, ""
    try:
        c = db.cfg()
        if kind in ("setup", "daily"):
            _progress("Reading your activity history")
            garmin.sync_summaries(full=(kind == "setup"), progress=_progress)
            profile.derive()
            if not db.get("vo2max_backfilled") and kind == "daily":
                garmin.backfill_vo2max(_progress)
            found = results.detect()
            if found:
                log.info("Race results found in your history: %d new", found)
            _progress("Downloading recent runs")
            garmin.sync_details(c["detail_weeks"], _progress)
            _progress("Downloading sleep, HRV and heart rate")
            garmin.sync_daily(63 if kind == "setup" or db.rows("SELECT 1 FROM daily WHERE steps IS NOT NULL LIMIT 1") == [] else 10, _progress)
            garmin.sync_extras()
            garmin.sync_activity_steps(63 if db.rows("SELECT 1 FROM activities WHERE steps IS NOT NULL LIMIT 1") == [] else 10)
        if kind == "readiness":
            garmin.sync_daily(2, _progress)
        if kind in ("setup", "daily", "replan"):
            if aerobic.read_tests():
                log.info("Aerobic test read from your watch")
            _c, _p, _r, _L = context()
            if _L:
                up = aerobic.maybe_raise_lthr(_L)
                if up:
                    log.info("Aerobic-run heart rate moved up to %d: you ran 10 miles at the previous level", up)
            _progress("Learning from your data")
            m = calibrate.run()
            if m:
                log.info("Model: " + "; ".join(f"{k} {v['value']:.3f} ({'learned from ' + str(v['n']) if v['learned'] else 'default'})" for k, v in m.items() if isinstance(v, dict)))
            _progress("Planning")
            replan(force=(kind in ("setup", "replan")))
        reshuffle()
        adjust()
        if c["push_enabled"] and garmin.has_tokens():
            _progress("Sending workouts to Garmin")
            sent, removed, same = push.sync_calendar(db.cfg())
            msg = f"{sent} workouts sent, {same} unchanged"
        if kind in ("setup", "daily", "replan"):
            try:                       # keep the weekly fitness history for the trend charts up to date, so the page never waits for it
                _c, _p, _r, _L = context()
                if _L:
                    trends.history(_c, _L, dt.date.today())
            except Exception as e:
                log.error("Trend history update failed: %s", type(e).__name__)
        if kind == "daily" and c["auto_backup"]:
            backup.nightly()
        if kind == "setup":
            db.put("setup_done", True)
        if kind == "daily" or (kind == "readiness" and (db.get("readiness") or {}).get("level") != "unknown"):
            m = today_message()
            if m and db.get("notified") != dt.date.today().isoformat() and (db.get("readiness") or {}).get("level") != "unknown":
                notify(m)
                db.put("notified", dt.date.today().isoformat())
    except garmin.GaveUp as e:
        ok, msg = False, f"Garmin kept refusing requests ({e}). Progress is saved; it will resume on the next run."
        log.error("=== %s stopped: %s ===", kind, msg)
    except Exception as e:
        ok, msg = False, f"{type(e).__name__}: {scrub(str(e))[:200]}"
        log.error("=== %s failed ===\n%s", kind, traceback.format_exc())
    garmin.save_tokens()
    db.run("UPDATE jobs SET finished=?, ok=?, message=? WHERE id=?", (dt.datetime.now().isoformat(timespec="seconds"), int(ok), msg, jid))
    if ok:
        log.info("=== %s finished: %s ===", kind, msg or "done")
    status.update({"running": None, "progress": "", "error": None if ok else msg})
    _lock.release()
    return ok


def start(kind):
    if status["running"]:
        return False
    threading.Thread(target=run, args=(kind,), daemon=True).start()
    return True


def last_ok(kinds=("setup", "daily")):
    q = ",".join("?" * len(kinds))
    r = db.rows(f"SELECT finished FROM jobs WHERE ok=1 AND kind IN ({q}) ORDER BY id DESC LIMIT 1", kinds)  # nosec B608
    return dt.datetime.fromisoformat(r[0]["finished"]) if r else None


CHECK_HOURS_UTC = (2, 6, 10, 14, 18, 22)
JITTER_S = 1800      # every scheduled contact with Garmin moves up to 30 minutes either way


def jitter(tag):
    """A fixed random offset, from -30 to +30 minutes, for one scheduled run.

    Each install has its own random seed, so installs do not all reach Garmin at the same moment, and each run (a date and a slot)
    gets its own offset, so one install does not always call at the same minute either. The offset for a run never changes, so the
    scheduler, which wakes every five minutes, agrees with itself about when the run is due.
    """
    seed = db.get("jitter_seed")
    if not seed:
        seed = secrets.token_hex(16)
        db.put("jitter_seed", seed)
    h = hashlib.sha256(f"{seed}:{tag}".encode()).digest()
    return dt.timedelta(seconds=int.from_bytes(h[:4], "big") % (2 * JITTER_S + 1) - JITTER_S)


def _local(t):
    return t.astimezone().replace(tzinfo=None)


def _check_due(now):
    """True when a Garmin calendar check (every four hours, UTC, each moved by its own jitter) has passed since the last
    successful job of any kind."""
    utc = now.astimezone(dt.UTC)
    slots = [(utc.replace(hour=h, minute=0, second=0, microsecond=0) + dt.timedelta(days=d)) for d in (-1, 0, 1) for h in CHECK_HOURS_UTC]
    due = [t + jitter("check " + t.isoformat()) for t in slots]
    passed = [t for t in due if t <= utc]
    if not passed:
        return False
    lo = last_ok(("setup", "daily", "replan", "readiness", "push"))
    return lo is None or lo < _local(max(passed))


def daily_due(now):
    """When today's daily update is due: the chosen time, moved by today's jitter."""
    hh, mm = (int(x) for x in db.get("run_time").split(":"))
    return now.replace(hour=hh, minute=mm, second=0, microsecond=0) + jitter("daily " + now.date().isoformat())


def scheduler():
    """Runs for the life of the app. Once a day at the chosen time it downloads, reviews and sends; it catches up after downtime,
    and re-checks the morning's sleep and HRV until the watch has synced. Every four hours (02:00, 06:00, 10:00 ... UTC) it checks
    that the Garmin calendar holds the planned workouts for the next `push_days` days and sends any that are missing or changed."""
    last_try = None
    while True:
        try:
            if db.get("setup_done") and db.get("auto_backup") and dt.datetime.now().hour >= 2:
                backup.nightly()          # once a day, whether or not Garmin could be reached
            if db.get("setup_done") and garmin.has_tokens() and not status["running"]:
                now = dt.datetime.now()
                due = daily_due(now)
                lo = last_ok()
                recently_tried = last_try and (now - last_try).total_seconds() < 1800
                if not recently_tried and ((now >= due and (lo is None or lo < due)) or (lo is None or (now - lo).total_seconds() > 26 * 3600)):
                    last_try = now
                    run("daily")
                elif not recently_tried and (db.get("readiness") or {}).get("level") == "unknown" and now.hour < 13 and \
                        (db.get("readiness") or {}).get("date") == now.date().isoformat():
                    last_try = now
                    run("readiness")
                elif not recently_tried and db.get("push_enabled") and _check_due(now):
                    last_try = now
                    run("push")
        except Exception:
            log.error("scheduler error\n%s", traceback.format_exc())
        time.sleep(300)
