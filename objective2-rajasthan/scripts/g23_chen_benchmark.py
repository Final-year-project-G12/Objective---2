"""
scripts/g23_chen_benchmark.py
================================
Literature trend check against Chen et al. 2025 (Taguchi + GRA for a PCM-nanofluid flat-plate solar water heater; Sources/pdfs "Using the Taguchi method and
grey relational analysis.pdf", Table 10 and section 3 / Table 2). This is a TREND comparison, not a validation: the paper uses TRNSYS, a different collector, PCM tubes and
RT35HC; this simulator uses capsule spheres in a 10-node tank. What is taken from the paper and what is assumed:

  from the paper   tank volume 0.04 m3 (Table 2); daily demand set at a minimum of 30 L; collector area 0.1616 m2 (Table 3 air-layer area);
                   retention = hours after sunset until the tank water falls below 30 C with no sun; PCM volume levels 10 / 15 / 20 % of the tank (section 3);
                   Table 10 retention: without PCM 17.13 h simulated / 16.59 h experimental, with PCM 18.33 h simulated / 17.66 h experimental
                   (a gain of +1.20 h = +7.0 % simulated, +1.07 h = +6.4 % experimental)
  assumed          RT35HC data (latent heat, density, conductivity) are NOT in the repository. The PCM here is the database record with the lowest melt temperature
                   (RT42) with only Tm_C shifted to 35 C (a Tm-shifted analogue, in the same way as the synthetic-Tm control in g11); sphere inner radius 20 mm,
                   staggered, flow 0.020 kg/s; the demand profile of the project scaled to 30 L/day; weather of the regime medoid, explore years 2016-2020.

The retention metric is tau_hold at a 30 C threshold (delivery.target_temp_C = 30 for this script only, an in-memory override), restarted from the 18:00 state every 15th day,
censored at 72 h. The output prints plain vs PCM tau_hold and the gain in hours and percent next to Chen's numbers. The agreement to look for is the SIGN and the order of
magnitude of the gain, not the absolute hours (different collector, load and PCM).

Usage: python scripts/g23_chen_benchmark.py <cluster_id> [pcm_name=RT42]   ->  results/g23_chen_benchmark_r<c>.csv
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.design.space import count_for_fraction, geometry_bounds, load_space, wall_m, capsule_outer_volume_m3
from src.design.schema import DesignVector
from src.optimize.evaluate import _weather
from src.simulation.run_case import run_case
from src.weather import roles

OUT = Path("results")
SP = load_space()
CHEN = {"plain_sim_h": 17.13, "plain_exp_h": 16.59, "pcm_sim_h": 18.33, "pcm_exp_h": 17.66}
OVER = {"tank": {"volume_L": 40.0}, "collector": {"area_m2": 0.1616}, "delivery": {"target_temp_C": 30.0}}
R_IN, FLOW, ARR = 0.020, 0.020, "staggered"


def n_for(fraction, vol_l=40.0):
    return int(round(fraction * (vol_l / 1000.0) / capsule_outer_volume_m3(R_IN)))


def run(cid, pcm, n, y, pcm_over):
    dv = DesignVector(capsule_diameter_m=2.0 * (R_IN + wall_m()), n_capsule=int(n), flow_rate_kg_s=FLOW, capsule_arrangement=ARR)
    r = run_case("rajasthan", cid, pcm, dv, design_bounds=geometry_bounds(), weather=_weather(cid, y, "explore"), tank_model=SP["model"]["tank_model"],
                 n_nodes=SP["model"]["n_nodes"], stack_anchor=SP["model"]["stack_anchor"], compute_tes_metrics=True, night_day_stride=15,
                 system_config_overrides=OVER, volume_multiplier=0.1, pcm_record_overrides=pcm_over)
    return r


def main(cid, pcm="RT42"):
    rows = []
    for frac in (0.10, 0.15, 0.20):
        n = n_for(frac)
        pl, pc, cen_pl, cen_pc = [], [], [], []
        for y in roles.years_for("explore"):
            a = run(cid, None, n, y, None)
            b = run(cid, pcm, n, y, {"Tm_C": 35.0})
            if not (a["valid"] and b["valid"]):
                print("invalid", frac, a.get("reason"), b.get("reason"))
                break
            pl.append(a["tes"]["tau_hold_mean_h"]); pc.append(b["tes"]["tau_hold_mean_h"])
            cen_pl.append(a["tes"]["tau_hold_censored_frac"]); cen_pc.append(b["tes"]["tau_hold_censored_frac"])
        if not pl:
            continue
        p0, p1 = float(np.mean(pl)), float(np.mean(pc))
        rows.append({"regime": cid, "pcm_analogue": f"{pcm} with Tm_C=35", "pcm_fraction": frac, "N": n, "tau_hold30_plain_h": p0, "tau_hold30_pcm_h": p1,
                     "gain_h": p1 - p0, "gain_pct": 100.0 * (p1 - p0) / p0 if p0 > 0 else np.nan,
                     "censored_frac_plain": float(np.mean(cen_pl)), "censored_frac_pcm": float(np.mean(cen_pc)),
                     "chen_gain_sim_h": CHEN["pcm_sim_h"] - CHEN["plain_sim_h"], "chen_gain_exp_h": CHEN["pcm_exp_h"] - CHEN["plain_exp_h"],
                     "chen_gain_sim_pct": 100.0 * (CHEN["pcm_sim_h"] / CHEN["plain_sim_h"] - 1), "chen_gain_exp_pct": 100.0 * (CHEN["pcm_exp_h"] / CHEN["plain_exp_h"] - 1)})
        print(f"fraction {frac:.2f}: plain {p0:.2f} h, PCM {p1:.2f} h, gain {p1 - p0:+.2f} h ({rows[-1]['gain_pct']:+.1f} %); "
              f"Chen: +{rows[-1]['chen_gain_sim_h']:.2f} h sim ({rows[-1]['chen_gain_sim_pct']:.1f} %), +{rows[-1]['chen_gain_exp_h']:.2f} h exp ({rows[-1]['chen_gain_exp_pct']:.1f} %)", flush=True)
        pd.DataFrame(rows).to_csv(OUT / f"g23_chen_benchmark_r{cid}.csv", index=False)


if __name__ == "__main__":
    main(int(sys.argv[1]), *(sys.argv[2:3]))
