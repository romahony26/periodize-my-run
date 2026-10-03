"""Periodize My Run web app. Start with:  python web.py   then open http://localhost:8321

Runs on a Mac or a Raspberry Pi. One athlete per install. The scheduler
thread keeps the plan and the watch up to date every day.
"""
import argparse
import datetime as dt
import hashlib
import hmac
import io
import ipaddress
import json
import os
import re
import secrets
import socket
import sqlite3
import sys
import threading
import time

import requests

from flask import Flask, jsonify, request, send_file, send_from_directory, session

import assess
import backup
import calibrate
import db
import engine
import execution
import course
import functools
import mimetypes
import agegrade
import insights
import forecast
import garmin
import calfile
import heat
import coros
import watch
import aerobic
import jobs
import profile
import push
import results
import vault
import equiv
import trends
import updates
from flask.sessions import SecureCookieSessionInterface

from log import log, scrub, setup

HERE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=os.path.join(HERE, "static"))
mimetypes.add_type("application/manifest+json", ".webmanifest")
app.config["MAX_CONTENT_LENGTH"] = 512 * 1024   # no request to this app needs to be larger


class Cookies(SecureCookieSessionInterface):
    """The login cookie is marked Secure whenever the browser reached the app over HTTPS, including through a proxy that terminates TLS."""

    def get_cookie_secure(self, app):
        return bool(app.config.get("SESSION_COOKIE_SECURE")) or request.is_secure or request.headers.get("X-Forwarded-Proto", "").lower() == "https"


app.session_interface = Cookies()
app.config.update(SESSION_COOKIE_SAMESITE="Strict", SESSION_COOKIE_HTTPONLY=True)
SETTINGS = ["units", "long_day", "run_days", "strength", "run_time", "push_enabled", "push_days", "easy_target", "daily_adjust",
            "hrmax", "peak_miles_override", "weekly_increase", "detail_weeks", "blocked_days", "notify_url", "weeks_ahead",
            "aero_test", "aero_test_weeks", "aero_runs", "aero_format", "forecast_completion", "week_start"]


def _is_num(v, lo, hi):
    return isinstance(v, int | float) and not isinstance(v, bool) and v == v and lo <= v <= hi


def _is_int(v, lo, hi):
    return isinstance(v, int) and not isinstance(v, bool) and lo <= v <= hi


# What each setting may hold. A value that fails its check is refused, so nothing malformed can be stored and break the planner later.
VALID = {
    "units": lambda v: v in ("mi", "km"), "long_day": lambda v: _is_int(v, 0, 6), "run_days": lambda v: _is_int(v, 3, 6), "week_start": lambda v: _is_int(v, 0, 6),
    "strength": lambda v: isinstance(v, bool), "push_enabled": lambda v: isinstance(v, bool), "daily_adjust": lambda v: isinstance(v, bool),
    "aero_test": lambda v: isinstance(v, bool), "aero_runs": lambda v: isinstance(v, bool),
    "run_time": lambda v: isinstance(v, str) and bool(re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", v)), "push_days": lambda v: v in (7, 14, 21) and not isinstance(v, bool),
    "easy_target": lambda v: v in ("none", "pace"), "aero_format": lambda v: v in ("short", "original"), "aero_test_weeks": lambda v: _is_int(v, 4, 8),
    "hrmax": lambda v: v is None or _is_num(v, 120, 230), "peak_miles_override": lambda v: v is None or _is_num(v, 10, 150),
    "weekly_increase": lambda v: _is_num(v, 0, 0.2), "detail_weeks": lambda v: _is_int(v, 4, 104), "weeks_ahead": lambda v: _is_int(v, 1, 5),
    "forecast_completion": lambda v: v is None or _is_num(v, 0.5, 1),
    "blocked_days": lambda v: isinstance(v, list) and len(v) <= 6 and len(set(map(str, v))) == len(v) and all(_is_int(x, 0, 6) for x in v),
    "notify_url": lambda v: v is None or (isinstance(v, str) and len(v) <= 500),
}
PBKDF2_ROUNDS = 600_000        # OWASP's current figure for PBKDF2-HMAC-SHA256


def _hash(pw, salt, rounds=PBKDF2_ROUNDS):
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), rounds).hex()


PROXY_HEADERS = ("X-Forwarded-For", "X-Forwarded-Host", "X-Forwarded-Proto", "Forwarded", "X-Real-Ip", "Via", "Tailscale-User-Login", "Cf-Connecting-Ip")


def _local():
    """Is the request from this computer itself? Only then is the app password not needed.

    A request relayed by a proxy on this computer (Tailscale Serve, nginx, Caddy) also arrives from 127.0.0.1, but it is someone
    else's. Proxies mark what they relay, so a marked request is never treated as local. For a proxy that adds no mark, start the
    app with --always-login.
    """
    if db.get("always_login") or any(h in request.headers for h in PROXY_HEADERS):
        return False
    return request.remote_addr in ("127.0.0.1", "::1")


def _allowed_hosts():
    names = {"localhost", socket.gethostname().lower(), socket.gethostname().lower() + ".local"}
    return names | {h.lower() for h in (db.get("allowed_hosts") or [])}


def _host_ok(host):
    host = host.rsplit(":", 1)[0].strip("[]").lower() if host.count(":") <= 1 else host.strip("[]").split("]")[0].lower()
    try:
        ipaddress.ip_address(host)      # a literal address cannot be a rebinding attack
        return True
    except ValueError:
        return host in _allowed_hosts()


SESSION_LIFETIME = dt.timedelta(days=90)
MAX_SESSIONS = 50


def _sid_key(sid):
    return hashlib.sha256(str(sid).encode()).hexdigest()


def _session_valid(sid):
    """A login is good only while the server still lists it: logging out, or a new app password, ends it everywhere for good."""
    return bool(sid) and (db.get("sessions") or {}).get(_sid_key(sid), 0) > time.time()


def _session_start():
    now = time.time()
    live = {k: v for k, v in (db.get("sessions") or {}).items() if v > now}
    live = dict(sorted(live.items(), key=lambda kv: kv[1])[-(MAX_SESSIONS - 1):])     # the oldest logins drop off first
    sid = secrets.token_urlsafe(24)
    live[_sid_key(sid)] = now + SESSION_LIFETIME.total_seconds()
    db.put("sessions", live)
    return sid


def _session_end(sid):
    live = db.get("sessions") or {}
    if live.pop(_sid_key(sid), None) is not None:
        db.put("sessions", live)


FAILS = {}            # address -> [failed attempts, locked until]
MAX_FAILS, LOCK_S = 5, 900


@app.before_request
def guard():
    if not _host_ok(request.host):          # every path, pages included: an unknown host name is a rebinding attempt
        return jsonify(error="This address is not allowed. Add it with: python web.py --allow-host NAME"), 400
    if not request.path.startswith("/api/"):
        return None
    if request.method in ("POST", "PUT", "PATCH"):
        try:
            body = request.get_json(silent=True)
        except RecursionError:
            body = None
        if not isinstance(body, dict):
            return jsonify(error="The request must be a JSON object."), 400
    origin = request.headers.get("Origin")
    if origin and origin.split("://", 1)[-1] != request.host:
        return jsonify(error="cross-site request refused"), 403
    if request.method != "GET" and request.headers.get("X-Requested-With") != "periodize":
        return jsonify(error="bad request"), 400       # every write, local or not, must come from the app's own page
    if request.path == "/api/auth" or _local():
        return None
    if not db.get("app_password"):
        return jsonify(auth="no_password"), 401
    if not session.get("ok") or not _session_valid(session.get("id")):
        return jsonify(auth="login"), 401
    return None


@app.after_request
def headers(resp):
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=(), payment=()"
    resp.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    resp.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    if request.is_secure:
        resp.headers["Strict-Transport-Security"] = "max-age=31536000"
    tiles = " https://tile.openstreetmap.org" if db.get("map_tiles") else ""     # map tiles only if the athlete switched real maps on
    resp.headers["Content-Security-Policy"] = "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:" + tiles + "; connect-src 'self'; manifest-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    if request.path.startswith("/api/"):
        resp.headers["Cache-Control"] = "no-store"
    return resp


@app.post("/api/auth")
def auth():
    ip, now = request.remote_addr, time.time()
    n, until = FAILS.get(ip, (0, 0))
    if now < until:
        return jsonify(error=f"Too many attempts. Try again in {int((until - now) // 60) + 1} minutes."), 429
    stored = db.get("app_password")
    if not stored:
        return jsonify(error="No app password is set. On the device, run: python web.py --set-password"), 400
    pw = (request.json or {}).get("password")
    pw = pw if isinstance(pw, str) else ""
    if len(pw) > 256:           # hashing a huge string is wasted work an attacker can ask for repeatedly
        pw = ""
    if len(FAILS) > 5000:
        FAILS.clear()           # bounded memory; the lock on any one address is at most 15 minutes anyway
    rounds = stored.get("rounds", 200_000)
    if not hmac.compare_digest(_hash(pw, stored["salt"], rounds), stored["hash"]):
        n += 1
        FAILS[ip] = (0, now + LOCK_S) if n >= MAX_FAILS else (n, 0)
        log.warning("Failed app login from %s (%d)", ip, n)
        return jsonify(error="Wrong password."), 403
    FAILS.pop(ip, None)
    if rounds < PBKDF2_ROUNDS:      # stored with an older, weaker setting: re-hash now that the password is known to be right
        salt = secrets.token_hex(16)
        db.put("app_password", {"salt": salt, "hash": _hash(pw, salt), "rounds": PBKDF2_ROUNDS})
    session.clear()            # a fresh session on login, so a cookie planted beforehand is worthless
    session["ok"] = True
    session["id"] = _session_start()
    session.permanent = True
    log.info("App login from %s", ip)
    return jsonify(ok=True)


@app.delete("/api/auth")
def logout():
    _session_end(session.get("id"))
    session.clear()
    log.info("App logout from %s", request.remote_addr)
    return jsonify(ok=True)


@app.errorhandler(404)
def not_found(e):
    return jsonify(error="Not found."), 404


@app.errorhandler(405)
def bad_method(e):
    return jsonify(error="Not allowed."), 405


@app.errorhandler(413)
def too_big(e):
    return jsonify(error="That request is too large."), 413


@app.errorhandler(Exception)
def crashed(e):
    """Never show a stack trace or internal detail to the browser; the detail goes to the log."""
    from werkzeug.exceptions import HTTPException
    if isinstance(e, HTTPException):
        return jsonify(error=e.name), e.code
    if isinstance(e, ValueError | TypeError | KeyError | OverflowError | AttributeError | IndexError | sqlite3.InterfaceError | sqlite3.ProgrammingError | sqlite3.IntegrityError) \
            and (request.method != "GET" or request.view_args or request.args):
        log.warning("Rejected input on %s %s: %s", request.method, request.path, type(e).__name__)      # input the handler did not expect: refuse it, do not crash
        return jsonify(error="That input could not be understood."), 400
    log.error("Unhandled error on %s: %s", request.path, type(e).__name__)
    return jsonify(error="Something went wrong. The detail is in the log."), 500


def _lock_file(f):
    """Hold an exclusive lock on an open file for the life of the process, on macOS, Linux or Windows."""
    if os.name == "nt":
        import msvcrt
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)


