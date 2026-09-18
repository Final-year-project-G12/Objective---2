# 02 — Phase 2 (Tamil Nadu): Arrangement-Branched Geometry Engine

**Files touched:** `src/design/geometry.py`, `src/design/constraints.py`.
Adapted from `a Rajasthan-pilot change plan (source removed from this project after adaptation, see docs_objective2/tamilnadu_phase_docs/)`.

## What was actually run (Tamil Nadu)

`pack_capsules()` now dispatches to three packing models — `pack_staggered`
(unchanged hex-lattice math, wrapped into the common interface),
`pack_single_layer` (square-grid, no row offset), and `pack_radial`
(concentric rings around the tank axis). All three return a `PackingResult`
with `capsules_per_layer`, `n_layers`, `stack_height_m`, and `void_fraction`.

**A real physics bug was found and fixed during this work, not present in
the Rajasthan prompt's plan**: the first implementation derived
`void_fraction` from the *bulk* dilution formula
`1 - pcm_volume_fraction` (same for every arrangement, since it only depends
on diameter/count, not packing pattern) — this **failed** the required
cross-arrangement sanity check (identical `void_fraction`/`pressure_drop_pa`
across all three arrangements for the same design). The fix redefines
`void_fraction` as each pattern's own **unit-cell porosity**:
`1 - capsule_volume / (footprint_area_per_capsule × layer_pitch)` — a
bed-characteristic constant for the packing type (matches the Ergun
equation's intended meaning), not diluted by the tank's empty headspace.
Sanity check: this model gives 0.476 void fraction for the square-grid
pattern, matching the textbook simple-cubic sphere-packing porosity exactly
— good evidence the physics is right, not just "different."

`get_max_reachable_pcm_fraction(arrangement, diameter_m=0.08, count_max=37)`
sweeps count at the diameter ceiling and reports the max valid fraction.

```
python pipeline.py --state tamilnadu --stage geometry
```

## Results (Tamil Nadu, 2026-09-17)

**Boundary self-test: 24/24 deterministic** (8 cases × 3 arrangements, up
from 8 when arrangement was frozen).

**Cross-arrangement sanity check** (same 0.05 m / 20-capsule / 0.030 kg/s
design run under all three arrangements):

| Arrangement | void_fraction | pressure_drop_pa |
|---|---|---|
| single-layer | 0.5604 | 0.00154 |
| staggered | 0.4924 | 0.00284 |
| radial | 0.5802 | 0.00129 |

Genuinely different across all three — **PASS** (dispatcher is branching;
staggered is densest, matching physical intuition for hex-lattice packing).

**Max-reachable PCM-volume-fraction table** (diameter=0.08 m, count_max=37):

| Arrangement | Max N feasible | Max reachable PCM vol % |
|---|---|---|
| single-layer | 37 | 19.84% |
| staggered | 37 | 19.84% |
| radial | 21 | 11.26% |

**Finding, stated plainly rather than equalized away**: radial packing is
geometrically capped well below the other two arrangements (11.3% vs
19.8%) — radial rings leave more unused cross-section near the tank wall
per layer, forcing more layers (and thus a shorter total achievable stack
within the fixed tank height) for the same capsule count. single-layer and
staggered happen to tie at the shared 0.20 volume-fraction ceiling itself
(both are limited by that bound, not by their own packing density, at
count=37/diameter=0.08).

## Exit check before moving to Phase 3

Confirmed: no reason-code set changed (still `bounds_violation`, `overlap`,
`volume_exceeded`, `passage_blocked`, `pressure_drop_limit`,
`flow_out_of_range`); arrangement asymmetry (radial < the other two) is
reported here and carried forward, not silently narrowed to match.
