#!/usr/bin/env python3
"""Reference-lookup tools over the Wikipedia study pack (study/, built by
build_study.py), exposed as tools any agent can call (Anthropic tool schemas in TOOLS,
dispatcher RefLibrary.call, CLI below, MCP server in ref_mcp.py).

The pack contains only encyclopedia articles — no exams, no solutions — so giving
these tools to a model under test does not leak answers.

Tools (results are capped so a call costs at most a few k tokens):
  search_references(query, course?, k?)   BM25 over article *sections* -> ranked refs + snippets
  read_reference(ref, offset?)            one section (or a whole article) by ref
  list_course_references(course)          a course's articles with 1-line definitions

Refs look like "physikiii/05_Momentum.md#Conservation" (section) or
"physikiii/05_Momentum.md" (article).

CLI for trying it out:
  python3 ref_tools.py search "lever rule phase diagram"
  python3 ref_tools.py read "metamorphoseundmagmatismusii/00_Igneous_rock.md#Classification"
  python3 ref_tools.py list kartenpraktikumi
"""
import json
import math
import pickle
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

STUDY = Path(__file__).resolve().parent.parent / "study"
READ_CHARS = 6000      # max chars returned per read_reference call
SNIPPET_CHARS = 280
MAX_K = 10

TOOLS = [
    {
        "name": "search_references",
        "description": (
            "Full-text search over a library of ~1000 English Wikipedia articles covering "
            "earth sciences, physics, chemistry and mathematics (split into sections). Use it to "
            "look up definitions, formulas, constants or background you are unsure of. Write the "
            "query in ENGLISH keywords (translate German exam terms first, e.g. 'Hebelgesetz' -> "
            "'lever rule'). Returns ranked section refs with short snippets; open one with "
            "read_reference. Searches all courses unless `course` is given."),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "English keywords, e.g. 'centripetal force loop'"},
                "course": {"type": "string", "description": "Optional course slug to restrict to, e.g. 'physikiii'"},
                "k": {"type": "integer", "description": f"Number of results (default 5, max {MAX_K})"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "read_reference",
        "description": (
            f"Read the text of a section or article returned by search_references (ref like "
            f"'physikiii/05_Momentum.md#Conservation', or without '#…' for the whole article). "
            f"Returns at most {READ_CHARS} characters; if truncated, call again with the given "
            f"`offset` to continue. Formulas are in LaTeX."),
        "input_schema": {
            "type": "object",
            "properties": {
                "ref": {"type": "string"},
                "offset": {"type": "integer", "description": "Character offset to continue from (default 0)"},
            },
            "required": ["ref"],
        },
    },
    {
        "name": "list_course_references",
        "description": (
            "List the reference articles collected for one course: ref, title, one-line "
            "definition and section names. Useful to browse what background is available."),
        "input_schema": {
            "type": "object",
            "properties": {"course": {"type": "string", "description": "Course slug, e.g. 'mathematikiii'"}},
            "required": ["course"],
        },
    },
]

_TOKEN = re.compile(r"[a-z0-9]+")
_STOP = set("the a an of and or in on to for is are was were be by with as at from that this which "
            "it its into can also such these those has have had not but".split())


def _tokens(s):
    return [t for t in _TOKEN.findall(s.lower()) if t not in _STOP and len(t) > 1]