def set_password():
    import getpass
    a = getpass.getpass("Choose an app password (8+ characters): ")
    if len(a) < 8 or a != getpass.getpass("Again: "):
        raise SystemExit("Passwords did not match or were too short. Nothing changed.")
    salt = secrets.token_hex(16)
    db.put("app_password", {"salt": salt, "hash": _hash(a, salt), "rounds": PBKDF2_ROUNDS})
    db.put("sessions", {})          # a new password signs every device out
    print("App password set. Every device must log in again.")


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


_FRESH, _PERF = {}, {"key": None, "data": {}}


def _fresh(d, c):
    """Freshness and the night's numbers for one day, remembered until that day's data changes."""
    row = db.rows("SELECT rhr,sleep_h,hrv,sleep_score FROM daily WHERE date>=? AND date<=? ORDER BY date", ((d - dt.timedelta(days=67)).isoformat(), d.isoformat()))
    key = (d.isoformat(), json.dumps(row))
    if _FRESH.get(d.isoformat(), (None,))[0] != key:
        r = engine.readiness(d, c)
        _FRESH[d.isoformat()] = (key, None if r["level"] == "unknown" else {"fresh": r["fresh"], "sleep_score": r["sleep_score"], "sleep_h": r["sleep_h"], "hrv": r["hrv"], "rhr": r["rhr"],
                                                                        "normal": r["normal"], "week": r["week"], "reasons": r["reasons"]})
    return _FRESH[d.isoformat()][1]


def _performance(starts, today, L, c):
    """For each calendar week shown: pace per heartbeat across the whole week's runs against the four weeks before it, as a percentage.

    A week, not a run: one run's pace for its heart rate swings with wind, heat, route and time of day.
    """
    n = db.rows("SELECT COUNT(*) n, MAX(date) m FROM activities WHERE detail IS NOT NULL")[0]
    key = (tuple(s.isoformat() for s in starts), today.isoformat(), n["n"], n["m"])
    if _PERF["key"] == key:
        return _PERF["data"]
    bands = [(h - 5, h + 5) for h in engine.hr_levels(L["hrmax"])["stages"][:4]]
    runs = [r for r in assess.load_runs(min(starts) - dt.timedelta(days=28), today + dt.timedelta(days=1)) if r.get("hr_sec") and assess.usable(r, c)]

    def speeds(rs):
        out = []
        for lo, hi in bands:
            t = [assess.hr_band(r, lo, hi) for r in rs]
            s, m = (sum(x) for x in zip(*t, strict=True)) if t else (0, 0)
            out.append((m / s, s) if s >= 900 else None)
        return out

    data = {}
    for ws in starts:
        if ws > today:
            continue
        wk = speeds([r for r in runs if ws <= r["date"] < ws + dt.timedelta(days=7)])
        ref = speeds([r for r in runs if ws - dt.timedelta(days=28) <= r["date"] < ws])
        num = den = 0.0
        for a, b in zip(wk, ref, strict=True):
            if a and b:
                num += (a[0] / b[0] - 1) * a[1]
                den += a[1]
        if den >= 1800:
            data[ws.isoformat()] = round(100 * num / den, 1)
    _PERF.update({"key": key, "data": data})
    return data


def _sync_status(p, day, tp, adj, c, d, today):
    """Where this day stands with Garmin: on the watch and current, waiting to be sent, or not sent and why."""
    if not day["steps"]:
        return {"state": "none", "text": "Rest day: nothing to send."}
    if d < today:
        return {"state": "past", "text": "Was on your Garmin calendar." if p["garmin_id"] else "Was not sent to Garmin."}
    if not c["push_enabled"]:
        return {"state": "off", "text": "Sending to Garmin is switched off in Settings."}
    if not watch.can_push():
        return {"state": "off", "text": "Garmin is not connected." if watch.name() == "garmin" else
                f"Your runs come from {watch.NAMES[watch.name()]}, which cannot receive workouts; follow the plan from this page."}
    if (d - today).days >= int(c["push_days"]):
        first = d - dt.timedelta(days=int(c["push_days"]) - 1)
        return {"state": "later", "text": f"Not sent yet. The next {c['push_days']} days are kept on your watch; this one goes on {first.day} {first.strftime('%b')}."}
    wk = push.workout(day, tp, c, (adj or {}).get("slow", 0.0)) if tp else None
    h = hashlib.sha256(json.dumps(wk, sort_keys=True).encode()).hexdigest() if wk else None
    if p["garmin_id"] and h == p["pushed_hash"]:
        return {"state": "synced", "text": "On your Garmin calendar and up to date" + (", with today's eased paces." if (adj or {}).get("slow") else ".") + " It reaches the watch at its next sync."}
    if p["garmin_id"]:
        return {"state": "pending", "text": "On your Garmin calendar, but it has changed since. The change goes at the next sync with Garmin."}
    return {"state": "pending", "text": "Not on your Garmin calendar yet. It goes at the next sync with Garmin."}


def _days(c, today, L=None):
    ws = int(c.get("week_start", 0)) % 7
    back = (today.weekday() - ws) % 7
    start, end = today - dt.timedelta(days=back + 7), today + dt.timedelta(days=7 * (int(c["weeks_ahead"]) + 1) - 1 - back)
    starts = [start + dt.timedelta(days=7 * i) for i in range(int(c["weeks_ahead"]) + 2)]
    perf = _performance(starts, today, L, c) if L else {}
    tps = {r["monday"]: r["tp"] for r in db.rows("SELECT monday,tp FROM weeks")}
    plan = {r["date"]: r for r in db.rows("SELECT * FROM plan WHERE date>=? AND date<=?", (start.isoformat(), end.isoformat()))}
    done = {}
    for r in db.rows("SELECT id,date,dist_m,timer_s,avg_hr,name FROM activities WHERE sport='running' AND date>=? AND date<=? ORDER BY dist_m DESC", (start.isoformat(), end.isoformat())):
        a = done.setdefault(r["date"], {"m": 0.0, "s": 0.0, "n": 0, "id": r["id"]})     # the link goes to the day's longest run
        a["m"] += r["dist_m"] or 0
        a["s"] += r["timer_s"] or 0
        a["n"] += 1
    out, d = [], start
    while d <= end:
        k = d.isoformat()
        p, a = plan.get(k), done.get(k)
        item = {"date": k, "dow": engine.DAYS[d.weekday()], "past": d < today, "today": d == today}
        if p:
            tp = tps.get((d - dt.timedelta(days=d.weekday())).isoformat())
            adj = json.loads(p["adjust"]) if p["adjust"] else None
            planned = dict(p, steps=json.loads(p["steps"]) if p["steps"] else None)
            day = engine.as_run(planned, adj)
            item.update({"type": day["type"], "label": day["label"], "dist": engine.dist(p["miles"], c["units"]) if p["miles"] else "", "miles": p["miles"] or 0,
                         "short": engine.short(day, c["units"]), "week": (d - dt.timedelta(days=d.weekday())).isoformat(),
                         "text": engine.describe(day, tp, c["units"], (adj or {}).get("slow", 0.0)) if tp and day["steps"] else "",
                         "note": p["note"], "strength": p["strength"], "source": p["source"], "adjust": adj, "on_watch": bool(p["pushed_hash"]),
                         "original": engine.describe(planned, tp, c["units"], 0.0) if tp and day["steps"] and adj and (adj.get("slow") or adj.get("easy")) else "",
                         "sync": _sync_status(p, day, tp, adj, c, d, today)})
            if tp and day["steps"] and not item["past"] and L:
                mins = sum(execution.planned_zones(day["steps"], tp, L["hrmax"])[0]) / 60
                race = p["type"] == "Race"
                fu = insights.fuel(mins, c["race_carbs_g_per_h"] if race else insights.note_carbs(p["note"]), int(c["gel_carbs_g"]), race)
                if fu:
                    item["fuel"] = fu
        if a:
            v = a["m"] / a["s"] if a["s"] else None
            item["done"] = {"dist": engine.dist(round(a["m"] / assess.MI, 1), "mi") if c["units"] == "mi" else f"{a['m'] / 1000:.1f} km",
                            "pace": engine.pace(v, c["units"]) + "/" + c["units"] if v else "", "runs": a["n"], "id": a["id"]}
        if d <= today:
            f = _fresh(d, c)
            if f:
                item["body"] = f
            if k in perf:
                item["week_perf"] = perf[k]      # carried on the first day of each displayed week
        out.append(item)
        d += dt.timedelta(days=1)
    return out


