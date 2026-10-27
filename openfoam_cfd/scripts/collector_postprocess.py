#!/usr/bin/env python3
"""
collector_postprocess.py -- useful gain, efficiency and F_R of a collector_make_case.py run.

  python collector_postprocess.py ../cases_collector/test_T30

Reads the latest time's water/T and water/phi boundary values (outlet), forms the flow-weighted
outlet temperature, and reports (for the FULL riser = 2 x the half-strip in the domain):
  Q_u [W], T_out [C], eta = Q_u/(G W L),  F_R_cfd = Q_u / [A (S - U_L (T_in - T_amb))]
next to the Duffie-Beckman estimate stored in case_meta.json.
"""
import json
import os
import re
import sys


def latest_time(case):
    ts = []
    for d in os.listdir(case):
        try:
            ts.append((float(d), d))
        except ValueError:
            pass
    return max(ts)[1]


def patch_values(path, patch):
    txt = open(path).read()
    i = txt.index(patch + "\n") if (patch + "\n") in txt else txt.index(patch)
    seg = txt[i:]
    j = seg.index("value")
    seg = seg[j:]
    if "nonuniform" not in seg.split(";")[0]:
        return [float(seg.split("uniform")[1].split(";")[0])], True
    m = re.search(r"nonuniform\s+List<scalar>\s*\n?\s*(\d+)\s*\n?\s*\(", seg)
    n = int(m.group(1))
    body = seg[m.end():]
    vals = [float(x) for x in body.split(")")[0].split()][:n]
    return vals, False


def main(case):
    meta = json.load(open(os.path.join(case, "case_meta.json")))
    t = latest_time(case)
    T, _ = patch_values(os.path.join(case, t, "water", "T"), "outlet")
    phi, _ = patch_values(os.path.join(case, t, "water", "phi"), "outlet")
    cp = 4186.0
    mdot_dom = -sum(phi)                          # outlet flux is positive out of the domain in OpenFOAM
    mdot_dom = abs(mdot_dom)
    Tout = sum(abs(p) * x for p, x in zip(phi, T)) / sum(abs(p) for p in phi)
    Tin = meta["T_in_C"] + 273.15
    Q_half = abs(sum(phi)) * cp * (Tout - Tin)
    Q = 2.0 * Q_half
    A = meta["W"] * meta["L"]
    G, S, UL = meta["G"], meta["S"], meta["U_L"]
    Tamb = meta["T_amb_C"] + 273.15
    res = dict(time=float(t), mdot_domain=mdot_dom, mdot_riser_expected=meta["mdot_riser"],
               T_out_C=Tout - 273.15, Q_u_W=Q, eta=Q / (A * G),
               F_R_cfd=Q / (A * (S - UL * (Tin - Tamb))),
               analytic=meta["analytic"])
    json.dump(res, open(os.path.join(case, "collector_metrics.json"), "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
