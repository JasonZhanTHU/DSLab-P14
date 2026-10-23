#!/usr/bin/env python3
"""Author the DERIVED tier (tasks_derived.jsonl).

Tier semantics (never mixed with the official 6-exam set in ../tasks.jsonl):
  reference_source = "official_embedded_solution"   Groundwater Assessment I: the lecturer's handwritten
                                                    solutions are interleaved in the exam PDF; our own
                                                    recomputation is asserted to agree with them.
  reference_source = "derived_verified"             no official key exists; the answer is computed here
                                                    from the data given in the question (decay constants,
                                                    Darcy, lever rule, mass balance, ...). Values are
                                                    produced by code, not typed by hand.
Items whose answer depends on a reading assumption carry `confidence: "medium"` and a note.
Points marked `assigned` are benchmark-assigned (the sheet does not print them).
"""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import DATA

import numpy as np

HERE = DATA / "derived"
TASKS = []
ERR = []


def add(**kw):
    kw.setdefault("tier", "derived")
    kw.setdefault("points_source", "assigned")
    kw.setdefault("confidence", "high")
    kw.setdefault("auto_gradable", True)
    kw.setdefault("figures", [])
    kw.setdefault("notes", "")
    kw.setdefault("language", "de")
    if kw["rubric"] and isinstance(kw["rubric"][0], str):      # unweighted: 1 point per criterion, to be re-weighted later
        kw["rubric"] = [{"points": 1.0, "criterion": c} for c in kw["rubric"]]
        kw["max_points"] = float(len(kw["rubric"]))
        kw["points_source"] = "unassigned"
    s = round(sum(r["points"] for r in kw["rubric"]), 3)
    if abs(s - kw["max_points"]) > 1e-6:
        raise ValueError(f"{kw['id']}: rubric sums to {s} != {kw['max_points']}")
    TASKS.append(kw)


def agree(tag, ours, official, tol):
    ok = abs(ours - official) <= tol * abs(official)
    print(f"{'OK  ' if ok else 'DIFF'} {tag:34s} ours {ours:.5g}   official {official:.5g}")
    if not ok:
        ERR.append(tag)


def clip(exam, pages):
    return [{"file": f"clips/{exam}_p{p:02d}.png", "caption": f"{exam} page {p}"} for p in pages]


# =========================================================================
# GROUNDWATER Assessment I (Midterm), 26 Oct 2020 — official embedded solutions
# =========================================================================
GW1 = dict(course="Groundwater", course_slug="groundwater", exam_name="Assessment I (Midterm Exam), 26 Oct 2020",
           exam_id="o62zs9b4.pdf", term="2020", language="en", reference_source="official_embedded_solution",
           points_source="official", verification="official handwritten solution in the exam PDF; recomputed here",
           source_exam_pdf="data/groundwater/exams/o62zs9b4.pdf/exam.pdf")
USEFUL = "Useful values: g = 10 m/s², ρ = 1000 kg/m³, ν = 10⁻⁶ m²/s, β = 10⁻¹⁰ 1/Pa. "
P1 = ("Problem 1 (flow in a layered confined aquifer). Two horizontal layers: thicknesses m1 = 6 m, m2 = 4 m; "
      "hydraulic conductivities K1 = 1.0×10⁻³ m/s, K2 = 5.0×10⁻⁴ m/s. Piezometers A and B (diameter 0.1 m) are "
      "L = 100 m apart in the flow direction with heads hA = 400 m and hB = 401 m. Porosity 0.2, specific "
      "storativity Ss = 1.0×10⁻⁵ 1/m. " + USEFUL)

m1, m2, K1, K2, hA, hB, L, n, Ss, dpz = 6, 4, 1e-3, 5e-4, 400.0, 401.0, 100.0, 0.2, 1e-5, 0.1
T = K1 * m1 + K2 * m2
q = (T / (m1 + m2)) * (hB - hA) / L
u = q / n
Sst = Ss * (m1 + m2)
rw = dpz / 2
Q = np.pi * T * (hB - hA) / np.log((L - rw) / rw)
agree("gw1 1b T", T, 8e-3, 1e-9)
agree("gw1 1c q", q, 8e-6, 1e-9)
agree("gw1 1c u", u, 4e-5, 1e-9)
agree("gw1 1d S", Sst, 1e-4, 1e-9)
agree("gw1 1e Q [m3/s]", Q, 3.3e-3, 0.02)
agree("gw1 1e Q [L/min]", Q * 60e3, 198, 0.02)
fig1 = clip("o62zs9b4", [2])

add(**GW1, id="gw1_1a", part="1a", max_points=2, answer_modality="derivation", figures=fig1,
    question=P1 + "(a) Write down the groundwater flow equation without source/sink term for the one-dimensional "
                  "transient hydraulic head distribution in this aquifer.",
    reference_answer="Ss ∂h/∂t = K ∂²h/∂x², equivalently S ∂h/∂t = T ∂²h/∂x² = K(m1+m2) ∂²h/∂x² with S = Ss·m and T = K·m "
                     "(h: head at time t and position x; S: storativity; T: transmissivity).",
    rubric=[{"points": 1.0, "criterion": "transient storage term (S or Ss)·∂h/∂t on the left"},
            {"points": 1.0, "criterion": "second-derivative term T·∂²h/∂x² (or K·∂²h/∂x²), no source term"}])
add(**GW1, id="gw1_1b", part="1b", max_points=2, answer_modality="numeric", figures=fig1,
    question=P1 + "(b) Determine the transmissivity of this aquifer.",
    reference_answer=f"T = K1·m1 + K2·m2 = 1.0e-3·6 + 5.0e-4·4 = {T:.1e} m²/s.",
    rubric=[{"points": 1.0, "criterion": "T = Σ K_i·m_i (layers in parallel)"},
            {"points": 1.0, "criterion": "T = 8×10⁻³ m²/s"}])
add(**GW1, id="gw1_1c", part="1c", max_points=3, answer_modality="numeric", figures=fig1,
    question=P1 + "(c) Determine the groundwater flow direction and the mean water velocity along the straight line "
                  "between the two piezometers.",
    reference_answer=f"Flow is from high to low head: from B to A. Specific discharge q = (T/m)·Δh/L = "
                     f"(8e-3/10)·(1/100) = {q:.1e} m/s; mean (pore) velocity u = q/n = {u:.1e} m/s.",
    rubric=[{"points": 1.0, "criterion": "direction B → A (high to low head)"},
            {"points": 1.0, "criterion": "q = 8×10⁻⁶ m/s (Darcy, with K_eff = T/m)"},
            {"points": 1.0, "criterion": "u = q/n = 4×10⁻⁵ m/s"}])
add(**GW1, id="gw1_1d", part="1d", max_points=2, answer_modality="numeric", figures=fig1,
    question=P1 + "(d) Determine the storativity of this aquifer.",
    reference_answer=f"S = Ss·m = 1e-5 1/m · (6+4) m = {Sst:.0e} (dimensionless).",
    rubric=[{"points": 1.0, "criterion": "S = Ss·(m1+m2)"}, {"points": 1.0, "criterion": "S = 1×10⁻⁴ (dimensionless)"}])
add(**GW1, id="gw1_1e", part="1e", max_points=6, answer_modality="numeric", figures=fig1,
    question=P1 + "(e) The current head difference between A and B is maintained only by steady-state pumping from "
                  "piezometer A and recharging back into B. Determine the pumping/recharging rate using the steady-state "
                  "(dipole) solution.",
    reference_answer=("Dipole of a pumping and a recharge well (distance L, well radius r_w = 0.05 m): the head difference "
                      "is twice the absolute drawdown at one well: Δh = (Q/(πT))·ln((L−r_w)/r_w) ⇒ "
                      f"Q = π·T·Δh / ln((L−r_w)/r_w) = {Q:.2e} m³/s ≈ {Q*60e3:.0f} L/min."),
    rubric=[{"points": 2.0, "criterion": "dipole (pumping + injection) steady-state drawdown formula s = (Q/2πT)·ln((L−r_w)/r_w)"},
            {"points": 1.0, "criterion": "Δh = 2|s| ⇒ Q = πTΔh / ln((L−r_w)/r_w)"},
            {"points": 1.0, "criterion": "r_w = D/2 = 0.05 m used"},
            {"points": 2.0, "criterion": "Q ≈ 3.3×10⁻³ m³/s ≈ 198 L/min"}])

# ---- Problem 2: flow net beneath a dam
rho, g, hres, ndrops = 1000.0, 10.0, 11.0, 10
hA2 = hres - 10.0 / ndrops
pA = rho * g * (hA2 - (-15.0))
iBC = (6.0 - 5.0) / 10.0
QD = 1e-7 * iBC * 10.0 * 1.0
agree("gw1 2a hA", hA2, 10.0, 1e-9)
agree("gw1 2a pA", pA, 2.5e5, 1e-9)
agree("gw1 2c Q", QD, 1e-7, 1e-9)
P2 = ("Problem 2 (flow net beneath an impervious dam). Equipotential lines (red dashed) are equally spaced in head. "
      "Upstream reservoir head h = 11 m; head difference between upstream and downstream reservoirs 10 m (10 equal "
      "head drops); K = 10⁻⁷ m/s; datum z = 0 at the bottom of the upstream reservoir; point A lies at z = −15 m; "
      "Box D is 10 m × 10 m. " + USEFUL)