@app.get("/api/state")
def state():
    c, today = db.cfg(), dt.date.today()
    prof = db.get("profile")
    rs = db.rows("SELECT * FROM races ORDER BY date")
    goal = next((r for r in rs if r["priority"] == "A" and r["date"] >= today.isoformat()), None)
    L = profile.limits(prof, c, goal["miles"] if goal else None) if prof else None
    mon = today - dt.timedelta(days=today.weekday())
    wk = db.rows("SELECT * FROM weeks WHERE monday=?", (mon.isoformat(),))
    fitness = None
    if wk:
        w, s = wk[0], json.loads(wk[0]["summary"])
        tp = w["tp"]
        fitness = {"threshold": engine.pace(tp, c["units"]) + "/" + c["units"], "zones": {engine.ZONE_NAME[z]: engine.zone_pace(tp, z, c["units"]) for z in assess.ZONES},
                   "evidence": s["tp_why"], "change": (tp / s["tp_prev"] - 1) * 100, "endurance": s["endurance"], "endurance_parts": s["endurance_parts"],
                   "week": {"mode": s["mode"], "total": engine.dist(s["total"], c["units"]), "why": s["why"], "flags": s["flags"], "weeks_to_race": s["weeks_to_race"]},
                   "history": [{"start": x["start"], "dist": engine.dist(round(x["mi"], 1), "mi") if c["units"] == "mi" else f"{x['mi'] * 1.609:.0f} km",
                                "runs": x["runs"], "long": round(x["long"] if c["units"] == "mi" else x["long"] * 1.609, 1), "t_min": round(x["t_min"])} for x in s["weeks"]]}
        if goal:
            st = {"tp": tp, "endurance": s["endurance"]}
            now_s, full_s = assess.projection(st, c, goal["miles"])
            fitness["goal"] = {"name": goal["name"], "date": goal["date"], "days": (dt.date.fromisoformat(goal["date"]) - today).days,
                               "now": engine.hms(now_s), "full": engine.hms(full_s), "target": goal["goal_time"]}
            fc = forecast.forecast(tp, s["endurance"], c, goal, today)
            cp = fc["completion"]
            log_ = db.get("forecast_log") or {}
            prev = [v for k, v in sorted(log_.items()) if k < mon.isoformat()]
            if log_.get(mon.isoformat()) is None or abs(log_[mon.isoformat()] - fc["seconds"]) > 1:
                log_[mon.isoformat()] = round(fc["seconds"])
                db.put("forecast_log", dict(sorted(log_.items())[-30:]))
            gs = None
            if goal["goal_time"]:
                try:
                    parts = [int(x) for x in goal["goal_time"].split(":")]
                    gs = sum(x * 60 ** i for i, x in enumerate(reversed(parts)))
                except ValueError:
                    gs = None
            fitness["goal"]["forecast"] = {
                "time": engine.hms(fc["seconds"]), "all": engine.hms(fc["all"]), "poor": engine.hms(fc["poor"]), "poor_pct": round(fc["poor_share"] * 100),
                "pct": round(cp["value"] * 100), "chosen": cp["chosen"], "history_pct": round(cp["history"] * 100) if cp["history"] is not None else None, "history_weeks": cp["history_weeks"],
                "plan_pct": round(cp["plan"] * 100) if cp["plan"] is not None else None, "plan_days": cp["plan_days"], "plan_weight": round(cp["plan_weight"] * 100),
                "gap": (("behind", engine.hms(fc["seconds"] - gs)) if fc["seconds"] > gs + 1 else ("ahead", engine.hms(gs - fc["seconds"]))) if gs else None,
                "needs_all": bool(gs and fc["all"] <= gs < fc["seconds"]), "out_of_reach": bool(gs and fc["all"] > gs),
                "change": round(fc["seconds"] - prev[-1]) if prev else None,
                "index_now": round(fc["current_index"], 1), "index_race": round(fc["index"], 1), "proven": round(fc["proven"]["index"], 1),
                "proven_from": fc["proven"]["from"], "proven_date": fc["proven"]["date"]}
            if c.get("heat_adjust"):
                rh = heat.at(dt.date.fromisoformat(goal["date"]), 9, cached_only=True)    # race starts are usually around 9
                if rh:
                    fitness["goal"]["heat"] = rh
    # plan against actual, by week, for weeks the app has planned
    comp = []
    for k in range(4, -1, -1):
        a, b = (mon - dt.timedelta(weeks=k)).isoformat(), (mon - dt.timedelta(weeks=k - 1)).isoformat()
        p = db.rows("SELECT SUM(miles) m, SUM(type IN ('Key','Long','Race')) k FROM plan WHERE date>=? AND date<? AND date<?", (a, b, today.isoformat()))[0]
        first = db.rows("SELECT MIN(date) d FROM plan WHERE date>=? AND date<?", (a, b))[0]["d"] or a   # count runs only on days that had a plan
        d = db.rows("SELECT SUM(dist_m) m, COUNT(*) n FROM activities WHERE sport='running' AND date>=? AND date<? AND date<?", (first, b, today.isoformat()))[0]
        if p["m"]:
            comp.append({"week": a, "planned": engine.dist(round(p["m"], 1), c["units"]), "done": engine.dist(round((d["m"] or 0) / assess.MI, 1), c["units"]),
                         "pct": round(100 * (d["m"] or 0) / assess.MI / p["m"]), "runs": d["n"]})
    w = db.rows("SELECT date,weight_kg FROM daily WHERE weight_kg IS NOT NULL AND date>=? ORDER BY date", ((today - dt.timedelta(days=35)).isoformat(),))
    recent = [x["weight_kg"] for x in w if x["date"] >= (today - dt.timedelta(days=7)).isoformat()]
    older = [x["weight_kg"] for x in w if x["date"] < (today - dt.timedelta(days=21)).isoformat()]
    weight = {"now": round(sum(recent) / len(recent), 1), "change": round(sum(recent) / len(recent) - sum(older) / len(older), 1) if older else None} if recent else None
    preds, vo2 = None, None
    if wk:
        tp, s0 = wk[0]["tp"], json.loads(wk[0]["summary"])
        st0 = {"tp": tp, "endurance": s0["endurance"]}
        preds = []
        for name, dm in equiv.DISTANCES + [("50K", 50000.0)]:
            now_s, full_s = assess.projection(st0, c, dm / assess.MI)
            per = assess.MI if c["units"] == "mi" else 1000
            preds.append({"name": name, "now": engine.hms(now_s), "full": engine.hms(full_s), "gap": engine.hms(now_s - full_s) if now_s - full_s >= 5 else None, "pace": engine.pace(per / (now_s / (dm / per)), c["units"]) + "/" + c["units"]})
        g = db.rows("SELECT date, vo2max FROM activities WHERE vo2max IS NOT NULL AND sport='running' ORDER BY date DESC LIMIT 1")
        trend = db.rows("SELECT substr(date,1,4) y, ROUND(AVG(vo2max),1) v FROM activities WHERE vo2max IS NOT NULL AND sport='running' GROUP BY y ORDER BY y")
        vo2 = {"garmin": g[0]["vo2max"] if g else None, "garmin_date": g[0]["date"] if g else None, "by_year": trend}
    aero = None
    if L:
        hl = engine.hr_levels(L["hrmax"])
        nxt = db.rows("SELECT date FROM plan WHERE label='Aerobic test' AND date>=? ORDER BY date LIMIT 1", (today.isoformat(),))
        aero = {"monthly": aerobic.monthly(L, c, today), "tests": aerobic.tests(c["units"]), "relationship": aerobic.relationship(c["units"]),
                   "levels": hl, "lthr": db.get("aero_lthr") or hl["start_lthr"], "next_test": nxt[0]["date"] if nxt else None,
                   "format": c["aero_format"], "peak": db.get("aero_peak_hr"),
                   "test_stages": hl["stages"] if c["aero_format"] == "original" else hl["stages"][:4]}
    res = results.listing(c["units"], everything=True)
    for r in res:
        r["age_grade"] = agegrade.grade(c.get("sex"), c.get("birth_date"), r["date"], r["dist_m"], r["flat_s"]) if r["counts"] else None
    graded = [r for r in res if r["age_grade"]]
    best_grade = max(graded, key=lambda r: r["age_grade"], default=None)
    form, season, lt, climb = None, [], None, None
    if wk and goal:
        s1 = json.loads(wk[0]["summary"])
        longm = max((d["miles"] or 0) for d in db.rows("SELECT miles FROM plan WHERE date>=? AND date<?", (mon.isoformat(), (mon + dt.timedelta(days=7)).isoformat())) or [{"miles": 0}])
        climb = course.climb_target(goal, s1.get("weeks_to_race"), s1["total"], longm, today)
    if wk and L:
        form = insights.form(today, wk[0]["tp"], L["hrmax"])
        for r in db.rows("SELECT monday,mode,summary FROM weeks WHERE monday>=? ORDER BY monday", (mon.isoformat(),)):
            sm = json.loads(r["summary"])
            season.append({"monday": r["monday"], "mode": r["mode"], "total": sm["total"], "long": max((d["miles"] or 0) for d in db.rows("SELECT miles FROM plan WHERE date>=? AND date<?", (r["monday"], (dt.date.fromisoformat(r["monday"]) + dt.timedelta(days=7)).isoformat())) or [{"miles": 0}])})
        last = season[-1]["monday"] if season else ""
        season += [x for x in (db.get("season") or []) if x["monday"] > last]
        k = 1 if c["units"] == "mi" else assess.MI / 1000
        season = [dict(x, total=round(x["total"] * k), long=round(x["long"] * k)) for x in season]
        for x in season:           # races in each week, so the outline can show them
            end = (dt.date.fromisoformat(x["monday"]) + dt.timedelta(days=7)).isoformat()
            x["races"] = [{"name": r["name"], "date": r["date"], "priority": r["priority"]}
                          for r in db.rows("SELECT name,date,priority FROM races WHERE date>=? AND date<? ORDER BY date", (x["monday"], end))]
        g = db.get("garmin_lt")
        if g:
            age = (today - dt.date.fromisoformat(g["date"])).days if g.get("date") else None
            lt = {"pace": engine.pace(g["speed"], c["units"]) + "/" + c["units"], "hr": g.get("hr"), "date": g.get("date"), "used": age is not None and age <= 42,
                  "diff": round(100 * (g["speed"] / wk[0]["tp"] - 1), 1), "app_hr": round(c["threshold_hr_fraction"] * L["hrmax"])}
    sp = assess.steps_summary(today, c)
    steps = {"week": round(sp["week"]), "normal": round(sp["base"]), "yesterday": sp["yesterday"],
             "miles_week": round(sp["week"] * 7 * 0.75 / assess.MI, 1)} if sp else None
    lo = jobs.last_ok()
    return jsonify(
        version=changelog()[0]["version"], project=PROJECT, terms_ok=terms_accepted(), climb=climb, map_tiles=bool(c.get("map_tiles")), reshuffled=db.get("reshuffled") or {}, form=form, season=season, watch_threshold=lt, warnings=insights.warnings(today, c["units"], c.get("sex"), L["hrmax"] if L else None) if db.get("setup_done") else [],
        timing=insights.timing(today, L["hrmax"] if L else None, c["sleep_7night_min_h"]) if db.get("setup_done") else None, shoes=insights.shoes(c["units"]),
        drift=insights.drift_history(today) if db.get("setup_done") else [], best_grade=best_grade, about_you={"sex": c.get("sex"), "birth_date": c.get("birth_date"), "gel_carbs_g": c.get("gel_carbs_g")},
        notify_set=bool(vault.get("notify_url")),
        bests=results.bests(today), aerobic=aero, steps=steps, predictions=preds, vo2=vo2, results=[{k: v for k, v in r.items() if k != "index"} for r in res[:150]],
        compliance=comp, weight=weight, can_undo=bool(db.rows("SELECT 1 FROM moves LIMIT 1")), has_password=bool(db.get("app_password")),
        update=updates.state() if c.get("update_check", True) else None, update_check=bool(c.get("update_check", True)),
        heat={"on": bool(c.get("heat_adjust")), "located": bool((db.get("heat_forecast") or {}).get("loc")),
              "today": heat.at(today, heat.run_hour(today), cached_only=True) if c.get("heat_adjust") else None},
        setup_done=bool(db.get("setup_done")), setup_seen=bool(db.get("setup_seen")), setup_started=bool(db.rows("SELECT 1 FROM jobs WHERE kind='setup' LIMIT 1")), watch={"source": watch.name(), "name": watch.NAMES[watch.name()], "connected": watch.connected(), "can_push": watch.can_push(),
               "recovery": watch.has_recovery_data(), "fit_folder": db.get("fit_folder") or "", "coros": coros.connected(), "local": _local()}, garmin={"connected": garmin.has_tokens(), "name": db.get("garmin_name")},
        job=jobs.status, last_run=lo.isoformat(timespec="minutes") if lo else None, stale=bool(lo and (dt.datetime.now() - lo).days >= 7),
        settings={k: (vault.get("notify_url") or "") if k == "notify_url" else c.get(k) for k in SETTINGS}, limits=L, profile=prof, races=[{k: v for k, v in r.items() if k != "course"} | {"has_course": bool(r.get("course"))} for r in rs], statuses=db.rows("SELECT * FROM status ORDER BY start DESC"),
holiday_modes=engine.HOLIDAY_MODES, fitness=fitness,
        backups=backup.listing()[:20], auto_backup=c["auto_backup"],
        week_info={r["monday"]: {"mode": r["mode"], "total": engine.dist(json.loads(r["summary"])["total"], c["units"]), "final": bool(r["final"])}
                   for r in db.rows("SELECT monday,mode,final,summary FROM weeks WHERE monday>=?", ((mon - dt.timedelta(days=7)).isoformat(),))}, readiness=db.get("readiness"), days=_days(c, today, L) if db.get("setup_done") else [], today=today.isoformat(),
        remote=not _local())


@app.post("/api/garmin/login")
def garmin_login():
    j = request.json or {}
    try:
        return jsonify(result=garmin.start_login(j.get("email", "").strip(), j.get("password", "")))
    except Exception as e:
        log.error("Garmin login failed: %s", type(e).__name__)
        return jsonify(error=f"Garmin login failed: {scrub(str(e))[:200]}"), 400


