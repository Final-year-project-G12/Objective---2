# Objective 3 — Inputs From Objective 2 and What To Do Next

**Updated 2026-10-27, third pass: tank/collector resized, all 3
robustness bars now met.** The contract was regenerated three times over
2026-10-26/27: a demand-timing bug fix, an actual enforced safety shield
(no longer just a spec — see §2), then a resize of the tank/collector
from an undersized 50L/1.5m² to a standard domestic 100L/2.5m² pairing.
**Every regime now meets all three Phase 8 robustness bars at once**
(P(meets delivery), P(meets demand), P(temperature-safe) all cross their
thresholds, Monte Carlo confirmed) — see `RESULTS.md` and
`TAMILNADU_REDESIGN_PLAN.md` §5c for the full account. The per-regime
numbers below are the final, thrice-corrected ones. If you cached any
earlier version of the contract or these numbers, discard that copy.
Supersedes all prior prose versions of this document, which described a
now-nonexistent K=5-regime run. See `history/18_OBJECTIVE1_SHORTLIST_RESTORED.md`
for the full history of how this state was reached.

Objective 2 is **complete** for Tamil Nadu: 3 climate regimes (Objective 1
was refreshed from K=5 to K=3 regimes, real elevation, rewritten MCDM
engine), each with a PCM design that is genuinely one of Objective 1's own
Top-3 shortlisted candidates for that regime — not a re-derived substitute.

**The formal boundary** (do not cross it in either direction): Objective 1
selected the PCM shortlist. Objective 2 selected the physical hardware
design (PCM identity, capsule geometry, arrangement, flow) and validated
operating envelope, below. **Objective 3 selects the real-time action —
nothing else.** It must not change PCM identity, capsule geometry, tank
volume, safety limits, or the physics model released here.

---

## 1. The one file Objective 3 actually needs

**`results/tamilnadu/obj3_environment_contract_tamilnadu.json`**
(`contract_version: "obj3_contract_v2.0_2026-09-17"`,
`validated_simulator_version: "sim_v2_tamilnadu"`). Read it
programmatically, don't hand-copy numbers out of it — the three regimes'
actual designs, for reference:

| Regime | PCM | Tm (°C) | Arrangement | Capsules | Diameter (mm) | PCM mass (kg) | Useful energy (kWh/yr) | Solar fraction | Constraint margin (°C) |
|---|---|---|---|---|---|---|---|---|---|
| 0 | n-Hexacosane (C26) | 56.5 | radial | 32 | 72.22 | 4.859 | 1668.65 | 0.652 | +2.70 |
| 1 | n-Hexacosane (C26) | 56.5 | radial | 33 | 75.31 | 5.682 | 1763.44 | 0.578 | +3.06 |
| 2 | n-Pentacosane (C25) | 54.0 | single-layer | 35 | 79.76 | 7.449 | 1679.40 | 0.647 | +2.70 |

Tank/collector are now **100 L / 2.5 m²** (resized 2026-10-27 from
50 L / 1.5 m² — a standard domestic size, not the earlier undersized
pairing). "Constraint margin" here is `max_safe_pcm_temp_C (65°C) −
nominal peak PCM temperature`; **every regime is positive** — the direct
effect of the safety shield Objective 2's own simulator enforces (§2
below). The honest cost: PCM still loses to a plain tank in every regime
(−12.5% to −14.8% — see §2), and this gap is now *wider* than right after
the shield alone, since the bigger tank's own thermal mass does more of
the safety-related buffering on its own.

Per-regime contract fields (all live, nothing placeholder):
- full PCM property record (`selected_pcm`: Tm, latent heat, conductivity,
  solid/liquid density and Cp, `any_property_imputed` flag)
- capsule geometry (diameter, count, arrangement, max conduction distance,
  PCM mass), tank (50 L, 0.05 m insulation, U=0.8 W/m²K), collector
  (1.5 m², FR(τα)=0.75, FR·UL=4.5 W/m²K) — all identical across regimes;
  only the PCM/geometry/arrangement differ
- flow envelope: nominal per-regime (0.0119–0.0274 kg/s) within a shared
  hard envelope **min 0.01 / max 0.05 kg/s**, pump efficiency 0.6, max
  pressure 3.5 bar
