#!/usr/bin/env python3
"""Author the ERFA-Exam-Bench task set and emit tasks.jsonl.

Each record is one gradable exam (sub-)question with an OFFICIAL reference
answer taken from the exam's Musterlösung (solution.pdf). The data below was
transcribed and verified by hand against the source PDFs in ../out; equations
are written in LaTeX, figures are referenced by file under figures/.

Provenance rule (see README): reference answers come only from the official
solution PDFs. Values that the exam sheets print in grey as carry-forward hints
("KEINE Lösungen") are deliberately NOT used. The one exam whose solution.pdf
does not match its exam.pdf (kristalleundmineralien: 2014 solution vs 2015 exam)
is excluded for lack of a valid official key.
"""
import json
from pathlib import Path
from paths import DATA

OUT = DATA
TASKS = []


def add(**kw):
    kw.setdefault("reference_source", "official_solution_pdf")
    kw.setdefault("points_source", "official")
    kw.setdefault("auto_gradable", True)
    kw.setdefault("figures", [])
    kw.setdefault("notes", "")
    # rubric points should sum to max_points (soft check at build time)
    s = round(sum(r["points"] for r in kw["rubric"]), 3)
    if abs(s - kw["max_points"]) > 1e-6:
        raise ValueError(f"{kw['id']}: rubric sums to {s}, max_points={kw['max_points']}")
    TASKS.append(kw)


# --------------------------------------------------------------------------
# EXAM 1 — Physik I/II, Probeprüfung 2018 (bfyvac29)
# Fully image-based exam; transcribed via vision. Point values are not printed
# on the original sheet, so they are benchmark-assigned (points_source="assigned").
# --------------------------------------------------------------------------
PHYS = dict(course="Physik I/II", course_slug="physikiii",
            exam_name="Probeprüfung Physik I_2018", exam_id="bfyvac29.pdf",
            term="2018", language="de",
            source_exam_pdf="data/physikiii/exams/bfyvac29.pdf/exam.pdf",
            source_solution_pdf="data/physikiii/exams/bfyvac29.pdf/solution.pdf")

add(**PHYS, id="physik_a1", part="1", points_source="assigned",
    max_points=4, answer_modality="derivation",
    figures=[{"file": "figures/physik_p1.png", "caption": "Aufgabe 1: Achterbahn / Looping (Radius r)."}],
    question=("Aufgabe 1 (Achterbahn). Ein Wagen der Masse m = 80 kg soll im Scheitel "
              "des Loopings (Radius r = 5 m) gerade noch so viel Geschwindigkeit besitzen, "
              "dass er mit dem Gleis in Kontakt bleibt. Sämtliche Reibung werde "
              "vernachlässigt. Wie gross muss die Anfangshöhe h sein?"),
    reference_answer=("Am Scheitel: Gewichtskraft = Zentripetalkraft ⇒ v² = g·r. "
                      "Energieerhaltung von der Starthöhe h (aus der Ruhe) bis zum Scheitel "
                      "(Höhe 2r): g·h = g·2r + ½v² = g·2r + ½g·r ⇒ h = (5/2)·r = 12.5 m "
                      "(unabhängig von m und g)."),
    rubric=[{"points": 1.5, "criterion": "Scheitelbedingung v²=g·r (Gewicht = Zentripetalkraft)"},
            {"points": 1.5, "criterion": "Energieerhaltung korrekt aufgestellt (Scheitel auf Höhe 2r)"},
            {"points": 1.0, "criterion": "Ergebnis h = 2.5·r = 12.5 m"}])

add(**PHYS, id="physik_a2a", part="2a", points_source="assigned",
    max_points=1.5, answer_modality="derivation",
    figures=[{"file": "figures/physik_p2.png", "caption": "Aufgabe 2: Feder (Dehnung ξ) und mathematisches Pendel."}],
    question=("Aufgabe 2 (Pendel). Eine Feder wird beim Anhängen einer Masse m um ξ gedehnt "
              "und schwingt mit der Periode T. (a) Wie lang muss ein mathematisches Pendel "
              "gleicher Schwingungsdauer sein?"),
    reference_answer=("Aus T = 2π√(ℓ/g) folgt ℓ = g·(T/2π)². Da für die Feder m·g = k·ξ und "
                      "T = 2π√(m/k) = 2π√(ξ/g) gilt, ist die äquivalente Pendellänge ℓ = ξ."),
    rubric=[{"points": 1.0, "criterion": "ℓ = g·(T/2π)² aus der Pendelformel"},
            {"points": 0.5, "criterion": "Erkenntnis ℓ = ξ (über k·ξ = m·g)"}])

add(**PHYS, id="physik_a2b", part="2b", points_source="assigned",
    max_points=1.5, answer_modality="derivation",
    question=("Aufgabe 2 (Pendel), Fortsetzung. Daten: m_Mond = 7·10²² kg, r_Mond = 2·10⁶ m, "
              "m_Erde = 6·10²⁴ kg, r_Erde = 6·10⁶ m. (b) Um wieviel ändert sich die Periode T, "
              "wenn das Pendel auf den Mond transportiert wird?"),
    reference_answer=("T_E/T_M = √(g_M/g_E) = (r_E/r_M)·√(m_M/m_E) ≈ 0.3. "
                      "Die Periode auf dem Mond ist also länger: T_M ≈ T_E/0.3 ≈ 3.3·T_E."),
    rubric=[{"points": 1.0, "criterion": "T_E/T_M = √(g_M/g_E) = (r_E/r_M)√(m_M/m_E)"},
            {"points": 0.5, "criterion": "Zahlenwert ≈0.3 ⇒ Periode ~3.3× länger auf dem Mond"}])

add(**PHYS, id="physik_a2c", part="2c", points_source="assigned",
    max_points=1.0, answer_modality="derivation",
    question=("Aufgabe 2 (Pendel), Fortsetzung. (c) Was muss am Pendel verändert werden, "
              "damit es auf dem Mond mit derselben Periode schwingt?"),
    reference_answer=("T_M = T_E ⇒ ℓ_M = ℓ_E·(g_M/g_E) = ℓ_E·(m_M/m_E)·(r_E/r_M)² ≈ 0.1·ℓ_E. "
                      "Die Pendellänge muss auf etwa ein Zehntel verkürzt werden."),
    rubric=[{"points": 0.5, "criterion": "ℓ_M = ℓ_E·(g_M/g_E) hergeleitet"},
            {"points": 0.5, "criterion": "ℓ_M ≈ 0.1·ℓ_E (Länge auf ~1/10 verkürzen)"}])

add(**PHYS, id="physik_a3", part="3", points_source="assigned",
    max_points=4, answer_modality="derivation",
    figures=[{"file": "figures/physik_p3.png", "caption": "Aufgabe 3: p–V-Diagramm des Dieselprozesses."}],
    question=("Aufgabe 3 (Dieselmotor). Der Dieselprozess besteht aus zwei Adiabaten, einer "
              "Isochore und einer Isobare (Schritte 1→2 adiabatisch, 2→3 isobar, 3→4 "
              "adiabatisch, 4→1 isochor). Berechnen Sie den Wirkungsgrad η_Diesel für "
              "Kompressionsverhältnis r_k = 15, Expansionsverhältnis r_e = 5 und "
              "Adiabatenexponent γ = 1.4. Behandeln Sie den Motor als ideale "
              "Wärmekraftmaschine mit idealem Gas."),
    reference_answer=("η = 1 − ΔQ_1/ΔQ_2 mit ΔQ_1 = C_V·(V_1/R)(p_4−p_1) (isochor) und "
                      "ΔQ_2 = C_P·(p_2/R)(V_3−V_2) (isobar). Mit den Adiabaten p_1V_1^γ=p_2V_2^γ, "
                      "p_2V_3^γ=p_4V_1^γ folgt "
                      "η = 1 − (1/γ)·[(1/r_e)^γ − (1/r_k)^γ]/[(1/r_e) − (1/r_k)] ≈ 0.558 (≈56 %)."),
    rubric=[{"points": 1.0, "criterion": "Umgesetzte Wärmen ΔQ_1 (isochor), ΔQ_2 (isobar)"},
            {"points": 1.0, "criterion": "η = 1 − ΔQ_1/ΔQ_2 angesetzt"},
            {"points": 1.0, "criterion": "Adiabatengleichungen eingesetzt → Ausdruck in r_k, r_e, γ"},
            {"points": 1.0, "criterion": "Zahlenwert η ≈ 0.558"}])

add(**PHYS, id="physik_a4a", part="4a", points_source="assigned",
    max_points=3, answer_modality="derivation",
    figures=[{"file": "figures/physik_p4.png", "caption": "Aufgabe 4: Massenspektrometer (Quelle S, Spannung V, Feld B, Abstand x)."}],
    question=("Aufgabe 4 (Massenspektrometer). Eine Ionenquelle S erzeugt Ionen der Masse m "
              "und Ladung q; die anfangs ruhenden Ionen werden durch das Potentialgefälle V "
              "beschleunigt und im homogenen Magnetfeld B auf eine Platte im Abstand x vom "
              "Eintrittsspalt abgelenkt. (a) Finden Sie einen Ausdruck für die Masse des Ions "
              "in Abhängigkeit von q, B, V und x."),
    reference_answer=("Beschleunigung: qV = ½mv² ⇒ v² = 2qV/m. Kreisbahn: qvB = m v²/r ⇒ r = mv/(qB). "
                      "Treffabstand x = 2r = 2mv/(qB). Auflösen ⇒ m = q·B²·x² / (8V)."),
    rubric=[{"points": 1.0, "criterion": "Energiebilanz qV = ½mv² ⇒ v = √(2qV/m)"},
            {"points": 1.0, "criterion": "Radius r = mv/(qB) und x = 2r"},
            {"points": 1.0, "criterion": "Ergebnis m = qB²x²/(8V)"}])

