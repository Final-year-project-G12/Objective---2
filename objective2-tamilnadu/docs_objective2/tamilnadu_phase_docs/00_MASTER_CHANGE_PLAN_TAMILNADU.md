# 00 — Master Change Plan (Tamil Nadu): Restoring Arrangement + Refreshing Objective 1 Data

> **2026-09-18 update:** the "Tm-retargeting + MCDM re-ranking" step
> described in this doc and in `01_PROMPT_PHASE1_CONFIG_TAMILNADU.md`
> (step 2 below) was found to violate the project's own objective
> statements — it had Objective 2 silently substituting its own re-derived
> PCM choice for Objective 1's actual shortlist. That mechanism is
> **superseded**: `configs/states/tamilnadu.yaml` now carries Objective
> 1's own unedited `Tm_target_C`/`pcm_shortlist`, and Phases 5-8 were
> re-run against it. See
> `../18_OBJECTIVE1_SHORTLIST_RESTORED.md` for the full correction and
> final results. Steps 1 and 3 below (Objective 1 data refresh, arrangement
> restoration) are unaffected and remain exactly as described.

**Scope:** `objective2_design_optimization/` (Tamil Nadu). Adapted from
`a Rajasthan-pilot change plan (source removed from this project after adaptation, see docs_objective2/tamilnadu_phase_docs/)`, which was written
against a sibling Rajasthan codebase. This version documents what was
**actually run** against the real Tamil Nadu implementation in this folder,
combining two changes that landed together on 2026-09-17:

1. **Objective 1 data refresh** — `tamilnadu_pipeline` (the sibling Objective 1
   project, read-only from here) was re-run with updated scripts. Its outputs
   changed substantially: GMM regime count K=5 → **K=3**, `Tm_target_C`
   57.0°C → **67.0°C** (climate-anchored, pre-Obj2-retargeting), a real
   elevation field (was a flat 150 m placeholder), a rewritten MCDM engine
   (new `mcdm_full_rankings.csv`/`mcdm_method_agreement.csv`), and a
   **kappa-calibrated** feasibility-rescue mechanism that the old strict
   latent-heat floor did not have.
2. **Capsule arrangement restored as a searched variable** — `single-layer`/
   `staggered`/`radial`, previously frozen to staggered-only. This is the
   same conceptual change `01-08_PROMPT_PHASE*.md` describe for Rajasthan,
   ported here.

## What is *not* broken and does not need fixing (confirmed for Tamil Nadu too)

- Thickness is still derived correctly (`pcm_thickness_m = diameter/2`), never
  sampled independently.
- The randomized-search-ranked-by-surrogate methodology, simulator-as-final-
  authority rule, ambient tank-loss term, 5% Pareto tolerance, >15%
  surrogate-error rule, and PCM-only selection pool are all still correct as
  implemented in the pre-2026-09-17 Tamil Nadu build. Leave alone (re-verify
  in Phase 4-7, don't redesign).

## Required execution order (identical structure to the Rajasthan plan)

```
Phase 0 (data refresh, once)     -- rebuild data/objective1/ from tamilnadu_pipeline,
                                     rebuild data/weather/ for K=3, rebuild
                                     configs/states/tamilnadu.yaml, re-run
                                     retarget_tm.py + mcdm_reranking.py --apply
Phase 1 (config edit, once)      -- design_bounds_shared.yaml gains the arrangement
                                     categorical bound; schema.py requires it
   → Phase 2 (geometry engine + re-verify bounds)
   → Phase 3 (pass-through logging + arrangement smoke runs)
   → Phase 4 (re-verify gates, version bump to sim_v2_tamilnadu)
   → Phase 5 (arrangement-stratified DOE, against fresh regimes/PCMs)
   → Phase 6 (surrogate with arrangement feature, retrained on fresh DOE)
   → Phase 7 (search spans arrangement, rationale reported)
   → Phase 8 (cards + O3 contract updated, robustness rerun)
```

Batched per the user's instruction: **Phases 1-4 first** (this batch),
**Phases 5-8 second** (next batch). Docs/plots updates deferred to after all
8 phases land.

## Cross-cutting rule this change must respect

`design_bounds_shared.yaml` is shared across all four states (Tamil Nadu,
Rajasthan, Assam, Uttarakhand). The arrangement edit here is applied to
**this project's copy only** — Rajasthan's copy (in its own sibling project)
already has it independently, from its own pilot run. Until Assam and
Uttarakhand also complete this same change, any four-state comparison is
stale (per `a Rajasthan-pilot change plan (source removed from this project after adaptation, see docs_objective2/tamilnadu_phase_docs/)`'s cross-state
validity checks — identical shared-config hash is required).

## Status this supersedes

Every prior "Objective 2 is complete for Tamil Nadu" status (docs 00-15,
`RESULTS.md`, `OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md`) is now a **stale
snapshot** of the pre-2026-09-17 K=5 / staggered-only run. Treat any
`obj3_environment_contract_tamilnadu.json` from before this change as a
working draft, not a frozen hand-off, until Phase 8 regenerates it. As of
2026-09-18, docs 00-01's Tm-retargeting mechanism (step 2 above) is
*further* superseded by `../18_OBJECTIVE1_SHORTLIST_RESTORED.md` — see the
update note at the top of this doc.

## Files in this set (Tamil Nadu versions)

| File | Covers |
|---|---|
| `01_PROMPT_PHASE1_CONFIG_TAMILNADU.md` | Objective 1 data refresh, `configs/states/tamilnadu.yaml` rebuild, `design_bounds_shared.yaml`, `schema.py` (Tm-retargeting step now superseded, see update note above) |
| `02_PROMPT_PHASE2_GEOMETRY_TAMILNADU.md` | `geometry.py`, `constraints.py` |
| `03_PROMPT_PHASE3_SIMULATOR_TAMILNADU.md` | `run_case.py` pass-through, smoke runs |
| `04_PROMPT_PHASE4_GATES_TAMILNADU.md` | `gates.py`, version bump |
| `05-08` | Written after Phases 5-8 land, **updated 2026-09-18** for the shortlist restoration — see final numbers in each |
| `../18_OBJECTIVE1_SHORTLIST_RESTORED.md` | **(2026-09-18, most recent)** the PCM-shortlist scope correction and final Phase 5-8 results — read this first for current numbers |
