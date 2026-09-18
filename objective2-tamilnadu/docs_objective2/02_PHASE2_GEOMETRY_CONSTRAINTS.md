# 02 — Phase 2 Audit: Geometry & Constraint Engine

> **SUPERSEDED 2026-09-17.** Describes the staggered-only geometry engine
> before capsule arrangement was restored as a searched variable. For the
> current 3-arrangement packing engine (and the void-fraction physics bug
> found while building it), see `docs_objective2/17_ARRANGEMENT_RESTORATION.md`
> and `docs_objective2/tamilnadu_phase_docs/02_PROMPT_PHASE2_GEOMETRY_TAMILNADU.md`.

> **Note (2026-09-13):** `capsule_count.max` was widened 24→37 after this
> doc was written — any "12.9% max reachable PCM fraction" figure below is
> superseded by ~19.8%. Code/methodology below (geometric model, reason
> codes) is unaffected; see `13_DESIGN_BOUNDS_WIDENING.md` for the current
> bound and finding.

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

`run_boundary_self_test()` (`python pipeline.py --state tamilnadu --stage geometry`)
runs 8 cases (min/max diameter × min/max count, flow above/below limits, an
oversized capsule) **twice each** and checks the valid/reason output is
byte-identical both times. Result: **all 8 cases deterministic, no
crashes** — satisfies the Phase 2 exit condition.

## Finding worth documenting: the 15%/20% Chen-style PCM levels are not geometrically reachable

The framework doc asks Phase 5's DOE to include "the documented 10%, 15%,
20% PCM-volume cases where geometrically applicable" (Chen et al. 2025
baseline). Working through the frozen bounds:

- Max capsule volume at the diameter ceiling (0.08 m) is ≈ 2.681×10⁻⁴ m³.
- Max capsule count is 24.
- Max reachable PCM volume = 24 × 2.681×10⁻⁴ = 6.434×10⁻³ m³ = **6.43 L**
  out of the 50 L tank = **12.9%** of tank volume.

So **15% and 20% are not achievable** with `capsule_diameter_m ≤ 0.08 m`
and `capsule_count ≤ 24` — reaching 20% would require either ~37 capsules
at the diameter ceiling (above the count bound) or capsules ~0.093 m in
diameter (above the diameter bound). This is a genuine interaction between
two independently-reasonable-looking bounds, discovered by actually
running the geometry engine rather than assumed. It is **not a bug** — the
framework doc's own phrasing ("where geometrically applicable") already
anticipates that not every documented level will fit every bound set — but
it must be stated plainly rather than silently testing only 10%/12% and
calling it "the 10/15/20% sweep."

**Consequence for Phase 4/5**: the "fixed PCM" and "optimized-looking"
baseline designs used in Gate 3 use the actual maximum reachable fraction
(`n_capsule=24, diameter=0.08` → 12.87%) rather than a nominal "20%" that
the geometry engine would silently cap or reject. Phase 5's DOE should
either (a) accept 10–13% as the practically testable range given these
bounds, or (b) if the guide wants a genuine 15–20% test, widen
`capsule_diameter_m` or `capsule_count` in `design_bounds_shared.yaml` —
but that is a **frozen shared config**, so per the Phase 0 gate, changing
it means every state re-runs from Phase 2 onward.

## How to re-run

```
python pipeline.py --state tamilnadu --stage geometry
```
(state-agnostic — geometry has no state-specific inputs, the flag is
accepted for CLI-contract consistency with the other stages.)

## Literature

- **[Chen2025]** is the direct source of the 15%/20% PCM-volume-fraction
  test levels this doc found unreachable at the original bounds — the
  finding that motivated doc 13's `capsule_count.max` widening.
- **[Kou2025]** independently confirms that capsule geometry / packing
  parameter interactions are a recurring, real constraint in PCM-TES
  design literature, not an artifact unique to this project's bound
  choices.
- **Ergun (1952)** (classical packed-bed correlation, cited in-code, not
  part of `vertopal.com_references.txt`) grounds the pressure-drop model
  in `constraints.py`/`hydraulic_model.py`.
