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
LinearRegression baseline on the identical train/holdout split (115
train / 30 holdout valid rows), plus one ExtraTreesClassifier for
feasibility (trained on all 215 rows, valid + invalid).

## Hold-out results (actual run)

| Target | ExtraTrees RMSE | ExtraTrees R² | Linear RMSE | Linear R² | Tree beats linear? |
|---|---|---|---|---|---|
| useful_energy_kWh | 0.540 kWh | 0.99989 | 0.668 kWh | 0.99983 | Yes |
| solar_fraction | 0.000250 | 0.99997 | 0.000370 | 0.99994 | Yes |
| unmet_energy_kWh | 0.952 kWh | 0.999998 | 1.378 kWh | 0.999995 | Yes |
| pump_energy_kWh | 4.38e-9 kWh | 0.9535 | 1.44e-10 kWh | 0.99995 | **No** |
| pcm_mass_kg | 0.0258 kg | 0.99964 | 0.0431 kg | 0.99898 | Yes |
| feasibility (accuracy / infeasible-recall) | 1.000 / 1.000 | — | — | — | — |

**Honest finding: linear regression ties or beats the tree for
`pump_energy_kWh`.** At the PCM volume fractions reachable within the
frozen bounds (≤12.9%, see Phase 2 doc), the packed-capsule bed is sparse
enough that the Ergun equation's *viscous* (linear-in-velocity) term
dominates — so pump power really is close to linear in flow rate in this
regime, and a linear model has no disadvantage. This is reported as-is
rather than only showing the metric that flatters the tree-based model.

**Feasibility classifier: 100% hold-out accuracy and 100% recall on the
infeasible class (15 infeasible hold-out examples).** This is expected,
not suspicious: the feasibility boundary in this project is currently a
single, sharp, deterministic rule (`capsule_diameter_m < 0.04 m`), which
is a trivially learnable threshold for a tree ensemble given 170 training
rows spanning it.

## Error breakdown by regime and by PCM (`surrogate_error_by_group.csv`)

MAE for `useful_energy_kWh` by regime (30 holdout rows total, 6 per regime):
- Regime 0: 0.263 kWh
- Regime 1: 0.430 kWh
- Regime 2: 0.255 kWh
- Regime 3: 0.514 kWh
- Regime 4: 0.536 kWh

MAE for `useful_energy_kWh` by PCM:
- n-Octacosane (C28): 0.201 kWh
- PureTemp 58: 0.382 kWh
- PlusICE A58: 0.422 kWh
- Palmitic-stearic acid/Expanded graphite: 0.906 kWh (highest — this PCM
  appears only in regimes 1 and 3 and has fewer training rows; noted but
  not a blocker at the overall R²>0.9998 level)

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
