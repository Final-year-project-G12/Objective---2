# 02 — Phase 2 Audit: Geometry & Constraint Engine (Rajasthan)

Files: `src/design/schema.py`, `src/design/geometry.py`, `src/design/constraints.py`.

> As of 2026-09-17 these modules **diverge from `objective2-tamilnadu/src/design/`**
> — Rajasthan was run as the pilot state for `Objective2 Consolidated
> plan.md`'s corrected 4-variable design vector (capsule arrangement
> restored as a searched variable, per the objective statement's own four
> named parameters: diameter, arrangement, count, flow). Tamil Nadu, Assam,
> and Uttarakhand have not received the identical change yet.

## Purpose (D2.2)

Given a design vector `[capsule_diameter_m, n_capsule, flow_rate_kg_s,
capsule_arrangement]` (sphere shape stays frozen — never named in the
objective statement, so that remains a documented scope cut), return
volume/area/spacing/pressure-drop and a valid/invalid flag with one reason
code. Universal across all four states.

## Geometric model

- **Tank**: vertical cylinder. Diameter/height are *derived* once from the
  frozen 50 L volume assuming height = 2×diameter (a stated proportion
  assumption, not measured) — `tank_dimensions_m()`. Result: tank diameter
  ≈ 0.317 m, height ≈ 0.634 m.
- **Packing — three arrangement-branched models**, dispatched by
  `pack_capsules(arrangement, diameter_m, tank_diameter_m, tank_height_m,
  n_capsule, spacing_min_m)`:
  - `pack_staggered` — 2D hexagonal-lattice footprint per sphere (the
    original, pre-2026-09-17 sole model). Footprint area per capsule =
    `(sqrt(3)/2) * pitch^2`.
  - `pack_single_layer` — simple square-grid spacing, no row offset.
    Footprint area per capsule = `pitch^2` — strictly larger than
    staggered's hex footprint at the same pitch, so this arrangement packs
    fewer capsules per layer by construction, not by an artificial penalty.
  - `pack_radial` — concentric rings of capsules around the tank's
    vertical axis. Ring 0 is a single capsule on the centerline; ring
    `k>0` holds `floor(2*pi*r_k / ring_pitch)` capsules, `r_k = k *
    ring_pitch`.
  - All three arrangements stack layers/rings up the tank height the same
    way and return a common `PackingResult` interface
    (`capsules_per_layer`, `n_layers`, `stack_height_m`, `void_fraction`).
  - **`void_fraction` is now a packing-structure quantity, not a mass-balance
    one.** It is computed from each arrangement's own lattice footprint —
    `1 - (n_capsule * V_capsule) / (bed_footprint_area * stack_height_m)`
    — so it genuinely differs across arrangements even for the identical
    `(diameter, count, flow)` triple. This feeds the `passage_blocked`
    check and the Ergun hydraulics below. `pcm_volume_fraction` (used for
    `volume_exceeded`) is a separate, purely mass-balance quantity
    (`n_capsule * V_capsule / V_tank`) and stays arrangement-agnostic, since
    it depends only on capsule count and volume, not on how they are
    spatially arranged.
- **Hydraulics**: pressure drop via the **Ergun equation** (Ergun, 1952) for
  flow through a packed bed of spheres — a standard, citable correlation,
  not derived from scratch, per the framework doc's requirement. Pump
  power = Δp·V̇/η_pump. Because it consumes the arrangement-specific
  `void_fraction` above, pressure drop and pump power now vary by
  arrangement too (see `03_PHASE3_GREYBOX_SIMULATOR.md` for how large that
  effect actually is in practice — it is small).

## Reason codes

No new reason codes were introduced when arrangement was restored — the
same six codes are just now computed from whichever packing model the
arrangement dispatches to.

| Code | Meaning |
|---|---|
| `bounds_violation` | A raw variable (diameter, count, shape, arrangement, or the *derived* thickness) is outside `design_bounds_shared.yaml` |
| `flow_out_of_range` | Flow rate outside [0.010, 0.050] kg/s |
| `overlap` | Capsule too large to fit even once in the tank's cross-section at the minimum spacing, for the given arrangement |
| `volume_exceeded` | N_capsule × V_capsule exceeds the 20%-of-tank-volume ceiling (mass-balance, arrangement-agnostic) |
| `passage_blocked` | The capsule stack doesn't fit within the tank height, or the arrangement's own packing void fraction falls below the minimum free-flow fraction |
| `pressure_drop_limit` | Estimated pressure drop exceeds the 3.5 bar safety limit |

