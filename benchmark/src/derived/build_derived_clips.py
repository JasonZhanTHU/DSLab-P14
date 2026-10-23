#!/usr/bin/env python3
"""Render question-page clips for the derived tier into derived/clips/ + manifest.json.

Only QUESTION pages are rendered. The Groundwater Assessment I PDF interleaves the
lecturer's handwritten solutions (pages 3, 5, 7); those pages are skipped entirely, and the
handwritten "+ Solutions" label on its title page is erased. Requires poppler's pdftoppm + Pillow.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import DATA, SCRAPE

from PIL import Image, ImageDraw

HERE = DATA / "derived"
ROOT = SCRAPE
CLIPS = HERE / "clips"
DPI = 150

# exam_id -> (pdf relative to project root, [1-based question pages to render])
EXAMS = {
    "o62zs9b4.pdf": ("data/groundwater/exams/o62zs9b4.pdf/exam.pdf", [1, 2, 4, 6]),   # solutions on 3,5,7
    "xlixdzi0.pdf": ("data/groundwater/exams/xlixdzi0.pdf/exam.pdf", [1, 2, 3, 4]),
    "2dsr5grf.pdf": ("data/geochemiei/exams/2dsr5grf.pdf/exam.pdf", [1, 2, 3, 4]),
    "3qrh212s.pdf": ("data/geochemiei/exams/3qrh212s.pdf/exam.pdf", list(range(1, 9))),
    "lxrou8zq.pdf": ("data/geochemieii/exams/lxrou8zq.pdf/exam.pdf", list(range(1, 8))),
    "jbojruz4.pdf": ("data/geochemieii/exams/jbojruz4.pdf/exam.pdf", list(range(1, 9))),
    "r22ulkoa.pdf": ("data/geochemieii/exams/r22ulkoa.pdf/exam.pdf", list(range(1, 8))),
    # batch 2
    "2nnqx08v.pdf": ("data/geochemieii/exams/2nnqx08v.pdf/exam.pdf", list(range(1, 7))),
    "q5d0tona.pdf": ("data/geochemieii/exams/q5d0tona.pdf/exam.pdf", list(range(1, 8))),
    "2b1u4d09.pdf": ("data/geochemieii/exams/2b1u4d09.pdf/exam.pdf", list(range(1, 10))),
    "ov68rh0o.pdf": ("data/geochemieii/exams/ov68rh0o.pdf/exam.pdf", list(range(1, 8))),
    "pd1hbp2y.pdf": ("data/geochemieii/exams/pd1hbp2y.pdf/exam.pdf", list(range(1, 4))),
    "0wswu25c.pdf": ("data/geochemieii/exams/0wswu25c.pdf/exam.pdf", list(range(1, 4))),
    "o4kcl6q0.pdf": ("data/geochemieii/exams/o4kcl6q0.pdf/exam.pdf", list(range(1, 3))),
}
# (exam_id, page) -> list of pixel boxes (at 150 dpi) to white-out
ERASE = {("o62zs9b4.pdf", 2): [(800, 150, 1010, 230)]}     # handwritten "+ Solutions"


def main():
    if not shutil.which("pdftoppm"):
        sys.exit("pdftoppm not found")
    CLIPS.mkdir(exist_ok=True)
    manifest = {}
    for exam_id, (rel, pages) in EXAMS.items():
        src = ROOT / rel
        if not src.exists():
            print("SKIP", exam_id, "missing", rel, file=sys.stderr)
            continue
        stem = exam_id.replace(".pdf", "")
        out = []
        for p in pages:
            tmp = CLIPS / f"__{stem}_{p}"
            subprocess.run(["pdftoppm", "-png", "-r", str(DPI), "-f", str(p), "-l", str(p),
                            "-singlefile", str(src), str(tmp)], check=True)
            dest = CLIPS / f"{stem}_p{p:02d}.png"
            Path(str(tmp) + ".png").replace(dest)
            for box in ERASE.get((exam_id, p), []):
                im = Image.open(dest).convert("RGB")
                ImageDraw.Draw(im).rectangle(box, fill=(255, 255, 255))
                im.save(dest)
            out.append(f"clips/{dest.name}")
        manifest[exam_id] = out
        print(f"{exam_id}: {len(out)} clip(s)")
    (CLIPS / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
