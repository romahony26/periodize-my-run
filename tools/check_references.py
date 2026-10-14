"""Check PRINCIPLES.md against itself and, with --live, against the published record.

  python tools/check_references.py           # offline: every citation has a reference, every reference is cited, numbering is sound
  python tools/check_references.py --live    # also looks each reference up in Europe PMC and compares title, year and first author

A reference is "verified" when Europe PMC (or, for journals PubMed does not index, Crossref) returns a record whose title matches, whose first author matches and whose year is within one of the one given. Books, regulator notices and
public-domain tables are not in the index and are listed as not checked, not as failures.
"""
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def principles():
    with open(os.path.join(HERE, "PRINCIPLES.md"), encoding="utf-8") as f:
        return f.read()


def parse():
    text = principles()
    body, _, refs = text.partition("## References")
    rules = re.findall(r"^(\d+[a-z]?)\. (.+?)(?=^\d+[a-z]?\. |^## |\Z)", body, re.S | re.M)
    out = []
    for line in refs.splitlines():
        m = re.match(r"- (.+?) \((\d{4})\)\. (.+)", line)
        if m:
            out.append({"authors": m.group(1), "year": m.group(2), "rest": m.group(3), "line": line})
    return rules, out


def first_author(authors):
    return re.split(r"[ ,]", authors.strip())[0]


def cited(rules_or_text):
    """{(surname, year)} named in the principles, from '(Surname and colleagues, 2020)' and '(Surname, 2020)' forms."""
    found = set()
    texts = [rules_or_text] if isinstance(rules_or_text, str) else [t for _n, t in rules_or_text]
    for t in texts:
        t = re.sub(r"\s+", " ", t)
        for m in re.finditer(r"([A-Z][A-Za-zÀ-ÿ'\-]+)(?: and [A-Z][A-Za-zÀ-ÿ'\-]+| and colleagues| [A-Z]{1,3})?,? \(?((?:(?:19|20)\d\d)(?:,? (?:19|20)\d\d)*)", t):
            for y in re.findall(r"(?:19|20)\d\d", m.group(2)):
                found.add((m.group(1), y))
        if re.search(r"Daniels-Gilbert|Daniels and Gilbert", t):      # named without a year
            found.add(("Daniels", "1979"))
    return found


def offline():
    rules, refs = parse()
    problems = []
    nums = [r[0] for r in rules]
    if len(nums) != len(set(nums)):
        problems.append("duplicate principle numbers")
    labels = [n for n, t in rules if not re.search(r"\[[RCP]\]", t)]
    if labels:
        problems.append(f"principles with no [R], [C] or [P] label: {labels}")
    uncited = []
    for n, txt in rules:
        if re.search(r"\[R\]", txt) and not cited([(n, txt)]):
            uncited.append(n)
    if uncited:
        problems.append(f"principles marked [R] (research) that name no study: {uncited}")
    cites = cited(principles().partition("## References")[0])
    by_year = {}
    for r in refs:
        by_year.setdefault(r["year"], []).append(r["authors"].lower())
    skip = {"Administration", "Periodize", "The", "In", "From", "By", "For", "Garmin", "Run", "Tour", "World", "WBGT", "Table", "Vuelta"}
    unlisted = sorted(c for c in cites if c[0] not in skip and not any(c[0].lower() in a for a in by_year.get(c[1], [])))
    cited_names = {}
    for name, year in cites:
        cited_names.setdefault(year, set()).add(name.lower())
    unused = sorted(f"{r['authors']} ({r['year']})" for r in refs if not any(n in r["authors"].lower() for n in cited_names.get(r["year"], ())))
    return rules, refs, problems, unlisted, unused


def _title(r):
    """The title as words only: punctuation and accents differ between a reference list and an index."""
    import unicodedata
    title = re.split(r"\. \*|\. [A-Z][^.]*\*", r["rest"])[0].strip(" .")
    title = unicodedata.normalize("NFKD", re.sub(r"[*_]", "", title)).encode("ascii", "ignore").decode()
    return " ".join(re.findall(r"[A-Za-z0-9]+", title)[:7])


