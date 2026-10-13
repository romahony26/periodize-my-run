"""Check Periodize My Run's marathon assumptions against a large public set of real marathon results and their training.

Not part of the running app: it needs pyarrow and numpy, and the dataset, which is CC BY 4.0:
  Afonseca LA, Watanabe RN, Duarte M (2022). PeerJ 10:e13192. Data: https://doi.org/10.6084/m9.figshare.16620238
  (file run_ww_2019_d.parquet, daily distance and duration for 36,412 athletes, with the World Marathon Majors each ran).

  python tools/validate_public.py /path/to/run_ww_2019_d.parquet

A race is a marathon-length day within a day of a 2019 Major's date. Only the autumn Majors (Berlin, Chicago, New York) have 16 weeks
of history inside the 2019 file. Everything is observational: it shows association between training and results across runners, not
that a plan causes a result. Findings are written up in PRINCIPLES.md section 18.
"""
import sys

import numpy as np

import equiv

DATES = {"BERLIN": "2019-09-29", "CHICAGO": "2019-10-13", "NEW YORK": "2019-11-03"}


def load(path):
    import pyarrow.parquet as pq
    t = pq.read_table(path, columns=["datetime", "athlete", "distance", "duration", "gender", "major"])
    ath = t["athlete"].to_numpy()
    n = int(ath.max()) + 1
    day = (t["datetime"].to_numpy().astype("datetime64[D]") - np.datetime64("2019-01-01")).astype(int)
    nd = int(day.max()) + 1
    dist, dur = np.zeros((n, nd), np.float32), np.zeros((n, nd), np.float32)
    dist[ath, day], dur[ath, day] = t["distance"].to_numpy(), t["duration"].to_numpy()
    meta, seen = {}, set()
    for a, g, m in zip(ath, t["gender"].to_numpy(zero_copy_only=False), t["major"].to_numpy(zero_copy_only=False), strict=True):
        if int(a) not in seen:
            seen.add(int(a))
            meta[int(a)] = (g, m or "")
    return dist, dur, meta


def races(dist, dur, meta):
    out = []
    nd = dist.shape[1]
    for a, (g, majors) in meta.items():
        for entry in (x.strip() for x in majors.split(",")):
            for name, date in DATES.items():
                if entry != f"{name} 2019":
                    continue
                r0 = int((np.datetime64(date) - np.datetime64("2019-01-01")).astype(int))
                r = max(range(max(r0 - 1, 0), min(r0 + 2, nd)), key=lambda i: dist[a, i])
                km, mins = float(dist[a, r]), float(dur[a, r])
                if not 41.0 <= km <= 44.5 or not 2.6 <= mins / max(km, 0.1) <= 10.0 or r < 118:
                    continue
                weeks = [dist[a, r - 7 * k: r - 7 * (k - 1)] for k in range(1, 17)]
                build = float(np.mean([w.sum() for w in weeks[3:]]))
                fast = 0.0
                for i in range(r - 112, r - 14):
                    d, t = float(dist[a, i]), float(dur[a, i])
                    if 5 <= d <= 25 and t > 0 and 2.6 <= t / d <= 9:
                        fast = max(fast, equiv.index(d * 1000, t * 60))
                if build < 5 or fast < 30 or (dist[a, r - 112: r - 14] > 0).sum() < 20:
                    continue
                run = longest_gap = 0
                for v in dist[a, r - 112: r - 14] < 1.0:
                    run = run + 1 if v else 0
                    longest_gap = max(longest_gap, run)
                out.append({"min": mins, "build": build, "idx": fast, "longest": float(dist[a, r - 112: r - 7].max()),
                            "taper": float(np.mean([w.sum() for w in weeks[:3]]) / build), "gap": longest_gap >= 7, "male": g == "M"})
    return out


def report(rs):
    y = np.log([r["min"] for r in rs])
    col = lambda k: np.array([r[k] for r in rs], float)
    z = lambda x: (x - x.mean()) / x.std()
    names = ["speed", "volume", "longest run", "taper", "break of 7+ days", "male"]
    X = np.column_stack([np.ones(len(rs)), z(col("idx")), z(col("build")), z(col("longest")), z(np.minimum(col("taper"), 1.5)), col("gap"), col("male")])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    print(f"{len(rs)} marathons. Change in finish time (percent) per standard deviation, or for a break, holding the rest equal:")
    for nm, c in zip(names, b[1:], strict=True):
        print(f"  {nm:18s} {100 * c:+.1f}%")
    pred = np.array([equiv.predict(v, 42195) for v in col("idx")]) / 60
    ratio = np.exp(y) / pred
    err = np.abs(np.exp(y) / (pred * np.median(ratio)) - 1)
    print(f"Daniels-Gilbert from the best training run: actual/predicted median {np.median(ratio):.3f};"
          f" after one calibration the median error is {100 * np.median(err):.1f}% and 80% are within {100 * np.quantile(err, .8):.1f}%")


if __name__ == "__main__":
    report(races(*load(sys.argv[1])))
