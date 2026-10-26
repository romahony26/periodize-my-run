"""Met Éireann weather warnings for the county of your latest run.

Switched on with the weather (Settings, Connections). The warnings are Met Éireann's public feed (www.met.ie/warningsxml/rss.xml; each
item links to a CAP file on cap.met.ie). No account or key is used and nothing about you is sent: the feed is the same for everyone, and
the county is worked out here, from the rounded location the weather already uses.

Licence (Met Éireann Custom Open Data Licence Notice, 22 May 2018: Creative Commons Attribution 4.0 plus the rules below):
  - Met Éireann is credited as the source, with the five attribution statements, wherever a warning is shown (ATTRIBUTION).
  - A warning is shown as issued. Its time of issue, onset, expiry, area, description, severity, certainty, event and headline are never
    changed; only the markup in the description is turned into plain lines.
  - Warnings are kept up to date: the feed is read at every sync, an expired warning is removed, and when the feed cannot be read for
    three hours no warning is shown at all, so an out-of-date one is never presented as current.
  - Where the app shows web content built on this data (the session, the plan), the current warnings are shown with it.
What the app does about a warning is its own advice and is written separately from the warning, never as part of it.
"""
import datetime as dt
import html
import math
import re
import xml.etree.ElementTree as ET  # nosec B405 - only Met Éireann's own files over HTTPS, and a file with a DTD or entity is refused below

import requests

import db
import heat
from log import log

FEED = "https://www.met.ie/warningsxml/rss.xml"
CAP_HOST = "https://cap.met.ie/"
NS = {"c": "urn:oasis:names:tc:emergency:cap:1.2"}
REFRESH_S = 20 * 60
STALE_S = 3 * 3600
MAX_BYTES = 200_000
NEAREST_KM = 60              # farther than this from every county centre is not in the Republic, so no Met Éireann warning applies
UA = {"User-Agent": "PeriodizeMyRun/2 (personal training planner; reads the public warnings feed)"}

# The five statements Met Éireann requires with its data and anything made from it.
ATTRIBUTION = ("Copyright Met Éireann",
               "Source: www.met.ie",
               "This data is published under a Creative Commons Attribution 4.0 International (CC BY 4.0) licence: https://creativecommons.org/licenses/by/4.0/",
               "Met Éireann does not accept any liability whatsoever for any error or omission in the data, their availability, or for any loss or damage arising from their use.",
               "The wording, times, area and level of each warning are unchanged; only its formatting is simplified.")

# Approximate county centres (latitude, longitude), only to find the county of a rounded location, and each county's province.
COUNTIES = {
    "Carlow": (52.72, -6.84, "Leinster"), "Cavan": (53.99, -7.36, "Ulster"), "Clare": (52.90, -8.98, "Munster"),
    "Cork": (51.95, -8.75, "Munster"), "Donegal": (54.90, -8.00, "Ulster"), "Dublin": (53.38, -6.28, "Leinster"),
    "Galway": (53.35, -9.00, "Connacht"), "Kerry": (52.15, -9.55, "Munster"), "Kildare": (53.16, -6.80, "Leinster"),
    "Kilkenny": (52.60, -7.25, "Leinster"), "Laois": (52.99, -7.35, "Leinster"), "Leitrim": (54.12, -8.00, "Connacht"),
    "Limerick": (52.50, -8.75, "Munster"), "Longford": (53.73, -7.75, "Leinster"), "Louth": (53.92, -6.50, "Leinster"),
    "Mayo": (53.90, -9.30, "Connacht"), "Meath": (53.62, -6.65, "Leinster"), "Monaghan": (54.15, -6.97, "Ulster"),
    "Offaly": (53.25, -7.55, "Leinster"), "Roscommon": (53.75, -8.20, "Connacht"), "Sligo": (54.15, -8.60, "Connacht"),
    "Tipperary": (52.60, -7.90, "Munster"), "Waterford": (52.20, -7.65, "Munster"), "Westmeath": (53.53, -7.45, "Leinster"),
    "Wexford": (52.45, -6.55, "Leinster"), "Wicklow": (53.00, -6.35, "Leinster"),
}
# Met Éireann's awareness types (the numbers are the European Meteoalarm ones) that matter to a run, and the level at which the app acts:
# Orange (Severe) or Red (Extreme). Yellow is shown, with a caution, and changes nothing.
RUN_TYPES = {1: "wind", 2: "snow or ice", 3: "thunderstorm", 4: "fog", 5: "heat", 6: "low temperature", 10: "rain", 11: "flood", 12: "rain and flood"}
ACT_ON = ("Severe", "Extreme")


def county(loc):
    """Name of the county whose centre is nearest (lat, lon), or None when none is within NEAREST_KM."""
    if not loc:
        return None
    best = None
    for name, (la, lo, _prov) in COUNTIES.items():
        dx = (lo - loc[1]) * 111.32 * math.cos(math.radians(loc[0]))
        dy = (la - loc[0]) * 110.57
        d = math.hypot(dx, dy)
        if best is None or d < best[0]:
            best = (d, name)
    return best[1] if best and best[0] <= NEAREST_KM else None


def applies(area, name):
    """Does the warning's area text name this county, its province, or all of Ireland?"""
    if not name:
        return False
    toks = {t.strip().lower() for t in re.split(r",|\band\b", area or "") if t.strip()}
    return name.lower() in toks or COUNTIES[name][2].lower() in toks or "ireland" in toks


