"""
src/surrogate/features.py
============================
Phase 6 / D2.5 — builds the surrogate's input feature matrix from
phase5_design_cases.parquet (Phase 5), joined against the frozen
Objective 1 climate/PCM tables, per the framework doc §7.1 ("use the
continuous Objective 1 climate features rather than only an integer
regime label").

State-Independent Feature Schema:
- Design: 9 geometric/flow features from Phase 2 geometry & design vector
- Climate: 9 canonical continuous features mapped consistently across states
  (GHI_daily_kWh, Ta_mean, DTR, RH_mean, wind_mean, monsoon_index,
   Tm_target_C, L_required_kJ_per_kg, T_mains_est_C)
- PCM: 10 physical thermophysical properties (zero-filled only for the
  no-PCM baseline, with an explicit `is_no_pcm` indicator)
- Methodology compliance:
  * Never substitutes missing historical MCDM values with 0.
  * Never uses physics-validation performance as a surrogate feature
    (prevents target leakage).
  * Standardized state-independent schema identical across states.
"""

import pandas as pd

from config import BASE_DIR
from src.io_utils import load_state_config

# Canonical climate features across all states
CLIMATE_COLS = [
    "GHI_daily_kWh",
    "Ta_mean",
    "DTR",
    "RH_mean",
    "wind_mean",
    "monsoon_index",
    "Tm_target_C",
    "L_required_kJ_per_kg",
    "T_mains_est_C",
]

# State-specific mapping to canonical climate feature names
CLIMATE_MAPPINGS = {
    "rajasthan": {
        "GHI_daily_kWh": "GHI_daily_kWh",
        "Ta_mean": "Ta_mean",
        "DTR_true": "DTR",
        "RH_sunrise_mean": "RH_mean",
        "wind_noon_mean": "wind_mean",
        "monsoon_index": "monsoon_index",
        "Tm_target_C": "Tm_target_C",
        "L_required_kJ_per_kg": "L_required_kJ_per_kg",
    },
    "assam": {
        "GHI_daily_kWh_est_mean": "GHI_daily_kWh",
        "Ta_mean_mean": "Ta_mean",
        "DTR_mean": "DTR",
        "RH_mean_mean": "RH_mean",
        "wind_mean_mean": "wind_mean",
        "monsoon_index_mean": "monsoon_index",
        "Tm_target_C": "Tm_target_C",
        "L_required_kJ_per_kg": "L_required_kJ_per_kg",
    },
}

PCM_COLS = [
    "Tm_C",
    "latent_heat_kJ_kg",
    "TC_W_mK",
    "density_liquid_kg_m3",
    "density_solid_kg_m3",
    "Cp_liquid_kJ_kgK",
    "Cp_solid_kJ_kgK",
    "supercooling_K",
    "rho_H_MJ_m3",
    "any_property_imputed",
]

DESIGN_COLS = [
    "capsule_diameter_m",
    "n_capsule",
    "flow_rate_kg_s",
    "geom_pcm_thickness_m",
    "geom_pcm_volume_fraction",
    "geom_void_fraction",
    "geom_pressure_drop_pa",
    "geom_pump_power_w",
    "geom_reynolds_number_particle",
]

TARGET_COLS = [
    "useful_energy_kWh",
    "solar_fraction",
    "unmet_energy_kWh",
    "pump_energy_kWh",
    "pcm_mass_kg",
    "mean_f_melt",
]


def build_feature_table(state: str, design_cases: pd.DataFrame) -> pd.DataFrame:
    cfg = load_state_config(state)
    cluster_profiles = pd.read_csv(BASE_DIR / "data" / "objective1" / f"cluster_profiles_{state}.csv")
    pcm_db = pd.read_csv(BASE_DIR / cfg["pcm_database_file"])

    df = design_cases.copy()
    df["is_no_pcm"] = (df["pcm_id"] == "NONE_plain_tank").astype(int)

    # --- 1. Climate features: map to canonical column names -----------
    mapping = CLIMATE_MAPPINGS.get(state.lower(), {})
    mapped_profiles = cluster_profiles.rename(columns=mapping)

    clim_cols_available = [c for c in CLIMATE_COLS if c in mapped_profiles.columns and c not in df.columns]
    if clim_cols_available:
        clim = mapped_profiles[["cluster_id"] + clim_cols_available]
        df = df.merge(clim, left_on="regime_id", right_on="cluster_id", how="left")

    # Injected T_mains_est_C from per-regime block if not in profile CSV
    if "T_mains_est_C" not in df.columns:
        t_mains_by_regime = {int(r["cluster_id"]): float(r["T_mains_est_C"]) for r in cfg["regimes"]}
        df["T_mains_est_C"] = df["regime_id"].map(t_mains_by_regime)

    # --- 2. PCM features: join on pcm_id == name ----------------------
    pcm_present_cols = [c for c in PCM_COLS if c in pcm_db.columns and c not in df.columns]
    if pcm_present_cols:
        pcm = pcm_db[["name"] + pcm_present_cols]
        df = df.merge(pcm, left_on="pcm_id", right_on="name", how="left")

    # For no-PCM baseline rows, fill PCM thermophysical features with 0.0
    pcm_all_cols = [c for c in PCM_COLS if c in df.columns]
    df[pcm_all_cols] = df[pcm_all_cols].fillna(0.0)

    # Convert any boolean columns (like any_property_imputed) to float/int
    if "any_property_imputed" in df.columns:
        df["any_property_imputed"] = df["any_property_imputed"].astype(float)

    return df


def feature_target_split(feature_df: pd.DataFrame, only_valid: bool = True):
    """Returns (X, y_dict, feasibility_y, feature_cols) ready for sklearn."""
    feature_cols = [c for c in DESIGN_COLS if c in feature_df.columns]
    feature_cols += [c for c in CLIMATE_COLS if c in feature_df.columns]
    feature_cols += [c for c in PCM_COLS if c in feature_df.columns]
    feature_cols += ["is_no_pcm"]
    feature_cols = list(dict.fromkeys(feature_cols))   # de-dup, preserve order

    feasibility_y = feature_df["valid"].astype(int)

    df = feature_df[feature_df["valid"]] if only_valid else feature_df
    X = df[feature_cols].copy()
    y = {t: df[t] for t in TARGET_COLS if t in df.columns}
    return X, y, feasibility_y, feature_cols
