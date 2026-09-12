# Objective 3 — Inputs From Objective 2 and What To Do Next

Objective 2 is **complete** for Uttarakhand (Phases 1–8, all built, run,
and verified — see `00_MASTER_OVERVIEW.md` for the full digest). This
document is the hand-off: what Objective 3 receives, what it must NOT
touch, and the concrete first steps for building the
charge/discharge/bypass controller.

**The formal boundary** (do not cross it in either direction): Objective 1
selected the PCM. Objective 2 selected the physical hardware design and
validated operating envelope, below. **Objective 3 selects the real-time
action — nothing else.** It must not change PCM identity, capsule
geometry, tank volume, safety limits, or the physics model released here.

---

## 1. The one file Objective 3 actually needs

**`results/uttarakhand/obj3_environment_contract_uttarakhand.json`**
(built by `src/handoff/build_obj3_contract.py`, Phase 8b). This is the
frozen, machine-readable package — read it programmatically, don't
hand-copy numbers out of it. It contains, per climate regime:

- the selected PCM (or "plain tank, no PCM") with its complete property record
- capsule geometry (diameter, count, PCM mass, conduction distance) — only
  regime 2 has capsules; regimes 0, 1, 3, 4 are plain-tank designs
- tank/collector configuration
- the flow envelope (nominal + min/max), pressure limit, pump efficiency
- delivery-temperature target (50°C, matching Objective 1's `T_DELIVERY_C`)
  and both safety temperature limits
- the validated simulator version tag (`sim_v1_uttarakhand`)
- a dynamic-state **schema** (field names, units, and which fields need a
  state estimator vs. a real sensor)
- both action-space options (discrete charge/discharge/bypass, and the
  recommended continuous-flow hybrid version) with the hard rule that the
  controller may never command outside the flow envelope or temperature limits
- a `global_limits` block for code that needs "the" envelope
- the safety-shield condition list — trips on a **3°C precautionary guard
  band below each hard limit** (bypass at 72°C water / 62°C PCM, not at
  75°C/65°C themselves)
- a **fully specified `reward_function`** — formula, normalized reference
  magnitudes, default weights `w1..w5` with an explicit rationale, and a
  tuning procedure. Ready-to-train-with defaults, not a placeholder.
- three reset scenarios (fully solid / partially charged / fully liquid
  initial PCM state)
- the acceptance-test checklist required before any DRL training starts
- an explicit `deferred_future_work` list

## 2. What Objective 2 is telling Objective 3 about the physical system

Read `00_MASTER_OVERVIEW.md` and `08_PHASE7_OPTIMIZATION.md` before writing
a reward function — the physical story matters for reward shaping:

- **4 of 5 regimes selected a plain sensible-water tank, not a PCM
  design.** Only regime 2 has an actual PCM (PureTemp 58, Tm=58°C) in its
  environment contract. A controller for regimes 0, 1, 3, 4 is controlling
  a conventional solar water heater with no phase-change dynamics at all —
  `f_melt`, `T_pcm_t`, and PCM-related safety limits are not meaningful
  state for those regimes' contracts (they're present in the schema for
  structural consistency, but always 0/derived-from-water for the no-PCM
  regimes).
- **Regime 2's PureTemp 58 does cycle meaningfully** (mean f_melt ≈ 34.4%
  in the matched-Tm capability check; the selected design cycles at a lower
  but non-negligible rate under real operating conditions). This is the
  one Uttarakhand regime where phase-change control logic is physically
  relevant. The cold climate (Ta_mean~9.4°C, T_mains=7.4°C) drives the
  tank into the PCM's operating range more reliably than the warmer regimes.
- **Uttarakhand's solar fractions are structurally low (28–41% nominal).**
  Phase 8's Monte Carlo shows P(meets demand, SF≥50%) = 0.0% across all
  5 regimes — this is a climate consequence, not a control failure to fix.
  Objective 3's reward function should not penalize the controller for
  failing to hit a 50% solar fraction that the hardware physically cannot
  reach under Uttarakhand's conditions. Consider using the regime-specific
  nominal solar fraction as the reference point rather than the fixed 50%
  bar.
