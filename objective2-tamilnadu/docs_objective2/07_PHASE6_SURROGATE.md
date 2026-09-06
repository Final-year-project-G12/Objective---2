# 07 — Phase 6 Audit: AI Surrogate Model

Files: `src/surrogate/features.py`, `src/surrogate/train.py`, `src/surrogate/evaluate.py`.
Run: `python pipeline.py --state tamilnadu --stage surrogate`.
Output: `results/tamilnadu/surrogate_metrics.csv`,
`surrogate_error_by_group.csv`, `surrogate/models.pkl`.

## Purpose (D2.5)

One combined tree-based surrogate (no ablation, per the framework doc's
reduced 40-hr spec) so Phase 7's optimization pass doesn't need thousands
of physics runs. **The surrogate is a proposal ranker, not the final
oracle** (Bug-Fix 5) — every design it favors gets re-run in the real
simulator before anything is reported (Phase 7).

## Features (36 total)

Design + geometry (9): `capsule_diameter_m, n_capsule, flow_rate_kg_s,
geom_pcm_thickness_m, geom_pcm_volume_fraction, geom_void_fraction,
geom_pressure_drop_pa, geom_pump_power_w, geom_reynolds_number_particle`.

Climate signature (13, from `cluster_profiles_tamilnadu.csv` — continuous
features, not just an integer regime label, per framework doc §7.1):
`GHI_daily_kWh_mean, Ta_mean_true, Ta_p95_true, Ta_p05_true, DTR_true_mean,
RH_mean_true, HSI, wind_mean_true, monsoon_index, elev_proxy, Tm_target_C,
T_mains_est_C, L_required_kJ_per_kg, seasonality_proxy`.

PCM properties (11, from `pcm_database_tamilnadu.csv`, zero-filled + an
explicit `is_no_pcm` flag for the plain-tank baseline so "no PCM" is never
confused with "a PCM with zero latent heat"): `Tm_C, latent_heat_kJ_kg,
TC_W_mK, density_liquid_kg_m3, density_solid_kg_m3, Cp_liquid_kJ_kgK,
Cp_solid_kJ_kgK, cycles_confidence, supercooling_K, rho_H_MJ_m3,
any_property_imputed`.

Objective 1 confidence (1): `top3_inclusion_probability` from
`monte_carlo_stability.csv` — a material-selection uncertainty feature,
never substituted for an actual thermophysical property (framework doc §2.3).

## Models trained

ExtraTreesRegressor (300 trees) per target, each compared against a plain
LinearRegression baseline on the identical train/holdout split (115
train / 30 holdout valid rows), plus one ExtraTreesClassifier for
feasibility (trained on all 215 rows, valid + invalid).

## Hold-out results (actual run)

| Target | ExtraTrees RMSE | ExtraTrees R² | Linear RMSE | Linear R² | Tree beats linear? |
|---|---|---|---|---|---|
| useful_energy_kWh | 0.708 kWh | 0.9999 | 0.810 kWh | 0.9999 | Yes |
| solar_fraction | 0.00035 | 0.9990 | 0.00112 | 0.9897 | Yes |
| unmet_energy_kWh | 1.235 kWh | 0.9997 | 2.926 kWh | 0.9983 | Yes |
| pump_energy_kWh | 2.38e-9 kWh | 0.9872 | 1.93e-10 kWh | 0.99992 | **No** |
| pcm_mass_kg | 0.057 kg | 0.9979 | 0.100 kg | 0.9933 | Yes |
| feasibility (accuracy / infeasible-recall) | 1.000 / 1.000 | — | — | — | — |

**Honest finding: linear regression ties or beats the tree for
`pump_energy_kWh`.** At the PCM volume fractions reachable within the
frozen bounds (≤12.9%, see Phase 2 doc), the packed-capsule bed is sparse
enough that the Ergun equation's *viscous* (linear-in-velocity) term
dominates over its *inertial* (quadratic) term — so pump power really is
close to linear in flow rate in this regime, and a linear model has no
disadvantage. This is reported as-is rather than only showing the metric
that flatters the tree-based model, per the framework doc's explicit
instruction to run this comparison and report it honestly.

**Feasibility classifier: 100% hold-out accuracy and 100% recall on the
infeasible class (15 infeasible hold-out examples).** This is expected,
not suspicious: the feasibility boundary in this project is currently a
single, sharp, deterministic rule (`capsule_diameter_m < 0.04 m` — see
Phase 5 doc), which is a trivially learnable threshold for a tree
ensemble given 170 training rows spanning it.

Note the fix that was needed to get a meaningful `infeasible_recall` at
all: the first version of `split_cases.py` only split the *valid* rows
into train/holdout, so the holdout set the classifier was scored on had
**zero** infeasible examples (`recall = nan`). Fixed by stratifying the
split on `(regime_id, pcm_id, valid)` instead of just `(regime_id,
pcm_id)` — see Phase 5 doc.

## Error breakdown by regime and by PCM (`surrogate_error_by_group.csv`)

MAE for `useful_energy_kWh` ranges 0.22–0.83 kWh across the 5 regimes and
0.34–0.79 kWh across the 4 PCM/baseline groups — no regime or PCM stands
out as a systematic weak spot (framework doc §7.4's "error by state and
climate regime ... error by PCM candidate", reduced scope — full ablation
against a regime-ID-only or design-only baseline is deferred, per the
40-hr cut list).

## Deviations from the full framework doc

No neural-network/Gaussian-process comparison, no full 4-way ablation
(climate+PCM+design / without-confidence / regime-ID-only / design-only)
— both explicitly deferred per the reduced spec. XGBoost was not tried;
Extra Trees already reaches R²>0.98 on every target, so there was no
signal that a second tree-based family was needed for this dataset size.
