#!/usr/bin/env python3
"""Turn the scraped Wikipedia references in data/*/references/ into an
agent-friendly study pack in study/. Local only, no network.

Layout produced:
  study/INDEX.md                  # all courses -> where to look
  study/index.json                # same, machine-readable (articles, sections, leads)
  study/<slug>/README.md          # course guide: each article, 1-line definition, section outline
  study/<slug>/GLOSSARY.md        # term -> defining first sentence (quick lookup)
  study/<slug>/articles/NN_Title.md   # clean article: markdown headings, no ref/link boilerplate
  study/<slug>/ALL.md             # all articles of the course concatenated (for one-shot reading)

Usage:
  python3 build_study.py
"""

import json
import re
import shutil
from pathlib import Path

from wiki2text import wiki_to_text

OUT = Path("data")
STUDY = Path("study")
DROP_SECTIONS = {"references", "further reading", "external links", "see also", "notes",
                 "bibliography", "sources", "citations", "footnotes", "literature",
                 "notes and references", "references and notes", "general references",
                 "cited sources", "works cited", "explanatory notes"}


def to_markdown(wikitext: str):
    """Wikitext -> (markdown body, [(level, heading)]) with boilerplate sections dropped."""
    # Protect headings from wiki_to_text, which flattens them.
    w = re.sub(r"(?m)^\s*(={2,6})\s*(.*?)\s*\1\s*$",
               lambda m: f"\n@@H{len(m.group(1))}@@{m.group(2)}\n", wikitext)
    text = wiki_to_text(w)
    out, sections, skip_level = [], [], None
    for line in text.splitlines():
        m = re.match(r"@@H(\d)@@(.*)", line.strip())
        if m:
            level, head = int(m.group(1)), re.sub(r"<[^>]+>|'{2,}", "", m.group(2)).strip()
            if skip_level is not None and level > skip_level:
                continue
            skip_level = level if head.lower() in DROP_SECTIONS else None
            if skip_level is None:
                sections.append((level, head))
                out.append("#" * level + " " + head)
            continue
        if skip_level is None:
            out.append(line)
    body = "\n".join(out)
    body = re.sub(r"(?m)^\s*(-\s*)+$", "", body)          # empty list markers
    body = re.sub(r"(?m)^(#+ .*)\n+(?=#+ |\Z)", "", body)  # headings left empty
    body = re.sub(r"\n{3,}", "\n\n", body).strip() + "\n"
    return body, [s for s in sections if f"{'#' * s[0]} {s[1]}" in body]


def lead_sentence(body: str) -> str:
    para = next((p for p in body.split("\n\n") if p.strip() and not p.startswith("#")
                 and len(p) > 60), "")
    para = re.sub(r"\s+", " ", re.sub(r"\([^()]*\)", "", para)).strip()
    m = re.match(r"(.{40,400}?[.!?])(?:\s+[A-Z]|$)", para)
    return (m.group(1) if m else para[:300]).replace(" ,", ",").replace("  ", " ")


def safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_")[:80]


def build_course(cat: Path, title: str):
    idx = json.loads((cat / "references" / "index.json").read_text())
    dst = STUDY / cat.name
    (dst / "articles").mkdir(parents=True)
    arts = []
    for e in sorted(idx.get("entries", []), key=lambda e: e.get("order", 99)):
        src = cat / "references" / e["file"]
        if not src.exists():
            continue
        body, sections = to_markdown(src.read_text(encoding="utf-8", errors="replace"))
        if len(body) < 300:  # disambiguation / stub pages
            continue
        fn = f"{e.get('order', 0):02d}_{safe(e['title'])}.md"
        (dst / "articles" / fn).write_text(
            f"# {e['title']}\n\n> Source: {e.get('url', '')} — reference for course *{title}*\n\n{body}")
        arts.append(dict(title=e["title"], file=f"articles/{fn}", url=e.get("url", ""),
                         words=len(body.split()), main=e.get("order") == 0,
                         lead=lead_sentence(body),
                         sections=[h for lvl, h in sections if lvl == 2]))
    if not arts:
        shutil.rmtree(dst)
        return None

    with open(dst / "ALL.md", "w") as fh:
        for a in arts:
            fh.write((dst / a["file"]).read_text() + "\n\n---\n\n")

    L = [f"# {title} — reference guide", "",
         f"Course slug `{cat.name}`. Wikipedia search term: *{idx.get('search_term', '')}*. "
         f"{len(arts)} articles, ~{sum(a['words'] for a in arts) // 1000}k words.", "",
         "Article 00 is the main topic article; the others were auto-picked from its links, "
         "so some are tangential — use the one-line definitions to judge relevance.", "",
         "- Quick definitions: [GLOSSARY.md](GLOSSARY.md)",
         "- Everything in one file: [ALL.md](ALL.md)", "",
         "## Articles", ""]
    for a in arts:
        L += [f"### [{a['title']}]({a['file']}){' — MAIN' if a['main'] else ''}",
              f"{a['lead']}", "",
              f"*{a['words']} words.* Sections: {', '.join(a['sections']) or '—'}", ""]
    (dst / "README.md").write_text("\n".join(L))
    G = [f"# {title} — glossary", ""] + [f"- **{a['title']}**: {a['lead']}"
                                          for a in sorted(arts, key=lambda a: a["title"].lower())]
    (dst / "GLOSSARY.md").write_text("\n".join(G) + "\n")
    return dict(slug=cat.name, title=title, search_term=idx.get("search_term", ""),
                main_article=idx.get("main_article", ""), articles=arts)


def main():
    if STUDY.exists():
        shutil.rmtree(STUDY)
    STUDY.mkdir()
    names = {c["slug"]: c["displayname"] for c in json.loads((OUT / "categories.json").read_text())}
    courses = [c for d in sorted(OUT.iterdir())
               if (d / "references" / "index.json").exists()
               and (c := build_course(d, names.get(d.name, d.name)))]
    courses.sort(key=lambda c: c["title"].lower())
    (STUDY / "index.json").write_text(json.dumps(courses, indent=1, ensure_ascii=False))

    L = ["# Study reference pack — index", "",
         "Wikipedia background material per course, cleaned for reading by an agent "
         "(generated by `build_study.py` from `data/*/references/`).", "",
         "## How to use",
         "1. Find the course below and open its `README.md`: every article with a one-line "
         "definition and its section list.",
         "2. Open only the articles you need under `articles/` (markdown with headings, so you can jump to a section),",
         "   or `GLOSSARY.md` for quick definitions, or `ALL.md` to read everything at once.",
         "3. This is general encyclopedia content, not course material: check notation and "
         "conventions against the exam's wording.", "",
         "## Courses", "",
         "| Course | Guide | Main article | Articles | Words |", "|---|---|---|---|---|"]
    for c in courses:
        L.append(f"| {c['title']} | [{c['slug']}/README.md]({c['slug']}/README.md) | "
                 f"{c['main_article']} | {len(c['articles'])} | "
                 f"{sum(a['words'] for a in c['articles']) // 1000}k |")
    (STUDY / "INDEX.md").write_text("\n".join(L) + "\n")
    print(f"{len(courses)} courses, {sum(len(c['articles']) for c in courses)} articles -> {STUDY}/")


if __name__ == "__main__":
    main()
