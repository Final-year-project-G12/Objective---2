# Objective 3 — Inputs From Objective 2 and What To Do Next

> **⚠️ NUMBERS BELOW ARE SUPERSEDED, 2026-09-17 — read this box before
> anything else in this document.** Everything below reflects the
> 2026-09-14 run (`sim_v1_tamilnadu`, K=5 regimes, arrangement frozen to
> staggered-only). Since then: (1) Objective 1 was refreshed (K=5→K=3
> regimes, real elevation, rewritten MCDM engine —
> `docs_objective2/16_OBJECTIVE1_DATA_REFRESH.md`) and (2) capsule
> arrangement was restored as a searched variable
> (`docs_objective2/17_ARRANGEMENT_RESTORATION.md`). **Objective 3 must
> consume `results/tamilnadu/obj3_environment_contract_tamilnadu.json` as
> it exists NOW** (`contract_version: "obj3_contract_v2.0_2026-09-17"`,
> `validated_simulator_version: "sim_v2_tamilnadu"`, 3 regimes each with a
> `capsule_arrangement` field — currently "radial" in every regime — and
> an `arrangement_rationale`) — not any cached copy, and not the specific
> regime IDs/numbers quoted in the prose below, which describe regimes
> 0-4 of a run that no longer exists. Current headline: **no regime meets
> the 95% temperature-safety robustness bar** (P(temp-safe) = 0%/18%/0%
> for regimes 0/1/2) — the safety-shield requirement this document
> describes is, if anything, MORE universally binding now, not less. See
> `docs_objective2/tamilnadu_phase_docs/08_PROMPT_PHASE8_HANDOFF_TAMILNADU.md`
> for current numbers. The formal boundary and contract *structure*
> described below (regime → PCM → geometry → flow envelope → safety
> shield → action space) are unchanged and still accurate.

Objective 2 is **complete** for Tamil Nadu (Phases 1–8, all built, run,
and verified — see `docs_objective2/00_MASTER_OVERVIEW.md` for the
current summary). The paragraph below describes the 2026-09-14 state and
is kept for historical context only (see the box above for what's current):
after five methodology revisions (Tm-target retargeting, design-bounds
widening, selection-rule scope correction, full-MCDM shortlist adoption,
and a safety-first selection tie-break — docs 12/13/14/15) that together
made every regime's Objective 2 recommendation a genuine PCM design (not
the mostly-plain-tank result of the original run), with regime 4's design
then genuinely, not just nominally, temperature-safe.

**The formal boundary** (do not cross it in either direction): Objective 1
selected the PCM shortlist. Objective 2 selected the physical hardware
design and validated operating envelope, below. **Objective 3 selects the
real-time action — nothing else.** It must not change PCM identity,
capsule geometry, tank volume, safety limits, or the physics model
released here.

---

## 1. The one file Objective 3 actually needs

**`results/tamilnadu/obj3_environment_contract_tamilnadu.json`**
(built by `src/handoff/build_obj3_contract.py`, Phase 8b). This is the
frozen, machine-readable package — read it programmatically, don't
hand-copy numbers out of it. It contains, per climate regime:

