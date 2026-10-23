#!/usr/bin/env python3
"""Fetch MIT OpenCourseWare courses (CC BY-NC-SA) and keep only their documents.

  python3 build/tools/ocw_fetch.py <ocw-course-url> [...]

Each course goes to data/_related/MIT_OCW/<course-slug>/ with
  files/<pdf|py|m|ipynb...>   documents extracted from the course zip (videos/html dropped)
  INDEX.md                    title, description, and every document with its title and section
"""
import io, json, re, sys, tempfile, zipfile
from pathlib import Path
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

KEEP = re.compile(r"\.(pdf|py|m|ipynb|txt|csv|dat|xlsx?|zip)$", re.I)
S = requests.Session()
S.headers["User-Agent"] = "scrapbot/1.0 (study material collector)"
ROOT = Path("data/_related/MIT_OCW")


def meta_from_zip(z):
    """Map resource file name -> (section, description) from resources/*/data.json in the zip."""
    out = {}
    for name in z.namelist():
        if name.startswith("resources/") and name.endswith("/data.json"):
            d = json.loads(z.read(name))
            fn = (d.get("file") or "").rsplit("/", 1)[-1]
            if fn:
                out[fn] = (d.get("parent_title") or ", ".join(d.get("learning_resource_types") or []) or "Other",
                           re.sub(r"\s+", " ", d.get("description") or d.get("title") or "").strip())
    return out


def clean(fn):
    return re.sub(r"^[0-9a-f]{32}_", "", fn)


def fetch(url):
    url = url.rstrip("/") + "/"
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    dst = ROOT / slug
    if (dst / "INDEX.md").exists():
        print("skip", slug); return
    page = S.get(url + "download/", timeout=60).text
    m = re.search(r'href="([^"]+\.zip)"', page)
    if not m:
        print("no zip", slug); return
    info = BeautifulSoup(S.get(url, timeout=60).text, "html.parser")
    title = (info.find("title").get_text(strip=True).split("|")[0].strip()) if info.find("title") else slug
    desc = info.find("meta", attrs={"name": "description"})
    desc = desc["content"] if desc else ""
    with tempfile.TemporaryFile() as tmp:
        with S.get(m.group(1), stream=True, timeout=600) as r:
            for chunk in r.iter_content(1 << 20):
                tmp.write(chunk)
        size = tmp.tell(); tmp.seek(0)
        z = zipfile.ZipFile(tmp)
        meta = meta_from_zip(z)
        (dst / "files").mkdir(parents=True, exist_ok=True)
        kept = []
        for zi in z.infolist():
            fn = zi.filename.rsplit("/", 1)[-1]
            if not KEEP.search(fn) or zi.file_size > 80e6 or fn.lower().endswith(".zip") and zi.file_size > 20e6:
                continue
            sec = re.sub(r"[^A-Za-z0-9]+", "_", meta.get(fn, ("Other", ""))[0]).strip("_") or "Other"
            (dst / "files" / sec).mkdir(parents=True, exist_ok=True)
            (dst / "files" / sec / clean(fn)).write_bytes(z.read(zi))
            kept.append((sec, clean(fn), meta.get(fn, ("", ""))[1]))
    L = [f"# {title}", "", f"Source: {url} (MIT OpenCourseWare, CC BY-NC-SA 4.0)", "", desc, "",
         f"{len(kept)} documents (zip was {size // 1_000_000} MB; videos and HTML dropped).", "",
         "| Section | File | Description |", "|---|---|---|"]
    for sec, fn, d in sorted(kept):
        L.append(f"| {sec} | [{fn}](files/{sec}/{fn.replace(' ', '%20')}) | {d.replace('|', '/')[:200]} |")
    (dst / "INDEX.md").write_text("\n".join(L) + "\n")
    json.dump(dict(url=url, title=title, description=desc, files=[f'{a}/{b}' for a, b, _ in kept]), open(dst / "meta.json", "w"), indent=1)
    print("ok", slug, len(kept), "docs", size // 1_000_000, "MB", flush=True)


if __name__ == "__main__":
    for u in sys.argv[1:]:
        try:
            fetch(u)
        except Exception as e:
            print("fail", u, e, flush=True)
