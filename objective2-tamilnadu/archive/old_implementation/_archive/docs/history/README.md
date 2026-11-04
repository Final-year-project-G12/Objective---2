# History — Full Methodology & Evolution Record

**Not required reading.** For the current, authoritative picture, see the
root `README.md` and `../RESULTS.md`. This folder preserves the real
engineering history — nothing here was deleted, only moved out of the
main view to reduce clutter (per a 2026-10-25 documentation cleanup).

## What's in here, roughly chronologically

- `00_MASTER_OVERVIEW.md` — the old primary overview doc (now superseded
  by the root `README.md` + `../RESULTS.md`), useful for its "findings
  worth reading" section and literature-per-phase pointers.
- `01_PHASE1_CONFIG_AND_STATE_SETUP.md` through
  `10_PHASE8_ROBUSTNESS_HANDOFF.md` — the original Phase 1-8
  implementation docs, each describing what was built and why. Some
  describe a pre-2026-09-17 run (K=5 regimes, staggered-arrangement-only)
  that no longer reflects current numbers — read for methodology/design
  rationale, not current results.
- `12_TM_TARGET_RETARGETING.md` through `15_MCDM_RERANKING_AND_SAFETY_
  TIEBREAK.md` — a methodology detour (Objective 2 re-deriving its own
  PCM melting-point target and re-ranking candidates) later found to
  violate the project's own objective-statement boundary between
  Objective 1 (material selection) and Objective 2 (hardware design) —
  see `18_OBJECTIVE1_SHORTLIST_RESTORED.md` for the correction. Docs
  13-15's non-PCM-selection content (bounds widening, selection-rule
  scope, safety-first tie-break) still applies as current methodology.
- `16_OBJECTIVE1_DATA_REFRESH.md`, `17_ARRANGEMENT_RESTORATION.md` — the
  2026-09-17 upstream refresh (K=5→K=3 regimes, real elevation data) and
  capsule-arrangement-as-searched-variable restoration.
- `18_OBJECTIVE1_SHORTLIST_RESTORED.md` — the scope-violation correction
  above, and the final Phase 5-8 re-run that produced the numbers now in
  `../RESULTS.md`.
- `tamilnadu_phase_docs/` — the actual prompt sequence used to execute
  the 2026-09-17/18 refresh, phase by phase. More procedural/literal than
  the numbered docs above; useful as a template for replicating this
  process on a new state (see `../other_states_prompts/` for the
  generalized version of this).
- `archive/` — earlier superseded snapshots (an old `RESULTS.md`, an
  external framework audit report, the Phase 6b multi-fidelity add-on
  doc — broken, never re-run against current data).
- `plots_narrative/` — narrative `.md` write-ups describing each phase's
  plots; the plots themselves are current (`results/tamilnadu/plots/`)
  but these text companions were never updated to match and are stale.
- `O2_Implementation_Plan_FreeSimulators.md`,
  `O2_free_simulators_survey_2026-09-24.md` — the planning/survey work
  that led to choosing ANSYS Fluent + OpenFOAM for the CFD
  cross-verification now documented, current, in `../CFD_VERIFICATION.md`.