fig2 = clip("o62zs9b4", [4])
add(**GW1, id="gw1_2a", part="2a", max_points=2, answer_modality="numeric", figures=fig2,
    question=P2 + "(a) Determine the hydraulic head hA and the pore pressure pA at point A (read A's equipotential from the figure).",
    reference_answer=f"A lies on the first equipotential below the upstream head: h_A = 11 m − 10 m/10 = {hA2:.0f} m. "
                     f"p_A = ρ·g·(h_A − z_A) = 1000·10·(10 − (−15)) = {pA:.1e} Pa.",
    rubric=[{"points": 1.0, "criterion": "h_A = 10 m (one head drop of 1 m below 11 m)"},
            {"points": 1.0, "criterion": "p_A = ρg(h_A − z_A) = 2.5×10⁵ Pa"}])
add(**GW1, id="gw1_2b", part="2b", max_points=3, answer_modality="short_answer", figures=fig2,
    question=P2 + "(b) Determine the hydraulic gradient between points B and C. Does the pore pressure increase or decrease from B to C?",
    reference_answer=f"h_B = 6 m, h_C = 5 m over Δs = 10 m: i = Δh/Δs = {iBC:.1f}. B and C have the same elevation, but the head at B "
                     "is higher than at C, so the pore pressure decreases from B to C.",
    rubric=[{"points": 1.5, "criterion": "i = (h_B − h_C)/Δs = 1 m / 10 m = 0.1"},
            {"points": 1.5, "criterion": "pore pressure decreases B→C (same elevation, head drops)"}])
add(**GW1, id="gw1_2c", part="2c", max_points=5, answer_modality="numeric", figures=fig2,
    question=P2 + "(c) Determine the groundwater discharge per unit width through Box D (10 m × 10 m).",
    reference_answer=f"Gradient across Box D i = 1 m/10 m = 0.1; Q_D = K·i·A = 1e-7 m/s · 0.1 · (10 m · 1 m) = {QD:.0e} m³/s per metre width.",
    rubric=[{"points": 2.0, "criterion": "gradient across the box i = 0.1"},
            {"points": 1.0, "criterion": "Darcy: Q = K·i·A"},
            {"points": 2.0, "criterion": "Q_D = 1×10⁻⁷ m³/s per m width (A = 10 m × 1 m)"}])

add(**GW1, id="gw1_3", part="3", max_points=9, answer_modality="conceptual", figures=clip("o62zs9b4", [6]),
    question=("Problem 3. The hydraulic conductivity of a homogeneous confined aquifer is to be determined by a pumping test; "
              "the well is screened across the whole aquifer thickness. List three methods that can be applied. For each, "
              "formulate the necessary equations/theory and specify the required quantities."),
    reference_answer=("Any three of: (1) single-well pumping test — steady radial flow in a confined aquifer, Thiem: "
                      "T = Q·ln(R/r_w)/(2π·s_w), K = T/m (needs drawdown, rate, well radius, radius of influence, thickness); "
                      "(2) slug test — transient radial response to an instantaneous head change (Hvorslev/Bouwer–Rice or "
                      "Cooper–Bredehoeft–Papadopulos; needs injected/withdrawn volume, drawdown vs. time, thickness); "
                      "(3) Theis — transient drawdown in observation wells, s = Q/(4πT)·W(u), u = r²S/(4Tt) (needs drawdown "
                      "vs. time, distance, rate, thickness); (4) Cooper–Jacob — late-time approximation "
                      "s = (2.3·Q/(4πT))·log10(2.25·T·t/(r²S)) from one well over time or several wells at one time "
                      "(needs drawdown, distances, rate, thickness)."),
    rubric=[{"points": 3.0, "criterion": "method 1 named with a correct governing equation"},
            {"points": 3.0, "criterion": "method 2 named with a correct governing equation"},
            {"points": 3.0, "criterion": "method 3 named with a correct governing equation; required measured quantities listed for each"}],
    notes="Any three valid methods earn full credit; each needs equation + required quantities.")

# ---- Problem 4: spring gallery
B_, Qg, N, L4, h1, h2 = 200.0, 100e-3 / 60.0, 0.5e-3 / 86400.0, 1000.0, 12.0, 1.0
K4 = (Qg - N * B_ * (L4 - L4 / 2)) * 2 * L4 / (B_ * (h1**2 - h2**2))
agree("gw1 4b K", K4, 7.6e-5, 0.01)
P4 = ("Problem 4 (spring gallery). A gallery in a fractured rock aquifer above an impermeable base collects groundwater; the "
      "detritus layer next to it is very permeable. Over a gallery length B = 200 m the measured outflow is 100 L/min; the "
      "infiltration rate is N = 0.5 mm/d; steady state. Rock aquifer length L = 1000 m; head above the base is h1 = 12 m at "
      "x = 0 (712 m a.s.l.) and h2 = 1 m at x = L (701 m, at the gallery; base z = 700 m). " + USEFUL)
add(**GW1, id="gw1_4a", part="4a", max_points=3, answer_modality="derivation", figures=clip("o62zs9b4", [6]),
    question=P4 + "(a) Formulate the steady-state one-dimensional flow problem (equation and boundary conditions) for the part "
                  "of the rock aquifer between the gallery and the detritus layer.",
    reference_answer="1D steady unconfined flow with recharge: d/dx (K·h·dh/dx) + N = 0, with boundary conditions h(x=0) = 12 m and h(x=L) = 1 m.",
    rubric=[{"points": 1.5, "criterion": "d/dx(K h dh/dx) + N = 0 (unconfined, recharge N)"},
            {"points": 1.5, "criterion": "boundary conditions h(0)=12 m, h(L)=1 m"}])
add(**GW1, id="gw1_4b", part="4b", max_points=3, answer_modality="numeric", figures=clip("o62zs9b4", [6]),
    question=P4 + "(b) What is the hydraulic conductivity of the rock aquifer?",
    reference_answer=(f"Gallery discharge Q = B·K·(h1²−h2²)/(2L) + N·B·(L − L/2) = 100 L/min. Solving for K gives K ≈ {K4:.1e} m/s."),
    rubric=[{"points": 1.5, "criterion": "Q = B·K(h1²−h2²)/(2L) + N·B·(L−L/2)"},
            {"points": 1.5, "criterion": "K ≈ 7.6×10⁻⁵ m/s"}])

# =========================================================================
# GROUNDWATER Assessment II (final), 17 Dec 2020 — no key in the PDF: derived
# =========================================================================
GW2 = dict(course="Groundwater", course_slug="groundwater", exam_name="Assessment II (final Exam), 17 Dec 2020",
           exam_id="xlixdzi0.pdf", term="2020", language="en", reference_source="derived_verified",
           source_exam_pdf="data/groundwater/exams/xlixdzi0.pdf/exam.pdf")
tA, tB, rho_s, Kd = 79.63, 119.45, 2650.0, 3.33e-5
R = tB / tA
porosity = (rho_s * Kd) / (R - 1 + rho_s * Kd)          # R = 1 + (1-n)·rho_s·Kd/n
agree("gw2 3a porosity", porosity, 0.15, 1e-3)
alpha = np.radians(45)
Lpath = 50.0 / np.cos(alpha)
v_pore = Lpath / tA                                        # m/d
q_darcy = porosity * v_pore
dh = 700.0 - 601.0
grad = dh / Lpath
K3 = q_darcy / grad / 86400.0
agree("gw2 3b gradient", grad, 1.4, 2e-3)
Bperp = 0.5 * np.cos(alpha)
nu, gg, Nfr = 1e-6, 10.0, 10
b_ap = (12 * nu * K3 * Bperp / (Nfr * gg)) ** (1 / 3)
Pc_07, sigma = 1.0e7, 0.072
re = 2 * sigma / Pc_07
P3T = ("Problem 3 (fault zone). Water flows from an inclined plane fault zone (dip α = 45°) into an aerated tunnel (seepage face). "
       "Rock grain density in the fault zone 2650 kg/m³; the rock above and below is practically impermeable; steady parallel "
       "flow. Tracers A and B were released simultaneously in the piezometer (head 700 m a.s.l., 50 m horizontal distance "
       "from the tunnel wall); the seepage face spans z = 600.5 m to 601 m. Tracer A is ideal; Tracer B sorbs linearly with "
       "K_d = 3.33×10⁻⁵ m³/kg. Peak arrival times at the tunnel: A 79.63 d, B 119.45 d. " + USEFUL)
add(**GW2, id="gw2_3a", part="3a", max_points=3, answer_modality="numeric", figures=clip("xlixdzi0", [3]),
    question=P3T + "(a) Which type of porosity is meant here, and what is the porosity of the fault zone from the tracer test "
                   "(assume effective porosity = porosity)?",
    reference_answer=(f"Effective (connected, fracture/fault-zone) porosity. Retardation R = t_B/t_A = {R:.3f} = 1 + ρ_b·K_d/n with "
                      f"bulk density ρ_b = (1−n)·ρ_s ⇒ n = ρ_s K_d/(R−1+ρ_s K_d) = {porosity:.2f}."),
    rubric=[{"points": 1.0, "criterion": "retardation factor R = t_B/t_A = 1.5"},
            {"points": 1.0, "criterion": "R = 1 + (1−n)ρ_s K_d / n with ρ_b = (1−n)ρ_s"},
            {"points": 1.0, "criterion": "n = 0.15"}],
    verification="computed here (verify_derived.py)")
