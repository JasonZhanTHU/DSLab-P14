#!/usr/bin/env python3
"""Run a model-under-test over ERFA-Exam-Bench and record its answers.

For each task it sends the question text plus any referenced figure image(s) to
the model and stores the free-text answer. The output JSONL (one record per
task) is what grade.py consumes.

Usage:
    python3 run_model.py                         # claude-opus-5-5, all tasks
    python3 run_model.py --model claude-sonnet-5-5 --out runs/sonnet.jsonl
    python3 run_model.py --limit 5               # smoke test on the first 5
    python3 run_model.py --only-auto-gradable    # skip drawing-only items

Credentials: the Anthropic SDK resolves ANTHROPIC_API_KEY or an `ant auth login`
profile automatically (see `ant auth status`).
"""
import argparse
import base64
import json
import sys
from pathlib import Path
from paths import DATA

import anthropic

HERE = DATA

SYSTEM = (
    "You are sitting an ETH Zürich Earth-sciences / mathematics / physics exam. "
    "Answer the question as a strong student would: show the key reasoning and give "
    "clear final results (numbers with units, equations, or short explanations as the "
    "question demands). Many questions are in German; answer in the language of the "
    "question. Some questions refer to a figure (a phase diagram, a geological map, a "
    "sketch) provided as an image — read values off it as needed. If a question asks you "
    "to *draw* something, describe the construction and state the quantitative result. "
    "Be concise; do not restate the question."
)

# Vision-only ("clips") mode: the model is shown page images of the exam and NO
# transcribed question text. It must read every question off the images itself.
SYSTEM_CLIPS = (
    "You are sitting an ETH Zürich exam. You are given scanned/rendered page images of "
    "the exam paper and NOTHING else — read every task directly off the images. Solve "
    "EVERY question and sub-question on the pages. Label each answer clearly with its "
    "Aufgabe/number and sub-part (e.g. '1a)', '2b)') so your answers can be matched to "
    "the questions. Show key reasoning and give clear final results (numbers with units, "
    "equations, short explanations). Answer in the language of the exam (mostly German). "
    "Read values off any phase diagram, geological map or sketch as needed. For a task "
    "that asks you to draw/construct something, describe the construction and give the "
    "quantitative result. Do not skip parts."
)


def load_tasks(path: Path):
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def image_block(fig_path: Path):
    data = base64.standard_b64encode(fig_path.read_bytes()).decode("utf-8")
    return {"type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": data}}


def build_content(task, base=HERE):
    content = []
    for fig in task.get("figures", []):
        fp = base / fig["file"]
        if fp.exists():
            content.append(image_block(fp))
            content.append({"type": "text", "text": f"(Abbildung: {fig.get('caption', fig['file'])})"})
        else:
            print(f"  WARN: figure not found: {fp}", file=sys.stderr)
    header = f"[{task['course']} — {task['exam_name']}] Aufgabe {task['part']} ({task['max_points']} Punkte)\n\n"
    content.append({"type": "text", "text": header + task["question"]})
    return content


def run_text_mode(client, a, tasks, out, base=HERE):
    done = set()
    if a.resume and out.exists():
        with out.open(encoding="utf-8") as f:
            done = {json.loads(l)["id"] for l in f if l.strip()}
    with out.open("a" if a.resume else "w", encoding="utf-8") as f:
        for i, t in enumerate(tasks, 1):
            if t["id"] in done:
                continue
            try:
                resp = client.messages.create(
                    model=a.model, max_tokens=a.max_tokens,
                    thinking={"type": "adaptive"}, output_config={"effort": a.effort},
                    system=SYSTEM,
                    messages=[{"role": "user", "content": build_content(t, base)}])
                text = "\n".join(b.text for b in resp.content if b.type == "text").strip()
                usage = {"input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens}
            except anthropic.APIError as e:
                print(f"[{i}/{len(tasks)}] {t['id']}: API error {e}", file=sys.stderr)
                text, usage = "", {"error": str(e)}
            f.write(json.dumps({"id": t["id"], "mode": "text", "model": a.model,
                                "effort": a.effort, "response": text, "usage": usage},
                               ensure_ascii=False) + "\n")
            f.flush()
            print(f"[{i}/{len(tasks)}] {t['id']}  ({usage.get('output_tokens', '?')} out-tok)")


def run_clips_mode(client, a, tasks, out, base=HERE):
    """One API call per exam: send its page images, no text. Each task of that
    exam gets a record pointing at the shared exam response (so grade.py is
    unchanged). The transcribed question is NEVER sent to the model."""
    manifest = json.loads((base / "clips" / "manifest.json").read_text(encoding="utf-8"))
    by_exam = {}
    for t in tasks:
        by_exam.setdefault(t["exam_id"], []).append(t)
    with out.open("w", encoding="utf-8") as f:
        for exam_id, items in by_exam.items():
            pages = manifest.get(exam_id, [])
            content = []
            for p in pages:
                fp = base / p
                if fp.exists():
                    content.append(image_block(fp))
            content.append({"type": "text",
                            "text": "Solve every question on these exam pages. "
                                    "Label each answer with its Aufgabe/sub-part."})
            try:
                resp = client.messages.create(
                    model=a.model, max_tokens=max(a.max_tokens, 16000),
                    thinking={"type": "adaptive"}, output_config={"effort": a.effort},
                    system=SYSTEM_CLIPS,
                    messages=[{"role": "user", "content": content}])
                text = "\n".join(b.text for b in resp.content if b.type == "text").strip()
                usage = {"input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens}
            except anthropic.APIError as e:
                print(f"{exam_id}: API error {e}", file=sys.stderr)
                text, usage = "", {"error": str(e)}
            print(f"{exam_id}: {len(pages)} page clips → {usage.get('output_tokens','?')} out-tok, "
                  f"{len(items)} items share this response")
            for t in items:
                f.write(json.dumps({"id": t["id"], "mode": "clips", "exam_id": exam_id,
                                    "model": a.model, "effort": a.effort,
                                    "response": text, "usage": usage},
                                   ensure_ascii=False) + "\n")
            f.flush()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tasks", type=Path, default=HERE / "tasks.jsonl")
    ap.add_argument("--model", default="claude-opus-5-5")
    ap.add_argument("--effort", default="high", choices=["low", "medium", "high", "xhigh", "max"])
    ap.add_argument("--max-tokens", type=int, default=8000)
    ap.add_argument("--out", type=Path, default=None, help="output JSONL (default runs/<model>[.clips].jsonl)")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--only-auto-gradable", action="store_true")
    ap.add_argument("--resume", action="store_true", help="skip tasks already present in --out (text mode)")
    ap.add_argument("--clips", action="store_true",
                    help="vision-only: send exam page images and NO question text")
    a = ap.parse_args()

    suffix = ".clips" if a.clips else ""
    out = a.out or (HERE / "runs" / f"{a.model}{suffix}.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)

    tasks = load_tasks(a.tasks)
    if a.only_auto_gradable:
        tasks = [t for t in tasks if t.get("auto_gradable", True)]
    if a.limit:
        tasks = tasks[:a.limit]

    base = a.tasks.resolve().parent          # figures/ and clips/ live next to the tasks file (tier dir)
    client = anthropic.Anthropic()
    if a.clips:
        run_clips_mode(client, a, tasks, out, base)
    else:
        run_text_mode(client, a, tasks, out, base)
    print(f"\nWrote answers → {out}")


if __name__ == "__main__":
    sys.exit(main())