def _text(markup):
    t = re.sub(r"(?i)<li[^>]*>", "\n• ", markup or "")
    t = re.sub(r"(?i)</?(p|ul|ol|br)[^>]*>", "\n", t)
    t = html.unescape(re.sub(r"<[^>]+>", "", t)).replace("\xa0", " ")
    return "\n".join(x.strip() for x in t.splitlines() if x.strip())


def _get(url):
    r = requests.get(url, headers=UA, timeout=20, stream=True, allow_redirects=False)
    if r.status_code != 200:
        raise ValueError(f"status {r.status_code}")
    body = r.raw.read(MAX_BYTES + 1, decode_content=True)
    if len(body) > MAX_BYTES:
        raise ValueError("too large")
    if b"<!DOCTYPE" in body.upper() or b"<!ENTITY" in body.upper():
        raise ValueError("refused: a document type or entity")
    return body.decode("utf-8-sig")


def parse(cap):
    """One CAP alert as the fields Met Éireann says may not be changed, plus the type and level. None if it is not a live land warning."""
    a = ET.fromstring(cap)  # noqa: S314  # nosec B314 - see the import
    if (a.findtext("c:status", namespaces=NS) or "") != "Actual" or (a.findtext("c:msgType", namespaces=NS) or "") == "Cancel":
        return None
    i = a.find("c:info", NS)
    if i is None:
        return None
    g = lambda t: (i.findtext("c:" + t, namespaces=NS) or "").strip()      # noqa: E731
    par = {(p.findtext("c:valueName", namespaces=NS) or ""): (p.findtext("c:value", namespaces=NS) or "") for p in i.findall("c:parameter", NS)}
    m = re.match(r"\s*(\d+)\s*;\s*(.*)", par.get("awareness_type", ""))
    if not m or not g("expires"):
        return None
    return {"id": (a.findtext("c:identifier", namespaces=NS) or "").strip(), "sent": (a.findtext("c:sent", namespaces=NS) or "").strip(),
            "event": g("event"), "severity": g("severity"), "certainty": g("certainty"), "onset": g("onset") or g("effective"),
            "expires": g("expires"), "headline": g("headline"), "description": _text(g("description")),
            "area": (i.findtext("c:area/c:areaDesc", namespaces=NS) or "").strip(), "type": int(m.group(1)), "kind": m.group(2).strip()}


def _when(text):
    try:
        return dt.datetime.fromisoformat(text)
    except (TypeError, ValueError):
        return None


def refresh(force=False, now=None):
    """Read the feed again if it is older than REFRESH_S. Does nothing with the weather switched off. Keeps the last good copy on failure."""
    if not db.get("heat_adjust"):
        return None
    now = now or dt.datetime.now()
    saved = db.get("met_warnings") or {}
    if not force and saved.get("fetched") and (now - dt.datetime.fromisoformat(saved["fetched"])).total_seconds() < REFRESH_S:
        return saved
    try:
        known = {x["id"]: x for x in saved.get("items") or []}
        items = []
        feed = ET.fromstring(_get(FEED))  # noqa: S314  # nosec B314 - see the import
        for link in [(x.findtext("link") or "").strip() for x in feed.iter("item")]:
            if not link.startswith(CAP_HOST):
                continue
            ident = link.rsplit("/", 1)[-1][:-4]
            w = known.get(ident) if ident in known else parse(_get(link))
            if w and (_when(w["expires"]) is None or _when(w["expires"]) > now.astimezone()):
                w["id"] = ident
                items.append(w)
        saved = {"fetched": now.isoformat(timespec="seconds"), "items": items}
        db.put("met_warnings", saved)
        log.info("Met Éireann warnings read: %d current", len(items))
    except (requests.RequestException, ValueError, ET.ParseError) as e:
        log.warning("Met Éireann warnings could not be read (%s); the last copy is kept until it is too old to show", type(e).__name__)
    return saved


def for_day(day, now=None):
    """The warnings for the athlete's county that are still valid and overlap `day`, as issued, worst first. None until the weather has a location."""
    if not db.get("heat_adjust"):
        return None
    saved = db.get("met_warnings") or {}
    now = now or dt.datetime.now()
    name = county(heat.location())      # where the latest GPS run started, and nowhere else
    out = {"county": name, "fetched": saved.get("fetched"), "items": [], "stale": True, "attribution": list(ATTRIBUTION)}
    if not saved.get("fetched") or (now - dt.datetime.fromisoformat(saved["fetched"])).total_seconds() > STALE_S:
        return out
    out["stale"] = False
    a = dt.datetime.combine(day, dt.time.min).astimezone()
    b = a + dt.timedelta(days=1)
    for w in saved.get("items") or []:
        on, ex = _when(w["onset"]), _when(w["expires"])
        if not on or not ex or ex <= now.astimezone() or on >= b or ex <= a or not applies(w["area"], name):
            continue
        out["items"].append(w)
    out["items"].sort(key=lambda w: ("Extreme", "Severe", "Moderate", "Minor").index(w["severity"]) if w["severity"] in ("Extreme", "Severe", "Moderate", "Minor") else 9)
    return out


def hold(day, hour):
    """The worst Orange or Red warning for a run type that covers the hour a run starts, or None. This is the app's advice trigger."""
    f = for_day(day)
    if not f or f["stale"]:
        return None
    a = dt.datetime.combine(day, dt.time(hour)).astimezone()
    b = a + dt.timedelta(hours=1)
    hit = [w for w in f["items"] if w["severity"] in ACT_ON and w["type"] in RUN_TYPES and _when(w["onset"]) < b and _when(w["expires"]) > a]
    return hit[0] if hit else None   # for_day sorts Extreme first
