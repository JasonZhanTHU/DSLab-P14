#!/usr/bin/env python3
"""Write data/<slug>/RELATED.md (courses on the same topics at other universities) and data/_related/README.md.

Inputs: build/tools/ocw_map.tsv, data/_related/MIT_OCW/*/meta.json, data/_related/<label>/meta.json, build/tools/related_links.tsv
"""
import collections, json, os, re
from pathlib import Path

OUT = Path("data")
REL = OUT / "_related"


def ocw_number(slug):
    m = re.match(r"((?:res-)?\d+-[\dA-Za-z]+?)-", slug)
    return m.group(1).replace("-", ".", 1).upper() if m else slug


def ocw_term(slug):
    m = re.search(r"-(spring|fall|summer|january-iap)-(\d{4})$", slug)
    return f"{m.group(1).replace('january-iap', 'IAP').title()} {m.group(2)}" if m else ""


TITLES = {
    "stull_practical_meteorology": "UBC: R. Stull, Practical Meteorology (open textbook)",
    "waldron_snyder_geological_structures": "U Alberta: Waldron & Snyder, Geological Structures: a Practical Introduction (open textbook)",
    "earle_physical_geology": "BCcampus: S. Earle, Physical Geology 2nd ed. (open textbook)",
    "hoek_practical_rock_engineering": "E. Hoek, Practical Rock Engineering (free full text)",
    "verruijt_soil_mechanics": "TU Delft: A. Verruijt, Soil Mechanics (screen book)",
    "unibas_geology_slides": "Uni Basel: Geologie der Schweiz, Strukturgeologie (with exam + solutions), deformation mechanisms (slides)",
    "uw_ess431_glaciology": "U Washington ESS 431: Principles of Glaciology (lectures 2018)",
    "lmu_igel_seismology": "LMU Munich (H. Igel): Seismology lectures",
    "lmu_igel_applied_geophysics": "LMU Munich (H. Igel): Angewandte Geophysik I (German slides + exercises)",
    "lmu_igel_intro_geophysics": "LMU Munich (H. Igel): Einführung in die Geophysik",
    "lmu_igel_numerical_methods": "LMU Munich (H. Igel): Numerical methods in geophysics",
    "uhh_seismische_wellen": "Uni Hamburg: Seismische Wellen (German lecture manuscript)",
    "cornell_cathles_mineral_resources": "Cornell (L. Cathles): Mineral and Energy Resources of the Earth (lectures)",
    "cornell_cathles_geochemistry": "Cornell (L. Cathles): Geochemistry lectures",
    "cornell_cathles_geohydrology": "Cornell (L. Cathles): Geohydrology lectures",
    "cornell_cathles_fluid_dynamics_solid_earth": "Cornell (L. Cathles): Fluid Dynamics of the Solid Earth (lectures)",
    "cornell_cathles_how_the_earth_works": "Cornell (L. Cathles): How the Earth Works",
    "cornell_white_geochemistry_1996": "Cornell: W. M. White, Geochemistry (free draft chapters)",
    "cornell_white_isotope_geochemistry_656_2003": "Cornell Geo 656: W. M. White, Isotope Geochemistry lecture notes (2003)",
    "fub_leinfelder_ind_org": "FU Berlin / LMU (R. Leinfelder): Paläontologie teaching material (German)",
    "fub_leinfelder_ind_riffe": "FU Berlin / LMU (R. Leinfelder): Riffe / reefs teaching material (German)",
}


def section_summary(files):
    c = collections.Counter(f.split("/", 1)[0].replace("_", " ") for f in files)
    return ", ".join(f"{n} {s.lower()}" for s, n in c.most_common())


