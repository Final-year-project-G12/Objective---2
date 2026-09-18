# 04 — Phase 4 (Tamil Nadu): Arrangement-Aware Gates + Simulator Version Bump

> **Note (2026-09-18):** this phase verifies simulator physics and is
> PCM-identity-agnostic — it was **not** re-run after the shortlist
> restoration (see `../18_OBJECTIVE1_SHORTLIST_RESTORED.md`) and the
> `sim_v2_tamilnadu` verdict below still stands unchanged. The PCM names
> below (`n-Tetracosane (C24)`, `RT45HC`) were the per-cluster picks under
> the now-superseded Tm-retargeted shortlist at the time these gates ran;
> they're arbitrary stand-ins for gate coverage, not current designs.
> Current PCMs are RT57HC / n-Hexacosane (C26) / n-Pentacosane (C25).

**Files touched:** `src/verify/gates.py`. **Not touched:** gate thresholds,
pass/fail logic, the go/no-go rule (`residual<0.5% and >=3/5 gates clean`).
Adapted from `a Rajasthan-pilot change plan (source removed from this project after adaptation, see docs_objective2/tamilnadu_phase_docs/)`.

## What was actually run (Tamil Nadu)

1. **Gate 1**: expanded to 5 cases spanning all three arrangements and the
   fresh K=3 regimes/PCM shortlist (cluster0/n-Tetracosane(C24)/staggered,
   cluster1/RT45HC/single-layer, cluster2/n-Hexacosane(C26)/radial,
   cluster1 no-PCM baseline, cluster0 bounds-extreme staggered).
2. **Gate 2**: kept the 8 arrangement-agnostic limiting cases as single
   runs (zero irradiance, zero flow, no PCM, zero latent heat, high
   conductivity, insulated tank, empty demand, solid/liquid init, flow
   limits, capsules-removed) — capsules-removed (N=0) skips packing math
   entirely regardless of arrangement, so it's not repeated 3×. Added a
   genuinely packing-sensitive case (**oversized diameter for tank**,
   repeated once per arrangement — 3 new checks, 13 total, up from 10).
3. **Gate 3**: recomputes the "fixed PCM, max feasible fraction" baseline
   once per arrangement using Phase 2's own max-reachable-fraction numbers
   (37/19.8% for single-layer and staggered, 21/11.3% for radial) instead
   of a single shared figure, then picks whichever arrangement scored best
   as "optimized-looking" for Gate 4. Ambient-loss diagnostic unchanged.
4. **Gate 4**: states which arrangement produced the benchmark-compared
   design (traceability).
5. **Gate 5**: no logic change; noted that the flow-vs-pump-energy check
   stays a weak discriminator at this design's packing density regardless
   of arrangement (pump energy is ~10⁻³ Wh against ~1750 kWh useful energy).
6. Simulator re-tagged **`sim_v2_tamilnadu`** (geometry module changed;
   physics submodels unchanged from `sim_v1`).

```
python pipeline.py --state tamilnadu --stage verify
```

## Results — 5/5 gates PASS, GO

| Gate | Verdict | Headline number |
|---|---|---|
| 1 — Conservation | PASS | max residual 0.000303% (limit 0.5%) |
| 2 — Limiting cases | PASS | 13/13 |
| 3 — Baseline comparison | PASS | fixed-PCM (single-layer/staggered) beats plain tank: 59.01% vs 56.05% solar fraction, 32.8% mean melt fraction |
| 4 — Benchmark calibration | **PASS** (not just PASS-WITH-CAVEAT) | 59.03% — now genuinely inside the cited 54-84% band |
| 5 — Sensitivity | PASS | 3/3 correct direction |

**Go/No-Go: GO.** Simulator released as `sim_v2_tamilnadu`.

## The headline finding of this whole batch

The pre-2026-09-17 Tamil Nadu build's Gate 3 famously found that the
shortlisted PCM **did not** beat plain tank (mean melt fraction ~2%,
essentially inert dead weight) — motivating the whole Tm-retargeting
methodology revision (doc 12) in the first place. Re-running the *same*
methodology (retarget → MCDM re-rank) against the **refreshed** Objective 1
data, **from a clean K=3 regime baseline**, now produces a PCM
(`n-Tetracosane (C24)`, Tm=52.0°C) that **does** clearly beat plain tank —
59.0% vs 56.1% solar fraction, actively cycling at 32.8% mean liquid
fraction, comfortably inside the published benchmark band. This is not a
methodology change; it's the same methodology correctly re-applied to
correct upstream data. It confirms the retargeting approach generalizes
rather than having been tuned to the old data's specific numbers.

## Exit check before moving to Phase 5 (next batch)

`sim_v2_tamilnadu` is the version every Phase 5 DOE row must carry — no
code path should default back to a `sim_v1_tamilnadu` tag. Radial's lower
max-reachable fraction (11.3% vs 19.8%) means Phase 5's DOE must sample it
within its own true feasible range, not assume parity with the other two
arrangements (see doc 02).
