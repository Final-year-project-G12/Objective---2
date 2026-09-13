# Objective 3 — Inputs From Objective 2 and What To Do Next (Rajasthan)

Objective 2 is **complete** for Rajasthan (Phases 1–8, all built, run, and
verified — see `README.md` at the project root and `results/README.md`
for the full digest). This document is the hand-off: what Objective 3
receives, what it must NOT touch, and the concrete first steps for
building the charge/discharge/bypass controller.

Mirrors `objective2-tamilnadu/docs_objective2/OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md`
— same structure, Rajasthan's own numbers throughout.

**The formal boundary** (do not cross it in either direction): Objective 1
selected the PCM. Objective 2 selected the physical hardware design and
validated operating envelope, below. **Objective 3 selects the real-time
action — nothing else.** It must not change PCM identity, capsule
geometry, tank volume, safety limits, or the physics model released here.

---

## 1. The one file Objective 3 actually needs

**`results/obj3_environment_contract_rajasthan.json`** (built by
`src/handoff/build_obj3_contract.py`, Phase 8b). This is the frozen,
machine-readable package — read it programmatically, don't hand-copy
numbers out of it. It contains, per climate regime:

- **Updated 2026-09-14**: the selected PCM (**all 3 Rajasthan regimes now
  select a shortlisted PCM** — RT45HC / Paraffin-HDPE PCM6 / Paraffin-HDPE
  PCM3, one per regime, see §2) with its complete property record. This
  reverses an earlier all-plain-tank contract, superseded when the
  rule-based safety shield became the pipeline default and the Phase 7
  selection rule was corrected to no longer let the plain tank win by
  tie-break (see `docs/09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md` §8).
- capsule geometry (diameter, count, PCM mass, conduction distance)
- tank/collector configuration
- the flow envelope (nominal + min/max), pressure limit, pump efficiency
- delivery-temperature target and both safety temperature limits
- the validated simulator version tag (`sim_v1_rajasthan`)
- a dynamic-state **schema** (field names, units, and which fields need a
  state estimator vs. a real sensor)
- the recommended continuous-flow hybrid action space (mode +
  continuous `flow_rate_kg_s`) with the hard rule that the controller may
  never command outside the flow envelope or temperature limits
- a `global_limits` block (delivery target, both temperature limits,
  pressure limit, irradiance cutoff, flow envelope) for code that needs
  "the" envelope rather than iterating every regime
- the safety-shield condition list — trips on a **3 °C precautionary guard
  band below each hard limit** (bypass at 72 °C water / 62 °C PCM, not at
  75 °C/65 °C themselves), so the shield engages before, not exactly at,
  the hard limit
- robustness probabilities embedded per regime (Phase 8 Monte Carlo — see
  §2 below)
- three reset scenarios (fully solid / partially charged / fully liquid
  initial PCM state)
- the acceptance-test checklist required before any DRL training starts
- an explicit `deferred_future_work` list (multi-state comparison,
  active-learning/NSGA-II, member-point robustness, widened PCM bounds,
  hardware validation) — read it before assuming any of these are done

## 2. What Objective 2 is telling Objective 3 about the physical system

Read `docs/00_MASTER_OVERVIEW.md` and `docs/07_PHASE7_OPTIMIZATION.md`
before writing a reward function — the physical story matters for reward
shaping. **This section was rewritten 2026-09-14** to match the current
pipeline default (rule-based safety shield active since 2026-09-13 +
PCM-only Phase 7 selection rule since 2026-09-14); the prior all-plain-
tank / no-shield version of this section is quoted at the end for the
historical record.

- **All 3 of Rajasthan's regimes now select a shortlisted PCM design**
  (RT45HC / Paraffin-HDPE PCM6 / Paraffin-HDPE PCM3), each beating the
  best plain-tank geometry the same search found by a fraction of a
  percent in useful energy, and each clearing both the 75 °C water and
  65 °C PCM limits with a ~2.8–2.9 °C margin. `f_melt`, `T_pcm_C`, and
  the PCM-related safety limit are now live, meaningful state for every
  Rajasthan regime's contract, not structural placeholders — a
  controller for Rajasthan is controlling a real phase-change system in
  all 3 regimes.
