#!/usr/bin/env python3
"""Sit the Groundwater Assessment I (26 Oct 2020) exam with a local OpenAI-compatible
model (vLLM) that has the reference-library tools from build/ref_tools.py.

The model gets: the clean question text (questions.txt) + the four question pages
rendered WITHOUT the PDF's handwritten annotations (pages/). The student-solution pages
(3, 5, 7) and the annotations are never sent. No scoring is done here.

Usage (server must be running, see README.md):
  python run_exam.py --base-url http://127.0.0.1:8137/v1 --model qwen3.8-27b
Writes answers.md (final answer) and trace.json (every message, tool call and result).
"""
import argparse
import base64
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import DATA, SCRAPE

from openai import OpenAI

HERE = DATA / "groundwater2020"
sys.path.insert(0, str(SCRAPE / "build"))
from ref_tools import TOOLS, RefLibrary  # noqa: E402

SYSTEM = """You are sitting an ETH Zürich exam: Groundwater (651-4023-00), Assessment I (Midterm), 26 Oct 2020. 40 points, 90 minutes.

Answer every problem and sub-question as a strong student would: state the governing equations, show the key intermediate steps, and give clear final results with units, rounded sensibly. Label each answer with its problem and sub-part (e.g. "1b)", "2c)"). The figures are on the attached page images; read values off them where needed. If a value seems missing, assume a reasonable one, say so, and continue.

You have access to a reference library (open-book exam). Tools:
- search_references(query, course?, k?): full-text search over ~1000 English Wikipedia articles on earth sciences, physics, chemistry and mathematics, split into sections. Query in ENGLISH keywords. Courses relevant here include "groundwater", "hydrogeologie" and "ozeanographieundhydrogeologie", but searching all courses is fine.
- read_reference(ref, offset?): read a section/article returned by search.
- list_course_references(course): list the articles collected for a course.
The library is general encyclopedia background, not course material, and contains no solutions to this exam. Use it when you want to check a definition, formula or concept; it is optional. Keep lookups purposeful (a handful of calls is usually enough), then write your complete final answer."""


def img(p: Path):
    return {"type": "image_url",
            "image_url": {"url": "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8137/v1")
    ap.add_argument("--model", default="qwen3.8-27b")
    ap.add_argument("--max-tool-rounds", type=int, default=12)
    ap.add_argument("--max-tokens", type=int, default=32768)
    ap.add_argument("--no-images", action="store_true", help="text-only model: send questions.txt only")
    ap.add_argument("--no-tools", action="store_true", help="do not offer the reference-library tools")
    ap.add_argument("--out", type=Path, default=HERE / "answers.md")
    a = ap.parse_args()

    client = OpenAI(base_url=a.base_url, api_key="EMPTY", timeout=3600)
    lib = RefLibrary()
    tools = [{"type": "function", "function": {"name": t["name"], "description": t["description"],
                                               "parameters": t["input_schema"]}} for t in TOOLS]
    pages = [] if a.no_images else sorted((HERE / "pages").glob("page-*.png"))
    user = [img(p) for p in pages] + [{"type": "text", "text":
            ("Transcribed question text only (figures are not available to you; state any assumption you need):\n\n" if a.no_images else "Exam pages are attached as images. Transcribed question text:\n\n")
            + (HERE / "questions.txt").read_text() + "\n\nSolve all problems."}]
    system = SYSTEM
    if a.no_images or a.no_tools:
        system += "\n\nNOTE: " + ("No page images are provided; figures cannot be seen, so state sensible assumptions for any figure-dependent value. " if a.no_images else "") + ("No tools are available; answer directly." if a.no_tools else "")
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    sampling = dict(temperature=1.0, top_p=0.95, extra_body={"top_k": 20, "min_p": 0.0})
    trace, usage = [], {"prompt_tokens": 0, "completion_tokens": 0}
    t0 = time.time()

    for rnd in range(a.max_tool_rounds + 1):
        last = rnd == a.max_tool_rounds
        r = client.chat.completions.create(model=a.model, messages=msgs, max_tokens=a.max_tokens,
                                           **({} if a.no_tools else dict(tools=tools, tool_choice="none" if last else "auto")), **sampling)
        m = r.choices[0].message
        usage["prompt_tokens"] += r.usage.prompt_tokens
        usage["completion_tokens"] += r.usage.completion_tokens
        reasoning = getattr(m, "reasoning_content", None) or getattr(m, "reasoning", None)
        entry = {"round": rnd, "finish_reason": r.choices[0].finish_reason, "reasoning": reasoning,
                 "content": m.content, "tool_calls": []}
        trace.append(entry)
        if not m.tool_calls:
            break
        msgs.append({"role": "assistant", "content": m.content or "",
                     "tool_calls": [tc.model_dump() for tc in m.tool_calls]})
        for tc in m.tool_calls:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            result = lib.call(tc.function.name, args)
            entry["tool_calls"].append({"name": tc.function.name, "args": args, "result": result})
            print(f"[round {rnd}] {tc.function.name}({json.dumps(args, ensure_ascii=False)})", flush=True)
            msgs.append({"role": "tool", "tool_call_id": tc.id, "content": result})

    answer = (trace[-1]["content"] or "").strip()
    calls = [c for e in trace for c in e["tool_calls"]]
    (HERE / "trace.json" if a.out.name == "answers.md" else a.out.with_suffix(".trace.json")).write_text(json.dumps(
        {"model": a.model, "seconds": round(time.time() - t0), "usage": usage,
         "tool_calls": len(calls), "rounds": trace}, indent=1, ensure_ascii=False))
    header = (f"# Groundwater Assessment I (26 Oct 2020) — {a.model} answers\n\n"
              f"_Reference tools available; {len(calls)} tool call(s) made: "
              + (", ".join(f"`{c['name']}({c['args'].get('query') or c['args'].get('ref') or c['args'].get('course')})`"
                           for c in calls) or "none") + "._\n\n")
    a.out.write_text(header + answer + "\n")
    print(f"\n{len(calls)} tool calls, {usage}, {round(time.time() - t0)}s -> {a.out}")


if __name__ == "__main__":
    main()