add(**GW2, id="gw2_3b", part="3b", max_points=4, answer_modality="numeric", figures=clip("xlixdzi0", [3, 4]),
    question=P3T + "(b) Estimate the hydraulic conductivity of the fault zone.",
    reference_answer=(f"Flow path along the plane L = 50 m/cos45° = {Lpath:.1f} m. Ideal tracer A: pore velocity v = L/t_A = "
                      f"{v_pore:.3f} m/d = {v_pore/86400:.2e} m/s; Darcy velocity q = n·v = {q_darcy/86400:.2e} m/s. Head drop "
                      f"700 − 601 = {dh:.0f} m over L ⇒ i = {grad:.2f}. K = q/i ≈ {K3:.1e} m/s."),
    rubric=[{"points": 1.0, "criterion": "pore velocity from the ideal tracer: v = L/t_A with L = 50/cos45° ≈ 70.7 m (≈0.89 m/d)"},
            {"points": 1.0, "criterion": "Darcy velocity q = n·v"},
            {"points": 1.0, "criterion": "gradient i = (700−601)/70.7 ≈ 1.4"},
            {"points": 1.0, "criterion": "K ≈ 1.1×10⁻⁶ m/s"}],
    confidence="medium", verification="computed here; depends on reading the seepage-face head as z = 601 m",
    notes="Using 600.5 m for the seepage-face head changes K by <1 %; accept 1.0–1.2×10⁻⁶ m/s.")
add(**GW2, id="gw2_3c", part="3c", max_points=3, answer_modality="numeric", figures=clip("xlixdzi0", [3, 4]),
    question=P3T + ("(c) Through the seepage face and logging in the piezometer, an average of 10 fractures is identified over the "
                    "total thickness of the fault zone; they can be assumed parallel to the fault plane and provide the total "
                    "hydraulic conductivity of the fault zone. Determine the average hydraulic aperture of these fractures."),
    reference_answer=(f"Fault-zone thickness perpendicular to the plane: 0.5 m·cos45° = {Bperp:.2f} m. Parallel-plate (cubic-law) "
                      f"transmissivity of N fractures: K·B = N·g·b³/(12ν) ⇒ b = (12νKB/(N g))^(1/3) ≈ {b_ap*1e6:.0f} μm."),
    rubric=[{"points": 1.0, "criterion": "cubic law: T = K·B = N·g·b³/(12ν)"},
            {"points": 1.0, "criterion": "perpendicular zone thickness B ≈ 0.35 m (0.5 m seepage-face height × cos 45°)"},
            {"points": 1.0, "criterion": "b ≈ 36 μm (accept 30–42 μm)"}],
    confidence="medium", verification="computed here; depends on reading the zone thickness from the seepage face",
    notes="If B = 0.5 m is used, b ≈ 40 μm: also accept.")
add(**GW2, id="gw2_4b", part="4b", max_points=4, answer_modality="numeric", figures=clip("xlixdzi0", [4]),
    question=("Problem 4b (cement precipitation). Figure 5 shows the measured water-retention curve of a sample from the shallow "
              "subsurface (capillary pressure P_c in Pa on a log axis vs. water saturation S_w). Water has a contact angle of 0° "
              f"and an interfacial surface tension of 0.072 N/m. Determine the corresponding effective pore size r_e at S_w = 0.7 "
              "using the left figure (the curve)."),
    reference_answer=(f"Read P_c(S_w=0.7) ≈ {Pc_07:.0e} Pa from the curve. Young–Laplace for a cylindrical pore, θ = 0: "
                      f"P_c = 2σ/r_e ⇒ r_e = 2σ/P_c = 2·0.072/{Pc_07:.0e} = {re:.2e} m ≈ {re*1e9:.0f} nm."),
    rubric=[{"points": 1.0, "criterion": "P_c(0.7) ≈ 10⁷ Pa read from the curve (accept 0.8–1.3×10⁷ Pa)"},
            {"points": 1.5, "criterion": "Young–Laplace P_c = 2σ·cosθ/r_e"},
            {"points": 1.5, "criterion": "r_e ≈ 1.4×10⁻⁸ m (14 nm; accept 11–18 nm)"}],
    confidence="medium", verification="P_c read from the figure by pixel extraction (gridline-calibrated): log10 Pc = 7.006",
    notes="Graph reading: accept r_e between 1.1e-8 and 1.8e-8 m.")

# =========================================================================
# GEOCHEMIE I (reconstructions)
# =========================================================================
GC1 = dict(course="Geochemie I", course_slug="geochemiei", language="de", reference_source="derived_verified",
           term="2017/2023")
tau = 0.053 * 1.4e21 / 6e12
agree("gc1 Mg residence time [a]", tau, 1.2367e7, 1e-3)
add(**GC1, id="gc1_2017_1a", part="1a", exam_name="Prüfung Geochemie, 14. August 2017", exam_id="2dsr5grf.pdf",
    source_exam_pdf="data/geochemiei/exams/2dsr5grf.pdf/exam.pdf", figures=clip("2dsr5grf", [1]),
    max_points=3, answer_modality="numeric",
    question=("Im Ozean beträgt die Konzentration an gelöstem Magnesium (Mg) ungefähr 0.053 mol/kg, die Masse des Ozeans beträgt "
              "1.4·10²¹ kg. Die einzigen relevanten Einträge von Mg in den Ozean entstammen Flussläufen, welche pro Jahr "
              "ungefähr 6·10¹² mol Mg in gelöster Form liefern. Welche Residenzzeit zeigt Mg im Ozean?"),
    reference_answer=(f"Residenzzeit τ = Inventar / Zufluss (Fliessgleichgewicht) = 0.053 mol/kg · 1.4·10²¹ kg / 6·10¹² mol/a "
                      f"= {0.053*1.4e21:.2e} mol / 6e12 mol/a ≈ {tau:.2e} a ≈ 12 Millionen Jahre."),
    rubric=[{"points": 1.0, "criterion": "τ = Menge im Reservoir / Flussrate (steady state)"},
            {"points": 1.0, "criterion": "Inventar = 0.053·1.4e21 = 7.4e19 mol"},
            {"points": 1.0, "criterion": "τ ≈ 1.2×10⁷ a (≈12 Ma)"}],
    verification="computed here")
LV_m, LV_p, LV_ci, core = 5.68, 3e-4, 556.0, 0.325
Mm = 1 - core
f_mantle = (LV_m - LV_p) / (LV_ci - LV_p)
f_earth = f_mantle * Mm
agree("gc1 late veneer f_mantle", f_mantle, 0.010216, 1e-3)
add(**GC1, id="gc1_2023_4", part="4", exam_name="Prüfungsrekonstruktion Geochemie I, Sommer 2023", exam_id="3qrh212s.pdf",
    source_exam_pdf="data/geochemiei/exams/3qrh212s.pdf/exam.pdf", figures=clip("3qrh212s", [1, 2]),
    max_points=4, answer_modality="numeric",
    question=("Berechne den Anteil der Erdmasse, der im „late veneer“ auf die Erde gekommen ist, mit Hilfe der Pb-Konzentration "
              "und dem Aufstellen von Massenbilanzen. Gegeben: Pb heute im Erdmantel 5.68 ng/g; Pb im Protoerden-Mantel "
              "3·10⁻⁴ ng/g; CI-Chondrite 556 ng/g; Massenanteil Erdkern 32.5 %."),
    reference_answer=(f"Annahme: das late veneer (CI-chondritische Zusammensetzung) wurde nach der Kernbildung vollständig dem Mantel "
                      f"zugefügt. Massenbilanz im Mantel: C_heute·M_M = C_proto·(M_M − M_LV) + C_CI·M_LV ⇒ "
                      f"M_LV/M_M = (5.68 − 3e-4)/(556 − 3e-4) = {f_mantle:.4f} ≈ {100*f_mantle:.2f} % der Mantelmasse. "
                      f"Mit M_M = (1 − 0.325)·M_Erde = 0.675·M_Erde: M_LV/M_Erde ≈ {100*f_earth:.2f} %."),
    rubric=[{"points": 2.0, "criterion": "Massenbilanz im Mantel mit Protomantel-Pb und CI-Chondrit-Pb als Endglieder"},
            {"points": 1.0, "criterion": "≈1.0 % der Mantelmasse"},
            {"points": 1.0, "criterion": "≈0.69 % der Erdmasse (Mantelanteil 0.675)"}],
    confidence="medium", verification="computed here; the reconstructed exam leaves the core-fraction convention implicit",
    notes="Beide Angaben (≈1.0 % Mantel, ≈0.69 % Erde) akzeptieren; die Rekonstruktion nennt keine Musterlösung.")

# =========================================================================
# ISOTOPENGEOCHEMIE exams (Geochemie II) — decay-constant computations
# =========================================================================
l238, l235, lRb = 1.55125e-10, 9.8485e-10, 1.42e-11
ISO = dict(course="Isotopengeochemie (Geochemie II)", course_slug="geochemieii", language="de", reference_source="derived_verified")

# ---- 24 Jan 2011
I11 = dict(ISO, exam_name="BSc Sessionsprüfung Isotopengeochemie, 24. Januar 2011", exam_id="lxrou8zq.pdf", term="2011",
           source_exam_pdf="data/geochemieii/exams/lxrou8zq.pdf/exam.pdf")
t10 = np.log(137.88 / 10.0) / (l235 - l238)
agree("iso11 1 back-substitution R(t)", 137.88 * np.exp(-(l235 - l238) * t10), 10.0, 1e-9)
add(**I11, id="iso11_1", part="1", figures=clip("lxrou8zq", [1]), max_points=4, answer_modality="numeric",
    question=("Aufgabe 1 (Radioaktiver Zerfall). Vor wie vielen Jahren hatte das ²³⁸U/²³⁵U-Verhältnis einen Wert von genau 10.0? "
              "Berechnen Sie diesen Zeitpunkt auf 1 Ma genau. Parameter: λ238 = 1.55125·10⁻¹⁰ a⁻¹, λ235 = 9.8485·10⁻¹⁰ a⁻¹, "
              "(²³⁸U/²³⁵U)heute = 137.88."),
    reference_answer=(f"(²³⁸U/²³⁵U)(t) = 137.88·exp[(λ238 − λ235)·t] mit t Jahre in der Vergangenheit ⇒ 10 = 137.88·exp[−(λ235−λ238)t] "
                      f"⇒ t = ln(13.788)/(λ235 − λ238) = {t10:.4e} a ≈ {t10/1e6:.0f} Ma."),
    rubric=[{"points": 2.0, "criterion": "R(t) = R_0·exp[−(λ235−λ238)·t] korrekt aufgestellt (²³⁵U zerfällt schneller)"},
            {"points": 2.0, "criterion": "t ≈ 3162 Ma (±2 Ma)"}],
    verification="computed here", notes="Die Aufgabe verlangt 1-Ma-Genauigkeit: 3162 ± 2 Ma.")
