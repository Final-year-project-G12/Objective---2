# 02 — Phase 2 Audit: Geometry & Constraint Engine

Files: `src/design/schema.py`, `src/design/geometry.py`, `src/design/constraints.py`.

## Purpose (D2.2)

Given a design vector `[capsule_diameter_m, n_capsule, flow_rate_kg_s]`
(sphere shape and staggered arrangement are frozen for the 40-hr scope —
see Phase 1 doc), return volume/area/spacing/pressure-drop and a
valid/invalid flag with one reason code. Universal across all four states.

## Geometric model

- **Tank**: vertical cylinder. Diameter/height are *derived* once from the
  frozen 50 L volume assuming height = 2×diameter (a stated proportion
  assumption, not measured) — `tank_dimensions_m()`. Result: tank diameter
  ≈ 0.317 m, height ≈ 0.634 m.
- **Packing**: capsules are packed in staggered horizontal layers using a
  2D hexagonal-lattice footprint per sphere (`capsules_per_layer()`);
  layers stack up the tank height. This is the "staggered arrangement"
  the design bounds freeze.
- **Hydraulics**: pressure drop via the **Ergun equation** (Ergun, 1952) for
  flow through a packed bed of spheres — a standard, citable correlation,
  not derived from scratch, per the framework doc's requirement. Pump
  power = Δp·V̇/η_pump.

## Reason codes

| Code | Meaning |
|---|---|
| `bounds_violation` | A raw variable (diameter, count, shape, arrangement, or the *derived* thickness) is outside `design_bounds_shared.yaml` |
| `flow_out_of_range` | Flow rate outside [0.010, 0.050] kg/s |
| `overlap` | Capsule too large to fit even once in the tank's cross-section at the minimum spacing |
| `volume_exceeded` | N_capsule × V_capsule exceeds the 20%-of-tank-volume ceiling |
| `passage_blocked` | The capsule stack doesn't fit within the tank height, or bed void fraction falls below the minimum free-flow fraction |
| `pressure_drop_limit` | Estimated pressure drop exceeds the 3.5 bar safety limit |

## Exit check — boundary cases + determinism

`run_boundary_self_test()` (`python pipeline.py --state uttarakhand --stage geometry`)
runs 8 cases (min/max diameter × min/max count, flow above/below limits, an
oversized capsule) **twice each** and checks the valid/reason output is
byte-identical both times. The geometry engine is state-agnostic — the
`--state uttarakhand` flag is accepted for CLI-contract consistency with
other stages but does not affect geometry calculations.

## Finding worth documenting (RESOLVED 2026-09-14): the 15%/20% Chen-style PCM levels are now reachable after the bounds widening

The framework doc asks Phase 5's DOE to include "the documented 10%, 15%,
20% PCM-volume cases where geometrically applicable" (Chen et al. 2025
baseline). Working through the **original** frozen bounds:

- Max capsule volume at the diameter ceiling (0.08 m) is ≈ 2.681×10⁻⁴ m³.
- Max capsule count was 24.
- Max reachable PCM volume = 24 × 2.681×10⁻⁴ = 6.434×10⁻³ m³ = **6.43 L**
  out of the 50 L tank = **12.9%** of tank volume.

So **15% and 20% were not achievable** with `capsule_diameter_m ≤ 0.08 m`
and `capsule_count ≤ 24` — reaching 20% required either ~37 capsules
at the diameter ceiling (above the old count bound) or capsules ~0.093 m
in diameter (above the diameter bound). This was a genuine interaction
between two independently-reasonable-looking bounds, discovered by
actually running the geometry engine rather than assumed.

**Fixed 2026-09-14** (`13_DESIGN_BOUNDS_WIDENING.md`, ported from Tamil
Nadu): `capsule_count.max` widened 24 → 37, verified directly —
`check_design(DesignVector(0.08, 37, 0.030))` → `valid=True,
pcm_volume_fraction=0.19838`. **Max reachable PCM volume fraction is now
19.84%**, landing right at `design_bounds_shared.yaml`'s own 20% ceiling
without needing to raise that ceiling too. Every design at `count ≤ 24`
remains exactly as valid as before — this only added previously
unreachable higher-fraction designs to the space Phases 5–7 search over.

**Consequence for Phase 4/5**: Gate 3's specific "fixed PCM"/"optimized-
looking" test cases still use `n_capsule=24` (≈12.9%) as a fixed,
unchanged reference point (`src/verify/gates.py` was not modified by the
widening — only `design_bounds_shared.yaml` was), but Phase 5's DOE and
Phase 7's search now sample the full widened range up to 19.84%, and
Phase 7 regime 3's actual selected design uses `n_capsule=31` — a count
only reachable after this widening (see `08_PHASE7_OPTIMIZATION.md`).

## How to re-run

```
python pipeline.py --state uttarakhand --stage geometry
```
(state-agnostic — geometry has no state-specific inputs, the flag is
accepted for CLI-contract consistency with the other stages.)
