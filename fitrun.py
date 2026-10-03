"""Parse one activity FIT file into a compact summary. Pure Python + fitdecode.

Everything is SI (metres, seconds, m/s). Conversion to miles happens only
when the report is written.
"""
import math
import os

import fitdecode

MAX_GAP = 60.0          # a longer gap between records is a pause
SMOOTH_S = 10.0         # speed is measured over this many seconds
BIN = 0.1               # speed histogram bin, m/s
NBINS = 90              # up to 9 m/s
HR_LO, HR_STEP, HR_NBINS = 80, 5, 28   # heart rate histogram: 5-bpm bins from 80 to 220
EFFORT_DUR = [180, 360, 720, 1200, 1800, 3600]
EFFORT_DIST = [5000, 10000, 16093, 21097, 42195]
STOP_TYPES = ("stop", "stop_all", "stop_disable", "stop_disable_all")


def _best_distance(tt, d, dur):
    """Largest distance covered in any window of `dur` seconds of moving time."""
    if tt[-1] - tt[0] < dur:
        return None
    best, j, n = 0.0, 0, len(tt)
    for i in range(n):
        while j < n and tt[j] - tt[i] < dur:
            j += 1
        if j >= n:
            break
        dist = d[j] - d[i]
        seg = tt[j] - tt[j - 1]
        if seg > 0:
            dist -= (d[j] - d[j - 1]) * (tt[j] - tt[i] - dur) / seg
        best = max(best, dist)
    return best or None


def _best_time(tt, d, target):
    """Shortest moving time covering `target` metres."""
    if d[-1] - d[0] < target:
        return None
    best, j, n = None, 0, len(d)
    for i in range(n):
        j = max(j, i)
        while j < n and d[j] - d[i] < target:
            j += 1
        if j >= n:
            break
        t = tt[j] - tt[i]
        seg = d[j] - d[j - 1]
        if seg > 0:
            t -= (tt[j] - tt[j - 1]) * (d[j] - d[i] - target) / seg
        if t > 0 and (best is None or t < best):
            best = t
    return best


def effort(g):
    """Energy cost of running on gradient g relative to the flat (Minetti et al. 2002). 1.0 on the flat, more uphill, less on gentle downhill."""
    g = max(min(g, 0.30), -0.30)
    return (155.4 * g ** 5 - 30.4 * g ** 4 - 43.3 * g ** 3 + 46.3 * g ** 2 + 19.5 * g + 3.6) / 3.6


def _grades(d, al, window=80.0):
    """Gradient at each record from altitude smoothed over `window` metres, and whether the altitude trace can be trusted.

    A barometer that is failing jitters: raw climb is several times the climb left after smoothing. Those runs are flagged and not adjusted.
    """
    n = len(d)
    grade = [0.0] * n
    if sum(1 for a in al if a is not None) < 0.8 * n:
        return grade, False, 0.0
    last = next(a for a in al if a is not None)
    alt = []
    for a in al:
        last = a if a is not None else last
        alt.append(last)
    j = 0
    for i in range(n):
        while d[i] - d[j] > window and j < i:
            j += 1
        k = max(j - 1, 0)
        if d[i] - d[k] >= window * 0.5:
            grade[i] = (alt[i] - alt[k]) / (d[i] - d[k])
    raw = sum(max(alt[i] - alt[i - 1], 0) for i in range(1, n))
    smooth, mark = 0.0, 0
    for i in range(1, n):       # climb measured in steps of at least one window
        if d[i] - d[mark] >= window:
            smooth += max(alt[i] - alt[mark], 0)
            mark = i
    km = max((d[-1] - d[0]) / 1000, 0.1)
    ok = not (raw / km > 12 and raw > 3 * max(smooth, 1))
    return grade, ok, smooth