r7, r6 = 10.73, 0.4738
t7, t6 = np.log(1 + r7) / l235, np.log(1 + r6) / l238
agree("iso11 2a t207 [Ma]", t7 / 1e6, 2500.0, 2e-3)
agree("iso11 2a t206 [Ma]", t6 / 1e6, 2499.0, 2e-3)
add(**I11, id="iso11_2a", part="2a", figures=clip("lxrou8zq", [2]), max_points=3, answer_modality="numeric",
    question=("Aufgabe 2a (U-Pb-Datierung). Berechnen Sie beide U-Pb-Alter eines Zirkons aus den gemessenen Verhältnissen "
              "²⁰⁷Pb_rad/²³⁵U = 10.73 und ²⁰⁶Pb_rad/²³⁸U = 0.4738 (Konstanten aus Aufgabe 1; D = P·(e^{λt} − 1)). "
              "Interpretieren Sie das Resultat."),
    reference_answer=(f"t = ln(1 + D/P)/λ: t(²⁰⁷Pb/²³⁵U) = ln(11.73)/λ235 = {t7/1e6:.0f} Ma; t(²⁰⁶Pb/²³⁸U) = ln(1.4738)/λ238 = "
                      f"{t6/1e6:.0f} Ma. Beide Alter stimmen überein (≈2.5 Ga): konkordant — geschlossenes U-Pb-System, Kristallisationsalter ≈ 2.5 Ga."),
    rubric=[{"points": 1.0, "criterion": "t207 ≈ 2500 Ma"}, {"points": 1.0, "criterion": "t206 ≈ 2499 Ma"},
            {"points": 1.0, "criterion": "beide gleich ⇒ konkordant ⇒ ungestörtes System"}], verification="computed here")
r7b, r6b = 3.740, 0.1953
t7b, t6b = np.log(1 + r7b) / l235, np.log(1 + r6b) / l238
agree("iso11 2b t207 [Ma]", t7b / 1e6, 1580.0, 5e-3)
agree("iso11 2b t206 [Ma]", t6b / 1e6, 1150.0, 5e-3)
add(**I11, id="iso11_2b", part="2b", figures=clip("lxrou8zq", [2]), max_points=3, answer_modality="numeric",
    question=("Aufgabe 2b. Berechnen Sie beide U-Pb-Alter eines Zirkons aus einem anderen Gebiet aus ²⁰⁷Pb_rad/²³⁵U = 3.740 und "
              "²⁰⁶Pb_rad/²³⁸U = 0.1953 und interpretieren Sie das Resultat."),
    reference_answer=(f"t(²⁰⁷Pb/²³⁵U) = ln(4.740)/λ235 = {t7b/1e6:.0f} Ma; t(²⁰⁶Pb/²³⁸U) = ln(1.1953)/λ238 = {t6b/1e6:.0f} Ma. "
                      "Die Alter sind diskordant (t207 > t206): Hinweis auf Pb-Verlust (oder Mischung/Vererbung); der Datenpunkt liegt "
                      "unterhalb der Konkordia, das wahre Alter liegt ≥ t207."),
    rubric=[{"points": 1.0, "criterion": "t207 ≈ 1580 Ma"}, {"points": 1.0, "criterion": "t206 ≈ 1150 Ma"},
            {"points": 1.0, "criterion": "diskordant (t207 > t206) ⇒ Pb-Verlust/Mischung; Punkt unterhalb der Konkordia"}],
    verification="computed here")

# ---- 22 Jan 2008
I08 = dict(ISO, exam_name="BSc Sessionsprüfung Isotopengeochemie, 22. Januar 2008", exam_id="jbojruz4.pdf", term="2008",
           source_exam_pdf="data/geochemieii/exams/jbojruz4.pdf/exam.pdf")
P4T = ("Aufgabe 4 (Abkühlungsraten). An Muskovit und Biotit aus einem Handstück bestimmen Sie folgende Rb-Sr-Daten: "
       "Muskovit ⁸⁷Rb/⁸⁶Sr = 75.2, ⁸⁷Sr/⁸⁶Sr = 0.72977; Biotit ⁸⁷Rb/⁸⁶Sr = 121.7, ⁸⁷Sr/⁸⁶Sr = 0.73099. "
       "Beide Proben haben ein identisches initiales ⁸⁷Sr/⁸⁶Sr von 0.70900. λ(⁸⁷Rb) = 1.42·10⁻¹¹ a⁻¹. ")
rad_m, rad_b = 0.72977 - 0.709, 0.73099 - 0.709
age_m, age_b = np.log(1 + rad_m / 75.2) / lRb, np.log(1 + rad_b / 121.7) / lRb
rate = (500 - 390) / ((age_m - age_b) / 1e6)
agree("iso08 4b age Mus [Ma]", age_m / 1e6, 19.45, 5e-3)
agree("iso08 4b age Bt [Ma]", age_b / 1e6, 12.72, 5e-3)
add(**I08, id="iso08_4ab", part="4a-b", figures=clip("jbojruz4", [5]), max_points=3, answer_modality="numeric",
    question=P4T + "(a) Berechnen Sie die ⁸⁷Sr_rad/⁸⁶Sr-Verhältnisse der Proben. (b) Berechnen Sie die Alter der beiden Proben.",
    reference_answer=(f"(a) ⁸⁷Sr_rad/⁸⁶Sr = gemessen − initial: Muskovit {rad_m:.5f}, Biotit {rad_b:.5f}. "
                      f"(b) t = ln(1 + (⁸⁷Sr_rad/⁸⁶Sr)/(⁸⁷Rb/⁸⁶Sr))/λ: Muskovit {age_m/1e6:.1f} Ma, Biotit {age_b/1e6:.1f} Ma."),
    rubric=[{"points": 1.0, "criterion": "radiogene Verhältnisse 0.02077 (Mus) und 0.02199 (Bt)"},
            {"points": 1.0, "criterion": "Muskovit-Alter ≈ 19.4 Ma"}, {"points": 1.0, "criterion": "Biotit-Alter ≈ 12.7 Ma"}],
    verification="computed here")
add(**I08, id="iso08_4cd", part="4c-d", figures=clip("jbojruz4", [5]), max_points=2, answer_modality="numeric",
    question=P4T + ("(c) Definieren die beiden Proben unter den gegebenen Voraussetzungen eine Isochrone? Begründen Sie. "
                    "(d) Welche Abkühlungsrate berechnen Sie, wenn Sie Schliessungstemperaturen von 500 °C (Muskovit) und "
                    "390 °C (Biotit) annehmen?"),
    reference_answer=(f"(c) Nein: die beiden Proben ergeben unterschiedliche Alter ({age_m/1e6:.1f} vs {age_b/1e6:.1f} Ma), liegen also nicht auf einer "
                      f"gemeinsamen Isochrone durch das gemeinsame Initialverhältnis (die Steigungen (⁸⁷Sr_rad/⁸⁶Sr)/(⁸⁷Rb/⁸⁶Sr) sind verschieden). "
                      f"(d) Abkühlungsrate = ΔT/Δt = (500−390) °C/({age_m/1e6:.1f}−{age_b/1e6:.1f}) Ma ≈ {rate:.0f} °C/Ma."),
    rubric=[{"points": 1.0, "criterion": "(c) nein, da unterschiedliche Alter / Steigungen verschieden"},
            {"points": 1.0, "criterion": "(d) ≈ 16 °C/Ma (110 °C in ≈ 6.7 Ma)"}], verification="computed here")
x3, y3 = np.exp(l235 * 3.0e9) - 1, np.exp(l238 * 3.0e9) - 1
x2, y2 = np.exp(l235 * 2.0e9) - 1, np.exp(l238 * 2.0e9) - 1
m_d = (y3 - y2) / (x3 - x2)
q_d = y2 - m_d * x2
agree("iso08 5b x", x3, 18.19, 5e-3)
add(**I08, id="iso08_5b", part="5b", figures=clip("jbojruz4", [6]), max_points=2, answer_modality="numeric",
    question=("Aufgabe 5b. Berechnen Sie die Koordinaten (²⁰⁷Pb_rad/²³⁵U ; ²⁰⁶Pb_rad/²³⁸U) eines Zirkons, der vor 3.0 Ga aus einer Schmelze "
              "kristallisierte und dessen U-Pb-System bis heute geschlossen blieb (λ235 = 9.8485·10⁻¹⁰ a⁻¹, λ238 = 1.55125·10⁻¹⁰ a⁻¹)."),
    reference_answer=(f"x = ²⁰⁷Pb_rad/²³⁵U = e^{{λ235·3.0 Ga}} − 1 = {x3:.2f}; y = ²⁰⁶Pb_rad/²³⁸U = e^{{λ238·3.0 Ga}} − 1 = {y3:.4f} "
                      f"(Punkt auf der Konkordia)."),
    rubric=[{"points": 1.0, "criterion": "²⁰⁷Pb/²³⁵U ≈ 18.19"}, {"points": 1.0, "criterion": "²⁰⁶Pb/²³⁸U ≈ 0.5925"}],
    verification="computed here")
