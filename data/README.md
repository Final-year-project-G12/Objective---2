# Objective 2 — Input Data Reference (Rajasthan)

Everything under `data/objective1/rajasthan/` is produced by running, **in this order**,
from the repo root:

```
python build_input_package.py      # copies/hashes Obj1 outputs  -> data/objective1/rajasthan/
python build_regime_weather.py     # per-regime weather          -> .../rajasthan/weather/
python build_demand_profile.py     # canonical draw profile      -> .../rajasthan/demand/
```

Add `--all-years` to `build_regime_weather.py` for the 10-year hourly files, and
`--skip-sunevents` to skip its 1.5 GB streaming pass.

All three read paths from [config.py](../config.py). **To run a different state, edit
only the `EDIT FOR YOUR STATE` block there** (`STATE`, `OBJ1_FOLDER_NAME`,
`POINT_ID_PREFIX`) — every filename below follows automatically.

Nothing in `data/objective1/` is edited by hand. Re-run the scripts and diff
`manifest.json`.

## Layout — how this differs from the Tamil Nadu project

Tamil Nadu is one state per repo, so it uses `data/objective1/`, `data/weather/`,
`data/demand/` as siblings. This repo holds all four states, so weather and demand are
nested **inside** the state folder:

```
data/objective1/rajasthan/
  <27 frozen Objective-1 tables>      see table below
  weather/                            per-regime representative weather (built here)
  demand/                             canonical hot-water draw profile (built here)
  raw_weather/                        30 medoid NASA POWER JSON files (2016-2025)
  manifest.json                       SHA-256 + source path of everything
```

Relative structure is otherwise identical, so shared `src/design`, `src/simulation` and
`src/surrogate` code only needs `STATE_DIR` handed to it.

Naming follows the team convention: `{content}_{state}.csv`, lowercase, no spaces;
per-cluster files add `_cluster{k}`.

---

## `data/objective1/rajasthan/` — frozen Objective-1 outputs

