# Objective 3 — Inputs From Objective 2 and What To Do Next (Assam)

> **Legacy pipeline (label added 2026-11-10): not reconciled with the current method, no held-out test.** Single-node tank, 300 s step, no selection logs, no `held_out_test.lock`; not a surrogate-assisted NSGA-II search with held-out validation. See "Corrections applied 2026-11-10" in `README.md`.

> **NOT A VALID OBJECTIVE 3 INPUT until Assam is re-run on the current method (2026-11-10).** The Phase 7 designs are unvalidated candidates (safety verdict issue below), O1 inputs are an older version-locked copy, and there is no held-out test.

**Objective 2 is NOT complete for Assam.** This doc previously described
Rajasthan's finished hand-off (`obj3_environment_contract_rajasthan.json`)
with no Assam-specific content — that was wrong. For Assam:

- Phases 0–7 have been run (with two open issues, below).
- **Phase 8 outputs exist (corrected 2026-11-10; dated 2026-09-14) but are not usable**: Phase 8 outputs read 2026-11-10 (all dated 2026-09-14): `results/phase8_robustness.csv` has 3 rows (regime 0 savE OM48, regime 1 savE OM48, regime 2 savE OM46), 100 Monte Carlo draws each (not the 120 mentioned below); P(temp-safe) = 0.13 / 0.02 / 0.00 against a 0.95 requirement, P(meets delivery temp) = 1.00 / 1.00 / 0.96, P(meets annual demand) = 1.00 / 1.00 / 0.75, status "CAVEAT / NOT ROBUST" in all three. The designs behind them (`phase7_deployable_design_per_regime.csv`) have simulated PCM peaks of 66.14 / 67.73 / 69.96 C against the 65 C limit (margin -1.14 / -2.73 / -4.96 C) and 11 / 297 / 160 safety-violation sub-hours; the 13-313 / -1.2 to -5.1 C quoted elsewhere comes from `phase7_resimulation_results.csv`, a different set of re-simulated candidates. `phase7_optimization_report.md` still reports "PASSED" because it tests 95 C water / 90 C PCM limits (its section on constraints), not the frozen 75 C / 65 C. `results/obj3_environment_contract_assam.json` exists (schema v1, `sim_v1_assam`, delivery 45 C, 300 s step) but carries `Tm_target_C` 44.0 (older O1 value), the 129-point regime sizes 33 / 61 / 35, "NOT YET SPLIT" weather (one medoid year per regime, no train/validation/test years), unchosen reward weights, and a shield rationale that itself cites P(temp-safe) well below 0.95. `phase8_recommendation_cards.md` headlines the PCMs as an "Objective 1 Validated PCM Shortlist" and shows "Safety Margin to 75 C" values (-1.1 C etc.) that are actually `constraint_margin_C`, the margin to the 65 C PCM limit. Verdict: the files exist but are an unsafe-design hand-off, not a valid O3 input.
- **(Superseded: the file now exists in `results/`, but see above and do not train on it.)** Earlier text: there is no `obj3_environment_contract_assam.json` file anywhere in
  this repo.** Objective 3 has nothing to consume for Assam yet.

## 1. What's actually blocking the hand-off

Two issues found while auditing `results/` against the docs, both must
be resolved before an Assam contract can be trusted:

1. **Phase 7's safety verdict is wrong** — Assam's 3 "deployable" PCM
   designs all exceed the frozen 65 °C PCM safety limit (margins −1.2 to
   −5.1 °C) and log 13–313 safety-violation sub-hours each in the
   *nominal* (non-perturbed) simulation, but
   `results/phase7_optimization_report.md` reports them as "PASSED"
   against an invented 90 °C/95 °C standard instead of the real one. See
   `07_PHASE7_OPTIMIZATION.md`, "The safety-verdict bug," for the full
   trace of where this went wrong (`scripts/run_phase7_optimization.py`
   computes the correct negative margin, then the report template
   prints a hardcoded PASS against a different number).
2. **Phase 8 (Monte Carlo robustness + recommendation cards + the
   contract itself) has never been run for Assam.** The code exists and
   is untouched (`src/robustness/`, `src/handoff/`) — it just needs
   `--state assam` invoked, once (1) is fixed.

## 2. What Objective 2 is telling Objective 3 so far (provisional)

Even without a finished contract, a few things are already clear from
Phases 4–7 and worth knowing before Objective 3 starts its own design
work:

- **Assam's demand is 100 L/day (50 L morning + 50 L evening), not
  300 L/day** like Rajasthan/Tamil Nadu. Any reward-function energy
  scale ported from another state's Objective 3 work must be rescaled.
- **Gate 3 (Phase 4) already showed plain water beating every PCM
  option tried, including a synthetic PCM matched to the tank's own
  operating range** (`04_PHASE4_VERIFICATION_GATES.md`). This is a
  stronger warning than Rajasthan or Tamil Nadu saw at this checkpoint.
  Objective 3 should not assume Assam's controller will have meaningful
  latent-heat dynamics to exploit until Phase 7 is re-run with the
  correct safety filter and a design actually clears it.
- **If the corrected Phase 7 forces a plain tank in some or all
  regimes** (the likely outcome, given Gate 3 and the negative PCM
  margins above, and consistent with Rajasthan's outcome under the same
  rule), the controller for those regimes will again be a conventional
  water heater with no phase-change dynamics — same implication as
  Rajasthan's hand-off doc describes for its 3 regimes.
- **No auxiliary/backup heater exists in this system** (same as every
  other state) — "unmet energy" means genuinely undelivered heat.
- **A real safety shield does not exist in the physics model** — the
  simulator records violations, it doesn't prevent them. Given that
  Assam's *nominal* (unperturbed) designs already violate the PCM limit
  before any weather/demand noise is even added, an active
  high-temperature bypass is very likely to be at least as urgent a
  requirement here as it was for Rajasthan (P(temp-safe) 0.45–0.57
  there, on designs that started from a genuinely safe nominal point —
  Assam's nominal point is already unsafe).

## 3. Concrete first steps — in order

1. **Do not start Objective 3 controller work for Assam from
   `phase7_deployable_design_per_regime.csv` as it stands.** It is not
   a validated design set.
2. **Fix Phase 7's selection** (see `07_…`'s recommendation: filter the
   existing 7,966-candidate feasible pool through the real 65 °C/75 °C
   rule before applying the 5%-near-best ranking) and regenerate
   `phase7_deployable_design_per_regime.csv`.
3. **Run Phase 8** (`python pipeline.py --state assam --stage
   robustness --mc-draws 120` then `--stage handoff`) on the corrected
   designs to produce `obj3_environment_contract_assam.json`.
4. **Then** follow the same steps Rajasthan's hand-off doc lays out
   (`objective2-rajasthan/docs/OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md`,
   §3) — load the contract, implement the safety shield first, build a
   step-by-step simulator interface, freeze reward weights, run the
   acceptance test with a trivial rule-based controller before any
   learning code.

## 4. What Objective 2 explicitly has not resolved for Assam

- The two open issues in §1 above.
- No unseen-weather-year or member-point re-confirmation (medoid-only,
  same 40-hr cut-list deferral as every other state).
- Objective 1's PCM shortlist for Assam is not a standard MCDM Top-3 —
  it's a Phase 9/10 physics-ranked substitute (a ranking by O1's physics model, not a validation), because Objective 1's
  own confirmed-feasible K=3 MCDM ranking returned zero candidates (see
  `00_MASTER_OVERVIEW.md`). If Objective 1 revisits this, Assam's
  Objective 2 phases 5–7 would need re-running against a new shortlist.
