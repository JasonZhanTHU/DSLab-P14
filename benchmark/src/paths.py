"""Single source of truth for where things live. Every script imports from here."""
from pathlib import Path

SRC = Path(__file__).resolve().parent
BENCH = SRC.parent                     # benchmark/
DATA = BENCH / "data"                  # tasks, figures, clips, answers, runs, scores, exam workspaces
SCRAPE = BENCH.parent                  # project root: data/ (scraped exams), build/ (scrapers, ref_tools.py)
SCORING = SRC / "scoring"              # exam-scoring toolkit (prepare/score/compile)