@app.post("/api/garmin/mfa")
def garmin_mfa():
    try:
        return jsonify(result=garmin.finish_mfa((request.json or {}).get("code", "").strip()))
    except Exception as e:
        log.error("Garmin two-step login failed: %s", type(e).__name__)
        return jsonify(error=f"Code not accepted: {scrub(str(e))[:200]}"), 400


@app.post("/api/settings")
def settings():
    j = request.json or {}
    for k in SETTINGS:
        if k in j and not VALID[k](j[k]):
            return jsonify(error=f"That value for {k.replace('_', ' ')} is not allowed."), 400
    for k in SETTINGS:
        if k in j and k == "notify_url":       # the address can contain a private topic, so it is kept encrypted
            url = (j[k] or "").strip()
            if url and not jobs.safe_url(url):
                return jsonify(error="That notification address is not allowed. Use an https address that is not this computer."), 400
            vault.put("notify_url", url or None)
        elif k in j:
            db.put(k, j[k])
    if "sex" in j:
        db.put("sex", j["sex"] if j["sex"] in ("M", "F") else None)
    if "birth_date" in j:
        try:
            b = dt.date.fromisoformat(j["birth_date"]) if j["birth_date"] else None
            if b and not dt.date(1900, 1, 1) <= b <= dt.date.today():
                raise ValueError
        except (ValueError, TypeError):
            return jsonify(error="That date of birth is not a valid date."), 400
        db.put("birth_date", b.isoformat() if b else None)
    if "gel_carbs_g" in j:
        try:
            db.put("gel_carbs_g", min(max(int(j["gel_carbs_g"]), 10), 60))
        except (ValueError, TypeError):
            return jsonify(error="Carbohydrate per gel must be a number of grams."), 400
    if "auto_backup" in j:
        db.put("auto_backup", bool(j["auto_backup"]))
    if "map_tiles" in j:
        db.put("map_tiles", bool(j["map_tiles"]))
    if "update_check" in j:
        db.put("update_check", bool(j["update_check"]))
    if "heat_adjust" in j:
        db.put("heat_adjust", bool(j["heat_adjust"]))
        log.info("Heat adjustment switched %s", "on" if j["heat_adjust"] else "off")
        if db.get("setup_done"):
            jobs.start("readiness")
    if set(j) <= {"auto_backup", "sex", "birth_date", "gel_carbs_g", "map_tiles", "heat_adjust", "update_check"}:
        return jsonify(ok=True)       # nothing here changes the plan
    sr = j.get("seed_race")
    if isinstance(sr, dict) and _is_num(sr.get("miles"), 0.5, 200) and _is_num(sr.get("time_s"), 120, 400_000):
        db.put("seed_threshold", float(sr["miles"]) * assess.MI / float(sr["time_s"]) / assess.race_factor(float(sr["miles"])))
    log.info("Settings changed: %s", ", ".join(k for k in SETTINGS if k in j))
    if db.get("setup_done"):
        jobs.start("replan")
    return jsonify(ok=True)


@app.post("/api/races")
def race_save():
    j = request.json or {}
    try:
        day = dt.date.fromisoformat(str(j["date"]))
        miles = float(j["miles"])
    except (KeyError, ValueError, TypeError):
        return jsonify(error="A race needs a date and a distance."), 400
    if not (dt.date(1990, 1, 1) <= day <= dt.date.today() + dt.timedelta(days=5 * 366)):
        return jsonify(error="The race date must be between 1990 and five years from now."), 400
    if not 0.5 <= miles <= 200:
        return jsonify(error="The distance must be between 0.5 and 200 miles."), 400
    name, prio, goal = j.get("name") or "Race", j.get("priority") or "A", j.get("goal_time") or None
    if not isinstance(name, str) or len(name) > 120:
        return jsonify(error="The race name must be text of up to 120 characters."), 400
    if prio not in ("A", "B"):
        return jsonify(error="The priority must be a goal race or a tune-up."), 400
    if goal is not None and not (isinstance(goal, str) and re.fullmatch(r"(\d{1,2}:)?[0-5]?\d:[0-5]\d", goal.strip())):
        return jsonify(error="The goal time must look like 3:00:00 or 39:30."), 400
    if j.get("id") is not None and not (isinstance(j["id"], int) and not isinstance(j["id"], bool)):
        return jsonify(error="bad race id"), 400
    args = (name.strip() or "Race", day.isoformat(), miles, prio, goal.strip() if goal else None)
    if j.get("id"):
        db.run("UPDATE races SET name=?,date=?,miles=?,priority=?,goal_time=? WHERE id=?", args + (j["id"],))
    else:
        db.run("INSERT INTO races(name,date,miles,priority,goal_time) VALUES(?,?,?,?,?)", args)
    log.info("Race saved: %s on %s", args[0], args[1])
    if db.get("setup_done"):
        jobs.start("replan")
    return jsonify(ok=True)


@app.post("/api/races/<int:rid>/course")
def race_course(rid):
    """Attach a course to a race: an elevation profile read from a GPX file in the browser, or just the total climb."""
    j = request.json or {}
    if not db.rows("SELECT 1 FROM races WHERE id=?", (rid,)):
        return jsonify(error="No such race."), 404
    try:
        if j.get("points"):
            prof = course.clean(j["points"])
            db.run("UPDATE races SET course=?, climb_m=? WHERE id=?", (json.dumps(prof), course.climb(prof), rid))
        elif "climb_m" in j:
            cm = float(j["climb_m"]) if j["climb_m"] not in (None, "") else None
            if cm is not None and not 0 <= cm <= 30000:
                raise ValueError("Climb must be between 0 and 30,000 metres.")
            db.run("UPDATE races SET climb_m=?, course=NULL WHERE id=?", (cm, rid))
        else:
            db.run("UPDATE races SET course=NULL, climb_m=NULL WHERE id=?", (rid,))
    except (ValueError, TypeError) as e:
        return jsonify(error=str(e) or "That course could not be read."), 400
    return jsonify(ok=True)


@app.get("/api/races/<int:rid>/pacing")
def race_pacing(rid):
    r = db.rows("SELECT * FROM races WHERE id=?", (rid,))
    if not r or not r[0]["course"]:
        return jsonify(error="Add the course (a GPX file) to this race first."), 404
    r, c = r[0], db.cfg()

    def secs(text):
        try:
            p = [int(x) for x in (text or "").split(":")]
            return sum(x * 60 ** i for i, x in enumerate(reversed(p))) if 1 < len(p) <= 3 else None
        except ValueError:
            return None

    target, source = secs(request.args.get("time")), "the time you entered"
    if not target:
        target, source = secs(r["goal_time"]), "your goal time"
    if not target:
        wk = db.rows("SELECT tp, summary FROM weeks ORDER BY monday DESC LIMIT 1")
        if not wk:
            return jsonify(error="Enter a target time."), 400
        target, source = assess.projection({"tp": wk[0]["tp"], "endurance": json.loads(wk[0]["summary"])["endurance"]}, c, r["miles"])[0], "what you could run today"
    if not 300 <= target <= 400_000:
        return jsonify(error="That target time is not possible."), 400
    out = course.pacing(json.loads(r["course"]), r["miles"], target, c["units"])
    out.update({"race": r["name"], "date": r["date"], "source": source, "ultra": r["miles"] > 27})
    return jsonify(out)


@app.delete("/api/races/<int:rid>")
def race_delete(rid):
    db.run("DELETE FROM races WHERE id=?", (rid,))
    if db.get("setup_done"):
        jobs.start("replan")
    return jsonify(ok=True)


@app.post("/api/results")
def result_save():
    j = request.json or {}
    try:
        dt.date.fromisoformat(j["date"])
        dist_m, time_s = float(j["miles"]) * assess.MI, float(j["time_s"])
        if not (400 <= dist_m <= 400_000 and 60 <= time_s <= 200_000):
            raise ValueError
    except (KeyError, ValueError, TypeError):
        return jsonify(error="A result needs a date, a distance and a time."), 400
    if j.get("id"):      # correcting a result: its name, time, and whether it counts toward fitness numbers
        db.run("UPDATE results SET date=?,name=?,dist_m=?,time_s=?,counts=?,note=COALESCE(?,note) WHERE id=?",
               (j["date"], (j.get("name") or "Race")[:80], dist_m, time_s, 0 if j.get("off_road") else 1, j.get("note"), int(j["id"])))
    else:
        db.run("INSERT INTO results(date,name,dist_m,time_s,source,counts,note) VALUES(?,?,?,?,'entered',?,?)",
               (j["date"], (j.get("name") or "Race")[:80], dist_m, time_s, 0 if j.get("off_road") else 1, (j.get("note") or "")[:400]))
    log.info("Race result added: %s", j["date"])
    return jsonify(ok=True)


@app.post("/api/results/import")
def result_import():
    try:
        out = results.import_csv((request.json or {}).get("csv") or "")
    except ValueError as e:
        return jsonify(error=str(e)), 400
    log.info("Race log imported: %s", out)
    if db.get("setup_done"):
        jobs.start("replan")
    return jsonify(out)


@app.delete("/api/results/<int:rid>")
def result_delete(rid):
    db.run("UPDATE results SET hidden=1 WHERE id=?", (rid,))   # hidden, not deleted, so a found result does not come back
    return jsonify(ok=True)


@app.post("/api/aerobic")
def aero_save():
    """Enter a Aerobic test by hand: a date and, for each stage, the heart rate and the time for 2400 m."""
    j = request.json or {}
    try:
        dt.date.fromisoformat(j["date"])
        metres = 2400.0 if db.get("aero_format") == "original" else assess.MI
        stages = [{"hr": int(s["hr"]), "s_per_mi": round(float(s["time_s"]) / metres * assess.MI)} for s in j["stages"] if s.get("time_s")]
        if len(stages) < 2 or any(not (90 <= s["hr"] <= 220 and 240 <= s["s_per_mi"] <= 1200) for s in stages):
            raise ValueError
    except (KeyError, ValueError, TypeError):
        return jsonify(error="Enter a date and at least two stages, each with its heart rate and 2400 m time."), 400
    db.run("INSERT OR REPLACE INTO aerobic_tests(date,stages,source) VALUES(?,?,'entered')", (j["date"], json.dumps(stages)))
    log.info("Aerobic test entered for %s", j["date"])
    return jsonify(ok=True)


@app.delete("/api/aerobic/<date>")
def aero_delete(date):
    db.run("DELETE FROM aerobic_tests WHERE date=?", (date,))
    return jsonify(ok=True)


@app.post("/api/status")
def status_save():
    j = request.json or {}
    if j.get("id"):
        db.run("UPDATE status SET end=? WHERE id=?", (j.get("end") or dt.date.today().isoformat(), j["id"]))
        log.info("Status %s ended", j["id"])
    else:
        if j.get("kind") not in ("sick", "injured", "holiday"):
            return jsonify(error="Choose sick, injured or holiday."), 400
        mode = j.get("mode") if j["kind"] == "holiday" else None
        if j["kind"] == "holiday" and mode not in engine.HOLIDAY_MODES:
            return jsonify(error="Choose how you want to run on holiday."), 400
        try:
            start = dt.date.fromisoformat(j.get("start") or dt.date.today().isoformat())
            end = dt.date.fromisoformat(j["end"]) if j.get("end") else None
        except ValueError:
            return jsonify(error="Check the dates."), 400
        if end and end < start:
            return jsonify(error="The end date is before the start date."), 400
        db.run("INSERT INTO status(kind,start,end,note,mode) VALUES(?,?,?,?,?)", (j["kind"], start.isoformat(), end.isoformat() if end else None, (j.get("note") or "")[:120], mode))
        log.info("Status recorded: %s from %s", j["kind"], j.get("start"))
    jobs.start("replan")
    return jsonify(ok=True)


