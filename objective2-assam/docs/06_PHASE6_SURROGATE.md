# 06 — Phase 6 Audit: AI Surrogate Model (Assam)

Files: `src/surrogate/features.py`, `src/surrogate/train.py`,
`src/surrogate/evaluate.py` (+ `scripts/build_phase6_models_and_report.py`,
the script that actually produced `results/phase6_surrogate_report.md`).
Output: `results/phase6_surrogate_metrics.csv`,
`results/phase6_surrogate_error_by_group.csv`,
`results/phase6_surrogate_feature_cols.json`,
`results/phase6_surrogate_report.md`.

> Rewritten from Assam's actual report/metrics files — the previous
> version of this doc described Rajasthan's 39-feature, R²=0.9998 run.
> Assam's surrogate uses **29 features** and reaches a lower (still
> passing) **R² = 0.9977** on useful energy.

## Purpose (D2.5)

One combined tree-based surrogate so Phase 7's optimization pass doesn't
need thousands of physics runs. Trained from the 111 valid rows of
`phase5_design_cases.csv`/`.parquet`, using its `split` column (Phase 5).

## Dataset

165 total DOE cases: 111 valid (67.3%) / 54 infeasible (32.7%).
138 train (93 valid / 45 invalid) / 27 holdout (18 valid / 9 invalid).
Feasibility classifier trains on all 165 (138/27); performance
regressors train strictly on the 111 valid cases (93 train / 18
holdout) — the 54 infeasible rows never reach the regressors.

## Features (29 total — fewer than Rajasthan's 39)

1. **Design/geometry (9):** `capsule_diameter_m, n_capsule,
   flow_rate_kg_s, geom_pcm_thickness_m, geom_pcm_volume_fraction,
   geom_void_fraction, geom_pressure_drop_pa, geom_pump_power_w,
   geom_reynolds_number_particle`.
2. **Climate, continuous (9):** `GHI_daily_kWh, Ta_mean, DTR, RH_mean,
   wind_mean, monsoon_index, Tm_target_C, L_required_kJ_per_kg,
   T_mains_est_C`. Assam's `cluster_profiles_assam.csv` does not carry
   the finer climate breakdown Rajasthan's table has (no separate
   `Ta_p95`/`Ta_p05`, sunrise-specific RH/HSI, noon-specific wind, CDD/HDD,
   `kt_daily_mean`, `cloudy_frac`) — hence fewer climate features here,
   a genuine Objective-1-table difference, not a code change.
3. **PCM thermophysical properties (10):** `Tm_C, latent_heat_kJ_kg,
   TC_W_mK, density_liquid_kg_m3, density_solid_kg_m3, Cp_liquid_kJ_kgK,
   Cp_solid_kJ_kgK, supercooling_K, rho_H_MJ_m3, any_property_imputed`.
4. **Baseline indicator (1):** `is_no_pcm`.

No separate Objective-1-confidence feature (`top3_inclusion_probability`)
here — consistent with `assam.yaml`'s note that Objective 1 did not
produce a confirmed-feasible MCDM ranking for Assam to draw a confidence
score from.

## Models trained

ExtraTreesRegressor (300 trees, seed `20260905`) per target vs. a
LinearRegression baseline, on the 93 train / 18 holdout valid split,
plus one ExtraTreesClassifier for feasibility (all 165 rows, 138/27
split).

## Hold-out results (actual run)

| Target | ExtraTrees R² | ExtraTrees RMSE | Linear R² | Linear RMSE | Tree beats linear? |
|---|---|---|---|---|---|
| `useful_energy_kWh` | 0.9977 | 1.011 kWh | 0.9981 | 0.917 kWh | No — linear competitive |
| `solar_fraction` | 0.9999 | 4.91e-4 | 0.9997 | 7.90e-4 | Yes (RMSE −37.9%) |
| `unmet_energy_kWh` | 0.9999 | 0.597 kWh | 0.9999 | 0.792 kWh | Yes (RMSE −24.7%) |
| `pump_energy_kWh` | 0.8819 | 2.79e-9 kWh | 0.3849 | 6.38e-9 kWh | Yes (RMSE −56.2%) — **unlike Rajasthan, where linear won here** |
| `pcm_mass_kg` | 0.9980 | 0.0639 kg | 0.9994 | 0.0342 kg | No — linear competitive |
| `mean_f_melt` | 0.9982 | 1.29e-3 | 0.9771 | 4.63e-3 | Yes (RMSE −72.2%) |

### Exit check

Framework doc: hold-out R² for useful energy must clear **> 0.80**.
**Result: 0.9977 (Extra Trees)** — passes with margin, though notably
lower than Rajasthan's 0.9998 and Tamil Nadu's comparable figure; Assam's
smaller demand (100 L/day vs 300 L/day) and the resulting smaller
absolute-energy scale likely make relative noise more visible. Feasibility
classifier: 100% hold-out accuracy, 100% infeasible recall, 5-fold CV
perfect (1.0000 ± 0.0000 across accuracy/F1/recall/ROC-AUC).

### Honest findings

1. **Linear ties/beats the tree on `useful_energy_kWh` and
   `pcm_mass_kg`** — same "physics is close to linear in this design
   region" story as Rajasthan/Tamil Nadu.
2. **Tree clearly wins on `pump_energy_kWh` here (R²=0.88 vs 0.38)** —
   the opposite of Rajasthan, where the tree was worse than linear on
   this near-numerical-noise target. Not a contradiction — both are
   fitting a ~1e-9 kWh signal that is close to noise at these sparse-bed
   flow rates; small differences in dataset/regime spread which model
   happens to fit better.
3. **Feasibility boundary is a sharp deterministic rule** (same
   diameter/thickness interaction documented in `02_…`/`05_…`) — the
   100%/100% classifier result is expected, not suspicious.

## Feature importance (useful energy)

`L_required_kJ_per_kg` (30.95%) > `T_mains_est_C` (17.59%) > `Ta_mean`
(16.06%) > `GHI_daily_kWh` (13.63%) > `DTR` (8.14%). `solar_fraction` is
dominated even more heavily by `L_required_kJ_per_kg` (52.74%) — Assam's
regime-to-regime spread in required latent heat (252–280 kJ/kg, driven
by the colder mains temperatures in Cluster 2) is the single strongest
predictor of both targets, more so than the climate/GHI features
themselves.

## Error breakdown by regime and by PCM

`useful_energy_kWh` MAE: 0.62–0.80 kWh across the 3 regimes (highest in
regime 0); 0.37–1.13 kWh across the 3 PCMs (highest for `savE® OM48`,
which appears in all 3 regimes' shortlists and so has the most holdout
rows spanning the widest climate range). `solar_fraction` MAE stays
≤4.2e-4 everywhere — no regime or PCM is a systematic weak spot.

## Deviations from the full framework doc

No neural-network/Gaussian-process comparison, no ablation study — same
40-hr cut-list deferral as the other states.
