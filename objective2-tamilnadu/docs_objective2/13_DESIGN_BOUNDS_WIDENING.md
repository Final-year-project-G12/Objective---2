# 13 — Design Bounds Widening: `capsule_count.max` 24 → 37 (2026-09-12)

**Status: APPLIED to `configs/design_bounds_shared.yaml` (shared across all 4 states). Applied after the Tm-target retargeting (doc 12); Phases 2 and 5–8 have since been fully re-run against it for Tamil Nadu, together with the selection-rule scope correction (doc 14) — see `RESULTS.md` for final, current numbers. The "Expected direction of effect (not yet confirmed)" section below is kept as a historical record of what was predicted before that re-run; see `08_PHASE7_OPTIMIZATION.md` for what actually happened. Rajasthan/Assam/Uttarakhand have NOT had this bound widened/re-run yet — it is shared config, so it applies whenever those states' Objective 2 is run next.**

This is a deliberate, documented methodology revision — not a silent edit.

## Why

`docs_objective2/02_PHASE2_GEOMETRY_CONSTRAINTS.md` (and `RESULTS.md`'s Phase 2 section) already flagged, before this change, that the documented 15%/20% PCM-volume-fraction test levels (the Chen et al. 2025 baseline this project cites) were **not geometrically reachable** within the old bounds: `capsule_diameter_m ≤ 0.08 m` and `capsule_count ≤ 24` topped out at **12.9%** maximum reachable `pcm_volume_fraction` (at `n=24, d=0.08m`).

Tracing the actual binding constraint: with `capsule_diameter_m` capped at its own 0.08 m ceiling, `capsule_count=24` — not the diameter cap, and not `design_bounds_shared.yaml`'s own stated `pcm_volume_fraction` ceiling of 0.20 — was the real bottleneck keeping the design space from ever reaching the literature's tested PCM-loading levels.

## What changed

```yaml
capsule_count: {min: 8, max: 24, step: 1}   # before
capsule_count: {min: 8, max: 37, step: 1}   # after (config_v1.1_2026-09-12)
```

`capsule_count.max = 37` was chosen because it reaches `pcm_volume_fraction = 0.198` — verified geometrically valid (passes the existing overlap/passage/pressure checks in `src/design/constraints.py`) — landing right at the file's own existing `0.20` ceiling **without needing to raise that ceiling too**. This is the smallest change that closes the gap: every design at `count ≤ 24` remains exactly as valid as it was before (nothing is invalidated, no rejection criteria changed), and the widened range only **adds** previously-unreachable higher-PCM-fraction designs to the space Phases 5–7 search over.

This is a **shared config** (`configs/design_bounds_shared.yaml` applies to all 4 states in the unified framework, not just Tamil Nadu), so the effect and the required re-run apply to every state, not only the one currently implemented (Tamil Nadu).

## What this does NOT change

- `capsule_diameter_m` bounds (`[0.02, 0.08] m`) — unchanged.
- `flow_rate_kg_s` bounds — unchanged.
- The `pcm_volume_fraction` ceiling itself (`0.20`) — unchanged; the widened count reaches it, doesn't raise it.
- Any Phase 2 geometry/constraint logic (`src/design/constraints.py`) — unchanged; this is a bounds-file edit only, not a code change to how validity is computed.
- Phase 1–4 findings that don't depend on the reachable design space (e.g. the simulator verification gates) — unaffected.

## What DOES need to change / re-run

Per the framework's Phase 0 gate, a shared-config bounds change requires re-running **Phases 2–8** (not just 5–7 — Phase 2's own "maximum reachable PCM-volume-fraction" self-test, and its plots/finding text in `RESULTS.md`, are computed against the bounds file and are now stale too), for **every state**, not only Tamil Nadu:

1. `python pipeline.py --state <state> --stage geometry` — Phase 2 self-test; the "12.9% max reachable" finding should be re-verified (expected to move toward ~19.8%).
2. `python pipeline.py --state <state> --stage doe` — Phase 5, regenerates `design_cases.csv` over the now-larger design space.
3. `python pipeline.py --state <state> --stage surrogate` — Phase 6, retrain on the new DOE set.
4. `python pipeline.py --state <state> --stage optimize` — Phase 7, re-search and re-confirm.
5. `python pipeline.py --state <state> --stage robustness` then `--stage handoff` — Phase 8, since Phase 7's selected designs will change.

**As of 2026-09-12, none of these have been re-run against the widened bound yet** for Tamil Nadu (the `results/tamilnadu/` DOE/surrogate/optimize outputs on disk were generated between the Tm-target retargeting and this widening — see the ordering note in `docs_objective2/12_TM_TARGET_RETARGETING.md`). Treat every quantitative Phase 2/5/6/7/8 number in the current `RESULTS.md` as describing the **pre-widening** design space until this re-run happens.

## Literature

- **[Chen2025]** is the direct source of the 15%/20% PCM-volume-fraction
  levels this widening was designed to reach — see `REFERENCES.md` for
  the full citation and Phase 2's original reachability finding
  (`02_PHASE2_GEOMETRY_CONSTRAINTS.md`).
- **[Kou2025]** independently confirms that capsule packing/geometry
  bound interactions limiting the reachable PCM fraction are a real,
  recurring issue in this literature, not unique to this project's
  bound choices.

## Expected direction of effect (not yet confirmed by a re-run)

Widening `capsule_count` allows designs with substantially more PCM mass per unit volume than were reachable before (up to ~0.198 vs ~0.129 fraction — roughly 50% more PCM by volume at the new ceiling). Whether this changes the "PCM barely beats plain tank" finding (Phases 4/6/7, and now also seen in the retargeted-but-pre-widening Phase 7 run per doc 12) is an open, re-run-dependent question — more PCM mass could either close the ~0.08% gap or simply cost more pump/pressure-drop for the same marginal benefit. Do not assume either outcome; re-run and report what actually comes out.