def parse(path):
    """Return a summary dict, or a dict with an "error" key."""
    try:
        return _parse(path)
    except Exception as e:  # one bad file must not stop the weekly run
        return {"file": os.path.basename(path), "error": repr(e)[:200]}


def _parse(path):
    rec, stops, sess, laps = [], [], {}, []
    device, first, last = None, None, None
    pos = []
    with fitdecode.FitReader(path, check_crc=fitdecode.CrcCheck.DISABLED) as fr:
        for fm in fr:
            if not isinstance(fm, fitdecode.FitDataMessage):
                continue
            if fm.name == "record":
                t = fm.get_value("timestamp", fallback=None)
                if t is None or not hasattr(t, "timestamp"):
                    continue
                alt = fm.get_value("enhanced_altitude", fallback=None)
                if alt is None:
                    alt = fm.get_value("altitude", fallback=None)
                rec.append((t.timestamp(), fm.get_value("distance", fallback=None), fm.get_value("heart_rate", fallback=None), alt))
                la, lo = fm.get_value("position_lat", fallback=None), fm.get_value("position_long", fallback=None)
                if la is not None and lo is not None and alt is not None:
                    first = first or (la, lo, alt)
                    last = (la, lo, alt)
                if la is not None and lo is not None:
                    pos.append((t.timestamp(), la, lo))
            elif fm.name == "file_id":
                device = f"{fm.get_value('garmin_product', fallback='')}-{fm.get_value('serial_number', fallback='')}"
            elif fm.name == "session" and not sess:
                for k in ("sport", "sub_sport", "start_time", "total_distance", "total_timer_time", "avg_heart_rate", "total_ascent"):
                    v = fm.get_value(k, fallback=None)
                    if v is not None:
                        sess[k] = v.isoformat() if hasattr(v, "isoformat") else (str(v) if k in ("sport", "sub_sport") else v)
            elif fm.name == "lap" and len(laps) < 80:
                ld, lt, lh = (fm.get_value(k, fallback=None) for k in ("total_distance", "total_timer_time", "avg_heart_rate"))
                if ld and lt:
                    laps.append([round(ld, 1), round(lt, 1), lh])
            elif fm.name == "event":
                if str(fm.get_value("event", fallback="")) == "timer" and str(fm.get_value("event_type", fallback="")) in STOP_TYPES:
                    t = fm.get_value("timestamp", fallback=None)
                    if hasattr(t, "timestamp"):
                        stops.append(t.timestamp())

    loop_err = None
    if first and last:      # on a run that ends where it began, a healthy altitude sensor reads the same at both ends
        k = math.pi / 2 ** 31
        dy = (last[0] - first[0]) * k * 6371000
        dx = (last[1] - first[1]) * k * 6371000 * math.cos(first[0] * k)
        if math.hypot(dx, dy) < 150:
            loop_err = round(abs(last[2] - first[2]), 1)
    out = {"file": os.path.basename(path), "device": device, "loop_alt_err": loop_err, "laps": laps, "sport": sess.get("sport"), "sub_sport": sess.get("sub_sport"),
           "start": sess.get("start_time"), "ascent_m": sess.get("total_ascent")}
    rec = [r for r in rec if r[1] is not None]
    if len(rec) < 30:
        out["dist_m"] = sess.get("total_distance") or 0.0
        out["timer_s"] = sess.get("total_timer_time") or 0.0
        out["avg_hr"] = sess.get("avg_heart_rate")
        return out
    rec.sort(key=lambda r: r[0])

    # moving-time axis that skips pauses, and a monotonic distance
    stops.sort()
    tt, d, hr, al = [0.0], [rec[0][1]], [rec[0][2]], [rec[0][3]]
    si = 0
    for k in range(1, len(rec)):
        gap = rec[k][0] - rec[k - 1][0]
        while si < len(stops) and stops[si] <= rec[k - 1][0]:
            si += 1
        stopped = si < len(stops) and stops[si] <= rec[k][0] and gap > 3
        step = gap if (0 < gap <= MAX_GAP and not stopped) else 0.0
        tt.append(tt[-1] + step)
        d.append(max(d[-1], rec[k][1]))
        hr.append(rec[k][2])
        al.append(rec[k][3])
    n = len(tt)
    grade, gap_ok, climb = _grades(d, al)

    # histograms on speed smoothed over SMOOTH_S seconds
    sec_by_speed, m_by_speed = [0.0] * NBINS, [0.0] * NBINS
    hr_sec, hr_m, hr_gap = [0.0] * HR_NBINS, [0.0] * HR_NBINS, [0.0] * HR_NBINS
    gap_m = 0.0
    hr_sum = hr_w = 0.0
    hr_peak = 0
    j = 0
    for i in range(1, n):
        dt = tt[i] - tt[i - 1]
        if dt <= 0:
            continue
        while tt[i] - tt[j] > SMOOTH_S and j < i - 1:
            j += 1
        span = tt[i] - tt[j]
        v = (d[i] - d[j]) / span if span > 0 else 0.0
        if v < 0 or v > 7.5:
            continue
        b = min(int(v / BIN), NBINS - 1)
        sec_by_speed[b] += dt
        m_by_speed[b] += d[i] - d[i - 1]
        flat_m = (d[i] - d[i - 1]) * (effort(grade[i]) if gap_ok else 1.0)     # the flat distance this stretch was worth
        gap_m += flat_m
        h = hr[i]
        if h:
            hr_sum += h * dt
            hr_w += dt
            hr_peak = max(hr_peak, h)
            if v >= 1.8 and HR_LO <= h < HR_LO + HR_STEP * HR_NBINS:
                bi = int((h - HR_LO) // HR_STEP)
                hr_sec[bi] += dt
                hr_m[bi] += d[i] - d[i - 1]
                hr_gap[bi] += flat_m

    out.update({
        "dist_m": d[-1] - d[0], "timer_s": tt[-1],
        "avg_hr": round(hr_sum / hr_w, 1) if hr_w else sess.get("avg_heart_rate"), "max_hr": hr_peak or None,
        "sec_by_speed": [round(x, 1) for x in sec_by_speed], "m_by_speed": [round(x, 1) for x in m_by_speed],
        "hr_sec": [round(x, 1) for x in hr_sec], "hr_m": [round(x, 1) for x in hr_m], "hr_gap": [round(x, 1) for x in hr_gap],
        "gap_ok": gap_ok, "gap_ratio": round(gap_m / (d[-1] - d[0]), 4) if gap_ok and d[-1] > d[0] else None, "climb_m": round(climb) if gap_ok else None,
        "best_dur": {str(s): _best_distance(tt, d, s) for s in EFFORT_DUR},
        "best_dist": {str(m): _best_time(tt, d, m) for m in EFFORT_DIST},
    })
    # a light series for charts (about every 30 s of moving time) and the route outline (up to 300 points)
    series, nxt, k0 = [], 0.0, 0
    for i in range(1, n):
        if tt[i] >= nxt + 30:
            span = tt[i] - tt[k0]
            hs = [h for h in hr[k0:i + 1] if h]
            series.append([round(tt[i]), round((d[i] - d[k0]) / span, 2) if span > 0 else 0, round(sum(hs) / len(hs)) if hs else None])
            nxt, k0 = tt[i], i
    step = max(len(series) // 400, 1)
    out["series"] = series[::step]
    k = math.pi / 2 ** 31 * 180 / math.pi
    stride = max(len(pos) // 300, 1)
    out["track"] = [[round(p[1] * k, 5), round(p[2] * k, 5)] for p in pos[::stride]]
    # GPS glitch guard: a 3-minute effort faster than 2:35/km is not real for this use
    b3 = out["best_dur"].get("180")
    out["glitch"] = bool(b3 and b3 / 180 > 6.45)
    return out