- **A rule-based safety shield IS implemented in the physics model
  itself, and is the pipeline default as of 2026-09-13**
  (`system_config_shared.yaml: safety_shield.enabled: true`,
  `src/simulation/tank_model.py`): the pump is forced to bypass the
  collector loop once water reaches 72 °C, and PCM charging is blocked
  once PCM temperature reaches 62 °C — a 3 °C precautionary guard band
  below each hard limit (75 °C / 65 °C), citing IS 12976:2023 §8.2 as the
  standard Indian method for this exact mechanism. This is no longer a
  **specification** for Objective 3 to implement from scratch — Objective
  2's own simulator already enforces it, for every phase (5 through 8),
  not only at the Monte Carlo step. Objective 3 inherits a working
  reference implementation to build on (or replace with something
  smarter), not a blank page.
- **Phase 8's Monte Carlo robustness analysis (120 draws/design,
  weather/demand/mains uncertainty) now shows all 3 selected PCM designs
  are robustly safe**: P(temp-safe) = 1.00 in every regime (up from
  0.45–0.57 for the earlier, now-superseded plain-tank/no-shield
  baseline), P95 max water temperature 72.2–72.3 °C in every regime — the
  shield converges every regime's worst-case draws to just above its own
  72 °C trigger point, exactly as designed. See
  `docs/08_PHASE8_ROBUSTNESS_HANDOFF.md` for the full table (and its
  "superseded result" subsection for the pre-shield numbers).
- **This narrows, but does not eliminate, Objective 3's justification.**
  The original brief for this section argued the controller's job was
  "make the system survive at all" — that argument no longer holds,
  since O2's own fixed-threshold shield already achieves 100%
  temperature safety. What remains is the case Emami et al. (2025/2026)
  and this project's own CLAUDE.md §3.4 make: real-time weather/demand
  stochasticity is still better handled by a learned policy than a fixed
  72 °C/62 °C threshold, which necessarily bypasses collector energy it
  may not have strictly needed to reject — a DRL controller's job is to
  beat this shield's energy efficiency while matching (or improving on)
  its 100% safety record, not to invent safety where none existed.
- **No auxiliary/backup heater exists in this system.** "Unmet energy"
  in every Objective 2 metric means genuinely undelivered heat, not a
  gap an electric backup fills. If Objective 3's reward function assumes
  a backup exists, that assumption must be stated as a NEW addition, not
  inherited from Objective 2. (Unchanged by the shield/selection-rule
  update.)
- **All 3 regimes clear the demand bar** (P(meets annual demand)
  83.3–98.3%; the 75% threshold holds in all 3) alongside the now-clean
  temperature-safety record — a reward function still should not conflate
  "delivers enough hot water" with "does so safely," since Phase 8 tracks
  them as genuinely separate mechanisms (the shield trades a small amount
  of collected energy for safety; it does not automatically guarantee
  demand is met, and vice versa), even though both currently pass.

### What this section said before the 2026-09-13/14 updates (superseded, kept for the record)

> All 3 of Rajasthan's regimes selected a plain sensible-water tank, not
> a PCM design. None of the environment contracts carried a real PCM.
> No PCM candidate cleared the 65 °C safety limit anywhere in Rajasthan
> (0/45 across all regimes and all shortlisted PCMs). A real safety
> shield was not yet implemented in the physics model itself — Objective
> 2's simulator recorded temperature-safety violations but did not
> prevent them — and every one of the 3 selected (plain-tank) designs
> failed the framework's 95% temperature-safety bar badly (P(temp-safe)
> 45–57%). This was the finding that originally motivated treating an
> active overheat bypass as an Objective 3 first-class requirement,
> "more urgently than for any other state run under this framework so
> far." That framing is now out of date in degree (the shield is real and
> O2's own default) but not in spirit (see the narrowed justification
> above).

## 3. Concrete first steps for Objective 3

1. **Load the contract, don't re-derive it.** Parse
   `obj3_environment_contract_rajasthan.json` for each regime's static
   design inputs — do not re-run Objective 2's optimizer or re-pick a PCM.
