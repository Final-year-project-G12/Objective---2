"""
scripts/c15_l7_grid_band.py   (level L7, steps O2-11 and O2-12)
==================================================================
For ONE (regime, O1 PCM) pair, using the best design found by the L6 search (highest ROBUST mean paired gain among feasible designs):
  A. DENSE GRID (162 points: 6 radii 10-40 mm x 9 fractions 2-40 % x 3 arrangements, centre anchor, cheap fidelity): is any grid point better than
     the search's best at the same anchor/fidelity? epsilon = grid best - search best (kWh). The box boundary contacts are listed.
  B. REPEATABILITY BAND of the paired gain of that design. CORE band (used by the funnel) = root-sum-square of
       years (sd of the gain over explore years 2016-2019) | timestep (150 vs 37.5 s) | nodes (10 vs 20) | PCM properties (latent +/-10 %, Tm +/-1.5 K,
       conductivity +/-20 %) | stack anchor (max-min over bottom/centre/top).
     FULL band additionally includes mains +/-3 C and demand +/-20 %. Those two are SCENARIO shifts (they move the expected gain monotonically, they are
     not measurement noise), are reported as separate sensitivities, and the legacy 26-30 kWh band is only consistent with the core definition.
     Decision taken before any real select/test run and DISCLOSED: it followed a smoke test in which demand +/-20 % alone moved the gain by ~99 kWh.
     Every component is a paired difference (PCM minus water-only twin under the same perturbation). Components and the RSS band are reported.
Usage: python scripts/c15_l7_grid_band.py <cluster_id> <pcm_rank>   -> results/c15_l7_{grid,band}_r<c>_p<k>.csv
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.design.space import geometry_bounds, to_design                                  # noqa: E402
from src.io_utils import get_pcm_properties, get_regime                                  # noqa: E402
from src.optimize.evaluate import evaluate_design                                        # noqa: E402
from src.simulation.run_case import run_case                                             # noqa: E402
from src.weather import roles                                                            # noqa: E402
from src.weather.inventory import CURRENT_MEDOIDS                                        # noqa: E402
from config import STATE                                                                 # noqa: E402

ARRS = ("single-layer", "staggered", "radial")
GRID_R, GRID_F = 6, 9             # 6 x 9 x 3 = 162 grid points (smoke tests lower these)


def paired_gain(cid, pcm, dv, w, dt=150.0, nodes=10, anchor="center", ovr=None, vol=1.0, mains=None):
    kw = dict(design_bounds=geometry_bounds(), weather=w, tank_model="multinode", n_nodes=nodes, compute_tes_metrics=True, night_day_stride=0,
              volume_multiplier=vol, mains_temp_override_C=mains, system_config_overrides={"solver": {"timestep_s": dt}})
    a = run_case(STATE, cid, pcm, dv, stack_anchor=anchor, pcm_record_overrides=ovr, **kw)
    b = run_case(STATE, cid, None, dv, **kw)
    return a["tes"]["E_del45_window_kWh"] - b["tes"]["E_del45_window_kWh"]


def main(cid, rank):
    t0 = time.time()
    pcm = get_regime(STATE, cid)["pcm_shortlist"][rank - 1]
    tag = f"r{cid}_p{rank}"
    pts = pd.read_csv(f"results/c14_l6_points_{tag}.csv")
    pts = pts[(pts.feasible == True)]                                                    # noqa: E712
    best = pts.sort_values("g_window_mean", ascending=False).iloc[0]
    r, f, arr = float(best.R_in_m), float(best.fraction), best.arrangement
    # ---- A. dense grid (centre anchor, cheap fidelity, 2017)
    rows = []
    for R in np.linspace(0.010, 0.040, GRID_R):
        for F in np.linspace(0.02, 0.40, GRID_F):
            for A in ARRS:
                e = evaluate_design(cid, pcm, float(R), float(F), 0.030, A, years=[2017], dt_s=150.0, stack_anchor="center")
                rows.append({"R_in_m": R, "fraction_req": F, "arrangement": A, "valid": e["valid"], "g_window_center": e.get("g_window", np.nan),
                             "feasible": e.get("feasible", False)})
    grid = pd.DataFrame(rows)
    gv = grid[(grid.valid) & (grid.feasible == True)]                                    # noqa: E712
    gbest = gv.sort_values("g_window_center", ascending=False).iloc[0]
    sbest_center = float(best.g_window_center)
    grid["search_best_center"] = sbest_center
    grid["epsilon_grid_minus_search"] = float(gbest.g_window_center) - sbest_center
    grid.to_csv(f"results/c15_l7_grid_{tag}.csv", index=False)
    # ---- B. repeatability band of the search's best design
    dv = to_design(r, f, 0.030, arr)
    rec = get_pcm_properties(STATE, pcm)
    w17 = roles.load_point_year(STATE, cid, CURRENT_MEDOIDS[cid], 2017, "explore")
    mains0 = get_regime(STATE, cid)["T_mains_est_C"]
    base = paired_gain(cid, pcm, dv, w17)
    comp = {}
    yrs = [paired_gain(cid, pcm, dv, roles.load_point_year(STATE, cid, CURRENT_MEDOIDS[cid], y, "explore")) for y in roles.years_for("explore")]
    comp["years_sd"] = float(np.std(yrs, ddof=1))
    comp["timestep"] = abs(paired_gain(cid, pcm, dv, w17, dt=37.5) - base)
    comp["nodes"] = abs(paired_gain(cid, pcm, dv, w17, nodes=20) - base)
    props = [{"latent_heat_kJ_kg": rec["latent_heat_kJ_kg"] * 0.9}, {"latent_heat_kJ_kg": rec["latent_heat_kJ_kg"] * 1.1},
             {"Tm_C": rec["Tm_C"] - 1.5}, {"Tm_C": rec["Tm_C"] + 1.5},
             {"TC_W_mK": rec["TC_W_mK"] * 0.8}, {"TC_W_mK": rec["TC_W_mK"] * 1.2}]
    comp["pcm_properties"] = max(abs(paired_gain(cid, pcm, dv, w17, ovr=o) - base) for o in props)
    comp["mains"] = max(abs(paired_gain(cid, pcm, dv, w17, mains=mains0 + d) - base) for d in (-3.0, 3.0))
    comp["demand"] = max(abs(paired_gain(cid, pcm, dv, w17, vol=v) - base) for v in (0.8, 1.2))
    anc = [paired_gain(cid, pcm, dv, w17, anchor=a) for a in ("bottom", "center", "top")]
    comp["stack_anchor"] = float(max(anc) - min(anc))
    core = ("years_sd", "timestep", "nodes", "pcm_properties", "stack_anchor")      # measurement repeatability of the paired gain
    band = float(np.sqrt(sum(comp[k] ** 2 for k in core)))                           # funnel band (core)
    band_full = float(np.sqrt(sum(v ** 2 for v in comp.values())))                   # + mains and demand scenario shifts (reported, not used by the funnel)
    out = {"pair": tag, "regime": cid, "pcm": pcm, "R_in_m": r, "fraction": f, "arrangement": arr, "N": int(best.N),
           "search_best_g_window_mean": float(best.g_window_mean), "search_best_g_window_worst": float(best.g_window_worst),
           "reference_gain_center_2017": base, "band_rss_kWh": band, "band_full_rss_kWh": band_full, **{f"band_{k}": v for k, v in comp.items()},
           "grid_best_g_window_center": float(gbest.g_window_center), "grid_best_R_in_m": float(gbest.R_in_m), "grid_best_fraction": float(gbest.fraction_req),
           "grid_best_arrangement": gbest.arrangement, "epsilon_grid_minus_search": float(gbest.g_window_center) - sbest_center,
           "epsilon_within_band": bool(float(gbest.g_window_center) - sbest_center <= band),
           "best_on_box_boundary": bool(r <= 0.0101 or r >= 0.0399 or f >= 0.395), "runtime_s": time.time() - t0}
    pd.DataFrame([out]).to_csv(f"results/c15_l7_band_{tag}.csv", index=False)
    print("done", tag, "band", round(band, 2), "full", round(band_full, 2), "eps", round(out["epsilon_grid_minus_search"], 2), flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]))