add(**PHYS, id="physik_a4b", part="4b", points_source="assigned",
    max_points=3, answer_modality="numeric",
    question=("Aufgabe 4 (Massenspektrometer), Fortsetzung. (b) Für Uranatome sei q = +2e und "
              "V = 10 kV. Welcher Wert muss für B verwendet werden, um ²³⁵U und ²³⁸U um mehr als "
              "5 mm zu trennen?"),
    reference_answer=("Δx = x_238 − x_235 = (2/B)·(√(2·m_238·V/q) − √(2·m_235·V/q)). "
                      "Auflösen nach B: B = (2/Δx)·(√(m_238·V/e) − √(m_235·V/e)). "
                      "Mit Δx = 5 mm, q = 2e, V = 10 kV ⇒ B ≈ 0.4 T."),
    rubric=[{"points": 1.5, "criterion": "Δx als Differenz der Treffabstände mit x = (2/B)√(2mV/q)"},
            {"points": 0.5, "criterion": "nach B aufgelöst"},
            {"points": 1.0, "criterion": "Zahlenwert B ≈ 0.4 T"}])

add(**PHYS, id="physik_a5_1", part="5-1", points_source="assigned",
    max_points=3, answer_modality="derivation",
    figures=[{"file": "figures/physik_p5.png", "caption": "Aufgabe 5: Leiterrechteck (ℓ×b) in ortsabhängigem Feld B(x); Regionen (i)–(v)."}],
    question=("Aufgabe 5 (Induktionsstrom). Ein Rechteck der Länge ℓ und Breite b aus dünnem "
              "Kupferdraht (Durchmesser 2R, Leitfähigkeit σ = 1/ρ) bewegt sich mit Geschwindigkeit "
              "v parallel zur x-Achse im Feld B(x)‖z. B ist in Gebiet (iii) der Länge s konstant "
              "gleich B₀; in (ii) bzw. (iv) steigt/fällt es linear über die Länge a; in (i),(v) ist "
              "B = 0. Das Rechteck sei ganz in einem Gebiet (ℓ≪s,a). (1) Berechnen Sie die im Draht "
              "in Wärme umgewandelte Leistung P in den Gebieten (i)–(v)."),
    reference_answer=("Fluss Φ = b·∫B dx, induzierte Spannung U_ind = −Φ̇ = −b·(dB/dx)·v·ℓ. "
                      "Widerstand des Drahtes R_Ω = 2(ℓ+b)/(σ·πR²), Strom I = σ·πR²/(2(ℓ+b))·U_ind. "
                      "Leistung P = U_ind·I = σ·πR²·b²ℓ²/(2(ℓ+b))·v²·(dB/dx)². "
                      "In (i),(iii),(v) ist dB/dx = 0 ⇒ P = 0. In (ii),(iv) ist dB/dx = ±B₀/a ⇒ "
                      "P = σ·πR²·b²ℓ²/(2(ℓ+b))·v²·B₀²/a²."),
    rubric=[{"points": 1.0, "criterion": "U_ind = −b·(dB/dx)·v·ℓ aus Φ̇"},
            {"points": 1.0, "criterion": "P = U_ind·I mit R_Ω = 2(ℓ+b)/(σπR²)"},
            {"points": 1.0, "criterion": "P=0 in (i),(iii),(v); P = σπR²b²ℓ²/(2(ℓ+b))·v²B₀²/a² in (ii),(iv)"}])

add(**PHYS, id="physik_a5_2", part="5-2", points_source="assigned",
    max_points=3, answer_modality="derivation",
    question=("Aufgabe 5 (Induktionsstrom), Fortsetzung. (2) Berechnen Sie die totale Kraft F "
              "auf das Rechteck in den Gebieten (i)–(v)."),
    reference_answer=("Aus P = F_ext·v folgt F = −F_ext = −P/v. In (i),(iii),(v): F = 0. "
                      "In (ii),(iv): F = −σ·πR²·b²ℓ²/(2(ℓ+b))·v·B₀²/a² (bremsend). "
                      "Gleiches Resultat über F = b·I·[B(x₀+ℓ)−B(x₀)]."),
    rubric=[{"points": 1.5, "criterion": "F = −P/v (Leistung = F_ext·v)"},
            {"points": 1.5, "criterion": "F=0 in (i),(iii),(v); F = −σπR²b²ℓ²/(2(ℓ+b))·vB₀²/a² in (ii),(iv)"}])

add(**PHYS, id="physik_a6", part="6", points_source="assigned",
    max_points=4, answer_modality="numeric",
    question=("Aufgabe 6 (Planck'sches Wirkungsquantum). Bei Beleuchtung einer Cs-Photokathode "
              "mit einer Quecksilberdampflampe wurden für zwei Spektrallinien die maximalen "
              "Gegenspannungen gemessen: UV-Linie λ₁ = 365.4 nm, U₁ = 1.603 V; violette Linie "
              "λ₂ = 435.8 nm, U₂ = 1.054 V. Berechnen Sie daraus das Planck'sche Wirkungsquantum h "
              "und das Austrittspotential Φ der Photokathode."),
    reference_answer=("Photoeffekt: e·U = h·c/λ − e·Φ. Differenz der beiden Gleichungen: "
                      "e·(U₁−U₂) = h·c·(1/λ₁ − 1/λ₂) ⇒ h = (e/c)·(U₁−U₂)/(1/λ₁ − 1/λ₂) ≈ 6.64·10⁻³⁴ J·s. "
                      "Austrittspotential: Φ = (h/e)(c/λ₁) − U₁ = (U₁−U₂)/(1 − λ₁/λ₂) − U₁ ≈ 1.80 V."),
    rubric=[{"points": 1.0, "criterion": "Photoeffekt-Gleichung e·U = hc/λ − eΦ"},
            {"points": 1.0, "criterion": "Differenzbildung eliminiert Φ"},
            {"points": 1.0, "criterion": "h ≈ 6.6·10⁻³⁴ J·s"},
            {"points": 1.0, "criterion": "Φ ≈ 1.8 V"}])

# --------------------------------------------------------------------------
# EXAM 2 — Mathematik I/II Basisprüfung, Herbst 2006 (m0kj6fp1); total 50
# --------------------------------------------------------------------------
MATH = dict(course="Mathematik I/II", course_slug="mathematikiii",
            exam_name="Basisprüfung Mathematik I/II, Herbst 2006", exam_id="m0kj6fp1.pdf",
            term="H2006", language="de",
            source_exam_pdf="data/mathematikiii/exams/m0kj6fp1.pdf/exam.pdf",
            source_solution_pdf="data/mathematikiii/exams/m0kj6fp1.pdf/solution.pdf")

add(**MATH, id="math_1a", part="1a", max_points=4, answer_modality="derivation",
    question=(r"Bestimmen Sie Real- und Imaginärteil der komplexen Zahl $z$, für welche gilt "
              r"$\arg\!\left(\frac{z}{1-i}\right)=\arg\!\left(\frac{i}{i^{3}}\right)$ und "
              r"$\left|\frac{z}{1-i}\right|=\left|e^{7\pi i/12}\cdot\frac{5-3\sqrt{3}\,i}{1+2\sqrt{3}\,i}\right|$."),
    reference_answer=(r"Mit $z=re^{i\varphi}$: aus dem Argument $\varphi+\pi/4=\pi\Rightarrow\varphi=3\pi/4$; "
                      r"aus dem Betrag $r/\sqrt2=\sqrt{(25+27)/(1+12)}=\sqrt{52/13}=2\Rightarrow r=2\sqrt2$ (die Betragsgleichung ist eine Gleichung für $|z/(1-i)|$, nicht für die Phase). "
                      r"Also $z=2\sqrt2\,(\cos\frac{3\pi}{4}+i\sin\frac{3\pi}{4})=-2+2i$, d.h. "
                      r"$\operatorname{Re}z=-2,\ \operatorname{Im}z=2$."),
    rubric=[{"points": 1.5, "criterion": "Argumentbedingung ⇒ φ = 3π/4"},
            {"points": 1.5, "criterion": "Betragsbedingung ⇒ r = 2√2"},
            {"points": 1.0, "criterion": "z = −2 + 2i (Re=−2, Im=2)"}])

add(**MATH, id="math_1b", part="1b", max_points=2, answer_modality="derivation",
    question=r"Bestimmen Sie den Grenzwert $\displaystyle\lim_{x\to0}\frac{\tan^{2}x}{x^{2}}$.",
    reference_answer=(r"$\lim_{x\to0}\frac{\tan^2x}{x^2}=\left(\lim_{x\to0}\frac{\tan x}{x}\right)^2=1$ "
                      r"(z.B. mit de l'Hôpital zweimal oder $\tan x\sim x$)."),
    rubric=[{"points": 1.0, "criterion": "korrekte Methode (l'Hôpital bzw. tan x ~ x)"},
            {"points": 1.0, "criterion": "Ergebnis = 1"}])

add(**MATH, id="math_1c", part="1c", max_points=3, answer_modality="derivation",
    question=(r"Berechnen Sie $\displaystyle J=\int_{1}^{e^{2}}\frac{\ln x}{x}\,dx$. "
              r"Hinweis: partielle Integration liefert eine Gleichung für $J$."),
    reference_answer=(r"Partielle Integration mit $u=\ln x,\ dv=\frac{\ln x}{x}dx$ liefert "
                      r"$J=\big[\ln^2 x\big]_1^{e^2}-J=4-J\Rightarrow 2J=4\Rightarrow J=2$. "
                      r"(Alternativ Substitution $u=\ln x$: $J=\int_0^2 u\,du=2$.)"),
    rubric=[{"points": 2.0, "criterion": "partielle Integration/Substitution korrekt ⇒ 2J = 4"},
            {"points": 1.0, "criterion": "J = 2"}])

add(**MATH, id="math_1d", part="1d", max_points=5, answer_modality="derivation",
    question=(r"Bestimmen Sie die Lösung des Anfangswertproblems "
              r"$\dot x(t)-2t\,x(t)=t,\quad x(0)=0$."),
    reference_answer=(r"Homogen: $x_h=D\,e^{t^2}$. Variation der Konstanten: $\dot D(t)=t\,e^{-t^2}$, "
                      r"$D(t)=-\tfrac12 e^{-t^2}+C$, also $x(t)=C\,e^{t^2}-\tfrac12$. "
                      r"Mit $x(0)=0\Rightarrow C=\tfrac12$: $\;x(t)=\tfrac12\big(e^{t^2}-1\big)$."),
    rubric=[{"points": 1.5, "criterion": "homogene Lösung x_h = D·e^{t²}"},
            {"points": 2.0, "criterion": "Variation der Konstanten ⇒ x = C·e^{t²} − 1/2"},
            {"points": 1.5, "criterion": "Anfangsbedingung ⇒ x(t) = ½(e^{t²} − 1)"}])