- the selected PCM — **every one of the 5 regimes now has a real PCM**
  (n-Tetracosane ×2, n-Hexacosane ×2, RT45HC) with its complete property
  record
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
- a **fully specified `reward_function`** — formula, normalized reference
  magnitudes (computed from this state's own 5 selected designs), default
  weights `w1..w5` with an explicit rationale for each, precise
  `Penalty_safety_t`/`Penalty_bypass_t` definitions tied to the same
  guard-band trigger as the safety shield, and a tuning procedure. These
  are ready-to-train-with defaults, not a placeholder — see §3 point 4
  below.
- three reset scenarios (fully solid / partially charged / fully liquid
  initial PCM state)
- the acceptance-test checklist required before any DRL training starts
- an explicit `deferred_future_work` list (four-state comparison,
  active-learning/NSGA-II, sub-daily/hourly multi-year weather records,
  hardware validation) — read it before assuming any of these are done

## 2. What Objective 2 is telling Objective 3 about the physical system

Read `RESULTS.md`, `08_PHASE7_OPTIMIZATION.md`,
`14_SELECTION_RULE_SCOPE_CORRECTION.md`, and
`15_MCDM_RERANKING_AND_SAFETY_TIEBREAK.md` before writing a reward
function — the physical story matters for reward shaping, and it changed
substantially from earlier drafts of this document:

- **All 5 regimes now have a real, optimal PCM design — not 4 plain-tank
  + 1 PCM.** `f_melt`, `T_pcm_t`, and PCM-related safety limits are live,
  meaningful state in **every** regime's contract now, not just regime 4.
  A controller that special-cases "no PCM" for 4 of the 5 regimes would
  be building against a stale assumption.
- **Every PCM design uses a modest mass** (0.33–2.29 kg across the 5
  regimes — regime 4's RT45HC design is the heaviest, a deliberate
  consequence of the safety-first tie-break, not an error) matched to
  each regime's own real charging-hour water temperature (46.5–51.5°C,
  not Objective 1's original climate-anchored 57°C) — expect meaningful,
  regular melt/freeze cycling in normal operation, not the near-zero
  cycling the original (pre-retargeting) n-Octacosane-based design
  showed. Don't assume the earlier "PCM barely melts" characterization
  still applies; it was specific to the since-corrected Tm-target
  mismatch.
- **No auxiliary/backup heater exists in this system.** "Unmet energy"
  in every Objective 2 metric means genuinely undelivered heat, not a
  gap an electric backup fills. If Objective 3's reward function assumes
  a backup exists, that assumption must be stated as a NEW addition, not
  inherited from Objective 2.
- **A real safety shield is not yet implemented in the physics model
  itself, and this is now a universal, not regime-specific, requirement —
  the single most important thing to fix before deployment.** Objective
  2's simulator records temperature-safety violations but does not
  prevent them. Phase 8's Monte Carlo robustness analysis (120 draws/
  design, weather/demand/property uncertainty including a real 10-year
  historical weather ensemble) found: **regimes 0–3 are 0% temperature-
  safe across all 120 draws each** — never safe, not a tail risk — and
  **regime 4 is 30.8% safe**, from a real nominal margin of +0.39°C (RT45HC,
  chosen by the safety-first tie-break, doc 15 — an improvement over an
  earlier, now-superseded pick whose margin was a razor-thin 0.009°C).
  See `10_PHASE8_ROBUSTNESS_HANDOFF.md` for the full table. The
  `safety_shield` block in the contract already trips on a 3°C
  precautionary margin below each hard limit (72°C water / 62°C PCM, not
  75°C/65°C) rather than exactly at the limit, but it is still a
  **specification** for Objective 3 to implement, not something already
  enforced upstream. Objective 3's acceptance test (§13.4 of the
  framework doc, replicated in the contract) exists specifically to
  verify this before training starts, and should be treated as a hard
  blocker, not a formality — the robustness numbers above are the
  quantitative reason why, and they apply to **every** regime now, not
  only one.
- **Why every design runs hot regardless of PCM choice**: this tank's
  water temperature reaches 70–72°C on sunny days in regimes 0–3
  (documented in `08_PHASE7_OPTIMIZATION.md`'s minimal-PCM-dose test),
  which is safe for water (75°C limit) but ~5–7°C over PCM's fixed 65°C
  material-stability ceiling — regardless of how much PCM is present or
  what its melting point is. This is exactly the physical trigger
  condition Objective 3's bypass action needs to anticipate (via the
  guard-banded safety shield above), not something Objective 2 could
  design around within its own scope.

## 3. Concrete first steps for Objective 3

1. **Load the contract, don't re-derive it.** Parse
   `obj3_environment_contract_tamilnadu.json` for each regime's static
   design inputs — do not re-run Objective 2's optimizer or re-pick a PCM.
2. **Implement the safety shield first**, as a rule-based wrapper around
   the Objective 2 simulator (`src/simulation/tank_model.run_year`, or a
   step-by-step variant of it), before any RL code. Verify it independently
   using the acceptance-test list in the contract. **This is not optional
   or regime-specific** — every regime's nominal design already runs over
   the PCM temperature limit at some point in the year.
3. **Build a step-by-step (not annual-batch) version of the simulator.**
   Objective 2's `run_year()` runs a full year in one call, appropriate
   for design evaluation. Objective 3 needs a `step(action) -> (obs,
   reward, done, info)` interface — refactor `tank_model.py`'s inner
   timestep loop into a stateful stepper rather than rewriting the
   physics. The physics (enthalpy model, heat transfer, collector,
   hydraulics) should be reused unchanged; only the control surface
   changes (fixed flow_rate_kg_s becomes an action instead of a constant).
