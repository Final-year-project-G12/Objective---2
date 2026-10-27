# Replicating Objectives 1-2 for Rajasthan, Assam, Uttarakhand

**Status as of 2026-10-25: none of the other 3 states have been started.**
Only Tamil Nadu exists (`tamilnadu_pipeline/` for Objective 1,
`objective2_design_optimization/` for Objective 2 — the current project).
No sibling Rajasthan/Assam/Uttarakhand code exists anywhere in this
workspace yet, despite an earlier doc (`tamilnadu_phase_docs/00_MASTER_
CHANGE_PLAN_TAMILNADU.md`) referencing a "Rajasthan-pilot" project — that
source was never actually present in this workspace and should not be
assumed to exist or be reachable.

This folder is a **from-scratch, generalized prompt sequence** — not a
copy of the Tamil-Nadu-specific migration docs in `tamilnadu_phase_docs/`
(those document a historical data-refresh event for an *already-built*
Tamil Nadu pipeline, not a "how to start a new state" guide, and they
reference a now-reverted methodology — see the next paragraph).

## Important: use the CURRENT methodology, not the historical detour

Tamil Nadu's own build went through a mid-course correction: an earlier
"Tm-retargeting + MCDM re-ranking" mechanism (docs 12/15) had Objective 2
silently re-deriving its own PCM target instead of using Objective 1's
real shortlist — found to violate the project's own objective statements,
and reverted (`../history/18_OBJECTIVE1_SHORTLIST_RESTORED.md`). **For a new state,
skip that detour entirely and go straight to the corrected approach**:
Objective 2 consumes Objective 1's `Tm_target_C` and `pcm_shortlist`
columns completely unedited, per climate regime. Do not re-implement
`retarget_tm.py`/`mcdm_reranking.py --apply` as part of the standard flow
— those scripts still exist and still work, but as an optional diagnostic
question only (see doc 18), never as the live mechanism.

## The two-part process, in order

1. **Objective 1** (new, per-state climate pipeline) — see
   `01_OBJECTIVE1_SETUP.md`. Produces `data/objective1/*_<state>.csv` for
   Objective 2 to consume. This is the larger, more open-ended piece
   (real climate data acquisition + clustering + MCDM).
2. **Objective 2** (config authoring + run) — see
   `02_OBJECTIVE2_CONFIG_AND_RUN.md`. Objective 2's own pipeline code
   (`pipeline.py --state <state>`) is **already state-parameterized** —
   confirmed by reading the code, not assumed. What's missing for a new
   state is only: that state's Objective 1 output, and a new
   `configs/states/<state>.yaml`.
3. **(Optional) CFD cross-verification** — see `03_CFD_VERIFICATION.md`,
   a basic Fluent/OpenFOAM sanity check of whatever design Objective 2
   selects, following the same approach already proven for Tamil Nadu
   (see `../CFD_VERIFICATION.md`).

## Cross-cutting rule (from the Tamil Nadu plan, still applies)

`configs/design_bounds_shared.yaml` and `configs/system_config_shared.yaml`
are meant to be **shared across all four states** — edit them once, not
per-state, unless a state genuinely needs different hardware assumptions
(tank size, collector spec). Don't fork these files per state without a
real reason; if you do, a future four-state comparison becomes invalid
unless every state's shared-config content matches.

## 2026-10-26/27 update: three fixes now baked into the shared code/config

Tamil Nadu's build surfaced and fixed three real issues in Objective 2's
own simulator and shared config — a new state inherits all three
automatically, with **no extra steps required**, since none of them are
Tamil-Nadu-specific:
1. A demand-timing bug (UTC vs. local-hour mismatch) in
   `src/simulation/tank_model.py` — fixed at the simulator level, applies
   to every state.
2. A genuine safety shield (hard temperature-trip, `safety.shield_enabled:
   true` in `system_config_shared.yaml`) — now enforced inside the
   simulator for every state, not just specified for Objective 3.
3. The shared tank/collector size is now **100 L / 2.5 m²**
   (`system_config_shared.yaml`, `config_v2.0_2026-10-26`) — resized up
   from an undersized 50 L / 1.5 m² after Tamil Nadu's own demand profile
   (300 L/day) proved too large for that pairing under IS 12976:2023
   guidance. This is a real hardware assumption, not a Tamil-Nadu-only
   diagnostic value, and per the cross-cutting rule above should NOT be
   re-forked per state — but it was *chosen* using Tamil Nadu's own demand
   profile, so **do check, don't assume**, whether a new state's demand
   profile (`configs/states/<state>.yaml`'s demand section) still makes
   100 L/2.5 m² adequate before trusting the inherited default; if not,
   that's a real reason to revisit the shared value for all four states,
   not to fork it silently for one.

Full detail, evidence, and the sweep that picked 100 L/2.5 m²: `../RESULTS.md`
(current, single reference for Tamil Nadu's numbers — supersedes `../history/`)
and `../TAMILNADU_REDESIGN_PLAN.md` §5/§5c.

## How to use these prompts

Each numbered file in this folder is written to be pasted directly as an
instruction to a Claude Code session, with `{STATE}` as a literal
placeholder to replace with the real state name (lowercase, e.g.
`rajasthan`) before use. They assume the session has this whole
`jammalamadugu/new_obj/` workspace open and can read `tamilnadu_pipeline/`
and `objective2_design_optimization/` as reference implementations.
