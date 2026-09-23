# 08 — Phase 8 Audit: Light Robustness + Recommendation Cards + Objective 3 Handoff (Rajasthan)

Files: `src/robustness/monte_carlo.py`, `src/handoff/build_recommendation_cards.py`,
`src/handoff/build_obj3_contract.py`. Run:
```
python pipeline.py --state rajasthan --stage robustness [--mc-draws 120]
python pipeline.py --state rajasthan --stage handoff
```
Output:
- `results/phase8_robustness.csv` (per-regime summary) + `results/phase8_robustness_draws.csv` (every draw, for audit)
- `results/phase8_recommendation_cards.md` (one card per regime — D2.8)
- `results/obj3_environment_contract_rajasthan.json` (D2.9)

This closes Objective 2 (D2.7, D2.8, D2.9) — every deliverable in the
framework doc's Section 1.2 table now has a file behind it for Rajasthan.

> **File/function naming matches `objective2-tamilnadu/src/handoff/` and
> `src/robustness/` one-for-one.**

## History this phase carries (why today's numbers look the way they do)

Four changes landed in sequence and each is visible in the results
below — recorded here briefly so a reader isn't confused by why the
"deployable design" changed identity three times:

1. **2026-09-13 — rule-based safety shield became the pipeline default**
   (`system_config_shared.yaml: safety_shield.enabled: true`, bypass at
   72 °C water / 62 °C PCM). Before this, no PCM candidate cleared the
   65 °C PCM safety limit and the plain (no-PCM) tank was selected in
   every regime; after it, PCM candidates clear safety too.
2. **2026-09-14 — `apply_selection_rule()` corrected** to exclude the
   plain tank from the pool it selects a winner from (Objective 2's
   stated problem presupposes a PCM design — the plain tank was always a
   diagnostic baseline, never an eligible final answer). Combined with
   (1), all three regimes' deployable designs became real PCM designs
   (RT45HC / Paraffin-HDPE PCM6 / Paraffin-HDPE PCM3).
3. **2026-09-17 — capsule arrangement restored as a searched variable**
   (`Objective2 Consolidated plan.md`). The widened count bound (8–37,
   was 8–24), the larger 600-candidate search (was 400), and arrangement
   now entering the candidate pool changed which near-tied PCM design
   wins each regime again — winners became RT50 / Paraffin-HDPE PCM3
   / savE® OM50 (radial), see `07_PHASE7_OPTIMIZATION.md`. `monte_carlo.py`
   builds its `DesignVector` from the deployable row's own `arrangement`
   column (never assumed staggered).
4. **2026-09-18 — the Objective 1 → Objective 2 input chain was
   resynced** (`configs/states/rajasthan.yaml`,
   `state_config_rajasthan_v2.0_2026-09-18-resync`): the O1 PCM
   shortlist itself changed per regime, superseding the RT50/RT45HC/
   Lauric acid C12 and savE OM50/PCM3/PCM6 names above entirely.
   Phase 7 and Phase 8 were both re-run today (Phase 7 13:43–13:46,
   Phase 8 14:12–14:13) against the resynced config — **current winners
   are savE® OM55 (single-layer) / PureTemp 60 (staggered) / PureTemp 58
   (staggered)**, see `07_PHASE7_OPTIMIZATION.md`. Every number below is
   freshly computed against these current winners, not carried over from
   any earlier run.

Two smaller methodology notes, both still true: (a) this project's
weather/demand/mains perturbation model and fixed absolute
`solar_fraction` thresholds were the template Tamil Nadu's own Phase 8
pass was later aligned to match, for cross-state comparability
(`O2_Unified_PerState_Execution_Framework.md` §0.1); (b) `monte_carlo.py`'s
`summarize_design()` has always guarded the PCM-temperature check with
`if has_pcm:`, so a plain-tank design's water temperature is never
mis-flagged as a *PCM* over-temperature (a bug Tamil Nadu's first pass
had and fixed by porting this guard).

## D2.7 — Light robustness (Bug-Fix 6, framework doc §11.1)

**120 Monte Carlo draws per regime** (360 total; framework band 100–200,
never < 50), each a full simulated year of the current Phase 7 deployable
design with independent perturbations, driven through `run_case`'s
`weather_perturbation` keyword:

| Source | Distribution | Notes |
|---|---|---|
| Weather — GHI | annual scale ~ U(0.93, 1.07) × per-hour iid N(1, 0.04), clipped [0.5, 1.5] | "medoid + noise" — Rajasthan has no alternate member-point weather series |
| Weather — ambient temp | annual offset ~ U(−1.5, +1.5) °C + per-hour iid N(0, 0.4) °C | |
| Demand volume | `volume_multiplier` ~ U(0.80, 1.20) | ±20 % |
| Demand timing | `timing_shift_hours` ~ U(−0.5, +0.5) | ±30 min |
| Inlet / mains temperature | `T_mains_est_C` + U(−2, +2) °C | |
| PCM latent heat ±10 % | applied | all three current winners are real PCM designs, so this source is genuinely exercised in every regime |

