"""
src/verify/results_registry.py
=================================
One flat table of every number the report is allowed to cite, each with
the file it came from.

Her report carries a registry of ~604 quantities for the same reason: once
a document quotes a number that no file can produce, the document and the
results have silently diverged, and nobody can tell which one is wrong.
A registry makes that failure detectable -- every figure in the write-up
resolves to a `(quantity, value, source)` row, and a quantity with no row
is a quantity that was made up.

The registry is BUILT FROM the result CSVs, never typed in by hand. If a
stage has not been run, its quantities are absent rather than stale, which
is the behaviour you want: a missing number is obvious, a stale one is not.
"""

import hashlib
from pathlib import Path

import pandas as pd

from config import RESULTS_DIR
from src.io_utils import load_design_bounds, load_system_config

# (file, stage label, the columns worth registering per row)
SOURCES = [
    ("dt_convergence_summary.csv", "G2 dt convergence",
     ["cluster_id", "dt_coarse_s", "dt_fine_s", "worst_metric_change_pct",
      "converged_at_coarse"]),
    ("dt_convergence_richardson.csv", "G2 Richardson",
     ["cluster_id", "metric", "observed_order_p", "extrapolated_limit"]),
    ("sobol_doe_results.csv", "G8 Sobol DOE",
     ["cluster_id", "pcm_name", "arrangement", "pcm_volume_fraction",
      "capsule_diameter_m", "flow_rate_kg_s", "g_window_kWh", "g_annual_kWh",
      "d_overheat_h", "max_pcm_temp_C", "max_water_temp_C",
      "residual_pct_of_collector"]),
    ("surrogate_bakeoff.csv", "G8 surrogate bake-off",
     ["cluster_id", "pcm_name", "arrangement", "target", "model", "spearman",
      "rmse_over_sd", "std_calibration", "is_winner"]),
    ("nsga2_fronts.csv", "G9 NSGA-II fronts",
     ["cluster_id", "pcm_name", "arrangement", "g_window_kWh_pred",
      "pcm_volume_fraction", "capsule_diameter_m", "flow_rate_kg_s", "n_capsule"]),
    ("active_learning_rounds.csv", "G8 active learning",
     ["cluster_id", "pcm_name", "arrangement", "round", "n_designs",
      "hypervolume", "hv_rel_move"]),
    ("repeatability_band.csv", "repeatability band",
     ["cluster_id", "year_sd_kWh", "dt_effect_kWh", "node_effect_kWh",
      "property_effect_kWh", "band_kWh"]),
    ("selection_funnel_audit.csv", "S0/S1/S2 funnel",
     ["cluster_id", "S0_candidates", "S1_safety_feasible", "S2_within_band",
      "best_objective_kWh", "indistinguishable", "band_kWh"]),
    ("deployable_design_per_regime.csv", "chosen design",
     None),
    ("held_out_test_results.csv", "G10 held-out test",
     ["cluster_id", "pcm_name", "year", "g_window_kWh", "max_pcm_temp_C",
      "max_water_temp_C", "residual_pct_of_collector", "run_id"]),
    ("g13_shield_split.csv", "G13 shield split", None),
    ("g14_g16_stack_position.csv", "G14/G16 stack position", None),
    ("g15_serve_decomposition.csv", "G15 serve decomposition", None),
    ("g17_widened_bounds.csv", "G17 widened bounds", None),
    ("g11_one_at_a_time.csv", "G11 one-at-a-time", None),
]


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def build_registry(state: str = "tamilnadu", results_dir: Path = None) -> pd.DataFrame:
    results_dir = results_dir or (RESULTS_DIR / state)
    rows = []

    # config provenance first: every number below is conditional on these
    sysconf = load_system_config()
    bounds = load_design_bounds()
    for q, v in [
        ("config.design_bounds_version", bounds.get("version")),
        ("config.tank_volume_L", sysconf["tank"]["volume_L"]),
        ("config.collector_area_m2", sysconf["collector"]["area_m2"]),
        ("config.delivery_target_C", sysconf["delivery"]["target_temp_C"]),
        ("config.max_water_temp_C", sysconf["safety"]["max_water_temp_C"]),
        ("config.max_pcm_temp_C", sysconf["safety"]["max_pcm_temp_C"]),
        ("config.shield_guard_band_C", sysconf["safety"].get("shield_guard_band_C")),
        ("config.shield_predictive", sysconf["safety"].get("shield_predictive", True)),
        ("config.solver_timestep_s", sysconf["solver"]["timestep_s"]),
    ]:
        rows.append({"stage": "config", "source_file": "configs/", "source_sha": "",
                     "row": 0, "quantity": q, "value": v})

    for fname, stage, cols in SOURCES:
        path = results_dir / fname
        if not path.exists():
            rows.append({"stage": stage, "source_file": fname, "source_sha": "",
                         "row": -1, "quantity": "STATUS", "value": "NOT RUN"})
            continue
        df = pd.read_csv(path)
        sha = _file_sha256(path)
        use = [c for c in (cols or df.columns) if c in df.columns]
        for i, rec in df[use].iterrows():
            for q, v in rec.items():
                rows.append({"stage": stage, "source_file": fname, "source_sha": sha,
                             "row": int(i), "quantity": q, "value": v})

    return pd.DataFrame(rows)


def main(state: str = "tamilnadu"):
    reg = build_registry(state)
    out = RESULTS_DIR / state / "results_registry.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    reg.to_csv(out, index=False)

    n_quant = len(reg)
    missing = reg[reg["value"].astype(str) == "NOT RUN"]["source_file"].tolist()
    print(f"registry: {n_quant} registered quantities from "
          f"{reg['source_file'].nunique()} sources")
    print(reg.groupby("stage").size().to_string())
    if missing:
        print(f"\nstages NOT YET RUN ({len(missing)}): {', '.join(missing)}")
    print(f"\nwrote {out}")
    return reg


if __name__ == "__main__":
    main()
