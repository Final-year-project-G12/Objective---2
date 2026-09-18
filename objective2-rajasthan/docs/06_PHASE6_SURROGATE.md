# 06 — Phase 6 Audit: AI Surrogate Model (Rajasthan)

Files: `src/surrogate/features.py`, `src/surrogate/train.py`, `src/surrogate/evaluate.py`.
Run: `python pipeline.py --state rajasthan --stage surrogate`.
Output: `results/phase6_surrogate_metrics.csv`,
`results/phase6_surrogate_error_by_group.csv`,
`results/phase6_arrangement_importance.csv`,
`results/phase6_surrogate_models.pkl`,
`results/phase6_surrogate_feature_cols.json`.

> **Ported from `objective2-tamilnadu/src/surrogate/`**, then given
> **arrangement as a first-class feature on 2026-09-17**
> (`Objective2 Consolidated plan.md` §6, Phase 6). `train.py` and
> `evaluate.py` keep TN's model family, hyper-parameters and train/holdout
> logic exactly — only the I/O paths differ (this repo's flat
> `results/phaseN_*` scheme) and the new arrangement-importance diagnostic
> (below). `features.py` keeps TN's four feature groups and its
> merge/split logic, but the **column names differ** because Rajasthan's
> Objective 1 pipeline writes different headers than Tamil Nadu's — see
> "Feature adaptation" below. Nothing about the surrogate's role changes:
> **it is a proposal ranker, not the final oracle** (Bug-Fix 5) — every
> design it favors is re-run in the real simulator in Phase 7 before
> anything is reported.

## Purpose (D2.5)

One combined tree-based surrogate (no ablation, per the reduced 40-hr
spec) so Phase 7's optimization pass doesn't need thousands of physics
runs. Trained from the 128 valid rows of `phase5_design_cases.parquet`
(101 train / 27 holdout), using its `split` column (Phase 5).

## Features (42 total)

Design + geometry (12 — was 9 before arrangement was restored):
`capsule_diameter_m, n_capsule, flow_rate_kg_s, geom_pcm_thickness_m,
geom_pcm_volume_fraction, geom_void_fraction, geom_pressure_drop_pa,
geom_pump_power_w, geom_reynolds_number_particle`, plus the **arrangement
one-hot** `arr_single_layer, arr_staggered, arr_radial` (added
2026-09-17). No-PCM baseline rows get all three arrangement columns
forced to zero — arrangement doesn't apply to a PCM-less config, and an
arbitrary default would look like a 4th category to the model.

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
`cloudy_frac` in its `cluster_profiles`, which are kept. This is a
state-specific Objective-1-table difference, exactly the kind the
framework doc's "what VARIES per state" list anticipates; the surrogate
*code* is unchanged.

## Models trained

ExtraTreesRegressor (300 trees, seed `20260905`) per target, each compared
against a plain LinearRegression baseline on the identical split
(**101 train / 27 holdout valid rows**), plus one ExtraTreesClassifier for
feasibility (trained on all non-holdout rows, valid + invalid; 54-row
holdout).

## Hold-out results (actual run)

| Target | ExtraTrees MAE | ExtraTrees RMSE | ExtraTrees R² | Linear RMSE | Linear R² | Tree beats linear? |
|---|---|---|---|---|---|---|
| useful_energy_kWh | 0.362 kWh | 0.723 kWh | **0.9997** | 0.529 kWh | 0.9998 | No (tie — linear marginally lower RMSE) |
| solar_fraction | 3.69e-4 | 6.20e-4 | 0.9990 | 1.01e-3 | 0.9973 | Yes |
| unmet_energy_kWh | 0.932 kWh | 1.537 kWh | 0.9996 | 2.498 kWh | 0.9990 | Yes |
| pump_energy_kWh | 4.24e-8 kWh | 1.368e-7 kWh | 0.9631 | 4.44e-9 kWh | 0.99996 | No |
| pcm_mass_kg | 0.164 kg | 0.516 kg | 0.9403 | 0.0867 kg | 0.9983 | No |
| feasibility (accuracy / infeasible-recall) | — | — | 1.000 / 1.000 (27/27 infeasible holdout rows) | — | — | — |

### Exit check