Both "meets …" thresholds are FIXED and state-independent:
`p_meets_delivery_temp` = `solar_fraction ≥ 0.45`,
`p_meets_annual_demand` = `solar_fraction ≥ 0.50`. Two distinct
temperature-safety metrics are reported: `p_temperature_violation` (any
per-substep safety flag over the year) and `p_exceeds_max_safe_temp` (the
reported annual max actually clearing the 75 °C water / 65 °C PCM hard
limit).

### Result (resynced run, 2026-09-18)

| Regime | PCM | Arrangement | P(meets delivery temp) | P(meets annual demand) | **P(temp-safe)** | P(exceeds max safe temp) | Useful energy P5–P50–P95 (kWh) | Max water T P95 | Robust? |
|---|---|---|---|---|---|---|---|---|---|
| 0 | savE® OM55 | single-layer | 1.000 | 0.917 | **1.00** | 0.00 | 1448 – 1553 – 1711 | 72.36 °C | **Yes** |
| 1 | PureTemp 60 | staggered | 1.000 | 1.000 | **1.00** | 0.00 | 1652 – 1804 – 1961 | 72.15 °C | **Yes** |
| 2 | PureTemp 58 | staggered | 1.000 | 1.000 | **1.00** | 0.00 | 1613 – 1758 – 1891 | 72.27 °C | **Yes** |

Robust if `P(meets annual demand) ≥ ~0.75` **and** `P(temp-safe) ≥ ~0.95`.
**All three regimes clear both bars.** P95 max water temperature converges
tightly to just above the 72 °C shield trip point in every regime — the
shield forcing a pump bypass once water reaches 72 °C regardless of draw,
acting as designed, not a coincidence of sampling. These numbers are
freshly computed against the 2026-09-18 resynced winners (not carried
over from the pre-resync arrangement-restore run) — both the PCM identity
and the geometry differ from the earlier winners even where the same
qualitative shield behavior holds, per the consolidated plan's requirement
not to assume robustness transfers across a design-space change.

### What this means

