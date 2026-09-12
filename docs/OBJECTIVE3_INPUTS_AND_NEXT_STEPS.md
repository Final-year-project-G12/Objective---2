# Objective 3 — Inputs From Objective 2 and What To Do Next (All Four States)

## Hand-off status by state

| State | Contract file exists? | Safe to build a controller against it today? |
|---|---|---|
| Tamil Nadu | `obj3_environment_contract_tamilnadu.json` | Yes — with the caveat that no regime is robustly safe (see below) |
| Rajasthan | `obj3_environment_contract_rajasthan.json` | Yes — same caveat, worse margins |
| Assam | **Does not exist** | **No** — Phase 7's selected designs are not validated (safety-verdict bug), and Phase 8 was never run |
| Uttarakhand | `obj3_environment_contract_uttarakhand.json` | Yes — with the same caveat, plus regime 0's nominal design is itself marginally unsafe |

**Do not start Objective 3 work on Assam yet.** Fix Phase 7's selection
(re-filter through the real 65 °C/75 °C limits, likely forcing the plain
tank in some or all regimes), then run Phase 8, before generating a
contract for that state.

## What every completed contract tells Objective 3, regardless of state

**The formal boundary** (do not cross it in either direction): Objective
1 selected the PCM. Objective 2 selected the physical hardware design
and validated operating envelope. **Objective 3 selects the real-time
action — nothing else.** No contract lets Objective 3 change PCM
identity, capsule geometry, tank volume, safety limits, or the physics
model Objective 2 released.

Every completed contract (Tamil Nadu, Rajasthan, Uttarakhand) contains,
per regime: the selected PCM (or "plain tank"), full geometry, the flow
envelope, both safety temperature limits, the validated simulator
version tag, a dynamic-state schema (measurable vs. estimator-needed
fields), a discrete and a continuous-flow hybrid action space, a
`global_limits` block, a `safety_shield` with a 3 °C precautionary guard
band (bypass at 72 °C water / 62 °C PCM, not at the hard 75/65 limits
themselves), a fully-specified default `reward_function` with weights
`w1..w5` and an explicit tuning procedure, 3 PCM-state reset scenarios,
and a 6-item pre-training acceptance-test checklist.

## Cross-state facts that should shape reward-function design

- **No state has an auxiliary/backup heater modeled.** "Unmet energy"
  means genuinely undelivered heat everywhere — if Objective 3 assumes a
  backup exists in any state's reward function, that must be a stated
  NEW addition, not something inherited from Objective 2.
- **No state has a real safety shield in the physics model itself** —
  every simulator records temperature-safety violations but does not
  prevent them. This makes implementing the safety shield as a
  rule-based wrapper, *before* any RL code, the literal first step in
  every state, not an optional hardening pass.
- **Most regimes across all three completed states are plain-tank
  designs** (9 of 13 total regimes across Tamil Nadu/Rajasthan/
  Uttarakhand) — a controller for those regimes has no phase-change
  dynamics to reason about at all; `f_melt`, `T_pcm`, and PCM-specific
  safety limits are structural placeholders there, always
  0/derived-from-water.
- **Demand-reliability reference points differ sharply by state and must
  not be conflated**: Rajasthan/Tamil Nadu mostly clear the 75% demand
  bar even while failing temperature safety; Uttarakhand's nominal solar
  fractions are structurally below the fixed 50% demand bar in every
  regime — a reward function ported from Rajasthan to Uttarakhand
  unchanged would punish Uttarakhand's controller for a ceiling the
  hardware cannot physically reach. Consider a regime-specific nominal
  reference for climates like Uttarakhand's, as that state's own hand-off
  doc recommends.
- **Overheat protection is a first-class control objective everywhere**,
  not just in the states/regimes that use PCM — Rajasthan's worst
  temperature-safety numbers (45–57%) belong entirely to plain-tank
  designs; the hot-dry climate alone, with no PCM present, is enough to
  make this a hard requirement.

## Concrete first steps (apply per completed state; do not skip to Assam until fixed)

1. **Load the contract, don't re-derive it.** Parse the JSON for each
   regime's static design inputs — never re-run Objective 2's optimizer
   or re-pick a PCM from inside Objective 3's code.
2. **Implement the safety shield first**, as a rule-based wrapper around
   the Objective 2 simulator, before any RL code. Verify it against the
   contract's acceptance-test checklist.
3. **Build a step-by-step (`step(action) -> obs, reward, done, info`)
   version of the simulator** by refactoring `tank_model.py`'s inner
   timestep loop into a stateful stepper — reuse the physics unchanged;
   only the control surface (fixed flow rate becomes an action) changes.
   `run_case()`'s `weather_perturbation` keyword (added for Phase 8) is
   already a usable seam for Objective 3's own train/val/test weather
   noise.
4. **Start from each contract's own `reward_function` defaults** (where
   present — Rajasthan's earlier contract left weights unset as "not yet
   Objective 2's decision"; Tamil Nadu's and Uttarakhand's are fully
   specified) rather than inventing new ones from scratch.
5. **Run the acceptance test with a trivial rule-based controller**
   before writing any learning code, per-state.
6. **Re-use, don't reopen, each state's own climate-regime split** — do
   not re-cluster or merge regimes across states.
7. **Build one contract-consuming Objective 3 codebase that takes
   `--state`**, the same way Objective 2's `pipeline.py` does, rather
   than forking per-state controller code — this only becomes possible
   once all four states have a valid contract, which is not yet true.

## What Objective 2 explicitly has not resolved, in any state

- No unseen-weather-year or member-point re-confirmation of final
  designs' *hourly* shape (medoid-only everywhere; Tamil Nadu/Uttarakhand's
  robustness pass uses real historical *annual* magnitude only).
- No widened PCM design bounds and no re-investigation of `Tm_target_C`
  derivation anywhere — see `09_NEXT_STEPS.md`.
- Pump/heat-transfer-coefficient and manufacturing-tolerance uncertainty
  were never sampled in any state's robustness pass.
- Assam's two open issues (§ above) — unresolved as of this writing.