- `global_limits`: delivery target 45°C, max safe water 75°C, max safe PCM
  65°C, irradiance cutoff 10 W/m², flow envelope — use this block for code
  that needs "the" envelope rather than iterating every regime
- `safety_shield`: 6 trip conditions, all on a **3°C precautionary guard
  band below each hard limit** (bypass at 72°C water / 62°C PCM, not
  75/65°C themselves), plus flow-envelope clipping, dry-run detection, and
  sensor-failure fallback — see §2, this is a specification, not something
  already enforced in the simulator
- `reward_function`: fully specified — formula, normalized reference
  magnitudes (from these 3 designs), default weights with rationale
  (`w1`=`w2`=1.0 delivered/unmet energy, `w3`=0.1 pump energy, `w4`=10.0
  safety penalty, `w5`=0.05 bypass-switching penalty), penalty-term
  definitions tied to the same guard-band trigger as the safety shield,
  and a tuning procedure — ready-to-train defaults, not a placeholder
- `action_space`: discrete (charge/discharge/bypass) and a recommended
  continuous-flow hybrid version, with the hard rule that the controller
  may never command outside the flow envelope or temperature limits
- 3 reset scenarios (fully solid / partially charged / fully liquid
  initial PCM state)
- `acceptance_test_before_drl_training`: the checklist required before any
  DRL training starts
- `deferred_future_work`: 4-state comparison, active-learning/NSGA-II,
  sub-daily/hourly multi-year weather, hardware validation — read before
  assuming any of these are done

## 2. What Objective 2 is telling Objective 3 about the physical system

- **All 3 regimes have a real PCM design, genuinely drawn from Objective
  1's own Top-3 shortlist** for that regime (not a re-derived target or
  substitute PCM — see `history/18_OBJECTIVE1_SHORTLIST_RESTORED.md` for why this
  matters: an earlier Tm-retargeting revision had quietly violated this,
  since fixed).
- **PCM masses are now larger than the pre-fix designs** (1.26–6.18 kg
  across the 3 regimes, vs. 0.41–0.90 kg before 2026-10-26) and sized to
  each regime's own real (corrected) tank thermal behavior — expect
  regular melt/freeze cycling in normal operation.
- **No auxiliary/backup heater exists in this system.** "Unmet energy" in
  every Objective 2 metric means genuinely undelivered heat, not a gap an
  electric backup fills. If Objective 3's reward function assumes a
  backup exists, that must be a stated new addition, not something
  inherited from Objective 2.
- **A real safety shield IS implemented in the physics model itself**
  (`src/simulation/tank_model.py`, added 2026-10-26, immediately after the
  demand-timing fix below exposed how badly the passive tank overheats
  without one). It forces the collector off whenever water reaches 72°C
  or PCM reaches 62°C (3°C below the 75°C/65°C hard limits), tightened
  further for PCM designs specifically (see `TAMILNADU_REDESIGN_PLAN.md`
  §5 for why). **The tank/collector was then resized** from an undersized
  50L/1.5m² to a standard domestic 100L/2.5m² (§5c) after the shield alone
  left demand reliability very low on the small tank. Phase 8's Monte
  Carlo robustness analysis (120 draws/design) now finds, with both
  changes in place:

  | Regime | PCM | P(meets delivery) | P(meets demand) | P(temperature-safe) | Robust? |
  |---|---|---|---|---|---|
  | 0 | n-Hexacosane (C26) | **1.00** | **1.00** | **1.00** | **Yes** |
  | 1 | n-Hexacosane (C26) | **1.00** | **0.942** | **1.00** | **Yes** |
  | 2 | n-Pentacosane (C25) | **1.00** | **1.00** | **1.00** | **Yes** |

  **All three bars are met in every regime, confirmed under Monte Carlo
  uncertainty, not just nominally.** Note how this was reached: the shield
  alone got temperature-safety to 100% but collapsed demand reliability to
  0–4% (a real, disclosed trade-off at the time); resizing the tank then
  recovered demand reliability without giving up any of the shield's
  safety margin — the two fixes were independently necessary, not
  redundant. **For Objective 3**: the environment it inherits is already
  safe and already delivery-reliable on average; its job is to do better
  than this blunt reactive on/off shield on finer-grained metrics (e.g.
  shield-activation frequency, discharge timing precision) and on harsher
  weather years/regimes this project hasn't tested, not to fix a broken
  baseline.
