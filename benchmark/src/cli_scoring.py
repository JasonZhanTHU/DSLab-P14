#!/usr/bin/env python3
"""ERFA-Exam-Bench in the exam-scoring format of src/scoring.

The benchmark keeps its outline (same exams, items, point values and rubric
criteria, all taken from tasks.jsonl). This script only re-expresses it as one
scoring workspace per exam, so src/scoring/score_exams.py can grade a
model's whole exam against the official rubric, and prints the familiar
per-exam table.

    python3 cli_scoring.py build                          # tasks.jsonl -> cli/<exam>/
    python3 cli_scoring.py candidates runs/<model>.jsonl  # model answers -> cli/<exam>/RawExams/ExamNNN.pdf
    python3 cli_scoring.py report                         # evals/*.json -> score table

Scoring itself is src/scoring (prepare_exam.py / score_exams.py, see README).
Needs reportlab and pypdf (requirements.txt).
"""
import argparse
import json
import re
import shutil
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from paths import DATA, SCORING
from xml.sax.saxutils import escape

HERE = DATA
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
NAME_MAX = 48            # heading must stay on one line of the rubric PDF
CANDIDATE_RE = r"^(?:exam_?)?(?P<id>[0-9]+)$"

# Judge rules from grade.py, carried over as the exam-level notes of every workspace.
JUDGE_NOTES = (
    "Candidate answers are typed model outputs labelled by Aufgabe/sub-part, not handwriting. "
    "Each rubric section gives the question, the OFFICIAL reference answer (Musterloesung) and "
    "the point criteria. The reference is authoritative, but an equivalent answer earns full "
    "credit (equivalent algebraic form; a vector times any nonzero scalar; strike/dip given as "
    "the opposite azimuth +-180 deg). For numeric answers use the tolerance in the item notes, "
    "otherwise about 5% (+-8 deg for orientations, +-10 deg for stress axes). Award partial "
    "credit per criterion, never above the criterion maximum. Score correctness only, never "
    "style, length or language. Empty, irrelevant or refused answers get 0."
)


def load_jsonl(path):
    with Path(path).open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def num(x):
    return int(x) if float(x) == int(x) else float(x)


def pdf_kit():
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer
        from reportlab.lib.utils import ImageReader
    except ImportError:
        sys.exit("reportlab is required: pip install -r requirements.txt")
    for name, fn in (("DV", "DejaVuSans.ttf"), ("DV-B", "DejaVuSans-Bold.ttf")):
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / fn)))
    base = ParagraphStyle("b", fontName="DV", fontSize=9.5, leading=13)
    styles = {
        "body": base,
        "h1": ParagraphStyle("h1", parent=base, fontName="DV-B", fontSize=14, leading=18, spaceAfter=6),
        "h2": ParagraphStyle("h2", parent=base, fontName="DV-B", fontSize=11.5, leading=15,
                             spaceBefore=12, spaceAfter=4),
        "crit": ParagraphStyle("crit", parent=base, fontName="DV-B", fontSize=9.5, leading=13,
                               spaceBefore=5),
        "small": ParagraphStyle("s", parent=base, fontSize=8.5, leading=11),
    }
    return dict(A4=A4, mm=mm, doc=SimpleDocTemplate, para=Paragraph, spacer=Spacer, image=Image,
                reader=ImageReader, styles=styles)


def text_flow(k, text, style="body"):
    """Escaped text as one Paragraph per line (page-splittable, whitespace kept)."""
    out = []
    for line in str(text).replace("\r", "").split("\n"):
        if not line.strip():
            out.append(k["spacer"](1, 5))
            continue
        lead = len(line) - len(line.lstrip(" "))
        out.append(k["para"]("&nbsp;" * lead + escape(line.strip()), k["styles"][style]))
    return out


def figure_flow(k, path, caption, max_w=440, max_h=300):
    w, h = k["reader"](str(path)).getSize()
    s = min(max_w / w, max_h / h, 1.0)
    return [k["image"](str(path), width=w * s, height=h * s),
            k["para"](escape(caption), k["styles"]["small"]), k["spacer"](1, 6)]


def build_pdf(k, path, story, title):
    doc = k["doc"](str(path), pagesize=k["A4"], title=title, author="ERFA-Exam-Bench",
                   leftMargin=18 * k["mm"], rightMargin=18 * k["mm"],
                   topMargin=16 * k["mm"], bottomMargin=16 * k["mm"])
    doc.build(story)