@app.delete("/api/status/<int:sid>")
def status_delete(sid):
    db.run("DELETE FROM status WHERE id=?", (sid,))
    jobs.start("replan")
    return jsonify(ok=True)


def _hard_warning(today):
    hard = {r["date"] for r in db.rows("SELECT date FROM plan WHERE type IN ('Key','Long','Race') AND date>=?", (today,))}
    return next((f"Two hard days are now back to back ({d} and the day after). Consider an easy day between them."
                 for d in sorted(hard) if (dt.date.fromisoformat(d) + dt.timedelta(days=1)).isoformat() in hard), None)


@app.post("/api/plan/move")
def move():
    j = request.json or {}
    a, b, today = j.get("from"), j.get("to"), dt.date.today().isoformat()
    if not a or not b or a < today or b < today:
        return jsonify(error="Only today and future days can be moved."), 400
    if not jobs.swap(a, b):
        return jsonify(error="No plan for that day."), 400
    db.run("INSERT INTO moves(a,b) VALUES(?,?)", (a, b))
    log.info("Sessions swapped: %s and %s", a, b)
    jobs.start("push")
    return jsonify(ok=True, warning=_hard_warning(today))


@app.post("/api/plan/undo")
def undo():
    m = db.rows("SELECT * FROM moves ORDER BY id DESC LIMIT 1")
    if not m:
        return jsonify(error="Nothing to undo."), 400
    jobs.swap(m[0]["a"], m[0]["b"])
    db.run("DELETE FROM moves WHERE id=?", (m[0]["id"],))
    if not db.rows("SELECT 1 FROM moves WHERE a IN (?,?) OR b IN (?,?)", (m[0]["a"], m[0]["b"]) * 2):
        db.run("UPDATE plan SET source='auto' WHERE date IN (?,?)", (m[0]["a"], m[0]["b"]))
    log.info("Move undone: %s and %s", m[0]["a"], m[0]["b"])
    jobs.start("push")
    return jsonify(ok=True)


@app.get("/api/export")
def export():
    """A zip with a copy of the database (login secrets removed) and the plan as JSON."""
    buf = io.BytesIO(backup.portable())
    log.info("Backup downloaded")
    return send_file(buf, mimetype="application/zip", as_attachment=True, download_name=f"periodize-backup-{dt.date.today()}.zip")


@app.post("/api/setup/finish")
def setup_finish():
    """The athlete has seen the summary at the end of the first-run wizard."""
    db.put("setup_seen", True)
    return jsonify(ok=True)


@app.get("/api/updates")
def updates_state():
    return jsonify(updates.state())


@app.post("/api/updates")
def updates_act():
    """check | install | choose | dismiss. Installing or choosing restarts the app into that version."""
    j = request.json or {}
    act, v = j.get("action"), j.get("version")
    try:
        if act == "check":
            updates.check()
        elif act == "dismiss":
            db.put("update_dismissed", str(v)[:20])
        elif act in ("install", "choose"):
            if jobs.status["running"]:
                return jsonify(error="Wait for the current update to finish, then try again."), 409
            (updates.install if act == "install" else updates.choose)(v)
            updates.restart_soon()
            return jsonify(ok=True, restarting=True)
        else:
            return jsonify(error="Unknown action."), 400
    except ValueError as e:
        return jsonify(error=str(e)), 400
    except (requests.RequestException, OSError) as e:
        log.error("Update failed: %s", type(e).__name__)
        return jsonify(error="The update could not be completed. Nothing was changed."), 400
    return jsonify(updates.state())


@app.post("/api/watch")
def watch_source():
    """Choose where runs come from. The folder for FIT files can only be set from the computer the app runs on."""
    j = request.json or {}
    src = j.get("source")
    if src not in watch.SOURCES:
        return jsonify(error="Unknown source."), 400
    if src == "fitfolder":
        folder = j.get("fit_folder")
        if folder is not None:
            if not _local():
                return jsonify(error="The folder can only be chosen on the computer Periodize My Run runs on."), 403
            folder = os.path.abspath(os.path.expanduser(str(folder).strip()))[:500]
            if not os.path.isdir(folder):
                return jsonify(error="That folder was not found."), 400
            db.put("fit_folder", folder)
        if not db.get("fit_folder"):
            return jsonify(error="Choose the folder first."), 400
    if src == "coros" and not coros.connected():
        return jsonify(error="Sign in to COROS first."), 400
    db.put("watch_source", src)
    log.info("Runs now come from %s", watch.NAMES[src])
    if db.get("setup_done"):
        jobs.start("daily")
    return jsonify(ok=True)


@app.post("/api/coros/login")
def coros_login():
    j = request.json or {}
    try:
        return jsonify(result=coros.login(str(j.get("email") or "").strip(), str(j.get("password") or "")))
    except ValueError as e:
        return jsonify(error=str(e)), 400
    except (coros.Unrecognised, requests.RequestException) as e:
        log.error("COROS (experimental) sign-in failed: %s", type(e).__name__)
        return jsonify(error="COROS did not accept the sign-in. This connection is experimental and may not work."), 400


@app.post("/api/coros/disconnect")
def coros_disconnect():
    coros.disconnect()
    return jsonify(ok=True)


@app.post("/api/garmin/disconnect")
def garmin_disconnect():
    garmin.disconnect()
    return jsonify(ok=True)


@app.post("/api/run")
def run_now():
    kind = (request.json or {}).get("kind", "daily")
    if kind not in ("setup", "daily", "replan", "readiness", "push"):
        return jsonify(error="unknown job"), 400
    return jsonify(started=jobs.start(kind))


def learned(c, L):
    """The model values taken from this athlete's own data, with how much data each rests on."""
    m = db.get("model") or {}

    def line(key, text_learned, text_default):
        v = m.get(key)
        if not v:
            return "Not calculated yet."
        return text_learned(v) if v["learned"] else text_default(v)

    out = [
        line("threshold_correction",
             lambda v: f"Your races come out at {v['value']:.2f} times what your pace-to-heart-rate line predicts, measured in the four weeks before {v['n']} of your races. Your threshold estimate is corrected by that.",
             lambda v: "Threshold from heart rate: read straight from your own pace-to-heart-rate line, with no correction yet. It is checked against your races once one has four weeks of detailed runs before it."),
        line("distance_slope",
             lambda v: (f"Across {v['n']} of your race results, your race fitness changes by {v['value']:+.2f} index points for each step of 2.7 times the distance: "
                        + ("you are relatively stronger at shorter races" if v["value"] < -0.3 else "you are relatively stronger at longer races" if v["value"] > 0.3 else "you race evenly across distances")
                        + ". Predictions use this profile."),
             lambda v: f"Your profile across distances: not enough race results yet ({v['n']} usable; needs 4 across two distances in a year). Predictions assume you race evenly across distances."),
        line("slow_per_point",
             lambda v: f"On mornings with poor recovery you have run {v['value']:.1%} slower per heartbeat for each readiness point, measured on {v['n']} such runs. That is how much today's fast running is eased.",
             lambda v: f"Easing per readiness point: using the general value {v['value']:.1%}. It becomes yours after 8 runs on poor-recovery mornings ({v['n']} so far) and 20 on normal ones."),
    ]
    if L:
        out.append(f"From your history: maximum heart rate {L['hrmax']}, peak week {engine.dist(L['peak_miles'], c['units'])}, longest long run {engine.dist(L['long_run_cap_specific'], c['units'])}.")
    out.append("Your normal ranges for sleep, HRV, resting heart rate and steps are recalculated every day from your last 8 weeks. A value counts as poor when it is unusual for you, not when it crosses a fixed number.")
    out.append("Race results from the last 26 weeks carry forward as evidence of fitness, faded 0.15% a week if you have kept your training up since, 0.5% a week if it has dropped.")
    tr = db.get("altitude_trust") or {}
    for dev, v in tr.items():
        name = dev.split("-")[0] or "watch"
        out.append(f"Altitude from your {name}: " + (f"trusted (on {v['runs']} loop runs it returned to within {v['median']:g} m of where it started), so hilly runs are grade-adjusted."
                   if v["trusted"] else f"not trusted (on {v['runs']} loop runs it was typically {v['median']:g} m out at the finish), so its hilly runs are left out of pace-at-heart-rate comparisons instead of being adjusted."))
    if m.get("updated"):
        out.append(f"Last recalculated {m['updated']}. It is redone after every sync.")
    return out


PROJECT = {"url": "https://github.com/romahony26/periodize",
           "support": "https://buymeacoffee.com/romahony"}      # the maintainer's Buy Me a Coffee page; the link is hidden when empty
_TRENDS = {"key": None, "data": None}


@app.get("/api/trends")
def trends_view():
    """Speed, endurance base, durability, steps and recovery over time, each with its direction. Cached until the next sync."""
    c, today = db.cfg(), dt.date.today()
    lo = jobs.last_ok(("setup", "daily", "replan", "readiness", "push"))
    key = (today.isoformat(), lo.isoformat() if lo else None, c["units"])
    if _TRENDS["key"] != key:
        _c, prof, rs, L = jobs.context()
        if not prof or not L:
            return jsonify(error="Not enough data yet."), 404
        hist = trends.history(_c, L, today)
        _TRENDS["data"] = {"speed": trends.speed(c, hist), "base": trends.base(hist), "durability": trends.durability(today),
                           "steps": trends.steps(today), "recovery": trends.recovery(today),
                           "predictions": trends.prediction_change(_c, hist, trends.all_distances()),
                           "races": trends.race_check(_c, L, today)}
        _TRENDS["key"] = key
    return jsonify(_TRENDS["data"])


@app.get("/api/backups")
def backups():
    return jsonify({"backups": backup.listing()})


@app.post("/api/backups")
def backup_now():
    """Make a backup, or restore one. Restores: what full|config|plan."""
    j = request.json or {}
    try:
        if j.get("restore"):
            what = j.get("what") or "full"
            backup.restore(j["restore"], what)
            done = what
            _FRESH.clear()
            _PERF["key"] = None
            jobs.start("replan" if done == "config" else "push")
            return jsonify(ok=True, restored=done)
        return jsonify(ok=True, made=backup.make(dt.datetime.now().strftime("%H%M%S")))
    except ValueError as e:
        return jsonify(error=str(e)), 400
    except RuntimeError as e:
        return jsonify(error=scrub(str(e))[:200]), 400


@app.get("/api/calendar.ics")
def calendar_file():
    return app.response_class(calfile.ics(db.cfg()), mimetype="text/calendar", headers={"Content-Disposition": "attachment; filename=periodize.ics"})


