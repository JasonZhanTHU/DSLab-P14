# ERFA-Exam-Bench

An LLM benchmark built from real ETH Zürich Earth-sciences / mathematics / physics
exams (scraped from the ERFA community-solutions archive into `../out`). Each item
is one exam (sub-)question paired with the **official** reference answer from that
exam's *Musterlösung*, a point-allocated grading rubric, and any figure the question
needs. Models are scored by an LLM judge against the rubric.

## Why these 6 exams (and not all 111)

The archive has 111 exams, but a benchmark needs a *trustworthy answer key*. Two facts
decided the scope:

- The scraped community answers (`answers.json`) are **empty** across the whole corpus —
  there are no crowd solutions to use.
- Only **7 exams** ship an official `solution.pdf`. Of those, one
  (`kristalleundmineralien`) is **excluded**: its `solution.pdf` is the *2014* crystallography
  solution (20 faces) while its `exam.pdf` is the *2015* Gruppe-1 exam (14 faces) — they
  don't match, so there is no valid official key for that exam.

That leaves **6 exams with genuinely official solutions**, which is the entire benchmark.
This directly reflects the design rule below.

### Provenance rule (reference ≠ whatever was lying around)

Every reference answer comes **only** from an official solution PDF. In particular:

- The **grey carry-forward values** printed on the two Kartenpraktikum exam sheets are
  explicitly labelled *"KEINE Lösungen"* (not solutions — hints for later sub-parts). They are
  **not** used; the answers here are the real values from the `solution.pdf` (e.g. fold limbs
  `085/22`, not the sheet's hint `094/38`).
- Where a solution itself flags an error (*"stimmt nicht, steht aber so im Skript"*), the
  rubric scores the geologically correct content, not the erratum.

## The exams

| Exam file | Course | Term | Lang | Items | Points | Notes |
|---|---|---|---|---|---|---|
| `bfyvac29.pdf` | Physik I/II (Probeprüfung) | 2018 | de | 10 | 28 | 6 physics problems; point values benchmark-assigned (`points_source=assigned`) |
| `m0kj6fp1.pdf` | Mathematik I/II (Basisprüfung) | H2006 | de | 16 | 50 | complex analysis, ODEs, linear algebra, vector calc |
| `pifr77kc.pdf` | Mathematik I/II – Systemanalyse | H2005 | de | 12 | 25 | reservoir/box-model ODEs |
| `s475u9b8.pdf` | Metamorphose & Magmatismus II | FS2005 | de | 6 | 30 | phase diagrams (figures required) |
| `k9mytfrn.pdf` | Kartenpraktikum I | 2014 | de | 14 | 28* | geological map analysis (map required) |
| `ja9djbrh.pdf` | Kartenpraktikum I | 2013 | de | 12 | 30 | geological map analysis (map required) |

70 items total, 191 points; **65 items (170.5 pts) are auto-gradable**. The 5 remaining
are pure drawing/construction tasks (profiles, borehole-area maps, a qualitative sketch) —
kept in the set for completeness but flagged `auto_gradable: false` and skipped by the grader
by default. (*2014's sheet reserves 2 of its 30 points for neatness, which is not a task.)

Most questions are in German; several are **multimodal** — they reference a figure
(phase diagram, geological map, physics sketch) rendered from the source PDF into `figures/`.

## Layout

```
src/        all code (paths.py holds the locations every script uses)
data/       everything the code reads or writes
script/     command-line entry points: run any of them from anywhere, e.g. benchmark/script/run_model
```

```
data/tasks.jsonl    the benchmark (one JSON object per line) — the authoritative dataset
data/figures/       PNG renders of the figures referenced by tasks (text-mode input)
data/clips/         full exam-page renders + manifest.json (vision-only "clips" input)
data/answers/       verified answer key per exam
data/derived/       second tier (exams without an official solution file)
data/runs/          model answers          data/scores/   judge scores
data/cli/           one scoring workspace per exam: rubric PDF, manifest, config, submissions, results
data/groundwater2020/  separate local-model experiment (code in src/groundwater2020/)

src/build_tasks.py src/build_figures.py src/build_clips.py src/redact_clips.py src/build_answer_keys.py   regenerate data/
src/run_model.py    runs a model-under-test → data/runs/<model>.jsonl  (+ --clips mode)
src/grade.py        LLM-as-judge; scores a run against the rubrics → data/scores/*.jsonl
src/cli_scoring.py  builds the scoring workspaces data/cli/<exam>/ and reports their scores
src/scoring/        whole-exam scoring code: prepare_exam, score_exams, compile_ai_grades, PDF guards (docs/scoring/)
tests/              offline tests of src/scoring (fixtures: tests/fixtures/minimal_exam)
src/verify/         independent re-derivations of the answer keys
script/<name>       build_tasks build_figures build_clips build_answer_keys run_model grade
                    cli_build cli_prepare cli_candidates cli_score cli_report cli_compile cli_normalize test
```

The scraped source exams stay in `../out`. Setup once: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`.
Below, `python3 run_model.py` / `grade.py` mean `script/run_model` / `script/grade`; paths like `runs/…`
mean `data/runs/…`.

## Two input modes

The same `tasks.jsonl` (and the same rubrics/grader) backs two ways of presenting
the questions to the model:

- **Text mode (default).** The model gets the transcribed `question` (LaTeX for math)
  plus the relevant figure image(s) from `figures/`. Tests reasoning given a clean question.
- **Clips mode (`run_model.py --clips`).** The model gets **only page images of the exam**
  (`clips/`) and **no transcribed text at all** — it must read every task off the images
  itself. One API call per exam ("solve every question on these pages"); each item reuses
  that exam's response for grading. This is the most faithful "sit the real paper" setting
  and folds OCR + figure-reading into the score. The transcribed text is still used, but only
  as the grader's reference key — never shown to the candidate.

```bash
python3 run_model.py --clips --model claude-opus-5-5     # → runs/claude-opus-5-5.clips.jsonl
python3 grade.py runs/claude-opus-5-5.clips.jsonl        # same grader, same rubrics
```

A worked example is checked in: `runs/demo-opus-4-8.clips.jsonl` /
`scores/demo-opus-4-8.clips.scores.jsonl` — the Physik exam solved vision-only (the author
model read `clips/bfyvac29_p01..p06.png` with no text) and graded against the official
Musterlösung (28/28). It's a pipeline demonstration, not a competitive result: for a real
comparison, run `--clips` against your chosen model via the API and grade with an independent
judge.

### Task schema (`tasks.jsonl`)

| field | meaning |
|---|---|
| `id` | stable item id, e.g. `meta_1c` |
| `course`, `course_slug`, `exam_name`, `exam_id`, `term`, `language` | provenance |
| `part` | sub-question label, e.g. `"1c"` |
| `question` | the question text (LaTeX for math), self-contained |
| `figures` | `[{file, caption}]` — images to show the model (paths relative to this dir) |
| `max_points` | points for this item |
| `points_source` | `official` (marked on the exam) or `assigned` (physik, unmarked) |
| `answer_modality` | `numeric` / `short_answer` / `derivation` / `conceptual` / `drawing` |
| `auto_gradable` | `false` for drawing/construction items |
| `reference_answer` | the official answer (from the Musterlösung) |
| `reference_source` | always `official_solution_pdf` |
| `rubric` | `[{points, criterion}]`, summing to `max_points` |
| `source_exam_pdf`, `source_solution_pdf` | paths into `../out` |
| `notes` | tolerances / caveats for the grader |

## Scoring methodology

LLM-as-judge with a point-allocated rubric. For each item the judge sees the question,
the official reference answer, the rubric, and the candidate's answer, and awards points
per criterion with a short justification (stored for auditing). The judge is instructed to:

- treat the reference as authoritative but accept **equivalent** answers (equivalent algebraic
  forms; a direction vector times any nonzero scalar; an orientation given as the opposite
  azimuth ±180°);
- apply the stated numeric tolerance, or default to ~5% (±8° for orientations, ±10° for
  stress axes) when none is given;
- give partial credit per criterion; never exceed a criterion's or the item's maximum;
- award 0 for empty / irrelevant / refused answers.

Scores are reported per exam and overall as `awarded / possible` points and a percentage.

### Run it

```bash
pip install anthropic            # and set ANTHROPIC_API_KEY, or `ant auth login`

# 1) get a model's answers (figures are sent automatically for multimodal items)
python3 run_model.py --model claude-opus-5-5          # → runs/claude-opus-5-5.jsonl
python3 run_model.py --model claude-sonnet-5-5         # another model to compare

# 2) grade them against the official rubrics
python3 grade.py runs/claude-opus-5-5.jsonl            # → scores/…; prints per-exam table
```

Both scripts default to `claude-opus-5-5`; override with `--model` / `--judge`. Use
`--limit N` on `run_model.py` for a cheap smoke test. **Use a judge at least as capable as
the strongest model under test**, and ideally a different model family than the candidate to
reduce self-preference bias.


## Pre-printed hints & verified answer keys

Both Kartenpraktikum sheets (2013, 2014) ship with grey hint values already typed into answer
boxes (e.g. `094/38`, `301/74`, `332°`, `16°`). They are *not* solutions, and a vision-only model
would simply copy them. `redact_clips.py` (run by `build_clips.py`) white-outs them, plus the
sentence explaining them, in the clips of both exams; locations come from the PDF text layer. The
other four exams (Physik, Mathematik, Systemanalyse, Magmatismus) carry no pre-printed answers.

`answers/` holds a verified key per exam (`answers/INDEX.md`; generated by
`build_answer_keys.py` from `tasks.jsonl`), listing for each item how it was checked:

- `verify/numeric_checks.py` re-derives the Physik / Mathematik / Systemanalyse / Magmatismus numbers
  (37/38 agree; the one DIFF is the erratum below).
- `verify/kartenpraktikum_geometry_check.py` re-derives fold axis, opening angle, slip pitch,
  principal stresses (Coulomb, σ1 at 30° to the fault — reproduces both official stress sets
  exactly) and offsets for both map exams, to graphical precision.
- Map readings (limbs, thicknesses, fault attitudes) and drawing tasks are official-only; the
  official drawings are in `answers/*_official_drawings/`.

Findings from verification (all reflected in `tasks.jsonl`):

- **Erratum in an official solution:** Magmatismus table, T₂: enstatite is printed as 56.6 % (the row
  sums to 101 %); the lever rule gives 55.6 %.
- **Approximations the exam permits:** Systemanalyse 2e/2f/3d use e⁻¹≈1/3 and a zeroed small
  coefficient; the exact values (221 kg/a, 0.074 mg/m³, ≈36 d) are accepted as well.
- **Hint-derived alternates dropped:** the official "bzw." values (e.g. 104°, 93 m, 120 m) are what
  you get when building on the exam's hints; they are no longer accepted.
- **A transcription error of mine, fixed:** Mathematik 1a's second condition is a modulus equation
  (the extracted text had lost the absolute-value bars). Vision-only clips mode is immune to this class
  of error, since the model reads the original page.


## Derived tier (`derived/`)

A second, **separate** tier for exams without an official solution file (`derived/tasks_derived.jsonl`, 48 items,
14 exams: Groundwater, Geochemie, Isotopengeochemie). One exam (Groundwater Assessment I) has the lecturer's solutions
embedded in the exam PDF and counts as official-embedded; the rest are computed from the question data and asserted in code.
Scores must not be mixed with the official tier. See `derived/README.md` and `derived/TRIAGE.md`. Run it with
`python3 run_model.py --tasks derived/tasks_derived.jsonl [--clips]` and grade with `python3 grade.py <run> --tasks derived/tasks_derived.jsonl`.

## Command-line scoring

The same 6 exams / 65 auto-gradable items / 170.5 points, re-expressed for the whole-PDF scoring code in `src/scoring`
(one structured result per exam; guides in `docs/scoring/`). The outline is unchanged: `tasks.jsonl` stays the
authoritative dataset and `cli_scoring.py` derives everything from it.

| benchmark | scoring workspace (`data/cli/<exam>/`) |
|---|---|
| exam (`bfyvac29.pdf`, …) | one workspace, `exam_config.json` |
| item (`physik_a2b`, part `2b`) | `part_id` `2b`, `problem_id` `2` |
| rubric criterion `{points, criterion}` | manifest item `rubric_item` `2b.1`, `continuous` score mode, `rubric_name` = criterion (truncated) |
| question + figures + `reference_answer` + `notes` | `Rubrics/rubric.pdf` (a "Aufgabe 2b" section with the criteria as headings), item `notes` |
| judge rules of `grade.py` (equivalence, 5 % / ±8° / ±10° tolerance, partial credit) | `notes` in `exam_config.json` |
| model answers (`runs/*.jsonl`) | `RawExams/ExamNNN.pdf` (text and `--clips` runs both work; no model name inside) |
| `scores/*.jsonl` | `evals/ExamNNN.json` (+ provenance), `compile_ai_grades.py` exports |

Drawing items (`auto_gradable: false`) are left out, as in `grade.py`; `build --include-drawing` adds them.

```bash
script/cli_build                                  # data/tasks.jsonl → data/cli/<exam>/  (--tasks data/derived/tasks_derived.jsonl for the derived tier)
script/cli_prepare                                # prepare_exam.py in every workspace (checks headings, writes prompt.txt)

script/run_model --model claude-opus-5-5          # unchanged: data/runs/claude-opus-5-5.jsonl (or --clips)
script/cli_candidates data/runs/claude-opus-5-5.jsonl   # → data/cli/<exam>/RawExams/Exam001.pdf

# scoring: copy .env.example to .env and fill it, review the rubric PDFs, set "approved_for_scoring": true
script/cli_score --check && script/cli_score
script/cli_report --by-part                       # per-exam awarded/possible, like grade.py's table
script/cli_compile data/cli/bfyvac29/exam_config.json --require-complete   # xlsx/csv + human-review list
```

Differences from `grade.py` worth knowing: the judge is whatever model `.env` points at (Azure or
OpenAI-compatible, not the Anthropic SDK); it scores a whole exam in one call and returns an exam-level
`human_review_recommended` flag instead of per-item justifications only; and every workspace starts with
`approved_for_scoring=false`, so nothing is sent until you flip it. A run's PDF is built from `run_model.py`
output, so the candidate sees nothing but its own answers.

## Limitations & honest caveats

- **Judge variance.** LLM grading is not perfectly reproducible; spot-check `scores/*.jsonl`
  justifications, and consider grading each run 2–3× and averaging for headline numbers.
- **Figure-dependent reading.** Map/phase-diagram items require reading values off an image;
  scores there reflect both reasoning *and* visual estimation, and depend on the render DPI
  in `figures/`.
- **Small, single-institution, mostly-German set** (6 exams, one university). It measures
  undergraduate Earth-science/math/physics problem-solving, not general capability.
- **Physik point weights are benchmark-assigned** (the original sheet marks none); the other
  five exams use the points printed on the official sheets.
- **Contamination risk is low but not zero** — these PDFs sit behind an authenticated archive,
  but treat absolute scores with the usual caution for any public-adjacent benchmark.
- **Drawing tasks** (`auto_gradable: false`) can't be judged from text; run with
  `grade.py --include-drawing` only if you also feed the model's described construction, and
  read those scores loosely.

## Regenerating

```bash
script/build_figures     # re-render data/figures/ from ../out exam PDFs
script/build_tasks       # re-emit data/tasks.jsonl (validates every rubric sums to max_points)
```