| File | Produced by (Obj1) | Grain | Contents |
|---|---|---|---|
| `population_grid_points_rajasthan.csv` | `00a_build_population_grid.py` | 1/point | 320 sampling locations: `point_id, lat, lon, population, weight`. |
| `climate_signature_rajasthan.csv` | `04_climate_signature_rajasthan.py` | **1/point** | **Main climate input for O2 geometry/constraint setup.** 88 columns: raw climate indices, `Tm_target_C` / `Tm_target_capped_C`, `L_required_kJ_per_kg`, interaction terms, `PC1..PC4`, and the `*_z` standardized columns clustering ran on. |
| `cluster_assignments_levelA_rajasthan.csv` | `05_cluster_rajasthan.py` | **1/point** | Which climate regime each point belongs to: `cluster_id` (k=3, GMM) + `prob_cluster0..2` + `max_membership_prob` + bootstrap ARI. This is the Level-A (spatial) table. |
| `cluster_assignments_levelB_rajasthan.csv` | `05_cluster_rajasthan.py` | 1/point/season | Level-B (seasonal) assignment — use to check whether a regime's design should be seasonal rather than fixed. |
| `cluster_profiles_rajasthan.csv` | `05_cluster_rajasthan.py` | **1/cluster** | **What the DOE reads for each regime's design target** — population-weighted mean of every signature column, incl. `Tm_target_C`, `Tm_target_capped_C`, `L_required_kJ_per_kg`, `HSI_sunrise`, `GHI_daily_kWh`, `n_points`, `total_population`. |
| `bic_selection_rajasthan.csv`, `bic_selection_levelB_rajasthan.csv` | `05_cluster_rajasthan.py` | 1/k | Model-selection diagnostics (BIC, silhouette, bootstrap ARI, KMeans baseline) — why k=3. Reference, not an input. |
| `koppen_validation_rajasthan.csv` | `05_cluster_rajasthan.py` | — | External validation of the clusters against Köppen-Geiger classes (ARI / NMI). |
| `level_b_feature_importance_rajasthan.csv` | `05_cluster_rajasthan.py` | 1/feature | Which features drive the seasonal (Level-B) split. |
| `pcm_database_rajasthan.csv` | shared `PCM_data/` | 1/PCM | **Full property records, all 55 manufacturer candidates** — `Tm_C, latent_heat_kJ_kg, density_*, Cp_*, TC_*, cycles, supercooling, corrosion, cost`, plus imputation flags (MICE-PMM). See caveat below about the +7 literature rows. |
| `feasibility_survivors_rajasthan.csv` | `07_feasibility_filter_rajasthan.py` | 1/cluster/PCM | Every PCM checked against every cluster's `Tm_target` / `L_required`, per-filter pass/fail + `passes_all`. **This is the kappa-calibrated branch** — the one MCDM actually ranked. |
| `mcdm_rankings_rajasthan.csv` | `08_mcdm_ranking_rajasthan.py` | 1/cluster/survivor | The full wide ranking table: `TOPSIS_rank, PROMETHEE_II_rank, VIKOR_rank, GRA_rank`, Borda/Copeland consensus, Kendall's W, entropy weights, `top3_at_lambda05` / `top3_at_lambda00`, and the Monte Carlo columns. |
| `mcdm_topk_by_cluster_rajasthan.csv` | *derived here* | 1/cluster/top-3 | **The Top-3 PCM recommendation per regime** — a projection of the wide table using its own `top3_at_lambda05` flag, with `consensus_rank` 1-3. No re-ranking happens; this is exactly what O1 reported. |
| `monte_carlo_stability_rajasthan.csv` | *derived here* | 1/cluster/PCM | The `mc_*` columns split out: top-3 inclusion %, top-1 retention %, rank-reversal frequency, mean Spearman vs baseline. |
| `mcdm_method_agreement_rajasthan.csv` | `08_mcdm_ranking_rajasthan.py` | 1/cluster/pair | Pairwise agreement between the four MCDM methods. |
| `physics_validation_rajasthan.csv` | `09_physics_validation_rajasthan.py` | 1/cluster/PCM | Simulated annual solar fraction from O1's own grey-box check — a sanity baseline before O2 builds its higher-fidelity, geometry-aware simulator. |
| `physics_validation_spearman_rajasthan.csv` | `09_physics_validation_rajasthan.py` | 1/cluster | Correlation between MCDM rank and simulated performance. |
| `physics_validation_summary_rajasthan.txt` | `09_physics_validation_rajasthan.py` | — | Human-readable summary of the above, including its own stated caveats. |
| `calibration_check_rajasthan.csv` | `09_physics_validation_rajasthan.py` | 1/cluster | Whether each medoid's calibration run lands in the 54-84% benchmark solar-fraction band. |
| `pcm_mass_sensitivity_rajasthan.csv` | `09_physics_validation_rajasthan.py` | 1/mass | PCM mass sweep 50-800 kg — evidence the architecture is tank-dominated at 50 kg. **Read this before choosing O2's mass range.** |
| `phase8_supercooling_sweep_rajasthan.csv` | `08_phase8_supercooling_sweep.py` | 1/k | Sensitivity of the ranking to the supercooling penalty factor. |
| `daily_aggregates_summary_rajasthan.csv` | `02b_build_daily_aggregates.py` | 1/point | Point-level rollup of the daily weather table (annual means, HDD18/CDD24, CCI). |
| `daily_aggregates_medoids_rajasthan.csv` | *subset cut here* | 1/point/date | Full daily record, **medoids only** (10,959 rows). The full 147 MB file is hashed, not copied. |
| `suntimes_medoids_rajasthan.csv` | *subset cut here* | 1/point/date/event | Exact UTC sunrise/noon/sunset timestamps, **medoids only** (32,877 rows). Full file is 202 MB, hashed only. |
| `era5_power_agreement_rajasthan.csv` | `03b_agreement_analysis.py` | varies | ERA5 vs NASA POWER cross-validation (MBE/RMSE/Pearson r) — evidence the weather is trustworthy, not itself an input. |
| `quality_report_rajasthan.json` | `03b_quality_check_rajasthan.py` | — | Full QC report on the raw/cleaned data. |
| `medoid_points_rajasthan.csv` | *derived here* | 1/cluster | Which point represents each regime, with lat/lon, population, membership prob, cluster size. |
| `recommendation_cards_rajasthan.md`, `cluster_profile_cards_rajasthan.md` | `10_recommendation_cards_rajasthan.py`, `05_cluster_rajasthan.py` | — | Human-readable per-cluster summary — O1's results section. Not meant to be parsed. |
| `manifest.json` | `build_input_package.py` | — | SHA-256 + source path of every file above, the large hashed-only files, and the medoid list. **Re-generate any time O1 is re-run** so a stale copy is never silently used. |
| `raw_weather/power_RJP_XXXX_{year}.json` | `01b_download_nasapower.py` (copied selectively) | full hourly | Real, unmodified NASA POWER hourly records — **medoids only**, all 10 years. Raw material for the per-regime hourly files. |

**Referenced-but-not-copied** (hashed in `manifest.json`; read directly from
`era5-rajasthan/data/...` if you need row-level access): `suntimes.csv` (202 MB),
`daily_aggregates_rajasthan.csv` (147 MB), `climate_rajasthan_points.csv` (1.5 GB),
`climate_rajasthan_points_clean.csv` (1.6 GB), `rajasthan_cleaned_physical.csv` (4.2 GB),
`rajasthan_cleaned_scaled.csv` (4.7 GB).

---

## `weather/` — per-regime representative weather (built here)

Not produced anywhere in Objective 1 — O1 only has per-*point* weather. Each regime is
represented by its **medoid**: the point nearest the cluster mean in the standardized
(`*_z`) clustering space, via Objective 1's own `physics_lib.find_medoid`. That is the
same point `09_physics_validation_rajasthan.py` simulates, so O1's reported solar
fractions and O2's simulations refer to the same locations.

| Regime | Medoid | lat, lon | Cluster size |
|---|---|---|---|
| 0 | RJP_0132 | 24.375, 74.125 | 114 pts |
| 1 | RJP_0202 | 26.875, 73.625 | 103 pts |
| 2 | RJP_0055 | 26.625, 76.375 | 103 pts |

