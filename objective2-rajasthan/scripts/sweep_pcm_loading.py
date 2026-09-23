"""
scripts/sweep_pcm_loading.py
================================
Step 3.5 of the 2026-09-20 fix plan ("Objective2 rajasthan fix plan.md"):
run a real loading sweep (capsule PCM volume fraction ~0.5% to ~20%) on
each of the three regime medoids, using each cluster's own O1 rank-1
shortlisted PCM, so the D1 minimum-PCM-volume-fraction floor (used by
src/design/geometry.py's below_min_pcm_fraction gate) comes from measured
useful_energy_kWh gain over the plain-tank baseline, not a guess.

Replaces the "ad hoc probe" numbers quoted in the fix plan (gains
0.075-0.13% at low loading, losses -0.03 to -0.78% at ~19.8% loading) with
a reproducible script and its own output file.

Sweeps (diameter_m, n_capsule) pairs at a fixed arrangement (staggered --
arrangement is not the variable under test here) across the full design
bounds, computes the realized pcm_volume_fraction from the geometry engine
itself (not assumed), and reports useful_energy_kWh gain vs the regime's
plain-tank baseline for every valid, feasible point.

Output: results/phase3_5_pcm_loading_sweep.csv
"""

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import RESULTS_DIR
from src.design.schema import DesignVector
from src.design.constraints import check_design
from src.io_utils import load_state_config, load_system_config, load_design_bounds, write_manifest_sidecar
from src.simulation.run_case import run_case

ARRANGEMENT = "staggered"   # arrangement is not the variable under test here (see docstring)
DIAMETERS_M = [0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08]
COUNTS = [8, 14, 20, 26, 32, 37]


def sweep_state(state: str = "rajasthan"):
    cfg = load_state_config(state)
    system_config = load_system_config()
    bounds = load_design_bounds()

    rows = []
    for regime in cfg["regimes"]:
        cid = regime["cluster_id"]
        rank1_pcm = regime["pcm_shortlist"][0]
        print(f"\nRegime {cid} — rank-1 PCM: {rank1_pcm!r}")

        # plain-tank baseline for this regime (n_capsule irrelevant when pcm_id=None)
        baseline_design = DesignVector(0.05, 20, 0.030, capsule_arrangement=ARRANGEMENT)
        t0 = time.time()
        base_out = run_case(state, cid, None, baseline_design, system_config, bounds, record_hourly=False)
        baseline_kWh = base_out["metrics"]["useful_energy_kWh"]
        print(f"  baseline (plain tank): useful_energy_kWh={baseline_kWh:.3f}  ({time.time()-t0:.1f}s)")

        for d in DIAMETERS_M:
            for n in COUNTS:
                design = DesignVector(d, n, 0.030, capsule_arrangement=ARRANGEMENT)
                geom = check_design(design, system_config, bounds)
                if not geom["valid"]:
                    rows.append({"cluster_id": cid, "pcm_id": rank1_pcm, "capsule_diameter_m": d,
                                 "n_capsule": n, "valid": False, "reason": geom["reason"],
                                 "pcm_volume_fraction": None, "useful_energy_kWh": None,
                                 "gain_over_plain_tank_pct": None})
                    continue

                out = run_case(state, cid, rank1_pcm, design, system_config, bounds, record_hourly=False)
                if not out["valid"]:
                    rows.append({"cluster_id": cid, "pcm_id": rank1_pcm, "capsule_diameter_m": d,
                                 "n_capsule": n, "valid": False, "reason": out["reason"],
                                 "pcm_volume_fraction": geom["pcm_volume_fraction"],
                                 "useful_energy_kWh": None, "gain_over_plain_tank_pct": None})
                    continue

                useful_kWh = out["metrics"]["useful_energy_kWh"]
                gain_pct = (useful_kWh - baseline_kWh) / baseline_kWh * 100.0 if baseline_kWh else float("nan")
                rows.append({"cluster_id": cid, "pcm_id": rank1_pcm, "capsule_diameter_m": d,
                             "n_capsule": n, "valid": True, "reason": None,
                             "pcm_volume_fraction": geom["pcm_volume_fraction"],
                             "useful_energy_kWh": useful_kWh, "gain_over_plain_tank_pct": gain_pct})
                print(f"    d={d:.2f} n={n:2d}  frac={geom['pcm_volume_fraction']*100:5.2f}%  "
                      f"useful={useful_kWh:8.3f} kWh  gain={gain_pct:+.4f}%")

    df = pd.DataFrame(rows)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / "phase3_5_pcm_loading_sweep.csv"
    df.to_csv(out_path, index=False)
    print(f"\nSaved: {out_path}")
    write_manifest_sidecar(out_path, state, extra={"diameters_m": DIAMETERS_M, "counts": COUNTS,
                                                     "arrangement": ARRANGEMENT})

    valid = df[df["valid"]]
    if len(valid):
        print("\nGain vs plain tank, binned by pcm_volume_fraction decile:")
        binned = valid.copy()
        binned["frac_bin"] = pd.cut(binned["pcm_volume_fraction"], bins=10)
        summary = binned.groupby("frac_bin", observed=True)["gain_over_plain_tank_pct"].agg(["mean", "min", "max", "count"])
        print(summary.to_string())
    return df


if __name__ == "__main__":
    state = sys.argv[1] if len(sys.argv) > 1 else "rajasthan"
    sweep_state(state)