@app.post("/api/shoes")
def shoe_save():
    j = request.json or {}
    try:
        name = (j.get("name") or "").strip()[:60]
        start = dt.date.fromisoformat(j["start"]).isoformat()
        k = 1 if db.cfg()["units"] == "mi" else 1000 / assess.MI
        sm = float(j.get("start_dist") or 0) * k
        al = float(j["alert_dist"]) * k if j.get("alert_dist") not in (None, "") else None
        if not name or not 0 <= sm <= 5000 or (al is not None and not 50 <= al <= 5000):
            raise ValueError
    except (KeyError, ValueError, TypeError):
        return jsonify(error="A pair of shoes needs a name and the date you started using them."), 400
    if j.get("id"):
        db.run("UPDATE shoes SET retired=? WHERE id=?", (dt.date.today().isoformat() if j.get("retire") else None, int(j["id"])))
    else:
        db.run("INSERT INTO shoes(name,start,start_miles,alert_miles) VALUES(?,?,?,?)", (name, start, sm, al))
    return jsonify(ok=True)


@app.delete("/api/shoes/<int:sid>")
def shoe_delete(sid):
    db.run("DELETE FROM shoes WHERE id=?", (sid,))
    return jsonify(ok=True)


@app.post("/api/notify/test")
def notify_test():
    if not vault.get("notify_url"):
        return jsonify(error="Save a daily message address first."), 400
    jobs.notify(jobs.today_message() or "Periodize My Run test message: this is where your morning session will arrive.")
    return jsonify(ok=True)


@functools.cache
def changelog():
    """Every version from CHANGELOG.md, newest first: [{version, date, sections: [{title, items}]}]."""
    out = []
    with open(os.path.join(HERE, "CHANGELOG.md"), encoding="utf-8") as f:
        for line in f:
            line = line.rstrip()
            if line.startswith("## "):
                v, _, d = line[3:].partition(" - ")
                out.append({"version": v.strip(), "date": d.strip(), "sections": []})
            elif line.startswith("### ") and out:
                out[-1]["sections"].append({"title": line[4:].strip(), "items": []})
            elif line.startswith("- ") and out and out[-1]["sections"]:
                out[-1]["sections"][-1]["items"].append(line[2:].strip())
    return out


TERMS_VERSION = 1


def terms_accepted():
    return (db.get("terms_accepted") or {}).get("version") == TERMS_VERSION


@app.get("/api/terms")
def terms_text():
    with open(os.path.join(HERE, "DISCLAIMER.md"), encoding="utf-8") as f:
        return jsonify(version=TERMS_VERSION, accepted=terms_accepted(), text=f.read())


@app.post("/api/terms")
def terms_accept():
    if (request.json or {}).get("accept") is not True:
        return jsonify(error="Tick the box to accept the terms."), 400
    db.put("terms_accepted", {"version": TERMS_VERSION, "at": dt.datetime.now().isoformat(timespec="seconds")})
    log.info("Terms of use version %d accepted", TERMS_VERSION)
    return jsonify(ok=True)


@app.get("/api/changelog")
def changelog_page():
    return jsonify(versions=changelog())


@app.get("/api/history")
def history():
    c = db.cfg()
    prof = db.get("profile")
    if not prof:
        return jsonify(sessions=[], weeks=[], average=None, count=0)
    goal = db.rows("SELECT miles FROM races WHERE priority='A' AND date>=? ORDER BY date LIMIT 1", (dt.date.today().isoformat(),))
    return jsonify(execution.history(c, profile.limits(prof, c, goal[0]["miles"] if goal else None), weeks=min(max(request.args.get("weeks", 12, type=int), 1), 104)))


@app.get("/api/day/<date>")
def day_detail(date):
    """One day in full, for the popup: plan, execution score, and each run with its pace and heart rate series and route outline."""
    try:
        dt.date.fromisoformat(date)
    except ValueError:
        return jsonify(error="Not a date."), 400
    c = db.cfg()
    prof = db.get("profile")
    if not prof:
        return jsonify(error="No data yet."), 404
    goal = db.rows("SELECT miles FROM races WHERE priority='A' AND date>=? ORDER BY date LIMIT 1", (dt.date.today().isoformat(),))
    return jsonify(execution.day(date, c, profile.limits(prof, c, goal[0]["miles"] if goal else None)))