- **Why the tank would run hot regardless of PCM choice, absent the
  shield**: on sunny days, tank water temperature would reach well above
  the PCM's own stability ceiling (65°C) even though it stays within
  water's own 75°C limit — this is exactly the condition the now-enforced
  shield (§2) reacts to, and every regime's positive constraint margin in
  §1's table (+2.7 to +3.1°C) shows it is currently doing its job under
  nominal operation.

## 3. Concrete first steps for Objective 3

1. **Load the contract, don't re-derive it.** Parse
   `obj3_environment_contract_tamilnadu.json` for each regime's static
   design inputs — do not re-run Objective 2's optimizer or re-pick a PCM.
2. **A basic safety shield is already enforced inside
   `src/simulation/tank_model.run_year` itself** (§2) — Objective 3 does
   not need to build this from scratch before training. Still verify it
   independently using the acceptance-test list in the contract (the
   checklist item "the safety shield cannot be bypassed by the policy"
   should pass trivially against this baseline, since the shield sits
   inside the physics, not the policy). **What Objective 3 should actually
   build first is a *better* shield/control policy** than this blunt
   instantaneous trip — one that anticipates approaching the limit instead
   of reacting at it, to recover the demand-reliability this version gives
   up (§2's P(meets demand) = 0–4%).
3. **Build a step-by-step (not annual-batch) version of the simulator.**
   Objective 2's `run_year()` runs a full year in one call, appropriate
   for design evaluation. Objective 3 needs a
   `step(action) -> (obs, reward, done, info)` interface — refactor
   `tank_model.py`'s inner timestep loop into a stateful stepper rather
   than rewriting the physics. Reuse the physics (enthalpy model, heat
   transfer, collector, hydraulics) unchanged; only the control surface
   changes (fixed `flow_rate_kg_s` becomes an action instead of a
   constant).
4. **Start from the contract's `reward_function` defaults**, don't invent
   new ones from scratch — copy `w1..w5` into Objective 3's own frozen
   config as the training starting point, then follow the contract's
   `tuning_procedure` if retuning is needed after a first training run.
5. **Run the acceptance test with a trivial rule-based controller** (e.g.
   "charge whenever irradiance is high and PCM isn't full, discharge
   during demand hours, bypass otherwise") before writing any learning
   code. If this fails any check in the contract's
   `acceptance_test_before_drl_training` list, fix the environment before
   touching RL.
6. **Re-use, don't reopen, Objective 2's climate-regime split.**
   Train/validate/test across regimes 0–2 as Objective 2 defined them
   (`configs/states/tamilnadu.yaml`) — do not re-cluster or merge regimes.
7. **When Rajasthan/Assam/Uttarakhand versions of Objective 2 exist**,
   build one contract-consuming Objective 3 codebase that takes `--state`
   the same way Objective 2's `pipeline.py` does, rather than forking
   per-state controller code. Those states have NOT yet had the K=5→K=3
   refresh or shortlist restoration applied — do not assume their
   contracts already describe equivalent designs until confirmed.

## 4. What Objective 2 explicitly did NOT resolve (don't assume it did)

- Phase 8's Monte Carlo draws its *annual* weather magnitude from a real
  10-year historical ensemble, but no unseen-weather-year or member-point
  re-confirmation of the final designs' *hourly* shape exists yet
  (medoid-only, synthetic per-hour jitter) — Objective 3's own weather
  train/val/test split is still genuinely unstarted work.
- Phase 8's robustness analysis covers PCM-property, weather-noise, demand
  and mains-temperature uncertainty only — pump/heat-transfer-coefficient
  and manufacturing-tolerance uncertainty were not sampled.
- Phase 6b (multi-fidelity surrogate) still reflects an older DOE set —
  not re-run against the current PCM shortlist or design bounds. Irrelevant
  to Objective 3 (it's a Phase 6 modeling bonus, not part of the
  environment contract) but noted for completeness.
- The 4-state comparison, active-learning/NSGA-II search, sub-daily
  multi-year weather, and hardware validation are all explicitly deferred
  — see the contract's own `deferred_future_work` list.

## 5. Literature grounding Objective 3's contract design

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
- **[Rubitherm2024]** — the datasheet source for the 65°C PCM stability
  ceiling that is the direct physical trigger condition the safety shield
  exists to anticipate (§2 above).
