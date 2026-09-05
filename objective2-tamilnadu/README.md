# Objective 2 — Input Data Reference

This describes every file that lands in `objective2_design_optimization/data/`
after running, **in this order**:

```
python build_input_package.py     # copies/hashes Obj1 outputs -> data/objective1/
python build_regime_weather.py    # builds per-regime weather   -> data/weather/
python build_demand_profile.py    # builds the canonical draw   -> data/demand/
```

All three scripts have a `STATE = "tamilnadu"` variable near the top.
**If you are doing a different state, change only that one line** (and
`OBJ1_ROOT` in `config.py` if your Objective 1 folder isn't named
`era5_tamilnadu`) — everything else, including every filename below,
follows automatically. This is the point of naming files
`{thing}_{state}.csv`: every state's teammate produces an identically
structured `data/` folder, so Objective 2's design/simulation/surrogate
code never needs to know which state it's looking at.

**Naming convention — please follow this exactly when you add your state:**
`{content}_{state}.csv`, all lowercase, state name with no spaces
(`tamilnadu`, `rajasthan`, `assam`, `uttarakhand`). Per-cluster files add
`_cluster{k}` before the extension, e.g. `weather_regime_rajasthan_cluster2_hourly.csv`.

---

## `data/objective1/` — frozen copies of Objective 1 outputs

| File | Produced by (Obj1 script) | Grain | What it contains |
|---|---|---|---|
| `population_grid_points.csv` | `00a_build_population_grid.py` | 1 row/point | Sampling locations: `point_id, lat, lon, population, weight`. `weight` is that point's share of total state population covered. |
| `suntimes.csv` | `00b_build_suntimes.py` | 1 row/point/date/event | Exact UTC sunrise/solar-noon/sunset timestamps, 2016–2025. |
| `daily_aggregates_{state}.csv` | `02b_build_daily_aggregates.py` | 1 row/point/date | **Daily-resolution** weather from the full NASA POWER hourly cache: `GHI_daily_kWh, GHIcs_daily_kWh, kt_daily, Ta_mean_true, Ta_max_true, Ta_min_true, DTR_true, RH_mean_true, wind_mean_true`. This is the real daily integral, not a proxy. |
| `tier2_signature_{state}.csv` | `02b_build_daily_aggregates.py` | 1 row/point | Point-level rollup of the daily table above (annual means, HDD18/CDD24, cloudy-day run length CCI, etc.) — feeds into the climate signature below. |
| `era5_power_agreement_{state}.csv` | `03b_agreement_analysis.py` | varies | Cross-source validation stats (MBE/RMSE/Pearson r) between ERA5 and NASA POWER, per season/event — evidence the underlying weather data is trustworthy, not itself a modeling input. |
| `climate_signature_{state}.csv` | `04b_climate_signature.py` | **1 row/point** | **The main climate input for Obj2 geometry/constraint setup.** Every point's ~18-index climate fingerprint: `Ta_mean, Ta_p95, Ta_p05, DTR, GHI_daily_kWh, kt_mean, kt_std, SAI, CCI, cloudy_frac, HDD18, CDD24, RH_mean, HSI, wind_mean, seasonality, monsoon_index, elev_proxy`, plus `Tm_target_C` (constant, delivery-anchored) and `L_required_kJ_per_kg` (derived from the 300 L/day draw assumption — see `demand_profile_{state}.csv` below), plus PCA components and z-scored (`_z`) columns used only for clustering. |
| `pca_loadings.csv` | `04b_climate_signature.py` | 1 row/feature | How the PCA components in the signature file are built (diagnostic, not usually needed downstream). |
| `cluster_assignments_{state}.csv` | `05_cluster_tamilnadu.py` (or `05_cluster_regions.py` for multi-state) | **1 row/point** | Which climate regime (cluster) each point belongs to: `cluster_id` (hard label) plus `prob_cluster0...N` (soft GMM membership) and `max_membership_prob`. **This is the "Level A" assignment table** — the requested `_levelA` suffix isn't in the filename, but this *is* that file; rename it if your team wants the suffix for clarity. |
| `cluster_profiles_{state}.csv` | `05_cluster_tamilnadu.py` | **1 row/cluster** | Population-weighted mean of every signature column, per regime — `n_points`, `total_population_covered`, plus mean `Tm_target_C`, `L_required_kJ_per_kg`, `HSI`, `GHI_daily_kWh`, etc. **This is what Obj2's DOE reads to get each regime's design target.** |
| `bic_selection_{state}.csv`, `kmeans_comparison_{state}.csv` | `05_cluster_tamilnadu.py` | 1 row/K | Model-selection diagnostics (why K was chosen) — reference material, not a modeling input. |
| `pcm_database_{state}.csv` | `06_build_pcm_database.py` | 1 row/PCM | **Full property records for every candidate PCM** (not just the shortlisted ones): `name, family, Tm_C, latent_heat_kJ_kg, density_*, Cp_*, TC_W_mK, cycles_tested, supercooling_K, rho_H_MJ_m3, corrosion_class`, plus `any_property_imputed` flagging which values came from MICE/RF imputation vs. a real datasheet/paper. |
| `feasibility_survivors_by_cluster.csv` | `07_feasibility_filter.py` | 1 row/cluster/PCM | Every PCM checked against every cluster's `Tm_target`/`L_required`, with a pass/fail column per filter (melting window, latent-heat floor, cycling, supercooling, corrosion, safety) and `passes_all`. |
| `mcdm_topk_by_cluster.csv` | `08_mcdm_ranking.py` | 1 row/cluster/top-3 | **The Top-3 PCM recommendation per regime** — `consensus_rank`, `name`, `Tm_C`, `latent_heat_kJ_kg`, plus each method's score (`topsis_score`, `gra_grade`, `promethee_flow`, `vikor_Q`) and `top3_inclusion_probability` from the Monte Carlo stability check. **This is what tells Obj2 which PCM(s) to design hardware for.** |
| `mcdm_full_scores_by_cluster.csv` | `08_mcdm_ranking.py` | 1 row/cluster/survivor | Same as above but every feasibility survivor, not just the top 3 — useful if Obj2's DOE wants to simulate more than 3 candidates per regime. |
| `monte_carlo_stability.csv` | `08_mcdm_ranking.py` | 1 row/cluster/PCM | Standalone version of the Monte Carlo columns above (inclusion probability, rank-reversal rate). |
| `physics_validation_results.csv` *(optional)* | `10_physics_validation.py` | 1 row/cluster/PCM | Simulated annual solar fraction from Obj1's own grey-box check — **only present if you've run that script.** Useful as a sanity baseline before Obj2 builds its own (higher-fidelity, geometry-aware) simulator. |
| `physics_validation_spearman.csv` *(optional)* | `10_physics_validation.py` | 1 row/cluster | Correlation between MCDM rank and simulated performance, per regime. |
| `level_b_seasonal_topk.csv`, `level_b_seasonal_summary.md` *(optional)* | `11_level_b_seasonal_analysis.py` | 1 row/cluster/season | Whether the Top-1 PCM changes by season within a regime — if `flips_from_annual` is `True` anywhere, that regime may need a seasonal or cascaded PCM design in Obj2, not a single fixed one. |
| `recommendation_cards.md` | `09_recommendation_cards.py` | — | Human-readable summary of everything above, one card per cluster — Obj1's results section. Good for a quick sanity read, not meant to be parsed programmatically. |
| `manifest.json` | `build_input_package.py` (this project) | — | SHA-256 hash + source path of every file above, plus which files were too large to copy (hashed only — see below) and which points are each cluster's medoid. **Re-generate this any time Objective 1 is re-run**, so a stale copy is never silently used. |
| `raw_weather/power_{point_id}_{year}.json` | `01b_download_nasapower.py` (copied selectively) | full hourly | Real, unmodified NASA POWER hourly records — **only for each cluster's medoid point**, all available years. This is the raw material `build_regime_weather.py` turns into the per-regime files below. |

