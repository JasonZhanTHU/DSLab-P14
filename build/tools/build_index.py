#!/usr/bin/env python3
"""Write data/INDEX.md: one row per ERFA course with exams, topic map, catalogue entry and gathered material."""
import glob, json, os
from pathlib import Path

OUT = Path("data")

# Courses without ERFA exams: point to the best gathered material elsewhere in the tree.
CROSS = {
    "continuummechanics": "`strukturgeologie/lecture_material/web/www.files.ethz.ch/continuum mec.pdf` (Burg)",
    "earthquakesiseismotectonics": "`seismologie/` (seismo-live, Fichtner notes), `strukturgeologie/` (faults)",
    "engineeringseismology": "`seismologie/`, `ingenieurgeologie/`",
    "explorationandenvironmentalgeophysics": "`reflectionseismologyprocessing/lecture_material/` (van der Kruk, *Reflection seismic 1*)",
    "geobiologie": "`paleoceanographybiogeochemicalcycles/`, `sedimentologyii…/`",
    "kartenpraktikum2geologicalmapanalysis": "`kartenpraktikumi/EXAM_TOPICS.md` (same task types)",
    "mathematicalmethods": "`mathematikiii/`, `mathematikiii_0/` (old D-MATH exams)",
    "mathematikivstatistik": "archived statistics summary in `lecture_material/`",
    "numericalmodellingforappliedgeophysics": "student exercise repos in `lecture_material/github/`",
    "ozeanographieundhydrogeologie": "`hydrogeologie/`, `groundwater/`, `klimasysteme/`",
    "planetaryphysicsandchemistry": "`planetarygeochemistry/`",
    "quartrgeologieundgeomorphologie": "`kryosphre/`, `sedimentologie/`",
    "reflectionseismologyprocessing": "`lecture_material/rescoll_146502/` (*Reflection seismic 1*, 20 chapters)",
    "snowcoverphysicsandmodelling": "`kryosphre/`",
    "soilmechanicsandfoundationengineering": "`ingenieurgeologie/`, `rockmechanicsandrockengineering/`",
    "wettersysteme": "`atmosphre/` (IAC scripts), `klimasysteme/`",
}


def count_files(p):
    return sum(1 for f in glob.glob(f"{p}/**/*", recursive=True)
               if os.path.isfile(f) and not f.endswith(("sources.json", ".txt")))


def main():
    cats = json.loads((OUT / "categories.json").read_text())
    rows = []
    for c in sorted(cats, key=lambda c: c["displayname"].lower()):
        s = c["slug"]
        if s in ("default", "bscthesis"):
            continue
        d = OUT / s
        exams = len(glob.glob(f"{d}/exams/*/exam.txt"))
        docs = len(glob.glob(f"{d}/documents/*.json"))
        mat = count_files(d / "lecture_material")
        vvz = json.loads((d / "course" / "vvz.json").read_text()) if (d / "course" / "vvz.json").exists() else []
        codes = ", ".join(v["code"] for v in vvz) or "— (no longer offered)"
        lect = "; ".join(v["lecturers"] for v in vvz[:1])
        topics = f"[topics]({s}/EXAM_TOPICS.md)" if (d / "EXAM_TOPICS.md").exists() else "—"
        course = f"[catalogue]({s}/course/COURSE.md)" if (d / "course" / "COURSE.md").exists() else "—"
        extra = CROSS.get(s, "")
        related = f"[related]({s}/RELATED.md)" if (d / "RELATED.md").exists() else "—"
        rows.append(f"| {c['displayname']} | {codes} | {lect} | {exams} | {topics} | {course} | {docs} | {mat} | {related} | {extra} |")
    total_mat = count_files(OUT / "*" / "lecture_material")
    L = ["# ERFA study collection — index", "",
         "Per-course study material for the ETH Earth Sciences courses in the ERFA exam collection. "
         "Everything is organised under `data/<course-slug>/`:", "",
         "| Path | What it is |", "|---|---|",
         "| `EXAM_TOPICS.md` | **Start here.** What the exams actually ask (ranked by frequency where there are several exams), exam format, and where each topic is covered in the material below |",
         "| `exams/<id>/exam.pdf`, `exam.txt` | ERFA exams; `exam.txt` is OCR (EasyOCR de+en) of the scanned PDF, `answers.json` holds community answers |",
         "| `documents/` | Student summaries and notes uploaded to ERFA |",
         "| `course/COURSE.md` | Official ETH course catalogue entry (VVZ): number, lecturers, content, literature, exam mode, allowed aids |",
         "| `lecture_material/rescoll_<id>/` | Lecture scripts from the ETH Research Collection (open access) |",
         "| `lecture_material/wayback/<source>/` | Archived ETH course files (scripts, slides, exercises, old exams) recovered from the Wayback Machine; `sources.json` has the original URL and snapshot |",
         "| `lecture_material/web/<host>/` | Files from course web pages that are still public |",
         "| `lecture_material/github/` | Course-related public repositories (notebooks, exercises) |",
         "| `lecture_material/old_exams_dmath_*` | D-MATH old exams with solutions |",
         "| `RELATED.md` | Courses on the same topics at other universities: MIT OpenCourseWare, open textbooks (UBC, Alberta, BCcampus), lecture material from Basel, LMU, Hamburg, Cornell, Washington, the Groundwater Project. Files live once in `data/_related/` (overview: [_related/README.md](_related/README.md)) |",
         "| `references/` | Older keyword-picked Wikipedia background articles; low relevance, superseded by the above |",
         "",
         f"Totals: {sum(len(glob.glob(f'data/{c['slug']}/exams/*/exam.txt')) for c in cats)} exams with text, "
         f"{len(glob.glob('data/*/documents/*.json'))} ERFA student documents, {total_mat} gathered lecture-material files.", "",
         "Course pages on Moodle and most current slides need an ETH login and are not included. "
         "Where a course page links material behind `auth/nethz`, `COURSE.md` keeps the link.", "",
         "## Courses", "",
         "| Course | Catalogue no. | Lecturers (current) | Exams | Exam topics | Course info | ERFA docs | Lecture files | Other universities | See also |",
         "|---|---|---|---|---|---|---|---|---|---|"] + rows + [""]
    (OUT / "INDEX.md").write_text("\n".join(L))
    print(len(rows), "courses ->", OUT / "INDEX.md")


if __name__ == "__main__":
    main()