@app.get("/api/about")
def about():
    """What the app does and how, built from the live settings and rule tables so it never drifts from the code."""
    c, today = db.cfg(), dt.date.today()
    prof = db.get("profile")
    rs = db.rows("SELECT * FROM races ORDER BY date")
    goal = next((r for r in rs if r["priority"] == "A" and r["date"] >= today.isoformat()), None)
    L = profile.limits(prof, c, goal["miles"] if goal else None) if prof else {}
    D = lambda m: engine.dist(m, c["units"])
    n_act = db.rows("SELECT COUNT(*) n, SUM(detail IS NOT NULL) d FROM activities")[0]
    yn = lambda b: "on" if b else "off"
    ladder = " → ".join(f"{t} min ({n} x {m})" for t, n, m, _ in engine.T_LADDER)
    zones = "; ".join(f"{engine.ZONE_NAME[z]} {lo:.0%}" + (f"–{hi:.0%}" if hi != lo else "") for z, (lo, hi) in assess.ZONES.items())
    sec = [
        ("Data it uses", [
            f"Your whole Garmin activity list, in summary: {n_act['n'] or 0:,} activities stored. Used for best times, highest sustained mileage, maximum heart rate and breaks from running.",
            f"Second-by-second files for runs in the last {c['detail_weeks']} weeks: {n_act['d'] or 0} stored. Used to measure pace, heart rate and time at each intensity.",
            "Resting heart rate, sleep, overnight HRV and weight for the last 9 weeks, then each new day.",
            "Planning looks at the 8 weeks before each Monday.",
        ]),
        ("Your personal limits (from your history)", [
            f"Peak week: {D(L['peak_miles'])}, from {L['peak_why']}. A block counts only if the six weeks after it held up: no two weeks in a row under 35% of it "
            "(rest after a race, a very long run or a holiday is not counted against it), and no time recorded as sick or injured. Your recent average does not raise it." if L else "Not yet calculated.",
            f"Above {D(engine.half(L['proven_miles']))} a week (the most you have held for eight weeks in the last year) the weekly rise is halved, and after a week or more without running "
            "the distance is held level for three weeks." if L else "",
            f"Longest long run: {D(L['long_run_cap_specific'])} in the race-specific phase, {D(L['long_run_cap_base'])} before it." if L else "",
            f"Maximum heart rate {L['hrmax']}: easy under {L['easy_hr_max']}, steady under {L['steady_hr_max']}, threshold cap {L['threshold_hr_cap']}, race-effort band {L['marathon_hr_band'][0]}–{L['marathon_hr_band'][1]}." if L else "",
            f"Race-specific phase: the last {L['specific_weeks']} weeks before the goal race." if L else "",
        ]),
        ("How fitness is measured", [
            "Threshold speed is the best of: your best efforts in the last 8 weeks (20, 30 and 60 minutes; 5K, 10K, 10 miles, half marathon), your races in the last 26 weeks, and your own pace-to-heart-rate line.",
            f"The pace-to-heart-rate line: below threshold, speed rises almost in a straight line with heart rate. The app fits that line to your last 28 days of steady running and reads it at threshold heart rate (about {c['threshold_hr_fraction']:.0%} of your maximum). No figure from any other runner is involved.",
            f"It may rise at most {c['max_weekly_gain']:.1%} and fall at most {c['max_weekly_loss']:.1%} per week, so one odd run cannot swing your paces.",
            f"All training paces are fractions of threshold speed: {zones}.",
            f"Race predictions use the same speed; marathon and half marathon predictions are slowed by up to {c['max_endurance_penalty']:.0%} when long runs, race-pace miles and weekly volume are short of a full build.",
            "Paces follow your fitness, not your goal time. The goal time is only used to show the gap.",
        ]),
        ("Aerobic base: is it working?", [
            "The idea: aerobic fitness shows up as a faster pace at the same heart rate. That is what the app tracks, and what the aerobic test measures. These are coaching conventions applied alongside the app's other rules, not findings from controlled studies.",
            (f"The aerobic test, every {c['aero_test_weeks']} weeks. Short version: a mile warm-up, then one mile at each of {', '.join(str(x) for x in engine.hr_levels(L['hrmax'])['stages'][:4]) if L else ''} bpm without stopping, then 500 m all out, about 6 miles in all. The all-out finish also checks your maximum heart rate. "
             "The long version is five 2400 m stages with 90 seconds rest, about 10 miles; choose it in Settings if you prefer."),
            "What to look for: the same heart rate at a faster pace. Aerobic adaptation is slow, so expect small changes after 3 weeks and clear ones after 6. Testing more often mostly measures noise.",
            "Between tests the app shows your pace at each heart rate month by month from your ordinary runs, so you can see the trend without waiting.",
            "Those paces are grade-adjusted: each stretch of a run is converted to what it was worth on the flat, using the energy cost of running uphill and downhill (Minetti and colleagues, 2002), so hilly road runs count too. Trail runs are left out: rough ground and walking slow them in ways gradient does not explain. Nothing is adjusted for wind or heat.",
            f"Aerobic runs by heart rate: before the race-specific phase, one session a week is run at a fixed heart rate below your threshold (currently {db.get('aero_lthr') or (engine.hr_levels(L['hrmax'])['start_lthr'] if L else '')} bpm), not at a pace. If the heart rate climbs, you slow down. It builds from 5 to 10 miles.",
            "The heart rate moves up 5 only when you have run 10 miles at the current level in one run. Building patiently at each level is the point.",
            "Easy days stay easy: about 50 beats below your maximum. Endurance falls short for two common reasons: too few miles, and easy miles run too fast.",
            f"Race-pace relationship: a well-trained runner slows by about {aerobic.DOUBLING_GOOD} seconds a mile each time the race distance doubles; {aerobic.DOUBLING_LOOSE}+ means aerobic work is the priority. This is a long-standing coaching rule of thumb. The Fitness page shows yours.",
            "A sign the aerobic base is ready for race-specific work: 10 miles at marathon heart rate with no fall in pace.",
            "200s: 200 m at about 5K pace, 200 m easy, without stopping. Fast legs without hard effort; the point is the difference between the fast and easy halves, not the overall time.",
        ]),
        ("Race predictor and VO2max", [
            "Predictions turn one performance into equivalent times at other distances, using published equations for the oxygen cost of running at a speed and the fraction of capacity that can be held for a given time (Daniels and Gilbert, 1979).",
            "The starting point is your threshold speed, treated as the pace you could hold for an hour.",
            f"For the half marathon, marathon and 50K, the prediction has two parts: your speed, and up to {c['max_endurance_penalty']:.0%} added while your long runs, race-pace miles and weekly volume are short of a full build. The predictor shows how much of the time is that endurance gap, and what the time would be at the same speed once it is closed.",
            "50K is the marathon speed faded for distance. It ignores terrain, so treat it as a rough guide.",
            "The VO2max figure on the Fitness page is Garmin's own estimate from your watch, shown for reference. The app does not use it.",
            "Race results are found in your history as runs of a standard race distance within 6% of your best form of that period, entered by hand, or imported from your own race log (a CSV file). Official times from your log replace the watch times for the same race.",
            "Cross-country, trail and paced races are kept with their notes but do not count toward your fitness numbers.",
        ]),
        ("What it has learned about you", learned(c, L)),
        ("Race-day forecast", [
            "The forecast is where you are likely to be on race day, not where you are today. It is recalculated at every sync, so it moves with what you actually do.",
            "It starts from your current fitness and moves toward your proven level: the best you have shown in race results in the last three years, adjusted for distance using your own record.",
            f"How far it gets depends on the training you complete. Each {forecast.TAU:g} weeks of completed training closes about 63% of the remaining gap; the last {forecast.TAPER_WEEKS} weeks are taper and do not count. This rate is a general rule, not learned from you.",
            "It does not assume you do everything. It uses the share of training you have historically delivered: each of your last 104 weeks is compared with the six weeks before it, and missed or cut weeks pull the average down.",
            "As this plan runs, your actual completion (distance run on planned days against distance planned) replaces the historical figure, taking over fully after about 8 weeks of planned days. Do more of the plan and the forecast improves; miss training and it slips.",
            "You can set the completion figure yourself in Settings instead; the card then shows your choice beside what your history and this plan say.",
            "It also shows the time if you complete all of it, and if you complete 20 points less than expected.",
            "It cannot forecast beyond your proven level. If you go past it, your new results raise the level and the forecast follows.",
        ]),
        ("How each week is chosen", [
            "Race week, taper (3 weeks for a marathon, 1 for a half), tune-up race week, recovery after a race, recovery when warning signs appear, return after missed training, down week, or build week, checked in that order.",
            f"Build weeks add {c['weekly_increase']:.0%} to your recent volume up to your cap. Volume is held level in a week where fast running is being reintroduced.",
            f"A down week (75%) follows {c['build_weeks_before_down']} full weeks in a row; from age 50, two, unless you have set this yourself.",
            "After two or more weeks well below your usual level, for any reason, the return lasts about as long as the break (up to four weeks): about half your usual volume, then three quarters, all easy. The break is spotted from your runs.",
            "During a break the fitness estimate fades too: nothing for the first 10 days without a run, then 0.35% a day, up to 12%, so your first paces back match what you can do now.",
            f"Warning signs: resting heart rate up {c['rhr_rise_bpm']}+ on your normal, HRV down {1 - c['hrv_drop_fraction']:.0%}+, sleep under {c['sleep_7night_min_h']} h a night, easy pace per heartbeat down {c['easy_pace_drop_fraction']:.0%}+. {c['flags_to_back_off']} of them make a recovery week.",
            f"Each Monday the week is planned from real data. The {c['weeks_ahead']} weeks after are planned provisionally, each assuming the one before goes to plan, and are redone at every weekly review.",
        ]),
        ("How sessions progress", [
            f"Threshold ladder, one step on from your biggest session of the last 3 weeks: {ladder}.",
            "Marathon goal: midweek marathon-pace block grows one mile at a time (4 to 8); marathon-pace long runs of 8 → 10 → 12 → 14 miles at least 13 days apart in the specific phase; 10K-pace intervals every third week.",
            "Half marathon goal: half-marathon-pace blocks of 3 to 6 miles in the specific phase. 5K and 10K goals: alternating 5K-pace and 10K-pace intervals, plus threshold.",
            "Long run: never more than 10% beyond your longest run of the last 30 days, and, except for ultra goals, no more than about three hours.",
            f"Your week: {c['run_days']} running days, long run on {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][c['long_day']]}. With 5 or 6 days there are two quality sessions; with 3 or 4 there is one.",
            f"Strength reminders: {yn(c['strength'])}.",
        ]),
        ("Steps outside your runs", [
            "Everyday walking is training load the plan does not schedule, so the app tracks it. It takes your daily step count from Garmin and subtracts the steps of your runs.",
            "If the last 7 days average more than one standard deviation above your own normal, that counts as a warning sign for the weekly plan.",
            "Steps are not added to your running miles: walking loads the body differently from running.",
        ]),
        ("Freshness and weekly trend on the calendar", [
            "Freshness is one number for how recovered you are this morning. 100 means everything is at your normal or better; it never goes below 35. Each marker is read over the window the research supports.",
            "Sleep is read from last night alone: a single short night does measurably reduce endurance performance the next day (Lopes and colleagues, 2023; Craven and colleagues, 2022). The last three nights together also count, because sleep debt builds.",
            "HRV and resting heart rate are read as 7-day averages against your own normal range over the 60 days before. One night's reading is too noisy to act on; a 7-day average is the established method (Plews and colleagues, 2012 and 2013), and a shift of half your normal spread is the smallest change treated as real.",
            "So a bad night's sleep eases today's session and a normal night clears it, while HRV and resting heart rate only ease a session once they have drifted for several days.",
            "The week's ±% in each week's heading is your pace for your heart rate across all that week's road runs, hills adjusted, against the four weeks before. It is a weekly comparison because a single run swings with wind, heat, route and time of day.",
            "Read them together over weeks: freshness falling while the weekly ±% falls is fatigue showing in the running.",
            "Both are the app's own measures built from your Garmin data, not Garmin's figures, and neither is a medical reading.",
        ]),
        ("History and execution score", [
            "The History tab lists every planned session that has passed, what you ran that day, and an execution score from 0 to 100. Click a session for the run itself: time of day, heart rate, load, pace and heart rate charts, and the route.",
            "The method is taken from the training-load research, not from weights of the app's own. Running is split into three zones at the two thresholds: easy, moderate and hard. Minutes in each are weighted 1, 2 and 3. That is Lucia's TRIMP (Lucia and colleagues, 2003), a published measure of training load: a minute of hard running counts three times a minute of easy running.",
            "The score is how far the session you ran departed from the session planned, zone by zone, in those weighted minutes, as a share of the planned load. Too much counts the same as too little: the best-known finding here (Foster and colleagues, 2001) is that athletes run easy days harder than intended and hard days easier.",
            "So an easy run done too fast loses marks, a session with the reps cut short loses marks, and a session run much harder than set loses marks too.",
            "What is still the app's own judgement: where the zone boundaries sit without a laboratory test (88% and 102% of your threshold speed; 82% and 89% of maximum heart rate for sessions set by heart rate), and one minute of tolerance per zone for GPS noise. The combined score is a direct use of a validated load measure, not itself a validated test.",
            "A missed session scores 0. Scores build up from the day the app started planning for you.",
            "Load, shown on each run, is the same weighted minutes. Garmin's own training effect and load are shown beside it where Garmin provides them.",
            "The route is drawn as an outline from the watch's GPS points. There is no map behind it, because the app loads nothing from outside services.",
        ]),
        ("Fitness, fatigue and form", [
            "Every run has a load: its easy, moderate and hard minutes weighted 1, 2 and 3 (Lucia's TRIMP), the same measure the execution score uses.",
            "Fitness is your average daily load fading over 42 days; fatigue is the same over 7 days; form is fitness minus fatigue. This is Banister's impulse-response model in its usual simplified form. The 42 and 7 are the conventional values, not fitted to you.",
            "Rising fitness with form mildly negative is normal building. Form deeply negative for long means you are digging a hole. Form should rise toward zero or above in a taper.",
            "Runs older than the detail window count all their minutes as easy, so fitness from more than six months ago is slightly understated.",
        ]),
        ("Watch-outs", [
            "A run more than 10% longer than your longest run of the previous 30 days is flagged, whether you ran it or the plan asks for it this week. In a study of 5,200 runners (Frandsen and colleagues, 2025), that single-run jump went with more overuse injuries.",
            "The same study found no link between injury and week-to-week mileage change, so there is no weekly-increase warning.",
        ]),
        ("Aerobic drift", [
            "For each steady run of 70 minutes or more: how much your pace per heartbeat fell from the first half to the second, leaving out the first 10 minutes.",
            "Lower is better and it should fall as endurance builds. Under 5% is a common coaching rule of thumb; it is not a research threshold. Heat, hills and a fast finish all raise it, so judge the trend, not one run.",
            "Sessions, races, trail runs and treadmill runs are left out.",
        ]),
        ("Season outline", [
            "The Plan page shows every week to your goal race: the kind of week, the total and the long run. Each week assumes the one before goes to plan.",
            "Only this week is fixed. The outline is redrawn at every weekly review from what you actually ran.",
        ]),
        ("Fuelling", [
            "Any planned run of 75 minutes or more shows a fuelling outline in its popup: grams of carbohydrate an hour and what that is in gels.",
            "The amounts follow Jeukendrup (2014): about 30 g an hour for runs of 1 to 2 hours, up to 60 g for 2 to 3 hours, and up to 90 g beyond 2.5 hours if your stomach is trained for it. Long runs in a marathon or ultra build step the amount up toward race day.",
            f"A gel is taken as {c['gel_carbs_g']} g of carbohydrate; set your own under Settings. Race day uses {c['race_carbs_g_per_h']} g an hour.",
        ]),
        ("Age grading", [
            "Each road result is shown as a percentage of the world-best standard for your age and sex at that distance, so a race at 30 and a race at 45 can be compared.",
            "The standards are Alan Jones's 2025 road tables, which are public domain. Your sex and date of birth are read from Garmin once and can be changed or removed under Settings.",
            "Where a course's hills are known, the flat-equivalent time is graded. Off-road and paced races are not graded.",
        ]),
        ("The watch's own threshold", [
            "Garmin's estimate of your threshold pace and heart rate is read once a day and shown beside the app's own figure.",
            "While it is no more than six weeks old it counts as one more piece of evidence for your threshold pace, alongside your best efforts, races and heart-rate line. The best evidence wins, and the weekly limits on change still apply.",
        ]),
        ("Treadmill runs", [
            "A watch on a treadmill guesses distance from arm swing, so pace is not trusted. Treadmill runs are scored on heart rate, and are left out of threshold evidence, pace-at-heart-rate trends and aerobic drift. Their time still counts toward load and their distance toward weekly totals.",
            "Track runs recorded in the watch's track mode are treated as normal runs.",
        ]),
        ("Shoes", [
            "Add a pair with the date you started using it. Its distance is every run from that date until you start the next pair. Set a limit and you are told when it is passed.",
            "This assumes one pair in use at a time. There is no research-backed distance at which shoes should be replaced.",
        ]),
        ("Daily message", [
            "For a morning message with the day's session and any easing, set a daily message address under Settings, Advanced (for example a private ntfy topic), save, and press Send a test message.",
        ]),
        ("Missed sessions", [
            "If a session day passes with no run, the session is moved to the first later day that week that keeps an easy or rest day either side of every hard day. It replaces that day's easy run, and the day is marked as moved.",
            "If you ran the session on a different day, the app recognises it (the run matches the session at 65 or more) and moves nothing.",
            "If no day fits, the session is dropped. Squeezing hard days together costs more than the session gains. Keeping hard days apart is standard coaching practice, not a research threshold.",
            "Long runs are not moved: they sit at the end of the week, and the next week is planned from what you actually ran. Days you were sick, injured or on holiday are not counted as missed. A day you dragged yourself is never overwritten.",
        ]),
        ("Race pacing plan", [
            "Add a race's course as a GPX file (Races & status) and the app gives you a split for every mile or kilometre.",
            "The plan is even effort: every stretch costs the same energy, using Minetti's measured cost of running up and down gradients (2002), the curve behind grade-adjusted pace. Uphill splits are slower, downhill faster, and they add up to your target time.",
            "The target is your goal time, or what you could run today if no goal is set; you can type any time.",
            "The GPX file is read in your browser; only distance and elevation every 100 m are stored. Elevation is smoothed over 300 m because GPX elevation is noisy.",
            "It does not model fatigue, walking, footing, wind or heat. For an ultra, treat it as how the effort should be spread, not as times to hit.",
        ]),
        ("Climb targets", [
            "When your goal race is hilly (about 10 m of climb per km or more), the Plan page shows a climb target for the week and for the long run.",
            "The target ramps from your own climb per mile over the last four weeks to the race's climb per mile, starting 16 weeks out and reaching it 3 weeks out. That is specificity, a coaching principle, not a research finding.",
            "A race's climb comes from its GPX course, or you can enter the total by hand. Climb done is Garmin's figure for each run.",
        ]),
        ("Maps", [
            "Each run's route is drawn as an outline by default, and nothing is loaded from outside.",
            "If you switch on real maps (Settings, Connections), map images are loaded from OpenStreetMap when you open a run. OpenStreetMap's servers then see which area you are looking at. No account, name or run data is sent.",
        ]),
        ("Daily adjustment", [
            f"Status: {yn(c['daily_adjust'])}. Runs at {c['run_time']}. A bad night's sleep eases today's session; HRV and resting heart rate ease it only when their 7-day average has drifted.",
            "Sleep points, against your own normal: last night an hour or more under = 1 (two hours under, or under 5 hours = 2); last night's sleep score below your normal range = 1 (far below = 2); the last 3 nights averaging an hour under = 1. Sleep counts for at most 2.",
            "Trend points: 7-day HRV half a spread below your normal = 1 (a full spread below, outside your normal range = 2); 7-day resting heart rate 3 above normal = 1 (5 above = 2).",
            "The windows come from the research. The exact point values are the app's own choice.",
            f"Each point eases today's fast running by {calibrate.value('slow_per_point'):.1%}, up to four points. Easy running is not changed.",
            "At 3+ points, or a point or more on three mornings running, the session becomes an easy run of the same distance, on the watch too. The planned session is still shown, and comes back once you have recovered.",
            "Every scheduled contact with Garmin (the daily sync and the four-hourly watch check) is moved by its own random amount, up to 30 minutes either way, so installs do not all reach Garmin at the same moment.",
            "The easing per point is measured from your own runs once there are enough; see What it has learned about you.",
        ]),
        ("Holidays", [
            "Add a holiday with its dates and choose how you want to run: " + "; ".join(v.lower() for v in engine.HOLIDAY_MODES.values()) + ".",
            "Sessions only keeps the quality sessions and drops everything else. Easy runs only turns sessions and the long run into shorter easy runs.",
            "Strength reminders are dropped while you are away. A race during a holiday is left as planned.",
            "There is no return period after a holiday. If your running dropped a lot, the next weekly review treats it as a return week automatically.",
        ]),
        ("Sick or injured", [
            "While marked sick or injured, every day is rest.",
            "After sickness: easy running only for as many days as you were out (up to 7), building from half distance.",
            "After injury: easy running only for twice the days you were out (up to 14).",
            "Any change replans from today.",
        ]),
        ("Your watch", [
            f"Status: {yn(c['push_enabled'])}. The next {c['push_days']} days are kept on your Garmin calendar as structured workouts with pace targets on the fast parts.",
            f"Easy and steady runs: {'pace range alerts' if c['easy_target'] == 'pace' else 'no pace alerts'}.",
            "A day is re-sent only when it changes: a replan, a move, or today's pace adjustment. Only workouts made by this app (names starting PZ) are ever deleted.",
            "Every four hours (around 02:00, 06:00, 10:00, 14:00, 18:00 and 22:00 UTC, each moved by up to 30 minutes at random) the app checks your Garmin calendar and puts back any workout that is missing, such as one deleted in Garmin Connect.",
        ]),
        ("Moving sessions", [
            "Drag any future day onto another to swap them. It warns if two hard days end up back to back.",
            "Your moves are kept when the plan is recalculated: they are replayed onto the new plan. Undo reverses the last move.",
        ]),
        ("Keeping itself running", [
            "Checks every 5 minutes whether today's sync has happened; catches up after the computer was off; retries failed Garmin requests with growing waits.",
            f"Requests to Garmin are spaced {c['pause_min_s']:g}–{c['pause_max_s']:g} seconds apart at random. Everything downloaded is cached.",
            "The plan page warns when there has been no successful sync for 7 days.",
        ]),
        ("Fuelling", [
            "Marathon and longer: practise taking carbohydrate on long runs, building from 30 g an hour early in the plan to 60–70 g an hour in the last ten weeks. The long run note shows the week's target.",
            f"Race day for a half marathon or longer: {c['race_carbs_g_per_h']} g of carbohydrate an hour as a minimum, in small amounts every 15–20 minutes, with whatever you practised.",
            "Marathon: 10–12 g of carbohydrate per kg of body weight per day for the last 36–48 hours.",
            "Do not train hard while eating well under what you burn. If you want to lose weight, do it early in the plan, by a small daily deficit, and stop before the race-specific phase.",
        ]),
        ("Strength", [
            "Two short sessions a week on the days shown, one a week in the race-specific phase, none in the last two weeks before the goal race.",
            "Strength A: squat or leg press; single-leg deadlift; calf raises with straight and bent knee; side plank.",
            "Strength B: split squat or step-up; hip thrust; hamstring curl or bridge walk-outs; then plyometrics: pogo hops, skipping for height and bounding, quick and light, with full recovery between sets.",
            "Three sets of 5–8 controlled reps, stopping well short of failure. Start light for four weeks, then add load.",
        ]),
        ("Backups and calendars", [
            f"Automatic backups: {yn(c['auto_backup'])}. One is made every night on this computer and thinned as it ages: every day for the last {backup.DAILY} days, the last of each of the last {backup.WEEKLY} weeks, and the last of each of the last {backup.MONTHLY} months. Older ones are deleted. This is the standard grandfather-father-son scheme.",
            "Restore options: everything; settings and races only; or the plan only. Restoring everything keeps this computer's own Garmin connection. The state just before any restore is saved first, so it can be undone.",
            "Download backup gives a copy with every login secret removed, for keeping somewhere else. To keep a copy off this computer every day, tools/pull_backup.py fetches one from another computer into a folder that a sync app such as Google Drive for desktop or iCloud Drive uploads.",
            "Calendar file: the next sessions as a file that Apple Calendar, Outlook or Google Calendar can import.",
        ]),
        ("Privacy and security", [
            "No password is stored, anywhere. Your Garmin password goes straight to Garmin once and is exchanged for an access token. Garmin offers personal apps no sign-in that avoids this.",
            "The Garmin tokens and your notification address are encrypted before they are stored. The key is kept in a separate file outside the data folder, readable only by you, so a copy of your data or a backup gives away no logins.",
            "What encryption here cannot do: someone who can read all of your user account's files can read the key as well. Full-disk encryption on the computer is the protection against that.",
            "Nothing is sent anywhere except your watch's service (Garmin, or COROS if you choose it), your notification address if you set one, only if you switch heat adjustment on, your rough location (to about 10 km) to Open-Meteo for the weather, and, unless you switch it off, a daily request to GitHub for the latest version number.",
            "From other devices the app needs a password, set on this computer; only a salted hash of it is kept. Five wrong attempts lock that device out for 15 minutes. The app refuses to listen on the network without one.",
            "On a Raspberry Pi the installer creates a certificate so the connection is encrypted (https). Your browser will warn once because the certificate is self-made.",
            "Every change must come from the app's own page: requests from other websites, unknown host names and forged forms are refused. The page runs no script except its own file.",
            "Logs are private to you and are filtered for anything resembling a password, token, key or email address.",
            "The app is checked with a red-team test suite organised by the OWASP Top 10, two static security scanners, a known-vulnerability audit of its libraries, and two secret scanners (gitleaks and trufflehog).",
        ]),
    ]
    return jsonify(sections=[{"title": t, "items": [i for i in items if i]} for t, items in sec])


