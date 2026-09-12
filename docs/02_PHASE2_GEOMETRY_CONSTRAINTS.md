# 02 — Phase 2 Audit: Geometry & Constraint Engine (All Four States)

Files: `src/design/schema.py`, `src/design/geometry.py`,
`src/design/constraints.py` — **byte-identical across Tamil Nadu,
Rajasthan, Assam, and Uttarakhand** (confirmed by direct `diff` between
the Tamil Nadu/Rajasthan/Uttarakhand copies; Assam's Phase 4 Gate 2
behavior is consistent with the same engine). Phase 2 has no
state-specific inputs — this is the one phase where "per-state summary"
is simply "one engine, run four times."

## Purpose (D2.2)

Given a design vector `[capsule_diameter_m, n_capsule, flow_rate_kg_s]`
(sphere shape, staggered arrangement — frozen for the 40-hr scope),
return volume/area/spacing/pressure-drop and a valid/invalid flag with
one reason code.

## Geometric model

- **Tank**: vertical cylinder, diameter/height derived from the frozen
  50 L volume at height = 2×diameter (tank diameter ≈ 0.317 m, height ≈
  0.634 m, identical in every state since the tank size is frozen).
- **Packing**: staggered horizontal layers, 2D hexagonal-lattice
  footprint per sphere.
- **Hydraulics**: pressure drop via the **Ergun equation** (Ergun, 1952)
  for flow through a packed bed of spheres.

## Exit check — identical result in every state

`run_boundary_self_test()` (`python pipeline.py --state <state> --stage
geometry`) runs 8 boundary cases (min/max diameter × min/max count, flow
above/below limits, an oversized capsule) twice each. **Result in all
four states: all 8 cases deterministic, no crashes, output matches
line-for-line** (only the printed state name differs).

## The one finding every state independently confirms: 12.9%, not 20%

This is a **shared-config finding**, not a per-state result — it
depends only on the frozen `design_bounds_shared.yaml`, so it is
identical in Tamil Nadu, Rajasthan, Assam, and Uttarakhand:

- Max capsule volume at the diameter ceiling (0.08 m): ≈ 2.681×10⁻⁴ m³.
- Max capsule count: 24.
- Max reachable PCM volume: 24 × 2.681×10⁻⁴ = 6.434×10⁻³ m³ = 6.43 L of
  the 50 L tank = **12.9%** — not the 15–20% Chen et al. (2025) report
  on their own (differently-sized) rig.

This single geometric fact is the root cause behind every state's Phase
4 Gate 3 finding that the shortlisted PCM barely (or never) beats plain
water: none of the four states can reach the PCM fraction the literature
associates with a decisive latent-storage benefit, within these frozen
bounds. Widening `capsule_diameter_m` or `capsule_count` in
`design_bounds_shared.yaml` would fix this for all four states at once,
but is a **frozen shared config** — a Phase-0-gate decision, not a
per-state edit (see `09_NEXT_STEPS.md`).

## Reason codes (shared vocabulary across all four states)

| Code | Meaning |
|---|---|
| `bounds_violation` | A raw variable (diameter, count, shape, arrangement, or the *derived* thickness) is outside `design_bounds_shared.yaml` |
| `flow_out_of_range` | Flow rate outside [0.010, 0.050] kg/s |
| `overlap` | Capsule too large to fit even once in the tank's cross-section |
| `volume_exceeded` | N_capsule × V_capsule exceeds the 20%-of-tank-volume ceiling |
| `passage_blocked` | Capsule stack doesn't fit within tank height, or void fraction falls below the free-flow minimum |
| `pressure_drop_limit` | Estimated pressure drop exceeds the 3.5 bar safety limit |

This shared vocabulary is what lets Phase 5's DOE report the same
`bounds_violation` rejection rate (~32.6–32.7%) in every state — the
same diameter/thickness bound interaction fires at essentially the same
rate regardless of climate, because it depends only on the frozen bounds
(see `06_PHASE5_DOE.md`).

## Literature review — why the Ergun equation, and why sphere/staggered-only

- **The Ergun equation** (Ergun, 1952, `Ergun1952PackedColumns`) is the
  standard, widely-cited correlation for pressure drop through a packed
  bed of particles, combining a viscous (linear-in-velocity) term and an
  inertial (quadratic-in-velocity) term. It is used here rather than a
  bespoke CFD-derived correlation because it is analytically closed-form,
  well-validated across decades of packed-bed literature, and matches the
  framework doc's explicit instruction to use a standard, citable
  correlation rather than deriving one from scratch for a student project
  of this scope.
- **Sphere-only, staggered-only capsules**: spherical PCM capsules with
  staggered packing are the most common geometry in the PCM-SWH
  literature this project draws on (Chen et al. 2025's flat-plate/PCM rig,
  Singh et al. 2025's review of direct-encapsulation designs) — choosing
  it here keeps the geometry engine's packing-density and Ergun-drop
  calculations analytically tractable, at the documented cost of not
  exploring cylindrical/slab/finned capsule geometries (an explicitly
  named 40-hr-scope cut, not an oversight).
- **The 20%-of-tank-volume PCM ceiling** in the frozen bounds is set to
  bracket, not exceed, Chen et al. (2025)'s own reported 10/15/20%
  PCM-volume sweep — the fact that this project's *derived* geometric
  ceiling (12.9%) falls short of the *bounds* ceiling (20%) is the
  bounds-interaction finding above, not a deliberate under-shoot.
