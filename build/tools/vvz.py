#!/usr/bin/env python3
"""ETH course catalogue (VVZ, public) for the ERFA exam categories.

  python3 build/tools/vvz.py catalog          # all D-ERDW learning units, several semesters -> data/vvz_catalog.json
  python3 build/tools/vvz.py match            # category -> VVZ candidates (fuzzy) -> data/vvz_match.json
  python3 build/tools/vvz.py details          # per matched unit: catalogue data + links -> data/<slug>/course/

Manual corrections go in build/tools/vvz_overrides.json: {"<slug>": ["651-4004-00L", ...]}.
"""
import json, re, sys, time, unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://www.vvz.ethz.ch/Vorlesungsverzeichnis/"
SEMS = ["2026S", "2025W", "2025S", "2024W", "2024S", "2023W"]
OUT = Path("data")
S = requests.Session()
S.headers["User-Agent"] = "scrapbot/1.0 (study material collector)"


def get(url, **params):
    for i in range(5):
        try:
            r = S.get(url, params=params, timeout=60)
            if r.status_code == 200:
                time.sleep(0.4)
                return r.text
        except requests.RequestException:
            pass
        time.sleep(2 ** i)
    raise RuntimeError(url)


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def parse_list(html, sem, lang):
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for tr in soup.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 3:
            continue
        code = tds[0].get_text(strip=True)
        if not re.fullmatch(r"\d{3}-\d{4}-[0-9A-Z]{3}", code):
            continue
        a = tds[1].find("a", href=re.compile("lerneinheitId="))
        if not a:
            continue
        lid = re.search(r"lerneinheitId=(\d+)", a["href"]).group(1)
        rows.append(dict(code=code, sem=sem, id=lid, lang=lang, title=a.get_text(" ", strip=True),
                         lecturers=tds[-1].get_text(" ", strip=True).replace(" ,", ",")))
    pages = [int(m) for m in re.findall(r"seite=(\d+)", html)]
    return rows, max(pages or [1])


# D-ERDW units are 651-*; service courses taken by Earth science students are found by title.
QUERIES = [("651-*", "")] + [("", t) for t in (
    "Mathemati*", "Physi*", "Chemie*", "Chemistry*", "Soil Mechanics*", "Rock Mechanics*",
    "Engineering Geology*", "Ingenieurgeologie*", "Geophysical Fluid*", "Continuum*",
    "Snow*", "Groundwater*", "Hydrogeolog*", "Seismolog*", "Earthquake*", "Statisti*",
    "Paleoceanograph*", "Planetary*", "Ore *", "Mineral *", "Climate*", "Klima*", "Weather*",
    "Wetter*", "Atmosph*", "Cryosphere*", "Kryosph*", "Ocean*", "Ozean*", "Geobiolog*",
    "Biogeochemi*", "Mathematical Methods*")]


def catalog():
    units = {}
    for sem in SEMS:
        for code_q, title_q in QUERIES:
          for lang in ("de", "en"):
            page, last = 1, 1
            while page <= last:
                # VVZ only pages correctly when the full parameter set is sent.
                html = get(BASE + "sucheLehrangebot.view", lerneinheitscode=code_q, deptId="", famname="",
                           unterbereichAbschnittId="", seite=page, lerneinheitstitel=title_q, rufname="",
                           kpRange="0,999", lehrsprache="", bereichAbschnittId="", semkez=sem,
                           studiengangAbschnittId="", studiengangTyp="", ansicht=1, lang=lang,
                           katalogdaten="", wahlinfo="", **({"search": "on"} if page == 1 else {}))
                rows, last = parse_list(html, sem, lang)
                for r in rows:
                    u = units.setdefault(r["code"], dict(code=r["code"], titles=set(), offerings={}))
                    u["titles"].add(r["title"])
                    u["offerings"].setdefault(sem, dict(id=r["id"], lecturers=r["lecturers"]))
                print(sem, code_q or title_q, lang, page, "/", last, len(units), flush=True)
                page += 1
    for u in units.values():
        u["titles"] = sorted(u["titles"])
    (OUT / "vvz_catalog.json").write_text(json.dumps(units, indent=1, ensure_ascii=False))


ALIASES = {"i": "1", "ii": "2", "iii": "3", "iv": "4"}


def toks(s):
    return [ALIASES.get(t, t) for t in norm(s).split()]


