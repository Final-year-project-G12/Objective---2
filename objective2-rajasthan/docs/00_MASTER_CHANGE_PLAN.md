# 00 — Master Change Plan: Restoring Arrangement as a Searched Variable

**Scope:** `objective2-rajasthan/` (and, once verified here, the identical edit ported to
`objective2-tamilnadu/`, `objective2-assam/`, `objective2-uttarakhand/`). This plan closes the
single gap between the current Rajasthan implementation and `Objective2_Consolidated_Plan.md`:
**capsule arrangement is frozen to sphere/staggered-only; it must become a searched categorical
variable (`single-layer`/`staggered`/`radial`)**, matching the objective statement's four named
parameters.

## What is *not* broken and does not need fixing

Confirmed from the audit docs — do not re-touch these:
- **Thickness is already derived correctly** (`pcm_thickness_m = diameter/2` in `geometry.py`),
  never sampled independently. The "impossible dimension" bug the consolidated plan warned about
  does not exist in this codebase. No change needed here.
- Randomized-search-ranked-by-surrogate, single-pass (no NSGA-II/active learning), simulator as
  final authority, ambient tank-loss term, 5% Pareto tolerance, >15% surrogate-error rule,
  PCM-only selection pool, safety-shield default — all correct per the consolidated plan and
  already implemented. Leave alone.

## What changes, and why it cascades through every phase

Arrangement determines packing geometry (`capsules_per_layer`, void fraction, pressure drop),
which Phase 2 computes and every later phase consumes. Because it was previously a *constant*
baked into one code path (staggered only), making it a *variable* touches:

| Phase | What changes | What doesn't |
|---|---|---|
| 1 | `design_bounds_shared.yaml` gains an arrangement enum; count bound reconsidered | Regime/PCM/demand/mains config (all state-specific, untouched) |
| 2 | Geometry engine gains 2 new packing branches (single-layer, radial) | Reason-code set, determinism requirement |
| 3 | Nothing (arrangement is geometry-consumed, not physics-consumed) — add pass-through logging only | All physics submodels |
| 4 | Gate case sets expand to cover 3 arrangements; simulator re-tagged `sim_v2_<state>` | Gate pass/fail logic and thresholds |
| 5 | DOE stratified 3-way by arrangement; case counts and rejection-rate reporting change shape | Sampling method (LHS + boundary + baseline) |
| 6 | Arrangement one-hot feature added; new arrangement-importance diagnostic | Model family, train/holdout logic |
| 7 | Candidate generator samples arrangement; winner gets an arrangement rationale field | Selection rule, safety shield, PCM-only pool |
| 8 | Recommendation cards + O3 contract gain an arrangement field; robustness reruns | Robustness methodology, draw counts |

## Required execution order

Run phases **2 → 8 in sequence** for Rajasthan (Phase 1's config edit is a prerequisite, not a
rerun step — do it once, first). Do not skip ahead: Phase 5's DOE depends on Phase 2's new
per-arrangement reachable-fraction numbers; Phase 6 depends on Phase 5's arrangement column;
Phase 7 depends on Phase 6's retrained surrogate; Phase 8 depends on Phase 7's new winners.

```
Phase 1 (config edit, once)
   → Phase 2 (geometry engine + re-verify bounds)
   → Phase 3 (pass-through logging + arrangement smoke runs)
   → Phase 4 (re-verify gates, version bump to sim_v2)
   → Phase 5 (arrangement-stratified DOE)
   → Phase 6 (surrogate with arrangement feature)
   → Phase 7 (search spans arrangement, rationale reported)
   → Phase 8 (cards + O3 contract updated, robustness rerun)
```

## Cross-cutting rule this whole change must respect

`design_bounds_shared.yaml` is a **shared, frozen-and-hashed file across all four states**. This
change edits it. Per the project's own rule ("no state may modify shared config independently"),
the Phase 1 edit below must be applied identically to Tamil Nadu, Assam, and Uttarakhand's copies
before any of them re-run — even though this change plan is being executed against Rajasthan
first as the pilot state. Until all four states complete their own Phase 2–8 rerun, **any existing
cross-state comparison artifact is stale** and must not be cited as final.

## Status — COMPLETE for Rajasthan (2026-09-17)

All 8 phases below have been executed for Rajasthan and are documented, with actual results, in
this project's own `docs/0N_PHASEN_*.md` files (not the one-off prompt files this plan originally
shipped with — those have been deleted now that the work they specified is done; see "Files in
this set" below). `obj3_environment_contract_rajasthan.json` has been regenerated with arrangement
included and is a frozen hand-off, not a working draft — see `docs/08_PHASE8_ROBUSTNESS_HANDOFF.md`
and `docs/OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md`.

**Still open:** Tamil Nadu, Assam, and Uttarakhand have not received this same change — see the
cross-cutting rule above and `docs/09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md` §9.

## Files in this set

The original per-phase prompt files this plan shipped with
(`01_PROMPT_PHASE1_CONFIG.md` through `08_PROMPT_PHASE8_HANDOFF.md`) have been deleted — the work
they specified is done, and their content (rationale, implementation notes, actual exit-check
results) now lives in the corresponding phase doc:

| Phase | Covers | Result documented in |
|---|---|---|
| 1 | `design_bounds_shared.yaml`, `schema.py` | `docs/01_PHASE1_CONFIG_AND_STATE_SETUP.md` |
| 2 | `geometry.py`, `constraints.py` | `docs/02_PHASE2_GEOMETRY_CONSTRAINTS.md` |
| 3 | `run_case.py` pass-through, smoke runs | `docs/03_PHASE3_GREYBOX_SIMULATOR.md` |
| 4 | `gates.py`, version bump | `docs/04_PHASE4_VERIFICATION_GATES.md` |
| 5 | `generate_cases.py`, `run_batch.py`, `split_cases.py` | `docs/05_PHASE5_DOE.md` |
| 6 | `features.py`, `train.py`, `evaluate.py` | `docs/06_PHASE6_SURROGATE.md` |
| 7 | `search.py`, `select_deployable.py` | `docs/07_PHASE7_OPTIMIZATION.md` |
| 8 | recommendation cards, `build_obj3_contract.py`, robustness | `docs/08_PHASE8_ROBUSTNESS_HANDOFF.md` |

This document (`00_MASTER_CHANGE_PLAN.md`) is kept as the record of *why* and *what was planned*;
the phase docs above are the record of *what actually happened*, with real numbers.

