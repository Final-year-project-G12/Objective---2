# Phase 6 Plots — Surrogate Model (Rajasthan)

Files: `phase6_parity_plots.*`, `phase6_feature_importance.*`. Data
source: `results/phase6_surrogate_models.pkl` + the hold-out rows of
`phase5_design_cases.parquet`.

## Plot 1 — Surrogate parity plots (hold-out set, n = 18)

**What it is**: two scatter panels — simulator value (x) vs
surrogate-predicted value (y) for `useful_energy_kWh` and
`solar_fraction`, on the 18 valid hold-out cases, with the y = x parity
line.

**What we infer**: every point sits essentially *on* the parity line —
the R² ≈ 0.9998 / 0.9996 reported in `06_PHASE6_SURROGATE.md` made
visual. No systematic bias (points not consistently above or below the
line), no fan-out at the extremes.

**How to justify it**: *"You don't have to trust the R² number in the
table — the points are visibly on the line. With only 18 hold-out rows
this says 'the surrogate ranks designs reliably', which is all Phase 7
needs it for; Phase 7 re-confirms every selected design in the real
simulator anyway (Bug-Fix 5)."*

## Plot 2 — Top-15 feature importances (`useful_energy_kWh` model)

**What it is**: a horizontal bar chart of the 15 highest ExtraTrees
feature importances for the annual-useful-energy model.

**What we infer**: the top features are all **climate-signature**
columns — `Ta_p95`, `Ta_mean`, `wind_noon_mean`, `kt_daily_mean`,
`T_mains_est_C`, `RH_sunrise_mean` — not the design variables
(`capsule_diameter_m`, `n_capsule`, `flow_rate_kg_s`). That is the
expected physical story at this scale: with only 3 regimes and ≤12.9 %
PCM fraction, annual useful energy is set mostly by *which climate* the
design sits in, and only weakly by the geometry within a regime.

**How to justify it**: *"The surrogate learned the same thing Phases 4–7
found by other means — climate dominates annual useful energy here, and
the PCM/geometry knobs barely move it. That the model puts continuous
Objective 1 climate features on top (rather than an integer regime label)
is exactly the framework doc §7.1 design goal."*