add(**MATH, id="math_2a", part="2a", max_points=3, answer_modality="conceptual",
    question=(r"Für eine gegebene Funktion $f$ betrachten wir $\dot x(t)=f\!\left(\frac{x(t)}{t}\right)$ (∗). "
              r"Skizzieren Sie die Kurven $\frac{x(t)}{t}=c$ ($c\in\mathbb{R}$) in der $(t,x)$-Ebene. "
              r"Was können Sie über die Steigungen des durch (∗) definierten Richtungsfeldes entlang "
              r"einer solchen Kurve aussagen?"),
    reference_answer=(r"$x(t)/t=c\Rightarrow x=c\,t$: die Kurven sind Geraden durch den Ursprung mit "
                      r"Steigung $c$. Entlang einer solchen Geraden ist die Steigung des Richtungsfeldes "
                      r"$\dot x=f(c)$ konstant, d.h. das Richtungsfeld ist entlang jeder Ursprungsgeraden parallel."),
    rubric=[{"points": 1.5, "criterion": "Kurven sind Ursprungsgeraden x = c·t"},
            {"points": 1.5, "criterion": "Richtungsfeld entlang ihnen konstant = f(c) (parallel)"}])

add(**MATH, id="math_2b", part="2b", max_points=3, answer_modality="derivation",
    question=(r"Lösen Sie die Differentialgleichung (∗) aus 2a für $f(u)=u^{2}$ und kontrollieren Sie "
              r"Ihre Lösung durch Einsetzen."),
    reference_answer=(r"$\dot x=(x/t)^2=x^2/t^2$. Trennung der Variablen: $-1/x=-1/t+C\Rightarrow "
                      r"x(t)=\dfrac{t}{1-C\,t}$. Kontrolle: $\dot x=\dfrac{1}{(1-Ct)^2}=\dfrac{x^2}{t^2}$ ✓."),
    rubric=[{"points": 2.0, "criterion": "Separation ⇒ x(t) = t/(1 − C·t)"},
            {"points": 1.0, "criterion": "Kontrolle durch Einsetzen"}])

add(**MATH, id="math_3a", part="3a", max_points=3, answer_modality="numeric",
    question=(r"Gegeben $A=\begin{pmatrix}0&4&1\\3&-1&1\\1&2&1\end{pmatrix}$. Bestimmen Sie $\det A$ "
              r"sowie $\det B$ für die Matrix $B$ mit "
              r"$AB=\begin{pmatrix}0&0&3\\0&2&0\\1&0&0\end{pmatrix}$."),
    reference_answer=(r"Entwicklung nach der ersten Spalte: $\det A=-3(-2)+1\cdot5=-1$. "
                      r"$\det(AB)=\det\begin{pmatrix}0&0&3\\0&2&0\\1&0&0\end{pmatrix}=-6$, also "
                      r"$\det B=\det(AB)/\det A=-6/-1=6$."),
    rubric=[{"points": 1.5, "criterion": "det A = −1"},
            {"points": 1.5, "criterion": "det(AB) = −6 ⇒ det B = 6"}])

add(**MATH, id="math_3b", part="3b", max_points=3, answer_modality="numeric",
    question=(r"Mit $C=\begin{pmatrix}6&4&-10\\4&2&-6\\-14&-8&24\end{pmatrix}$: berechnen Sie $AC$ und "
              r"bestimmen Sie damit die Matrix $B$ aus 3a ($A$ wie oben, $D=AB$)."),
    reference_answer=(r"$AC=2\,\mathrm{Id}_3$, also $A^{-1}=\tfrac12 C=\begin{pmatrix}3&2&-5\\2&1&-3\\-7&-4&12\end{pmatrix}$. "
                      r"Dann $B=A^{-1}D=\begin{pmatrix}-5&4&9\\-3&2&6\\12&-8&-21\end{pmatrix}$."),
    rubric=[{"points": 1.0, "criterion": "AC = 2·Id ⇒ A⁻¹ = ½C"},
            {"points": 2.0, "criterion": "B = A⁻¹D = [[-5,4,9],[-3,2,6],[12,-8,-21]]"}])

add(**MATH, id="math_4a", part="4a", max_points=2, answer_modality="conceptual",
    question=(r"Gegeben das System $\dot x(t)=\begin{pmatrix}1&0\\1&3\end{pmatrix}x(t)=Ax(t)$. "
              r"Was können Sie über die Gleichgewichtslösungen des Systems aussagen?"),
    reference_answer=(r"$\det A=3\neq0$, daher hat $Ax=0$ nur die triviale Lösung: einziges "
                      r"Gleichgewicht ist der Ursprung $(0,0)$."),
    rubric=[{"points": 1.0, "criterion": "det A = 3 ≠ 0 festgestellt"},
            {"points": 1.0, "criterion": "einziges Gleichgewicht (0,0)"}])

add(**MATH, id="math_4b", part="4b", max_points=4, answer_modality="derivation",
    question=(r"Bestimmen Sie die Lösung des Systems aus 4a mit Anfangsbedingung "
              r"$x(0)=\begin{pmatrix}1\\0\end{pmatrix}$."),
    reference_answer=(r"Eigenwerte $\lambda_1=1,\lambda_2=3$ mit EV $v_1=(2,-1)^T,\ v_2=(0,1)^T$. "
                      r"Anfangsbedingung ⇒ $C_1=C_2=\tfrac12$: "
                      r"$x(t)=\tfrac12 e^{t}\begin{pmatrix}2\\-1\end{pmatrix}+\tfrac12 e^{3t}\begin{pmatrix}0\\1\end{pmatrix}$, "
                      r"d.h. $x(t)=e^{t},\ y(t)=\tfrac12(e^{3t}-e^{t})$."),
    rubric=[{"points": 2.0, "criterion": "Eigenwerte 1,3 und Eigenvektoren (2,−1),(0,1)"},
            {"points": 1.0, "criterion": "Konstanten aus AB: C1=C2=1/2"},
            {"points": 1.0, "criterion": "x(t)=½e^t(2,−1)+½e^{3t}(0,1)"}])

add(**MATH, id="math_4c", part="4c", max_points=3, answer_modality="derivation",
    question=(r"Die Lösung aus 4b definiert im Phasenraum eine Kurve. Beschreiben Sie sie durch eine "
              r"Koordinatengleichung $y=y(x)$ und skizzieren Sie sie."),
    reference_answer=(r"Mit $x=e^{t}$ und $y=\tfrac12(e^{3t}-e^{t})$ folgt $y(x)=\tfrac12(x^{3}-x)$ "
                      r"(Nullstellen bei $-1,0,1$)."),
    rubric=[{"points": 2.0, "criterion": "Elimination von t ⇒ y = ½(x³ − x)"},
            {"points": 1.0, "criterion": "Nullstellen/Skizze qualitativ korrekt"}],
    notes="Die Skizze selbst wird nicht automatisch bewertet; die Koordinatengleichung ist der bewertete Kern.")

add(**MATH, id="math_5a", part="5a", max_points=3, answer_modality="derivation",
    question=(r"Für $f:\mathbb{R}^2\to\mathbb{R}$ liegt $P(1,2,3)$ auf dem Graphen. Die Richtungsableitung "
              r"an der Stelle $(1,2)$ in Richtung der positiven $x$-Achse ist $1$, die in Richtung "
              r"$(1,1)^{T}$ ist $-3\sqrt2$. Bestimmen Sie Richtung und Betrag des Gradienten von $f$ in "
              r"$(1,2)$ über die Definition der Richtungsableitung."),
    reference_answer=(r"$D_{e}f=\langle\nabla f,e\rangle$. Aus $x$-Richtung: $f_x=1$. Aus $(1,1)/\sqrt2$: "
                      r"$\tfrac1{\sqrt2}(f_x+f_y)=-3\sqrt2\Rightarrow f_y=-7$. Also "
                      r"$\nabla f(1,2)=(1,-7)^T$, $|\nabla f|=\sqrt{1+49}=\sqrt{50}=5\sqrt2$."),
    rubric=[{"points": 1.0, "criterion": "f_x = 1"},
            {"points": 1.0, "criterion": "f_y = −7"},
            {"points": 1.0, "criterion": "∇f=(1,−7), |∇f| = 5√2"}])

add(**MATH, id="math_5b", part="5b", max_points=2, answer_modality="short_answer",
    question=r"Bestimmen Sie einen Tangentialvektor an die Niveaulinie von $f$ im Punkt $(1,2)$.",
    reference_answer=(r"Ein Tangentialvektor steht senkrecht auf $\nabla f=(1,-7)$, z.B. $t=(7,1)^T$ "
                      r"(jedes Vielfache $\lambda(7,1)$)."),
    rubric=[{"points": 2.0, "criterion": "Vektor ⊥ ∇f, z.B. (7,1) (oder Vielfaches)"}])

add(**MATH, id="math_5c", part="5c", max_points=3, answer_modality="derivation",
    question=(r"Geben Sie zwei Tangentialvektoren an den Graphen $F$ im Punkt $P$ an und bestimmen Sie "
              r"damit eine Koordinatengleichung der Tangentialebene an $F$ in $P$."),
    reference_answer=(r"$t_1=(1,0,f_x)^T=(1,0,1)^T$, $t_2=(0,1,f_y)^T=(0,1,-7)^T$. "
                      r"Normale $n=t_1\times t_2=(-1,7,1)^T$. Ebene: $-x+7y+z+d=0$; mit $P(1,2,3)$: "
                      r"$d=-16$, also $E:\,-x+7y+z-16=0$."),
    rubric=[{"points": 1.0, "criterion": "zwei Tangentialvektoren (1,0,1), (0,1,−7)"},
            {"points": 1.0, "criterion": "Normale n = (−1,7,1)"},
            {"points": 1.0, "criterion": "E: −x+7y+z−16 = 0"}])

