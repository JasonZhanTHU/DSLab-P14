#!/usr/bin/env python3
"""Independent numeric cross-check of the official Kartenpraktikum I answers (2014 and 2013).

Inputs are the map-read values from each official solution (fold limbs, fault attitude,
slip trend, Sprunghöhe); this does NOT re-measure the map. It recomputes the quantities that follow from them by pure geometry:
fold axis + interlimb angle (Q9), slip pitch (Q11), principal stresses (Q12) and the
offset components (Q13). Expect agreement to graphical (stereonet/map) precision.
"""
import sys

import numpy as np

D2R, R2D = np.pi / 180, 180 / np.pi


def normal_up(dip_dir, dip):
    """Unit normal of a plane, pointing up (x=E, y=N, z=Up)."""
    dd, d = dip_dir * D2R, dip * D2R
    return np.array([np.sin(d) * np.sin(dd), np.sin(d) * np.cos(dd), np.cos(d)])


def trend_plunge(v):
    """Lower-hemisphere trend/plunge (degrees) of an axis."""
    v = v / np.linalg.norm(v)
    if v[2] > 0:
        v = -v
    return (np.arctan2(v[0], v[1]) * R2D) % 360, np.arcsin(-v[2]) * R2D


EXAMS = {   # limbs, fault dip-dir/dip, slip trend (hanging-wall moves toward), Sprunghöhe [m], official numbers
    "2014": dict(limbs=((85, 22), (265, 22)), fault=(282, 67), slip_trend=355, throw=200,
                 official="axis 175-00, opening 136°, pitch 38°, s 032-43/219-46/125-03, SS/throw/ext 284/200/84 m"),
    "2013": dict(limbs=((90, 14), (270, 27)), fault=(66, 56), slip_trend=0, throw=150,
                 official="axis 000-00, opening 139°, pitch 39°, s 327-47/121-40/222-13, SS/throw/ext 210/150/100 m"),
}


def check(name, c):
    print(f"=== Kartenpraktikum {name}   official: {c['official']}")
    (d1, i1), (d2, i2) = c["limbs"]
    n1, n2 = normal_up(d1, i1), normal_up(d2, i2)
    t, p = trend_plunge(np.cross(n1, n2))
    print(f"fold axis {t:05.1f}/{p:04.1f}; interlimb angle {180 - np.arccos(n1 @ n2) * R2D:5.1f}°")

    dip_dir, dip = c["fault"]
    strike = (dip_dir - 90) % 360
    off = np.radians(((c["slip_trend"] - strike + 180) % 360) - 180)
    plunge = np.degrees(np.arctan(np.tan(dip * D2R) * abs(np.sin(off))))
    pitch = np.degrees(np.arctan(np.tan(plunge * D2R) / np.sin(dip * D2R)))
    print(f"slip plunge {plunge:4.1f}°, pitch from strike {pitch:4.1f}°")

    # principal stresses in the (normal, slip) plane; Coulomb: sigma1 at 30° to the fault
    # (kinematic 45° does NOT match the official numbers). s = hanging-wall slip vector.
    tr = c["slip_trend"] * D2R
    s = np.array([np.cos(plunge * D2R) * np.sin(tr), np.cos(plunge * D2R) * np.cos(tr),
                  -np.sin(plunge * D2R)])
    n = normal_up(dip_dir, dip)
    for theta in (45, 30):
        a = theta * D2R
        s1 = -np.cos(a) * s + np.sin(a) * n
        s3 = np.sin(a) * s + np.cos(a) * n
        (t1, p1), (t2, p2), (t3, p3) = (trend_plunge(v) for v in (s1, np.cross(s1, s3), s3))
        print(f"stress theta={theta}°  s1 {t1:05.1f}-{p1:02.0f}  s2 {t2:05.1f}-{p2:02.0f}  s3 {t3:05.1f}-{p3:02.0f}")

    net = c["throw"] / np.sin(plunge * D2R)
    horiz = net * np.cos(plunge * D2R)
    ang = np.radians(min((c["slip_trend"] - strike) % 180, 180 - (c["slip_trend"] - strike) % 180))
    print(f"offsets: strike-slip {horiz * np.cos(ang):4.0f} m, Sprunghöhe {c['throw']} m, "
          f"Dehnung {horiz * np.sin(ang):3.0f} m\n")


for name in (sys.argv[1:] or EXAMS):
    check(name, EXAMS[name])
