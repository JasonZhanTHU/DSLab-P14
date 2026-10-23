#!/usr/bin/env python3
"""Grade a model's answers to the Groundwater 2020 exam with a local OpenAI-compatible
judge (default: Qwen3.8-27B served by vLLM). No Claude/API calls.

For every sub-part in rubric.json the judge gets the question, the reference solution,
grading notes, and the student's full answer, and returns {"score": x, "reason": "..."}.
The score is clamped to [0, max] and rounded to 0.5.

Usage (judge server must be running, see README.md):
  python grade_local.py answers_gemma-4-31b.md
  python grade_local.py answers_*.md --samples 3          # median of 3 judge samples
Writes <answers>.grade.json and <answers>.grade.md next to each answers file.
"""
import argparse
import json
import re
import sys
import statistics
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import DATA

from openai import OpenAI

HERE = DATA / "groundwater2020"

SYSTEM = """You are a strict but fair teaching assistant marking an ETH Zürich Groundwater exam.
You mark ONE sub-question at a time against the official reference solution.
Rules:
- Find the student's answer to this sub-question in the full answer text (it is labelled by problem and part, e.g. "1c)" or "Problem 2, b"). Ignore other parts.
- Compare with the reference solution and grading notes. Award partial credit as the notes describe. Numerical results must match the reference within about 5% unless the notes say otherwise.
- Do not give credit for a correct final number reached by clearly wrong reasoning, and do not penalise a different but valid method that reaches the right result.
- If the student did not answer this sub-question, give 0.
- Do not reward length or confident tone. Use only the reference and notes given, not your own opinion of the correct answer.
Reply with ONLY a JSON object: {"score": <number>, "reason": "<one or two sentences>"}"""


def ask(client, model, item, answer, temperature, max_tokens):
    user = (f"SUB-QUESTION {item['id']} (max {item['max']} points)\n{item['question']}\n\n"
            f"REFERENCE SOLUTION\n{item['reference']}\n\nGRADING NOTES\n{item['notes']}\n\n"
            f"STUDENT'S FULL ANSWER\n<<<\n{answer}\n>>>\n\n"
            f"Mark sub-question {item['id']} only. Output the JSON object.")
    r = client.chat.completions.create(
        model=model, temperature=temperature, max_tokens=max_tokens,
        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}])
    text = r.choices[0].message.content or ""
    for m in reversed(re.findall(r"\{.*?\}", text, flags=re.S)):
        try:
            d = json.loads(m)
            s = float(d["score"])
            s = min(max(s, 0.0), float(item["max"]))
            return round(s * 2) / 2, str(d.get("reason", "")).strip()
        except (ValueError, KeyError, TypeError):
            continue
    return None, f"unparseable judge output: {text[:200]!r}"


def grade_file(client, model, path, rubric, samples, temperature, max_tokens):
    answer = path.read_text()
    rows = []
    for item in rubric["items"]:
        got = [ask(client, model, item, answer, temperature, max_tokens) for _ in range(samples)]
        scores = [s for s, _ in got if s is not None]
        score = statistics.median(scores) if scores else None
        reason = next((r for s, r in got if s == score), got[0][1])
        rows.append({"id": item["id"], "max": item["max"], "score": score,
                     "samples": [s for s, _ in got], "reason": reason})
        print(f"  {item['id']:>3}: {score}/{item['max']}  {reason[:100]}", flush=True)
    total = sum(r["score"] or 0 for r in rows)
    mx = sum(r["max"] for r in rows)
    out = {"file": path.name, "judge": model, "samples": samples, "total": total, "max": mx, "items": rows}
    path.with_suffix(".grade.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    md = [f"# Grade: {path.name}", f"Judge: {model} (median of {samples}). **Total {total:g} / {mx} ({100*total/mx:.0f}%)**", "",
          "| Part | Score | Judge note |", "|---|---|---|"]
    md += [f"| {r['id']} | {r['score']}/{r['max']} | {r['reason'].replace('|', '/')} |" for r in rows]
    path.with_suffix(".grade.md").write_text("\n".join(md) + "\n")
    print(f"  TOTAL {total:g}/{mx}  -> {path.with_suffix('.grade.md').name}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("answers", nargs="+", type=Path)
    ap.add_argument("--base-url", default="http://127.0.0.1:8137/v1")
    ap.add_argument("--model", default="qwen3.8-27b")
    ap.add_argument("--rubric", type=Path, default=HERE / "rubric.json")
    ap.add_argument("--samples", type=int, default=1, help="judge samples per sub-part (median is used)")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--max-tokens", type=int, default=8192)
    a = ap.parse_args()
    rubric = json.loads(a.rubric.read_text())
    client = OpenAI(base_url=a.base_url, api_key="EMPTY", timeout=1800)
    for p in a.answers:
        print(p.name)
        grade_file(client, a.model, p, rubric, a.samples, a.temperature, a.max_tokens)


if __name__ == "__main__":
    main()
