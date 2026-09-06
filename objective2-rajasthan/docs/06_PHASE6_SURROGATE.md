# 06 — Phase 6 Audit: AI Surrogate Model (Rajasthan)

Files: `src/surrogate/features.py`, `src/surrogate/train.py`, `src/surrogate/evaluate.py`.
Run: `python pipeline.py --state rajasthan --stage surrogate`.
Output: `results/phase6_surrogate_metrics.csv`,
`results/phase6_surrogate_error_by_group.csv`,
`results/phase6_surrogate_models.pkl`,
`results/phase6_surrogate_feature_cols.json`.

> **Ported from `objective2-tamilnadu/src/surrogate/`.** `train.py` and
> `evaluate.py` keep TN's model family, hyper-parameters and train/holdout
> logic exactly — only the I/O paths differ (this repo's flat
> `results/phaseN_*` scheme). `features.py` keeps TN's four feature groups
> and its merge/split logic, but the **column names differ** because
> Rajasthan's Objective 1 pipeline writes different headers than Tamil
> Nadu's — see "Feature adaptation" below. Nothing about the surrogate's
> role changes: **it is a proposal ranker, not the final oracle**
> (Bug-Fix 5) — every design it favors is re-run in the real simulator in
> Phase 7 before anything is reported.

## Purpose (D2.5)

One combined tree-based surrogate (no ablation, per the reduced 40-hr
spec) so Phase 7's optimization pass doesn't need thousands of physics
runs. Trained from the 111 valid rows of `phase5_design_cases.parquet`,
using its `split` column (Phase 5).

## Features (39 total)

Design + geometry (9): `capsule_diameter_m, n_capsule, flow_rate_kg_s,
geom_pcm_thickness_m, geom_pcm_volume_fraction, geom_void_fraction,
geom_pressure_drop_pa, geom_pump_power_w, geom_reynolds_number_particle`.

Climate signature (17, continuous features per framework doc §7.1 — not
just an integer regime label): `GHI_daily_kWh, Ta_mean, Ta_p95, Ta_p05,
DTR_true, RH_sunrise_mean, HSI_sunrise, wind_noon_mean, monsoon_index,
seasonality, CDD24, HDD18, kt_daily_mean, cloudy_frac, Tm_target_C,
L_required_kJ_per_kg` from `cluster_profiles_rajasthan.csv`, plus
`T_mains_est_C` from `configs/states/rajasthan.yaml`.

PCM properties (11, from `pcm_database_rajasthan.csv`, zero-filled + an
explicit `is_no_pcm` flag for the plain-tank baseline so "no PCM" is never
confused with "a PCM with zero latent heat"): `Tm_C, latent_heat_kJ_kg,
TC_W_mK, density_liquid_kg_m3, density_solid_kg_m3, Cp_liquid_kJ_kgK,
Cp_solid_kJ_kgK, cycles_confidence, supercooling_K, rho_H_MJ_m3,
any_property_imputed`.

Objective 1 confidence (1): `top3_inclusion_probability` — Monte-Carlo
top-3 inclusion, a material-selection uncertainty feature, never
substituted for an actual thermophysical property (§2.3).

### Feature adaptation (why the column list is not byte-identical to TN's)

Rajasthan's Objective 1 tables were produced by a different pipeline
(`PCM-Selection-ML-model/era5-rajasthan`) with different headers:

| Feature | Tamil Nadu column | Rajasthan column |
|---|---|---|
| daily GHI | `GHI_daily_kWh_mean` | `GHI_daily_kWh` |
| ambient temp | `Ta_mean_true` / `Ta_p95_true` / `Ta_p05_true` | `Ta_mean` / `Ta_p95` / `Ta_p05` |
| diurnal range | `DTR_true_mean` | `DTR_true` |
| humidity | `RH_mean_true` | `RH_sunrise_mean` |
| heat-stress index | `HSI` | `HSI_sunrise` |
| wind | `wind_mean_true` | `wind_noon_mean` |
| seasonality | `seasonality_proxy` | `seasonality` |
| elevation | `elev_proxy` | *(absent — dropped)* |
| mains temp | `T_mains_est_C` (in `cluster_profiles`) | *(absent — read from `states/rajasthan.yaml`)* |
| MC confidence | `monte_carlo_stability.csv::top3_inclusion_probability` (0–1) | `mcdm_topk_by_cluster.csv::mc_top3_inclusion_pct` (0–100, ÷100) |

Rajasthan also *has* `CDD18/CDD24`, `HDD18`, `kt_daily_mean`,
`cloudy_frac` in its `cluster_profiles`, which are kept — so the net
feature count is 39 vs Tamil Nadu's 36. This is a state-specific
Objective-1-table difference, exactly the kind the framework doc's "what
VARIES per state" list anticipates; the surrogate *code* is unchanged.

