# 06 — Phase 5 Audit: Design-of-Experiments Dataset

Files: `src/doe/generate_cases.py`, `src/doe/run_batch.py`, `src/doe/split_cases.py`.
Run: `python pipeline.py --state uttarakhand --stage doe`.
Output: `results/uttarakhand/design_cases.parquet` (+ `.csv`).

## Purpose (D2.4)

Build the simulation database Phase 6's surrogate learns from — one row
per **complete simulation case**, not per timestep, covering every
climate regime and every shortlisted PCM, plus boundary and baseline
cases, with infeasible cases kept rather than discarded (framework doc
§6.1–§6.2).

## Sampling plan actually run

| Component | Count | Method |
|---|---|---|
| No-PCM baseline (1 per regime) | 5 | fixed design |
| Latin Hypercube draws (8 per regime×PCM pair) | 120 | `scipy.stats.qmc.LatinHypercube` over (diameter, flow, count), fixed seed `20260905` |
| Boundary cases (6 per regime×PCM pair: dmin/dmax × fmin/fmax, nmin, nmax) | 90 | fixed corners |
| **Total** | **215** | |

15 regime×PCM pairs (5 clusters × 3 shortlisted PCMs each) + 5 baselines.
Simulator version tag: `sim_v1_uttarakhand` (released Phase 4).

**Note on PCM shortlist per regime**: regimes 0, 2, 4 have [PureTemp 58,
n-Octacosane (C28), PlusICE A58]; regimes 1 and 3 have [PureTemp 58,
Palmitic-stearic acid/Expanded graphite, n-Octacosane (C28)] — see
`configs/states/uttarakhand.yaml`.

## Result

**145 valid / simulated, 70 rejected at the Phase 2 geometry gate — all 70
for the same reason, `bounds_violation`.**

This is the Phase 2 finding (`02_PHASE2_GEOMETRY_CONSTRAINTS.md`) showing
up at DOE scale, not a new bug: any LHS draw with `capsule_diameter_m` in
`[0.02, 0.04)` produces a derived `pcm_thickness_m = diameter/2 < 0.02`,
which is below `design_bounds_shared.yaml`'s own thickness floor. Roughly
`(0.04-0.02)/(0.08-0.02) ≈ 33%` of the diameter range is affected, and
indeed 70/215 ≈ 32.6% of sampled cases were rejected for exactly this —
matching the expected rate almost exactly. **All 70 rejected rows are kept
in `design_cases.parquet` with `valid=False` and `reason=bounds_violation`**,
per the framework doc's "keep failed and infeasible cases" requirement —
they are what lets Phase 6's feasibility classifier learn this exact boundary.

## Case-level train/hold-out split

`split_cases.py` adds a `split ∈ {train, holdout}` column, stratified by
`(regime_id, pcm_id, valid)` so that:
- every regime×PCM pair has hold-out coverage, and
- **both** valid and invalid rows get a holdout share — needed so the
  feasibility classifier's hold-out evaluation actually contains
  infeasible examples (see Phase 6 doc for why this mattered).

Result: **170 train, 45 holdout** (of 215 total rows). Since every row is
already one complete, independent simulation (not a sub-sequence of a
longer trajectory), a random split at the row level is leakage-free by
construction.

## Deviations from the full framework doc (stated, not hidden)

- No separate "unseen weather year" or "unseen member point" hold-out —
  medoid-only, single representative year, per the 40-hr cut list.
- LHS draws capsule count as a continuous variable then round to the
  nearest integer, rather than a strict enumerated integer grid — with
  only 17 allowed values (8–24) this still gives reasonable coverage
  while keeping every LHS point jointly space-filling across all three
  variables at once.