# --------------------------------------------------------------------------- build

def short_name(text):
    s = re.sub(r"\s+", " ", text).strip().replace(" - ", " – ")
    return s if len(s) <= NAME_MAX else s[:NAME_MAX - 1].rstrip() + "…"


def problem_of(part):
    m = re.match(r"\d+", part)
    return m.group(0) if m else part


def exam_items(tasks, include_drawing):
    """[(task, [manifest item, ...])] preserving the benchmark's task/criterion order."""
    out, seen = [], set()
    for t in tasks:
        if not (include_drawing or t.get("auto_gradable", True)):
            continue
        part = t["part"]
        if part in seen:
            raise SystemExit(f"{t['exam_id']}: part {part!r} occurs twice; rubric_item ids would clash")
        seen.add(part)
        if abs(sum(c["points"] for c in t["rubric"]) - t["max_points"]) > 1e-9:
            raise SystemExit(f"{t['id']}: rubric does not sum to max_points")
        items = [{
            "rubric_item": f"{part}.{n}",
            "rubric_name": short_name(c["criterion"]),
            "max_points": num(c["points"]),
            "part_id": part,
            "problem_id": problem_of(part),
            "score_mode": "continuous",
            "notes": t.get("notes", ""),
            "dependencies": [],
        } for n, c in enumerate(t["rubric"], 1)]
        out.append((t, items))
    return out


def rubric_story(k, tasks_items, tasks_dir, title, term_note):
    s = []
    s.append(k["para"](escape(title), k["styles"]["h1"]))
    s += text_flow(k, term_note, "small")
    for t, items in tasks_items:
        s.append(k["para"](escape(f"Aufgabe {t['part']} — {num(t['max_points'])} points"), k["styles"]["h2"]))
        s += text_flow(k, "Question: " + t["question"])
        for fig in t.get("figures", []):
            fp = tasks_dir / fig["file"]
            if fp.exists():
                s += figure_flow(k, fp, "Figure: " + fig.get("caption", fig["file"]))
        s.append(k["spacer"](1, 4))
        s += text_flow(k, "OFFICIAL reference answer: " + t["reference_answer"])
        if t.get("notes"):
            s += text_flow(k, "Grader notes: " + t["notes"])
        for item, c in zip(items, t["rubric"]):
            pts = item["max_points"]
            s.append(k["para"](escape(f"{item['rubric_item']} - {item['rubric_name']} - "
                                      f"{pts} {'point' if pts == 1 else 'points'}:"), k["styles"]["crit"]))
            s += text_flow(k, c["criterion"])
    return s