@app.get("/api/logs")
def logs():
    try:
        with open(os.path.join(db.HOME, "logs", "periodize.log")) as f:
            return jsonify(lines=f.readlines()[-200:])
    except OSError:
        return jsonify(lines=[])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--host", default=os.environ.get("PERIODIZE_HOST", "127.0.0.1"), help="use 0.0.0.0 to reach the app from other devices")
    ap.add_argument("--port", type=int, default=int(os.environ.get("PERIODIZE_PORT", "8321")))
    ap.add_argument("--set-password", action="store_true", help="choose the app password needed from other devices, then exit")
    ap.add_argument("--allow-host", help="add a hostname that may be used to reach the app, then exit")
    ap.add_argument("--always-login", choices=("on", "off"), help="require the app password even from this computer (use behind a reverse proxy), then exit")
    a = ap.parse_args()
    if not (a.set_password or a.allow_host or a.always_login):
        updates.launch(sys.argv[1:])           # run the version chosen in the app, if one was
    if a.set_password:
        return set_password()
    if a.always_login:
        if a.always_login == "on" and not db.get("app_password"):
            sys.exit("Set a password first: python web.py --set-password")
        db.put("always_login", a.always_login == "on")
        return print("Password required from this computer too:", a.always_login)
    if a.allow_host:
        db.put("allowed_hosts", sorted(set((db.get("allowed_hosts") or []) + [a.allow_host.lower()])))
        return print("Allowed:", a.allow_host)
    setup(db.HOME)
    lock = open(os.path.join(db.HOME, "app.lock"), "w")  # noqa: SIM115 - held open for the life of the process
    try:
        _lock_file(lock)                                     # one copy only, or workouts would be sent twice
    except OSError:
        sys.exit("Periodize My Run is already running.")
    if a.host not in ("127.0.0.1", "localhost", "::1") and not db.get("app_password"):
        sys.exit("Refusing to listen on the network without an app password. Run: python web.py --set-password")
    key = vault.get("secret_key")          # the key that signs login cookies is kept encrypted, like the other secrets
    if not key:
        key = db.get("secret_key") or secrets.token_hex(32)
        vault.put("secret_key", key)
        db.put("secret_key", None)
    app.secret_key = key
    cert, pkey = os.path.join(db.HOME, "tls", "cert.pem"), os.path.join(db.HOME, "tls", "key.pem")
    tls = os.path.exists(cert) and os.path.exists(pkey)
    app.config.update(SESSION_COOKIE_SAMESITE="Strict", SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SECURE=tls,
                      PERMANENT_SESSION_LIFETIME=SESSION_LIFETIME, MAX_CONTENT_LENGTH=512 * 1024)
    threading.Thread(target=jobs.scheduler, daemon=True).start()
    from cheroot.wsgi import Server
    server = Server((a.host, a.port), app, numthreads=8, server_name="periodize-my-run")
    if tls:
        import ssl

        from cheroot.ssl.builtin import BuiltinSSLAdapter
        server.ssl_adapter = BuiltinSSLAdapter(cert, pkey)
        server.ssl_adapter.context.minimum_version = ssl.TLSVersion.TLSv1_2
        server.ssl_adapter.context.set_ciphers("ECDHE+AESGCM:ECDHE+CHACHA20")   # TLS 1.2 with forward secrecy and AEAD only: no CBC (LUCKY13)
    log.info("Periodize My Run started on %s://%s:%d", "https" if tls else "http", a.host, a.port)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()


if __name__ == "__main__":
    main()
