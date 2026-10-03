"""Heat: ease paces on hot, humid days. Off unless switched on, because it is the one feature that talks to a service other than
your watch's.

  - Weather comes from Open-Meteo (open-meteo.com: free, no account, no key). The only thing sent is your rough location, rounded to
    0.1 degrees (about 10 km), taken from the start of your latest outdoor run with GPS. Nothing else about you is sent.
  - The forecast is read for the hour you usually start running (the median start hour of your runs in the last four weeks).
  - How much to slow comes from race data: across 1,258 endurance races, performance was best at a wet-bulb globe temperature
    (WBGT) of 7.5 to 15 C and fell by 0.3 to 0.4% for every degree outside that range (Mantzios and colleagues, 2022) [R]. Marathon
    data agree: times fall progressively as it gets warmer, and slower runners lose more (Ely and colleagues, 2007) [R].
  - WBGT is estimated for shade from temperature and humidity (wet-bulb temperature by Stull's 2011 formula). It is an estimate:
    full sun on a still day is harder than the figure says.
  - Every outdoor run is also given the weather it was run in (temperature, dew point, wind and rain), read once from the same
    service for the run's rounded start location and hour. Fitness is then judged on what the run was worth in neutral weather,
    so a hot or very cold spell is not read as lost fitness. Wind and rain are recorded and shown but do not change any figure:
    in race data they had no effect of their own once temperature was allowed for (El Helou and colleagues, 2012; Vihma, 2010).
"""
import datetime as dt
import json
import math
import statistics

import requests

import db
from log import log

API = "https://api.open-meteo.com/v1/forecast"
REFRESH_S = 3 * 3600
ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"
BEST_WBGT = (7.5, 15.0)      # the range in which endurance running performance peaks (Mantzios and colleagues, 2022)
PCT_PER_DEGREE = 0.35        # per cent slower for each degree of WBGT outside it: the middle of their 0.3 to 0.4
TOO_HOT_WBGT = 28.0          # above this, no hard running: the level at which race organisers are advised to cancel or modify events [C]
TRACK_YEARS = 3
MAX_PCT = 12.0
MAX_COLD_PCT = 1.5


def wbgt(temp_c, dew_c):
    """Wet-bulb globe temperature in C for shade, from air temperature and dew point: 0.7 x wet-bulb + 0.3 x air temperature.

    The wet-bulb temperature comes from Stull's (2011) formula. Sun is not included, so a still, sunny day is harder than this says.
    """
    rh = 100 * math.exp(17.625 * dew_c / (243.04 + dew_c)) / math.exp(17.625 * temp_c / (243.04 + temp_c))
    rh = min(max(rh, 5.0), 99.0)
    wet = (temp_c * math.atan(0.151977 * (rh + 8.313659) ** 0.5) + math.atan(temp_c + rh) - math.atan(rh - 1.676331)
           + 0.00391838 * rh ** 1.5 * math.atan(0.023101 * rh) - 4.686035)
    return 0.7 * wet + 0.3 * temp_c


def slowdown(temp_c, dew_c):
    """Per cent slower in the heat for this temperature and dew point (Celsius). None when it is too hot for hard running."""
    if temp_c is None or dew_c is None:
        return 0.0
    w = wbgt(temp_c, dew_c)
    if w >= TOO_HOT_WBGT:
        return None
    return round(min(max(w - BEST_WBGT[1], 0.0) * PCT_PER_DEGREE, MAX_PCT), 1)


def worth(temp_c, dew_c):
    """Per cent that the weather took off a run's pace, hot or cold: what to add back to judge the run in neutral weather."""
    if temp_c is None or dew_c is None:
        return 0.0
    w = wbgt(temp_c, dew_c)
    cold = min(max(BEST_WBGT[0] - w, 0.0) * PCT_PER_DEGREE, MAX_COLD_PCT)      # the evidence for cold is weaker, so it counts for less
    return round(max(min(max(w - BEST_WBGT[1], 0.0) * PCT_PER_DEGREE, MAX_PCT), cold), 1)


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


def _hours(url, loc, **params):
    """{"YYYY-MM-DDTHH:00": [temp, dew, wind km/h, rain mm]} in GMT for one rounded location. {} if the service does not answer as expected."""
    try:
        r = requests.get(url, params={"latitude": loc[0], "longitude": loc[1], "hourly": "temperature_2m,dew_point_2m,wind_speed_10m,precipitation",
                                      "timezone": "GMT", **params}, timeout=30, allow_redirects=False)
        h = (r.json().get("hourly") if r.status_code == 200 else None) or {}
        cols = [h.get(k) for k in ("time", "temperature_2m", "dew_point_2m", "wind_speed_10m", "precipitation")]
        if not all(isinstance(x, list) and len(x) == len(cols[0]) for x in cols):
            raise ValueError("unexpected reply")
    except (requests.RequestException, ValueError, TypeError) as e:
        log.warning("Past weather could not be read (%s)", type(e).__name__)
        return {}
    return {t: [a, b, c, d] for t, a, b, c, d in zip(*cols, strict=True)}