def score(cat, title):
    a, b = " ".join(toks(cat)), " ".join(toks(title))
    r = SequenceMatcher(None, a, b).ratio()
    ta, tb = set(a.split()), set(b.split())
    nums_a, nums_b = {t for t in ta if t.isdigit()}, {t for t in tb if t.isdigit()}
    if nums_a != nums_b:
        r -= 0.25
    if ta <= tb:
        r += 0.15
    return r


def match():
    units = json.loads((OUT / "vvz_catalog.json").read_text())
    cats = json.loads((OUT / "categories.json").read_text())
    res = {}
    for c in cats:
        cand = sorted(((max(score(c["displayname"], t) for t in u["titles"]), code)
                       for code, u in units.items()), reverse=True)[:5]
        res[c["slug"]] = dict(name=c["displayname"],
                              candidates=[dict(code=k, score=round(s, 2), titles=units[k]["titles"])
                                          for s, k in cand])
    (OUT / "vvz_match.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    for slug, r in res.items():
        top = r["candidates"][0]
        print(f"{r['name'][:40]:40} {top['score']:.2f} {top['code']} {top['titles'][0][:60]}")


SECTIONS = ["Abstract", "Learning objective", "Content", "Lecture notes", "Literature",
            "Prerequisites / Notice", "Competencies", "Performance assessment",
            "Type", "Examination block", "Language of examination", "Repetition",
            "Mode of examination", "Additional information on mode of examination",
            "Written aids", "Online course materials", "Digital exam", "Admission requirement"]


def details_for(code, unit):
    sem = next(s for s in SEMS if s in unit["offerings"])  # most recent offering
    lid = unit["offerings"][sem]["id"]
    html = get(BASE + "lerneinheit.view", lerneinheitId=lid, semkez=sem, ansicht="ALLE", lang="en")
    soup = BeautifulSoup(html, "html.parser")
    fields = {}
    for tr in soup.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) == 2:
            k = tds[0].get_text(" ", strip=True)
            if k in SECTIONS and k not in fields:
                fields[k] = tds[1].get_text("\n", strip=True)
    links = sorted({a["href"] for a in soup.find_all("a", href=True)
                    if a["href"].startswith("http") and "vvz.ethz.ch" not in a["href"]
                    and not re.search(r"ethz\.ch/(de|en)\.html|floorplan|/rooms/|/studies/|lb-support|eaps\.ethz\.ch/en/studies", a["href"])})
    head = soup.get_text("\n", strip=True)
    lect = re.search(r"\nSemester\n[^\n]*\nLecturers\n(.*?)\nPeriodicity", head, re.S)
    return dict(code=code, semester=sem, url=f"{BASE}lerneinheit.view?lerneinheitId={lid}&semkez={sem}&ansicht=ALLE&lang=en",
                titles=unit["titles"], lecturers=re.sub(r"\s*\n,\s*\n?", ", ", lect.group(1)).strip() if lect else "",
                semesters_offered=sorted(unit["offerings"]), fields=fields, links=links)


def details():
    units = json.loads((OUT / "vvz_catalog.json").read_text())
    m = json.loads((OUT / "vvz_match.json").read_text())
    ov_path = Path("build/tools/vvz_overrides.json")
    ov = json.loads(ov_path.read_text()) if ov_path.exists() else {}
    for slug, r in m.items():
        codes = ov.get(slug) if slug in ov else (
            [r["candidates"][0]["code"]] if r["candidates"][0]["score"] >= 0.75 else [])
        if not codes:
            print("skip", slug); continue
        d = OUT / slug / "course"
        d.mkdir(exist_ok=True)
        info = []
        for code in codes:
            if code not in units:
                print("  missing", code); continue
            info.append(details_for(code, units[code]))
        (d / "vvz.json").write_text(json.dumps(info, indent=1, ensure_ascii=False))
        md = [f"# {r['name']} — ETH course catalogue", ""]
        for i in info:
            md += [f"## {i['code']} {i['titles'][0]}", "",
                   f"- Lecturers: {i['lecturers']}", f"- Catalogue entry ({i['semester']}): {i['url']}",
                   f"- Offered in: {', '.join(i['semesters_offered'])}", ""]
            for k, v in i["fields"].items():
                md += [f"### {k}", "", v, ""]
            if i["links"]:
                md += ["### Links", ""] + [f"- {l}" for l in i["links"]] + [""]
        (d / "COURSE.md").write_text("\n".join(md))
        print(slug, codes, flush=True)


if __name__ == "__main__":
    {"catalog": catalog, "match": match, "details": details}[sys.argv[1]]()
