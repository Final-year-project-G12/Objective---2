# 03 — Phase 3 (Tamil Nadu): Arrangement Pass-Through + Smoke Runs

> **Note (2026-09-18):** this phase is PCM-identity-agnostic (it verifies
> pass-through logging, not physics) and was **not** re-run after the
> shortlist restoration — see `../18_OBJECTIVE1_SHORTLIST_RESTORED.md`.
> `n-Tetracosane (C24)` below was cluster 0's PCM under the now-superseded
> Tm-retargeted shortlist at the time this smoke test was run; it is
> illustrative of the pass-through mechanism only, not a current design
> choice. Cluster 0's actual current PCM is RT57HC.

**Files touched:** `src/simulation/run_case.py` (one field added, logging
only). **Not touched:** `capsule_enthalpy.py`, `collector_model.py`,
`heat_transfer.py`, `hydraulic_model.py`, `demand_profile.py`,
`energy_balance.py`, `tank_model.py` — no physics code changed, exactly as
the Rajasthan plan anticipated.
Adapted from `a Rajasthan-pilot change plan (source removed from this project after adaptation, see docs_objective2/tamilnadu_phase_docs/)`.

## Why

The simulator's submodels consume *derived geometry outputs* (void
fraction, pressure drop, pump power), not the arrangement label itself.
Since Phase 2 now computes those outputs differently per arrangement, the
simulator is automatically arrangement-aware without any physics code
changing — this phase is pass-through + verification, not implementation.

## What was actually run (Tamil Nadu)

```python
# run_case.py's metrics dict gained one field:
"arrangement": design.capsule_arrangement,
```
Pass-through only — no `if arrangement == ...` branch exists anywhere in
`src/simulation/`.

Three smoke tests (cluster 0, `n-Tetracosane (C24)` — cluster 0's current
MCDM+retargeting shortlist winner, replacing the pre-refresh
`n-Octacosane (C28)` used as the Rajasthan-plan's RT50 stand-in):

```
python pipeline.py --state tamilnadu --stage simulate --cluster 0 \
    --pcm "n-Tetracosane (C24)" --diameter 0.08 --count 19 --arrangement staggered --flow 0.030
python pipeline.py --state tamilnadu --stage simulate --cluster 0 \
    --pcm "n-Tetracosane (C24)" --diameter 0.08 --count 19 --arrangement single-layer --flow 0.030
python pipeline.py --state tamilnadu --stage simulate --cluster 0 \
    --pcm "n-Tetracosane (C24)" --diameter 0.08 --count 19 --arrangement radial --flow 0.030
```

(count=19 is within radial's own max-feasible ceiling of 21 at this
diameter, so the same count is usable for all three without substitution —
unlike the Rajasthan case, which needed a fallback count for some
arrangements.)

## Results

All three completed cleanly: no NaN/inf, no crash, residuals in the
0.00004-0.0003% range (see Gate 1's readout in doc 04) — far under the 0.1%
threshold for all three arrangements. staggered and single-layer give
near-identical `useful_energy_kWh`/`solar_fraction` at equal (diameter,
count, flow) — expected, since arrangement in this model only affects
pressure drop/pump power (a separate, currently tiny energy channel) and
packing feasibility, not the heat-transfer physics itself (see doc 02's
note on why void_fraction doesn't feed into the Wakao-Kaguei heat-transfer
coefficient). radial's own numbers differ only insofar as its lower
max-feasible count changes the design being compared, not because its
physics differs.

## Exit check before moving to Phase 4

No arrangement showed a residual meaningfully worse than the others — this
confirms Phase 2's packing models are each producing a self-consistent
(void_fraction, pressure_drop) pairing, not one that would corrupt energy
accounting. Proceed to Phase 4.