add(**MATH, id="math_6a", part="6a", max_points=4, answer_modality="derivation",
    question=(r"Dreieck $A(1,1),B(3,1),C(3,2)$ und Vektorfeld "
              r"$F(x,y)=\big(x\ln y,\ \tfrac{x^{2}}{2y}\big)^{T}$. Skizzieren Sie den Definitionsbereich. "
              r"Ist $F$ dort ein Potentialfeld? Wenn ja, geben Sie eine Potentialfunktion an, sonst eine Begründung."),
    reference_answer=(r"$D(F)=\{(x,y):y>0\}$ (einfach zusammenhängend). "
                      r"$\operatorname{rot}F=\partial_x F_2-\partial_y F_1=\tfrac{2x}{2y}-\tfrac{x}{y}=0$. "
                      r"Da rot $F=0$ und $D$ einfach zusammenhängend ⇒ Potentialfeld. "
                      r"Potentialfunktion $V(x,y)=\tfrac{x^{2}}{2}\ln y + \text{const}$."),
    rubric=[{"points": 1.0, "criterion": "D(F) = {y>0}, einfach zusammenhängend"},
            {"points": 1.5, "criterion": "rot F = 0 ⇒ Potentialfeld"},
            {"points": 1.5, "criterion": "V(x,y) = (x²/2)·ln y (+ C)"}])

add(**MATH, id="math_6b", part="6b", max_points=3, answer_modality="derivation",
    question=(r"Berechnen Sie die Arbeit des Vektorfeldes $F$ entlang des geradlinigen Weges von "
              r"$A$ über $B$ nach $C$."),
    reference_answer=(r"Im Potentialfeld ist die Arbeit wegunabhängig: "
                      r"$A=V(C)-V(A)=V(3,2)-V(1,1)=\tfrac{9}{2}\ln2-\tfrac12\ln1=\tfrac{9}{2}\ln2$."),
    rubric=[{"points": 1.5, "criterion": "Wegunabhängigkeit: A = V(C) − V(A)"},
            {"points": 1.5, "criterion": "A = (9/2)·ln 2"}])

# --------------------------------------------------------------------------
# EXAM 3 — Mathematik I&II: Teil Systemanalyse, Herbst 2005 (pifr77kc); total 25
# --------------------------------------------------------------------------
SA = dict(course="Mathematik I/II (Systemanalyse)", course_slug="mathematikiii_0",
          exam_name="Systemanalyse, Herbst 2005", exam_id="pifr77kc.pdf",
          term="H2005", language="de",
          source_exam_pdf="data/mathematikiii_0/exams/pifr77kc.pdf/exam.pdf",
          source_solution_pdf="data/mathematikiii_0/exams/pifr77kc.pdf/solution.pdf")

add(**SA, id="sa_1a", part="1a", max_points=3, answer_modality="short_answer",
    question=(r"Charakterisieren Sie die folgenden Gleichungen als linear/nichtlinear und "
              r"autonom/nichtautonom ($V(t)$ Systemvariable, $t$ Zeit, $a,b$ Konstanten): "
              r"(1) $\dot V=a t^{2}+bV$;  (2) $\dot V=-a V^{2}+b$;  (3) $\dot V=-a\sqrt{V}+b t^{2}$."),
    reference_answer=("(1) linear, nichtautonom; (2) nichtlinear, autonom; (3) nichtlinear, nichtautonom."),
    rubric=[{"points": 1.0, "criterion": "(1) linear, nichtautonom"},
            {"points": 1.0, "criterion": "(2) nichtlinear, autonom"},
            {"points": 1.0, "criterion": "(3) nichtlinear, nichtautonom"}])

add(**SA, id="sa_1b", part="1b", max_points=2, answer_modality="drawing", auto_gradable=False,
    question=(r"System $\dot C(t)=J(t)-k\,C(t)$ mit $C(t_0)=0$. Skizzieren Sie qualitativ den "
              r"zeitlichen Verlauf von $C(t)$, wenn $J(t)$ den gegebenen (rechteckigen) Verlauf hat."),
    reference_answer=("C(t) steigt während J>0 gesättigt-exponentiell an (gegen J/k) und klingt nach "
                      "Abschalten von J exponentiell mit Rate k ab (verzögerte, geglättete Antwort auf J)."),
    rubric=[{"points": 2.0, "criterion": "qualitativ: exponentielles Auffüllen gegen J/k, danach exp. Abklingen mit Rate k"}],
    notes="Reine Skizzieraufgabe — nur über Beschreibung bewertbar; standardmässig nicht automatisch gewertet.")

add(**SA, id="sa_2a", part="2a", max_points=1, answer_modality="short_answer",
    question=(r"Fabrik am Fluss: Eine Fabrik leitet 600 kg/a einer Substanz kontinuierlich in den "
              r"Zufluss eines vollständig durchmischten Sees im Stationärzustand. Im Ausfluss misst man "
              r"$0.2\ \mathrm{mg\,m^{-3}}$. Seevolumen $10^{9}\,\mathrm{m^3}$, Durchfluss "
              r"$10^{9}\,\mathrm{m^3\,a^{-1}}$. Wird die Substanz im See abgebaut? Begründen Sie."),
    reference_answer=(r"$C_{in}=J/Q=6\cdot10^{8}\,\mathrm{mg\,a^{-1}}/10^{9}\,\mathrm{m^3\,a^{-1}}"
                      r"=0.6\ \mathrm{mg\,m^{-3}}$. Da $C_{aus}=0.2<C_{in}=0.6$, wird die Substanz "
                      r"im See abgebaut."),
    rubric=[{"points": 1.0, "criterion": "C_in = 0.6 mg/m³ > C_aus = 0.2 ⇒ Abbau (mit Begründung)"}])

add(**SA, id="sa_2b", part="2b", max_points=2, answer_modality="derivation",
    question=(r"Zeichnen Sie ein Boxschema des Systems aus 2a und stellen Sie die Bilanzgleichung "
              r"für die Konzentration $C$ auf."),
    reference_answer=(r"Ein Reservoir (See) mit Zufluss $Q\,C_{in}$, Abfluss $Q\,C$ und interner Abbaurate "
                      r"$R(C)$. Bilanz: $\dfrac{dC}{dt}=\dfrac{J}{V}-k_w C-R(C)=k_w C_{in}-k_w C-R(C)$, "
                      r"mit $k_w=Q/V$."),
    rubric=[{"points": 1.0, "criterion": "Boxschema: Zufluss QC_in, Abfluss QC, Abbau R(C)"},
            {"points": 1.0, "criterion": "Bilanz dC/dt = k_w·C_in − k_w·C − R(C)"}],
    notes="Boxschema als Zeichnung; die Bilanzgleichung ist der automatisch bewertbare Kern.")

add(**SA, id="sa_2c", part="2c", max_points=2, answer_modality="numeric",
    question=(r"Bestimmen Sie die Abbaurate der Substanz im Wasser unter der Annahme, dass der "
              r"Abbauprozess linear verläuft ($R(C)=k_r C$)."),
    reference_answer=(r"Stationär: $0=k_w C_{in}-(k_w+k_r)C_\infty$ mit $C_\infty=C_{aus}=0.2$, "
                      r"$k_w=Q/V=1\,\mathrm{a^{-1}}$. $k_r=k_w(C_{in}/C_\infty-1)=1\,(0.6/0.2-1)=2\ \mathrm{a^{-1}}$."),
    rubric=[{"points": 1.0, "criterion": "Stationaritätsbedingung mit k_w = 1 a⁻¹"},
            {"points": 1.0, "criterion": "k_r = 2 a⁻¹"}])

add(**SA, id="sa_2d", part="2d", max_points=2, answer_modality="numeric",
    question=(r"Der Grenzwert wird neu auf $0.1\ \mathrm{mg\,m^{-3}}$ verschärft. Wie lange würde es "
              r"dauern, bis die Konzentration unter den Grenzwert fiele, wenn die Fabrik sofort "
              r"geschlossen würde?"),
    reference_answer=(r"Ohne Input: $C(t)=C(0)e^{-k_{tot}t}$, $C(0)=0.2$, $k_{tot}=k_w+k_r=3\,\mathrm{a^{-1}}$. "
                      r"$\tau=-\tfrac1{k_{tot}}\ln\frac{0.1}{0.2}=\tfrac{\ln2}{3}\approx0.23\ \mathrm{a}\approx\tfrac14$ Jahr."),
    rubric=[{"points": 1.0, "criterion": "C(t)=C(0)e^{-k_tot t} mit k_tot = 3 a⁻¹"},
            {"points": 1.0, "criterion": "τ ≈ 0.23 a (≈ ¼ Jahr)"}])

add(**SA, id="sa_2e", part="2e", max_points=2, answer_modality="numeric",
    question=(r"Die Fabrik darf weiterbetreiben, muss aber den Ausstoss mit Rate $0.1\ \mathrm{a^{-1}}$ "
              r"verringern. Welche Menge schüttet die Fabrik 10 Jahre nach Beginn der Umstellung noch "
              r"in den See?"),
    reference_answer=(r"$J(t)=J_0 e^{-\beta t}$ mit $J_0=600\,\mathrm{kg\,a^{-1}}$, $\beta=0.1\,\mathrm{a^{-1}}$. "
                      r"$J(10)=600\,e^{-1}$; mit der Wertetabelle der Aufgabe ($e^{-1}\simeq 1/3$) ≈ 200 kg/a "
                      r"(exakt $600/e\approx221$ kg/a)."),
    rubric=[{"points": 1.0, "criterion": "J(t) = J_0·e^{-βt}"},
            {"points": 1.0, "criterion": "J(10 a) ≈ 200 kg/a (exakt 221 kg/a ebenfalls korrekt)"}],
    notes="Die Musterlösung rechnet mit e^-1 ≈ 1/3 (Tabelle der Aufgabe); 200 und 221 kg/a sind beide korrekt.")