**Referenced-but-not-copied** (too large — hashed in `manifest.json`, read
directly from `era5_tamilnadu/data/...` if you ever need row-level access):
`climate_tamilnadu_points.csv` (every point × sun-event × ERA5+POWER
columns), `tamilnadu_cleaned_physical.csv` / `tamilnadu_cleaned_scaled.csv`
(the same, post-QC).

---

## `data/weather/` — per-regime representative weather (NEW, built here)

Not produced anywhere in Objective 1 — Obj1 only has per-*point* weather.
`build_regime_weather.py` picks each cluster's medoid point and produces:

| File | Grain | Columns |
|---|---|---|
| `weather_regime_{state}_cluster{k}_hourly.csv` | 1 row/hour, 1 representative year | `timestamp_utc, GHI_Wm2, GHI_clearsky_Wm2, T_amb_C, RH_pct, wind_ms, point_id, cluster_id, year`. **Real** hourly data (not a reconstructed sinusoid) from the medoid's raw NASA POWER cache — the best-covered year is picked automatically. |
| `weather_regime_{state}_cluster{k}_daily.csv` | 1 row/day, all available years | Same variables at daily resolution, straight from `daily_aggregates_{state}.csv` — use this for multi-year/multi-season DOE runs where hourly detail isn't needed. |

## `data/demand/` — canonical hot-water draw profile (NEW, built here)

| File | Grain | Columns |
|---|---|---|
| `demand_profile_{state}.csv` | 1 row/hour (0–23) | `hour, draw_fraction, draw_volume_L, draw_mass_kg`. **300 L/day total**, dual morning/evening peak — chosen specifically to match `climate_signature_{state}.csv`'s own `L_required_kJ_per_kg` assumption (Avargani et al. 2021, 300 L/day), which the existing `10_physics_validation.py` script does **not** currently match (it only draws 150 kg/day — see the script's own docstring for the full explanation). **Use this file, not a hand-picked number, wherever Obj2 needs a draw schedule**, so every regime/PCM/geometry combination is evaluated against the same household. |

This is currently **one file for the whole state, applied to every
cluster/season identically** — a stated simplification, not measured
per-regime demand data. If your team gets real Indian household draw data
later, replace `build_profile()` in `build_demand_profile.py` and keep the
same output columns so nothing downstream has to change.

---

## Quick checklist for a teammate starting a new state

1. Run that state's Objective 1 pipeline (00a → 11), producing
   `data/processed/...` under their own `era5_{state}/` folder — same
   scripts, same phase order, already state-parameterized.
2. Create their own `objective2_design_optimization/` folder as a sibling
   to `era5_{state}/`.
3. Copy in `config.py`, `build_input_package.py`, `build_regime_weather.py`,
   `build_demand_profile.py` from this project unchanged.
4. Edit `OBJ1_ROOT` in `config.py` and `STATE` at the top of each build
   script to their state name.
5. Run all three build scripts in order. They'll now have a `data/`
   folder with exactly the structure documented above, ready for the
   shared Obj2 `src/design`, `src/simulation`, `src/surrogate` code to
   consume identically regardless of which state it is.