| File | Grain | Columns |
|---|---|---|
| `weather_regime_rajasthan_cluster{k}_hourly.csv` | 1/hour, 8,760 rows, best year (2025) | `timestamp_utc, GHI_Wm2, T_amb_C, RH_pct, WS_ms, local_hour, local_date, point_id, cluster_id, year` |
| `weather_regime_rajasthan_cluster{k}_hourly_10yr.csv` | 1/hour, 87,672 rows, 2016-2025 | same — for multi-year DOE runs |
| `weather_regime_rajasthan_cluster{k}_daily.csv` | 1/day, 3,653 rows, 10 years | `point_id, date, n_hours, GHI_Wh_m2, GHI_clearsky_Wh_m2, kt_daily, T2M_min/max/mean, RH2M_mean, WS10M_mean, cluster_id` — note `GHI_Wh_m2`, not the `GHI_daily_kWh` the Tamil Nadu schema uses; divide by 1000 if porting TN code |
| `weather_regime_rajasthan_cluster{k}_sunevents.csv` | 3/day (sunrise/noon/sunset), 10,959 rows | Full ERA5 column set — DNI, DHI, cloud cover, pressure, SZA, azimuth, clear-sky GHI — which the NASA POWER hourly cache does **not** carry |

> **Rajasthan's hourly files are real reanalysis, not a reconstruction.** The Tamil Nadu
> script synthesises an hourly curve from daily aggregates because its pipeline has no
> hourly cache. Rajasthan's does (320 points × 2016-2025 of genuine hourly
> `ALLSKY_SFC_SW_DWN` / `T2M` / `RH2M` / `WS10M`), loaded through
> `physics_lib.load_nasapower_hourly_year` — same completeness rule O1 applies (most
> recent year with a full 8760/8784-h record and <1% fill values, falling back to older
> years, then interpolating remaining gaps). **State this difference in the methodology**
> — it is a real fidelity gap between the two states' D2.3 inputs.

## `demand/` — canonical hot-water draw profile (built here)

| File | Grain | Columns |
|---|---|---|
| `demand_profile_rajasthan.csv` | 1/local hour (0-23) | `hour, draw_fraction, draw_volume_L, draw_mass_kg, cumulative_fraction` |

**300 L/day**, two Gaussian peaks at 07:00 and 19:00 local (IST, σ = 1.5 h), weighted
0.42 morning / 0.58 evening; peak draw 46.3 L at 19:00.

Unlike the Tamil Nadu version, this script **does not invent a profile** — it exports
the one already in the pipeline. The TN script exists to resolve a contradiction (its
`04b` assumes 300 L/day while its `10_physics_validation.py` draws only 150 kg/day).
Rajasthan has no such conflict:

- `04_climate_signature_rajasthan.py:233` — `NIGHT_DRAW_TOTAL_L = 300.0`
- `physics_lib.py:340` — `DRAW_TOTAL_KG_PER_DAY = 300.0`

`build_demand_profile.py` imports `physics_lib.hourly_draw_fractions()` directly and
**hard-fails** if those two ever diverge. To change the demand assumption, edit
`physics_lib.py` — not this script — so O1's `L_required` and O2's simulator move
together, then re-run.

One profile for the whole state, every cluster and season — a stated simplification, not
measured per-regime demand. No measured Indian household draw data was available.

---

## Caveats carried over from Objective 1

- **PCM database is 55 rows, not 62.** `07_feasibility_filter_rajasthan.py` appends 7
  hard-coded literature rows in code; they are not in `pcm_database_rajasthan.csv`. If
  O2 needs all 62, read them from that script, or use
  `feasibility_survivors_rajasthan.csv`, which is post-filter and already carries the
  properties MCDM ranked on.
- **`L_required_kJ_per_kg` uses the combined sensible+latent basis** (`SHARE_PCM = 0.5`),
  per the 2026-08-31 correction in `CLAUDE.md` §3.1. Do not re-derive it against a
  latent-heat-only assumption.
- **The architecture is tank-dominated at 50 kg PCM.** O1's own PCM-vs-plain-tank
  comparator showed ~0.0% difference at `PCM_MASS_KG = 50` against a 300 kg tank —
  documented as a model-scope finding, not a bug. PCM-vs-PCM comparison stays meaningful.
  See `pcm_mass_sensitivity_rajasthan.csv` before fixing O2's mass range.
- **Mojibake in `pcm_id`.** Some values read `savEÂ® OM50` for `savE® OM50` (upstream
  encoding). Copies are byte-identical on purpose — normalize at read time in O2 rather
  than editing the freeze.
- **Level-A k=3** with bootstrap ARI 0.83. Level-B (seasonal) is a separate table; check
  it before assuming one fixed design per regime is enough.

## Other states

`data/objective1/{assam,tamil_nadu,uttarakhand}/` currently hold `_STATUS.md` files
listing what their upstream pipelines still owe. Tamil Nadu has signature/clusters/
profiles but no MCDM ranking and no point-level hourly cache; Assam and Uttarakhand have
no processed O1 outputs yet. Point `config.py` at each state's pipeline and re-run the
three build scripts as they finish.