add(**SA, id="sa_2f", part="2f", max_points=2, answer_modality="numeric",
    question=r"Welche Konzentration der Substanz liegt zu diesem Zeitpunkt (nach 10 Jahren) im See noch vor?",
    reference_answer=(r"Da $\beta=0.1\ll k_{tot}=3\,\mathrm{a^{-1}}$ gilt quasistationär "
                      r"$C(t)\approx j(t)/k_{tot}$ mit $j=J/V$. $j(10)=200\cdot10^{6}/10^{9}=0.2\ "
                      r"\mathrm{mg\,m^{-3}a^{-1}}$, also $C(10)\approx0.2/3\approx0.067\ \mathrm{mg\,m^{-3}}$ "
                      r"(mit exaktem $J(10)=221$ kg/a: ≈0.074)."),
    rubric=[{"points": 1.0, "criterion": "quasistationäre Näherung C ≈ j/k_tot (β ≪ k_tot)"},
            {"points": 1.0, "criterion": "C(10 a) ≈ 0.067 mg/m³ (0.074 mit exaktem J ebenfalls korrekt)"}],
    notes="Folgefehler der e^-1≈1/3-Näherung: 0.067 und 0.074 mg/m³ sind beide korrekt.")

add(**SA, id="sa_3a", part="3a", max_points=3, answer_modality="derivation",
    question=(r"Geschichteter See: Schadstoff gelangt ins Epilimnion. Boxschema mit Zu/Abfluss $Q$ und "
              r"Austausch $Q_{ex}$ zwischen Epilimnion ($V_E$) und Hypolimnion ($V_H$); Abbaurate $k_r$. "
              r"Stellen Sie die Bilanzgleichungen für $C_E$ und $C_H$ auf. Werte: $k_r=0.08\,\mathrm{d^{-1}}$, "
              r"$V_E=10^{9}$, $V_H=10^{10}\,\mathrm{m^3}$, $Q=3\cdot10^{7}$, $Q_{ex}=2\cdot10^{8}\,\mathrm{m^3 d^{-1}}$."),
    reference_answer=(r"$\dfrac{dC_E}{dt}=-(k_{ex,E}+k_w+k_r)C_E+k_{ex,E}C_H$, "
                      r"$\dfrac{dC_H}{dt}=k_{ex,H}C_E-(k_{ex,H}+k_r)C_H$, mit "
                      r"$k_w=Q/V_E=0.03$, $k_{ex,E}=Q_{ex}/V_E=0.2$, $k_{ex,H}=Q_{ex}/V_H=0.02\ \mathrm{d^{-1}}$."),
    rubric=[{"points": 1.0, "criterion": "dC_E/dt mit Austausch, Abfluss und Abbau"},
            {"points": 1.0, "criterion": "dC_H/dt mit Austausch und Abbau"},
            {"points": 1.0, "criterion": "Ratenkonstanten k_w=0.03, k_ex,E=0.2, k_ex,H=0.02 d⁻¹"}])

add(**SA, id="sa_3b", part="3b", max_points=2, answer_modality="short_answer",
    question=r"Welche stationären Konzentrationen stellen sich im Epilimnion und Hypolimnion nach langer Zeit ein?",
    reference_answer=(r"Da kein Input mehr und Abbau vorhanden: $C_E^\infty=0$ und $C_H^\infty=0$."),
    rubric=[{"points": 2.0, "criterion": "C_E∞ = 0 und C_H∞ = 0 (mit Begründung dC/dt=0)"}])

add(**SA, id="sa_3c", part="3c", max_points=2, answer_modality="numeric",
    question=r"Stellen Sie die Koeffizienten-Matrix des Gleichungssystems auf und bestimmen Sie ihre Werte.",
    reference_answer=(r"$\begin{pmatrix}-(k_{ex,E}+k_w+k_r)&k_{ex,E}\\ k_{ex,H}&-(k_{ex,H}+k_r)\end{pmatrix}"
                      r"=\begin{pmatrix}-0.31&0.2\\0.02&-0.1\end{pmatrix}\ \mathrm{d^{-1}}$."),
    rubric=[{"points": 1.0, "criterion": "Matrixstruktur korrekt"},
            {"points": 1.0, "criterion": "Werte [[-0.31, 0.2],[0.02, -0.1]] d⁻¹"}])

add(**SA, id="sa_3d", part="3d", max_points=2, answer_modality="numeric",
    question=(r"Wie lange dauert es, bis $C_E$ auf 5 % des ursprünglichen Wertes gesunken ist? "
              r"Begründen Sie (Tipp: benützen Sie die Koeffizienten-Matrix; ein kleiner Koeffizient "
              r"darf Null gesetzt werden)."),
    reference_answer=(r"Näherung (oberes Dreieck): Eigenwerte $\lambda_1=-0.31$, $\lambda_2=-0.1\,\mathrm{d^{-1}}$. "
                      r"Der betragskleinste EW bestimmt das Langzeitverhalten: "
                      r"$\tau_{5\%}\approx 3/|\lambda_2|=3/0.1=30\ \mathrm{d}$ "
                      r"(ohne den Tipp-Näherungsschritt: kleinster Eigenwert −0.082 d⁻¹ ⇒ ≈ 36 d)."),
    rubric=[{"points": 1.0, "criterion": "Eigenwerte ≈ −0.31 und −0.1 d⁻¹ (betragskleinster massgebend)"},
            {"points": 1.0, "criterion": "τ_5% ≈ 3/|λ| ≈ 30 d (≈36 d mit exaktem Eigenwert ebenfalls korrekt)"}],
    notes="Die Aufgabe erlaubt ausdrücklich, den kleinen Koeffizienten 0.02 auf 0 zu setzen (⇒ 30 d); exakt ≈ 36 d.")

# --------------------------------------------------------------------------
# EXAM 4 — Metamorphose und Magmatismus II (Magmatismus & Vulkane), FS2005 (s475u9b8); total 30
# --------------------------------------------------------------------------
META = dict(course="Metamorphose und Magmatismus II", course_slug="metamorphoseundmagmatismusii",
            exam_name="Magmatismus und Vulkanismus, Prüfung 23.06.2005", exam_id="s475u9b8.pdf",
            term="FS2005", language="de",
            source_exam_pdf="data/metamorphoseundmagmatismusii/exams/s475u9b8.pdf/exam.pdf",
            source_solution_pdf="data/metamorphoseundmagmatismusii/exams/s475u9b8.pdf/solution.pdf")
P11 = {"file": "figures/metamorph_figP1_1.png",
       "caption": "Figur P1.1: Binäres Forsterit–SiO₂ Phasendiagramm (En = Enstatit), mit Punkten R (1150 °C) und E (1000 °C)."}
P21 = {"file": "figures/metamorph_figP2_1.png",
       "caption": "Figur P2.1: Ternäres Cpx–Olivin–Quarz Phasendiagramm mit Druck-Kotektika (1–8 kbar)."}

add(**META, id="meta_1a", part="1a", max_points=2, answer_modality="conceptual", figures=[P11],
    question=(r"Gleichgewichtskristallisation im binären, peritektischen System Forsterit–Enstatit–SiO₂ "
              r"(Figur P1.1). Welche Phase ist inkongruent, und was bedeutet inkongruent?"),
    reference_answer=("Enstatit ist inkongruent. Inkongruentes Schmelzen/Verhalten bedeutet, dass die "
                      "Phase nicht direkt zu einer Schmelze der eigenen Zusammensetzung schmilzt, sondern "
                      "in einer (peritektischen) Reaktion in eine andere kristalline Phase plus eine "
                      "Schmelze zerfällt, deren Zusammensetzung nicht der der inkongruenten Phase entspricht."),
    rubric=[{"points": 1.0, "criterion": "Enstatit als inkongruente Phase benannt"},
            {"points": 1.0, "criterion": "Definition: zerfällt in andere Kristallphase + Schmelze anderer Zusammensetzung"}])

add(**META, id="meta_1b", part="1b", max_points=2, answer_modality="short_answer", figures=[P11],
    question=(r"Wie lauten die peritektische Reaktion am Punkt R (1150 °C) und die eutektische "
              r"Reaktion am Punkt E (1000 °C)?"),
    reference_answer=("Peritektisch (R): 100 Enstatit = 40 Schmelze + 60 Forsterit (beim Abkühlen "
                      "reagiert Schmelze + Forsterit → Enstatit). "
                      "Eutektisch (E): 62.5 SiO₂ + 37.5 Enstatit = 100 Schmelze (die Schmelze "
                      "kristallisiert zu Enstatit + SiO₂)."),
    rubric=[{"points": 1.0, "criterion": "R: Enstatit ⇌ Forsterit + Schmelze (≈60 Fo + 40 L)"},
            {"points": 1.0, "criterion": "E: Schmelze ⇌ Enstatit + SiO₂ (≈37.5 En + 62.5 SiO₂)"}])

add(**META, id="meta_1c", part="1c", max_points=12, answer_modality="numeric", figures=[P11],
    question=(r"Beschreiben Sie die Gleichgewichtskristallisation der Zusammensetzung X "
              r"(60 % Forsterit / 40 % SiO₂) für die Temperaturen T_L (1350 °C), T_1 (1275 °C), "
              r"T_R (1150 °C, bei Erreichen und bei Verlassen), T_2 (1060 °C), T_E (1000 °C, bei "
              r"Erreichen und bei Verlassen). Geben Sie jeweils die prozentualen Anteile der Phasen "
              r"(Schmelze/Kristalle) und die Schmelzzusammensetzung (in % Forsterit und SiO₂) an "
              r"(Hebelgesetz an Figur P1.1)."),
    reference_answer=(
        "Offizielle Hilfstabelle (Schmelze% / Forsterit% / Enstatit% / SiO₂% | Schmelze-Zus. Fo%/SiO₂%):\n"
        "T_L 1350: 100 / 0 / 0 / 0 | 60/40\n"
        "T_1 1275: 88.9 / 11.1 / 0 / 0 | 55/45\n"
        "T_R(in) 1150: 80 / 20 / 0 / 0 | 50/50\n"
        "T_R(out) 1150: 66.7 / 0 / 33.3 / 0 | 50/50\n"
        "T_2 1060: 44.4 / 0 / 55.6 / 0 | 35/65   (Musterlösung druckt 56.6 — Druckfehler, Summe sonst 101)\n"
        "T_E(in) 1000: 40 / 0 / 60 / 0 | 30/70\n"
        "T_E(out) 1000: 0 / 0 / 75 / 25 | 30/70\n"
        "(Bei T_L liegt alles als Schmelze der Zusammensetzung X vor; am Liquidus bis R fällt "
        "Forsterit aus, die Schmelze wandert Richtung SiO₂; an R reagiert Forsterit mit Schmelze "
        "zu Enstatit; zwischen R und E fällt Enstatit, bei E kristallisiert der Rest zu Enstatit+SiO₂.)"),
    rubric=[{"points": 2.0, "criterion": "T_L: 100 % Schmelze, Zusammensetzung 60/40"},
            {"points": 1.5, "criterion": "T_1: ≈88.9 % Schmelze + ≈11.1 % Forsterit, Schmelze ≈55/45"},
            {"points": 1.5, "criterion": "T_R(in): 80 % Schmelze + 20 % Forsterit, Schmelze 50/50"},
            {"points": 2.0, "criterion": "T_R(out): ≈66.7 % Schmelze + ≈33.3 % Enstatit (peritekt. Reaktion), 50/50"},
            {"points": 1.5, "criterion": "T_2: ≈44.4 % Schmelze + ≈55.6 % Enstatit (Musterlösung: 56.6, Druckfehler), Schmelze ≈35/65"},
            {"points": 1.5, "criterion": "T_E(in): 40 % Schmelze + 60 % Enstatit, Schmelze 30/70"},
            {"points": 2.0, "criterion": "T_E(out): 0 % Schmelze, 75 % Enstatit + 25 % SiO₂"}],
    notes="Toleranz ±ca. 3 Prozentpunkte (Ablesung aus dem Diagramm/Hebelgesetz).")