def cmd_build(a):
    tasks_path = a.tasks.resolve()
    tasks_dir = tasks_path.parent
    tier = "official" if tasks_path.name == "tasks.jsonl" else "derived"
    out_root = (a.out or HERE / ("cli" if tier == "official" else "cli_derived")).resolve()
    template = SCORING / "prompt.template.txt"
    k = pdf_kit()
    by_exam = defaultdict(list)
    for t in load_jsonl(tasks_path):
        by_exam[t["exam_id"]].append(t)

    summary = []
    for exam_file, tasks in by_exam.items():
        stem = Path(exam_file).stem
        ws = out_root / stem
        if ws.exists():
            if not a.force:
                sys.exit(f"{ws} exists; pass --force to rebuild (this deletes candidates/ and evals/ in it)")
            shutil.rmtree(ws)
        tasks_items = exam_items(tasks, a.include_drawing)
        if not tasks_items:
            continue
        items = [i for _, its in tasks_items for i in its]
        total = num(sum(Decimal(str(i["max_points"])) for i in items))
        t0 = tasks[0]
        exam_id = f"ERFA_{tier.upper()}_{stem.upper()}_V1"
        title = f"{t0['course']} — {t0['exam_name']} ({t0['term']})"
        skipped = [t["part"] for t in tasks if not (a.include_drawing or t.get("auto_gradable", True))]
        notes = JUDGE_NOTES
        if skipped:
            notes += f" Drawing/construction parts {', '.join(skipped)} are not scored."
        if any(t.get("points_source") == "assigned" for t in tasks):
            notes += " Point values on this exam were assigned by the benchmark, not printed on the sheet."

        for d in ("Rubrics", "Prompts", "RawExams", "evals"):
            (ws / d).mkdir(parents=True)
        shutil.copy(template, ws / "Prompts" / "prompt.template.txt")
        (ws / "exam_config.json").write_text(json.dumps({
            "schema_version": 1, "exam_id": exam_id, "exam_title": title,
            "approved_for_scoring": False,
            "paths": {"manifest": "rubric_manifest.json", "rubric": "Rubrics/rubric.pdf",
                      "prompt_template": "Prompts/prompt.template.txt", "prompt": "Prompts/prompt.txt",
                      "exams": "RawExams", "evals": "evals"},
            "filename_pattern": CANDIDATE_RE, "identity_mode": "numeric",
            "max_combined_pdf_bytes": 50000000,
            "rubric_validation": {"mode": "headings", "approved_sha256": ""},
            "notes": notes}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (ws / "rubric_manifest.json").write_text(json.dumps({
            "exam_id": exam_id, "expected_total_max_points": total, "items": items},
            indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        note = (f"{t0['course']}, {t0['term']}, language {t0['language']}. Source: "
                f"{' / '.join(filter(None, [t0.get('source_exam_pdf'), t0.get('source_solution_pdf')]))}. {len(tasks_items)} items, {len(items)} criteria, {total} points.")
        build_pdf(k, ws / "Rubrics" / "rubric.pdf",
                  rubric_story(k, tasks_items, tasks_dir, title, note), title)
        summary.append((stem, len(tasks_items), len(items), total))
        print(f"{stem}: {len(tasks_items)} items, {len(items)} criteria, {total} points → {ws}")

    print(f"\n{len(summary)} workspaces, {sum(s[3] for s in summary)} points in {out_root}")
    print("Next: script/cli_prepare")


# ---------------------------------------------------------------------- candidates

def workspaces(root):
    return sorted(p.parent for p in Path(root).glob("*/exam_config.json"))


def register(ws, label, source):
    """Candidate number for (label), stable across reruns. candidates.json is the registry."""
    reg_path = ws / "candidates.json"
    reg = json.loads(reg_path.read_text()) if reg_path.exists() else {}
    for exam, rec in reg.items():
        if rec["label"] == label:
            return exam, reg
    n = max([int(e[4:]) for e in reg] + [0]) + 1
    exam = f"Exam{n:03d}"
    reg[exam] = {"label": label, "source": str(source)}
    reg_path.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return exam, reg


def cmd_candidates(a):
    k = pdf_kit()
    runs = load_jsonl(a.run)
    if not runs:
        sys.exit(f"{a.run} is empty")
    label = a.label or Path(a.run).stem
    responses = {r["id"]: r.get("response", "") for r in runs}
    clips = any(r.get("mode") == "clips" for r in runs)
    tasks = defaultdict(list)
    for t in load_jsonl(a.tasks):
        tasks[Path(t["exam_id"]).stem].append(t)
    wrote = 0
    for ws in workspaces(a.root):
        mine = [t for t in tasks.get(ws.name, []) if t["id"] in responses]
        if not mine:
            print(f"{ws.name}: no answers in {a.run.name} — skipped")
            continue
        exam, _ = register(ws, label, a.run)
        target = ws / "RawExams" / f"{exam}.pdf"
        if target.exists():
            print(f"{ws.name}: {target.name} already exists for {label!r} — kept")
            continue
        # The submission carries no model name: the judge sees only the answers.
        story = [k["para"]("Exam submission", k["styles"]["h1"])]
        if clips:
            story += text_flow(k, responses[mine[0]["id"]])    # one shared response per exam
        else:
            for t in mine:
                story.append(k["para"](escape(f"Aufgabe {t['part']}"), k["styles"]["h2"]))
                story += text_flow(k, responses[t["id"]] or "(no answer)")
        build_pdf(k, target, story, "Exam submission")
        wrote += 1
        print(f"{ws.name}: {label!r} → RawExams/{target.name}")
    print(f"\n{wrote} submission PDFs written")


# ------------------------------------------------------------------------- report

def cmd_report(a):
    sys.path.insert(0, str(SCORING))
    from exam_common import ExamError, exact_sum, load_config, load_json, validate_result
    table = defaultdict(dict)                 # label -> exam title -> (awarded, possible, flagged)
    parts = defaultdict(lambda: defaultdict(lambda: [Decimal(0), Decimal(0)]))
    missing = []
    for ws in workspaces(a.root):
        cfg = load_config(ws / "exam_config.json")
        reg_path = ws / "candidates.json"
        reg = json.loads(reg_path.read_text()) if reg_path.exists() else {}
        for res in sorted(cfg.file("evals").glob("*.json")):
            label = reg.get(res.stem, {}).get("label", res.stem)
            try:
                data = validate_result(load_json(res), cfg)
            except ExamError as e:
                print(f"{ws.name}/{res.name}: INVALID — {e}", file=sys.stderr)
                continue
            by_label = {i.label: i for i in cfg.items}
            awarded = exact_sum(Decimal(str(g["awarded_points"])) for g in data["grades"])
            table[label][cfg.raw["exam_title"]] = (awarded, cfg.total, data["human_review_recommended"])
            for g in data["grades"]:
                p = parts[(label, cfg.raw["exam_title"])][by_label[g["rubric_item"]].part]
                p[0] += Decimal(str(g["awarded_points"]))
                p[1] += Decimal(str(g["max_points"]))
        if not any(cfg.file("evals").glob("*.json")):
            missing.append(ws.name)
    if not table:
        sys.exit("No scored results yet (evals/*.json). Run score_exams.py first.")
    for label, exams in sorted(table.items()):
        print("\n" + "=" * 72)
        print(f"{label}")
        print(f"{'EXAM':50s} {'SCORE':>12}  {'%':>5}")
        print("-" * 72)
        ta = tp = Decimal(0)
        for title, (aw, po, flag) in sorted(exams.items()):
            ta, tp = ta + aw, tp + po
            print(f"{title[:48] + (' *' if flag else ''):50s} {float(aw):6.2f}/{float(po):<5.1f} "
                  f"{100 * float(aw) / float(po):>5.1f}")
            if a.by_part:
                for part, (pa, pp) in parts[(label, title)].items():
                    print(f"    Aufgabe {part:<8s} {float(pa):6.2f}/{float(pp):<5.1f}")
        print("-" * 72)
        print(f"{'TOTAL':50s} {float(ta):6.2f}/{float(tp):<5.1f} {100 * float(ta) / float(tp) if tp else 0:>5.1f}")
    print("\n* = scorer recommended human review (see human_reviews via compile_ai_grades.py)")
    if missing:
        print("No results yet: " + ", ".join(missing))


def cmd_prepare(a):
    import subprocess
    for ws in workspaces(a.root):
        cmd = [sys.executable, str(SCORING / "prepare_exam.py"), "--config", str(ws / "exam_config.json")]
        if a.overwrite:
            cmd.append("--overwrite")
        r = subprocess.run(cmd, capture_output=True, text=True)
        ok = [l for l in r.stdout.splitlines() if "criteria" in l]
        print(f"{ws.name}: " + (ok[-1] if r.returncode == 0 and ok else f"FAILED\n{r.stderr.strip()}"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="tasks.jsonl → one toolkit workspace per exam")
    b.add_argument("--tasks", type=Path, default=HERE / "tasks.jsonl")
    b.add_argument("--out", type=Path, default=None, help="default cli/ (cli_derived/ for derived tasks)")
    b.add_argument("--include-drawing", action="store_true", help="also score drawing/construction items")
    b.add_argument("--force", action="store_true")
    b.set_defaults(fn=cmd_build)
    p = sub.add_parser("prepare", help="run the toolkit's prepare_exam.py in every workspace")
    p.add_argument("--root", type=Path, default=HERE / "cli")
    p.add_argument("--overwrite", action="store_true")
    p.set_defaults(fn=cmd_prepare)
    c = sub.add_parser("candidates", help="run_model.py output → RawExams/ExamNNN.pdf per exam")
    c.add_argument("run", type=Path)
    c.add_argument("--tasks", type=Path, default=HERE / "tasks.jsonl")
    c.add_argument("--root", type=Path, default=HERE / "cli")
    c.add_argument("--label", help="name shown in the report (default: run file stem)")
    c.set_defaults(fn=cmd_candidates)
    r = sub.add_parser("report", help="print the per-exam score table from evals/*.json")
    r.add_argument("--root", type=Path, default=HERE / "cli")
    r.add_argument("--by-part", action="store_true")
    r.set_defaults(fn=cmd_report)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
