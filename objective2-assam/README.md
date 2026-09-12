# Objective 2 — Assam

Per-state Objective 2 project for Assam. Same layout and frozen shared
configs as `objective2-tamilnadu`/`objective2-rajasthan`, but the
state-specific inputs (weather, regimes, PCM shortlist, mains
temperature, demand profile) and — critically — **the actual Phase 7
optimization method and Phase 8 completion status** differ.

> This README previously described Rajasthan (300 L/day demand, RT50/
> RT45HC PCMs, "Phases 0–8 complete") with no Assam content changed.
> Rewritten below from what's actually in `results/`.

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

This shortlist is Objective 1's **Phase 9/10 physics-validated
candidate universe**, not a standard MCDM Top-3 (Objective 1's own
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