add(**META, id="meta_2a", part="2a", max_points=4, answer_modality="conceptual",
    question=(r"Mittelozeanische Rücken: Nennen Sie die wichtigsten Unterschiede zwischen schnellen "
              r"(fast) und langsamen (slow) mittelozeanischen Rücken bezüglich Spreading-Rate, "
              r"Magmenentstehung/Differentiation sowie Struktur und Aufbau der ozeanischen Kruste."),
    reference_answer=(
        "Fast spreading: hohe Spreading-/Magmenproduktionsrate, grosse Schmelzmenge, flache, gut "
        "entwickelte (eng fokussierte) Magmenkammer/Schmelzlinse, kein zentrales Rift-Tal (axiale "
        "Erhebung), gut ausgebildeter sheeted-dike-Komplex, Fe-reiche/Na-arme Schmelzen, "
        "troktolitische Kumulate, Cpx-reich (wenig Tiefen-Cpx-Fraktionierung). "
        "Slow spreading: niedrigere, variable Magmenproduktion (magmatische/amagmatische Zyklen), "
        "schwach entwickelte Schmelzzone, ausgeprägtes axiales Rift-Valley, segmentierte Rücken mit "
        "vielen Brüchen, Na-reiche/Fe-arme Schmelzen, wehrlitische/gabbroide Kumulate."),
    rubric=[{"points": 1.0, "criterion": "Spreading-/Magmenproduktionsrate: fast hoch, slow niedrig/variabel"},
            {"points": 1.0, "criterion": "Magmenkammer/Schmelzzone: fast flach & fokussiert, slow schwach entwickelt"},
            {"points": 1.0, "criterion": "Struktur: fast axiale Erhebung + sheeted dikes, slow Rift-Valley + segmentiert/Brüche"},
            {"points": 1.0, "criterion": "Chemie/Kumulate: fast Fe-reich/troktolitisch, slow Na-reich/gabbroid-wehrlitisch"}])

add(**META, id="meta_2b", part="2b", max_points=4, answer_modality="conceptual", figures=[P21],
    question=(r"Analysieren Sie die Aussage: „Basaltische Laven an langsam spreizenden MOR enthalten "
              r"einen niedrigeren normativen Klinopyroxen-(Cpx-)Anteil als an schnell spreizenden MOR.“ "
              r"Kann man daraus etwas über die Differentiationsbedingungen ableiten? Stützen Sie sich "
              r"auf das ternäre Cpx–Ol–Qz Diagramm (Figur P2.1)."),
    reference_answer=(
        "Cpx-arme Laven plotten weiter von der Cpx-Ecke entfernt. Mit steigendem Druck erscheint Cpx "
        "bereits bei Cpx-ärmeren Zusammensetzungen auf dem Liquidus; das Ol–Cpx-(+Plag-)Kotektikum "
        "verschiebt sich, Magmen differenzieren Richtung Quarz. Magmen, die bei hohem Druck (tiefe "
        "Magmenkammern, typisch slow spreading) differenzieren, sind daher Cpx-ärmer; Magmen, die erst "
        "in flachen Krustenniveaus (typisch fast spreading) differenzieren, müssen mehr Ol+Plag "
        "ausscheiden, bevor Cpx-Sättigung erreicht wird, und sind Cpx-reicher. Der normative Cpx-Gehalt "
        "ist somit ein Indikator für die Tiefe der Magmenkammer/Differentiation."),
    rubric=[{"points": 1.0, "criterion": "Cpx-arm = weiter weg von Cpx-Ecke; Druckabhängigkeit des Cpx-Erscheinens"},
            {"points": 1.5, "criterion": "hoher Druck ⇒ Cpx-ärmer (tiefe Kammer, slow); flacher ⇒ Cpx-reicher (fast)"},
            {"points": 1.5, "criterion": "Schlussfolgerung: normativer Cpx-Gehalt ⇒ Tiefe der Differentiation/Magmenkammer"}])

add(**META, id="meta_3", part="3", max_points=6, answer_modality="conceptual",
    question=(r"Partielle Aufschmelzung im oberen Erdmantel: Wie kann der Schmelzanteil $F$, den ein "
              r"primäres basaltisches Magma repräsentiert, geochemisch bestimmt werden? Skizzieren Sie "
              r"schematisch, wie sich die Zusammensetzung einer Partialschmelze mit dem Aufschmelzgrad "
              r"ändert (inkompatible Spurenelemente, $D\ll1$, normierte Spidergramme). "
              r"Batch-melting: $C_L/C_0=[\,D+F(1-D)\,]^{-1}$. Es ist nur das Prinzip gefragt."),
    reference_answer=(
        "Inkompatible Spurenelemente reichern sich in der Schmelze invers zum Aufschmelzgrad an. Aus der "
        "Batch-Melting-Gleichung C_L/C_0 = 1/[D + F(1−D)] folgt für sehr inkompatible Elemente (D→0) die "
        "Näherung C_L/C_0 ≈ 1/F, also F ≈ C_0/C_L. Da die Quellenzusammensetzung C_0 (z. B. MORB-Pyrolit), "
        "die Zusammensetzung des primären Basalts C_L und die Verteilungskoeffizienten bekannt sind, lässt "
        "sich F direkt bestimmen. Im normierten Spidergramm (Konzentration/Quelle) liegen kleinere F höher "
        "(stärkere Anreicherung der inkompatiblen Elemente); mit zunehmendem F nähern sich die Kurven dem "
        "Quellenniveau (Verhältnis → 1) an. Schematische Kurvenschar für F = 0.01 … 0.20."),
    rubric=[{"points": 2.0, "criterion": "inkompatible Elemente ∝ 1/F; aus Batch-Melting für D→0: C_L/C_0 ≈ 1/F"},
            {"points": 2.0, "criterion": "F ≈ C_0/C_L bestimmbar, da C_0, C_L, D bekannt"},
            {"points": 2.0, "criterion": "Spidergramm: kleines F → stark angereichert/hoch, grosses F → Richtung Quellenniveau"}])

# --------------------------------------------------------------------------
# EXAM 5 — Kartenpraktikum I, Prüfung 18.12.2014 (k9mytfrn); 30 Pkt (2 für Sauberkeit)
# Map-based; the geological map (figure) is required. Grey carry-forward values on the
# exam sheet are NOT the official answers and are not used here.
# --------------------------------------------------------------------------
K14 = dict(course="Kartenpraktikum I", course_slug="kartenpraktikumi",
           exam_name="Kartenpraktikum I, Prüfung 18.12.2014", exam_id="k9mytfrn.pdf",
           term="2014", language="de",
           source_exam_pdf="data/kartenpraktikumi/exams/k9mytfrn.pdf/exam.pdf",
           source_solution_pdf="data/kartenpraktikumi/exams/k9mytfrn.pdf/solution.pdf")
MAP14 = {"file": "figures/karten2014_map.png",
         "caption": "Prüfungskarte 2014: Sedimentgesteine A–D und F–H, Verwerfung (fette Linie), Profilschnitt X–Y."}
K14_INTRO = ("Geologische Kartenanalyse. Die Karte (Figur) zeigt Sedimentgesteine A–D und F–H sowie "
             "eine Verwerfung (fette schwarze Linie) und die Profillinie X–Y. Orientierungen als "
             "Fallazimuth/Einfallswinkel. ")

add(**K14, id="k14_1", part="1", max_points=1.5, answer_modality="numeric", figures=[MAP14],
    question=K14_INTRO + ("Auf der Karte gibt es eine Winkeldiskordanz. An der Basis welcher Schicht "
                          "befindet sie sich, und wie ist ihre Orientierung (Fallazimuth/Einfallswinkel)?"),
    reference_answer="Winkeldiskordanz an der Basis von Schicht F; Orientierung ≈ 089/05.",
    rubric=[{"points": 0.75, "criterion": "Diskordanz an der Basis von Schicht F"},
            {"points": 0.75, "criterion": "Orientierung ≈ 089/05 (±~5°/±~3°)"}],
    notes="Das Einzeichnen der Diskordanz in die Karte wird nicht automatisch bewertet.")

add(**K14, id="k14_2", part="2", max_points=1.5, answer_modality="numeric", figures=[MAP14],
    question=K14_INTRO + ("Die Schichten A–D sind verfaltet. Bestimmen Sie die Orientierung "
                          "(Fallazimuth/Einfallswinkel) beider Faltenschenkel."),
    reference_answer="Faltenschenkel ≈ 085/22 und ≈ 265/22.",
    rubric=[{"points": 0.75, "criterion": "ein Schenkel ≈ 085/22"},
            {"points": 0.75, "criterion": "anderer Schenkel ≈ 265/22"}])

