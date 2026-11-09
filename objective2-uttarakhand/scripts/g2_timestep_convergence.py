"""
scripts/g2_timestep_convergence.py
=====================================
G2 (O2, 2026-10-26) — time-step convergence of the Level-1-repaired
simulator. Runs the Phase-7 deployable design per regime (plain tank and PCM)
at dt (default 300/150/75 s; pass e.g. `150,75,37.5 out.csv`) via an in-memory solver override (frozen YAML
untouched) and writes a CSV under results/.

Pass condition (plan WP2 acceptance): Gate-1 residual <= 0.1 % in every run and
annual useful energy changes < 0.05 % each time dt is halved.
"""

import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.design.schema import DesignVector
from src.simulation.run_case import run_case

DTS = tuple(float(x) if "." in x else int(x) for x in sys.argv[1].split(",")) if len(sys.argv) > 1 else (300, 150, 75)
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("results/g2_timestep_convergence.csv")


def main():
    designs = pd.read_csv("data/legacy/g2_g4_illustrative_designs.csv")   # Uttarakhand: no K=4 legacy deployables; mid design + O1 rank-1 PCM
    rows = []
    for _, r in designs.iterrows():
        dv = DesignVector(capsule_diameter_m=r.capsule_diameter_m, n_capsule=int(r.n_capsule),
                          flow_rate_kg_s=r.flow_rate_kg_s, capsule_arrangement=r.arrangement)
        for tag, pcm in (("plain", None), ("pcm", r.pcm_id)):
            prev = None
            for dt in DTS:
                t0 = time.time()
                m = run_case("uttarakhand", int(r.regime_id), pcm, dv, record_hourly=False,
                             system_config_overrides={"solver": {"timestep_s": dt}})["metrics"]
                e = m["useful_energy_kWh"]
                rows.append(dict(regime=int(r.regime_id), case=tag, pcm=pcm or "", dt_s=dt,
                                 useful_energy_kWh=e, solar_fraction=m["solar_fraction"],
                                 collector_kWh=m["collector_energy_kWh"],
                                 residual_pct=m["residual_pct_of_collector"],
                                 n_hours=m["n_hours_simulated"],
                                 change_vs_prev_dt_pct=(100 * (e / prev - 1) if prev else float("nan")),
                                 runtime_s=time.time() - t0))
                prev = e
                print(rows[-1], flush=True)
    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    ok_res = bool((df["residual_pct"] <= 0.1).all())
    ok_conv = bool((df["change_vs_prev_dt_pct"].dropna().abs() < 0.05).all())
    print(f"\nresidual<=0.1% all runs: {ok_res}; |change on halving dt|<0.05% all: {ok_conv}")


if __name__ == "__main__":
    main()
