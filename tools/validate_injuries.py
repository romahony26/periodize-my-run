"""Check the app's injury-related rules against a public training log with injuries recorded.

Not part of the running app. Data (CC0): Lövdal, den Hartigh and Azzopardi (2021), DataverseNL doi:10.34894/UWU9PV, files
week_approach_maskedID_timeseries.csv and day_approach_maskedID_timeseries.csv (74 competitive runners, 2012-2019).

  python tools/validate_injuries.py week_approach_maskedID_timeseries.csv day_approach_maskedID_timeseries.csv

Each row is one day with the three weeks (or seven days) before it and whether an injury began on it. Relative risk is the injury rate
on days a rule flags over the rate on days it does not; the interval resamples whole runners, since a runner's days are not independent.
Association only: it does not show that following a rule prevents an injury.
"""
import csv
import sys

import numpy as np


def load(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    return rows[0], np.array([[float(x) if x not in ("", "nan") else np.nan for x in r] for r in rows[1:]])


def report(label, flag, injury, runner, boots=400):
    rng = np.random.default_rng(3)
    flag, injury = flag.astype(bool), injury.astype(bool)

    def rr(f, y):
        return (y[f].mean() / y[~f].mean()) if f.any() and (~f).any() and y[~f].mean() else float("nan")

    groups = {r: np.where(runner == r)[0] for r in np.unique(runner)}
    ids = list(groups)
    draws = [rr(flag[p], injury[p]) for p in (np.concatenate([groups[r] for r in rng.choice(ids, len(ids))]) for _ in range(boots))]
    lo, hi = np.nanpercentile(draws, [2.5, 97.5])
    print(f"{label:55s} flags {100 * flag.mean():4.1f}% of days, RR {rr(flag, injury):4.2f} ({lo:4.2f} to {hi:4.2f}), "
          f"catches {100 * (flag & injury).sum() / injury.sum():4.1f}% of injuries")


def main(week_csv, day_csv):
    h, w = load(week_csv)
    c = lambda name: w[:, h.index(name)]
    injury, runner = c("injury"), c("Athlete ID")
    t0, t1, t2 = c("total kms"), c("total kms.1"), c("total kms.2")
    m0, m1, m2 = c("max km one day"), c("max km one day.1"), c("max km one day.2")
    ok = (t1 > 8) & (t2 > 8)
    spike, rise = ok & (m0 > 1.10 * np.maximum(m1, m2)), ok & (t0 > 1.20 * np.maximum(t1, t2))
    hard, norest = ok & (c("max exertion") >= 0.9), ok & (c("nr. rest days") == 0)
    print(f"{len(w)} weeks, {int(injury.sum())} injuries")
    for label, f in (("longest day more than 10% over the two weeks before", spike), ("week more than 20% above the best of the two before", rise),
                     ("a session rated 0.9 or more for effort", hard), ("no rest day", norest),
                     ("any of spike, 20% rise, very hard session", spike | rise | hard),
                     ("... or no rest day", spike | rise | hard | norest)):
        report(label, f, injury, runner)
    h, d = load(day_csv)
    km = np.column_stack([d[:, h.index("total km" + ("" if i == 0 else f".{i}"))] for i in range(7)])
    mean, sd = km.mean(1), km.std(1)
    mono = np.where(sd > 0, mean / np.maximum(sd, 1e-9), np.nan)
    report("monotony of 2 or more over 7 days (week of 20 km or more)", (km.sum(1) >= 20) & (mono >= 2.0), d[:, h.index("injury")], d[:, h.index("Athlete ID")])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
