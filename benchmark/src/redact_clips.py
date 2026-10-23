#!/usr/bin/env python3
"""Remove pre-printed answer hints from exam page clips (white-out, not blur).

The 2014 Kartenpraktikum sheet ships with grey italic hint values already typed
into answer boxes (094/38, 274/38, 301/74, 332°) plus a sentence explaining them.
For the vision-only benchmark these must not be visible to the model. Locations
come from the PDF's own text layer (pdftotext -bbox), so nothing is hard-coded to
pixels; box borders are kept by insetting the erase rectangle.

Usage (normally called from build_clips.py):
    python3 redact_clips.py            # re-render + redact the 2014 exam pages
"""
import re
import subprocess
import sys
from pathlib import Path
from paths import DATA, SCRAPE
from xml.etree import ElementTree as ET

from PIL import Image, ImageDraw

ROOT = SCRAPE
DPI = 150
SCALE = DPI / 72.0

HINT_RE = re.compile(r"^\d{3}/\d{2}$|^\d{2,3}°$")      # 094/38, 301/74, 332°
INSET_PX = 4                                          # keep top/bottom box border lines
BORDER_PX = 4                                         # erase through, then restore, the right border


def words(pdf: Path, page: int):
    xml = subprocess.run(["pdftotext", "-bbox", "-f", str(page), "-l", str(page),
                          str(pdf), "-"], check=True, capture_output=True, text=True).stdout
    xml = re.sub(r"<!DOCTYPE[^>]*>", "", xml)
    root = ET.fromstring(xml.replace("xmlns=", "x="))
    return [(w.text or "", float(w.get("xMin")), float(w.get("yMin")),
             float(w.get("xMax")), float(w.get("yMax"))) for w in root.iter("word")]


def hint_rects(pdf: Path, page: int):
    """Pixel rects of grey hint values (digits/° only) plus the explanatory sentence."""
    ws = words(pdf, page)
    rects = []   # (x0, y0, x1, y1, restore_border)
    for text, x0, y0, x1, y1 in ws:
        if HINT_RE.match(text):
            # erase through the right box border (the last digit overlaps it) and
            # restore the border afterwards; top/bottom stay inset to keep those lines
            rects.append((x0 * SCALE, y0 * SCALE + INSET_PX,
                          x1 * SCALE + BORDER_PX, y1 * SCALE - INSET_PX, True))
    # sentence "Die angegebenen grauen kursiven Werte sind KEINE Lösungen! ..."
    start = next((w for w in ws if w[0] == "angegebenen"), None)
    end = next((w for w in ws if w[0] == "wurde."), None)
    if start and end:
        rects.append((110, start[2] * SCALE - 6, 1130, end[4] * SCALE + 6, False))
    return rects


def redact_exam(pdf: Path, clips_dir: Path, stem: str, pages=(1, 2)):
    n = 0
    for page in pages:
        png = clips_dir / f"{stem}_p{page:02d}.png"
        im = Image.open(png).convert("RGB")
        draw = ImageDraw.Draw(im)
        for x0, y0, x1, y1, restore in hint_rects(pdf, page):
            # remember a clean row of the same box (above the text) for the border
            ref = im.crop((int(x1) - 2 * BORDER_PX, int(y0) - 10,
                           int(x1) + BORDER_PX, int(y0) - 9)) if restore else None
            draw.rectangle((x0, y0, x1, y1), fill=(255, 255, 255))
            if ref is not None:
                for yy in range(int(y0), int(y1) + 1):
                    im.paste(ref, (int(x1) - 2 * BORDER_PX, yy))
            n += 1
        im.save(png)
    return n


if __name__ == "__main__":
    pdf = ROOT / "data/kartenpraktikumi/exams/k9mytfrn.pdf/exam.pdf"   # normally run via build_clips.py
    if not pdf.exists():
        sys.exit(f"missing {pdf}")
    print("erased", redact_exam(pdf, DATA / "clips", "k9mytfrn"), "regions")
