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

**Note on PCM shortlist per regime (post Tm-retargeting, doc 12)**:
regimes 0, 2 and 4 have [RT42, RT44HC, savE® OM42]; regime 3 has
[RT44HC, RT42, savE® OM42]; regime 1 (the coldest, smallest-sample
regime) has **no** retargeted survivor and keeps its old, climate-anchored
shortlist [PureTemp 53, n-Hexacosane (C26), Myristic acid (C14)] as a
documented fallback — see `configs/states/uttarakhand.yaml` and doc 12.

## Result

**142 valid / simulated, 73 rejected at the Phase 2 geometry gate — all 73
for the same reason, `bounds_violation`.**

This is the Phase 2 finding (`02_PHASE2_GEOMETRY_CONSTRAINTS.md`) showing
up at DOE scale, not a new bug: any LHS draw with `capsule_diameter_m` in
`[0.02, 0.04)` produces a derived `pcm_thickness_m = diameter/2 < 0.02`,
which is below `design_bounds_shared.yaml`'s own thickness floor. Roughly
`(0.04-0.02)/(0.08-0.02) ≈ 33%` of the diameter range is affected, and
indeed 73/215 ≈ 34.0% of sampled cases were rejected for exactly this —
close to the expected rate (the exact count shifts between runs depending
on the PCM shortlist used, since diameter draws are keyed per
regime×PCM pair, and this run also samples the widened `capsule_count`
range up to 37, doc 13). **All 73 rejected rows are kept
in `design_cases.parquet` with `valid=False` and `reason=bounds_violation`**,
per the framework doc's "keep failed and infeasible cases" requirement —
they are what lets Phase 6's feasibility classifier learn this exact boundary.

The valid rows' `geom_pcm_volume_fraction` now reaches up to **16.8%** in
the actual 215-case LHS/boundary sample (the theoretical ceiling at
`n_capsule=37, diameter=0.08` is 19.84%, see doc 13) — up from the
pre-widening maximum of ~12.9%.

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
  30 allowed values (8–37, widened from 8–24, doc 13) this still gives
  reasonable coverage while keeping every LHS point jointly space-filling
  across all three variables at once.
