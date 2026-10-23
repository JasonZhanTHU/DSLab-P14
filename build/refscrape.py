#!/usr/bin/env python3
"""Reference-knowledge scraper for the ERFA exam corpus.

For each course category (see data/categories.json produced by scrapbot.py) this
fetches open reference material from Wikipedia and saves it as plain-text
wikitext files, so you have study references lined up next to each exam set.

How topics are chosen (fully automatic, works for every course):
  1. The course display name is normalised to an English search term. A small
     German->English alias map (ALIASES) sharpens the common ERFA course names;
     anything not in the map falls back to the cleaned display name.
  2. Wikipedia search picks the best-matching main article; its wikitext is saved.
  3. The main article's outgoing [[wikilinks]] are ranked by how often they occur
     and the top --depth1 of them (real encyclopedia articles only) are fetched
     too, giving a topic pack around the course subject.

Output layout (resumable; existing files skipped unless --force):
  data/<slug>/references/index.json          # what was fetched, titles, urls
  data/<slug>/references/00_<Title>.wikitext # the main article
  data/<slug>/references/NN_<Title>.wikitext # linked sub-topics

Usage:
  python3 refscrape.py                         # every course in categories.json
  python3 refscrape.py --category strukturgeologie
  python3 refscrape.py --category seismologie --category geochemieii --depth1 30
  python3 refscrape.py --lang de               # search German Wikipedia instead
"""

import argparse
import json
import logging
import re
import sys
import time
from collections import Counter
from pathlib import Path
from urllib.parse import quote

import requests

log = logging.getLogger("refscrape")

UA = "scrapbot-refscrape/1.0 (ETH ERFA exam study helper; contact via local user)"

# German (and abbreviated) ERFA course names -> better English search terms.
# Anything missing just falls back to the cleaned display name, so this only
# needs entries where the raw name searches poorly.
ALIASES = {
    "strukturgeologie": "Structural geology",
    "seismologie": "Seismology",
    "geochemiei": "Geochemistry",
    "geochemieii": "Geochemistry",
    "dynamischeerde": "Plate tectonics",
    "atmosphre": "Atmosphere of Earth",
    "wettersysteme": "Weather",
    "klimasysteme": "Climate system",
    "kryosphre": "Cryosphere",
    "palontologie": "Paleontology",
    "sedimentologie": "Sedimentology",
    "mineralresourcesi": "Mineral resource classification",
    "oredeposits": "Ore genesis",
    "kristalleundmineralien": "Mineral",
    "grundlagendergesteinsmikroskopie": "Optical mineralogy",
    "metamorphoseundmagmatismusi": "Metamorphism",
    "metamorphoseundmagmatismusii": "Igneous rock",
    "hydrogeologie": "Hydrogeology",
    "groundwater": "Groundwater",
    "ingenieurgeologie": "Engineering geology",
    "rockmechanicsandrockengineering": "Rock mechanics",
    "soilmechanicsandfoundationengineering": "Soil mechanics",
    "geophysiki": "Geophysics",
    "geophysikii": "Geophysics",
    "geophysicalfluiddynamics": "Geophysical fluid dynamics",
    "continuummechanics": "Continuum mechanics",
    "mathematikiii": "Mathematical analysis",
    "mathematicalmethods": "Mathematical physics",
    "mathematikivstatistik": "Statistics",
    "physikiii": "Physics",
    "geologiederschweiz": "Geology of Switzerland",
    "quartrgeologieundgeomorphologie": "Geomorphology",
    "planetarygeochemistry": "Cosmochemistry",
    "planetaryphysicsandchemistry": "Planetary science",
    "appliedmineralogy": "Mineralogy",
    "appliedmineralogyi": "Mineralogy",
    "chemie": "Chemistry",
    "geobiologie": "Geobiology",
    "snowcoverphysicsandmodelling": "Snow science",
    "reflectionseismologyprocessing": "Reflection seismology",
    "engineeringseismology": "Seismic hazard",
    "earthquakesiseismotectonics": "Seismotectonics",
    "explorationandenvironmentalgeophysics": "Exploration geophysics",
    "numericalmodellingforappliedgeophysics": "Numerical modeling (geophysics)",
    "paleoceanographybiogeochemicalcycles": "Paleoceanography",
    "ozeanographieundhydrogeologie": "Physical oceanography",
    "kartenpraktikumi": "Geologic map",
    "kartenpraktikum2geologicalmapanalysis": "Geologic map",
}

