#!/usr/bin/env python3
"""Render every QUESTION page of the 6 benchmark exams into clips/ and write
clips/manifest.json (exam_id -> ordered list of page-image paths).

Clips are the input for the *vision-only* benchmark mode (run_model.py --clips):
the model sees these page images and NO transcribed text. Solution PDFs are never
rendered. Requires poppler's `pdftoppm`.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path
from paths import DATA, SCRAPE

ROOT = SCRAPE
CLIPS = DATA / "clips"
DPI = 150
# exams whose sheet carries pre-printed answer hints that must not reach the model
REDACT = {"k9mytfrn.pdf", "ja9djbrh.pdf"}

# exam_id -> exam.pdf relative to project root
EXAMS = {
    "bfyvac29.pdf": "data/physikiii/exams/bfyvac29.pdf/exam.pdf",
    "m0kj6fp1.pdf": "data/mathematikiii/exams/m0kj6fp1.pdf/exam.pdf",
    "pifr77kc.pdf": "data/mathematikiii_0/exams/pifr77kc.pdf/exam.pdf",
    "s475u9b8.pdf": "data/metamorphoseundmagmatismusii/exams/s475u9b8.pdf/exam.pdf",
    "k9mytfrn.pdf": "data/kartenpraktikumi/exams/k9mytfrn.pdf/exam.pdf",
    "ja9djbrh.pdf": "data/kartenpraktikumi/exams/ja9djbrh.pdf/exam.pdf",
}


def main():
    if not shutil.which("pdftoppm"):
        sys.exit("pdftoppm not found — install poppler-utils.")
    CLIPS.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for exam_id, rel in EXAMS.items():
        src = ROOT / rel
        stem = exam_id.replace(".pdf", "")
        if not src.exists():
            print(f"SKIP {exam_id}: {rel} missing", file=sys.stderr)
            continue
        for old in CLIPS.glob(f"{stem}_p*.png"):
            old.unlink()
        subprocess.run(["pdftoppm", "-png", "-r", str(DPI), str(src),
                        str(CLIPS / f"{stem}_p")], check=True)
        # pdftoppm names them <stem>_p-1.png, -2, ...; normalise to _pNN.png
        pages = sorted(CLIPS.glob(f"{stem}_p-*.png"),
                       key=lambda p: int(p.stem.rsplit("-", 1)[1]))
        rel_pages = []
        for i, p in enumerate(pages, 1):
            dest = CLIPS / f"{stem}_p{i:02d}.png"
            p.replace(dest)
            rel_pages.append(f"clips/{dest.name}")
        manifest[exam_id] = rel_pages
        print(f"{exam_id}: {len(rel_pages)} page clip(s)")
        if exam_id in REDACT:   # strip pre-printed hint values from the sheet
            import redact_clips
            n = redact_clips.redact_exam(src, CLIPS, stem)
            print(f"  redacted {n} pre-filled hint region(s)")
    (CLIPS / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {CLIPS/'manifest.json'}")


if __name__ == "__main__":
    main()
