# 17 — Capsule Arrangement Restored as a Searched Variable (2026-09-17)

**Status: RESOLVED / APPLIED, all 8 phases.** This is a summary/index doc
— the detailed per-phase mechanics and results are in
`docs_objective2/tamilnadu_phase_docs/01`–`08_*_TAMILNADU.md`. Adapted
from a change plan originally written and piloted against a sibling
Rajasthan codebase
(`a Rajasthan-pilot change plan (source removed from this project after adaptation, see docs_objective2/tamilnadu_phase_docs/)`).

## What was wrong

`design_bounds_shared.yaml` froze **both** capsule shape (sphere) and
capsule arrangement (staggered) as one combined "40-hr scope cut." Freezing
shape is correct — it's never named in the objective statement. Freezing
arrangement was not: the objective statement explicitly names "capsule
arrangement" as one of the four quantities Objective 2 must determine
(PCM thickness, capsule arrangement, number of capsules, flow rate). Every
recommendation card and the Objective 3 contract, before this fix, reported
"staggered" as if it had been searched, when it had in fact never been
compared against anything.

## What changed, phase by phase

| Phase | Change |
|---|---|
| 1 | `design_bounds_shared.yaml` gained a 3-way categorical `capsule_arrangement` bound (`single-layer`/`staggered`/`radial`); `schema.py`'s `DesignVector.capsule_arrangement` lost its default and became a required, explicitly-passed field |
| 2 | `geometry.py` gained 3 packing models (`pack_staggered`, `pack_single_layer`, `pack_radial`) behind a `pack_capsules()` dispatcher, each with genuinely different unit-cell porosity (see the real bug found and fixed below); `get_max_reachable_pcm_fraction()` added |
| 3 | `run_case.py` gained a pass-through `arrangement` field in its metrics dict — no physics submodel branches on arrangement |
| 4 | `gates.py`'s Gates 1–3 expanded to cover all three arrangements; simulator re-tagged `sim_v2_tamilnadu` |
| 5 | DOE stratified 3-way by arrangement (12 LHS + 12 boundary per pair, up from 8+6 staggered-only); rejection-rate reporting broken out by arrangement |
| 6 | Surrogate gained a 3-column arrangement one-hot feature + a dedicated arrangement feature-importance diagnostic |
| 7 | Candidate search samples arrangement (400→600 candidates/pair); winners get an `arrangement_rationale` field |
| 8 | Recommendation cards + Objective 3 contract carry the winning arrangement and its rationale; robustness Monte Carlo re-run against the arrangement-searched winners |

## A real physics bug found while restoring this (not anticipated by the change plan)

The first implementation computed `void_fraction` from the *bulk* dilution
formula `1 − pcm_volume_fraction`, which depends only on (diameter, count)
— **identical for every arrangement**. This failed the required
cross-arrangement sanity check (the same design run under all three
arrangements must NOT produce identical `void_fraction`/`pressure_drop_pa`).
Fixed by redefining `void_fraction` as each packing pattern's own
**unit-cell porosity**: `1 − capsule_volume / (footprint_area_per_capsule ×
layer_pitch)` — a bed-characteristic constant for the packing type (the
physically correct quantity for the Ergun equation), not a dilution figure.
Sanity check: the square-grid (single-layer) pattern gives 0.476 void
fraction under this model, matching the textbook simple-cubic
sphere-packing porosity exactly.

## Headline finding

Phase 2 found radial packing geometrically capped well below the other two
(max reachable PCM-volume fraction 11.3% vs 19.8%) — yet Phase 7's search
selected **radial in all three regimes**, honestly qualified: 2 of 3 wins
are "tied within noise" against single-layer, and the third regime's
surrogate top-20 pool was 100% radial candidates (no other arrangement to
compare). This is reported as a real, checked finding — not smoothed into
an overclaimed "radial is definitively best" — see
`docs_objective2/tamilnadu_phase_docs/07_PROMPT_PHASE7_OPTIMIZE_TAMILNADU.md`.

## What this resolves

- Every prior recommendation card / `obj3_environment_contract_tamilnadu.json`
  reporting `"capsule_arrangement": "staggered"` as if searched is
  superseded — see the contract's own `supersession_note` field.
- The `deferred_future_work` item "arrangement search" (implicit in the
  hardcoded staggered-only design blocks) no longer applies.
- Not yet done: the identical change for Rajasthan, Assam, and Uttarakhand
  — required before any four-state comparison is valid again (per
  `a Rajasthan-pilot change plan (source removed from this project after adaptation, see docs_objective2/tamilnadu_phase_docs/)`'s cross-state checks).