def main():
    names = {c["slug"]: c["displayname"] for c in json.loads((OUT / "categories.json").read_text())}
    per = collections.defaultdict(lambda: dict(mit=[], other=[], links=[]))
    overview = []

    for line in open("build/tools/ocw_map.tsv"):
        if line.startswith("#") or not line.strip():
            continue
        slugs, ocw = line.rstrip("\n").split("\t")
        mf = REL / "MIT_OCW" / ocw / "meta.json"
        if not mf.exists():
            continue
        m = json.loads(mf.read_text())
        has_exams = any(re.search(r"exam", f, re.I) for f in m["files"])
        entry = dict(title=f"MIT {ocw_number(ocw)} {m['title']} ({ocw_term(ocw)})", url=m["url"],
                     desc=" ".join(m["description"].split()), contents=section_summary(m["files"]), exams=has_exams,
                     path=f"../_related/MIT_OCW/{ocw}/INDEX.md", n=len(m["files"]))
        for s in slugs.split(","):
            per[s]["mit"].append(entry)
        overview.append((entry["title"], entry["n"], f"MIT_OCW/{ocw}/INDEX.md", slugs.split(",")))

    for d in sorted(REL.iterdir()):
        mf = d / "meta.json"
        if d.name == "MIT_OCW" or not mf.exists():
            continue
        m = json.loads(mf.read_text())
        files = [f for f in m["files"] if f.get("file")]
        if not files:
            continue
        title = (f"Groundwater Project: {d.name[len('gwproject_'):].replace('-', ' ').capitalize()}"
                 if d.name.startswith("gwproject_") else TITLES.get(d.name, d.name))
        # per-source file index
        L = [f"# {title}", "", m["description"], "", f"Source: {m['url']}", "", "| File | Link text |", "|---|---|"]
        for f in files:
            p = f["file"] if (d / "files" / f["file"]).exists() else next(
                (str(q.relative_to(d / "files")) for q in (d / "files").rglob(os.path.basename(f["file"]))), f["file"])
            L.append(f"| [{p}](files/{p.replace(' ', '%20')}) | {f.get('link_text', '')[:120]} |")
        (d / "INDEX.md").write_text("\n".join(L) + "\n")
        entry = dict(title=title, url=m["url"], desc=m["description"], n=len(files), path=f"../_related/{d.name}/INDEX.md")
        for s in m["erfa"]:
            per[s]["other"].append(entry)
        overview.append((title, len(files), f"{d.name}/INDEX.md", m["erfa"]))

    for line in open("build/tools/related_links.tsv"):
        if line.startswith("#") or not line.strip():
            continue
        slugs, title, url, note = line.rstrip("\n").split("\t")
        for s in slugs.split(","):
            per[s]["links"].append(dict(title=title, url=url, note=note))

    for s, r in per.items():
        if not (OUT / s).is_dir():
            continue
        name = names.get(s, s)
        L = [f"# {name} — related courses at other universities", "",
             "Open material on the same topics from other universities and open textbooks, "
             "chosen to match the exam topics in [EXAM_TOPICS.md](EXAM_TOPICS.md). "
             "Use it for extra explanations and practice problems; notation and depth differ from the ETH course.", ""]
        if r["mit"]:
            L += ["## MIT OpenCourseWare (CC BY-NC-SA)", ""]
            for e in sorted(r["mit"], key=lambda e: not e["exams"]):
                L += [f"- **[{e['title']}]({e['path']})**{' — includes exams' if e['exams'] else ''}",
                      f"  {e['desc']}", f"  Contents: {e['contents']}. Online: {e['url']}", ""]
        if r["other"]:
            L += ["## Other universities and open textbooks", ""]
            for e in r["other"]:
                L += [f"- **[{e['title']}]({e['path']})** ({e['n']} file{'s' if e['n'] != 1 else ''})", f"  {e['desc']}", f"  Source: {e['url']}", ""]
        if r["links"]:
            L += ["## Online only", ""] + [f"- [{e['title']}]({e['url']}): {e['note']}" for e in r["links"]] + [""]
        (OUT / s / "RELATED.md").write_text("\n".join(L))

    O = ["# Related courses from other universities", "",
         "Open course material on the topics of the ERFA courses. Each course folder has a `RELATED.md` "
         "that lists the relevant sources below.", "",
         "| Source | Files | Used by |", "|---|---|---|"]
    for title, n, path, slugs in sorted(overview):
        O.append(f"| [{title}]({path}) | {n} | {', '.join(names.get(x, x) for x in slugs)} |")
    (REL / "README.md").write_text("\n".join(O) + "\n")
    print(len(per), "courses with RELATED.md;", len(overview), "sources")


if __name__ == "__main__":
    main()