add(**I08, id="iso08_5c", part="5c", figures=clip("jbojruz4", [6]), max_points=3, answer_modality="numeric",
    question=("Aufgabe 5c. Wie lautet die Gleichung der Diskordia-Geraden (y = m·x + q), auf der die Datenpunkte aller Zirkone liegen, "
              "deren Primäralter dem der Aufgabe 5b (3.0 Ga) entspricht, die aber in unterschiedlichem Mass vor 2.0 Ga radiogenes Pb "
              "verloren haben? (x = ²⁰⁷Pb_rad/²³⁵U, y = ²⁰⁶Pb_rad/²³⁸U)"),
    reference_answer=(f"Die Diskordia ist die Gerade durch die Konkordiapunkte bei 3.0 Ga ({x3:.2f}; {y3:.4f}) (oberer Schnittpunkt) und 2.0 Ga "
                      f"({x2:.3f}; {y2:.4f}) (unterer Schnittpunkt = Zeitpunkt des Pb-Verlusts): m = Δy/Δx = {m_d:.5f}, "
                      f"q = {q_d:.4f}, also y ≈ {m_d:.4f}·x + {q_d:.3f}."),
    rubric=[{"points": 1.0, "criterion": "Gerade durch die Konkordiapunkte bei 3.0 Ga und 2.0 Ga (Pb-Verlust zur Zeit 2.0 Ga)"},
            {"points": 1.0, "criterion": "Steigung m ≈ 0.019"}, {"points": 1.0, "criterion": "Achsenabschnitt q ≈ 0.246"}],
    verification="computed here")

# ---- 10 Aug 2009
I09 = dict(ISO, exam_name="BSc Sessionsprüfung Isotopengeochemie, 10. August 2009", exam_id="r22ulkoa.pdf", term="2009",
           source_exam_pdf="data/geochemieii/exams/r22ulkoa.pdf/exam.pdf")
INTRO9 = ("Aufgabe 1 (Massenspektrometrie). In einer Ionenquelle werden Ionen der Masse m mit je einer Elementarladung e erzeugt und in "
          "einem elektrischen Feld mit der Spannung U beschleunigt (Anfangsenergie vernachlässigt): v = √(2·(e/m)·U). ")
add(**I09, id="iso09_1a", part="1a", figures=clip("r22ulkoa", [1]), max_points=1, answer_modality="short_answer",
    question=INTRO9 + "(a) Zwei Ionensorten der Massen m1 und m2 werden in einem Flugzeit-Massenspektrometer analysiert. Wie gross ist das "
                      "Verhältnis der Flugzeiten t(m2)/t(m1) für die konstante Flugstrecke s?",
    reference_answer="t = s/v = s·√(m/(2eU)) ⇒ t(m2)/t(m1) = √(m2/m1).",
    rubric=[{"points": 1.0, "criterion": "t(m2)/t(m1) = √(m2/m1)"}], verification="derived analytically")
add(**I09, id="iso09_1b", part="1b", figures=clip("r22ulkoa", [1]), max_points=2, answer_modality="short_answer",
    question=INTRO9 + ("(b) Im magnetischen Sektorfeld B gilt m/e = r²B²/(2U). B1 sei so gewählt, dass Ionen der Masse m1 den Austrittsspalt mit "
                       "Bahnradius r1 treffen. Wie gross muss der Bahnradius r2 eines zweiten Austrittsspalts sein, damit er bei gleichem B1 "
                       "von Ionen der Masse m2 getroffen wird?"),
    reference_answer="r² = 2U·m/(e·B²) ∝ m bei festem B ⇒ r2 = r1·√(m2/m1).",
    rubric=[{"points": 2.0, "criterion": "r2 = r1·√(m2/m1)"}], verification="derived analytically")
add(**I09, id="iso09_1c", part="1c", figures=clip("r22ulkoa", [1]), max_points=2, answer_modality="short_answer",
    question=INTRO9 + ("(c) Wie gross muss die magnetische Feldstärke B2 gewählt werden, damit Ionen der Masse m2 den Austrittsspalt mit Bahnradius "
                       "r1 treffen (gegeben m1, m2, B1)?"),
    reference_answer="Bei festem r: B² ∝ m ⇒ B2 = B1·√(m1/m2).",
    rubric=[{"points": 2.0, "criterion": "B2 = B1·√(m1/m2)"}], verification="derived analytically")
age9 = np.log(1 + (0.7310 - 0.7060) / 70.0) / lRb
agree("iso09 2c age [Ma]", age9 / 1e6, 25.14, 5e-3)
add(**I09, id="iso09_2c", part="2c", figures=clip("r22ulkoa", [2]), max_points=3, answer_modality="numeric",
    question=("Aufgabe 2c. Eine Biotitanalyse ergibt ⁸⁷Rb/⁸⁶Sr = 70.0 sowie ⁸⁷Sr/⁸⁶Sr = 0.7310. Wie alt ist die Probe unter Annahme eines "
              "initialen ⁸⁷Sr/⁸⁶Sr-Wertes von 0.7060 (λ87Rb = 1.42·10⁻¹¹ a⁻¹)?"),
    reference_answer=(f"t = ln(1 + (0.7310 − 0.7060)/70.0)/λ = ln(1 + {0.025/70:.4e})/1.42e-11 = {age9/1e6:.1f} Ma."),
    rubric=[{"points": 1.0, "criterion": "Isochronengleichung ⁸⁷Sr/⁸⁶Sr = (⁸⁷Sr/⁸⁶Sr)_0 + ⁸⁷Rb/⁸⁶Sr·(e^{λt} − 1)"},
            {"points": 2.0, "criterion": "t ≈ 25 Ma (25.1 Ma)"}], verification="computed here")


# =========================================================================
# BATCH 2 — remaining Geochemie / Isotopengeochemie exams.
# Points are deliberately UNASSIGNED: rubric lines carry weight 1, max_points = number of lines.
# =========================================================================
l232 = 4.9475e-11
l147, lLu = 6.54e-12, np.log(2) / 3.59e10
XI = "Isotopengeochemie (Geochemie II)"


def exam(eid, name, term, extra=None):
    d = dict(ISO, exam_name=name, exam_id=eid, term=term, source_exam_pdf=f"data/geochemieii/exams/{eid}/exam.pdf")
    d.update(extra or {})
    return d


def he_mol(U238, ratio, Th, t):
    U235 = U238 / ratio
    return (8 * U238 * (np.exp(l238 * t) - 1) + 7 * U235 * (np.exp(l235 * t) - 1) + 6 * Th * (np.exp(l232 * t) - 1))


def conc(t, lam):
    return np.exp(lam * t) - 1


# ---------------- 5 Oct 2006 (HS06): nuclide masses, Sm-Nd isochrons
H06 = exam("2nnqx08v.pdf", "Prüfung Isotopengeochemie und Isotopengeologie I, 5. Oktober 2006", "2006")
add(**H06, id="iso06_1ab", part="1a-b", figures=clip("2nnqx08v", [1, 2]), answer_modality="short_answer",
    question=("Aufgabe 1 (Kernphysik). Auf der Nuklidkarte sind Atomkerne als Quadrate dargestellt (Abszisse: Neutronenzahl, Ordinate: "
              "Ordnungszahl). (a) Im Quadrat von ¹³⁸Ce (Z = 58) steht die Isotopenmasse 137.90599 u; bei ¹³⁸La (Z = 57) findet man "
              "137.90711 u. Welcher der beiden Kerne ist demnach radioaktiv? (b) Welcher Zerfallstyp erzeugt aus einem der unter (a) "
              "genannten Kerne den anderen?"),
    reference_answer=("(a) ¹³⁸La ist radioaktiv: bei gleicher Massenzahl (Isobare) ist es schwerer (137.90711 u) als ¹³⁸Ce (137.90599 u), "
                      "kann also unter Energiegewinn in den leichteren Nachbarn zerfallen. (b) β⁻-Zerfall: ¹³⁸La (Z=57) → ¹³⁸Ce (Z=58) "
                      "(Neutron → Proton, Z+1 bei konstantem A)."),
    rubric=["¹³⁸La als radioaktiver Kern identifiziert, begründet mit der grösseren Masse gegenüber dem Isobar",
            "β⁻-Zerfall ¹³⁸La → ¹³⁸Ce (Z erhöht sich um 1, A bleibt gleich)"],
    verification="derived analytically from the given masses")
add(**H06, id="iso06_1c", part="1c", figures=clip("2nnqx08v", [1, 2]), answer_modality="conceptual",
    question=("Aufgabe 1c. Welche der vier grundlegenden Wechselwirkungen („Gravitation“, „Elektromagnetische“, „Starke“, „Schwache“) ist die "
              "Hauptursache für den unter 1b gesuchten Zerfallstyp, und wie heisst der entsprechende Term in der Massenformel nach "
              "von Weizsäcker (siehe Beilage der Prüfung)?"),
    reference_answer="Die schwache Wechselwirkung verursacht den β-Zerfall; der entsprechende Term der Massenformel ist die Asymmetrieenergie a_A·(A−2Z)²/A.",
    rubric=["schwache Wechselwirkung", "Asymmetrieenergie-Term a_A(A−2Z)²/A"],
    verification="from the exam's own Beilage, which labels the asymmetry term 'schwache Kraft'")
