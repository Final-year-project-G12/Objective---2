# Rajasthan — Objective 1 Handoff & Input Data Reference

**Status: Complete (Standardized to Tamil Nadu Reference Structure)**

This folder contains the complete, frozen Objective 1 outputs, per-regime weather profiles, hot water demand profile, and raw NASA POWER weather cache for Rajasthan, matching the exact directory layout, naming conventions, and file organization of Tamil Nadu.

## Directory Structure

```
data/objective1/rajasthan/
├── demand/
│   └── demand_profile_rajasthan.csv                # Canonical 300 L/day draw profile (24 local hours)
├── weather/
│   ├── weather_regime_rajasthan_cluster0_daily.csv  # Regime 0 daily weather (GHI_daily_kWh, Ta_mean_C, etc.)
│   ├── weather_regime_rajasthan_cluster0_hourly.csv # Regime 0 hourly weather (8,760 hrs, 2025)
│   ├── weather_regime_rajasthan_cluster0_hourly_10yr.csv # Multi-year hourly weather (2016-2025)
│   ├── weather_regime_rajasthan_cluster0_sunevents.csv   # Sun-event weather timestamps
│   ├── weather_regime_rajasthan_cluster1_daily.csv
│   ├── weather_regime_rajasthan_cluster1_hourly.csv
│   ├── weather_regime_rajasthan_cluster1_hourly_10yr.csv
│   ├── weather_regime_rajasthan_cluster1_sunevents.csv
│   ├── weather_regime_rajasthan_cluster2_daily.csv
│   ├── weather_regime_rajasthan_cluster2_hourly.csv
│   ├── weather_regime_rajasthan_cluster2_hourly_10yr.csv
│   └── weather_regime_rajasthan_cluster2_sunevents.csv
└── objective1/
    ├── bic_selection_levelB_rajasthan.csv          # Level B model selection diagnostics
    ├── bic_selection_rajasthan.csv                 # Level A model selection diagnostics (K=3)
    ├── calibration_check_rajasthan.csv             # Medoid solar fraction benchmark check
    ├── climate_signature_rajasthan.csv             # Main climate fingerprint (320 points, 88 columns)
    ├── cluster_assignments_levelA_rajasthan.csv    # Level A GMM regime assignments
    ├── cluster_assignments_levelB_rajasthan.csv    # Level B seasonal regime assignments
    ├── cluster_assignments_rajasthan.csv           # Standardized GMM regime assignments (Level A)
    ├── cluster_profile_cards_rajasthan.md          # Human-readable cluster profile cards
    ├── cluster_profiles_rajasthan.csv              # Population-weighted cluster means (3 regimes)
    ├── daily_aggregates_medoids_rajasthan.csv      # Daily weather aggregates for medoids
    ├── daily_aggregates_rajasthan.csv              # Full daily weather aggregates (320 points)
    ├── daily_aggregates_summary_rajasthan.csv      # Point-level daily weather summary
    ├── era5_power_agreement_rajasthan.csv          # ERA5 vs NASA POWER validation stats
    ├── feasibility_survivors_by_cluster.csv        # PCM feasibility filter results (186 pairs)
    ├── kmeans_comparison_rajasthan.csv             # KMeans baseline vs GMM
    ├── koppen_validation_rajasthan.csv             # External Köppen-Geiger validation
    ├── level_b_feature_importance_rajasthan.csv    # Seasonal feature importance ranking
    ├── level_b_seasonal_summary.md                 # Seasonal PCM sensitivity summary
    ├── level_b_seasonal_topk.csv                   # Seasonal top-K PCM rankings (12 rows)
    ├── manifest.json                               # SHA-256 hashes and file inventory
    ├── mcdm_full_scores_by_cluster.csv             # Full MCDM scores for all survivors (39 rows)
    ├── mcdm_method_agreement_rajasthan.csv         # Pairwise agreement between MCDM methods
    ├── mcdm_rankings_rajasthan.csv                 # Complete wide MCDM ranking table
    ├── mcdm_topk_by_cluster.csv                    # Top-3 PCM recommendation per regime (9 rows)
    ├── medoid_points_rajasthan.csv                 # Regime medoids (RJP_0132, RJP_0202, RJP_0055)
    ├── monte_carlo_stability.csv                   # Weight sensitivity & stability metrics (39 rows)
    ├── pca_loadings.csv                            # PCA component loadings
    ├── pcm_database_rajasthan.csv                  # Candidate PCM property database (62 rows: 55 manufacturer + 7 literature)
    ├── pcm_mass_sensitivity_rajasthan.csv          # Mass sweep sensitivity (50-800 kg)
    ├── pcm_properties.csv                          # Shared raw manufacturer PCM sheet
    ├── phase8_supercooling_sweep_rajasthan.csv     # Supercooling penalty sensitivity
    ├── physics_validation_results.csv              # Grey-box simulator solar fraction baseline (39 rows)
    ├── physics_validation_spearman.csv             # Correlation between MCDM rank and solar fraction
    ├── physics_validation_summary_rajasthan.txt    # Physics validation text summary
    ├── population_grid_points.csv                  # 320 sampling points with weights & elevation
    ├── quality_report_rajasthan.json               # Full QC report
    ├── recommendation_cards.md                     # Human-readable recommendation cards
    ├── suntimes.csv                                # UTC sun-event timestamps
    ├── suntimes_medoids_rajasthan.csv              # UTC sun-event timestamps for medoids
    ├── tier2_signature_rajasthan.csv               # Point-level daily weather rollup
    └── raw_weather/                                # Medoid points' raw NASA POWER JSON (30 files: 3 medoids × 10 years, 2016–2025)
        ├── power_RJP_0055_*.json                   # Medoid for Cluster 2
        ├── power_RJP_0132_*.json                   # Medoid for Cluster 0
        └── power_RJP_0202_*.json                   # Medoid for Cluster 1
```

## Schema & Format Alignment with Tamil Nadu

To ensure full compatibility across downstream Objective 2 pipelines:
1. **Directory Structure**: Objective 1 tables sit inside `objective1/`, per-regime weather in `weather/`, draw schedule in `demand/`, and NASA POWER JSON in `objective1/raw_weather/`.
2. **PCM Candidate Database**: `pcm_database_rajasthan.csv` contains 62 rows (55 manufacturer + 7 literature candidates), exactly matching Tamil Nadu's 62-row database schema.
3. **Clustering Assignments**: `cluster_assignments_rajasthan.csv` provides the standard Level A cluster assignment file name matching `cluster_assignments_tamilnadu.csv`.
4. **Weather Variables**: `weather_regime_rajasthan_cluster{k}_daily.csv` carries standardized column aliases (`GHI_daily_kWh`, `Ta_mean_C`, `Ta_max_C`, `Ta_min_C`, `DTR_C`, `RH_mean_pct`, `wind_mean_ms`) alongside raw ERA5/NASA POWER fields.

## Climate Regimes & Medoids

| Cluster ID | Medoid Point | Lat, Lon | Total Points | Top-3 Recommended PCMs |
|---|---|---|---|---|
| 0 | RJP_0132 | 24.375, 74.125 | 114 pts | RT50, RT45HC, Lauric acid (C12) |
| 1 | RJP_0202 | 26.875, 73.625 | 103 pts | savE® OM50, Paraffin-HDPE PCM3, PCM6 |
| 2 | RJP_0055 | 26.625, 76.375 | 103 pts | savE® OM50, Paraffin-HDPE PCM3, PCM6 |
