# Objective 3 — Inputs From Objective 2 and What To Do Next

Objective 2 is **complete** for Tamil Nadu (Phases 1–8, all built, run,
and verified — see `RESULTS.md` at the project root for the full digest).
This document is the hand-off: what Objective 3 receives, what it must
NOT touch, and the concrete first steps for building the
charge/discharge/bypass controller.

**The formal boundary** (do not cross it in either direction): Objective 1
selected the PCM. Objective 2 selected the physical hardware design and
validated operating envelope, below. **Objective 3 selects the real-time
action — nothing else.** It must not change PCM identity, capsule
geometry, tank volume, safety limits, or the physics model released here.

---

## 1. The one file Objective 3 actually needs

**`results/tamilnadu/obj3_environment_contract_tamilnadu.json`**
(built by `src/handoff/build_obj3_contract.py`, Phase 8b). This is the
frozen, machine-readable package — read it programmatically, don't
hand-copy numbers out of it. It contains, per climate regime:

- the selected PCM (or "plain tank, no PCM") with its complete property record
- capsule geometry (diameter, count, PCM mass, conduction distance)
- tank/collector configuration
- the flow envelope (nominal + min/max), pressure limit, pump efficiency
- delivery-temperature target and both safety temperature limits
- the validated simulator version tag (`sim_v1_tamilnadu`)
- a dynamic-state **schema** (field names, units, and which fields need a
  state estimator vs. a real sensor)
- both action-space options (discrete charge/discharge/bypass, and the
  recommended continuous-flow hybrid version) with the hard rule that the
  controller may never command outside the flow envelope or temperature
  limits
- a `global_limits` block (delivery target, both temperature limits,
  pressure limit, irradiance cutoff, flow envelope) for code that needs
  "the" envelope rather than iterating every regime
- the safety-shield condition list — trips on a **3°C precautionary guard
  band below each hard limit** (bypass at 72°C water / 62°C PCM, not at
  75°C/65°C themselves), so the shield engages before, not exactly at, the
  hard limit
- three reset scenarios (fully solid / partially charged / fully liquid
  initial PCM state)
- the acceptance-test checklist required before any DRL training starts
- an explicit `deferred_future_work` list (four-state comparison,
  active-learning/NSGA-II, member-point robustness, widened PCM bounds,
  hardware validation) — read it before assuming any of these are done

## 2. What Objective 2 is telling Objective 3 about the physical system

Read `00_MASTER_OVERVIEW.md` and `08_PHASE7_OPTIMIZATION.md` before writing
a reward function — the physical story matters for reward shaping:

- **4 of 5 regimes selected a plain sensible-water tank, not a PCM
  design.** Only regime 4 has an actual PCM (n-Octacosane) in its
  environment contract. A controller for regimes 0–3 is controlling a
  conventional solar water heater with no phase-change dynamics at all —
  `f_melt`, `T_pcm_t`, and PCM-related safety limits are not meaningful
  state for those regimes' contracts (they're present in the schema for
  structural consistency across regimes, but always 0/derived-from-water
  for the no-PCM regimes).
- **Regime 4's PCM only reaches high liquid fractions on the sunniest
  days** (mean f_melt ≈ 1–2% annually, per Phase 3/7 docs) — a
  charge-heavy policy will spend most of the year unable to charge past a
  small fraction of the PCM's latent capacity, not because of a bad
  policy but because of the collector/climate/geometry combination
  Objective 2 already characterized. Don't tune a reward function
  expecting deep cycling that the hardware doesn't actually produce.
- **No auxiliary/backup heater exists in this system.** "Unmet energy"
  in every Objective 2 metric means genuinely undelivered heat, not a
  gap an electric backup fills. If Objective 3's reward function assumes
  a backup exists, that assumption must be stated as a NEW addition, not
  inherited from Objective 2.
