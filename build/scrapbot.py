#!/usr/bin/env python3
"""Crawler for the ERFA exam collection (https://exams.erfa.ethz.ch/).

The site runs VSETH "Community Solutions" (Django JSON API behind a React SPA).
Only the category list is public; everything else needs a logged-in session.

Auth: log in via the browser, then export your cookies for exams.erfa.ethz.ch
(DevTools > Application > Cookies) as a single "name=value; name2=value2" string
and pass it with --cookies or the ERFA_COOKIES env var. The crawler refreshes the
access token itself via /api/auth/refresh while the refresh token is valid.

Output layout (resumable; existing files are skipped unless --force):
    data/categories.json
    data/<category-slug>/category.json
    data/<category-slug>/exams/<filename>/metadata.json
    data/<category-slug>/exams/<filename>/answers.json   (cuts + answers + comments)
    data/<category-slug>/exams/<filename>/exam.pdf       (with --pdfs)
    data/<category-slug>/documents/<author>__<slug>.json
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from pathlib import Path

import requests

BASE = "https://exams.erfa.ethz.ch"
SCOPE = "profile+openid"
log = logging.getLogger("scrapbot")


class Client:
    def __init__(self, cookies: str | None, delay: float):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = "scrapbot/1.0 (ERFA exam agent)"
        self.delay = delay
        self._last = 0.0
        if cookies:
            for part in cookies.split(";"):
                if "=" in part:
                    k, v = part.strip().split("=", 1)
                    self.s.cookies.set(k, v, domain="exams.erfa.ethz.ch")
        # Django CSRF cookie, required for refresh and any non-GET call.
        self._get_raw("/api/can_i_haz_csrf_cookie/")

    def _throttle(self):
        wait = self.delay - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.monotonic()

    def _headers(self):
        return {"X-CSRFToken": self.s.cookies.get("csrftoken", "")}

    def _get_raw(self, path, **kw):
        self._throttle()
        url = path if path.startswith("http") else BASE + path
        return self.s.get(url, headers=self._headers(), timeout=60, **kw)

    def refresh(self) -> bool:
        r = self._get_raw(f"/api/auth/refresh?scope={SCOPE}", allow_redirects=False)
        ok = r.status_code < 400
        log.info("token refresh -> %s", r.status_code)
        return ok

    def get(self, path, retries=3):
        """GET a JSON endpoint and return its "value" (or the whole body)."""
        for attempt in range(retries):
            r = self._get_raw(path)
            if r.status_code == 401 and attempt == 0 and self.refresh():
                continue
            if r.status_code in (429, 502, 503, 504):
                time.sleep(2 ** attempt * 5)
                continue
            if r.status_code == 404:
                return None
            r.raise_for_status()
            body = r.json()
            return body.get("value", body) if isinstance(body, dict) else body
        r.raise_for_status()

    def download(self, url, dest: Path, _retry=True):
        self._throttle()
        with self.s.get(url, stream=True, timeout=120) as r:
            if r.status_code == 401 and _retry and self.refresh():
                return self.download(url, dest, _retry=False)
            r.raise_for_status()
            tmp = dest.with_suffix(dest.suffix + ".part")
            with open(tmp, "wb") as f:
                for chunk in r.iter_content(1 << 16):
                    f.write(chunk)
            tmp.replace(dest)


def safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", str(name)).strip("_") or "_"


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


class Crawler:
    def __init__(self, client: Client, out: Path, force: bool, pdfs: bool):
        self.c, self.out, self.force, self.pdfs = client, out, force, pdfs

    def skip(self, path: Path) -> bool:
        return path.exists() and not self.force

    def run(self, only: set[str] | None):
        cats = self.c.get("/api/category/listwithmeta/") or []
        write_json(self.out / "categories.json", cats)
        log.info("%d categories", len(cats))

        me = self.c.get("/api/auth/me/")
        if not (me or {}).get("loggedin"):
            log.warning("Not logged in: only the public category list was saved. "
                        "Pass --cookies / ERFA_COOKIES to crawl exams.")
            return

        for cat in cats:
            slug = cat["slug"]
            if only and slug not in only:
                continue
            try:
                self.crawl_category(slug)
            except requests.HTTPError as e:
                log.error("category %s failed: %s", slug, e)

    def crawl_category(self, slug: str):
        cdir = self.out / safe(slug)
        meta = self.c.get(f"/api/category/metadata/{slug}/")
        exams = self.c.get(f"/api/category/listexams/{slug}/") or []
        write_json(cdir / "category.json", {"metadata": meta, "exams": exams})
        log.info("[%s] %d exams", slug, len(exams))

        for ex in exams:
            fn = ex.get("filename")
            if not fn:
                continue
            try:
                self.crawl_exam(cdir / "exams" / safe(fn), fn)
            except requests.HTTPError as e:
                log.error("exam %s failed: %s", fn, e)

        docs = self.c.get(f"/api/document/?category={slug}") or []
        for d in docs:
            author = d.get("author") or (d.get("author_user") or {}).get("username", "")
            dslug = d.get("slug")
            if not (author and dslug):
                continue
            path = cdir / "documents" / f"{safe(author)}__{safe(dslug)}.json"
            if self.skip(path):
                full = json.loads(path.read_text(encoding="utf-8"))
            else:
                full = self.c.get(f"/api/document/{author}/{dslug}/?include_comments&include_files") or d
                write_json(path, full)
            if self.pdfs:
                self.fetch_document_files(full, path.with_suffix(""))

    def fetch_document_files(self, doc: dict, ddir: Path):
        for f in doc.get("files") or []:
            fn = f.get("filename")
            if not fn:
                continue
            ext = Path(fn).suffix
            name = safe(f.get("display_name") or Path(fn).stem)
            dest = ddir / f"{f.get('order', 0):02d}_{name}{ext if not name.endswith(ext) else ''}"
            if self.skip(dest):
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                self.c.download(f"{BASE}/api/document/file/{fn}", dest)
            except requests.HTTPError as e:
                log.error("  document file %s failed: %s", fn, e)

    def crawl_exam(self, edir: Path, fn: str):
        if self.skip(edir / "metadata.json"):
            meta = json.loads((edir / "metadata.json").read_text(encoding="utf-8"))
        else:
            meta = self.c.get(f"/api/exam/metadata/{fn}/") or {}
            write_json(edir / "metadata.json", meta)

        if not self.skip(edir / "answers.json"):
            cuts = self.c.get(f"/api/exam/cuts/{fn}/") or {}
            sections = []
            # cuts: {page_number: [{oid, relHeight, name, ...}, ...]}
            for page, page_cuts in sorted(cuts.items(), key=lambda kv: int(kv[0])):
                for cut in page_cuts:
                    sec = self.c.get(f"/api/exam/answersection/{cut['oid']}/")
                    sections.append({"page": int(page), "cut": cut, "section": sec})
            write_json(edir / "answers.json", sections)
            log.info("  %s: %d answer sections", fn, len(sections))

        if self.pdfs:
            self.fetch_pdf(fn, "exam", edir / "exam.pdf")
            if meta.get("has_solution"):
                self.fetch_pdf(fn, "solution", edir / "solution.pdf")

    def fetch_pdf(self, fn: str, kind: str, dest: Path):
        if self.skip(dest):
            return
        # Returns a presigned MinIO URL for the file.
        url = self.c.get(f"/api/exam/pdf/{kind}/{fn}/")
        if isinstance(url, str) and url.startswith("http"):
            self.c.download(url, dest)
        else:
            log.warning("  %s: no %s PDF URL returned", fn, kind)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cookies", default=os.environ.get("ERFA_COOKIES"),
                    help="browser cookie string (or set ERFA_COOKIES)")
    ap.add_argument("--cookies-file", type=Path, help="file containing the cookie string")
    ap.add_argument("--out", type=Path, default=Path("data"))
    ap.add_argument("--category", action="append", help="limit to category slug (repeatable)")
    ap.add_argument("--pdfs", action="store_true", help="also download exam PDFs")
    ap.add_argument("--delay", type=float, default=1.0, help="seconds between requests")
    ap.add_argument("--force", action="store_true", help="re-fetch existing files")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()

    logging.basicConfig(level=logging.DEBUG if a.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    if a.cookies_file:
        a.cookies = a.cookies_file.read_text().strip()
    client = Client(a.cookies, a.delay)
    Crawler(client, a.out, a.force, a.pdfs).run(set(a.category) if a.category else None)


if __name__ == "__main__":
    sys.exit(main())
