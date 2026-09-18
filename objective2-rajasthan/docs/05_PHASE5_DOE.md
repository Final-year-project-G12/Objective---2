# 05 — Phase 5 Audit: Design-of-Experiments Dataset (Rajasthan)

Files: `src/doe/generate_cases.py`, `src/doe/run_batch.py`, `src/doe/split_cases.py`.
Run: `python pipeline.py --state rajasthan --stage doe`.
Output: `results/phase5_design_cases.parquet` (+ `.csv`), one row per simulation.

> **Ported from `objective2-tamilnadu/src/doe/`**, then made
> **arrangement-stratified on 2026-09-17** (`Objective2 Consolidated plan.md`
> §6, Phase 5) when capsule arrangement was restored as a searched
> variable. `run_batch.py` / `split_cases.py` also differ from Tamil
> Nadu's copies in the simulator-version tag (`sim_v2_rajasthan`), the flat
> `results/phaseN_*` output path (this repo's convention, not TN's
> `results/<state>/`), and `n_lhs_per_pair` defaulting to **12 instead of
> TN's 8** (rationale below).

## Purpose (D2.4)

Build the simulation database Phase 6's surrogate learns from — one row
per **complete simulation case**, not per timestep, covering every
climate regime, every shortlisted PCM, and every arrangement, plus
boundary and baseline cases, with infeasible cases kept rather than
discarded (framework doc §6.1–§6.2).

## Sampling plan — arrangement-stratified