add(**H06, id="iso06_1d", part="1d", figures=clip("2nnqx08v", [1, 2]), answer_modality="conceptual",
    question=("Aufgabe 1d. ¹³⁸Ba (Z = 56) hat die Isotopenmasse 137.90524 u. Welche mathematische Eigenschaft haben die Protonen- und "
              "Neutronenzahlen der drei Kerne ¹³⁸Ba, ¹³⁸La, ¹³⁸Ce, und wie heisst der damit zusammenhängende Term der Massenformel, der die "
              "relativen Werte der drei Isotopenmassen erklärt?"),
    reference_answer=("¹³⁸Ba (Z=56, N=82) und ¹³⁸Ce (Z=58, N=80) sind gerade-gerade (gg), ¹³⁸La (Z=57, N=81) ist ungerade-ungerade (uu). "
                      "Der Paarungsenergie-Term ±a_P·A^(−3/4) macht gg-Kerne leichter (−) und uu-Kerne schwerer (+); darum liegt ¹³⁸La über den beiden Nachbarn."),
    rubric=["Ba und Ce gerade-gerade (Z,N gerade), La ungerade-ungerade (Z,N ungerade)",
            "Paarungsenergie ±a_P·A^(−3/4): gg leichter, uu schwerer"],
    verification="derived from Z, N parity and the exam's Beilage")
# Sm-Nd isochrons
wr = np.array([[0.0741, 0.510376], [0.0871, 0.510638], [0.0999, 0.510902], [0.1707, 0.512195], [0.2346, 0.513518]])
mn = np.array([[0.9170, 0.521015], [0.8730, 0.520465], [0.0254, 0.509867], [0.2260, 0.512375]])
m_wr = np.polyfit(wr[:, 0], wr[:, 1], 1)[0]
m_mn = np.polyfit(mn[:, 0], mn[:, 1], 1)[0]
t_wr = np.log(1 + m_wr) / l147
t_mn = np.log(1 + m_mn) / l147
on_line = [round(float(np.polyval(np.polyfit(mn[:, 0], mn[:, 1], 1), x) - y), 6) for x, y in wr]
agree("iso06 2 mineral age [Ga]", t_mn / 1e9, 1.90, 0.01)
pair = [np.log(1 + (wr[j, 1] - wr[i, 1]) / (wr[j, 0] - wr[i, 0])) / l147 / 1e9 for i in range(5) for j in range(i + 1, 5)]
assert min(pair) - 1e-9 <= t_wr / 1e9 <= max(pair) + 1e-9, "fit outside the range of pairwise ages"
print(f"OK   iso06 2 whole-rock fit {t_wr/1e9:.2f} Ga, pairwise range {min(pair):.2f}-{max(pair):.2f} Ga")
SMT = ("Aufgabe 2 (Isochronen). Sm-Nd-Daten (¹⁴⁷Sm/¹⁴⁴Nd ; ¹⁴³Nd/¹⁴⁴Nd) einer Serie von Gesamtgesteinsproben aus einer Gneisregion: "
       "(0.0741; 0.510376), (0.0871; 0.510638), (0.0999; 0.510902), (0.1707; 0.512195), (0.2346; 0.513518). Mineralien, die aus einer der "
       "Gesamtgesteinsproben präpariert wurden: (0.9170; 0.521015), (0.8730; 0.520465), (0.0254; 0.509867), (0.2260; 0.512375). "
       "λ(¹⁴⁷Sm) = 6.54·10⁻¹² a⁻¹. ")
add(**H06, id="iso06_2ab", part="2a-b", figures=clip("2nnqx08v", [3]), answer_modality="numeric",
    question=SMT + ("(a) Geben Sie eine kurze qualitative Interpretation der Daten bezüglich der geologischen Geschichte. (b) Berechnen Sie die Alter "
                    "der in (a) beschriebenen geologischen Ereignisse (nur grobe Berechnung, keine Geraden-Fits)."),
    reference_answer=(f"Zwei Isochronen: Die Gesamtgesteinsproben liegen auf einer Geraden mit Steigung ≈ {m_wr:.4f} ⇒ t = ln(1+m)/λ ≈ {t_wr/1e9:.1f} Ga "
                      f"(älteres Ereignis, z. B. Krustenbildung/Protolith). Die Mineralien liegen auf einer anderen Geraden mit Steigung ≈ {m_mn:.4f} ⇒ "
                      f"t ≈ {t_mn/1e9:.2f} Ga (jüngeres Ereignis, z. B. Metamorphose/Rehomogenisierung der Mineralien, wobei das Gesamtgestein "
                      "ein geschlossenes System blieb)."),
    rubric=["Zwei verschiedene Isochronen (Gesamtgestein vs. Mineralien) erkannt und als zwei Ereignisse gedeutet",
            "Gesamtgesteinsalter ≈ 2.9 Ga (akzeptiere 2.7–3.2 Ga)", "Mineralalter ≈ 1.9 Ga (akzeptiere 1.8–2.0 Ga)"],
    verification="computed here (least-squares slope of each group; the mineral line passes through whole-rock point 2 within 1e-6)",
    notes="Die Aufgabe verlangt nur grobe Berechnung. Die Gesamtgesteinspunkte sind nicht exakt kollinear (Paaralter 2.8–3.2 Ga); Fit ≈ 2.9 Ga. Die Mineralgerade geht exakt durch die zweite Gesamtgesteinsprobe.")
add(**H06, id="iso06_2c", part="2c", figures=clip("2nnqx08v", [3]), answer_modality="conceptual",
    question=SMT + ("(c) Falls sich herausstellt, dass dem aus dem Gesamtgesteinsmuster abgeleiteten Alter kein reales geologisches Ereignis entspricht, "
                    "welche alternative Erklärung bietet sich für dieses Datenmuster an?"),
    reference_answer="Eine Pseudochrone infolge binärer Mischung zweier Endglieder (Mischungslinie), die in diesem Diagramm eine Gerade bildet, ohne ein Alter zu haben.",
    rubric=["binäre Mischung / Mischungsgerade (Pseudochrone) als Erklärung"],
    verification="standard isotope-geochemistry result; the exam's own question 3b of the 2011 paper uses the same wording")

# ---------------- 1 Mar 2007 (FS07)
F07 = exam("q5d0tona.pdf", "BSc Sessionsprüfung Isotopengeochemie, 1. März 2007", "2007")
s_lu = (0.294 - 0.286) / (8.0 - 2.2)
age_lu = np.log(1 + s_lu) / lLu
init_lu = 0.286 - s_lu * 2.2
agree("iso07 Lu-Hf age [Ma]", age_lu / 1e6, 71.4, 5e-3)
LU = ("Aufgabe 3 (Lu-Hf). ¹⁷⁶Lu zerfällt durch β⁻-Zerfall zum stabilen ¹⁷⁶Hf; Normierungsisotop ist ¹⁷⁷Hf. Zwei der drei Proben haben im "
      "Isochronendiagramm (x = ¹⁷⁶Lu/¹⁷⁷Hf, y = ¹⁷⁶Hf/¹⁷⁷Hf) die Koordinaten (x1; y1) = (2.2; 0.286) und (x2; y2) = (8.0; 0.294). "
      "¹⁷⁶Lu hat eine Halbwertszeit von 3.59·10¹⁰ a. ")
add(**F07, id="iso07_3c", part="3c", figures=clip("q5d0tona", [4]), answer_modality="numeric",
    question=LU + "(c) Wie alt sind die Proben?",
    reference_answer=(f"Steigung der Isochrone m = (0.294 − 0.286)/(8.0 − 2.2) = {s_lu:.6f}; λ = ln2/T½ = {lLu:.4e} a⁻¹; "
                      f"t = ln(1 + m)/λ = {age_lu/1e6:.1f} Ma."),
    rubric=["Isochronensteigung m = Δy/Δx = e^{λt} − 1 aus den zwei Punkten", "λ = ln2/T½ = 1.93·10⁻¹¹ a⁻¹", "t ≈ 71 Ma"],
    verification="computed here", notes="Mit der Näherung t ≈ m/λ ergibt sich 71.4 Ma ebenfalls (Differenz < 0.1 %).")
add(**F07, id="iso07_3d", part="3d", figures=clip("q5d0tona", [4]), answer_modality="numeric",
    question=LU + "(d) Welcher Wert war den drei Proben beim Start des Systems gemeinsam? Berechnen Sie diesen Wert.",
    reference_answer=f"Das gemeinsame Initialverhältnis (¹⁷⁶Hf/¹⁷⁷Hf)₀ = y-Achsenabschnitt der Isochrone = y1 − m·x1 = 0.286 − {s_lu:.6f}·2.2 = {init_lu:.5f}.",
    rubric=["gemeinsamer Wert = Initialverhältnis (¹⁷⁶Hf/¹⁷⁷Hf)₀ (y-Achsenabschnitt)", "(¹⁷⁶Hf/¹⁷⁷Hf)₀ ≈ 0.2830"],
    verification="computed here")
