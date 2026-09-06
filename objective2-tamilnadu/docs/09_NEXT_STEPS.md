# 09 — What Phase 8 Needs From This Code, and What to Decide First

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

## Not built yet

`src/robustness/`, `src/handoff/` (Objective 3 contract + recommendation
cards) — Phase 8 is not started. `results/tamilnadu/recommendation_cards.md`
and `obj3_environment_contract_tamilnadu.json` do not exist yet.
