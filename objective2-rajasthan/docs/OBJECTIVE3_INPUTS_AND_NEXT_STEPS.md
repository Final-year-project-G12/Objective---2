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

- the selected PCM (or "plain tank, no PCM" — **all 3 Rajasthan regimes
  selected the plain tank**, see §2) with its complete property record
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
shaping:

- **All 3 of Rajasthan's regimes selected a plain sensible-water tank,
  not a PCM design.** None of the environment contracts carry a real
  PCM. A controller for Rajasthan is controlling a conventional solar
  water heater with no phase-change dynamics at all — `f_melt`,
  `T_pcm_C`, and PCM-related safety limits are not meaningful state for
  any Rajasthan regime's contract (they're present in the schema for
  structural consistency with future PCM-bearing states, but always
  0/derived-from-water here).
- **No PCM candidate cleared the 65 °C safety limit anywhere in
  Rajasthan** (0/45 across all regimes and all shortlisted PCMs, Phase 7)
  — this is a stronger and more general finding than "the best PCM
  wasn't worth its cost" (Tamil Nadu's finding in 4/5 regimes): in
  Rajasthan's hot-dry climate, every shortlisted PCM's melting point sits
  inside a temperature band the tank itself already reaches on an
  ordinary sunny day, so PCM never survives long enough to matter.
- **No auxiliary/backup heater exists in this system.** "Unmet energy"
  in every Objective 2 metric means genuinely undelivered heat, not a
  gap an electric backup fills. If Objective 3's reward function assumes
  a backup exists, that assumption must be stated as a NEW addition, not
  inherited from Objective 2.
- **A real safety shield is not yet implemented in the physics model
  itself, and this is the single most important thing to fix before
  deployment — more urgently than for any other state run under this
  framework so far.** Objective 2's simulator records
  temperature-safety violations but does not prevent them. Phase 8's
  Monte Carlo robustness analysis (120 draws/design under
  weather/demand/mains uncertainty, fixed cross-state-comparable
  thresholds) found that **every one of the 3 selected (plain-tank)
  designs fails the framework's 95% temperature-safety bar by a wide
  margin** — P(temp-safe) ranges **45–57%**, i.e. roughly half of
  realistic operating scenarios exceed the 75 °C water scald limit even
  with no PCM in the tank at all. Regime 1 is the worst (P(temp-safe) =
  45%; P95 max water temperature 88.2 °C) because its nominal Phase 7
  safety margin was only 2.6 °C, which a single above-average-GHI or
  above-average-mains draw erases. See
  `docs/08_PHASE8_ROBUSTNESS_HANDOFF.md` for the full table. The
  `safety_shield` block in the contract already trips on a 3 °C
  precautionary margin below each hard limit (72 °C water / 62 °C PCM,
  not 75 °C/65 °C), but it is still a **specification** for Objective 3 to
  implement, not something already enforced upstream. Objective 3's
  acceptance test (contract's `acceptance_test_before_drl_training`
  list) exists specifically to verify this before training starts, and
  should be treated as a hard blocker, not a formality — the robustness
  numbers above are the quantitative reason why.
- **All 3 regimes mostly clear the demand bar** (P(meets annual demand)
  80.0–99.2%; the 75% threshold holds in all 3) even though every regime
  fails temperature safety — so a
  reward function should not conflate "delivers enough hot water" with
  "does so safely." These are the two axes Phase 8 tracks separately for
  exactly this reason.

## 3. Concrete first steps for Objective 3

1. **Load the contract, don't re-derive it.** Parse
   `obj3_environment_contract_rajasthan.json` for each regime's static
   design inputs — do not re-run Objective 2's optimizer or re-pick a PCM.
2. **Implement the safety shield first**, as a rule-based wrapper around
   the Objective 2 simulator (`src/simulation/tank_model.run_year`, or a
   step-by-step variant of it), before any RL code. Verify it
   independently using the acceptance-test list in the contract. Given
   the 33–51% P(temp-safe) numbers above, treat this step as the
   project's actual bottleneck, not a checkbox — a policy trained without
   a working shield will spend most of its operating time in an unsafe
   regime by construction.
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
- **Rajasthan-specific**: because 0/45 PCM candidates cleared the safety
  limit, this project never validated the simulator's PCM-charging
  dynamics against a *deployed* Rajasthan design — the PCM physics
  (`capsule_enthalpy.py`, `heat_transfer.py`) is the same, verified engine
  used for Tamil Nadu's one PCM regime, but no Rajasthan-specific PCM
  run went through Phase 4's Gate 1–5 battery as a *selected* design.
  If a future bounds-widening exercise makes a Rajasthan PCM design
  deployable, re-run Phase 4 before trusting its numbers the way this
  document trusts the plain-tank ones.
