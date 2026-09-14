# 13 — Design Bounds Widening: `capsule_count.max` 24 → 37 (2026-09-14)

**Status: APPLIED to `configs/design_bounds_shared.yaml`. Ported from `objective2-tamilnadu`'s identical widening (2026-09-12) — that project's `docs_objective2/13_DESIGN_BOUNDS_WIDENING.md` explicitly noted "Rajasthan/Assam/Uttarakhand have NOT had this bound widened/re-run yet — it is shared config, so it applies whenever those states' Objective 2 is run next." This is that run. Phases 2 and 5–8 have been fully re-run against it for Uttarakhand, together with the Tm-target retargeting (doc 12) and the selection-rule scope correction — see `08_PHASE7_OPTIMIZATION.md` for what actually happened.**

This is a deliberate, documented methodology revision — not a silent edit.

## Why

`02_PHASE2_GEOMETRY_CONSTRAINTS.md` already flagged, before this change, that the documented 15%/20% PCM-volume-fraction test levels (the Chen et al. 2025 baseline this project cites) were **not geometrically reachable** within the old bounds: `capsule_diameter_m ≤ 0.08 m` and `capsule_count ≤ 24` topped out at **12.9%** maximum reachable `pcm_volume_fraction`.

Tracing the actual binding constraint: with `capsule_diameter_m` capped at its own 0.08 m ceiling, `capsule_count=24` — not the diameter cap, and not `design_bounds_shared.yaml`'s own stated `pcm_volume_fraction` ceiling of 0.20 — was the real bottleneck.

## What changed

```yaml
capsule_count: {min: 8, max: 24, step: 1}   # before
capsule_count: {min: 8, max: 37, step: 1}   # after (config_v1.1_2026-09-14)
```

`capsule_count.max = 37` reaches `pcm_volume_fraction = 0.1984` (verified directly: `check_design(DesignVector(0.08, 37, 0.030))` → `valid=True, pcm_volume_fraction=0.19838`) — landing right at the file's own existing `0.20` ceiling without needing to raise that ceiling too. Every design at `count ≤ 24` remains exactly as valid as before; the widened range only **adds** previously-unreachable higher-PCM-fraction designs to the space Phases 5–7 search over.

This is a **shared config** (`configs/design_bounds_shared.yaml`) — each state folder keeps its own physical copy of this file (it is not one file symlinked across states), so the widening had to be applied to Uttarakhand's own copy explicitly; it does not update automatically when Tamil Nadu's copy changes.

## What this does NOT change

- `capsule_diameter_m` bounds (`[0.02, 0.08] m`) — unchanged.
- `flow_rate_kg_s` bounds — unchanged.
- The `pcm_volume_fraction` ceiling itself (`0.20`) — unchanged.
- Phase 2 geometry/constraint logic (`src/design/constraints.py`) — unchanged.

## Result after re-running Phases 2–8

- Phase 2 self-test: max reachable PCM-volume-fraction confirmed at **19.84%** (up from 12.9%).
- Phase 5 DOE: the widened space is reflected in `design_cases.csv` — max `n_capsule` sampled is now 37 (max achieved `pcm_volume_fraction` in the actual 215-case LHS/boundary sample: 16.8%).
- Phase 7: regime 3's selected design uses `n_capsule=31` (a count only reachable after this widening) — see `08_PHASE7_OPTIMIZATION.md`.
- The combined effect of retargeting + widening did **not** eliminate the "PCM's own temperature exceeds the safety limit on hot days" finding in 4 of 5 regimes — more available PCM mass and a better-matched melting point improved the useful-energy margin over plain tank slightly, but did not change the fundamental physical picture. See `08_PHASE7_OPTIMIZATION.md` and `10_PHASE8_ROBUSTNESS_HANDOFF.md`.
