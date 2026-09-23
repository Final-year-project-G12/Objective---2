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
runs. Trained from the 126 valid rows of `phase5_design_cases.parquet`
(99 train / 27 holdout), using its `split` column (Phase 5). (126 valid /
99+27 split verified directly from `results/phase5_design_cases.csv` on
2026-09-18 — supersedes the pre-resync 128/101/27 figures previously
stated here.)

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
(**99 train / 27 holdout valid rows**), plus one ExtraTreesClassifier for
feasibility (trained on all non-holdout rows, valid + invalid; 54-row
holdout).

## Hold-out results (actual run)

**Re-run 2026-09-18 (post-resync) — table below replaces the pre-resync
numbers, pulled directly from `results/phase6_surrogate_metrics.csv`.**

| Target | ExtraTrees MAE | ExtraTrees RMSE | ExtraTrees R² | Linear RMSE | Linear R² | Tree beats linear? |
|---|---|---|---|---|---|---|
| useful_energy_kWh | 0.305 kWh | 0.512 kWh | **0.99998** | 0.680 kWh | 0.99996 | Yes |
| solar_fraction | 1.12e-4 | 1.81e-4 | 0.99995 | 7.39e-4 | 0.99917 | Yes |
| unmet_energy_kWh | 0.304 kWh | 0.485 kWh | 0.99997 | 1.808 kWh | 0.99954 | Yes |
| pump_energy_kWh | 9.07e-9 kWh | 1.58e-8 kWh | 0.99952 | 4.73e-9 kWh | 0.99992 | No |
| pcm_mass_kg | 0.042 kg | 0.081 kg | 0.99781 | 0.141 kg | 0.99331 | Yes |
| feasibility (accuracy / infeasible-recall) | — | — | 1.000 / 1.000 (27/27 infeasible holdout rows) | — | — | — |

### Exit check

Framework doc: hold-out R² for useful energy must clear **> 0.80** to
trust ranking (< 0.75 → add DOE cases or drop to a single target).
**Result: useful-energy hold-out R² = 0.99998 (Extra Trees), 0.99996
(linear).** Passed with a wide margin on the larger, arrangement-
stratified dataset — no extra DOE cases needed. The three "key outputs"
named in D2.5 (useful energy, solar fraction, unmet energy) all sit at
R² ≥ 0.999.

### Arrangement feature-importance diagnostic (new 2026-09-17)

| Target | arr_single_layer | arr_staggered | arr_radial | Combined |
|---|---|---|---|---|
| useful_energy_kWh | 0.000002 | 0.000001 | 0.000001 | 0.000003 |
| solar_fraction | 0.000011 | 0.000004 | 0.000010 | 0.000024 |
| unmet_energy_kWh | 0.000005 | 0.000002 | 0.000007 | 0.000014 |
| pump_energy_kWh | 0.000991 | 0.000336 | 0.000182 | 0.001509 |
| pcm_mass_kg | 0.000700 | 0.000346 | 0.000658 | 0.001704 |

(Pulled directly from `results/phase6_arrangement_importance.csv`,
2026-09-18 re-run — replaces the pre-resync values previously listed
here.)

**Finding — arrangement's feature importance is genuinely near-zero for
every target** (combined importance 0.000003–0.001704, highest for
`pcm_mass_kg` and `pump_energy_kWh`). This is not a bug: it is the direct,
consistent consequence of Phase 3's finding that `void_fraction` (the only
channel arrangement affects) is consumed solely by the hydraulics/pump-
power path, which is itself a negligible fraction of this system's total
energy balance. "Arrangement had minimal effect on every performance
target in this design-space region" is the honest, reproducible result —
reported as found, per the phase's own instruction not to treat a low
number as a sign something is broken.

### Honest findings (framework doc requires this comparison be reported as-is)

1. **Linear regression only ties/beats the tree on `pump_energy_kWh`
   in the current (2026-09-18 post-resync) run** (ET RMSE=1.58e-8 kWh vs.
   Linear RMSE=4.73e-9 kWh). `pump_energy_kWh` is Ergun-viscous-term
   dominated (linear in flow) and only ~1e-8 kWh in magnitude anyway (near
   numerical noise — the tree's R²=0.9995 there is not a real defect, it
   is a model fitting nanoscale noise). On every other target — including
   `useful_energy_kWh` and `pcm_mass_kg` — Extra Trees now has the lower
   hold-out RMSE (e.g. `pcm_mass_kg`: ET RMSE=0.081 kg vs. Linear
   RMSE=0.141 kg; `useful_energy_kWh`: ET RMSE=0.512 kWh vs. Linear
   RMSE=0.680 kWh). **This reverses the pre-resync finding stated in an
   earlier version of this doc, which had linear tying/beating on
   `useful_energy_kWh` and `pcm_mass_kg` too** — not re-derived here (no
   root-cause investigation was done into why the resync's re-shuffled/
   larger dataset changed this), flagged for anyone relying on the older
   claim. The tree is kept as the ranking model regardless, and the linear
   baseline is retained in the metrics CSV as the honest comparator.
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
   there is the number that actually matters (UNVERIFIED against the
   2026-09-18 post-resync Phase 7 outputs — this audit was scoped to
   docs 05/06 only; Phase 7's own doc should be checked separately for
   whether this figure still holds after the resync).

## Error breakdown by regime, PCM, and arrangement (`phase6_surrogate_error_by_group.csv`)

`useful_energy_kWh` MAE: 0.20–0.37 kWh across the 3 regimes (9 holdout
rows each); 0.14–0.44 kWh across the 8 PCM groups (highest for
`PureTemp 58`, which has only 3 holdout rows; `n-Heptacosane (C27)`
pools 6 holdout rows since it appears in both regimes 1 and 2 — the
pre-resync shortlist's `RT50` no longer exists post-resync). `solar_fraction`
MAE ≤ 6.2e-4 everywhere. No regime is a systematic weak spot; the per-PCM
spread is dominated by holdout-count noise (3–6 rows per group), not by
any PCM being modelled badly. The file's `(regime_id, pcm_id,
arrangement)` breakdown (27 groups with ≥1 holdout row — of 30 valid
combinations, the 3 `(regime, NONE_plain_tank, staggered)` singleton
baseline combos have none, per Phase 5's split logic — 1 holdout row each)
shows no arrangement is a systematic weak spot either — errors scatter
across all three arrangements without a consistent pattern by
arrangement. Full ablation (regime-ID-only / design-only / no-confidence)
is deferred per the 40-hr cut list.

## Deviations from the full framework doc

No neural-network / Gaussian-process comparison, no 4-way ablation — both
explicitly deferred. XGBoost not tried: Extra Trees already reaches
R² ≥ 0.997 on every non-noise target (lowest is `pcm_mass_kg` at 0.9978),
so there was no signal a second tree family was needed at this dataset
size.