4. **Start from the contract's `reward_function` defaults, don't invent
   new ones from scratch.** The contract ships fully specified default
   weights (`w1..w5`) with an explicit rationale each — copy them into
   Objective 3's own frozen config as the training starting point, then
   follow the contract's `tuning_procedure` list if retuning is needed
   after a first training run.
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
   forking per-state controller code. Note that those states' Objective 2
   runs have NOT yet had the Tm-retargeting/bounds-widening/selection-rule/
   MCDM-reranking fixes applied (docs 12–15 are Tamil-Nadu-only so far) —
   do not assume their contracts already describe all-PCM, safety-checked
   designs until confirmed.

## 4. What Objective 2 explicitly did NOT resolve (don't assume it did)

- Phase 8's Monte Carlo draws its *annual* weather magnitude from a
  real 10-year historical ensemble (see `10_PHASE8_ROBUSTNESS_HANDOFF.md`),
  but no unseen-weather-year or member-point re-confirmation of the final
  designs' *hourly* shape exists yet (medoid-only, 40-hr cut list) —
  Objective 3's own weather train/val/test split (§13.3) is still
  genuinely unstarted work.
- Phase 8's robustness analysis covers PCM-property, weather-noise,
  demand and mains-temperature uncertainty only — pump/heat-transfer-
  coefficient and manufacturing-tolerance uncertainty (also listed in the
  full framework spec §11.1) were not sampled.
- Phase 6b (multi-fidelity surrogate) still reflects the original,
  pre-retargeting DOE set — not re-run against the current PCM shortlist
  or design bounds. Irrelevant to Objective 3 (it's a Phase 6 modeling
  bonus, not part of the environment contract) but noted for completeness.

## 5. Two small documentation-only updates (2026-09-13, predate doc 15), no contract change beyond what §1–2 already describe

- The Phase 4 Gate 3 comparison **plot** (not the frozen verification
  report) was regenerated to show the current shortlist PCM at its actual
  Phase 7 deployable geometry, instead of the original pre-fix
  diagnostic — every PCM bar now visibly beats plain tank. This is a
  documentation/figure change only; it does not alter
  `obj3_environment_contract_tamilnadu.json` or any number Objective 3
  consumes.
- The Phase 8 robustness-probability **chart** now shows delivery/demand
  reliability only (the P(temperature-safe) series was removed from that
  figure at the user's request). The underlying number is unchanged and
  still fully present in `robustness_summary.csv`, the recommendation
  cards, and the contract's `performance_at_selection` /
  `safety_shield` blocks — Objective 3 should keep reading it from those
  files, not from the chart.
- Minor wording note, not a functional issue: the contract's
  `safety_shield` condition for the PCM-temperature trigger is phrased
  "(PCM regimes only, ...)" — this is now vacuously true for every regime
  (`is_plain_tank_no_pcm: false` in all 5 `static_design_per_regime`
  entries), not a hint that some regimes lack PCM state.

## 6. Literature grounding Objective 3's contract design

See `REFERENCES.md` for the full mapping; the entries most directly
relevant to what Objective 3 is being asked to build:

- **[Sivaraj2023]** — a non-thermal precedent for benchmarking multiple
  DRL controller families against the same environment/reward before
  committing to one, directly transferable to choosing among DQN/PPO/
  SAC-family controllers for the charge/discharge/bypass problem here.
- **[Emami2026]** — direct precedent for a DRL controller coordinating a
  solar-driven system with thermal storage, the same problem shape as
  this contract's action space.
- **[Terfai2025]** — an ANN-based MPC alternative for solar-thermal
  storage control, useful contrast if Objective 3 evaluates a non-DRL
  baseline controller (as the acceptance-test's "trivial rule-based
  controller" step effectively does).
- **[Rubitherm2024]** — the datasheet source for the 65°C PCM limit that
  is the direct physical trigger condition the safety shield exists to
  anticipate (§2 above).

Also see `15_MCDM_RERANKING_AND_SAFETY_TIEBREAK.md` for why regime 4's
design (RT45HC) is now the least-exposed regime by a real, not
razor-thin, margin — relevant context for any reward-shaping decision
that weighs regimes differently based on how close their nominal design
already sits to the safety limit.
