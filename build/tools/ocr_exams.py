#!/usr/bin/env python3
"""OCR the scanned exam PDFs: data/<slug>/exams/<id>.pdf -> data/<slug>/exams/<id>.txt.
Uses the text layer when there is one, else EasyOCR (de+en, GPU). Resumable."""
import glob, subprocess, sys, tempfile, os
from pathlib import Path

def text_layer(pdf):
    return subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout

def main():
    pdfs = sorted(glob.glob(sys.argv[1] if len(sys.argv) > 1 else "data/*/exams/*.pdf"))
    reader = None
    for pdf in pdfs:
        dst = Path(pdf).with_suffix(".txt")
        if dst.exists():
            continue
        t = text_layer(pdf)
        if len(t.strip()) > 200:
            dst.write_text(t); print("text", pdf, flush=True); continue
        if reader is None:
            import easyocr
            reader = easyocr.Reader(["de", "en"], gpu=True)
        with tempfile.TemporaryDirectory() as td:
            subprocess.run(["pdftoppm", "-r", "200", "-png", pdf, f"{td}/p"], check=True)
            pages = []
            for i, png in enumerate(sorted(glob.glob(f"{td}/p*.png")), 1):
                lines = reader.readtext(png, detail=0, paragraph=True)
                pages.append(f"--- page {i} ---\n" + "\n".join(lines))
        dst.write_text("\n\n".join(pages)); print("ocr ", pdf, len(pages), "pages", flush=True)

if __name__ == "__main__":
    main()