- **Regime 2's PCM design is the safest under robustness analysis
  (P(temp-safe)=100.0%)**. The cold climate prevents overheating naturally.
  Regimes 0 and 3 (the warmest plain-tank designs) are the most
  problematic for temperature safety. Objective 3's bypass logic matters
  most for those regimes.
- **No auxiliary/backup heater exists in this system.** "Unmet energy" in
  every Objective 2 metric means genuinely undelivered heat. If Objective
  3's reward function assumes a backup exists, that assumption must be
  stated as a NEW addition, not inherited from Objective 2.
- **A real safety shield is not yet implemented in the physics model
  itself.** Objective 2's simulator records temperature-safety violations
  but does not prevent them. The `safety_shield` block in the contract
  already trips on a 3°C precautionary margin (72°C water / 62°C PCM),
  but it is still a **specification** for Objective 3 to implement, not
  something already enforced upstream.

## 3. Concrete first steps for Objective 3

1. **Load the contract, don't re-derive it.** Parse
   `obj3_environment_contract_uttarakhand.json` for each regime's static
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
   physics.
4. **Start from the contract's `reward_function` defaults.** The contract
   ships fully specified default weights — copy them into Objective 3's
   own frozen config as the training starting point, then follow the
   contract's `tuning_procedure` if retuning is needed after a first run.
5. **Adapt the demand reference for Uttarakhand's climate.** The fixed
   50% solar-fraction bar used in Phase 8's robustness analysis is
   appropriate for cross-state comparability (matching Tamil Nadu and
   Rajasthan) — but for Objective 3's reward signal, using the
   *regime-specific nominal solar fraction* as the "success" reference
   is more informative than a bar the hardware can never clear.
6. **Run the acceptance test with a trivial rule-based controller** before
   writing any learning code. If this fails any of the six checks in the
   contract's `acceptance_test_before_drl_training` list, fix the
   environment before touching RL.
7. **Re-use, don't reopen, Objective 2's climate-regime split.** Train/
   validate/test across regimes 0–4 as Objective 2 defined them
   (`configs/states/uttarakhand.yaml`) — do not re-cluster or merge regimes.
8. **When Tamil Nadu/Rajasthan/Assam versions of Objective 2 exist**,
   build one contract-consuming Objective 3 codebase that takes
   `--state` the same way Objective 2's `pipeline.py` does.

## 4. What Objective 2 explicitly did NOT resolve (don't assume it did)

- Phase 8's Monte Carlo draws its *annual* weather magnitude from a real
  10-year historical ensemble (see `10_PHASE8_ROBUSTNESS_HANDOFF.md`),
  but no unseen-weather-year or member-point re-confirmation of the final
  designs' *hourly* shape exists yet (medoid-only, 40-hr cut list) —
  Objective 3's own weather train/val/test split is still genuinely
  unstarted work.
- No widened PCM design bounds and no re-investigation of the `Tm_target_C`
  derivation (see `09_NEXT_STEPS.md`) — if the project later decides to
  revisit either, Objective 3's contract will need to be regenerated from
  a new Phase 7 run, and any trained controller re-validated against it.
- Phase 8's robustness analysis covers PCM-property, weather-noise, demand
  and mains-temperature uncertainty only — pump/heat-transfer-coefficient
  and manufacturing-tolerance uncertainty (also listed in the full framework
  spec §11.1) were not sampled, per the 40-hr cut list.
- Uttarakhand's elevation inconsistency (three coexisting elevation values —
  see `01_PHASE1_CONFIG_AND_STATE_SETUP.md`) is a known Objective 1
  limitation carried forward. If elevation affects the climate-regime
  assignment for specific grid points materially, a future Objective 1
  re-run with a consistent elevation source would require Objective 2
  (and Objective 3) to re-run from Phase 2 onward.
