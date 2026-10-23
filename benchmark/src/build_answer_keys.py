#!/usr/bin/env python3
"""Write answers/<exam>_correct_answers.{md,json} for every exam from tasks.jsonl.

The reference answers in tasks.jsonl come from the official Musterlösungen; this adds, per item,
how each was verified (independent re-derivation script, or official-only) and flags errata /
approximations. Hint values pre-printed on the Kartenpraktikum sheets are never used as answers.
"""
import json
from collections import defaultdict
from pathlib import Path
from paths import DATA

HERE = Path(__file__).resolve().parent
NUM = "independently re-derived (verify/numeric_checks.py)"
GEO = "independently re-derived (verify/kartenpraktikum_geometry_check.py)"
OFF = "official Musterlösung only"
MAPR = "official Musterlösung only (map measurement; needs the georeferenced map to re-derive)"
DRW = "official Musterlösung (drawing/construction)"

V = {}
for i in "physik_a1 physik_a2b physik_a2c physik_a3 physik_a4b physik_a6".split(): V[i] = NUM
for i in "math_1a math_1c math_1d math_3a math_3b math_4c math_5a math_5c math_6b".split(): V[i] = NUM
for i in "sa_2a sa_2c sa_2d sa_2e sa_2f sa_3c sa_3d".split(): V[i] = NUM
for i in "meta_1b meta_1c".split(): V[i] = NUM + " — lever rule"
for i in "k14_1 k14_2 k14_3 k14_4 k14_5 k13_1 k13_4 k13_5".split(): V[i] = MAPR
for i in "k14_6 k14_14 k13_6 k13_12".split(): V[i] = DRW
for i in "k14_7 k14_9 k14_10 k14_11 k14_12 k14_13 k13_3 k13_8 k13_9 k13_10".split(): V[i] = GEO
V["k13_11"] = GEO + " (strike-slip 227 vs official 210 m: ~8 % graphical difference)"

FLAGS = {
    "meta_1c": "Erratum: Musterlösung druckt Enstatit 56.6 % bei T_2 (Summe 101 %); korrekt 55.6 %.",
    "sa_2e": "Musterlösung nutzt e^-1≈1/3 (Tabelle der Aufgabe) ⇒ 200 kg/a; exakt 221 kg/a. Beides korrekt.",
    "sa_2f": "Folgewert der Näherung: 0.067 (offiziell) bzw. 0.074 mg/m³ (exakt). Beides korrekt.",
    "sa_3d": "Aufgabe erlaubt Nullsetzen des kleinen Koeffizienten ⇒ 30 d; exakt ≈ 36 d.",
    "math_1a": "Zweite Bedingung ist eine Betragsgleichung |z/(1−i)| = |…| (Betragsstriche im Original).",
    "k14_2": "Hinweiswerte 094/38, 274/38 der Prüfung sind NICHT die Lösung.",
    "k14_5": "Hinweiswert 301/74 ist NICHT die Lösung.",
    "k14_10": "Hinweiswert 332° ist NICHT die Lösung.",
    "k13_2": "Hinweiswerte 067/24, 247/37 der Prüfung sind NICHT die Lösung.",
    "k13_5": "Hinweiswert 079/69 ist NICHT die Lösung.",
    "k13_8": "Hinweiswert 16° ist NICHT die Lösung.",
    "k14_13": "Musterlösung nennt zusätzlich 93 m / 77 m (Hinweiswert-Variante) — nicht gültig.",
    "k13_11": "Musterlösung nennt zusätzlich 120 m / 160 m / 107 m (Hinweiswert-Variante) — nicht gültig.",
    "k14_6": "Zwei zulässige Profile (Diskordanz jünger/älter als Verwerfung): answers/k9mytfrn_official_drawings/profile_XY.png",
    "k14_14": "Siehe answers/k9mytfrn_official_drawings/map_construction.png",
    "k13_6": "Siehe answers/ja9djbrh_official_drawings/profile_XY.png (zwei Lösungen: Bennison / Frehner)",
    "k13_12": "Siehe answers/ja9djbrh_official_drawings/map_construction.png",
}

by_exam = defaultdict(list)
for line in open(DATA / "tasks.jsonl", encoding="utf-8"):
    t = json.loads(line)
    by_exam[t["exam_id"]].append(t)

out = DATA / "answers"
out.mkdir(exist_ok=True)
index = ["# Verified answer keys\n", "| Exam | Course | Items | Points |", "|---|---|---|---|"]
for exam_id, items in by_exam.items():
    stem = exam_id.replace(".pdf", "")
    rows = [{"id": t["id"], "part": t["part"], "max_points": t["max_points"],
             "correct_answer": t["reference_answer"],
             "verification": V.get(t["id"], OFF),
             "note": FLAGS.get(t["id"], t.get("notes", ""))} for t in items]
    head = items[0]
    (out / f"{stem}_correct_answers.json").write_text(json.dumps(
        {"exam": f"{head['course']} — {head['exam_name']} ({exam_id})",
         "source": "official solution.pdf, cross-checked", "answers": rows},
        ensure_ascii=False, indent=2), encoding="utf-8")
    md = [f"# Correct answers — {head['course']}, {head['exam_name']} (`{stem}`)\n",
          "Source: official Musterlösung, cross-checked where possible. Pre-printed grey hint "
          "values on the sheets are not answers.\n",
          "| Q | Pts | Correct answer | Verification |", "|---|---|---|---|"]
    for r in rows:
        ans = r["correct_answer"].replace("\n", "<br>").replace("|", "\\|")
        note = f" *{r['note']}*" if r["note"] else ""
        md.append(f"| {r['part']} | {r['max_points']} | {ans}{note} | {r['verification']} |")
    (out / f"{stem}_correct_answers.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    index.append(f"| [{stem}]({stem}_correct_answers.md) | {head['course']} {head['term']} | "
                 f"{len(rows)} | {sum(r['max_points'] for r in rows):g} |")
(out / "INDEX.md").write_text("\n".join(index) + "\n", encoding="utf-8")
print("wrote", len(by_exam), "answer keys →", out)
