"""Race equivalence from the oxygen-cost and time-to-exhaustion equations published by Daniels and Gilbert (1979).

The index is the VO2max that would explain a race result if running economy were
average. It is a performance figure, not a lab measurement: two runners with
the same index race the same times whatever their true VO2max. It is used
internally to turn one result into equivalent times at other distances.
"""
import math

MI = 1609.344
DISTANCES = [("1 mile", 1609.344), ("5K", 5000), ("5 miles", 8046.72), ("10K", 10000), ("10 miles", 16093.44),
             ("Half marathon", 21097.5), ("Marathon", 42195)]
WINDOWS = [("5K", 5000, 4950, 5200), ("5 miles", 8046.72, 8000, 8250), ("10K", 10000, 9950, 10350), ("10 miles", 16093.44, 16050, 16400),
           ("Half marathon", 21097.5, 21050, 21500), ("Marathon", 42195, 42100, 43000)]   # GPS reads a little long


def oxygen_cost(v):
    """ml/kg/min to run at v metres per minute."""
    return -4.60 + 0.182258 * v + 0.000104 * v * v


def fraction(t):
    """Fraction of VO2max that can be held for t minutes."""
    return 0.8 + 0.1894393 * math.exp(-0.012778 * t) + 0.2989558 * math.exp(-0.1932605 * t)


def index(dist_m, time_s):
    t = time_s / 60
    return oxygen_cost(dist_m / t) / fraction(t)


def predict(v, dist_m):
    """Seconds to run dist_m at index v (bisection on time)."""
    lo, hi = dist_m / 10.0, dist_m / 0.8     # between 10 m/s and 0.8 m/s
    for _ in range(60):
        mid = (lo + hi) / 2
        if index(dist_m, mid) > v:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def from_threshold(tp):
    """Index from threshold speed (m/s), taking threshold as the pace that can be held for an hour."""
    return oxygen_cost(tp * 60) / fraction(60)


def race_distance(dist_m):
    """(name, official metres) if a run's length matches a standard race distance, else None."""
    for name, official, lo, hi in WINDOWS:
        if lo <= dist_m <= hi:
            return name, official
    return None


def threshold_speed(v):
    """Threshold speed in m/s for index v (inverse of from_threshold)."""
    lo, hi = 1.0, 8.0
    for _ in range(50):
        mid = (lo + hi) / 2
        if from_threshold(mid) < v:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2
