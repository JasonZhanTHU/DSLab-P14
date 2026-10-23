# This is an invented demonstration

The rubric, question statements, two typed submissions and two result JSON files were newly authored for this source package. They are not an actual instructor exam, a real student's work, a model evaluation dataset or outputs obtained from a model.

There are five criteria totaling six points. Exam001 demonstrates complete correct work (six points). Exam002 deliberately contains an ambiguous MC choice, incorrect arithmetic in an otherwise correct distance relation, and a later consistent follow-through result (four points). The assigned example scores illustrate the stated synthetic rubric, not an empirical accuracy claim.

`synthetic_evals` is kept distinct from live `evals`. The tests copy these authored fixtures into a temporary workspace solely to exercise compilation. It does not create scoring-provenance sidecars that would falsely describe them as API results. A live scorer will refuse to silently resume those copied results; use a new output directory for any explicitly authorized live toy test.

`approved_for_scoring` starts false. Do not turn this example into a real course merely by changing its title. Start a clean workspace and replace every synthetic criterion, note, reference key and problem statement with the instructor's approved materials.
