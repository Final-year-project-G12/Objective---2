# 08 — Phase 8 Audit: Robustness + Recommendation Cards + Objective 3 Handoff (Assam)

**Status: NOT RUN.** This doc previously contained Rajasthan's Phase 8
numbers (120 Monte Carlo draws/regime, P(temp-safe) 0.45–0.57, an
`obj3_environment_contract_rajasthan.json`) copy-pasted with no Assam
content changed. There is no equivalent Assam output anywhere in this
repo:

- No `results/phase8_robustness.csv` or `_robustness_draws.csv`.
- No `results/phase8_recommendation_cards.md`.
- No `results/obj3_environment_contract_assam.json`.

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
