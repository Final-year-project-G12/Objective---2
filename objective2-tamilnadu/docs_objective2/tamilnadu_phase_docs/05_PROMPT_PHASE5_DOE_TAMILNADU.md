# 05 — Phase 5 (Tamil Nadu): Arrangement-Stratified DOE

**Files touched:** `src/doe/generate_cases.py`, `src/doe/run_batch.py`,
`src/doe/split_cases.py`. Adapted from
`a Rajasthan-pilot change plan (source removed from this project after adaptation, see docs_objective2/tamilnadu_phase_docs/)`.

## Why

The pre-2026-09-17 DOE (per regime × PCM pair: 8 LHS + 6 boundary corners,
all implicitly staggered) needs every arrangement represented in roughly
even numbers, or Phase 6's surrogate would see "staggered" far more often
than "radial" and any arrangement comparison it makes wouldn't be
trustworthy. On top of that, Objective 1's data refresh changed the
regime/PCM pairing entirely (K=3 regimes now, not K=5; different PCM
shortlist per regime).

## What was actually run (Tamil Nadu)

1. **`generate_cases.py`**: LHS split into 4 draws × 3 arrangements (12
   LHS/pair, up from 8 staggered-only) using a distinct seed offset per
   arrangement (same base seed + arrangement index, not the same points
   relabeled). Boundary cases: the **reduced 4-corner set** (dmin/dmax ×
   fmin/fmax at mid-count) repeated per arrangement (12/pair) — chosen over
   the full 6-corner × 3 variant (which would give 273 cases) to keep
   runtime to a few minutes; documented explicitly in the manifest's
   `case_count_decision` field, not silently picked. No-PCM baseline: 1 per
   regime, `capsule_arrangement="staggered"` explicit (not an implicit
   default — a no-PCM design's dummy geometry still runs Phase 2's packing
   check, so arrangement is a real field there too).
2. **`run_batch.py`**: `DesignVector` construction now passes
   `spec.capsule_arrangement`; every row tagged `sim_v2_tamilnadu` (bumped
   from `sim_v1`, Phase 4). Rejection-rate reporting broken out by
   arrangement (not one pooled percentage) plus a rejection-reasons-by-
   arrangement table.
3. **`split_cases.py`**: stratification key changed from
   `(regime_id, pcm_id, valid)` to `(regime_id, pcm_id, arrangement, valid)`
   so every regime × PCM × arrangement combination gets hold-out coverage.

```
python pipeline.py --state tamilnadu --stage doe
```

## Case-count decision (documented, not silently picked)

9 regime × PCM pairs (3 regimes × 3 shortlisted PCMs each) ×
(12 LHS + 12 boundary) + 3 no-PCM baselines = **219 cases** — inside the
framework's 150-350 target band.

## Results

*(Updated 2026-09-18 for the Objective-1-shortlist restoration — see
[docs_objective2/18_OBJECTIVE1_SHORTLIST_RESTORED.md](../18_OBJECTIVE1_SHORTLIST_RESTORED.md).
Case count/structure is unchanged since the regime × PCM pairing count
(3 regimes × 3 PCMs each) is the same; only which PCMs are used differs.)*

**219 cases total: 107 valid, 112 rejected** at Phase 2's geometry gate
(runtime ~18 minutes).

**Rejection rate by arrangement — a real, expected asymmetry, not a bug:**

| Arrangement | n_total | n_valid | n_rejected | rejection % |
|---|---|---|---|---|
| radial | 72 | 23 | 49 | **68.1%** |
| single-layer | 72 | 40 | 32 | 44.4% |
| staggered | 75 | 44 | 31 | 41.3% |

Rejection reasons: 94 `bounds_violation` (diameter/thickness interaction,
arrangement-independent, hits all three roughly evenly: 31/32/31), plus
**18 `passage_blocked` — all 18 in radial, zero in the other two**. This is
Phase 2's max-reachable-fraction finding (radial capped well below the
other two arrangements) showing up directly in the DOE: radial designs run
out of tank height far more often at the same (diameter, count) the other
arrangements handle fine.

Train/holdout split: 165 train rows (incl. invalid, for the feasibility
classifier), 54 holdout. **27/30** regime × PCM × arrangement combinations
have ≥1 holdout case (the remaining 3 are singleton groups with too few
valid rows for a holdout share — the split rule's documented behavior, not
a bug).

## Exit check before moving to Phase 6

Check every `(regime, pcm, arrangement)` combination has ≥1 valid row where
a feasible design exists for that combination at all — if any comes back
zero, that's a real finding (the surrogate can't learn what it's never
seen), not something to silently paper over.
