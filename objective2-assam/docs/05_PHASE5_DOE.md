# 05 — Phase 5 Audit: Design-of-Experiments Dataset (Assam)

Files: `src/doe/generate_cases.py`, `src/doe/run_batch.py`,
`src/doe/split_cases.py`. Output: `results/phase5_design_cases.csv`
(+ `.parquet`), one row per simulation.

> Rewritten from the actual `results/phase5_design_cases.csv` — the
> counts (165 total / 111 valid / 54 infeasible, 32.7%) turn out
> **identical** to Rajasthan's, because both states use the same
> sampling parameters (12 LHS/pair, 3 Level-A regimes → 9 regime×PCM
> pairs) against the same frozen geometry bounds — this is a real
> coincidence of matching regime counts, not a copy-paste error. PCM
> names, regime labels, and the DOE-scale safety finding below are
> Assam's own.

## Sampling plan actually run

| Component | Count | Method |
|---|---|---|
| No-PCM baseline (1 per regime) | 3 | fixed design (dmax, nmin, mid-flow) |
| Latin Hypercube draws (12 per regime×PCM pair) | 108 | `scipy.stats.qmc.LatinHypercube` over (diameter, flow, count→rounded) |
| Boundary cases (6 per regime×PCM pair) | 54 | fixed corners |
| **Total** | **165** | |

9 regime×PCM pairs (3 Level-A clusters × `savE® OM48/OM50/OM46`, the
same 3-PCM shortlist in every regime) + 3 baselines. Simulator version
tag: `sim_v1_assam`.

## Result

**111 valid / 54 rejected at the Phase 2 geometry gate, all `bounds_violation`
(32.7%)** — verified directly by counting `valid` in
`results/phase5_design_cases.csv` (111 `True` / 54 `False` of 165
rows). Same root cause as every other state: any design with
`capsule_diameter_m` in `[0.02, 0.04)` produces a derived
`pcm_thickness_m < 0.02 m`, below the frozen thickness floor.

## Train/holdout split

`split_cases.py` reports (matching `results/phase6_surrogate_report.md`'s
dataset section): **138 train (93 valid / 45 infeasible), 27 holdout
(18 valid / 9 infeasible)**, stratified by `(regime_id, pcm_id, valid)`.

## What the valid rows show (first read, not a Phase 6/7 result)

Directly counted from `results/phase5_design_cases.csv` (111 valid
rows): **79 / 111 (71%) log `max_pcm_temp_C > 65 °C`**; **0 / 111
exceed `max_water_temp_C > 75 °C`**. So at DOE scale, Assam's
overheating problem is real but less pervasive than Rajasthan's
(108/111, 97%) and lands entirely on the *PCM* limit, never the water
limit — consistent with Phase 4 Gate 2's finding that even the plain
(no-PCM) Cluster-0 tank already reaches 66.84 °C (`04_…`), and with
Phase 7's 3 selected PCM designs all showing `max_pcm_temp_C` in the
66–70 °C range (`07_…`). This is the DOE-scale evidence behind Phase
7's safety-verdict problem: a genuinely narrower failure mode than
Rajasthan's near-universal one, but it still means most valid designs
(not just the 3 eventually selected) would fail the frozen 65 °C
filter if it were actually applied.

## Deviations from the full framework doc (same as every state)

No unseen-weather-year hold-out (medoid-only, single representative
year); capsule count sampled continuously then rounded to the nearest
integer (17 allowed values, 8–24); 12 LHS draws per pair to land in the
framework's 150–300 total-case target with 3 regimes.
