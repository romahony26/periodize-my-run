"""Run Periodize My Run's own planner, week by week, on real athletes' histories and compare it with what they did.

Not part of the running app. Needs pyarrow and numpy and the public dataset (see validate_public.py):

  python tools/validate_engine.py /path/to/run_ww_2019_d.parquet [athletes] [--long]

--long gives the planner every day the file holds before the build (17 to 25 weeks) as the app's profile would use it, instead of eight weeks.

For each autumn-Major marathoner it builds the planner's state from the eight weeks before an 18-week build (weekly miles, longest run,
threshold from the best training run, running days from their own habit), plans all 18 weeks with the athlete's goal as the marathon, and
reports safety properties of the plans, how they compare with what the athletes actually ran, and how a rise above the plan went with
results. The last is observational and biased towards people who stayed healthy enough to race.
"""
import datetime as dt
import os
import random
import sys
import tempfile

import numpy as np

os.environ.setdefault("PERIODIZE_HOME", tempfile.mkdtemp())
os.environ.setdefault("PERIODIZE_KEY_FILE", os.path.join(tempfile.mkdtemp(), "vault.key"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db  # noqa: E402
import engine  # noqa: E402
import equiv  # noqa: E402
import profile  # noqa: E402

KM = 1 / 1.609344
WEEKS = 18
DATES = {"BERLIN": "2019-09-29", "CHICAGO": "2019-10-13", "NEW YORK": "2019-11-03"}


def athletes(path):
    import pyarrow.parquet as pq
    t = pq.read_table(path, columns=["datetime", "athlete", "distance", "duration", "major"])
    ath = t["athlete"].to_numpy()
    day = (t["datetime"].to_numpy().astype("datetime64[D]") - np.datetime64("2019-01-01")).astype(int)
    dist = np.zeros((int(ath.max()) + 1, int(day.max()) + 1), np.float32)
    dur = np.zeros_like(dist)
    dist[ath, day], dur[ath, day] = t["distance"].to_numpy(), t["duration"].to_numpy()
    majors, seen = {}, set()
    for a, m in zip(ath, t["major"].to_numpy(zero_copy_only=False), strict=True):
        if int(a) not in seen:
            seen.add(int(a))
            majors[int(a)] = m or ""
    ids = list(majors)
    random.Random(7).shuffle(ids)  # noqa: S311 - a repeatable shuffle, not security
    return dist, dur, majors, ids


def state_for(dist, dur, a, start, mon0):
    """The planner's state at the Monday 18 weeks before the race, from the athlete's own eight earlier weeks."""
    week = lambda s: dist[a, s: s + 7]
    hist = [float(week(start - 7 * k).sum()) for k in range(8, 0, -1)]
    best = 0.0
    for i in range(start - 56, start):
        d, t = float(dist[a, i]), float(dur[a, i])
        if 5 <= d <= 25 and t > 0 and 2.6 <= t / d <= 9:
            best = max(best, equiv.index(d * 1000, t * 60))
    if sum(hist) < 64 or best < 30:
        return None
    weeks = [{"start": mon0 - dt.timedelta(weeks=8 - i), "mi": h * KM, "runs": int((week(start - 7 * (8 - i)) >= 3).sum()),
              "long": float(week(start - 7 * (8 - i)).max()) * KM, "fast_mi": 3, "t_min": 0} for i, h in enumerate(hist)]
    st = {"monday": mon0, "tp": equiv.threshold_speed(best), "flags": [], "endurance": 0.6, "prev_t_min": 0, "prev_mp_mid": 0, "prev_mp_long": 0,
          "last_mp_long": None, "longest_30d": float(dist[a, start - 30: start].max()) * KM, "longest_10d": float(dist[a, start - 10: start].max()) * KM, "weeks": weeks}
    return st, hist


def whole_history(dist, a, start):
    """The same profile fields the app derives from the whole activity list, from every day the file has before the build."""
    runs = [{"date": (dt.date(2019, 1, 1) + dt.timedelta(days=i)).isoformat(), "dist_m": float(dist[a, i]) * 1000}
            for i in range(start) if dist[a, i] > 0]
    wk = profile.weekly_miles(runs)
    excused = [dt.date.fromisoformat(r["date"]) for r in runs if r["dist_m"] >= 20 * profile.MI]
    recent = list(wk.values())[-8:]
    return {"recent8": sum(recent) / max(len(recent), 1), "best8_3y": profile.best_block(wk, dt.date.min), "hrmax_observed": 190,
            "proven8_3y": profile.proven_block(wk, dt.date.min, excused, []), "proven8_all": profile.proven_block(wk, dt.date.min, excused, []),
            "weeks_unbroken": 99, "weeks": len(wk)}


def build(st, hist, races, c0, prof=None):
    mean = float(np.mean(hist)) * KM
    prof = prof or {"best8_3y": max(mean, max(np.mean(hist[i:i + 4]) for i in range(5)) * KM), "recent8": mean, "hrmax_observed": 190}
    c = dict(c0, run_days=int(min(6, max(3, round(np.mean([w["runs"] for w in st["weeks"]]))))))
    L = profile.limits(prof, c, 26.219)
    plans = []
    for _ in range(WEEKS):
        pl = engine.plan(st, c, L, races)
        plans.append(pl)
        st = engine.project(st, pl)
    return plans


def main(path, limit=600, long_history=False):
    dist, dur, majors, ids = athletes(path)
    c0 = dict(db.DEFAULTS, aero_test=True, aero_test_weeks=4, aero_format="short", aero_runs=True)
    rows = []
    for a in ids:
        for entry in (x.strip() for x in majors[a].split(",")):
            name = entry.rsplit(" ", 1)[0]
            if entry.endswith("2019") and name in DATES:
                r0 = int((np.datetime64(DATES[name]) - np.datetime64("2019-01-01")).astype(int))
                r = max(range(r0 - 1, min(r0 + 2, dist.shape[1])), key=lambda i: dist[a, i])
                km, mins = float(dist[a, r]), float(dur[a, r])
                start = r - 7 * WEEKS
                if not (41 <= km <= 44.5 and 2.6 <= mins / km <= 10) or start < 56:
                    continue
                mon0 = dt.date(2019, 1, 1) + dt.timedelta(days=start)
                got = state_for(dist, dur, a, start, mon0)
                actual = [float(dist[a, start + 7 * k: start + 7 * k + 7].sum()) * KM for k in range(WEEKS)]
                if not got or sum(actual) < 100:
                    continue
                st, hist = got
                races = [{"name": "M", "date": mon0 + dt.timedelta(days=7 * WEEKS - 1), "miles": 26.219, "priority": "A", "goal_time": None}]
                plans = build(st, hist, races, c0, whole_history(dist, a, start) if long_history else None)
                if long_history and (dist[a, :start] > 0).sum() < 60:
                    continue
                rows.append({"hist": [h * KM for h in hist], "actual": actual, "plan": [p["total"] for p in plans], "mode": [p["mode"] for p in plans],
                             "mp_long": sum(1 for p in plans if p["done"]["mp_long"]), "mins": mins})
                break
        if len(rows) >= limit:
            break
    report(rows)


def report(rows):
    n = len(rows)
    spikes = []
    for r in rows:
        p = r["hist"][-3:] + r["plan"]
        for i in range(3, len(p) - 1):
            if max(p[i - 3: i]) >= 8 and r["mode"][i - 3] == "build":
                spikes.append(p[i] / max(p[i - 3: i]) - 1)
    s = np.array(spikes)
    print(f"{n} athletes, 18 weeks each, planned by the app's own engine")
    print(f"build weeks above the best of the last three by >10%: {100 * np.mean(s > .10):.1f}%, >20%: {100 * np.mean(s > .20):.1f}%, >30%: {100 * np.mean(s > .30):.1f}%")
    print(f"planned peak week median {np.median([max(r['plan']) for r in rows]):.0f} mi; the athletes' actual {np.median([max(r['actual']) for r in rows]):.0f} mi")
    print(f"marathon-pace long runs per athlete: {np.mean([r['mp_long'] for r in rows]):.1f}")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 600, "--long" in sys.argv)