def track(progress=lambda m: None, today=None):
    """Give each outdoor run of the last three years the weather it was run in. Only when heat adjustment is on. Returns how many were filled."""
    if not db.get("heat_adjust"):
        return 0
    today = today or dt.date.today()
    home = location()
    todo = {}
    for r in db.rows("SELECT id,start,date,timer_s,name,detail FROM activities WHERE sport='running' AND weather IS NULL AND start IS NOT NULL AND date>=? ORDER BY date",
                     ((today - dt.timedelta(days=365 * TRACK_YEARS)).isoformat(),)):
        loc, indoor = home, "treadmill" in (r["name"] or "").lower()
        try:
            d = json.loads(r["detail"]) if r["detail"] else {}
            tr = d.get("track") or []
            indoor = indoor or (d.get("sub_sport") or "") in ("treadmill", "indoor_running")
            if tr and len(tr[0]) == 2 and -90 <= tr[0][0] <= 90 and -180 <= tr[0][1] <= 180:
                loc = (round(tr[0][0], 1), round(tr[0][1], 1))
            t0 = dt.datetime.fromisoformat(str(r["start"]).replace(" ", "T"))
        except ValueError:
            continue
        if indoor or not loc:
            if indoor:
                db.run("UPDATE activities SET weather='{}' WHERE id=?", (r["id"],))
            continue
        t0 = t0.replace(tzinfo=None) if t0.tzinfo is None else t0.astimezone(dt.UTC).replace(tzinfo=None)      # stored in GMT
        todo.setdefault(tuple(loc), []).append((r["id"], t0, r["timer_s"] or 0))
    done = 0
    for n, (loc, runs) in enumerate(todo.items(), 1):
        progress(f"Weather for past runs: place {n} of {len(todo)}")
        recent = [x for x in runs if (today - x[1].date()).days <= 85]
        older = [x for x in runs if (today - x[1].date()).days > 85]
        hours = {}
        if recent:
            hours.update(_hours(API, loc, past_days=92, forecast_days=1))
        if older:
            hours.update(_hours(ARCHIVE, loc, start_date=min(x[1] for x in older).date().isoformat(), end_date=max(x[1] for x in older).date().isoformat()))
        for rid, t0, secs in runs:
            span = [hours.get((t0.replace(minute=0, second=0, microsecond=0) + dt.timedelta(hours=k)).strftime("%Y-%m-%dT%H:00")) for k in range(int((t0.minute * 60 + secs) // 3600) + 1)]
            span = [x for x in span if x and x[0] is not None and x[1] is not None]
            if not span:
                if (today - t0.date()).days > 10:        # the service has nothing for it and never will: do not ask again
                    db.run("UPDATE activities SET weather='{}' WHERE id=?", (rid,))
                continue
            t, d = sum(x[0] for x in span) / len(span), sum(x[1] for x in span) / len(span)
            w = {"t": round(t, 1), "d": round(d, 1), "wind": round(max((x[2] or 0) for x in span)), "rain": round(sum((x[3] or 0) for x in span), 1),
                 "wbgt": round(wbgt(t, d), 1), "pct": worth(t, d)}
            db.run("UPDATE activities SET weather=? WHERE id=?", (json.dumps(w), rid))
            done += 1
    if done:
        log.info("Weather stored for %d runs", done)
    return done


def of(row):
    """The stored weather of an activity row, or None."""
    try:
        w = json.loads(row["weather"]) if row["weather"] else None
    except (ValueError, KeyError, IndexError):
        return None
    return w or None


def on_day(date, activity_id=None):
    """The weather of a run on a date (the named activity, else the day's longest outdoor run). None when weather is off or unknown."""
    if not db.get("heat_adjust"):
        return None
    rows = db.rows("SELECT weather FROM activities WHERE id=?", (activity_id,)) if activity_id else []
    rows = rows or db.rows("SELECT weather FROM activities WHERE sport='running' AND date=? AND weather IS NOT NULL AND weather!='{}' ORDER BY dist_m DESC LIMIT 1", (date,))
    return of(rows[0]) if rows else None


def words(w, units="mi"):
    """One line for a run's weather."""
    if not w:
        return ""
    wind = f"{w['wind'] / 1.609344:.0f} mph" if units == "mi" else f"{w['wind']} km/h"
    out = f"{w['t']:.0f}°C, dew point {w['d']:.0f}°C, wind up to {wind}" + (f", {w['rain']:g} mm of rain" if w.get("rain") else ", dry")
    return out + (f". Worth about {w['pct']:g}% on your pace." if w.get("pct") else ".")