def _get(url, tries=4):
    import time
    for k in range(tries):
        try:
            if not url.startswith("https://"):
                raise ValueError("only https addresses are fetched")
            # https only, and only the two index hosts named above
            with urllib.request.urlopen(url, timeout=30) as f:  # noqa: S310  # nosec B310
                return json.load(f)
        except urllib.error.HTTPError as e:
            if e.code != 429 or k == tries - 1:
                raise
            time.sleep(2 * (k + 1))
    return {}


def lookup(r):
    """(status, note). Europe PMC first (PubMed and more), then Crossref for journals PubMed does not index. A year one off is
    accepted and said so: the online and the print year of an article often differ."""
    fa, title = first_author(r["authors"]).lower(), _title(r)
    year = int(r["year"])
    try:
        q = f'TITLE:"{title}" AND PUB_YEAR:[{year - 1} TO {year + 1}]'
        hits = _get("https://www.ebi.ac.uk/europepmc/webservices/rest/search?format=json&resultType=lite&pageSize=5&query=" + urllib.parse.quote(q))["resultList"]["result"]
        if not hits:         # punctuation in a title (a colon, an apostrophe) can defeat a phrase search: try its longer words
            words = [w for w in title.split() if len(w) >= 6][:3]
            q = f'AUTH:"{first_author(r["authors"])}" AND ' + " AND ".join(f"TITLE:{w}" for w in words) + f" AND PUB_YEAR:[{year - 1} TO {year + 1}]"
            hits = _get("https://www.ebi.ac.uk/europepmc/webservices/rest/search?format=json&resultType=lite&pageSize=5&query=" + urllib.parse.quote(q))["resultList"]["result"]
        for h in hits:
            if fa in h.get("authorString", "").lower():
                off = "" if str(h.get("pubYear")) == r["year"] else f" (indexed as {h.get('pubYear')})"
                return "verified", h.get("title", "")[:70] + off
        cr = _get("https://api.crossref.org/works?rows=3&query.bibliographic=" + urllib.parse.quote(title + " " + fa)
                  + f"&filter=from-pub-date:{year - 1},until-pub-date:{year + 1}")
        for it in cr["message"]["items"]:
            names = " ".join(a.get("family", "") for a in it.get("author", [])).lower()
            if fa in names and title[:25].lower() in " ".join(it.get("title", [""])).lower():
                return "verified", ("Crossref: " + it["title"][0])[:70]
    except Exception as e:  # noqa: BLE001
        return "error", str(e)[:60]
    return "not found", title[:70]


def main(live):
    rules, refs, problems, unlisted, unused = offline()
    print(f"{len(rules)} principles, {len(refs)} references")
    for p in problems:
        print("PROBLEM:", p)
    if unlisted:
        print("cited in a principle but not in the reference list:", unlisted)
    if unused:
        print("in the reference list but not cited in a principle:", unused)
    if not live:
        return
    tally = {}
    for r in refs:
        if re.search(r"book|manual|Human Kinetics|public-domain|Not peer-reviewed|CC0|CC BY", r["line"], re.I):
            status, note = "not checked (not a journal article)", ""
        else:
            status, note = lookup(r)
            if status == "not found" and re.search(r"from memory", r["line"], re.I):
                status = "not in an index; marked from memory"
            elif status == "not found" and re.search(r"record confirmed|abstract read|text read", r["line"], re.I):
                status = "confirmed by hand when written (the search could not match its title)"
        tally.setdefault(status, []).append((r["authors"], r["year"], note))
    for status, items in tally.items():
        print(f"\n{status}: {len(items)}")
        if status != "verified":
            for a, y, n in items:
                print(f"  - {a} ({y}) {n}")


if __name__ == "__main__":
    main("--live" in sys.argv)
