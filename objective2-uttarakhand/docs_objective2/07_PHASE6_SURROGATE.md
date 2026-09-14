# 07 — Phase 6 Audit: AI Surrogate Model

Files: `src/surrogate/features.py`, `src/surrogate/train.py`, `src/surrogate/evaluate.py`.
Run: `python pipeline.py --state uttarakhand --stage surrogate`.
Output: `results/uttarakhand/surrogate_metrics.csv`,
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

Climate signature (13, from `cluster_profiles_uttarakhand.csv` — continuous
features, not just an integer regime label, per framework doc §7.1):
`GHI_daily_kWh_mean, Ta_mean_true, Ta_p95_true, Ta_p05_true, DTR_true_mean,
RH_mean_true, HSI, wind_mean_true, monsoon_index, elev_proxy, Tm_target_C,
T_mains_est_C, L_required_kJ_per_kg, seasonality_proxy`.

PCM properties (11, from `pcm_database_uttarakhand.csv`, zero-filled + an
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
LinearRegression baseline on the identical train/holdout split (112
train / 30 holdout valid rows), plus one ExtraTreesClassifier for
feasibility (trained on all 215 rows, valid + invalid).

## Hold-out results (final run: post Tm-retargeting + bounds widening)

| Target | ExtraTrees RMSE | ExtraTrees R² | Linear RMSE | Linear R² | Tree beats linear? |
|---|---|---|---|---|---|
| useful_energy_kWh | 0.6148 kWh | ~1.000 | 1.776 kWh | 0.998 | Yes |
| solar_fraction | 0.0002913 | ~1.000 | 0.0009963 | ~1.000 | Yes |
| unmet_energy_kWh | 1.197 kWh | ~1.000 | 4.477 kWh | ~1.000 | Yes |
| pump_energy_kWh | 7.297e-9 kWh | 0.929 | 2.642e-10 kWh | ~1.000 | **No** |
| pcm_mass_kg | 0.2711 kg | 0.977 | 0.1451 kg | 0.994 | **No** |
| feasibility (accuracy / infeasible-recall) | 1.000 / 1.000 | — | — | — | — |

**Honest finding: linear regression ties or beats the tree for
`pump_energy_kWh` and `pcm_mass_kg`.** At the PCM volume fractions this
training set spans (up to ~16.8%, doc 13), the packed-capsule bed is still
sparse enough that the Ergun equation's *viscous* (linear-in-velocity)
term dominates for pump power. `pcm_mass_kg` is fundamentally
`density × volume_fraction × tank_volume` — an already-near-linear
relationship in the design variables the tree has to work harder to beat,
especially with the widened design space adding more PCM-mass range for a
linear fit to already capture well. This is reported as-is rather than
only showing the metric that flatters the tree-based model.

**Feasibility classifier: 100% hold-out accuracy and 100% recall on the
infeasible class (15 infeasible hold-out examples).** This is expected,
not suspicious: the feasibility boundary in this project is currently a
single, sharp, deterministic rule (`capsule_diameter_m < 0.04 m`), which
is a trivially learnable threshold for a tree ensemble given 170 training
rows spanning it.

## Error breakdown by regime and by PCM (`surrogate_error_by_group.csv`)

MAE for `useful_energy_kWh` by regime (30 holdout rows total, 6 per regime):
- Regime 0: 0.320 kWh
- Regime 1: 0.899 kWh
- Regime 2: 0.517 kWh
- Regime 3: 0.291 kWh
- Regime 4: 0.343 kWh

MAE for `useful_energy_kWh` by PCM (post-retargeting shortlist — 6
distinct PCMs, regime 1 still isolated on its own fallback shortlist):
- savE® OM42: 0.199 kWh (n=8)
- RT44HC: 0.346 kWh (n=8)
- PureTemp 53: 0.352 kWh (n=2)
- RT42: 0.557 kWh (n=8)
- Myristic acid (C14): 0.904 kWh (n=2)
- n-Hexacosane (C26): 1.441 kWh (highest, n=2 — smallest sample, only
  appears in regime 1's fallback shortlist)

No regime or PCM stands out as a systematic weak spot at a level that would
invalidate the surrogate's use as a proposal ranker for Phase 7.

## Deviations from the full framework doc

No neural-network/Gaussian-process comparison, no full 4-way ablation
(climate+PCM+design / without-confidence / regime-ID-only / design-only)
— both explicitly deferred per the reduced spec. ExtraTrees already reaches
R²>0.9998 on the primary targets, so there was no signal that a second
tree-based family was needed for this dataset size. GP uncertainty
quantification and multi-fidelity modeling remain open; see
`11_MULTIFIDELITY_SURROGATE.md` for the Phase 6b multi-fidelity
demonstration (carried over from the Tamil Nadu run, applicable here
once Phase 5 data existed).
