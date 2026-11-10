# 08 — Phase 8 Audit: Robustness + Recommendation Cards + Objective 3 Handoff (Assam)

> **Legacy pipeline (label added 2026-11-10): not reconciled with the current method, no held-out test.** Single-node tank, 300 s step, no selection logs, no `held_out_test.lock`; not a surrogate-assisted NSGA-II search with held-out validation. See "Corrections applied 2026-11-10" in `README.md`.

**Status (corrected 2026-11-10): RUN on 2026-09-14; outputs exist but are not a valid hand-off.** Phase 8 outputs read 2026-11-10 (all dated 2026-09-14): `results/phase8_robustness.csv` has 3 rows (regime 0 savE OM48, regime 1 savE OM48, regime 2 savE OM46), 100 Monte Carlo draws each (not the 120 mentioned below); P(temp-safe) = 0.13 / 0.02 / 0.00 against a 0.95 requirement, P(meets delivery temp) = 1.00 / 1.00 / 0.96, P(meets annual demand) = 1.00 / 1.00 / 0.75, status "CAVEAT / NOT ROBUST" in all three. The designs behind them (`phase7_deployable_design_per_regime.csv`) have simulated PCM peaks of 66.14 / 67.73 / 69.96 C against the 65 C limit (margin -1.14 / -2.73 / -4.96 C) and 11 / 297 / 160 safety-violation sub-hours; the 13-313 / -1.2 to -5.1 C quoted elsewhere comes from `phase7_resimulation_results.csv`, a different set of re-simulated candidates. `phase7_optimization_report.md` still reports "PASSED" because it tests 95 C water / 90 C PCM limits (its section on constraints), not the frozen 75 C / 65 C. `results/obj3_environment_contract_assam.json` exists (schema v1, `sim_v1_assam`, delivery 45 C, 300 s step) but carries `Tm_target_C` 44.0 (older O1 value), the 129-point regime sizes 33 / 61 / 35, "NOT YET SPLIT" weather (one medoid year per regime, no train/validation/test years), unchosen reward weights, and a shield rationale that itself cites P(temp-safe) well below 0.95. `phase8_recommendation_cards.md` headlines the PCMs as an "Objective 1 Validated PCM Shortlist" and shows "Safety Margin to 75 C" values (-1.1 C etc.) that are actually `constraint_margin_C`, the margin to the 65 C PCM limit. Verdict: the files exist but are an unsafe-design hand-off, not a valid O3 input. The text below was written 2026-09-12, before those files existed, and is kept as history.

**Original status line: NOT RUN.** This doc previously contained Rajasthan's Phase 8
numbers (120 Monte Carlo draws/regime, P(temp-safe) 0.45–0.57, an
`obj3_environment_contract_rajasthan.json`) copy-pasted with no Assam
content changed. There is no equivalent Assam output anywhere in this
repo:

- (Written 2026-09-12; now exist) `results/phase8_robustness.csv` and `_robustness_draws.csv`.
- (Written 2026-09-12; now exists) `results/phase8_recommendation_cards.md`.
- (Written 2026-09-12; now exists) `results/obj3_environment_contract_assam.json`.

The code this stage needs already exists and is untouched/ported:
`src/robustness/monte_carlo.py` (`run_all(state, n_draws)`),
`src/handoff/build_recommendation_cards.py` and
`src/handoff/build_obj3_contract.py` (both `run(state)`). Nothing about
these files is Assam-specific or broken — they simply have not been
invoked for `state="assam"` yet.

## Why this should wait for the Phase 7 fix

Running Monte Carlo robustness and building the Objective 3 contract on
top of Assam's current `phase7_deployable_design_per_regime.csv` would
be running Phase 8 against **3 designs that already fail this project's
own frozen 65 °C PCM safety limit before any weather/demand noise is
added** (see `07_PHASE7_OPTIMIZATION.md`, "The safety-verdict bug").
Every one of those designs already has 13–313 flagged safety-violation
sub-hours in the nominal (non-perturbed) simulation. Running Phase 8 on
them now would produce P(temp-safe) numbers that are misleadingly framed
as "how often does this design fail under uncertainty" when the honest
framing is "this design is not the deployable design yet."

## How to actually run it once Phase 7 is fixed

```
python pipeline.py --state assam --stage robustness --mc-draws 120
python pipeline.py --state assam --stage handoff
```

This will need `phase7_deployable_design_per_regime.csv` to be
regenerated first (see `07_…`'s recommended fix — filter Assam's 12,000
candidates through the correct 65 °C/75 °C rule before applying the
5%-near-best selection). Once that produces a design per regime that
genuinely clears the safety filter in the nominal simulation, Phase 8
can run exactly as documented for Rajasthan
(`objective2-rajasthan/docs/08_PHASE8_ROBUSTNESS_HANDOFF.md` — a good
template for structure/methodology, not for Assam's numbers, which do
not exist yet).

## What Objective 3 should NOT assume

Do not read `docs/OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` for Assam and
expect a contract file to exist — it has also been corrected in this
pass to say so explicitly. There is currently **no valid Objective 3
hand-off artifact for Assam.**
