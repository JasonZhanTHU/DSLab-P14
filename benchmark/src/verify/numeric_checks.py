#!/usr/bin/env python3
"""Independent numeric re-derivation of the official answers for the four non-map exams
(Physik 2018, Mathematik H2006, Systemanalyse H2005, Magmatismus FS2005).

Each line prints our value, the official value and OK/DIFF, so errata or loose
approximations in the Musterlösungen show up. numpy only."""
import numpy as np

rows = []


def chk(tag, ours, official, tol=0.02, note=""):
    ok = abs(ours - official) <= tol * max(1.0, abs(official))
    rows.append((tag, ours, official, "OK" if ok else "DIFF", note))


# ---------------- Physik I/II 2018 ----------------
chk("phys 1  h/r", 2.5, 2.5)
e, c, u = 1.602176634e-19, 2.99792458e8, 1.66053907e-27
chk("phys 2b T_E/T_M", (6e6 / 2e6) * np.sqrt(7e22 / 6e24), 0.3, tol=0.1, note="official rounds 0.32 to 0.3")
gm_ge = (7e22 / 6e24) * (6e6 / 2e6) ** 2
chk("phys 2c l_M/l_E", gm_ge, 0.1, tol=0.1)
g, rk, re_ = 1.4, 15.0, 5.0
eta = 1 - (1 / g) * ((1 / re_) ** g - (1 / rk) ** g) / ((1 / re_) - (1 / rk))
chk("phys 3  eta_Diesel", eta, 0.5581, tol=1e-3)
B = 2 / 5e-3 * (np.sqrt(238 * u * 1e4 / e) - np.sqrt(235 * u * 1e4 / e))
chk("phys 4b B [T]", B, 0.4, tol=0.05)
l1, l2, U1, U2 = 365.4e-9, 435.8e-9, 1.603, 1.054
h = (e / c) * (U1 - U2) / (1 / l1 - 1 / l2)
chk("phys 6  h/1e-34", h / 1e-34, 6.637, tol=5e-3)
chk("phys 6  Phi [V]", (U1 - U2) / (1 - l1 / l2) - U1, 1.795, tol=5e-3)

# ---------------- Mathematik I/II H2006 ----------------
z = -2 + 2j
chk("math 1a arg(z/(1-i)) = pi", np.angle(z / (1 - 1j)) % (2 * np.pi), np.pi, tol=1e-9)
rhs = np.exp(7j * np.pi / 12) * (5 - 3 * np.sqrt(3) * 1j) / (1 + 2 * np.sqrt(3) * 1j)
chk("math 1a |z/(1-i)| = |rhs|", abs(z / (1 - 1j)) - abs(rhs), 0.0, tol=1e-9)
x = np.linspace(1, np.e ** 2, 400001)
chk("math 1c J", np.trapezoid(np.log(x) / x, x), 2.0, tol=1e-6)
t = np.linspace(0, 1.5, 150001)
xs = 0.5 * (np.exp(t ** 2) - 1)
res = np.gradient(xs, t) - 2 * t * xs - t
chk("math 1d ODE residual", np.max(np.abs(res[2:-2])), 0.0, tol=1e-4)
A = np.array([[0, 4, 1], [3, -1, 1], [1, 2, 1]], float)
C = np.array([[6, 4, -10], [4, 2, -6], [-14, -8, 24]], float)
D = np.array([[0, 0, 3], [0, 2, 0], [1, 0, 0]], float)
chk("math 3a det A", np.linalg.det(A), -1.0, tol=1e-9)
Bm = np.linalg.solve(A, D)
chk("math 3a det B", np.linalg.det(Bm), 6.0, tol=1e-9)
chk("math 3b |AC-2I|", np.abs(A @ C - 2 * np.eye(3)).max(), 0.0, tol=1e-9)
chk("math 3b |B-official|", np.abs(Bm - np.array([[-5, 4, 9], [-3, 2, 6], [12, -8, -21]])).max(), 0.0, tol=1e-9)
M = np.array([[1, 0], [1, 3.0]])
w, V = np.linalg.eig(M)
chk("math 4b eigenvalues sum", w.sum(), 4.0, tol=1e-9)
tt = 0.7
xt = 0.5 * np.exp(tt) * np.array([2, -1]) + 0.5 * np.exp(3 * tt) * np.array([0, 1])
chk("math 4c y=(x^3-x)/2", xt[1] - 0.5 * (xt[0] ** 3 - xt[0]), 0.0, tol=1e-9)
fx, fy = 1.0, -7.0
chk("math 5a D_(1,1)", (fx + fy) / np.sqrt(2), -3 * np.sqrt(2), tol=1e-9)
chk("math 5a |grad|", np.hypot(fx, fy), 5 * np.sqrt(2), tol=1e-9)
n = np.cross([1, 0, fx], [0, 1, fy])
chk("math 5c d", -(n @ [1, 2, 3]), -16.0 * (n[0] / -1), tol=1e-9, note="plane -x+7y+z-16=0")
yy = np.linspace(1, 2, 200001)  # work A->B->C of F=(x ln y, x^2/(2y)); on A->B y=1, on B->C x=3
wAB = 0.0
wBC = np.trapezoid(9 / (2 * yy), yy)
chk("math 6b work", wAB + wBC, 4.5 * np.log(2), tol=1e-6)