class RefLibrary:
    def __init__(self, root: Path = STUDY):
        if not (root / "index.json").exists():
            raise FileNotFoundError(f"{root}/index.json missing — run build_study.py first")
        self.root = root
        self.courses = {c["slug"]: c for c in json.loads((root / "index.json").read_text())}
        cache = root / ".ref_index.pkl"   # one file loads much faster than ~1000 articles
        stamp = (root / "index.json").stat().st_mtime
        try:
            cached = pickle.loads(cache.read_bytes())
            assert cached["stamp"] == stamp
            self.sections, self.tf, self.df = cached["sections"], cached["tf"], cached["df"]
        except Exception:
            self.sections = []          # (ref, course, title, heading, text)
            self.tf, self.df = [], Counter()
            for slug, c in self.courses.items():
                for a in c["articles"]:
                    self._add_article(slug, a)
            try:
                cache.write_bytes(pickle.dumps({"stamp": stamp, "sections": self.sections,
                                                "tf": self.tf, "df": self.df}))
            except OSError:
                pass
        self.avgdl = sum(sum(t.values()) for t in self.tf) / max(len(self.tf), 1)
        self.postings = defaultdict(list)
        for i, tf in enumerate(self.tf):
            for t in tf:
                self.postings[t].append(i)

    def _add_article(self, slug, a):
        text = (self.root / slug / a["file"]).read_text(encoding="utf-8")
        art_ref = f"{slug}/{Path(a['file']).name}"
        # split at ##/### headings; the lead (before the first heading) is its own section
        parts = re.split(r"(?m)^(#{2,6}) (.+)$", text)
        chunks = [("", parts[0])] + [(parts[i + 1].strip(), parts[i + 2]) for i in range(1, len(parts) - 2, 3)]
        for head, body in chunks:
            body = re.sub(r"^# .*\n+(> Source:.*\n+)?", "", body).strip()
            if len(body) < 80:
                continue
            ref = art_ref + (f"#{head}" if head else "")
            # title and heading count double: they are the strongest relevance signal
            tf = Counter(_tokens(body) + _tokens(a["title"] + " " + head) * 2)
            self.sections.append((ref, slug, a["title"], head or "(introduction)", body))
            self.tf.append(tf)
            self.df.update(tf.keys())

    def search(self, query, course=None, k=5):
        k = max(1, min(int(k or 5), MAX_K))
        if course and course not in self.courses:
            return {"error": f"unknown course '{course}'", "courses": sorted(self.courses)}
        q = _tokens(query)
        if not q:
            return {"error": "empty query"}
        N, scores = len(self.tf), defaultdict(float)
        for t in set(q):
            idf = math.log(1 + (N - self.df[t] + 0.5) / (self.df[t] + 0.5)) if self.df[t] else 0
            for i in self.postings.get(t, ()):
                if course and self.sections[i][1] != course:
                    continue
                f, dl = self.tf[i][t], sum(self.tf[i].values())
                scores[i] += idf * f * 2.2 / (f + 1.2 * (0.25 + 0.75 * dl / self.avgdl))
        hits, seen = [], set()
        for i in sorted(scores, key=scores.get, reverse=True):
            ref, slug, title, head, body = self.sections[i]
            key = (title, head)          # same article is often collected under several courses
            if key in seen:
                continue
            seen.add(key)
            hits.append({"ref": ref, "article": title, "section": head,
                         "score": round(scores[i], 2), "snippet": _snippet(body, q)})
            if len(hits) == k:
                break
        return {"query": query, "results": hits} if hits else {"query": query, "results": [],
                                                              "hint": "no match — try other English keywords"}

    def read(self, ref, offset=0):
        path, _, head = ref.partition("#")
        slug, _, fname = path.partition("/")
        f = self.root / slug / "articles" / fname
        if not fname or not f.resolve().is_relative_to(self.root.resolve()) or not f.exists():
            return {"error": f"unknown ref '{ref}' — use a ref returned by search_references"}
        if head:
            sec = next((s for s in self.sections if s[0] == ref), None)
            if not sec:
                return {"error": f"section '{head}' not found in {path}"}
            text = f"## {head}\n\n{sec[4]}"
        else:
            text = f.read_text(encoding="utf-8")
        offset = max(0, int(offset or 0))
        chunk = text[offset:offset + READ_CHARS]
        out = {"ref": ref, "text": chunk}
        if offset + READ_CHARS < len(text):
            out["truncated"] = True
            out["next_offset"] = offset + READ_CHARS
            out["total_chars"] = len(text)
        return out

    def list_course(self, course):
        c = self.courses.get(course)
        if not c:
            return {"error": f"unknown course '{course}'", "courses": sorted(self.courses)}
        return {"course": c["title"], "articles": [
            {"ref": f"{course}/{Path(a['file']).name}", "title": a["title"], "definition": a["lead"],
             "sections": a["sections"]} for a in c["articles"]]}

    def call(self, name, args):
        """Run a tool by name; always returns a JSON string (errors included) for a tool_result."""
        try:
            if name == "search_references":
                r = self.search(args["query"], args.get("course"), args.get("k", 5))
            elif name == "read_reference":
                r = self.read(args["ref"], args.get("offset", 0))
            elif name == "list_course_references":
                r = self.list_course(args["course"])
            else:
                r = {"error": f"unknown tool {name}"}
        except Exception as e:  # never crash the agent loop on a bad tool input
            r = {"error": f"{type(e).__name__}: {e}"}
        return json.dumps(r, ensure_ascii=False)


def _snippet(body, q):
    flat = re.sub(r"\s+", " ", body)
    low = flat.lower()
    pos = min((p for t in q if (p := low.find(t)) >= 0), default=0)
    start = max(0, pos - 80)
    s = flat[start:start + SNIPPET_CHARS]
    return ("…" if start else "") + s + ("…" if start + SNIPPET_CHARS < len(flat) else "")


if __name__ == "__main__":
    lib = RefLibrary()
    cmd, arg = (sys.argv[1], " ".join(sys.argv[2:])) if len(sys.argv) > 2 else ("search", "lever rule")
    name = {"search": "search_references", "read": "read_reference", "list": "list_course_references"}[cmd]
    key = {"search": "query", "read": "ref", "list": "course"}[cmd]
    print(json.dumps(json.loads(lib.call(name, {key: arg})), indent=1, ensure_ascii=False))
