# Objective 2 — Assam

Per-state Objective 2 project for Assam. Same layout and frozen shared
configs as `objective2-tamilnadu`/`objective2-rajasthan`, but the
state-specific inputs (weather, regimes, PCM shortlist, mains
temperature, demand profile) and — critically — **the actual Phase 7
optimization method and Phase 8 completion status** differ.

> This README previously described Rajasthan (300 L/day demand, RT50/
> RT45HC PCMs, "Phases 0–8 complete") with no Assam content changed.
> Rewritten below from what's actually in `results/`.

## Corrections applied 2026-11-10

Source: `.claude/Objective_1_and_Objective_2_corrected_methodology_.docx`, each item checked against the file named. **Documentation and comments only:** nothing was re-run and no result file changed. Code/config edits were comments or messages only (`configs/states/assam.yaml` header comment, `scripts/phase0_smoke_test_assam.py` print text).

- **Legacy pipeline, not reconciled with the current method, no held-out test.** Single-node tank (`src/simulation/collector_model.py:8`, "Direct-tank, single-node system"), 300 s step (`configs/system_config_shared.yaml:67`; Rajasthan uses 150 s because 300 s failed its dt-halving check), result files named `phase4`-`phase8` rather than the `g2`-`g24` chain, no selection logs and no `results/held_out_test.lock`. The method is a Phase 6 surrogate plus a bespoke Phase 7 optimisation script (`scripts/run_phase7_optimization.py`), **not** a "surrogate-assisted, constrained multi-objective search" and **not** NSGA-II with held-out validation; `docs/07_PHASE7_OPTIMIZATION.md` already says there is no NSGA-II or full active-learning loop. Its Phase 7 designs are unvalidated candidates (that doc), never "optimal".
- **Which PCMs Assam used.** Not an O1 MCDM ranking. O1 Assam has no K = 3 MCDM ranking (`PCM-Selection-ML-model/era5-assam/data/processed/pcm/mcdm_cluster_eligibility_summary.csv`: 0 confirmed in every cluster, "NOT PERFORMED"). The shortlist savE OM48 / savE OM50 / savE OM46 (`configs/states/assam.yaml`, same list for all three regimes) is, per that file's own header, taken from the O1 Phase 9/10 10-year physics-model performance (OM48 first and OM50 second on delivery), after the historical K = 4 MCDM ranking was set aside. That is a ranking by the physics model, not a validation of those PCMs (the "physics-validated" label elsewhere in these documents is replaced by "physics-ranked").
- **Point count resolved.** The O1 Assam files currently on disk have 80 points (`era5-assam/data/processed/population_grid_points.csv`: 80 rows; `clustering/cluster_assignments_assam.csv`: 80 rows; regimes 27 / 28 / 25; physics medoids ASP_0003 / ASP_0036 / ASP_0080). This folder's `data/objective1/` holds the older 129-point set (129 rows; regimes 33 / 61 / 35; medoids ASP_0012 / ASP_0092 / ASP_0028). O1's current 80-point result is the current one; this O2 copy, its weather files and everything built on them (including the contract) are from the older grid and are stale.
- **O1 inputs are a version-locked older copy.** `configs/states/assam.yaml` lines 65/75/85 carry `Tm_target_C: 44.0`; the current O1 Assam files give 56 C nominal and 49.36-50.31 C capped (`cluster_profiles_assam.csv`), and the O1 physics comparison now reads weak-to-mixed (delivery-rank rho about -0.3, solar-fraction rho about +0.6, verdict "partially supported / inconclusive"), not the "rho = -0.52 to -0.64" quoted in these documents. See the Assam O1 master overview, "Corrections applied 2026-11-10". Not reconciled.
- **Delivery target.** 45 C (`configs/system_config_shared.yaml:54`), PCM limit 65 C (line 50). O1 Assam uses 50 C (own constants).
- **Tank sizing.** 50 L (`configs/system_config_shared.yaml:25`) with 1.5 m2 (line 19) = 33.3 L/m2, below the 40-100 L/m2 of IS 12976:2023 section 4.2 (O2 decision D8, `../objective2-rajasthan/docs/05_LIMITATIONS_AND_OPEN_ITEMS.md` item 2); the 112.5 L resizing study is Rajasthan legacy-model only.
- **Terminology.** Simulator verification: Phase 4, 4 of 5 gates clean, Gate 3 fails (this folder's `docs/04_PHASE4_VERIFICATION_GATES.md`). CFD cross-check: none exists for Assam. Experimental validation: not done (Objective 4).
- **Phase 8 files were read and the docs updated.** Phase 8 outputs read 2026-11-10 (all dated 2026-09-14): `results/phase8_robustness.csv` has 3 rows (regime 0 savE OM48, regime 1 savE OM48, regime 2 savE OM46), 100 Monte Carlo draws each (not the 120 mentioned below); P(temp-safe) = 0.13 / 0.02 / 0.00 against a 0.95 requirement, P(meets delivery temp) = 1.00 / 1.00 / 0.96, P(meets annual demand) = 1.00 / 1.00 / 0.75, status "CAVEAT / NOT ROBUST" in all three. The designs behind them (`phase7_deployable_design_per_regime.csv`) have simulated PCM peaks of 66.14 / 67.73 / 69.96 C against the 65 C limit (margin -1.14 / -2.73 / -4.96 C) and 11 / 297 / 160 safety-violation sub-hours; the 13-313 / -1.2 to -5.1 C quoted elsewhere comes from `phase7_resimulation_results.csv`, a different set of re-simulated candidates. `phase7_optimization_report.md` still reports "PASSED" because it tests 95 C water / 90 C PCM limits (its section on constraints), not the frozen 75 C / 65 C. `results/obj3_environment_contract_assam.json` exists (schema v1, `sim_v1_assam`, delivery 45 C, 300 s step) but carries `Tm_target_C` 44.0 (older O1 value), the 129-point regime sizes 33 / 61 / 35, "NOT YET SPLIT" weather (one medoid year per regime, no train/validation/test years), unchosen reward weights, and a shield rationale that itself cites P(temp-safe) well below 0.95. `phase8_recommendation_cards.md` headlines the PCMs as an "Objective 1 Validated PCM Shortlist" and shows "Safety Margin to 75 C" values (-1.1 C etc.) that are actually `constraint_margin_C`, the margin to the 65 C PCM limit. Verdict: the files exist but are an unsafe-design hand-off, not a valid O3 input.
- **`docs/OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` is not a valid O3 input until Assam is re-run** on the current method (open decision c).
- **Open:** (b) 60 C versus the local delivery bases; (c) re-run Assam on the current method or keep it labelled legacy; (e) missing method citations (Sobol, XGBoost, active learning, expected improvement); the `.docx` / report files were not updated.

Start at [`docs/00_MASTER_OVERVIEW.md`](docs/00_MASTER_OVERVIEW.md) for
full phase status. **Headline, in short:**

- Phases 0–7 have been run for Assam. Phase 4 verification is a weaker
  pass than Rajasthan's (**4/5 gates clean — Gate 3 FAILS**: plain water
  beats every PCM option tried, including a synthetic PCM matched to
  the tank's own operating range).
- Phase 7 was run with a **bespoke script**
  (`scripts/run_phase7_optimization.py`), not the ported
  `src/optimize/` module used elsewhere, and its report
  (`results/phase7_optimization_report.md`) claims all 3 regimes'
  selected PCM designs "PASSED" temperature safety. **This is wrong.**
  Checked against the project's own frozen 65 °C PCM / 75 °C water
  limits, all 3 selected designs exceed the 65 °C PCM limit (margins
  −1.2 to −5.1 °C) and log 13–313 safety-violation sub-hours each. See
  [`docs/07_PHASE7_OPTIMIZATION.md`](docs/07_PHASE7_OPTIMIZATION.md),
  "The safety-verdict bug."
- **Phase 8 (robustness + recommendation cards + Objective 3 contract)
  has not been run for Assam at all.** No `results/phase8_*` files, no
  `obj3_environment_contract_assam.json`.

Do not treat `results/phase7_deployable_design_per_regime.csv` as a
validated recommendation until the safety filter is corrected — see
[`docs/OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md`](docs/OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md).

## Climate regimes (Level-A GMM, K_FINAL = 3)

| cluster_id | medoid | members | population | PCM shortlist |
|---|---|---|---|---|
| 0 | ASP_0012 (Lower Brahmaputra Valley) | 33 | 4,757,891 | savE® OM48, savE® OM50, savE® OM46 |
| 1 | ASP_0092 (Upper Assam Tea Belt) | 61 | 4,271,199 | savE® OM48, savE® OM50, savE® OM46 |
| 2 | ASP_0028 (Barak Valley & Southern Hills) | 35 | 2,466,324 | savE® OM48, savE® OM50, savE® OM46 |

This shortlist is Objective 1's **Phase 9/10 physics-ranked
candidate universe** (called "physics-validated" in `assam.yaml`; it is a ranking by O1's physics model, not a validation), not a standard MCDM Top-3 (Objective 1's own
confirmed-feasible K=3 MCDM ranking returned zero candidates — see
`configs/states/assam.yaml`'s embedded note and
`docs/00_MASTER_OVERVIEW.md`).

Mains water temperature: 15–28 °C (framework doc, Assam row); per-regime
point estimates 16.6–19.9 °C. **Demand: 100 L/day** (50 L morning +
50 L evening) — **not** 300 L/day like Rajasthan/Tamil Nadu; Assam's
absolute energy numbers are not directly comparable to theirs without
rescaling.

## How to run

### Phase 0/1 — nothing to execute separately

`configs/states/assam.yaml` is a static, already-frozen file with its
own embedded climate-signature check result (`PASSED`) — there is no
separate `results/phase0_*` report for Assam the way there is for
Rajasthan. See
[`docs/01_PHASE1_CONFIG_AND_STATE_SETUP.md`](docs/01_PHASE1_CONFIG_AND_STATE_SETUP.md).

### Phase 2 — geometry & constraint boundary self-test (state-agnostic)

```
python pipeline.py --state assam --stage geometry
```

Same engine, same 8/8-deterministic result as every other state. See
[`docs/02_PHASE2_GEOMETRY_CONSTRAINTS.md`](docs/02_PHASE2_GEOMETRY_CONSTRAINTS.md).

### Phase 3 — grey-box enthalpy simulator, one full-year case

```
python pipeline.py --state assam --stage simulate --cluster 0 \
    --pcm "savE® OM48" --diameter 0.0403 --count 24 --flow 0.046
python pipeline.py --state assam --stage simulate --cluster 1 --no-pcm
```

No standalone `results/phase3_simulate_*.json` files were saved for
Assam in this repo; see
[`docs/03_PHASE3_GREYBOX_SIMULATOR.md`](docs/03_PHASE3_GREYBOX_SIMULATOR.md)
for the closest verified numbers (Phase 4/5 outputs).

### Phase 4 — verification gate battery (Gates 1–5)

```
python pipeline.py --state assam --stage verify
```

Writes `results/phase4_simulator_verification_report_assam.txt`.
**Result: GO, but only 4/5 gates clean — Gate 3 FAILS** (plain tank
beats every PCM option, including a matched-Tm synthetic PCM). See
[`docs/04_PHASE4_VERIFICATION_GATES.md`](docs/04_PHASE4_VERIFICATION_GATES.md).

### Phase 5 — reduced DOE

```
python pipeline.py --state assam --stage doe
```

Writes `results/phase5_design_cases.csv`/`.parquet`. **Result: 111
valid / 54 infeasible-retained (all `bounds_violation`, 32.7%); 138
train / 27 holdout** — same counts as Rajasthan (same sampling
parameters, coincidentally). **79/111 valid cases (71%) exceed the
65 °C PCM safety limit**; 0/111 exceed the 75 °C water limit. See
[`docs/05_PHASE5_DOE.md`](docs/05_PHASE5_DOE.md).

### Phase 6 — tree surrogate

```
python pipeline.py --state assam --stage surrogate
```

Writes `results/phase6_surrogate_*.csv/.json` +
`results/phase6_surrogate_report.md`. **Result: useful-energy hold-out
R² = 0.9977** (29 features — fewer than Rajasthan's 39, because Assam's
Objective 1 tables carry fewer climate columns), feasibility classifier
100%/100%. See
[`docs/06_PHASE6_SURROGATE.md`](docs/06_PHASE6_SURROGATE.md).

### Phase 7 — optimization (run via a bespoke script, not `pipeline.py`)

```
python scripts/run_phase7_optimization.py
```

Writes `results/phase7_top_candidates.csv`,
`results/phase7_optimized_designs.csv`,
`results/phase7_resimulation_results.csv`,
`results/phase7_deployable_design_per_regime.csv`,
`results/phase7_optimization_report.md`. **Reported result: a PCM
design "PASSED" safety in all 3 regimes. Actual result (checked against
the frozen config): all 3 fail the 65 °C PCM limit.** See
[`docs/07_PHASE7_OPTIMIZATION.md`](docs/07_PHASE7_OPTIMIZATION.md),
"The safety-verdict bug," before citing this phase's output as
validated.

### Phase 8 — NOT RUN for Assam

```
python pipeline.py --state assam --stage robustness --mc-draws 120   # not yet run
python pipeline.py --state assam --stage handoff                      # not yet run
```

No `results/phase8_*` files or `obj3_environment_contract_assam.json`
exist. Fix Phase 7's selection first (see above), then run these. See
[`docs/08_PHASE8_ROBUSTNESS_HANDOFF.md`](docs/08_PHASE8_ROBUSTNESS_HANDOFF.md).

### Plots

```
python pipeline.py --state assam --stage plots
```

`docs/plots/` was not fully re-audited against Assam's numbers in this
pass — treat captions there with the same caution as everything else
in `docs/` before this update.
