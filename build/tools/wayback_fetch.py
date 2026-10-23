#!/usr/bin/env python3
"""Download archived course files from the Wayback Machine.

  python3 build/tools/wayback_fetch.py <rules.tsv> <cdx-list> [<cdx-list> ...]

rules.tsv: "<slug>\t<url-regex>\t<subdir>" per line. Each CDX line is "<url> <timestamp> <length>";
the first matching rule wins. Files go to data/<slug>/lecture_material/wayback/<subdir>/ with sources.json
recording the original URL and the snapshot used.
"""
import json, re, sys, time
from pathlib import Path
from urllib.parse import unquote

import requests

S = requests.Session()
S.headers["User-Agent"] = "scrapbot/1.0 (study material collector)"


def main():
    rules = [l.rstrip("\n").split("\t") for l in open(sys.argv[1]) if l.strip() and not l.startswith("#")]
    rules = [(s, re.compile(r, re.I), d) for s, r, d in rules]
    seen = set()
    for lst in sys.argv[2:]:
        for line in open(lst):
            parts = line.split()
            if len(parts) < 2:
                continue
            url, ts = parts[0].replace(":80/", "/"), parts[1]
            key = re.sub(r"^https?://(www\.)?", "", url)
            if key in seen:
                continue
            for slug, rx, sub in rules:
                if rx.search(url):
                    seen.add(key)
                    dst_dir = Path("data") / slug / "lecture_material" / "wayback" / sub
                    name = unquote(url.rstrip("/").rsplit("/", 1)[-1])
                    if not name.lower().endswith(".pdf"):
                        name += ".pdf"
                    dst = dst_dir / name
                    if dst.exists():
                        break
                    snap = f"https://web.archive.org/web/{ts}id_/{url}"
                    for attempt in range(4):
                        try:
                            r = S.get(snap, timeout=120)
                            if r.status_code == 200:
                                break
                        except requests.RequestException:
                            pass
                        time.sleep(5 * (attempt + 1))
                    else:
                        print("  fail", url); break
                    if r.content[:4] != b"%PDF":
                        print("  not pdf", url); break
                    dst_dir.mkdir(parents=True, exist_ok=True)
                    dst.write_bytes(r.content)
                    sf = dst_dir / "sources.json"
                    src = json.loads(sf.read_text()) if sf.exists() else {}
                    src[name] = dict(original=url, snapshot=snap)
                    sf.write_text(json.dumps(src, indent=1))
                    print("  got", dst, len(r.content) // 1024, "KB", flush=True)
                    time.sleep(1)
                    break


if __name__ == "__main__":
    main()