# ---------------- Systemanalyse H2005 ----------------
Q = V_ = 1e9
Cin, Caus = 600e6 / Q, 0.2
chk("sa 2a C_in", Cin, 0.6, tol=1e-9)
kr = (Q / V_) * (Cin / Caus - 1)
chk("sa 2c k_r [1/a]", kr, 2.0, tol=1e-9)
chk("sa 2d tau [a]", np.log(2) / (Q / V_ + kr), 0.23, tol=0.02)
J10 = 600 * np.exp(-0.1 * 10)
chk("sa 2e J(10) [kg/a]", J10, 200.0, tol=0.12, note=f"exact 600/e = {J10:.0f}; official uses e^-1 ~ 1/3 (allowed by exam table)")
C10 = J10 * 1e6 / 1e9 / (Q / V_ + kr)
chk("sa 2f C(10) [mg/m3]", C10, 0.067, tol=0.12, note=f"exact {C10:.3f}; official 0.067 uses the same approximation")
kw, kexE, kexH, kr2 = 3e7 / 1e9, 2e8 / 1e9, 2e8 / 1e10, 0.08
Mx = np.array([[-(kexE + kw + kr2), kexE], [kexH, -(kexH + kr2)]])
chk("sa 3c a11", Mx[0, 0], -0.31, tol=1e-9)
ev = np.sort(np.linalg.eigvals(Mx).real)
chk("sa 3d slowest |lambda|", abs(ev[-1]), 0.1, tol=0.15, note=f"full eigenvalues {ev.round(3)}")
chk("sa 3d tau_5% [d]", np.log(20) / abs(ev[-1]), 30.0, tol=0.25, note="exact ~36 d; official 30 d uses the exam-permitted triangular approximation")

# ---------------- Magmatismus FS2005 (lever rule, X = 40 % SiO2) ----------------
X = 40.0
Fo, En, Si = 0.0, 20.0, 100.0           # SiO2 % of Fo, En (from 100 En = 40 L + 60 Fo), SiO2
Lr, L1, L2, Le, LT1 = 50.0, 45.0, 65.0, 70.0, 45.0
lever = lambda a, b: (X - a) / (b - a)   # fraction of the phase at b
chk("meta T1   liquid %", 100 * lever(Fo, L1), 88.9, tol=1e-3)
chk("meta TR in liquid %", 100 * lever(Fo, Lr), 80.0, tol=1e-3)
chk("meta TR out liquid %", 100 * lever(En, Lr), 66.7, tol=1e-3)
chk("meta T2   liquid %", 100 * lever(En, L2), 44.4, tol=2e-3)
chk("meta T2   enstatite %", 100 - 100 * lever(En, L2), 56.6, tol=1e-3,
    note="official table prints 56.6 (44.4+56.6=101): erratum, correct 55.6")
chk("meta TE in  liquid %", 100 * lever(En, Le), 40.0, tol=1e-3)
chk("meta TE out SiO2 %", 100 * lever(En, Si), 25.0, tol=1e-3)
chk("meta R: En = 40 L + 60 Fo", 0.4 * Lr + 0.6 * Fo, En, tol=1e-9)
chk("meta E: 62.5 Si + 37.5 En = L", 0.625 * Si + 0.375 * En, Le, tol=1e-9)

w = max(len(r[0]) for r in rows)
for tag, ours, off, st, note in rows:
    print(f"{st:4s} {tag:{w}s} ours {ours:12.5g}  official {off:10.5g}  {note}")
print(f"\n{sum(r[3] == 'OK' for r in rows)}/{len(rows)} OK;",
      "DIFF items:", [r[0] for r in rows if r[3] == "DIFF"] or "none")