add(**K14, id="k14_3", part="3", max_points=1.5, answer_modality="numeric", figures=[MAP14],
    question=K14_INTRO + "Bestimmen Sie die wahre Mächtigkeit der Schicht C auf beiden Faltenschenkeln.",
    reference_answer="Wahre Mächtigkeit der Schicht C ≈ 186 m (auf beiden Schenkeln gleich).",
    rubric=[{"points": 1.5, "criterion": "Mächtigkeit ≈ 186 m (±~15 m), auf beiden Schenkeln gleich"}])

add(**K14, id="k14_4", part="4", max_points=1, answer_modality="short_answer", figures=[MAP14],
    question=K14_INTRO + ("Um was für Falten handelt es sich (Antiformen, Synformen, Antiklinalen, "
                          "Synklinalen)? Begründen Sie."),
    reference_answer=("Von W nach E: Synform – Antiform – Synform. Die Begriffe Antiklinale/Synklinale "
                      "können nicht verwendet werden, da das relative Alter der Schichten unbekannt ist."),
    rubric=[{"points": 0.5, "criterion": "Abfolge Synform–Antiform–Synform (W→E)"},
            {"points": 0.5, "criterion": "Begründung: Anti-/Synklinale nicht möglich, da relatives Alter unbekannt"}])

add(**K14, id="k14_5", part="5", max_points=1, answer_modality="numeric", figures=[MAP14],
    question=K14_INTRO + "Bestimmen Sie die Orientierung (Fallazimuth/Einfallswinkel) der Verwerfung (fette schwarze Linie).",
    reference_answer="Verwerfung ≈ 282/67.",
    rubric=[{"points": 1.0, "criterion": "Orientierung der Verwerfung ≈ 282/67 (±~8°)"}])

add(**K14, id="k14_6", part="6", max_points=6, answer_modality="drawing", auto_gradable=False, figures=[MAP14],
    question=K14_INTRO + ("Zeichnen Sie das Profil X–Y und tragen Sie die Spur(en) der "
                          "Faltenachsenebene(n) ein."),
    reference_answer=("Profilschnitt entlang X–Y mit den verfalteten Schichten A–D, der Diskordanz und "
                      "den diskordant auflagernden Schichten F–H; die Faltenachsenebenen sind vertikal."),
    rubric=[{"points": 6.0, "criterion": "korrektes Profil (Faltengeometrie A–D, Diskordanz, F–H) mit vertikaler Axialebenenspur"}],
    notes="Konstruktionsaufgabe (Profil zeichnen) — standardmässig nicht automatisch bewertet; bewertbarer Kern: Axialebene vertikal.")

add(**K14, id="k14_7", part="7", max_points=1, answer_modality="short_answer", figures=[MAP14],
    question=K14_INTRO + "Entspricht die Winkelhalbierende-Ebene der Falte auch der Faltenachsenebene? Begründen Sie.",
    reference_answer=("Ja. Da die Mächtigkeit auf beiden Faltenschenkeln gleich ist, handelt es sich um "
                      "eine symmetrische Falte; bei symmetrischen Falten fällt die Winkelhalbierende mit "
                      "der Axialebene zusammen."),
    rubric=[{"points": 0.5, "criterion": "Ja"},
            {"points": 0.5, "criterion": "Begründung: symmetrische Falte (gleiche Schenkelmächtigkeit) ⇒ Winkelhalbierende = Axialebene"}])

add(**K14, id="k14_8", part="8", max_points=3, answer_modality="short_answer", figures=[MAP14],
    question=K14_INTRO + "Beschreiben Sie stichwortartig die geologische Geschichte des Gebiets.",
    reference_answer=("1) Ablagerung A–D; 2) Verfaltung; 3) Erosion; 4) Ablagerung F–H (diskordant); "
                      "5) Verkippung; 6) Erosion (heutige Oberfläche). Die Verwerfung kann zu einem "
                      "beliebigen späteren Zeitpunkt auftreten."),
    rubric=[{"points": 1.0, "criterion": "Ablagerung A–D, dann Verfaltung"},
            {"points": 1.0, "criterion": "Erosion, dann diskordante Ablagerung F–H"},
            {"points": 1.0, "criterion": "Verkippung + erneute Erosion; Verwerfung zeitlich frei"}])

add(**K14, id="k14_9", part="9", max_points=2, answer_modality="numeric", figures=[MAP14],
    question=K14_INTRO + ("Tragen Sie die beiden Faltenschenkel in das Schmidt'sche Netz ein. Bestimmen "
                          "Sie die Orientierung der Faltenachse und den Öffnungswinkel der Falte."),
    reference_answer=("Faltenachse ≈ 175/00 (= 355/00, dasselbe Lineament; horizontal); "
                      "Öffnungswinkel ≈ 136°."),
    rubric=[{"points": 1.0, "criterion": "Faltenachse ≈ 175/00 (horizontal, ~N–S/NNW streichend)"},
            {"points": 1.0, "criterion": "Öffnungswinkel ≈ 136° (±~10°)"}])

add(**K14, id="k14_10", part="10", max_points=2, answer_modality="numeric", figures=[MAP14],
    question=K14_INTRO + ("Bestimmen Sie auf der Karte den Trend (Azimuth) der Bewegungsrichtung der "
                          "Verwerfung (im Uhrzeigersinn ab Norden). Welche Bewegungskombination "
                          "(Auf-/Abschiebung, sinistrale/dextrale Blattverschiebung) hat stattgefunden?"),
    reference_answer=("Trend der Bewegungsrichtung ≈ 175°/355°. Bewegung: Abschiebung + dextrale "
                      "Blattverschiebung."),
    rubric=[{"points": 1.0, "criterion": "Trend ≈ 175°/355°"},
            {"points": 1.0, "criterion": "Abschiebung + dextrale Blattverschiebung"}])

add(**K14, id="k14_11", part="11", max_points=1, answer_modality="numeric", figures=[MAP14],
    question=K14_INTRO + ("Tragen Sie Verwerfungsfläche und Trend der Bewegungsrichtung in das "
                          "Schmidt'sche Netz ein und bestimmen Sie den Pitch der Bewegungsrichtung."),
    reference_answer="Pitch der Bewegungsrichtung ≈ 38° (von Norden gemessen).",
    rubric=[{"points": 1.0, "criterion": "Pitch ≈ 38° (±~8°)"}])

add(**K14, id="k14_12", part="12", max_points=2.5, answer_modality="numeric", figures=[MAP14],
    question=K14_INTRO + ("Bestimmen Sie im Schmidt'schen Netz die Orientierungen der drei "
                          "Hauptspannungen σ1, σ2, σ3."),
    reference_answer="σ1 ≈ 032/43, σ2 ≈ 219/46, σ3 ≈ 125/03.",
    rubric=[{"points": 1.0, "criterion": "σ1 ≈ 032/43"},
            {"points": 0.75, "criterion": "σ2 ≈ 219/46"},
            {"points": 0.75, "criterion": "σ3 ≈ 125/03"}],
    notes="Toleranz ±~10°. Alternative Lösungen abhängig davon, ob Prüfungswerte verwendet wurden (siehe Musterlösung).")

add(**K14, id="k14_13", part="13", max_points=2, answer_modality="numeric", figures=[MAP14],
    question=K14_INTRO + ("Bestimmen Sie die Versatzkomponenten der Verwerfung: "
                          "Blattverschiebungskomponente, Sprunghöhe und Dehnungsbetrag."),
    reference_answer=("Blattverschiebungskomponente ≈ 284 m; Sprunghöhe ≈ 200 m; "
                      "Dehnungsbetrag ≈ 84 m."),
    rubric=[{"points": 0.75, "criterion": "Blattverschiebungskomponente ≈ 284 m (±~15 m)"},
            {"points": 0.75, "criterion": "Sprunghöhe ≈ 200 m"},
            {"points": 0.5, "criterion": "Dehnungsbetrag ≈ 84 m (±~8 m)"}],
    notes=("Die Musterlösung nennt zusätzlich 93 m / 77 m; das sind Folgewerte bei Verwendung der "
           "(entfernten) Prüfungs-Hinweiswerte und gelten hier nicht."))

add(**K14, id="k14_14", part="14", max_points=2, answer_modality="drawing", auto_gradable=False, figures=[MAP14],
    question=K14_INTRO + "Zeichnen Sie auf der Karte die Gebiete ein, in denen ein vertikales Bohrloch die Schicht D antrifft.",
    reference_answer=("Gebiete, in denen Schicht D unter der heutigen Oberfläche liegt (abgeleitet aus "
                      "Streichlinien/Ausbisslinien der Basis und des Tops von D und der Topografie)."),
    rubric=[{"points": 2.0, "criterion": "korrekt konstruierte Gebiete aus Streichlinien von D vs. Topografie"}],
    notes="Konstruktions-/Zeichenaufgabe — standardmässig nicht automatisch bewertet.")

# --------------------------------------------------------------------------
# EXAM 6 — Kartenpraktikum I, Prüfung 19.12.2013 (ja9djbrh); 30 Pkt
# --------------------------------------------------------------------------
K13 = dict(course="Kartenpraktikum I", course_slug="kartenpraktikumi",
           exam_name="Kartenpraktikum I, Prüfung 19.12.2013", exam_id="ja9djbrh.pdf",
           term="2013", language="de",
           source_exam_pdf="data/kartenpraktikumi/exams/ja9djbrh.pdf/exam.pdf",
           source_solution_pdf="data/kartenpraktikumi/exams/ja9djbrh.pdf/solution.pdf")
MAP13 = {"file": "figures/karten2013_map.png",
         "caption": "Prüfungskarte 2013: zwei kohleführende Schichten ('Coal' Flötz, 'COAL MEASURES' mit Kreis-Basis), Permischer Kalk (Limestone), Verwerfung F, Profil X–Y."}
K13_INTRO = ("Geologische Kartenanalyse. Die Karte (Figur) zeigt zwei kohleführende Sedimentgesteine "
             "(das Kohleflötz 'Coal' und die mit Kreisen an der Basis markierten 'COAL MEASURES'), "
             "ein permisches Kalkgestein ('Limestone') und eine Verwerfung (F). "
             "Orientierungen als Fallazimuth/Einfallswinkel. ")