# Wikilink targets that are never useful study references.
LINK_SKIP_PREFIX = ("file:", "image:", "category:", "wikipedia:", "help:",
                     "template:", "portal:", "wikt:", "wiktionary:", "s:",
                     "special:", "media:", "mos:", ":")
# Dated / list-ish targets to drop.
LINK_SKIP_RE = re.compile(r"(?i)\b(list of|\d{3,4}s?$|disambiguation)\b")


class Wiki:
    def __init__(self, lang: str, delay: float):
        self.api = f"https://{lang}.wikipedia.org/w/api.php"
        self.base = f"https://{lang}.wikipedia.org/wiki/"
        self.s = requests.Session()
        self.s.headers["User-Agent"] = UA
        self.delay = delay
        self._last = 0.0

    def _get(self, params):
        wait = self.delay - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        params = {**params, "format": "json", "formatversion": "2"}
        for attempt in range(5):
            r = self.s.get(self.api, params=params, timeout=60)
            self._last = time.monotonic()
            if r.status_code in (429, 503):
                back = min(60, 5 * 2 ** attempt)
                log.warning("rate-limited (%s); backing off %ds", r.status_code, back)
                time.sleep(back)
                continue
            r.raise_for_status()
            return r.json()
        r.raise_for_status()

    def search(self, term: str):
        """Return the best-matching article title, or None."""
        d = self._get({"action": "query", "list": "search", "srsearch": term,
                        "srnamespace": "0", "srlimit": "1"})
        hits = d.get("query", {}).get("search", [])
        return hits[0]["title"] if hits else None

    def wikitext(self, title: str):
        """Return (resolved_title, wikitext) following redirects, or (None, None)."""
        d = self._get({"action": "query", "prop": "revisions", "titles": title,
                        "rvprop": "content", "rvslots": "main", "redirects": "1"})
        pages = d.get("query", {}).get("pages", [])
        if not pages or pages[0].get("missing"):
            return None, None
        p = pages[0]
        try:
            rev = p["revisions"][0]
        except (KeyError, IndexError):
            return None, None
        # formatversion=2 with rvslots puts content under slots.main.content;
        # tolerate the older flat shape too.
        text = rev.get("slots", {}).get("main", {}).get("content") or rev.get("content")
        if not text:
            return None, None
        return p["title"], text


def norm_term(slug: str, displayname: str) -> str:
    if slug in ALIASES:
        return ALIASES[slug]
    # Clean the display name: drop trailing roman numerals / arabic numbers.
    name = re.sub(r"\s+(I{1,3}|IV|V|VI|\d+)\b\.?$", "", displayname).strip()
    return name or displayname


# Body sections whose links are usually off-topic for an exam (history anecdotes,
# economics, pop-culture), so links appearing only under them are down-weighted.
LOW_VALUE_SECTION_RE = re.compile(
    r"(?i)(history|etymology|econom|cultur|popular culture|society|"
    r"in fiction|applications?)\b")


def rank_links(text: str, limit: int):
    """Pull [[wikilinks]] ranked by position: lead and early body beat appendices.

    Core concepts are introduced in an article's lead and early sections; history,
    economics and culture sections (and plain frequency) pull in noise like
    'Babylonia' on a mineralogy page. We score each link occurrence by where it
    sits and keep the highest-scoring distinct targets.
    """
    # Drop appendix sections (See also / References / ...) outright.
    cut = re.search(r"(?im)^==\s*(see also|references|notes|external links|"
                    r"further reading|bibliography|sources|citations)\s*==", text)
    if cut:
        text = text[:cut.start()]

    # Index section boundaries so we can tell which == section == a link sits in.
    lead_end = len(text)
    first_head = re.search(r"(?m)^==[^=].*?==\s*$", text)
    if first_head:
        lead_end = first_head.start()
    low_spans = [(m.start(), m.end()) for m in
                 re.finditer(r"(?ms)^==\s*[^=]*?==\s*$.*?(?=^==[^=]|\Z)", text)
                 if LOW_VALUE_SECTION_RE.search(m.group(0).split("\n", 1)[0])]

    def in_low(pos):
        return any(a <= pos < b for a, b in low_spans)

    scores = Counter()
    for m in re.finditer(r"\[\[([^\]|#]+)", text):
        target = m.group(1).strip()
        low = target.lower()
        if not target or low.startswith(LINK_SKIP_PREFIX):
            continue
        if LINK_SKIP_RE.search(target):
            continue
        pos = m.start()
        if pos < lead_end:
            w = 6.0          # lead: core subject matter
        elif in_low(pos):
            w = 0.5          # history/economics/culture: noise
        else:
            w = 2.0          # ordinary body section
        scores[target] += w

    out, seen = [], set()
    for target, _ in scores.most_common():
        key = target.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(target)
        if len(out) >= limit:
            break
    return out


def safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_")[:80] or "_"


def scrape_course(wiki: Wiki, slug: str, displayname: str, outdir: Path,
                  depth1: int, force: bool):
    refdir = outdir / slug / "references"
    index_path = refdir / "index.json"
    if index_path.exists() and not force:
        log.info("[%s] already done (index.json exists); use --force to redo", slug)
        return

    term = norm_term(slug, displayname)
    log.info("[%s] search term: %r", slug, term)
    title = wiki.search(term)
    if not title:
        log.warning("[%s] no Wikipedia hit for %r", slug, term)
        return
    main_title, main_text = wiki.wikitext(title)
    if not main_text:
        log.warning("[%s] could not fetch wikitext for %r", slug, title)
        return

    refdir.mkdir(parents=True, exist_ok=True)
    entries = []

    def save(n, t, text):
        fn = f"{n:02d}_{safe(t)}.wikitext"
        (refdir / fn).write_text(text, encoding="utf-8")
        entries.append({"order": n, "title": t, "file": fn,
                        "url": wiki.base + quote(t.replace(" ", "_")),
                        "bytes": len(text.encode("utf-8"))})
        log.info("[%s]   %02d %s (%d bytes)", slug, n, t, len(text))

    save(0, main_title, main_text)

    links = rank_links(main_text, depth1)
    n = 1
    for link in links:
        try:
            rt, txt = wiki.wikitext(link)
        except requests.HTTPError as e:
            log.warning("[%s]   skip %r: %s", slug, link, e)
            continue
        if not txt or any(e["title"].lower() == (rt or "").lower() for e in entries):
            continue
        # Skip redirects that collapse onto something already saved.
        save(n, rt, txt)
        n += 1

    index = {
        "slug": slug,
        "displayname": displayname,
        "search_term": term,
        "main_article": main_title,
        "language": wiki.base,
        "count": len(entries),
        "entries": entries,
        "license": "Wikipedia text is CC BY-SA 4.0; see each article URL for history/attribution.",
    }
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("[%s] saved %d reference files -> %s", slug, len(entries), refdir)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path("data"))
    ap.add_argument("--category", action="append",
                    help="limit to a course slug (repeatable); default = all")
    ap.add_argument("--lang", default="en", help="Wikipedia language edition (en/de)")
    ap.add_argument("--depth1", type=int, default=25,
                    help="max linked sub-topic articles per course")
    ap.add_argument("--delay", type=float, default=0.5, help="seconds between API calls")
    ap.add_argument("--force", action="store_true", help="re-fetch courses already done")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()

    logging.basicConfig(level=logging.DEBUG if a.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")

    cats = json.loads((a.out / "categories.json").read_text(encoding="utf-8"))
    only = set(a.category) if a.category else None
    wiki = Wiki(a.lang, a.delay)

    picked = [c for c in cats if (only is None or c["slug"] in only)
              and c["slug"] != "default"]
    log.info("%d course(s) to process", len(picked))
    for c in picked:
        try:
            scrape_course(wiki, c["slug"], c.get("displayname", c["slug"]),
                          a.out, a.depth1, a.force)
        except requests.HTTPError as e:
            log.error("[%s] HTTP error: %s", c["slug"], e)
        except Exception as e:  # keep going across the whole corpus
            log.error("[%s] failed: %s", c["slug"], e)


if __name__ == "__main__":
    sys.exit(main())
