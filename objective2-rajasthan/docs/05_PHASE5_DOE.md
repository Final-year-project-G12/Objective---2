# 05 — Phase 5 Audit: Design-of-Experiments Dataset (Rajasthan)

Files: `src/doe/generate_cases.py`, `src/doe/run_batch.py`, `src/doe/split_cases.py`.
Run: `python pipeline.py --state rajasthan --stage doe`.
Output: `results/phase5_design_cases.parquet` (+ `.csv`), one row per simulation.

> **Ported from `objective2-tamilnadu/src/doe/`.** `generate_cases.py` is
> byte-identical (state-agnostic — it reads regimes + PCM shortlist from
> `configs/states/rajasthan.yaml` and bounds from the frozen
> `design_bounds_shared.yaml`). `run_batch.py` / `split_cases.py` differ
> only in: the simulator-version tag (`sim_v1_rajasthan`), the flat
> `results/phaseN_*` output path (this repo's convention, not TN's
> `results/<state>/`), and — in `run_batch.py` — `n_lhs_per_pair`
> defaulting to **12 instead of TN's 8**. Rationale below.

## Purpose (D2.4)

Build the simulation database Phase 6's surrogate learns from — one row
per **complete simulation case**, not per timestep, covering every
climate regime and every shortlisted PCM, plus boundary and baseline
cases, with infeasible cases kept rather than discarded (framework doc
§6.1–§6.2).

## Sampling plan actually run

| Component | Count | Method |
|---|---|---|
| No-PCM baseline (1 per regime) | 3 | fixed design (dmax, nmin, mid-flow) |
| Latin Hypercube draws (12 per regime×PCM pair) | 108 | `scipy.stats.qmc.LatinHypercube` over (diameter, flow, count→rounded), fixed seed base `20260905` |
| Boundary cases (6 per regime×PCM pair: dmin/dmax × fmin/fmax, nmin, nmax) | 54 | fixed corners |
| **Total** | **165** | |

9 regime×PCM pairs (3 Level-A clusters × 3 shortlisted PCMs each) + 3
baselines. Simulator version tag: `sim_v1_rajasthan` (released Phase 4).
Total DOE runtime: **809 s for 165 cases** (~4.9 s/case average).

**Why 12 LHS/pair, not TN's 8:** Rajasthan has 3 Level-A regimes vs Tamil
Nadu's 5, so 9 regime×PCM pairs vs TN's 15. At 8 LHS/pair the total would
be 9·(8+6)+3 = 129 — below the framework doc's stated 150–300 target. 12
LHS/pair gives 9·(12+6)+3 = 165, inside the band, using the same sampler
and the same fixed seed base. This is a call-argument change
(`N_LHS_PER_PAIR_DEFAULT` in `run_batch.py`), not a change to the sampling
code, and it is recorded in the returned manifest.

## Result

**111 valid / simulated, 54 rejected at the Phase 2 geometry gate — all 54
for the same reason, `bounds_violation`.**

This is the Phase 2 finding (`02_PHASE2_GEOMETRY_CONSTRAINTS.md`) showing
up at DOE scale, not a new bug: any design with `capsule_diameter_m` in
`[0.02, 0.04)` produces a derived `pcm_thickness_m = diameter/2 < 0.02`,
below `design_bounds_shared.yaml`'s own thickness floor.

| Rejected by | Count | Note |
|---|---|---|
| LHS draws | 36 / 108 (33.3%) | ≈ `(0.04−0.02)/(0.08−0.02)` = 33.3% of the diameter range — matches the expected rate exactly |
| Boundary cases | 18 / 54 | exactly the 2 `dmin_*` corners × 9 pairs; every `dmax`/`nmin`/`nmax` corner passes |
| **Total** | **54 / 165 (32.7%)** | vs Tamil Nadu's 70/215 = 32.6% — same interaction, same rate |