Under realistic ±7% GHI / ±20% demand / ±2°C mains variability, **not a
single one of the 360 Monte Carlo draws across all three regimes breaches
either the 75 °C water or 65 °C PCM limit** — P(temp-safe) = 1.00
everywhere. This confirms, at Monte Carlo scale, what Phase 7's nominal
run already showed per design: the shield closes the safety gap for PCM
exactly as completely as it does for plain water, so PCM's small
(fraction-of-a-percent) useful-energy edge over plain water is free to
decide the winner without a safety penalty — a conclusion neither
arrangement restoration nor the 2026-09-18 resync changed (see
`07_PHASE7_OPTIMIZATION.md`'s headline finding).

Useful-energy spread is moderate (P5–P95 ≈ ±8-9% around the median),
driven mostly by the GHI scale and demand-volume draws — no draw produced
a NaN/inf or a failed year. `pump_energy_p05/p95_kWh` is negligible in
every regime (~1e-9 kWh, consistent with this system's tiny pump load,
see `03_PHASE3_GREYBOX_SIMULATOR.md`); `pcm_mass_p05/p95_kg` is constant
within each regime (0.297 / 0.390 / 0.388 kg for regimes 0/1/2 —
savE® OM55 / PureTemp 60 / PureTemp 58) since geometry does not vary
across Monte Carlo draws, only weather/demand/PCM latent heat do.

## D2.8 — Recommendation cards (`results/phase8_recommendation_cards.md`)

One card per regime, each carrying: regime/climate summary
(`cluster_profiles_rajasthan.csv`), the Objective 1 PCM shortlist with its
MCDM rank + Monte-Carlo top-3 inclusion, the selected geometry + flow,
**the selected arrangement and its rationale** (added 2026-09-17), the
`sim_v2_rajasthan`-confirmed full-year performance, the Phase 8 robustness
probabilities, the surrogate-vs-simulator delta (0.00–0.05%), a decision
rationale, and a caveats block (imputed PCM properties, single-pass
optimization, reduced Monte Carlo, single-state scope, lumped-model
±15%). The file recomputes nothing — every number is a lookup from a
frozen table or an earlier phase's output.

## D2.9 — Objective 3 environment contract (`results/obj3_environment_contract_rajasthan.json`)

`schema: obj3_environment_contract/v1`, `simulator_version: sim_v2_rajasthan`.
One entry per regime plus shared blocks:

- **`global_limits`** — delivery target 45 °C, max water 75 °C, max PCM
  65 °C, max pressure 3.5 bar, irradiance cutoff 10 W/m², pump flow
  0.010–0.050 kg/s (all from `system_config_shared.yaml`).
- **`control_skeleton`** — `actions: [charge, discharge, bypass]` with
  notes, the recommended continuous-flow hybrid action space, a
  10-element `state_vector`, and a `safety_shield` that forces `bypass`
  at `T_water ≥ 72 °C` (3 °C guard band), clamps flow to the pump
  envelope, cuts the pump below the irradiance cutoff, and states the
  dry-run and sensor-failure fallback rules explicitly.
- **`dynamic_state_schema`** — a fielded schema (10 fields: `GHI_Wm2`,
  `T_amb_C`, `T_water_C`, `T_pcm_C`, `f_melt`, `T_mains_C`,
  `draw_mass_kg_now`, `hour_of_day`, `minutes_since_last_draw`,
  `store_energy_above_mains_kWh`), each with unit, whether it's directly
  `measurable` or needs an estimator, and its source.
- **`reset_scenarios`**, **`reward_components_suggested`**,
  **`acceptance_test_before_drl_training`**, **`weather_sequences`** —
  three PCM-state reset scenarios, the suggested (unweighted) reward
  formula with weights marked "not yet chosen", the 6-item pre-training
  acceptance-test checklist, and an explicit note that no train/val/test
  weather split exists yet (medoid-only, 40-hr cut list).
- **per regime** — `regime_id`, label, `regime_membership_rule`, medoid
  weather path, `T_mains_est_C`, `Tm_target_C`; `selected_design`
  (`pcm_id`, `is_plain_tank`, `arrangement_rationale`, full geometry
  **including the real per-regime `capsule_arrangement`** — was
  hardcoded `"staggered"` before 2026-09-17 — `flow_envelope_kg_s`);
  `sim_confirmed_performance`; `robustness` (both temperature-safety
  probabilities + P5/P95 + `robust_per_framework_rule` flag).
- **`deferred_future_work`** — multi-state comparison, active-learning
  loop / full NSGA-II, full-draw robustness with real member-point
  weather, hardware validation (Objective 4 scope). No longer lists
  "arrangement search" as a limitation — it is implemented.
- **`supersedes`** — states explicitly that this version of the contract
  supersedes any prior plain-tank / no-shield / staggered-only version.

## Exit check

Every one of Rajasthan's 3 Level-A regimes has a recommendation card and
appears in the contract file, with a real PCM design, a real searched
arrangement, and a Monte-Carlo-confirmed robust safety margin under the
rule-based shield. **This is the Objective 2 "done" line for the ~40-hour
version, including the corrected 4-variable design vector.** Explicitly
deferred and enumerated in the contract's own `deferred_future_work`
field: the full four-state comparison (Tamil Nadu, Assam, and Uttarakhand
have not yet received the identical arrangement-restore change — see
`09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md` §9 and
`00_MASTER_CHANGE_PLAN.md`), the active-learning optimization loop, and
full-draw robustness with a genuine alternate weather series. See
`docs/OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` for the full Objective 3
hand-off brief.

## The caveat that must travel with these results

Rajasthan's Objective 2 conclusion is **positive but thin, not
decisive**: all three regimes now deploy a real PCM design that clears
temperature safety and beats plain water — but only by a
fraction-of-a-percent in useful energy (see
`07_PHASE7_OPTIMIZATION.md`'s headline finding), and only because the
rule-based safety shield is active as a pipeline default. Neither
arrangement restoration (2026-09-17) nor the 2026-09-18 resync changed
this: arrangement's effect on every performance target is near-zero
(`06_PHASE6_SURROGATE.md`), and all three regimes' winning arrangement is
"tied within noise" per `select_deployable.py`'s own rationale text, not
decisive. Objective 3 should treat the shield's bypass rule as a hard
floor to inherit, not a target to merely match — its own justification is
not "make PCM survive at all" (Objective 2 already does that) but
handling real-time weather/demand variability better than this fixed
threshold can (see `09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md` §8 for the
fuller reframing).

A second caveat travels alongside the first: the shielded/small-tank
design reported above is not the best design this project has already
found — `09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md` §7's tank-resize
alternative (112.5 L, IS 12976:2023's own reference ratio) beats it on
every axis (higher solar fraction, no shield needed, PCM wins more
decisively) using the same Phase 7 geometries. It is reported as a caveat on every recommendation card
(`results/phase8_recommendation_cards.md`), not folded into these
headline numbers, because it requires a coordinated shared-config change
across all four states — a scope decision, not an oversight.