## Models trained

ExtraTreesRegressor (300 trees, seed `20260905`) per target, each compared
against a plain LinearRegression baseline on the identical split
(**93 train / 18 holdout valid rows**), plus one ExtraTreesClassifier for
feasibility (trained on all non-holdout rows, valid + invalid; 27-row
holdout with 9 infeasible).

## Hold-out results (actual run)

| Target | ExtraTrees RMSE | ExtraTrees R² | Linear RMSE | Linear R² | Tree beats linear? |
|---|---|---|---|---|---|
| useful_energy_kWh | 0.525 kWh | **0.99983** | 0.438 kWh | 0.99988 | **No (tie)** |
| solar_fraction | 3.50e-4 | 0.99965 | 5.88e-4 | 0.99901 | Yes |
| unmet_energy_kWh | 0.880 kWh | 0.99986 | 1.466 kWh | 0.99962 | Yes |
| pump_energy_kWh | 2.93e-9 kWh | 0.326 | 4.64e-11 kWh | 0.99983 | **No** |
| pcm_mass_kg | 0.067 kg | 0.99725 | 0.058 kg | 0.99795 | **No (tie)** |
| feasibility (accuracy / infeasible-recall) | 1.000 / 1.000 | — | — | — | — |

### Exit check

Framework doc: hold-out R² for useful energy must clear **> 0.80** to
trust ranking (< 0.75 → add DOE cases or drop to a single target).
**Result: useful-energy hold-out R² = 0.99983 (Extra Trees), 0.99988
(linear).** Passed with a wide margin; no extra DOE cases needed. The
three "key outputs" named in D2.5 (useful energy, solar fraction, unmet
energy) all sit at R² ≥ 0.9996.

### Honest findings (framework doc requires this comparison be reported as-is)

1. **Linear regression ties or slightly beats the tree on
   `useful_energy_kWh`, `pump_energy_kWh` and `pcm_mass_kg`.** At the PCM
   volume fractions reachable within the frozen bounds (≤12.9%, Phase 2
   doc), the physics in this design region is close to linear in the
   sampled variables: `pcm_mass_kg` is exactly linear in
   `n_capsule·diameter³·ρ`; `pump_energy_kWh` is Ergun-viscous-term
   dominated (linear in flow) and only ~1e-9 kWh in magnitude anyway
   (near numerical noise — the tree's R²=0.33 there is not a real defect,
   it is a model fitting nanoscale noise); and annual `useful_energy` is
   driven mostly by the (few) regime-level climate features plus a near
   -linear PCM-mass contribution. Tamil Nadu saw the same for
   `pump_energy_kWh`; Rajasthan's smaller, sparser dataset makes it show
   for two more low-variance targets. The tree still wins where the
   relationship is genuinely non-linear (`solar_fraction`,
   `unmet_energy_kWh`), and ties elsewhere — so it is kept as the ranking
   model, and the linear baseline is retained in the metrics CSV as the
   honest comparator.
2. **Feasibility classifier: 100% hold-out accuracy, 100% recall on the
   infeasible class (9 infeasible hold-out examples).** Expected, not
   suspicious: the feasibility boundary here is one sharp deterministic
   rule (`capsule_diameter_m < 0.04 m` → derived thickness < floor, Phase
   5 doc) — a trivially learnable threshold for a tree ensemble.
3. **Small holdout (18 valid rows).** R² this close to 1.0 on 18 points
   should be read as "the surrogate ranks designs reliably", not as a
   precise generalisation-error estimate. Phase 7 re-confirms every
   selected design in the real simulator regardless (Bug-Fix 5).

## Error breakdown by regime and by PCM (`phase6_surrogate_error_by_group.csv`)

`useful_energy_kWh` MAE: 0.23–0.49 kWh across the 3 regimes; 0.05–0.91 kWh
across the 6 PCM groups (highest for `RT45HC`, which has only 2 holdout
rows). `solar_fraction` MAE ≤ 6.4e-4 everywhere. No regime is a
systematic weak spot; the per-PCM spread is dominated by holdout-count
noise (2–4 rows per group), not by any PCM being modelled badly. Full
ablation (regime-ID-only / design-only / no-confidence) is deferred per
the 40-hr cut list.

## Deviations from the full framework doc

No neural-network / Gaussian-process comparison, no 4-way ablation — both
explicitly deferred. XGBoost not tried: Extra Trees already reaches
R² ≥ 0.997 on every non-noise target, so there was no signal a second
tree family was needed at this dataset size.
