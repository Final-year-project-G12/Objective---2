# 09 — What Phase 8 Needs From This Code, and What to Decide First

> **Status update: Phase 8 is now complete** (see
> `10_PHASE8_ROBUSTNESS_HANDOFF.md` and the Objective 3 contract). This
> document was written before Phase 8 existed, as a briefing for whoever
> built it — it is kept as-is because the **decision it raises below is
> still unresolved** and does not go away just because Phase 8 has since
> run; Phase 8's robustness results (every regime fails the demand and
> temperature-safety bars — see below) make this decision more urgent, not
> less. The "Reusable building blocks" and "Not built yet" sections at the
> bottom are historical — read `10_PHASE8_ROBUSTNESS_HANDOFF.md` for what
> actually exists now.

Phases 1–7 are done for Uttarakhand: simulator verified (GO), 215-case
DOE run, surrogate trained (R²>0.9998 on every target), one optimization
pass complete with 100 simulator-confirmed candidates. This note is what
a Phase 8 implementer (possibly you, later) should read first.

## The decision this project needs before Phase 8, not after

Phase 7 confirmed, with a 400-candidate-per-pair search, that:
- In **4 of 5 regimes** (0, 1, 3, 4): every shortlisted PCM beats plain
  water by an amount within the pre-declared 5% Pareto tolerance — and
  the selection rule correctly picks the zero-mass plain tank.
- In **regime 2** (coldest, Ta_mean~9.4°C): PureTemp 58 wins outright
  (best-found useful energy exceeds the regime's own plain-tank optimum)
  — the one case where the cold-climate/high-L_required combination
  actually allows the PCM to cycle meaningfully.

This is not a simulator bug (Gate 3's capability check already ruled that
out — a synthetic PCM with Tm=40°C clearly beats plain tank, +0.56% solar
fraction). It is a real finding about *this specific 50 L
direct-encapsulation design at these design bounds*.

Before writing Phase 8's recommendation cards, the team needs to decide
which of these to report as Uttarakhand's Objective 2 conclusion:

1. **Report it straight**: "for a 50 L direct-encapsulation tank at the
   frozen design bounds, Objective 1's shortlisted PCMs justify their added
   mass/cost over a plain tank in only 1/5 regimes (the coldest, most
   demanding climate regime)" — a valid, citable, comparative-across-states
   finding once Tamil Nadu/Rajasthan/Assam are compared (does regime 2's
   PCM win pattern generalize to other cold high-altitude regimes?).
2. **Widen the design bounds** (larger `capsule_diameter_m` ceiling or
   `capsule_count` ceiling in `design_bounds_shared.yaml`) to reach the
   documented 15–20% PCM-volume levels and re-run Phases 2–7 — but that
   file is frozen for all four states, so this is a Phase-0-gate decision,
   not a quiet local edit.
3. **Flag the `Tm_target_C` derivation back to whoever owns Objective 1**
   — Gate 3's capability check showed a PCM melting point matched to this
   tank's actual operating range (not the climate/delivery-anchored 57°C)
   does beat the plain tank. That derivation lives in Objective 1's
   `04b_climate_signature.py` (`SHARE_PCM`, `DRAW_VOLUME_L` chain).

This is a judgment call for the guide/team — do not let a DOE/surrogate
script silently decide it.

## Reusable building blocks now in place for Phase 8

- `results/uttarakhand/optimized_designs.csv` — every simulator-confirmed
  candidate with `sim_*` columns already computed; Phase 8's Monte Carlo
  should start from the `deployable_design_per_regime.csv` row per regime.
- `run_case(..., pcm_record_overrides=..., system_config_overrides=...)`
  already supports every Monte Carlo perturbation Phase 8 needs (latent
  heat ±10%, demand ±20%/±30min via `volume_multiplier`/
  `timing_shift_hours`, inlet/mains temperature via
  `mains_temp_override_C`) — no new simulator plumbing required.
- The medoid-only weather limitation is still open (Phase 5/7 doc) — a
  member-point robustness pass is the most valuable single addition before
  Phase 8's Monte Carlo, since "weather" is one of the dominant uncertainty
  sources the framework doc requires covering.

## Not built yet (at the time this document was originally written)

`src/robustness/`, `src/handoff/` (Objective 3 contract + recommendation
cards) were not started when this section was written. **They now exist**
— see `10_PHASE8_ROBUSTNESS_HANDOFF.md`. `results/uttarakhand/
recommendation_cards.md` and `obj3_environment_contract_uttarakhand.json`
are both generated and current.