add(**K13, id="k13_1", part="1", max_points=1.5, answer_modality="numeric", figures=[MAP13],
    question=K13_INTRO + ("An der Basis welcher geologischen Einheit befindet sich eine Winkeldiskordanz, "
                          "und wie ist ihre Orientierung (Fallazimuth/Einfallswinkel)?"),
    reference_answer="Winkeldiskordanz an der Basis des Permian Limestone; Orientierung ≈ 340/09.",
    rubric=[{"points": 0.75, "criterion": "Diskordanz an der Basis des Permian Limestone"},
            {"points": 0.75, "criterion": "Orientierung ≈ 340/09 (±~5°/±~3°)"}])

add(**K13, id="k13_2", part="2", max_points=2.5, answer_modality="numeric", figures=[MAP13],
    question=K13_INTRO + ("Die kohleführenden Schichten sind verfaltet. Bestimmen Sie die Orientierung "
                          "beider Faltenschenkel. Um was für Falten handelt es sich (Antiformen, "
                          "Synformen, Antiklinalen, Synklinalen)? Begründen Sie."),
    reference_answer=("Faltenschenkel ≈ 090/14 und ≈ 270/27. Es handelt sich um 2× Antiform und 1× "
                      "Synform; dank der Kreis-Signatur an der Basis der COAL MEASURES ist oben/unten "
                      "bekannt, daher darf man auch von Antiklinale und Synklinale sprechen."),
    rubric=[{"points": 0.75, "criterion": "Schenkel ≈ 090/14"},
            {"points": 0.75, "criterion": "Schenkel ≈ 270/27"},
            {"points": 1.0, "criterion": "2× Antiform, 1× Synform; Anti-/Synklinale zulässig (Kreis-Signatur gibt Alter/Oben-Unten)"}])

add(**K13, id="k13_3", part="3", max_points=2, answer_modality="numeric", figures=[MAP13],
    question=K13_INTRO + ("Tragen Sie die beiden Faltenschenkel in das Schmidt'sche Netz ein. Bestimmen "
                          "Sie die Orientierung der Faltenachse und den Öffnungswinkel der Falte."),
    reference_answer="Faltenachse ≈ 000/00 (= 180/00, horizontal, N–S); Öffnungswinkel ≈ 139°.",
    rubric=[{"points": 1.0, "criterion": "Faltenachse ≈ 000/00 (horizontal, N–S)"},
            {"points": 1.0, "criterion": "Öffnungswinkel ≈ 139° (±~10°)"}])

add(**K13, id="k13_4", part="4", max_points=1.5, answer_modality="numeric", figures=[MAP13],
    question=K13_INTRO + "Bestimmen Sie die wahre Mächtigkeit der kohleführenden Schicht ('COAL MEASURES') auf beiden Faltenschenkeln.",
    reference_answer="Mächtigkeit der COAL MEASURES ≈ 135 m und ≈ 145 m.",
    rubric=[{"points": 0.75, "criterion": "ein Schenkel ≈ 135 m"},
            {"points": 0.75, "criterion": "anderer Schenkel ≈ 145 m"}])

add(**K13, id="k13_5", part="5", max_points=1, answer_modality="numeric", figures=[MAP13],
    question=K13_INTRO + "Bestimmen Sie die Orientierung (Fallazimuth/Einfallswinkel) der Verwerfung (F).",
    reference_answer="Verwerfung ≈ 066/56.",
    rubric=[{"points": 1.0, "criterion": "Orientierung der Verwerfung ≈ 066/56 (±~8°)"}])

add(**K13, id="k13_6", part="6", max_points=7, answer_modality="drawing", auto_gradable=False, figures=[MAP13],
    question=K13_INTRO + ("Zeichnen Sie das Profil X–Y und die Spur der Faltenachsenebene ins Profil. "
                          "Wie gross ist der Einfallswinkel der Faltenachsenebene?"),
    reference_answer=("Profil X–Y mit den verfalteten kohleführenden Schichten, Diskordanz und "
                      "auflagerndem Limestone; die Faltenachsenebene ist vertikal (Einfallswinkel ~90°)."),
    rubric=[{"points": 7.0, "criterion": "korrektes Profil mit Faltengeometrie und vertikaler Axialebene (~90°)"}],
    notes="Konstruktionsaufgabe — standardmässig nicht automatisch bewertet; bewertbarer Kern: Axialebene vertikal.")

add(**K13, id="k13_7", part="7", max_points=3, answer_modality="short_answer", figures=[MAP13],
    question=K13_INTRO + "Beschreiben Sie die geologische Geschichte des Gebiets stichwortartig.",
    reference_answer=("1) Horizontale Sedimentation der kohleführenden Sedimente; 2) Verfaltung; "
                      "3) Verwerfung; 4) Erosion zu einer ebenen Topografie; 5) horizontale Sedimentation "
                      "des Permian Limestone (diskordant); 6) tektonische Verkippung; 7) Erosion zur "
                      "heutigen Topografie."),
    rubric=[{"points": 1.0, "criterion": "Sedimentation Kohleschichten, Verfaltung, Verwerfung"},
            {"points": 1.0, "criterion": "Erosion, dann diskordante Sedimentation Permian Limestone"},
            {"points": 1.0, "criterion": "Verkippung + Erosion zur heutigen Topografie"}])

add(**K13, id="k13_8", part="8", max_points=2, answer_modality="numeric", figures=[MAP13],
    question=K13_INTRO + ("Bestimmen Sie den Trend (Azimuth) der Bewegungsrichtung der Verwerfung "
                          "(im Uhrzeigersinn ab Norden). Welche Bewegungskombination hat stattgefunden?"),
    reference_answer="Trend der Bewegungsrichtung ≈ 0° (N–S). Bewegung: Abschiebung + sinistrale Blattverschiebung.",
    rubric=[{"points": 1.0, "criterion": "Trend ≈ 0° (N)"},
            {"points": 1.0, "criterion": "Abschiebung + sinistrale Blattverschiebung"}])

add(**K13, id="k13_9", part="9", max_points=1.5, answer_modality="numeric", figures=[MAP13],
    question=K13_INTRO + ("Tragen Sie Verwerfungsfläche und Trend der Bewegungsrichtung ins Schmidt'sche "
                          "Netz ein und bestimmen Sie den Pitch der Bewegungsrichtung."),
    reference_answer="Pitch der Bewegungsrichtung ≈ 39° (Richtung NNW).",
    rubric=[{"points": 1.5, "criterion": "Pitch ≈ 39° (±~8°, Richtung NNW)"}])

add(**K13, id="k13_10", part="10", max_points=3, answer_modality="numeric", figures=[MAP13],
    question=K13_INTRO + "Bestimmen Sie im Schmidt'schen Netz die Orientierungen der drei Hauptspannungen σ1, σ2, σ3.",
    reference_answer="σ1 ≈ 327/47, σ2 ≈ 121/40, σ3 ≈ 222/13.",
    rubric=[{"points": 1.0, "criterion": "σ1 ≈ 327/47"},
            {"points": 1.0, "criterion": "σ2 ≈ 121/40"},
            {"points": 1.0, "criterion": "σ3 ≈ 222/13"}],
    notes="Toleranz ±~10°. Alternativen je nach Verwendung der Prüfungswerte (siehe Musterlösung).")

add(**K13, id="k13_11", part="11", max_points=1.5, answer_modality="numeric", figures=[MAP13],
    question=K13_INTRO + "Bestimmen Sie Blattverschiebungskomponente, Sprunghöhe und Dehnungsbetrag der Verwerfung.",
    reference_answer=("Blattverschiebungskomponente ≈ 210 m; Sprunghöhe ≈ 150 m; "
                      "Dehnungsbetrag ≈ 100 m."),
    rubric=[{"points": 0.5, "criterion": "Blattverschiebungskomponente ≈ 210 m (±~20 m)"},
            {"points": 0.5, "criterion": "Sprunghöhe ≈ 150 m (±~10 m)"},
            {"points": 0.5, "criterion": "Dehnungsbetrag ≈ 100 m (±~10 m)"}],
    notes=("Die Musterlösung nennt zusätzlich 120 m / 160 m / 107 m; das sind Folgewerte bei Verwendung der "
           "(entfernten) Prüfungs-Hinweiswerte und gelten hier nicht."))

add(**K13, id="k13_12", part="12", max_points=3.5, answer_modality="drawing", auto_gradable=False, figures=[MAP13],
    question=K13_INTRO + ("Konstruieren Sie auf der Karte die Schnittlinien zwischen dem Kohleflötz "
                          "('Coal') und der Diskordanz sowie zwischen dem Kohleflötz und der "
                          "Verwerfungsfläche, und zeichnen Sie die Gebiete ein, wo ein vertikales "
                          "Bohrloch das Kohleflötz antrifft."),
    reference_answer=("Schnittlinien des 'Coal'-Flötzes mit Diskordanz bzw. Verwerfung aus Streichlinien "
                      "konstruiert; daraus die Gebiete, in denen das Flötz unter der heutigen Oberfläche "
                      "(im Bohrloch) angetroffen wird."),
    rubric=[{"points": 3.5, "criterion": "korrekte Schnittlinien-Konstruktion und Bohrloch-Gebiete des 'Coal'-Flötzes"}],
    notes="Konstruktions-/Zeichenaufgabe — standardmässig nicht automatisch bewertet.")

# --------------------------------------------------------------------------
if __name__ == "__main__":
    out_path = OUT / "tasks.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for i, t in enumerate(TASKS, 1):
            t = {"schema_version": "1.0", **t}
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    # Summary
    n = len(TASKS)
    gradable = sum(1 for t in TASKS if t["auto_gradable"])
    pts = sum(t["max_points"] for t in TASKS)
    gpts = sum(t["max_points"] for t in TASKS if t["auto_gradable"])
    by_exam = {}
    for t in TASKS:
        by_exam.setdefault(t["exam_id"], [0, 0.0])
        by_exam[t["exam_id"]][0] += 1
        by_exam[t["exam_id"]][1] += t["max_points"]
    print(f"Wrote {n} items ({gradable} auto-gradable) → {out_path}")
    print(f"Total points: {pts}  (auto-gradable: {gpts})")
    for ex, (c, p) in by_exam.items():
        print(f"  {ex:16s} {c:2d} items, {p:5.1f} pts")
