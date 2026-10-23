#!/usr/bin/env python3
"""Download public lecture material (pdf/ppt/zip/ipynb...) reachable from a course web page.

  python3 build/tools/crawl_material.py <slug> <start-url> [<start-url> ...] [--depth 2] [--max-mb 80]

Stays on the start page's host and under its parent path, skips login/Moodle pages, and writes
data/<slug>/lecture_material/web/<host>/<file> plus sources.json (file -> URL, page it was linked from, link text).
"""
import argparse, json, re, time
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote

import requests
from bs4 import BeautifulSoup

EXT = re.compile(r"\.(pdf|pptx?|docx?|zip|ipynb|m|py|xlsx?|key)$", re.I)
SKIP = re.compile(r"login|moodle|shibboleth|/auth|polybox\.ethz\.ch/remote|mailto:|javascript:", re.I)
S = requests.Session()
S.headers["User-Agent"] = "scrapbot/1.0 (study material collector)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug"); ap.add_argument("urls", nargs="+")
    ap.add_argument("--depth", type=int, default=2); ap.add_argument("--max-mb", type=float, default=80)
    a = ap.parse_args()
    base = Path("data") / a.slug / "lecture_material" / "web"
    srcf = base / "sources.json"
    sources = json.loads(srcf.read_text()) if srcf.exists() else {}
    seen, queue = set(), [(u, 0) for u in a.urls]
    scopes = [(urlparse(u).netloc, urlparse(u).path.rsplit("/", 1)[0]) for u in a.urls]
    while queue:
        url, d = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        try:
            r = S.get(url, timeout=60, stream=True)
        except requests.RequestException as e:
            print("  err", url, e); continue
        ctype = r.headers.get("content-type", "")
        path = urlparse(r.url).path
        if EXT.search(path) or "pdf" in ctype or "officedocument" in ctype or "powerpoint" in ctype:
            size = int(r.headers.get("content-length") or 0)
            if size > a.max_mb * 1e6:
                print("  too big", url, size); continue
            data = r.content
            if b"<html" in data[:500].lower():
                continue  # login wall served as HTML
            name = unquote(path.rsplit("/", 1)[-1]) or "file.pdf"
            dst = base / urlparse(r.url).netloc / name
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(data)
            sources[str(dst.relative_to(base))] = sources.get(str(dst.relative_to(base)), {}) | {"url": r.url}
            print("  got", dst, len(data) // 1024, "KB", flush=True)
            continue
        if "html" not in ctype or d >= a.depth:
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        for link in soup.find_all("a", href=True):
            u = urljoin(r.url, link["href"]).split("#")[0]
            if SKIP.search(u) or not u.startswith("http"):
                continue
            p = urlparse(u)
            is_file = bool(EXT.search(p.path))
            in_scope = any(p.netloc == h and p.path.startswith(pre) for h, pre in scopes)
            if is_file or in_scope:
                if is_file:
                    key = f"{p.netloc}/{unquote(p.path.rsplit('/', 1)[-1])}"
                    sources.setdefault(key, {}).update(page=r.url, text=link.get_text(" ", strip=True)[:200])
                queue.append((u, d + 1))
        time.sleep(0.5)
    base.mkdir(parents=True, exist_ok=True)
    srcf.write_text(json.dumps(sources, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
