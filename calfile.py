"""The plan as a calendar file, for Apple Calendar, Outlook, Google Calendar or any other calendar app, imported by hand.

Nothing is sent anywhere: the file is made when you download it.
"""
import datetime as dt
import json

import db
import engine

TYPES = {"Key": "Session", "Long": "Long run", "Race": "Race", "Easy": "Easy run"}


def event(p, tp, c):
    """The event for one planned day, or None for a rest day. All-day, so it does not claim a time you did not choose."""
    if not p["steps"] or p["type"] == "Rest":
        return None
    day = dict(p, steps=json.loads(p["steps"]))
    adj = json.loads(p["adjust"]) if p["adjust"] else {}
    text = engine.describe(day, tp, c["units"], adj.get("slow", 0.0)) if tp else ""
    extra = [x for x in (p["note"], f"Also: {p['strength']}" if p["strength"] else "") if x]
    return {"summary": f"{TYPES.get(p['type'], 'Run')}: {p['label']} {engine.dist(p['miles'], c['units'])}", "description": "\n".join([text] + extra)}


def ics(c, days=60):
    """The plan as an iCalendar file."""
    today = dt.date.today()
    tps = {r["monday"]: r["tp"] for r in db.rows("SELECT monday,tp FROM weeks")}
    esc = lambda s: str(s).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")
    out = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Periodize//Training plan//EN", "CALSCALE:GREGORIAN", "X-WR-CALNAME:Periodize training"]
    for p in db.rows("SELECT * FROM plan WHERE date>=? AND date<=? ORDER BY date", (today.isoformat(), (today + dt.timedelta(days=days)).isoformat())):
        d = dt.date.fromisoformat(p["date"])
        ev = event(p, tps.get((d - dt.timedelta(days=d.weekday())).isoformat()), c)
        if ev:
            out += ["BEGIN:VEVENT", f"UID:periodize-{p['date']}@periodize.local", f"DTSTAMP:{dt.datetime.now(dt.UTC):%Y%m%dT%H%M%SZ}",
                    f"DTSTART;VALUE=DATE:{d:%Y%m%d}", f"DTEND;VALUE=DATE:{d + dt.timedelta(days=1):%Y%m%d}", f"SUMMARY:{esc(ev['summary'])}",
                    f"DESCRIPTION:{esc(ev['description'])}", "TRANSP:TRANSPARENT", "END:VEVENT"]
    return "\r\n".join(out + ["END:VCALENDAR"]) + "\r\n"
