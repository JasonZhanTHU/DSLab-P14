#!/usr/bin/env python3
"""LLM-as-judge grader for ERFA-Exam-Bench.

Scores a model's answers (from run_model.py) against each task's OFFICIAL
reference answer and point-allocated rubric. The judge awards points per rubric
criterion and returns a short justification, so scores are auditable.

Usage:
    python3 grade.py runs/claude-opus-5-5.jsonl
    python3 grade.py runs/sonnet.jsonl --judge claude-opus-5-5 --out scores/sonnet.jsonl

Only auto-gradable tasks are scored by default (drawing/construction items are
skipped; pass --include-drawing to score them too, with the caveat that a judge
cannot see the candidate's drawing).

Credentials: the SDK resolves ANTHROPIC_API_KEY or an `ant auth login` profile.
"""
import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from paths import DATA

import anthropic

HERE = DATA

JUDGE_SYSTEM = (
    "You are a meticulous, fair exam grader for ETH Zürich Earth-sciences, mathematics and "
    "physics exams. You are given a question, the OFFICIAL reference answer (from the course's "
    "Musterlösung), a point-allocated rubric, and a candidate's answer. Award points per rubric "
    "criterion based ONLY on whether the candidate's answer is correct and matches the required "
    "content — never on style, length or language. Follow these rules:\n"
    "• The reference answer is authoritative. A different but mathematically/physically equivalent "
    "answer (e.g. an equivalent algebraic form, a vector times any nonzero scalar, strike/dip given "
    "as the opposite azimuth ±180°) earns full credit.\n"
    "• For numeric answers, accept values within the tolerance stated in the rubric/notes, or within "
    "~5% (or ~±8° for orientations / ±10° for stress axes) when no tolerance is stated.\n"
    "• Award partial credit per criterion when only part is right. Points per criterion are capped "
    "at that criterion's maximum; never exceed max_points overall.\n"
    "• If the candidate's answer is empty, irrelevant, or an explicit refusal, award 0.\n"
    "Return ONLY a JSON object, no prose around it."
)

JUDGE_TEMPLATE = """Grade the following exam answer.

QUESTION:
{question}

OFFICIAL REFERENCE ANSWER:
{reference}

RUBRIC (criteria and their maximum points; total = {max_points}):
{rubric}

{notes_block}CANDIDATE ANSWER:
\"\"\"
{response}
\"\"\"

Return a JSON object with exactly these fields:
{{
  "criteria": [{{"criterion": "<verbatim criterion text>", "max": <number>, "awarded": <number>, "note": "<short reason>"}}, ...],
  "awarded_points": <number, sum of awarded, <= {max_points}>,
  "justification": "<one or two sentences>"
}}"""


def load_jsonl(path: Path):
    with path.open(encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def extract_json(text: str):
    """Pull the first JSON object out of the judge's reply (robust to stray prose)."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.S)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # find the outermost {...}
        depth, start = 0, None
        for i, ch in enumerate(text):
            if ch == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0 and start is not None:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        pass
    return None


def grade_one(client, judge_model, task, response):
    rubric_txt = "\n".join(f"  - [{r['points']} pt] {r['criterion']}" for r in task["rubric"])
    notes_block = ""
    if task.get("notes"):
        notes_block = f"GRADER NOTES (tolerances / caveats): {task['notes']}\n\n"
    prompt = JUDGE_TEMPLATE.format(
        question=task["question"], reference=task["reference_answer"],
        rubric=rubric_txt, max_points=task["max_points"],
        notes_block=notes_block, response=response or "(no answer)")
    resp = client.messages.create(
        model=judge_model, max_tokens=4000,
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
        system=JUDGE_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "\n".join(b.text for b in resp.content if b.type == "text")
    data = extract_json(text)
    if not data:
        return {"awarded_points": 0.0, "criteria": [], "justification": "JUDGE_PARSE_ERROR",
                "raw": text[:500], "max_points": task["max_points"]}
    awarded = min(float(data.get("awarded_points", 0)), task["max_points"])
    data["awarded_points"] = max(0.0, awarded)
    data["max_points"] = task["max_points"]
    return data


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("responses", type=Path, help="JSONL produced by run_model.py")
    ap.add_argument("--tasks", type=Path, default=HERE / "tasks.jsonl")
    ap.add_argument("--judge", default="claude-opus-5-5")
    ap.add_argument("--out", type=Path, default=None, help="per-item scores JSONL")
    ap.add_argument("--include-drawing", action="store_true",
                    help="also grade drawing/construction items (judge can't see the drawing)")
    a = ap.parse_args()

    tasks = {t["id"]: t for t in load_jsonl(a.tasks)}
    responses = {r["id"]: r.get("response", "") for r in load_jsonl(a.responses)}
    out = a.out or (HERE / "scores" / (a.responses.stem + ".scores.jsonl"))
    out.parent.mkdir(parents=True, exist_ok=True)

    client = anthropic.Anthropic()
    per_exam = defaultdict(lambda: [0.0, 0.0])   # exam -> [awarded, possible]
    graded = []
    items = [t for t in tasks.values() if a.include_drawing or t.get("auto_gradable", True)]

    with out.open("w", encoding="utf-8") as f:
        for i, t in enumerate(items, 1):
            if t["id"] not in responses:
                print(f"[{i}/{len(items)}] {t['id']}: no response — skipped", file=sys.stderr)
                continue
            res = grade_one(client, a.judge, t, responses[t["id"]])
            rec = {"id": t["id"], "exam_id": t["exam_id"], "course": t["course"],
                   "judge": a.judge, **res}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            per_exam[t["exam_name"]][0] += res["awarded_points"]
            per_exam[t["exam_name"]][1] += t["max_points"]
            graded.append(rec)
            print(f"[{i}/{len(items)}] {t['id']:12s} {res['awarded_points']:>5.2f}/{t['max_points']:<4} "
                  f"{res.get('justification', '')[:70]}")

    tot_a = sum(v[0] for v in per_exam.values())
    tot_p = sum(v[1] for v in per_exam.values())
    print("\n" + "=" * 64)
    print(f"{'EXAM':42s} {'SCORE':>12}  {'%':>5}")
    print("-" * 64)
    for exam, (aw, po) in sorted(per_exam.items()):
        print(f"{exam[:42]:42s} {aw:6.2f}/{po:<5.1f} {100*aw/po if po else 0:>5.1f}")
    print("-" * 64)
    print(f"{'TOTAL':42s} {tot_a:6.2f}/{tot_p:<5.1f} {100*tot_a/tot_p if tot_p else 0:>5.1f}")
    print(f"\nPer-item scores → {out}")


if __name__ == "__main__":
    sys.exit(main())
