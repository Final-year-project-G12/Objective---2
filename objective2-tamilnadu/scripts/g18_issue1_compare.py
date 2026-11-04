"""
scripts/g18_issue1_compare.py
================================
Issue 1 (progress log sections 18/24): the box-vertex step added during G9 was not pre-declared. This script reports G9 for all nine (regime, O1 PCM)
pairs under three states, using only saved files:
  base    the original G9 run (5 active-learning rounds, no vertices)                      results/g9_*_<pair>.csv
  novert  base + 3 more rounds WITHOUT the vertex step (G9_WARM=1 G9_MAX_ROUNDS=8; a first attempt without G9_MAX_ROUNDS added no rounds and is kept in
          results/issue1_novert/_invalid_run1_rounds_not_extended/)
                                                                                           results/issue1_novert/g9_*_<pair>_ext.csv
  vert    base + the 24 box vertices + 3 more rounds (G9_WARM=1 G9_VERTICES=1)           results/g9_*_<pair>_ext2.csv
Regime 0 PCM 1: its `novert` state is the historical 8-round no-vertex run (g9_*_r0_p1_ext.csv); its `vert` run continued from that state for 3 more rounds (11 rounds in total), unlike the other pairs, whose `vert` run continued from base (8 rounds in total).
Per pair and state: number of simulated points and feasible share, hypervolume of the simulated non-dominated set on a common reference point, and (for the rank-1
pairs, which have a dense 540-design grid) the additive-epsilon gap to the grid front against the WP6 band (the G9 criterion, `g9_assess.py`).
Writes results/g18_issue1_with_without.csv.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.optimize.nsga2 import additive_epsilon, hypervolume, non_dominated_mask

OUT = Path("results")
NV = OUT / "issue1_novert"
OBJ = ["g_window", "g_annual", "d_overheat"]


def F_of(df):
    return np.column_stack([-df["g_window"], -df["g_annual"], df["d_overheat"]])


def path(state, tag):
    if state == "novert" and tag == "r0_p1":      # r0_p1 already has an 8-round no-vertex run from the original G9 follow-up (its vert run continued from it)
        return OUT / "g9_points_r0_p1_ext.csv"
    return {"base": OUT / f"g9_points_{tag}.csv", "novert": NV / f"g9_points_{tag}_ext.csv", "vert": OUT / f"g9_points_{tag}_ext2.csv"}[state]


def main():
    band = pd.read_csv(OUT / "wp6_band.csv")
    bv = band[band.scope == "all"].set_index("objective").band.reindex(OBJ).to_numpy()
    rows = []
    for r in range(3):
        for k in (1, 2, 3):
            tag = f"r{r}_p{k}"
            states = {s: pd.read_csv(path(s, tag)) for s in ("base", "novert", "vert") if path(s, tag).exists()}
            ok = {s: d[d.feasible == True] for s, d in states.items()}  # noqa: E712
            allF = np.vstack([F_of(d) for d in ok.values()])
            ref = allF.max(axis=0) + 0.05 * (allF.max(axis=0) - allF.min(axis=0))
            grid = None
            gp = OUT / f"g9_s6_grid_{tag}.csv"
            if gp.exists():
                g = pd.read_csv(gp)
                g = g[(g.status == "ok") & (g.feasible == True)]  # noqa: E712
                Fg = F_of(g)
                grid = Fg[non_dominated_mask(Fg)]
                ref = np.maximum(ref, Fg.max(axis=0) + 0.05 * (Fg.max(axis=0) - Fg.min(axis=0)))
            for s, d in ok.items():
                F = F_of(d)
                Fn = F[non_dominated_mask(F)]
                row = {"pair": tag, "state": s, "n_points": len(states[s]), "n_feasible": len(d), "n_front": len(Fn), "hv_common_ref": hypervolume(Fn, ref)}
                if grid is not None:
                    eps, worst = additive_epsilon(Fn, grid)
                    row.update({"eps_g_window": worst[0], "eps_g_annual": worst[1], "eps_d_overheat": worst[2],
                                "within_band": bool(np.all(worst <= bv))})
                rows.append(row)
    t = pd.DataFrame(rows)
    t["hv_rel_to_best_state"] = t.groupby("pair").hv_common_ref.transform(lambda x: x / x.max())
    t.to_csv(OUT / "g18_issue1_with_without.csv", index=False)
    print(t.round(3).to_string(index=False))
    print("band (all regimes):", dict(zip(OBJ, bv.round(2))))


if __name__ == "__main__":
    main()