- **A real safety shield is not yet implemented in the physics model
  itself, and this is the single most important thing to fix before
  deployment.** Objective 2's simulator records temperature-safety
  violations but does not prevent them. Phase 7 found 65% of the 100
  nominal candidates searched violated the safety limit at some point in
  the year; Phase 8's Monte Carlo robustness analysis (120 draws/design
  under weather/demand/property uncertainty, using fixed
  cross-state-comparable thresholds) found something worse — **every one
  of the 5 selected designs fails the framework's 95% temperature-safety
  bar**, ranging from 67–87% safe for the plain-tank regimes down to just
  **44%** safe for the one regime with real PCM (regime 4) — see
  `10_PHASE8_ROBUSTNESS_HANDOFF.md` for the full table. Regime 4 also
  fails the 75% demand-reliability bar (70%) — the **only** regime to fail
  both criteria at once, making it the weakest performer in the state on
  every robustness axis, not just temperature. The `safety_shield` block
  in the contract already trips on a 3°C precautionary margin below each
  hard limit (72°C water / 62°C PCM, not 75°C/65°C) rather than exactly at
  the limit, but it is still a **specification** for Objective 3 to
  implement, not something already enforced upstream. Objective 3's
  acceptance test (§13.4 of the framework doc, replicated in the
  contract) exists specifically to verify this before training starts,
  and should be treated as a hard blocker, not a formality — the
  robustness numbers above are the quantitative reason why.

## 3. Concrete first steps for Objective 3

1. **Load the contract, don't re-derive it.** Parse
   `obj3_environment_contract_tamilnadu.json` for each regime's static
   design inputs — do not re-run Objective 2's optimizer or re-pick a PCM.
2. **Implement the safety shield first**, as a rule-based wrapper around
   the Objective 2 simulator (`src/simulation/tank_model.run_year`, or a
   step-by-step variant of it), before any RL code. Verify it independently
   using the acceptance-test list in the contract.
3. **Build a step-by-step (not annual-batch) version of the simulator.**
   Objective 2's `run_year()` runs a full year in one call, appropriate
   for design evaluation. Objective 3 needs a `step(action) -> (obs,
   reward, done, info)` interface — refactor `tank_model.py`'s inner
   timestep loop into a stateful stepper rather than rewriting the
   physics. The physics (enthalpy model, heat transfer, collector,
   hydraulics) should be reused unchanged; only the control surface
   changes (fixed flow_rate_kg_s becomes an action instead of a constant).
4. **Freeze the reward weights (w1..w5 in the contract's
   `reward_components_suggested`) before training**, and record them in
   Objective 3's own frozen config — this project deliberately left them
   unset because that is Objective 3's decision, not Objective 2's.
5. **Run the acceptance test with a trivial rule-based controller**
   (e.g. "charge whenever irradiance is high and PCM isn't full, discharge
   during demand hours, bypass otherwise") before writing any learning
   code. If this fails any of the six checks in the contract's
   `acceptance_test_before_drl_training` list, fix the environment before
   touching RL.
6. **Re-use, don't reopen, Objective 2's climate-regime split.** Train/
   validate/test across regimes 0–4 as Objective 2 defined them
   (`configs/states/tamilnadu.yaml`) — do not re-cluster or merge regimes.
7. **When Rajasthan/Assam/Uttarakhand versions of Objective 2 exist**,
   build one contract-consuming Objective 3 codebase that takes
   `--state` the same way Objective 2's `pipeline.py` does, rather than
   forking per-state controller code.

## 4. What Objective 2 explicitly did NOT resolve (don't assume it did)

- No unseen-weather-year or member-point re-confirmation of the final
  designs (medoid-only, 40-hr cut list) — Objective 3's own weather
  train/val/test split (§13.3) is genuinely unstarted work, not something
  to look for in Objective 2's outputs.
- No widened PCM design bounds and no re-investigation of the
  `Tm_target_C` derivation (see `09_NEXT_STEPS.md`) — if the project
  later decides to revisit either, Objective 3's contract will need to be
  regenerated from a new Phase 7 run, and any trained controller
  re-validated against it.
- Phase 8's robustness analysis covers PCM-property, weather-noise,
  demand and mains-temperature uncertainty only — pump/heat-transfer-
  coefficient and manufacturing-tolerance uncertainty (also listed in the
  full framework spec §11.1) were not sampled, per the 40-hr cut list.