2. **Reuse, don't reimplement, the safety shield.** Unlike the original
   version of this brief, the shield is now already implemented inside
   `src/simulation/tank_model.py` and active by default
   (`system_config_shared.yaml: safety_shield.enabled: true`) — Objective
   3's step-by-step environment (item 3 below) should call the same
   shield logic rather than writing a new rule-based wrapper from
   scratch. Still verify it independently using the acceptance-test list
   in the contract before trusting it inside a training loop, and treat
   "does my step-by-step refactor preserve the shield's 100% P(temp-safe)
   record" as a hard regression check, not a checkbox — a step-by-step
   refactor that silently drops or weakens the shield would reintroduce
   exactly the failure mode the original (pre-2026-09-13) version of this
   brief warned about.
3. **Build a step-by-step (not annual-batch) version of the simulator.**
   Objective 2's `run_year()` runs a full year in one call, appropriate
   for design evaluation. Objective 3 needs a `step(action) -> (obs,
   reward, done, info)` interface — refactor `tank_model.py`'s inner
   timestep loop into a stateful stepper rather than rewriting the
   physics. The physics (enthalpy model, heat transfer, collector,
   hydraulics) should be reused unchanged; only the control surface
   changes (fixed `flow_rate_kg_s` becomes an action instead of a
   constant). `run_case()`'s `weather_perturbation` keyword (added in
   Phase 8) is a ready-made seam for injecting Objective 3's own
   train/val/test weather noise the same way Phase 8's Monte Carlo does.
4. **Freeze the reward weights (w1..w5 in the contract's
   `reward_components_suggested`) before training**, and record them in
   Objective 3's own frozen config — this project deliberately left them
   unset because that is Objective 3's decision, not Objective 2's.
5. **Run the acceptance test with a trivial rule-based controller**
   (e.g. "charge whenever irradiance is high and the tank isn't near the
   safety limit, discharge during demand hours, bypass otherwise") before
   writing any learning code. If this fails any of the six checks in the
   contract's `acceptance_test_before_drl_training` list, fix the
   environment before touching RL.
6. **Re-use, don't reopen, Objective 2's climate-regime split.** Train/
   validate/test across regimes 0–2 as Objective 2 defined them
   (`configs/states/rajasthan.yaml`) — do not re-cluster or merge regimes.
7. **When Assam/Uttarakhand/Tamil Nadu versions of Objective 2 exist (or
   are complete)**, build one contract-consuming Objective 3 codebase
   that takes `--state` the same way Objective 2's `pipeline.py` does,
   rather than forking per-state controller code.

## 4. What Objective 2 explicitly did NOT resolve (don't assume it did)

- No unseen-weather-year or member-point re-confirmation of the final
  designs (medoid-only, 40-hr cut list) — Objective 3's own weather
  train/val/test split is genuinely unstarted work, not something to
  look for in Objective 2's outputs.
- No widened PCM design bounds and no re-investigation of the
  `Tm_target_C` derivation — if the project later decides to revisit
  either, Objective 3's contract will need to be regenerated from a new
  Phase 7 run, and any trained controller re-validated against it.
- Phase 8's robustness analysis covers weather-noise, demand, and mains-
  temperature uncertainty only (PCM-property uncertainty is structurally
  inapplicable here — every selected design is the plain tank); pump/
  heat-transfer-coefficient and manufacturing-tolerance uncertainty (also
  listed in the full framework spec §11.1) were not sampled, per the
  40-hr cut list.
- **Rajasthan-specific, updated 2026-09-14**: all 3 regimes now deploy a
  real PCM design, and Phase 4's Gate 1–5 battery was run (GO, 5/5 gates
  clean) — but that Gate battery predates both the safety-shield default
  and the corrected Phase 7 selection rule, and was never re-run against
  the shield-enabled physics or against the specific PCM designs now
  selected (RT45HC / Paraffin-HDPE PCM6 / Paraffin-HDPE PCM3). The PCM
  physics (`capsule_enthalpy.py`, `heat_transfer.py`) is the same,
  verified engine used for Tamil Nadu's PCM regime and for Rajasthan's
  own Phase 3 smoke runs, but a Gate 1–5 re-run specifically against the
  shielded physics and today's three selected designs has not been done.
  Treat that as open verification work before fully trusting these
  numbers the way a from-scratch Gate re-run would justify.
