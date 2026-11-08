"""Jet lag, read from the time zone Garmin records with every night's sleep and every day's summary. Nothing is entered by hand.

The watch stores each night's sleep start and each day's start twice, once in GMT and once in local time, so the difference is the
time zone the athlete was in. A change of two hours or more is a flight, not the clocks changing (that is one hour). From it the
body clock is followed: it moves towards local time by about an hour a day, which is the review finding that jet-lag symptoms last
about a day for each time zone crossed (Lee and Galvez, 2012). It does not move at once, so a three-day trip is not a full re-set at
home either: coming back from five zones after four days away leaves about four hours to make up, not five and not none.

How far the body clock is from local time is the jet lag. It is read as warning points in the daily readiness, so the existing
rules ease the fast running, and turn it into an easy run when other signs agree. No study says how much slower to run, so the
points are this project's choice (see PRINCIPLES.md, 54c); the research supports only the length of the effect, that eastward travel
is the harder direction, and that the evidence is thin (Lee and Galvez, 2012; Fowler and colleagues, 2017; Janse van Rensburg and
colleagues, 2021).

Where the record holds no time-zone data (a watch that does not give it, or days not yet read) nothing changes.
"""
import datetime as dt
import json
import zlib

import db

RATE = 1.0               # hours of shift a day: jet-lag symptoms last about a day per time zone crossed (Lee and Galvez, 2012)
MIN_HOURS = 2.0          # jet lag is travel across at least two time zones; one hour is the clocks changing
WINDOW = 28              # days of history followed: long enough for the body clock to have settled before the latest trip
STALE = 3                # days: if the newest time-zone reading is older than this, today's zone is not known
TWO_POINTS = {"east": 4.0, "west": 6.0}      # hours out of step at which the warning counts double; eastward is the harder direction


def _quarter(hours):
    return round(hours * 4) / 4


def _offset(kind, body):
    """Hours local time is ahead of GMT, from one stored Garmin record, or None."""
    try:
        j = json.loads(zlib.decompress(body))
        if kind == "sleep":
            s = j.get("dailySleepDTO") or {}
            g, loc = s.get("sleepStartTimestampGMT"), s.get("sleepStartTimestampLocal")
            if not (isinstance(g, (int, float)) and isinstance(loc, (int, float)) and g > 0 and loc > 0):
                return None
            hours = (loc - g) / 3_600_000
        else:
            g, loc = j.get("wellnessStartTimeGmt"), j.get("wellnessStartTimeLocal")
            if not (g and loc):
                return None
            hours = (dt.datetime.fromisoformat(loc) - dt.datetime.fromisoformat(g)).total_seconds() / 3600
    except (ValueError, TypeError, AttributeError, zlib.error):
        return None
    return _quarter(hours) if -12 <= hours <= 14 else None


def zones(today, window=WINDOW):
    """{date: hours ahead of GMT} for the last `window` days. A night's sleep is preferred, since that is where the athlete slept."""
    rows = db.rows("SELECT date,kind,body FROM garmin_raw WHERE kind IN ('sleep','stats') AND body IS NOT NULL AND date>=? AND date<=? ORDER BY date",
                   ((today - dt.timedelta(days=window)).isoformat(), today.isoformat()))
    out = {}
    for r in rows:
        o = _offset(r["kind"], r["body"])
        if o is not None and (r["date"] not in out or r["kind"] == "sleep"):
            out[r["date"]] = o
    return out


def follow(by_day, today):
    """Follow the body clock day by day. Returns {lag, local, shift: (date, hours) of the latest flight} or None with too little to go on.

    `lag` is local time minus the body clock, in hours: positive after travelling east (the body clock is behind local time and has to
    be moved forward), negative after travelling west. The body clock starts on the first day's zone, taken as settled.
    """
    if len(by_day) < 3 or (today - dt.date.fromisoformat(max(by_day))).days > STALE:
        return None
    day = dt.date.fromisoformat(min(by_day))
    body = local = by_day[min(by_day)]
    shift, lag = None, 0.0
    while day <= today:
        new = by_day.get(day.isoformat(), local)
        if abs(new - local) >= MIN_HOURS:
            shift = (day.isoformat(), new - local)
        local = new
        lag = local - body
        body += max(-RATE, min(RATE, lag))            # moves towards local time by up to an hour a day
        day += dt.timedelta(days=1)
    return {"lag": lag, "local": local, "shift": shift}


def _when(iso):
    d = dt.date.fromisoformat(iso)
    return f"{d.strftime('%a')} {d.day} {d.strftime('%b')}"


def state(today):
    """Today's jet lag as warning points and a sentence, or None when there is none (or no time-zone record to read)."""
    f = follow(zones(today), today)
    if not f or abs(f["lag"]) < MIN_HOURS:
        return None
    lag, east = f["lag"], f["lag"] > 0
    way = "east" if east else "west"
    hours = abs(lag)
    points = 2 if hours >= TWO_POINTS[way] else 1
    moved = ""
    if f["shift"]:
        moved = f"you changed time zone by {abs(f['shift'][1]):g} hours {'east' if f['shift'][1] > 0 else 'west'} on {_when(f['shift'][0])}, and "
    reason = (f"{moved}your body clock is still about {hours:g} hours {'behind' if east else 'ahead of'} local time (jet lag fades by about an hour a day"
              f"{', and takes longer after travelling east' if east else ''})")
    return {"points": points, "lag_h": lag, "direction": way, "hours": hours, "days_left": int(-(-hours // RATE)), "reason": reason}