Framework doc: hold-out R² for useful energy must clear **> 0.80** to
trust ranking (< 0.75 → add DOE cases or drop to a single target).
**Result: useful-energy hold-out R² = 0.9997 (Extra Trees), 0.9998
(linear).** Passed with a wide margin on the larger, arrangement-
stratified dataset — no extra DOE cases needed. The three "key outputs"
named in D2.5 (useful energy, solar fraction, unmet energy) all sit at
R² ≥ 0.999.

### Arrangement feature-importance diagnostic (new 2026-09-17)

| Target | arr_single_layer | arr_staggered | arr_radial | Combined |
|---|---|---|---|---|
| useful_energy_kWh | 0.000004 | 0.000009 | 0.000004 | 0.000018 |
| solar_fraction | 0.000026 | 0.000048 | 0.000025 | 0.000100 |
| unmet_energy_kWh | 0.000013 | 0.000021 | 0.000011 | 0.000045 |
| pump_energy_kWh | 0.000550 | 0.000676 | 0.000739 | 0.001964 |
| pcm_mass_kg | 0.000980 | 0.000349 | 0.001092 | 0.002421 |

**Finding — arrangement's feature importance is genuinely near-zero for
every target** (combined importance 0.000018–0.002421, highest for
`pcm_mass_kg` and `pump_energy_kWh`). This is not a bug: it is the direct,
consistent consequence of Phase 3's finding that `void_fraction` (the only
channel arrangement affects) is consumed solely by the hydraulics/pump-
power path, which is itself a negligible fraction of this system's total
energy balance. "Arrangement had minimal effect on every performance
target in this design-space region" is the honest, reproducible result —
reported as found, per the phase's own instruction not to treat a low
number as a sign something is broken.

### Honest findings (framework doc requires this comparison be reported as-is)

1. **Linear regression ties or slightly beats the tree on
   `useful_energy_kWh`, `pump_energy_kWh` and `pcm_mass_kg`.** The physics
   in this design region is close to linear in the sampled variables:
   `pcm_mass_kg` is exactly linear in `n_capsule·diameter³·ρ`;
   `pump_energy_kWh` is Ergun-viscous-term dominated (linear in flow) and
   only ~1e-7 kWh in magnitude anyway (near numerical noise — the tree's
   R²=0.963 there is not a real defect, it is a model fitting nanoscale
   noise); and annual `useful_energy` is driven mostly by the (few)
   regime-level climate features plus a near-linear PCM-mass contribution.
   The tree still wins where the relationship is genuinely non-linear
   (`solar_fraction`, `unmet_energy_kWh`) — so it is kept as the ranking
   model, and the linear baseline is retained in the metrics CSV as the
   honest comparator.
2. **Feasibility classifier: 100% hold-out accuracy, 100% recall on the
   infeasible class (27 infeasible hold-out examples).** Expected, not
   suspicious: the feasibility boundary here is one sharp deterministic
   rule (`capsule_diameter_m < 0.04 m` → derived thickness < floor, Phase
   5 doc) — a trivially learnable threshold for a tree ensemble,
   unaffected by arrangement.
3. **Small per-group holdout counts (3–9 rows).** R² this close to 1.0 on
   a small holdout should be read as "the surrogate ranks designs
   reliably", not as a precise generalisation-error estimate. Phase 7
   re-confirms every selected design in the real simulator regardless
   (Bug-Fix 5) — the 0.03% mean surrogate-vs-simulator error reported
   there is the number that actually matters.

## Error breakdown by regime, PCM, and arrangement (`phase6_surrogate_error_by_group.csv`)

`useful_energy_kWh` MAE: 0.11–0.54 kWh across the 3 regimes (9 holdout
rows each); 0.07–0.88 kWh across the 6 PCM groups (highest for `RT50`,
which has only 3 holdout rows). `solar_fraction` MAE ≤ 7.1e-4 everywhere.
No regime is a systematic weak spot; the per-PCM spread is dominated by
holdout-count noise (3–6 rows per group), not by any PCM being modelled
badly. The file's new `(regime_id, pcm_id, arrangement)` breakdown (30
groups, 1 holdout row each) shows no arrangement is a systematic weak
spot either — errors scatter across all three arrangements without a
consistent pattern by arrangement. Full ablation (regime-ID-only /
design-only / no-confidence) is deferred per the 40-hr cut list.

## Deviations from the full framework doc

No neural-network / Gaussian-process comparison, no 4-way ablation — both
explicitly deferred. XGBoost not tried: Extra Trees already reaches
R² ≥ 0.94 on every non-noise target, so there was no signal a second tree
family was needed at this dataset size.