## Exit check — boundary cases, determinism, and cross-arrangement sanity

`run_boundary_self_test()` (`python pipeline.py --state rajasthan --stage geometry`)
runs the original 8 boundary cases (min/max diameter × min/max count, flow
above/below limits, an oversized capsule) **once per arrangement (24
cases total)**, each run twice, and checks the valid/reason output is
byte-identical both times:

```
  min_diameter_min_count [single-layer]      valid=False reason=bounds_violation     deterministic=True
  max_diameter_max_count [single-layer]      valid=True  reason=None                 deterministic=True
  min_diameter_max_count [single-layer]      valid=False reason=bounds_violation     deterministic=True
  max_diameter_min_count [single-layer]      valid=True  reason=None                 deterministic=True
  mid_case [single-layer]                    valid=True  reason=None                 deterministic=True
  flow_below_min [single-layer]              valid=False reason=flow_out_of_range    deterministic=True
  flow_above_max [single-layer]              valid=False reason=flow_out_of_range    deterministic=True
  oversized_diameter_for_tank [single-layer] valid=False reason=bounds_violation     deterministic=True
  ... (same 8 cases repeated for [staggered] and [radial]) ...

  All 24 boundary cases deterministic: True

  Cross-arrangement sanity (same d=0.05, n=14, flow=0.030):
    single-layer   void_fraction=0.7801881857177827     pressure_drop_pa=0.0002043368652251768
    staggered      void_fraction=0.7779102822429281     pressure_drop_pa=0.00020912000105411443
    radial         void_fraction=0.7808351840194597     pressure_drop_pa=0.0002029947415395535
  Dispatcher genuinely branches (values differ across arrangements): True
```

(The `min_diameter_*` cases reject with `bounds_violation` because the
derived `pcm_thickness_m = diameter/2 = 0.01 m` is below the 0.02 m
thickness floor — the real interaction between the diameter bound and the
independently-checked thickness bound, unrelated to arrangement, see
below.)

The cross-arrangement sanity case exists to catch a dispatcher that
silently no-ops (returns identical results regardless of the arrangement
argument) — confirmed not the case here: void fraction and pressure drop
both differ measurably across all three arrangements for the same design
vector.

## Per-arrangement max-reachable PCM-volume-fraction table

`get_max_reachable_pcm_fraction(arrangement, diameter_m=0.08, count_max=37)`
sweeps capsule count at the diameter ceiling for each arrangement and
reports the largest still-valid PCM volume fraction:

| Arrangement | Max N feasible (at d=0.08 m) | Max reachable PCM vol. fraction |
|---|---|---|
| single-layer | 37 | 0.1984 |
| staggered | 37 | 0.1984 |
| radial | 37 | 0.1984 |

**Finding — identical across all three arrangements, not a bug.** At
`d=0.08 m`, the shared 20% mass-based `pcm_volume_fraction` ceiling
(`volume_exceeded`) binds before any arrangement's own packing/passage
constraint does — none of the three arrangements' `capsules_per_layer` /
`stack_height_m` geometry forces a `passage_blocked` or `overlap`
rejection before N=37 at this diameter. This is reported here rather than
silently narrowing the shared count bound per arrangement, per the
consolidated plan's instruction (§0.2) not to paper over a per-arrangement
asymmetry (or, as it turns out, a lack of one) without saying so.
Arrangement differences do show up downstream — Phase 5's DOE rejection
rates differ modestly by arrangement (38.7-44.4%, see
`05_PHASE5_DOE.md`), and Phase 7's search surfaces genuinely different
top-5 compositions per regime×PCM pair (see `07_PHASE7_OPTIMIZATION.md`)
— just not at this single diameter-ceiling slice.

**Historical note (pre-2026-09-17, staggered-only, count ceiling 24):**
under the original bounds, max reachable PCM volume fraction was 12.9%
(`n_capsule=24, diameter=0.08 m`) — short of the 15%/20% Chen et al.
(2025) reference levels. The count ceiling was widened 24→37 specifically
to close that gap (`pcm_volume_fraction` bound of 0.10-0.20 stays
unchanged); the 19.84% figure above confirms the widened ceiling reaches
essentially the full 20% target, for all three arrangements.

## How to re-run

```
python pipeline.py --state rajasthan --stage geometry
```
(state-agnostic — geometry has no state-specific inputs, the flag is
accepted for CLI-contract consistency with the other stages.)