CHUR0 = 0.512638
dSm = 0.22 - 0.1967
t_nd = np.log(1 + (10.0 / 1e4) * CHUR0 / dSm) / l147
agree("iso07 4b separation age [Ga]", t_nd / 1e9, 3.33, 0.01)
add(**F07, id="iso07_4b", part="4b", figures=clip("q5d0tona", [5]), answer_modality="numeric",
    question=("Aufgabe 4b (Nd-Evolution). Seit wann ist das MORB-Reservoir vom CHUR-Reservoir getrennt? Gegeben: λ(¹⁴⁷Sm) = 6.54·10⁻¹² a⁻¹, "
              "ε_Nd(MORB) = +10, ¹⁴⁷Sm/¹⁴⁴Nd(CHUR) = 0.1967, ¹⁴⁷Sm/¹⁴⁴Nd(MORB) = 0.22."),
    reference_answer=(f"ε = 10⁴·[(¹⁴³Nd/¹⁴⁴Nd)_MORB/(¹⁴³Nd/¹⁴⁴Nd)_CHUR − 1] = 10⁴·Δ(Sm/Nd)·(e^{{λt}} − 1)/(¹⁴³Nd/¹⁴⁴Nd)_CHUR(heute). Mit "
                      f"(¹⁴³Nd/¹⁴⁴Nd)_CHUR = {CHUR0} (Vorlesungswert, in der Aufgabe nicht angegeben): e^{{λt}} − 1 = 10⁻³·{CHUR0}/{dSm:.4f} = "
                      f"{1e-3*CHUR0/dSm:.5f} ⇒ t = ln(1.02200)/λ ≈ {t_nd/1e9:.2f} Ga."),
    rubric=["Beziehung ε_Nd ↔ Differenz der ¹⁴⁷Sm/¹⁴⁴Nd-Verhältnisse und e^{λt} − 1", "t ≈ 3.3 Ga (akzeptiere 3.2–3.4 Ga)"],
    confidence="medium", verification="computed here; needs (143Nd/144Nd)_CHUR = 0.512638, which this exam does not print",
    notes="Der CHUR-Wert 0.512638 steht in der Prüfung vom 22. Januar 2008 (Aufgabe 6c), nicht in dieser. Ohne ihn ist die Aufgabe nicht eindeutig.")

# ---------------- 5 Aug 2008 (FS08 isotopen) & 26 Jan 2009 (HS08): U-Pb / He
def uPbxy(t):
    return conc(t, l235), conc(t, l238)

x450, y450 = uPbxy(4.5e8)
x300, y300 = uPbxy(3.0e8)
agree("U-Pb 450 Ma x", x450, 0.5576, 1e-3)
agree("U-Pb 300 Ma y", y300, 0.04763, 2e-3)
UPB = ("Die radioaktiven Mutterkerne ²³⁸U, ²³⁵U und ²³²Th zerfallen über mehrere Stufen zu den stabilen Tochterkernen ²⁰⁶Pb, ²⁰⁷Pb und ²⁰⁸Pb "
       "(λ238 = 1.55125·10⁻¹⁰ a⁻¹, λ235 = 9.8485·10⁻¹⁰ a⁻¹, λ232 = 4.9475·10⁻¹¹ a⁻¹; D = P·(e^{λt} − 1)). ")
F08 = exam("2b1u4d09.pdf", "BSc Sessionsprüfung Isotopengeochemie, 5. August 2008", "2008")
H08 = exam("ov68rh0o.pdf", "BSc Sessionsprüfung Isotopengeochemie, 26. Januar 2009", "2009")
for E, tag, pg in ((F08, "iso08b", [6]), (H08, "iso09b", [3])):
    add(**E, id=f"{tag}_ua", part="a", figures=clip(E["exam_id"][:-4], pg), answer_modality="numeric",
        question=("Konkordiadiagramm. " + UPB + "Berechnen Sie die heutigen ²⁰⁷Pb_rad/²³⁵U- und ²⁰⁶Pb_rad/²³⁸U-Werte eines Zirkons, dessen U-Pb-System "
                  "seit seiner Kristallisation bei 450 Ma geschlossen war."),
        reference_answer=f"²⁰⁷Pb_rad/²³⁵U = e^{{λ235·450 Ma}} − 1 = {x450:.4f}; ²⁰⁶Pb_rad/²³⁸U = e^{{λ238·450 Ma}} − 1 = {y450:.4f} (Punkt auf der Konkordia).",
        rubric=["²⁰⁷Pb/²³⁵U ≈ 0.5576", "²⁰⁶Pb/²³⁸U ≈ 0.0723"], verification="computed here")
add(**F08, id="iso08b_ub", part="b", figures=clip("2b1u4d09", [6]), answer_modality="numeric",
    question=("Konkordiadiagramm. " + UPB + "Ein 1 Ga altes U-reiches Mineral erleidet bei 300 Ma während einer Metamorphose einen vollständigen "
              "Pb-Verlust. Danach bleibt sein U-Pb-System bis heute geschlossen. Berechnen Sie die heutigen Konkordia-Koordinatenwerte des Minerals."),
    reference_answer=(f"Vollständiger Pb-Verlust setzt die Uhr bei 300 Ma auf null zurück; das Mineral liegt heute auf der Konkordia bei 300 Ma: "
                      f"²⁰⁷Pb_rad/²³⁵U = {x300:.4f}, ²⁰⁶Pb_rad/²³⁸U = {y300:.4f}."),
    rubric=["Pb-Verlust setzt die Uhr zurück ⇒ Konkordiapunkt bei 300 Ma (nicht bei 1 Ga)", "(0.3437; 0.04763)"], verification="computed here")
U_, ratio_ = 1e-6, 137.88
he_f = he_mol(U_, ratio_, 5e-7, 1e9)
he_h = he_mol(U_, ratio_, 5e-6, 1e9)
add(**F08, id="iso08b_uc", part="c", figures=clip("2b1u4d09", [6]), answer_modality="numeric", confidence="medium",
    question=("Durch radioaktive Zerfälle in den Zerfallsketten von ²³⁸U, ²³⁵U und ²³²Th werden ⁴He-Kerne produziert. " + UPB +
              "Berechnen Sie die in einem Mineral produzierte ⁴He-Menge (mol) für: Gehalt an ²³⁸U 10⁻⁶ mol; ²³⁸U/²³⁵U = 137.88; Gehalt an ²³²Th "
              "5·10⁻⁷ mol; Kristallisationsalter 10⁹ a. Das Mineral war seit der Kristallisation ein geschlossenes System."),
    reference_answer=(f"Pro Zerfallskette entstehen 8 (²³⁸U), 7 (²³⁵U) bzw. 6 (²³²Th) ⁴He-Kerne. Heutige Mengen N (Gehalt) und t = 10⁹ a: "
                      f"n(⁴He) = 8·N238(e^{{λ238 t}}−1) + 7·N235(e^{{λ235 t}}−1) + 6·N232(e^{{λ232 t}}−1) = {he_f:.3e} mol."),
    rubric=["8/7/6 ⁴He pro ²³⁸U/²³⁵U/²³²Th-Kette", "Zerfallene Menge = N_heute·(e^{λt} − 1) je Nuklid, ²³⁵U = ²³⁸U/137.88", f"n(⁴He) ≈ {he_f:.2e} mol"],
    verification="computed here; assumes 'Gehalt' = present-day amounts",
    notes="Die Aufgabe sagt nur 'Gehalt'; die Parallelaufgabe von Januar 2009 sagt ausdrücklich 'heute'. Annahme: heutige Mengen.")
add(**H08, id="iso09b_uc", part="3c", figures=clip("ov68rh0o", [3]), answer_modality="numeric",
    question=("Durch radioaktive Zerfälle in den Zerfallsketten von ²³⁸U, ²³⁵U und ²³²Th werden ⁴He-Kerne produziert. " + UPB +
              "Berechnen Sie die gesamte in einem Mineral produzierte ⁴He-Menge (mol): Menge ²³⁸U (heute) 10⁻⁶ mol; ²³⁸U/²³⁵U (heute) 137.88; "
              "Menge ²³²Th (heute) 5·10⁻⁶ mol; Kristallisationsalter 10⁹ a; geschlossenes System für U, Th und alle Tochterkerne."),
    reference_answer=(f"n(⁴He) = 8·N238(e^{{λ238 t}}−1) + 7·N235(e^{{λ235 t}}−1) + 6·N232(e^{{λ232 t}}−1) mit den heutigen Mengen N und t = 10⁹ a "
                      f"= {he_h:.3e} mol."),
    rubric=["8/7/6 ⁴He pro ²³⁸U/²³⁵U/²³²Th-Kette", "Zerfallene Menge = N_heute·(e^{λt} − 1) je Nuklid, ²³⁵U = ²³⁸U/137.88", f"n(⁴He) ≈ {he_h:.2e} mol"],
    verification="computed here")
# HS08 mass spectrometry
add(**H08, id="iso09b_1a", part="1a", figures=clip("ov68rh0o", [1]), answer_modality="short_answer",
    question=("Aufgabe 1 (Massenspektrometrie). Ein einfach geladenes Ion (e) mit Geschwindigkeit v erfährt im Magnetfeld B die Lorentzkraft F = e·v×B und "
              "durchläuft eine Kreisbahn (Radius r); es wurde zuvor mit U beschleunigt, v = √(2(e/m)U); m/e = r²B²/(2U). (a) Wie gross ist das "
              "Verhältnis der Geschwindigkeiten v(m2)/v(m1) für einfach geladene Ionen der Massen m1 und m2 nach der Ablenkung um 90°, wenn beide mit "
              "gleicher Spannung U beschleunigt wurden?"),
    reference_answer="v = √(2eU/m) ⇒ v(m2)/v(m1) = √(m1/m2) (der Betrag der Geschwindigkeit ändert sich im Magnetfeld nicht).",
    rubric=["v(m2)/v(m1) = √(m1/m2)"], verification="derived analytically")
add(**H08, id="iso09b_1b", part="1b", figures=clip("ov68rh0o", [1]), answer_modality="short_answer",
    question=("Wie 1a, aber die Ionen der Masse m2 sind doppelt geladen (2e). Wie gross ist das Verhältnis der Bahnradien r(m2, 2e)/r(m1, e) bei "
              "konstantem B und U?"),
    reference_answer="r² = 2U·m/(q·B²) ⇒ r ∝ √(m/q) ⇒ r(m2,2e)/r(m1,e) = √((m2/2)/m1) = √(m2/(2·m1)).",
    rubric=["r ∝ √(m/q)", "r(m2,2e)/r(m1,e) = √(m2/(2m1))"], verification="derived analytically")
