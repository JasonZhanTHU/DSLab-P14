#!/usr/bin/env python3
"""Render the scraped .wikitext reference files into clean plain-text .txt.

Wikitext is great to keep as the source of truth, but hard to read. This makes a
readable study copy next to each .wikitext file (same name, .txt extension).

Usage:
  python3 wiki2text.py                       # all data/*/references/*.wikitext
  python3 wiki2text.py --category seismologie
  python3 wiki2text.py --force               # overwrite existing .txt
"""

import argparse
import re
import sys
from pathlib import Path


def strip_templates(s: str) -> str:
    """Remove {{...}} and {|...|} tables, handling nesting."""
    for open_, close in (("{{", "}}"), ("{|", "|}")):
        while True:
            i = s.find(open_)
            if i == -1:
                break
            depth, j = 0, i
            while j < len(s):
                if s.startswith(open_, j):
                    depth += 1
                    j += 2
                elif s.startswith(close, j):
                    depth -= 1
                    j += 2
                    if depth == 0:
                        break
                else:
                    j += 1
            if depth != 0:  # unbalanced; bail to avoid infinite loop
                s = s[:i] + s[i + 2:]
            else:
                s = s[:i] + s[j:]
    return s


def strip_bracket_links(s: str, kinds) -> str:
    """Remove [[File:...]] / [[Image:...]] / [[Category:...]] with nested brackets."""
    pat = re.compile(r"\[\[\s*(?:" + "|".join(kinds) + r")\s*:", re.I)
    while True:
        m = pat.search(s)
        if not m:
            break
        i = m.start()
        depth, j = 0, i
        while j < len(s):
            if s.startswith("[[", j):
                depth += 1
                j += 2
            elif s.startswith("]]", j):
                depth -= 1
                j += 2
                if depth == 0:
                    break
            else:
                j += 1
        if depth != 0:  # unbalanced; drop opening to avoid looping
            s = s[:i] + s[i + 2:]
        else:
            s = s[:i] + s[j:]
    return s


def wiki_to_text(w: str) -> str:
    s = w
    # HTML comments and ref blocks.
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    s = re.sub(r"<ref[^>]*?/>", "", s, flags=re.S)
    s = re.sub(r"<ref[^>]*?>.*?</ref>", "", s, flags=re.S)
    s = strip_templates(s)
    # Drop File/Image/Category links entirely (nested brackets, multi-line).
    s = strip_bracket_links(s, ("File", "Image", "Category"))
    # [[target|label]] -> label ; [[target]] -> target
    s = re.sub(r"\[\[([^\]|]*)\|([^\]]*)\]\]", r"\2", s)
    s = re.sub(r"\[\[([^\]]*)\]\]", r"\1", s)
    # [http://x label] -> label ; bare [http://x] -> ""
    s = re.sub(r"\[https?://\S+\s+([^\]]+)\]", r"\1", s)
    s = re.sub(r"\[https?://\S+\]", "", s)
    # Remaining HTML tags.
    s = re.sub(r"<[^>]+>", "", s)
    # Headings: ===x=== -> x (keep the text, mark level with blank lines).
    s = re.sub(r"(?m)^\s*(={2,6})\s*(.*?)\s*\1\s*$", r"\n\2\n", s)
    # Bold/italic quotes.
    s = s.replace("'''''", "").replace("'''", "").replace("''", "")
    # List markers at line start.
    s = re.sub(r"(?m)^[*#:;]+\s*", "  - ", s)
    # Entities.
    s = (s.replace("&nbsp;", " ").replace("&ndash;", "-").replace("&mdash;", "-")
         .replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
         .replace("&quot;", '"'))
    # Collapse excess blank lines / trailing spaces.
    s = re.sub(r"[ \t]+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip() + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path("data"))
    ap.add_argument("--category", action="append", help="limit to course slug(s)")
    ap.add_argument("--force", action="store_true", help="overwrite existing .txt")
    a = ap.parse_args()

    slugs = set(a.category) if a.category else None
    files = sorted(a.out.glob("*/references/*.wikitext"))
    n = 0
    for f in files:
        slug = f.parts[-3]
        if slugs and slug not in slugs:
            continue
        dest = f.with_suffix(".txt")
        if dest.exists() and not a.force:
            continue
        try:
            dest.write_text(wiki_to_text(f.read_text(encoding="utf-8")), encoding="utf-8")
            n += 1
        except Exception as e:
            print(f"WARN {f}: {e}", file=sys.stderr)
    print(f"wrote {n} .txt file(s)")


if __name__ == "__main__":
    sys.exit(main())
