#!/usr/bin/env python3
"""Regenerate benchmark/figures/*.png from the source exam PDFs in ../out.

Figures are page renders of the original exam PDFs (phase diagrams, the
geological maps, and the self-contained physics problem pages). Run this if the
figures are missing or you change the DPI. Requires poppler's `pdftoppm`.
"""
import shutil
import subprocess
import sys
from pathlib import Path
from paths import DATA, SCRAPE

ROOT = SCRAPE                          # project root (contains data/)
FIG = DATA / "figures"

# (output stem, source pdf relative to project root, page, dpi)
JOBS = [
    ("metamorph_figP1_1", "data/metamorphoseundmagmatismusii/exams/s475u9b8.pdf/exam.pdf", 2, 160),
    ("metamorph_figP2_1", "data/metamorphoseundmagmatismusii/exams/s475u9b8.pdf/exam.pdf", 5, 160),
    ("karten2014_map",    "data/kartenpraktikumi/exams/k9mytfrn.pdf/exam.pdf",              3, 160),
    ("karten2013_map",    "data/kartenpraktikumi/exams/ja9djbrh.pdf/exam.pdf",              3, 160),
    ("physik_p1",         "data/physikiii/exams/bfyvac29.pdf/exam.pdf",                     1, 140),
    ("physik_p2",         "data/physikiii/exams/bfyvac29.pdf/exam.pdf",                     2, 140),
    ("physik_p3",         "data/physikiii/exams/bfyvac29.pdf/exam.pdf",                     3, 140),
    ("physik_p4",         "data/physikiii/exams/bfyvac29.pdf/exam.pdf",                     4, 140),
    ("physik_p5",         "data/physikiii/exams/bfyvac29.pdf/exam.pdf",                     5, 140),
]


def main():
    if not shutil.which("pdftoppm"):
        sys.exit("pdftoppm not found — install poppler-utils.")
    FIG.mkdir(parents=True, exist_ok=True)
    for stem, rel, page, dpi in JOBS:
        src = ROOT / rel
        if not src.exists():
            print(f"SKIP {stem}: source missing ({rel})", file=sys.stderr)
            continue
        prefix = FIG / f"__tmp_{stem}"
        subprocess.run(["pdftoppm", "-png", "-r", str(dpi), "-f", str(page), "-l", str(page),
                        str(src), str(prefix)], check=True)
        # pdftoppm appends -<page>; move to the clean name
        produced = sorted(FIG.glob(f"__tmp_{stem}-*.png"))
        if not produced:
            print(f"FAIL {stem}: pdftoppm produced nothing", file=sys.stderr)
            continue
        produced[0].replace(FIG / f"{stem}.png")
        for extra in produced[1:]:
            extra.unlink()
        print(f"wrote figures/{stem}.png  (p{page} of {rel}, {dpi} dpi)")


if __name__ == "__main__":
    main()