| Component | Count | Method |
|---|---|---|
| No-PCM baseline (1 per regime) | 3 | fixed design (dmax, nmin, mid-flow), arrangement sentinel `staggered` (doesn't apply to a PCM-less config, see `generate_cases.py`) |
| Latin Hypercube draws (12 per regime×PCM pair, split 3 groups of 4, one group per arrangement) | 108 | `scipy.stats.qmc.LatinHypercube` over (diameter, flow, count→rounded), fixed seed base `20260905` + arrangement-group offset |
| Boundary cases (4 corners × 3 arrangements = 12 per regime×PCM pair: dmin/dmax × fmin/fmax) | 108 | fixed corners, once per arrangement |
| **Total** | **219** | |

9 regime×PCM pairs (3 Level-A clusters × 3 shortlisted PCMs each) + 3
baselines. Simulator version tag: `sim_v2_rajasthan` (released Phase 4).

**Case-count decision (2026-09-17):** the pre-arrangement-restore DOE used
6 boundary corners per pair (including nmin/nmax) for 165 total cases.
Stratifying that same 6-corner set across 3 arrangements would give
9×(12+18)+3 = 273 cases — still inside the framework's 150–350 target
band, but a 65% jump. Instead, the nmin/nmax corners were dropped (4
corners × 3 arrangements = 12/pair, not 18/pair), landing at
9×(12+12)+3 = **219** cases — comfortably inside the target band without
the full 3× blowup. Stated here, not silently applied — see
`generate_cases.py`'s `case_count_decision` manifest field.

**Why 12 LHS/pair, not TN's 8:** Rajasthan has 3 Level-A regimes vs Tamil
Nadu's 5, so 9 regime×PCM pairs vs TN's 15. At 8 LHS/pair the total would
be too small relative to the 150–350 target once arrangement-stratified;
12 LHS/pair (4 per arrangement) keeps continuous coverage per arrangement
comparable to the old 12-staggered-only draws while covering all three
arrangements.

## Result

**219 cases: 128 valid / 91 rejected — all 91 for the same reason,
`bounds_violation`.**

This is the Phase 2 finding (`02_PHASE2_GEOMETRY_CONSTRAINTS.md`) showing
up at DOE scale, not a new bug and not caused by arrangement: any design
with `capsule_diameter_m` in `[0.02, 0.04)` produces a derived
`pcm_thickness_m = diameter/2 < 0.02`, below `design_bounds_shared.yaml`'s
own thickness floor, regardless of arrangement.

| Rejected by | Count | Note |
|---|---|---|
| LHS draws | 37 / 108 (34.3%) | ≈ `(0.04−0.02)/(0.08−0.02)` = 33.3% of the diameter range — matches the expected rate |
| Boundary cases | 54 / 108 | exactly the `dmin` corners (2 of 4 corners) × 9 pairs × 3 arrangements |
| **Total** | **91 / 219 (41.6%)** | |

### Rejection rate by arrangement — the check this restore-change specifically required

| Arrangement | n cases | n rejected | Rejection % |
|---|---|---|---|
| single-layer | 72 | 32 | 44.4% |
| radial | 72 | 30 | 41.7% |
| staggered | 75 | 29 | 38.7% |

Close enough to each other (all driven by the same diameter-vs-thickness
bound, which is independent of arrangement) that **no arrangement is
meaningfully starved of valid examples** — a real finding, not assumed:
the `capsule_diameter_m < 0.04 m` interaction dominates the rejection
rate at this stage, while arrangement-specific packing/passage rejections
(the ones that *would* differ structurally by arrangement) don't bind
strongly within these bounds (consistent with Phase 2's max-reachable-
fraction finding that all three arrangements reach the same ceiling at
`d=0.08 m`).

Rows kept in `phase5_design_cases.parquet` with `valid=False` and
`reason=bounds_violation` regardless of arrangement — needed so Phase 6's
feasibility classifier can learn this boundary for every arrangement, not
just staggered.

### Coverage checklist (framework doc §Phase 5 "must include")

| Requirement | Status |
|---|---|
| min/max thickness & flow | ✔ boundary `dmin/dmax × fmin/fmax` per pair per arrangement (dmin rejected but retained with reason) |
| every arrangement represented per pair | ✔ 12 LHS + 12 boundary cases per pair split evenly across single-layer/staggered/radial |
| ≥1 case per shortlisted PCM per regime | ✔ 13-15 valid rows per (regime, PCM) pair (see table below) |
| one no-PCM baseline per regime | ✔ `c{0,1,2}_baseline_noPCM` |
| keep failed/infeasible cases + reason codes | ✔ 91 rows with `valid=False`, `reason=bounds_violation` |
| 10 / 15 / 20% PCM-volume baselines | reachable PCM volume fraction now spans up to 19.84% at the widened count ceiling (37) — see `02_PHASE2_GEOMETRY_CONSTRAINTS.md`; the 15%/20% Chen-style levels are now geometrically reachable, unlike the pre-2026-09-17 24-capsule ceiling. |

Valid rows per (regime, PCM) pair:

| Regime | PCM | Valid rows |
|---|---|---|
| 0 | Lauric acid (C12) | 15 |
| 0 | RT45HC | 14 |
| 0 | RT50 | 15 |
| 0 | NONE_plain_tank | 1 |
| 1 | Paraffin/HDPE PCM3 | 14 |
| 1 | Paraffin/HDPE PCM6 | 15 |
| 1 | savE® OM50 | 13 |
| 1 | NONE_plain_tank | 1 |
| 2 | Paraffin/HDPE PCM3 | 13 |
| 2 | Paraffin/HDPE PCM6 | 13 |
| 2 | savE® OM50 | 13 |
| 2 | NONE_plain_tank | 1 |

## Case-level train/hold-out split

`split_cases.py` adds a `split ∈ {train, holdout}` column, stratified by
**`(regime_id, pcm_id, arrangement, valid)`** since 2026-09-17 (was
`(regime_id, pcm_id, valid)`) so that:
- every regime×PCM×arrangement combination has hold-out coverage (not
  just every regime×PCM combination pooled across arrangements), and
- **both** valid and invalid rows get a holdout share — needed so the
  feasibility classifier's hold-out evaluation actually contains
  infeasible examples for every arrangement.

Result: **165 train, 54 holdout** (of 219 total rows). **9/9** valid
regime×PCM pairs (excluding the singleton no-PCM baselines) have ≥1
holdout case; **27/30** regime×PCM×arrangement combinations have ≥1
holdout row — the 3 missing combinations are all
`(regime, NONE_plain_tank, staggered)`, i.e. the singleton no-PCM
baseline rows (1 row each, by design get zero holdout share under the
`len > 1` rule inherited from Tamil Nadu). Not a coverage gap in any
PCM-bearing combination. Since every row is already one complete,
independent simulation (not a sub-sequence of a longer trajectory), a
random split at the row level is leakage-free by construction.

## What the valid rows look like (first read, not a Phase 6/7 result)

- `solar_fraction` 0.5382–0.5897 across the 128 valid cases (mean 0.560)
  — a narrow band, consistent with Phase 4 Gate 3's finding that a single
  PCM's marginal effect on annual solar fraction is small in this
  lumped-tank architecture, and now also consistent with Phase 6's
  finding that arrangement's effect is near-zero.
- `max_pcm_temp_C` up to 72.0 °C — above the frozen 65 °C PCM safety
  limit for a number of sampled designs (expected: this raw DOE sweep
  covers the whole design space, not just the safety-filtered subset a
  real deployment would use) — but **0/128 valid rows log
  `n_safety_violations > 0`**, because the rule-based safety shield
  (`system_config_shared.yaml: safety_shield.enabled`, adopted
  2026-09-13, active as the pipeline default through Phases 5–8, see
  `09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md` §6-§8) actively bypasses/stops
  charging before the hard limit is crossed for every sampled design in
  this run.

## Deviations from the full framework doc (stated, not hidden)

- No separate "unseen weather year" or "unseen member point" hold-out —
  medoid-only, single representative year, per the 40-hr cut list. A
  proper unseen-weather-year hold-out is named future work.
- LHS draws capsule count as a continuous variable then rounds to the
  nearest integer, rather than a strict enumerated integer grid.
  (Inherited from Tamil Nadu.)
- 12 LHS draws per pair (4 per arrangement) instead of a flat 8, to keep
  the arrangement-stratified total inside the 150–350 target with only 3
  regimes (see "Sampling plan" above).