add(**H08, id="iso09b_1c", part="1c", figures=clip("ov68rh0o", [1]), answer_modality="short_answer",
    question="Zusätzlich zu 1b gilt der Spezialfall m2 = 2·m1. Wie gross ist r(m2, 2e)/r(m1, e) dann?",
    reference_answer="√(2m1/(2m1)) = 1: beide Ionensorten (m/q gleich) folgen derselben Bahn und lassen sich nicht trennen.",
    rubric=["Verhältnis = 1 (gleiches m/q ⇒ gleicher Radius)"], verification="derived analytically")

# ---------------- Geochemie I/II short exams (2008/2009)
GCx = dict(course="Geochemie", course_slug="geochemieii", language="de", reference_source="derived_verified")
G08 = dict(GCx, exam_name="Prüfung Geochemie, 22.08.2008", exam_id="pd1hbp2y.pdf", term="2008", source_exam_pdf="data/geochemieii/exams/pd1hbp2y.pdf/exam.pdf")
add(**G08, id="gc08_7a", part="7a", figures=clip("pd1hbp2y", [2]), answer_modality="short_answer",
    question=("Aufgabe 7a. Bestimmen Sie nach der Definition D(i, Mineral j) = x(i, im Mineral j)/x(i, in der Schmelze) und den Angaben "
              "D_bulk(Sm) = 0.031, D_bulk(La) = 0.0055, ob La bzw. Sm im Peridotit kompatibel oder inkompatibel ist."),
    reference_answer="Beide sind inkompatibel (D < 1: das Element bevorzugt die Schmelze); La (D = 0.0055) ist stärker inkompatibel als Sm (D = 0.031).",
    rubric=["D < 1 ⇒ La und Sm beide inkompatibel", "La stärker inkompatibel als Sm (kleineres D)"], verification="derived from the definition")
c0La, c0Sm, DLa, DSm = 0.065, 0.41, 0.0055, 0.031
def cm(c0, D, F): return c0 / (D + F * (1 - D))
r1 = cm(c0La, DLa, 0.01) / cm(c0Sm, DSm, 0.01)
r10 = cm(c0La, DLa, 0.10) / cm(c0Sm, DSm, 0.10)
rsrc = c0La / c0Sm
agree("gc08 7b La/Sm @1%", r1, 0.4177, 2e-3)
add(**G08, id="gc08_7b", part="7b", figures=clip("pd1hbp2y", [2]), answer_modality="numeric",
    question=("Aufgabe 7b. Berechnen Sie das Verhältnis La/Sm in einer 1 %igen bzw. 10 %igen partiellen Schmelze im primitiven Mantel, mit "
              "C_Schmelze = c0/(D_bulk + F·(1 − D_bulk)), c0(La) = 0.065, c0(Sm) = 0.41 (in %), D_bulk(La) = 0.0055, D_bulk(Sm) = 0.031, "
              "F = Aufschmelzgrad. Warum ändert sich dieses Verhältnis mit steigendem Aufschmelzgrad?"),
    reference_answer=(f"F = 0.01: C(La) = {cm(c0La,DLa,0.01):.3f} %, C(Sm) = {cm(c0Sm,DSm,0.01):.3f} % ⇒ La/Sm = {r1:.3f}. "
                      f"F = 0.10: C(La) = {cm(c0La,DLa,0.10):.3f} %, C(Sm) = {cm(c0Sm,DSm,0.10):.3f} % ⇒ La/Sm = {r10:.3f}. "
                      f"Quellenwert La/Sm = {rsrc:.3f}. La ist stärker inkompatibel und wird bei kleinem F relativ zu Sm stärker in die Schmelze angereichert; "
                      "mit wachsendem F nähert sich das Verhältnis dem Quellenwert (bei F → 1 identisch)."),
    rubric=[f"La/Sm (1 %) ≈ {r1:.2f}", f"La/Sm (10 %) ≈ {r10:.2f}",
            "Begründung: La stärker inkompatibel ⇒ stärkere Anreicherung bei kleinem F; Verhältnis → Quellenwert für F → 1"],
    verification="computed here", notes="F in % umrechnen: 1 % = 0.01. Toleranz ±2 %.")
G0802 = dict(GCx, exam_name="Prüfung Geochemie, 21.02.2008", exam_id="0wswu25c.pdf", term="2008", source_exam_pdf="data/geochemieii/exams/0wswu25c.pdf/exam.pdf")
Dni, fcore, cbulk = 106.0, 0.3, 1.69
cm_ni = cbulk / (fcore * Dni + (1 - fcore))
agree("gc08 Ni mantle [%]", cm_ni, 0.0520, 2e-3)
add(**G0802, id="gc08b_4", part="4", figures=clip("0wswu25c", [2, 3]), answer_modality="numeric", confidence="medium",
    question=("Aufgabe 4. Berechnen Sie die Konzentration von Ni im Erdmantel. Der Gesamtverteilungskoeffizient D(M/S) von Ni zwischen Metall (Kern) und "
              "Silikat (Mantel) ist 106. Der Erdkern macht 30 % (0.3) der Gesamtmasse der Erde aus. Formulieren Sie eine Massenbilanzgleichung unter der "
              "Annahme, dass Mantel und Kern im chemischen Gleichgewicht sind. Die Ni-Konzentration in der gesamten Erde (bulk Earth) beträgt 1.69 %."),
    reference_answer=(f"Massenbilanz: C_bulk = f_Kern·C_Kern + (1 − f_Kern)·C_Mantel mit C_Kern = D·C_Mantel ⇒ C_Mantel = C_bulk/(f·D + 1 − f) = "
                      f"1.69 %/(0.3·106 + 0.7) = {cm_ni:.4f} % ≈ {cm_ni*1e4:.0f} ppm."),
    rubric=["Massenbilanz C_bulk = f·C_Kern + (1−f)·C_Mantel mit C_Kern = D·C_Mantel", f"C_Mantel ≈ {cm_ni:.3f} % (≈ {cm_ni*1e4:.0f} ppm)"],
    verification="computed here; D read literally as 106 (printed without superscript)",
    notes="Falls D = 10⁶ gemeint war (Hochzahl im Druck verloren), ergäbe sich 5.6·10⁻⁶ % (56 ppb); die Aufgabe druckt '106'. Gewertet wird 0.052 %.")
G09 = dict(GCx, exam_name="Geochemieprüfung FS 2009", exam_id="o4kcl6q0.pdf", term="2009", source_exam_pdf="data/geochemieii/exams/o4kcl6q0.pdf/exam.pdf")
add(**G09, id="gc09_9", part="9", figures=clip("o4kcl6q0", [2]), answer_modality="short_answer", confidence="medium",
    question="Aufgabe 9. Gegeben sind die Elemente Ba, Sr, La, Nb. Geben Sie die Reihenfolge nach abnehmender Kompatibilität in CaMgSi₂O₆ (Diopsid/Klinopyroxen) an.",
    reference_answer=("Sr > La > Nb > Ba. Sr²⁺ und La³⁺ passen von der Ionengrösse am besten auf den Ca-Platz (M2) des Klinopyroxens; Nb⁵⁺ (hohe Ladung, "
                      "HFSE) ist wenig kompatibel, Ba²⁺ ist zu gross und am inkompatibelsten (Grössenordnung der Kristall/Schmelze-Verteilungskoeffizienten: "
                      "Sr ~0.1, La ~0.05, Nb ~0.005, Ba ~0.0004)."),
    rubric=["Reihenfolge Sr > La > Nb > Ba", "Begründung über Ionenradius/Ladung relativ zum Ca-Platz"],
    verification="from published cpx/melt partition coefficients (order of magnitude), not computed",
    notes="Die Reihenfolge der unteren beiden (Nb, Ba) ist am wenigsten gesichert; Sr > La an der Spitze und Ba am Ende sind robust.")

# --------------------------------------------------------------------------
if __name__ == "__main__":
    if ERR:
        raise SystemExit(f"verification mismatches: {ERR}")
    with (HERE / "tasks_derived.jsonl").open("w", encoding="utf-8") as f:
        for t in TASKS:
            f.write(json.dumps({"schema_version": "1.1", **t}, ensure_ascii=False) + "\n")
    by = {}
    for t in TASKS:
        by.setdefault((t["exam_id"], t["reference_source"]), [0, 0.0])
        by[(t["exam_id"], t["reference_source"])][0] += 1
        by[(t["exam_id"], t["reference_source"])][1] += t["max_points"]
    md = ["# Derived-tier answer key\n",
          "Every value is produced by `build_derived_tasks.py`; `official_embedded_solution` items are additionally asserted against the "
          "lecturer's solution. `confidence: medium` marks items that depend on a figure reading or an unstated convention. "
          "Items with `points: unassigned` have 1 point per rubric line as a placeholder.\n",
          "| id | pts | points | source | conf. | answer |", "|---|---|---|---|---|---|"]
    for t in TASKS:
        ans = t["reference_answer"].replace("\n", "<br>").replace("|", "\\|")
        md.append(f"| {t['id']} | {t['max_points']:g} | {t['points_source']} | {t['reference_source'].replace('_', ' ')} | {t['confidence']} | {ans} |")
    (HERE / "answers_derived.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\nWrote {len(TASKS)} items, {sum(t['max_points'] for t in TASKS):g} points → tasks_derived.jsonl")
    for (ex, src), (c, p) in by.items():
        print(f"  {ex:14s} {src:28s} {c:2d} items {p:5.1f} pts")
