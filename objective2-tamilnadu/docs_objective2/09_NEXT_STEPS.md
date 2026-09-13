# 09 — What Phase 8 Needs From This Code, and What to Decide First

> **Status update: Phase 8 is now complete** (see
> `10_PHASE8_ROBUSTNESS_HANDOFF.md` and `RESULTS.md`). This document was
> written before Phase 8 existed, as a briefing for whoever built it — it
> is kept as-is because the **decision it raises below is still
> unresolved** and does not go away just because Phase 8 has since run;
> Phase 8's robustness results (every regime fails the 95% temperature-
> safety bar, and the PCM regime additionally fails the 75% demand bar)
> make this decision more urgent, not less. The "Reusable building
> blocks" and "Not built yet" sections at the bottom are historical —
> read `10_PHASE8_ROBUSTNESS_HANDOFF.md` for what actually exists now.

> **Status update 2026-09-13: RESOLVED.** Both options 2 and 3 were acted
> on — Tm-target retargeting (`12_TM_TARGET_RETARGETING.md`) and
> design-bounds widening (`13_DESIGN_BOUNDS_WIDENING.md`) — and Phases
> 5–8 were fully re-run against both. A **third** correction, not
> anticipated when this document was written, turned out to be the one
> that actually mattered most: the selection rule's plain-tank fallback
> was itself out of scope for Objective 2's actual problem statement
> (`14_SELECTION_RULE_SCOPE_CORRECTION.md`) and was removed. **Result:
> every regime's Objective 2 recommendation is now a genuine, optimal PCM
> design, beating plain tank on useful energy in all 5 regimes.** See
> `RESULTS.md` and `10_PHASE8_ROBUSTNESS_HANDOFF.md` for the final
> numbers, and `OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` for what this means
> for Objective 3 (a universal, not regime-4-only, safety-shield
> requirement). The rest of this document is kept for historical
> context — it accurately describes the state of the project on
> 2026-09-07 and the reasoning that led to the fixes above.

Phases 1–7 are done for Tamil Nadu: simulator verified (GO), 215-case
DOE run, surrogate trained (R²>0.98 on every target), one optimization
pass complete with 100 simulator-confirmed candidates. This note is what
a Phase 8 implementer (possibly you, later) should read first.

## The decision this project needs before Phase 8, not after

Phase 7 confirmed, with a 400-candidate-per-pair search (not just Gate
3's two hand-picked designs), that **every shortlisted PCM beats plain
water by ~0.08% at best — and the pre-declared 5% selection tolerance
correctly picks the zero-mass plain tank in 4 of 5 regimes** (see
`08_PHASE7_OPTIMIZATION.md`). This is not a simulator bug (Gate 3's
capability check already ruled that out — a melting point matched to this
tank's real operating range clearly does beat plain tank, +5 percentage
points). It is a real finding about *this specific 50 L
direct-encapsulation design at these design bounds* with *these three
climate-ranked PCMs*.

Before writing Phase 8's recommendation cards, the team needs to decide
which of these to report as Tamil Nadu's Objective 2 conclusion:

1. **Report it straight**: "for a 50 L direct-encapsulation tank at the
   frozen design bounds, none of Objective 1's shortlisted PCMs justify
   their added mass/cost over a plain tank in 4/5 regimes" — a valid,
   citable, comparative-across-states finding once Rajasthan/Assam/
   Uttarakhand are run the same way (do all four states show this, or is
   it Tamil-Nadu-specific?).
2. **Widen the design bounds** (larger `capsule_diameter_m` ceiling or
   `capsule_count` ceiling in `design_bounds_shared.yaml`) to reach the
   documented 15–20% PCM-volume levels and re-run Phases 2–7 — but that
   file is frozen for all four states, so this is a Phase-0-gate decision,
   not a quiet local edit.
3. **Flag the `Tm_target_C` derivation back to whoever owns Objective 1**
   — Gate 3's capability check showed a PCM melting point matched to this
   tank's real operating range (not the climate/delivery-anchored 57°C)
   clearly wins. That derivation lives in Objective 1's
   `04b_climate_signature.py` (`SHARE_PCM`, `DRAW_VOLUME_L` chain).

This is a judgment call for the guide/team — do not let a DOE/surrogate
script silently decide it by, e.g., quietly picking whichever PCM happens
to test best in a re-run.

## Reusable building blocks now in place for Phase 8

- `results/tamilnadu/optimized_designs.csv` — every simulator-confirmed
  candidate with `sim_*` columns already computed; Phase 8's Monte Carlo
  should start from the `deployable_design_per_regime.csv` row per regime.
- `run_case(..., pcm_record_overrides=..., system_config_overrides=...)`
  already supports every Monte Carlo perturbation Phase 8 needs (latent
  heat ±10%, demand ±20%/±30min via `volume_multiplier`/
  `timing_shift_hours`, inlet/mains temperature via
  `mains_temp_override_C`) — no new simulator plumbing required.
- The medoid-only weather limitation is still open (Phase 5/7 doc) — a
  member-point robustness pass is the most valuable single addition before
  Phase 8's Monte Carlo, since "weather" is one of the 3–4 dominant
  uncertainty sources the framework doc requires covering.

## Not built yet (at the time this document was originally written)

`src/robustness/`, `src/handoff/` (Objective 3 contract + recommendation
cards) were not started when this section was written. **They now exist**
— see `10_PHASE8_ROBUSTNESS_HANDOFF.md`. `results/tamilnadu/
recommendation_cards.md` and `obj3_environment_contract_tamilnadu.json`
are both generated and current.

## Literature

See `REFERENCES.md`. Option 2 (bounds widening) traces to **[Chen2025]**'s
documented 15–20% levels; option 3 (Tm retargeting) traces to
**[Rathore2024]**/**[AlMamun2023]**'s general operating-range-match
principle. Both were acted on (docs 12–13); the third, unanticipated fix
that actually resolved the finding (doc 14) was a scope correction, not a
literature-driven change — see that doc's own "Literature" note.
