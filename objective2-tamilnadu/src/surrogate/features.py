"""
src/surrogate/features.py
============================
Phase 6 / D2.5 — builds the surrogate's input feature matrix from
design_cases.parquet (Phase 5), joined against the frozen Objective 1
climate/PCM tables, per the framework doc §7.1 ("use the continuous
Objective 1 climate features rather than only an integer regime label").

Feature groups:
  - design      : the sampled design vector + Phase 2 geometry outputs
  - climate     : Tier-1/Tier-2 climate-signature columns from
                   cluster_profiles_<state>.csv (population-weighted
                   regime means — NOT re-derived, read as-is)
  - PCM         : full property record from pcm_database_<state>.csv
                   (zero-filled for the no-PCM baseline rows, with an
                   explicit `is_no_pcm` flag so the surrogate can still
                   distinguish "no PCM" from "a PCM with zero latent heat")
  - confidence  : Objective 1's `top3_inclusion_probability` (Monte Carlo
                   stability) — a material-selection uncertainty feature,
                   never substituted for a thermophysical property
                   (framework doc §2.3)
"""

import pandas as pd

from config import BASE_DIR
from src.io_utils import load_state_config

CLIMATE_COLS = [
    # Names updated 2026-09-13 to match cluster_profiles_tamilnadu.csv's
    # current schema (unified with Rajasthan's Phase 3/4 column names on
    # 2026-09-08 — the old _true/_proxy-suffixed names and elev_proxy no
    # longer exist in that file; the previous list silently matched ZERO
    # columns here via the `if c in cluster_profiles.columns` guard below,
    # so every climate feature had been dropped without error).
    "GHI_daily_kWh", "Ta_mean", "Ta_p95", "Ta_p05", "DTR_true",
    "RH_sunrise_mean", "HSI_sunrise", "wind_noon_mean", "wind_sunset_mean",
    "monsoon_index", "Tm_target_C", "Tm_target_capped_C",
    "L_required_kJ_per_kg", "seasonality",
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
    # Confidence source switched 2026-09-13 from monte_carlo_stability.csv
    # to mcdm_full_rankings.csv: Phase 6's rename (mcdm_full_scores_by_
    # cluster.csv -> mcdm_full_rankings.csv, 2026-09-08 unification) left
    # monte_carlo_stability.csv with pcm_id/mc_top3_inclusion_pct (0-100
    # scale) instead of the name/top3_inclusion_probability (0-1 scale)
    # columns this script reads — a hard KeyError, not a silent mismatch,
    # since this merge key is selected by name rather than an `if c in
    # columns` guard. mcdm_full_rankings.csv already carries both the old
    # and new-named confidence columns with the same values (just scaled),
    # so no computation changes, only the source file.
    mc_stability_path = BASE_DIR / "data" / "objective1" / "mcdm_full_rankings.csv"
    mc_stability = pd.read_csv(mc_stability_path) if mc_stability_path.exists() else None

    df = design_cases.copy()
    df["is_no_pcm"] = (df["pcm_id"] == "NONE_plain_tank").astype(int)

    # --- climate features: join on regime_id == cluster_id ------------
    clim = cluster_profiles[["cluster_id"] + [c for c in CLIMATE_COLS if c in cluster_profiles.columns]]
    df = df.merge(clim, left_on="regime_id", right_on="cluster_id", how="left", suffixes=("", "_clim"))

    # --- PCM features: join on pcm_id == name --------------------------
    pcm = pcm_db[["name"] + [c for c in PCM_COLS if c in pcm_db.columns]]
    df = df.merge(pcm, left_on="pcm_id", right_on="name", how="left", suffixes=("", "_pcm"))
    pcm_present_cols = [c for c in PCM_COLS if c in pcm_db.columns]
    df[pcm_present_cols] = df[pcm_present_cols].fillna(0.0)

    # --- Objective 1 confidence: top3_inclusion_probability ------------
    if mc_stability is not None:
        conf = mc_stability[["cluster_id", "name", "top3_inclusion_probability"]]
        df = df.merge(conf, left_on=["regime_id", "pcm_id"], right_on=["cluster_id", "name"],
                       how="left", suffixes=("", "_conf"))
        df["top3_inclusion_probability"] = df["top3_inclusion_probability"].fillna(0.0)
    else:
        df["top3_inclusion_probability"] = 0.0

    return df


def feature_target_split(feature_df: pd.DataFrame, only_valid: bool = True):
    """Returns (X, y_dict, feasibility_y) ready for sklearn."""
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
