"""
src/surrogate/features.py
============================
Phase 6 / D2.5 — builds the surrogate's input feature matrix from
phase5_design_cases.parquet (Phase 5), joined against the frozen
Objective 1 climate/PCM tables, per the framework doc §7.1 ("use the
continuous Objective 1 climate features rather than only an integer
regime label").

PORTED FROM objective2-tamilnadu/src/surrogate/features.py. Feature GROUPS
and the split/merge logic are unchanged; the column NAMES differ because
Rajasthan's Objective 1 pipeline (`PCM-Selection-ML-model/era5-rajasthan`)
writes different headers than Tamil Nadu's:
  - climate: `cluster_profiles_rajasthan.csv` uses `Ta_mean` / `GHI_daily_kWh`
    / `DTR_true` / `RH_sunrise_mean` / `HSI_sunrise` / `wind_noon_mean` /
    `seasonality` (not TN's `*_true` / `*_proxy` / `*_mean` suffixes), and
    has no `elev_proxy` or `T_mains_est_C` column.
  - `T_mains_est_C` is therefore taken from the per-regime block of
    `configs/states/rajasthan.yaml` instead (same value Objective 1
    produced, just stored there in this repo).
  - Objective 1 confidence: Rajasthan keeps the shortlisted-PCM Monte
    Carlo stability in `mcdm_topk_by_cluster.csv` (`mc_top3_inclusion_pct`,
    0-100) rather than TN's `monte_carlo_stability.csv`
    (`top3_inclusion_probability`, 0-1). Converted to the same 0-1
    `top3_inclusion_probability` feature name here.

Feature groups (unchanged from TN):
  - design      : the sampled design vector + Phase 2 geometry outputs
  - climate     : Tier-1/Tier-2 climate-signature columns from
                   cluster_profiles_rajasthan.csv (population-weighted
                   regime means — NOT re-derived, read as-is) + T_mains_est_C
                   from the state config
  - PCM         : full property record from pcm_database_rajasthan.csv
                   (zero-filled for the no-PCM baseline rows, with an
                   explicit `is_no_pcm` flag)
  - confidence  : Objective 1's Monte-Carlo top-3 inclusion probability
                   — a material-selection uncertainty feature, never
                   substituted for a thermophysical property (§2.3)
"""

import pandas as pd

from config import BASE_DIR
from src.io_utils import load_state_config

# Column names as they appear in cluster_profiles_rajasthan.csv (see docstring).
CLIMATE_COLS = [
    "GHI_daily_kWh", "Ta_mean", "Ta_p95", "Ta_p05", "DTR_true",
    "RH_sunrise_mean", "HSI_sunrise", "wind_noon_mean", "monsoon_index",
    "seasonality", "CDD24", "HDD18", "kt_daily_mean", "cloudy_frac",
    "Tm_target_C", "L_required_kJ_per_kg",
    # T_mains_est_C is injected from the state config, not this CSV (see docstring)
    "T_mains_est_C",
]
PCM_COLS = [
    "Tm_C", "latent_heat_kJ_kg", "TC_W_mK", "density_liquid_kg_m3", "density_solid_kg_m3",
    "Cp_liquid_kJ_kgK", "Cp_solid_kJ_kgK", "cycles_confidence", "supercooling_K",
    "rho_H_MJ_m3", "any_property_imputed",
]
DESIGN_COLS = [
    "capsule_diameter_m", "n_capsule", "flow_rate_kg_s",
    "geom_pcm_thickness_m", "geom_pcm_volume_fraction", "geom_void_fraction",
    "geom_pressure_drop_pa", "geom_pump_power_w", "geom_reynolds_number_particle",
]
TARGET_COLS = ["useful_energy_kWh", "solar_fraction", "unmet_energy_kWh",
               "pump_energy_kWh", "pcm_mass_kg", "mean_f_melt"]


def build_feature_table(state: str, design_cases: pd.DataFrame) -> pd.DataFrame:
    cfg = load_state_config(state)
    cluster_profiles = pd.read_csv(BASE_DIR / "data" / "objective1" / f"cluster_profiles_{state}.csv")
    pcm_db = pd.read_csv(BASE_DIR / cfg["pcm_database_file"])
    mcdm_topk_path = BASE_DIR / "data" / "objective1" / "mcdm_topk_by_cluster.csv"
    mcdm_topk = pd.read_csv(mcdm_topk_path) if mcdm_topk_path.exists() else None

    df = design_cases.copy()
    df["is_no_pcm"] = (df["pcm_id"] == "NONE_plain_tank").astype(int)

    # --- climate features: join on regime_id == cluster_id ------------
    clim_cols_here = [c for c in CLIMATE_COLS if c in cluster_profiles.columns]
    clim = cluster_profiles[["cluster_id"] + clim_cols_here]
    df = df.merge(clim, left_on="regime_id", right_on="cluster_id", how="left", suffixes=("", "_clim"))

    # --- T_mains_est_C from the state config's per-regime block --------
    if "T_mains_est_C" not in df.columns:
        t_mains_by_regime = {int(r["cluster_id"]): float(r["T_mains_est_C"]) for r in cfg["regimes"]}
        df["T_mains_est_C"] = df["regime_id"].map(t_mains_by_regime)

    # --- PCM features: join on pcm_id == name --------------------------
    pcm = pcm_db[["name"] + [c for c in PCM_COLS if c in pcm_db.columns]]
    df = df.merge(pcm, left_on="pcm_id", right_on="name", how="left", suffixes=("", "_pcm"))
    pcm_present_cols = [c for c in PCM_COLS if c in pcm_db.columns]
    df[pcm_present_cols] = df[pcm_present_cols].fillna(0.0)

    # --- Objective 1 confidence: mc_top3_inclusion_pct (0-100 -> 0-1) --
    if mcdm_topk is not None and {"cluster_id", "pcm_id", "mc_top3_inclusion_pct"}.issubset(mcdm_topk.columns):
        conf = mcdm_topk[["cluster_id", "pcm_id", "mc_top3_inclusion_pct"]].copy()
        conf = conf.rename(columns={"pcm_id": "pcm_id_conf"})
        df = df.merge(conf, left_on=["regime_id", "pcm_id"],
                       right_on=["cluster_id", "pcm_id_conf"], how="left", suffixes=("", "_conf"))
        df["top3_inclusion_probability"] = (df["mc_top3_inclusion_pct"] / 100.0).fillna(0.0)
    else:
        df["top3_inclusion_probability"] = 0.0

    return df


def feature_target_split(feature_df: pd.DataFrame, only_valid: bool = True):
    """Returns (X, y_dict, feasibility_y, feature_cols) ready for sklearn."""
    feature_cols = [c for c in DESIGN_COLS if c in feature_df.columns]
    feature_cols += [c for c in CLIMATE_COLS if c in feature_df.columns]
    feature_cols += [c for c in PCM_COLS if c in feature_df.columns]
    feature_cols += ["is_no_pcm", "top3_inclusion_probability"]
    feature_cols = list(dict.fromkeys(feature_cols))   # de-dup, keep order

    feasibility_y = feature_df["valid"].astype(int)

    df = feature_df[feature_df["valid"]] if only_valid else feature_df
    X = df[feature_cols].copy()
    y = {t: df[t] for t in TARGET_COLS if t in df.columns}
    return X, y, feasibility_y, feature_cols
