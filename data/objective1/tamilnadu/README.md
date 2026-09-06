# Tamil Nadu — Objective 1 Handoff & Input Data Reference

**Status: Complete (Source of Truth: `@objective2-tamilnadu/data`)**

This folder contains the complete, frozen Objective 1 outputs, per-regime weather profiles, hot water demand profile, and raw NASA POWER weather cache for Tamil Nadu.

## Directory Structure

```
data/objective1/tamilnadu/
├── demand/
│   └── demand_profile_tamilnadu.csv                # Canonical 300 L/day draw profile (24 local hours)
├── weather/
│   ├── weather_regime_tamilnadu_cluster0_daily.csv  # Regime 0 daily weather
│   ├── weather_regime_tamilnadu_cluster0_hourly.csv # Regime 0 hourly weather (8,784 hrs)
│   ├── weather_regime_tamilnadu_cluster1_daily.csv
│   ├── weather_regime_tamilnadu_cluster1_hourly.csv
│   ├── weather_regime_tamilnadu_cluster2_daily.csv
│   ├── weather_regime_tamilnadu_cluster2_hourly.csv
│   ├── weather_regime_tamilnadu_cluster3_daily.csv
│   ├── weather_regime_tamilnadu_cluster3_hourly.csv
│   ├── weather_regime_tamilnadu_cluster4_daily.csv
│   └── weather_regime_tamilnadu_cluster4_hourly.csv
└── objective1/
    ├── bic_selection_tamilnadu.csv                 # Model selection diagnostics (K=5)
    ├── climate_signature_tamilnadu.csv             # Main climate fingerprint (133 points)
    ├── cluster_assignments_tamilnadu.csv           # GMM regime assignments (Level A)
    ├── cluster_profiles_tamilnadu.csv              # Population-weighted cluster means (5 regimes)
    ├── era5_power_agreement_tamilnadu.csv          # ERA5 vs NASA POWER validation stats
    ├── feasibility_survivors_by_cluster.csv        # PCM feasibility filter results (310 candidate-cluster pairs)
    ├── kmeans_comparison_tamilnadu.csv             # KMeans silhouette baseline vs GMM
    ├── level_b_seasonal_summary.md                 # Seasonal PCM sensitivity summary
    ├── level_b_seasonal_topk.csv                   # Seasonal top-K PCM rankings (20 rows)
    ├── manifest.json                               # SHA-256 hashes and file inventory
    ├── mcdm_full_scores_by_cluster.csv             # Full MCDM scores for all survivors (59 rows)
    ├── mcdm_topk_by_cluster.csv                    # Top-3 PCM recommendation per regime (15 rows)
    ├── monte_carlo_stability.csv                   # Weight sensitivity & stability metrics (59 rows)
    ├── pca_loadings.csv                            # PCA component loadings
    ├── pcm_database_tamilnadu.csv                  # Candidate PCM property database (62 rows: 55 manufacturer + 7 literature)
    ├── physics_validation_results.csv              # Grey-box simulator solar fraction baseline (59 rows)
    ├── physics_validation_spearman.csv             # Correlation between MCDM rank and solar fraction (5 clusters)
    ├── population_grid_points.csv                  # 133 sampling points with weights
    ├── recommendation_cards.md                     # Human-readable summary per cluster
    ├── tier2_signature_tamilnadu.csv               # Point-level daily weather rollup
    └── raw_weather/                                # Medoid points' raw NASA POWER JSON (50 files: 5 medoids × 10 years, 2016–2025)
        ├── power_TNP_0001_*.json                   # Medoid for Cluster 0
        ├── power_TNP_0004_*.json                   # Medoid for Cluster 1
        ├── power_TNP_0005_*.json                   # Medoid for Cluster 2
        ├── power_TNP_0007_*.json                   # Medoid for Cluster 3
        └── power_TNP_0009_*.json                   # Medoid for Cluster 4
```

## Overview of Key Files

| Category | File | Description |
|---|---|---|
| **Demand** | `demand/demand_profile_tamilnadu.csv` | 24-hour canonical hot water draw profile (300 L/day, bimodal IST peaks at 07:00 & 19:00). |
| **Weather** | `weather/weather_regime_tamilnadu_cluster{k}_*.csv` | Per-regime representative weather (hourly and daily) derived from cluster medoid points. |
| **Clustering** | `objective1/cluster_assignments_tamilnadu.csv` | Level A GMM cluster labels for all 133 Tamil Nadu grid points (5 clusters: 0..4). |
| **Clustering** | `objective1/cluster_profiles_tamilnadu.csv` | Population-weighted mean signature per climate regime. |
| **PCMs** | `objective1/pcm_database_tamilnadu.csv` | 62 PCM candidates (55 manufacturer + 7 literature rows) with physical/thermal properties. |
| **MCDM** | `objective1/mcdm_topk_by_cluster.csv` | Top-3 recommended PCMs per climate cluster. |
| **Validation** | `objective1/physics_validation_results.csv` | Baseline solar fraction validation for top candidate PCMs. |
| **Metadata** | `objective1/manifest.json` | Hash manifest verifying byte integrity of all dataset components. |

## Climate Regimes & Medoids

| Cluster ID | Medoid Point | Lat, Lon | Total Points |
|---|---|---|---|
| 0 | TNP_0001 | 8.125, 77.375 | 28 pts |
| 1 | TNP_0004 | 8.375, 77.625 | 26 pts |
| 2 | TNP_0005 | 8.625, 77.125 | 27 pts |
| 3 | TNP_0007 | 8.625, 77.625 | 26 pts |
| 4 | TNP_0009 | 8.875, 77.375 | 26 pts |
