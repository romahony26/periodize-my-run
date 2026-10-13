"""A planned day as a .fit workout file, for watches that can import one (COROS, Suunto, Polar, Wahoo and others).

The same steps that are sent to Garmin are written in the FIT workout format, so any watch or app that reads FIT workouts can use
them. Nothing is sent anywhere: the file is downloaded and imported by hand. Whether a given watch accepts it is up to that watch.
The format is Garmin's published FIT protocol: a file id, one workout message and one workout_step message per step, and a
repeat step that points back at the first step of the group.
"""
import struct
import time

_CRC = (0x0000, 0xCC01, 0xD801, 0x1400, 0xF001, 0x3C00, 0x2800, 0xE401, 0xA001, 0x6C00, 0x7800, 0xB401, 0x5000, 0x9C01, 0x8801, 0x4400)
INTENSITY = {"interval": 0, "rest": 1, "warmup": 2, "cooldown": 3, "recovery": 4}
EPOCH = 631065600           # seconds from 1970 to the FIT epoch, 1989-12-31


def crc(data, c=0):
    for b in data:
        t = _CRC[c & 0xF]
        c = ((c >> 4) & 0x0FFF) ^ t ^ _CRC[b & 0xF]
        t = _CRC[c & 0xF]
        c = ((c >> 4) & 0x0FFF) ^ t ^ _CRC[(b >> 4) & 0xF]
    return c


def _flat(steps, out=None):
    """The Garmin-style step list as FIT step dicts, a repeat group becoming its steps then a step that repeats them."""
    out = [] if out is None else out
    for s in steps:
        if s.get("type") == "RepeatGroupDTO":
            first = len(out)
            _flat(s["workoutSteps"], out)
            out.append({"name": "Repeat", "dur": 6, "dv": first, "tt": 2, "tv": int(s.get("numberOfIterations") or 1), "lo": 0, "hi": 0, "int": 0})
            continue
        key = (s.get("endCondition") or {}).get("conditionTypeKey")
        val = float(s.get("endConditionValue") or 0)
        dur, dv = (0, int(val * 1000)) if key == "time" else (1, int(val * 100)) if key == "distance" else (5, 0)   # 5 = open (lap button)
        tgt = (s.get("targetType") or {}).get("workoutTargetTypeKey")
        tt, lo, hi = 2, 0, 0                                      # 2 = open: no target
        if tgt == "pace.zone":
            tt, lo, hi = 0, int(s["targetValueOne"] * 1000), int(s["targetValueTwo"] * 1000)    # speed, in thousandths of a metre a second
        elif tgt == "heart.rate.zone":
            tt, lo, hi = 1, int(s["targetValueOne"]) + 100, int(s["targetValueTwo"]) + 100       # heart rate, with FIT's offset of 100
        k = (s.get("stepType") or {}).get("stepTypeKey", "interval")
        out.append({"name": k.capitalize(), "dur": dur, "dv": dv, "tt": tt, "tv": 0, "lo": lo, "hi": hi, "int": INTENSITY.get(k, 0)})
    return out


def build(w, now=None):
    """The bytes of a FIT workout file for one Garmin-style workout dict (as made by push.workout)."""
    steps = _flat(w["workoutSegments"][0]["workoutSteps"])
    name = (w.get("workoutName") or "Workout").encode("ascii", "replace")[:31] + b"\x00"
    body = bytearray()

    def define(local, glob, fields):
        body.extend(struct.pack("<BBBHB", 0x40 | local, 0, 0, glob, len(fields)))
        for num, size, base in fields:
            body.extend(struct.pack("<BBB", num, size, base))

    created = int(now if now is not None else time.time()) - EPOCH
    define(0, 0, [(0, 1, 0x00), (1, 2, 0x84), (2, 2, 0x84), (4, 4, 0x86)])           # file_id: type, manufacturer, product, time_created
    body.extend(struct.pack("<BBHHI", 0, 5, 255, 0, created))
    define(1, 26, [(4, 1, 0x00), (6, 2, 0x84), (8, len(name), 0x07)])                  # workout: sport, number of steps, name
    body.extend(struct.pack("<BBH", 1, 1, len(steps)) + name)
    define(2, 27, [(254, 2, 0x84), (1, 1, 0x00), (2, 4, 0x86), (3, 1, 0x00), (4, 4, 0x86), (5, 4, 0x86), (6, 4, 0x86), (7, 1, 0x00)])
    for i, s in enumerate(steps):
        body.extend(struct.pack("<BHBIBIIIB", 2, i, s["dur"], s["dv"], s["tt"], s["tv"], s["lo"], s["hi"], s["int"]))
    header = struct.pack("<BBHI4s", 14, 0x10, 2093, len(body), b".FIT")
    header += struct.pack("<H", crc(header))
    data = header + bytes(body)
    return data + struct.pack("<H", crc(data))
