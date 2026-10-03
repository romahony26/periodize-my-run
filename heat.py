"""Heat: ease paces on hot, humid days. Off unless switched on, because it is the one feature that talks to a service other than
your watch's.

  - Weather comes from Open-Meteo (open-meteo.com: free, no account, no key). The only thing sent is your rough location, rounded to
    0.1 degrees (about 10 km), taken from the start of your latest outdoor run with GPS. Nothing else about you is sent.
  - The forecast is read for the hour you usually start running (the median start hour of your runs in the last four weeks).
  - How much to slow comes from the sum of temperature and dew point in degrees Fahrenheit, a widely used coaching table [C]. Its
    direction and size agree with marathon race data: performance falls progressively as it gets warmer and more humid, and slower
    runners lose proportionally more (Ely and colleagues, 2007) [R].
"""
import datetime as dt
import json
import statistics

import requests

import db
from log import log

API = "https://api.open-meteo.com/v1/forecast"
REFRESH_S = 3 * 3600
# (temperature + dew point in F, up to) -> per cent slower; the middle of each band of the usual table
TABLE = [(100, 0.0), (110, 0.25), (120, 0.75), (130, 1.5), (140, 2.5), (150, 3.75), (160, 5.25), (170, 7.0), (180, 9.0)]


def slowdown(temp_c, dew_c):
    """Per cent slower for this temperature and dew point (Celsius). None above the table: too hot for hard running."""
    if temp_c is None or dew_c is None:
        return 0.0
    s = (temp_c * 9 / 5 + 32) + (dew_c * 9 / 5 + 32)
    for top, pct in TABLE:
        if s <= top:
            return pct
    return None


def location():
    """(lat, lon) rounded to 0.1 degree, from the latest outdoor run with GPS; None if there is none."""
    for r in db.rows("SELECT detail FROM activities WHERE sport='running' AND detail IS NOT NULL ORDER BY date DESC LIMIT 30"):
        try:
            tr = (json.loads(r["detail"]) or {}).get("track") or []
        except ValueError:
            continue
        if tr and len(tr[0]) == 2 and -90 <= tr[0][0] <= 90 and -180 <= tr[0][1] <= 180:
            return round(tr[0][0], 1), round(tr[0][1], 1)
    return None


def run_hour(today=None):
    """The hour of day you usually start running: the median of the last four weeks, local time. 8 if unknown."""
    today = today or dt.date.today()
    hours = []
    for r in db.rows("SELECT start FROM activities WHERE sport='running' AND date>=?", ((today - dt.timedelta(days=28)).isoformat(),)):
        try:
            t = dt.datetime.fromisoformat(str(r["start"]).replace(" ", "T"))
        except ValueError:
            continue
        t = t.replace(tzinfo=dt.UTC) if t.tzinfo is None else t      # Garmin gives the start in UTC
        hours.append(t.astimezone().hour)
    return int(statistics.median(hours)) if hours else 8


def forecast(force=False, cached_only=False):
    """Hourly temperature and dew point for 16 days at the athlete's rough location, cached for three hours. With `cached_only`
    (the page, which refreshes every few seconds) it never waits on the weather service."""
    if not db.get("heat_adjust"):
        return None
    if cached_only:
        return db.get("heat_forecast") or None
    loc = location()
    if not loc:
        return None
    cached = db.get("heat_forecast") or {}
    now = dt.datetime.now()
    if not force and cached.get("loc") == list(loc) and cached.get("at") and (now - dt.datetime.fromisoformat(cached["at"])).total_seconds() < REFRESH_S:
        return cached
    try:
        r = requests.get(API, params={"latitude": loc[0], "longitude": loc[1], "hourly": "temperature_2m,dew_point_2m",
                                      "forecast_days": 16, "timezone": "auto"}, timeout=20, allow_redirects=False)
        h = r.json().get("hourly") if r.status_code == 200 else None
        times, temps, dews = (h or {}).get("time"), (h or {}).get("temperature_2m"), (h or {}).get("dew_point_2m")
        if not (isinstance(times, list) and isinstance(temps, list) and isinstance(dews, list) and len(times) == len(temps) == len(dews)):
            raise ValueError("unexpected reply")
    except (requests.RequestException, ValueError) as e:
        log.warning("Weather could not be read (%s); no heat adjustment this time", type(e).__name__)
        return cached or None
    out = {"loc": list(loc), "at": now.isoformat(timespec="seconds"), "hours": {t: [a, b] for t, a, b in zip(times, temps, dews, strict=True)}}
    db.put("heat_forecast", out)
    return out


def at(day, hour, cached_only=False):
    """{temp, dew, pct} for a date and hour, from the forecast; None outside it."""
    f = forecast(cached_only=cached_only)
    if not f:
        return None
    v = f["hours"].get(f"{day.isoformat()}T{hour:02d}:00")
    if not v or v[0] is None or v[1] is None:
        return None
    pct = slowdown(v[0], v[1])
    return {"temp": round(v[0]), "dew": round(v[1]), "pct": pct, "hour": hour}