Rejections are perfectly even across regimes (18 per cluster) — expected,
since the geometry gate is climate-independent. **All 54 rejected rows are
kept in `phase5_design_cases.parquet` with `valid=False` and
`reason=bounds_violation`**, per the framework doc's "keep failed and
infeasible cases" requirement — they are what lets Phase 6's feasibility
classifier learn this exact boundary.

### Coverage checklist (framework doc §Phase 5 "must include")

| Requirement | Status |
|---|---|
| min/max thickness & flow | ✔ boundary `dmin/dmax × fmin/fmax` per pair (dmin rejected but retained with reason) |
| min/max capsule count | ✔ boundary `nmin`/`nmax` per pair |
| ≥1 case per shortlisted PCM per regime | ✔ 12 valid rows per (regime, PCM) pair |
| one no-PCM baseline per regime | ✔ `c{0,1,2}_baseline_noPCM` |
| keep failed/infeasible cases + reason codes | ✔ 54 rows with `valid=False`, `reason=bounds_violation` |
| 10 / 15 / 20% PCM-volume baselines | **not enumerable** — reachable PCM volume fraction here spans 0.0064–0.1138; 15% and 20% are outside the frozen sphere-only/24-capsule bounds (`02_PHASE2_GEOMETRY_CONSTRAINTS.md`). Stated, not silently skipped. |

## Case-level train/hold-out split

`split_cases.py` adds a `split ∈ {train, holdout}` column, stratified by
`(regime_id, pcm_id, valid)` so that:
- every regime×PCM pair has hold-out coverage (not just the pairs that
  happened to draw more LHS samples), and
- **both** valid and invalid rows get a holdout share — needed so the
  feasibility classifier's hold-out evaluation actually contains
  infeasible examples (see Phase 6 doc for why this matters).

Result: **138 train, 27 holdout** (of 165 total rows) — 93 train-valid,
45 train-invalid, 18 holdout-valid, 9 holdout-invalid. All **9**
regime×PCM pairs have ≥1 holdout case; the 3 no-PCM baselines are
singletons (1 valid row each) so they get no holdout, by the same
`len > 1` rule as Tamil Nadu. Since every row is already one complete,
independent simulation (not a sub-sequence of a longer trajectory), a
random split at the row level is leakage-free by construction.

## What the valid rows look like (first read, not a Phase 6/7 result)

- `solar_fraction` 0.538–0.587 across the 111 valid cases (mean 0.559) —
  a narrow band, consistent with Phase 4 Gate 3's finding that a single
  PCM's marginal effect on annual solar fraction is small in this
  lumped-tank architecture at the reachable PCM fractions.
- `max_pcm_temp_C` 68.2–72.7 °C — **every** valid case exceeds the frozen
  65 °C PCM safety limit, and 108 / 111 log `n_safety_violations > 0`.
  This is the Phase 3 / Phase 4 Cluster-0 finding generalising: under the
  frozen 1.5 m² collector / 50 L tank, Rajasthan's solar input overheats
  the store for **all three regimes and all six shortlisted PCMs**, before
  any control action. Phase 7 selection must carry this as a hard
  constraint (or the frozen collector sizing needs a hot-dry-state
  revisit) — it is not something Phase 5 resolves, only quantifies at
  scale. See `docs/00_MASTER_OVERVIEW.md`.

## Deviations from the full framework doc (stated, not hidden)

- No separate "unseen weather year" or "unseen member point" hold-out —
  medoid-only, single representative year (2025), per the 40-hr cut list.
  A proper unseen-weather-year hold-out is named future work.
- LHS draws capsule count as a continuous variable then rounds to the
  nearest integer, rather than a strict enumerated integer grid — with
  only 17 allowed values (8–24) this still gives space-filling coverage
  across all three variables jointly. (Inherited from Tamil Nadu.)
- 12 LHS draws per pair instead of 8, to land in the 150–300 target with
  3 regimes rather than 5 (see "Sampling plan" above).
