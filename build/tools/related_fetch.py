#!/usr/bin/env python3
"""Download open course material from other universities / open textbooks.

  python3 build/tools/related_fetch.py build/tools/related_sources.tsv [label ...]

TSV columns: label, erfa slugs (comma-sep), kind, url, filter-regex, description
kinds:  pdf       - a single file
        page      - every PDF linked from the page (matching filter, if given)
        dir       - Apache-style directory listing, recursive (matching filter)
        pressbooks- Pressbooks book: its PDF export
Output: data/_related/<label>/files/... and data/_related/<label>/meta.json
"""
import json, re, sys, time
from pathlib import Path
from urllib.parse import urljoin, unquote, urlparse

import requests
from bs4 import BeautifulSoup

S = requests.Session()
S.headers["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
ROOT = Path("data/_related")


def links(url, rx):
    r = S.get(url, timeout=60)
    soup = BeautifulSoup(r.text, "html.parser")
    for a in soup.find_all("a", href=True):
        u = urljoin(r.url, a["href"]).split("#")[0]
        if rx.search(unquote(u)):
            yield u, a.get_text(" ", strip=True)


def save(u, dst_dir, name=None):
    name = name or unquote(urlparse(u).path.rsplit("/", 1)[-1])
    if name and (dst_dir / name).exists():
        return name
    for attempt in range(4):
        try:
            r = S.get(u, timeout=600)
            break
        except requests.RequestException as e:
            print("   retry", attempt, e); time.sleep(10 * (attempt + 1))
    else:
        return None
    cd = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)', r.headers.get("content-disposition", ""))
    if not name:
        name = unquote(cd.group(1)) if cd else unquote(urlparse(r.url).path.rstrip("/").rsplit("/", 1)[-1]) + ".pdf"
    dst = dst_dir / name
    if r.status_code != 200 or b"<html" in r.content[:600].lower():
        print("   not a file:", r.status_code, u); return None
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(r.content)
    print("   got", name, len(r.content) // 1024, "KB", flush=True)
    time.sleep(0.5)
    return name


def run(label, slugs, kind, url, flt, desc):
    d = ROOT / label
    files = d / "files"
    got = []
    rx = re.compile(flt or r"\.pdf$", re.I)
    if kind == "pdf":
        got.append((save(url, files), url, ""))
    elif kind == "pressbooks":
        u = url.rstrip("/") + "/open/download?type=pdf"
        got.append((save(u, files, label + ".pdf"), u, ""))
    elif kind == "page":
        for u, t in dict(links(url, rx)).items():
            got.append((save(u, files), u, t))
    elif kind == "dir":
        todo, seen = [url], set()
        while todo:
            cur = todo.pop()
            if cur in seen:
                continue
            seen.add(cur)
            for u, t in links(cur, re.compile(r".")):
                if u.endswith("/") and u.startswith(cur) and u != cur:
                    todo.append(u)
                elif rx.search(unquote(u)) and u.startswith(url):
                    sub = unquote(u[len(url):]).rsplit("/", 1)[0] if "/" in u[len(url):] else ""
                    got.append((save(u, files / sub), u, t))
    meta = dict(label=label, erfa=slugs.split(","), kind=kind, url=url, description=desc,
                files=[dict(file=f, url=u, link_text=t) for f, u, t in got if f])
    d.mkdir(parents=True, exist_ok=True)
    (d / "meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    print("ok", label, len(meta["files"]), "files", flush=True)


def main():
    want = set(sys.argv[2:])
    for line in open(sys.argv[1]):
        if not line.strip() or line.startswith("#"):
            continue
        label, slugs, kind, url, flt, desc = (line.rstrip("\n").split("\t") + [""] * 6)[:6]
        if want and label not in want:
            continue
        print("==", label, flush=True)
        try:
            run(label, slugs, kind, url, flt, desc)
        except Exception as e:
            print("fail", label, e, flush=True)


if __name__ == "__main__":
    main()
