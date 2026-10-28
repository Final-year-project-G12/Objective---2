"""
scripts/g3_metrics_report.py
===============================
G3 (O2, 2026-10-26) — evidence run for the WP1 metrics. Computes the full
metric set (in-run + night hold/serve scenarios on EVERY day) for the Phase-7
deployable design per regime, plain tank and PCM, at the production dt = 150 s.

ILLUSTRATIVE ONLY: these designs and PCMs are the legacy (retargeted
shortlist) ones; they are used here purely to exercise and report the metrics.
They are not the O1-top-3 designs (G6) and not optimised under the new metrics.

Writes
  results/g3_metrics_report.csv           one row per (regime, case)
  results/g3_night_daily_r{R}_{case}.csv  per-day hold/serve table
"""

import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.design.schema import DesignVector
from src.simulation.run_case import run_case

OUT = Path("results")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    designs = pd.read_csv("data/legacy/g2_g4_illustrative_designs.csv")   # Uttarakhand: no K=4 legacy deployables; mid design + O1 rank-1 PCM
    rows = []
    for _, r in designs.iterrows():
        dv = DesignVector(capsule_diameter_m=r.capsule_diameter_m, n_capsule=int(r.n_capsule),
                          flow_rate_kg_s=r.flow_rate_kg_s, capsule_arrangement=r.arrangement)
        for tag, pcm in (("plain", None), ("pcm", r.pcm_id)):
            t0 = time.time()
            out = run_case("uttarakhand", int(r.regime_id), pcm, dv, compute_tes_metrics=True, night_day_stride=1)
            m, tes = out["metrics"], out["tes"]
            rows.append({"regime": int(r.regime_id), "case": tag, "pcm": pcm or "",
                         "useful_energy_kWh": m["useful_energy_kWh"], "solar_fraction": m["solar_fraction"],
                         "gate1_residual_pct": m["residual_pct_of_collector"], **tes,
                         "runtime_s": time.time() - t0})
            out["night_daily"].to_csv(OUT / f"g3_night_daily_r{int(r.regime_id)}_{tag}.csv", index=False)
            print(tag, int(r.regime_id), f"{rows[-1]['runtime_s']:.0f}s", flush=True)
    pd.DataFrame(rows).to_csv(OUT / "g3_metrics_report.csv", index=False)


if __name__ == "__main__":
    main()
