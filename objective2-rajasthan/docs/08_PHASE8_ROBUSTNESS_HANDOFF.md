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
> `src/robustness/` one-for-one** (`build_recommendation_cards.py` /
> `build_obj3_contract.py`, entry points `run(state)`; `monte_carlo.py`'s
> entry point `run_all(state, n_draws)`), and `pipeline.py` exposes the
> same two-stage split (`robustness` then `handoff`) Tamil Nadu's does —
> this project originally combined both into one `handoff` stage; the
> split and the renames bring it in line with the reference layout.

## Alignment with the Tamil Nadu implementation (this project was the template, not the follower)

This project's Phase 8 pass was built **first**, and Tamil Nadu's own
Phase 8 doc (`objective2-tamilnadu/docs_objective2/10_PHASE8_ROBUSTNESS_HANDOFF.md`,
"Alignment with the Rajasthan implementation") records that its first
Phase 8 pass was later revised to match three methodology choices made
here — two-level weather noise (annual scale/offset **plus** independent
per-hour noise, not one constant multiplier for the whole year), fixed
absolute `solar_fraction` thresholds for the two "meets …" probabilities
(rather than thresholds relative to each design's own nominal value,
which trivially scores every design 100% and hides real differences), and
120 draws/design — all so the two states' `phase8_robustness*.csv` files
stay directly comparable column-by-column
(`O2_Unified_PerState_Execution_Framework.md` §0.1). This doc records the
reverse direction of the same alignment: one concrete improvement Tamil
Nadu's later pass made — a clean `weather_perturbation` keyword on
`run_case()` instead of monkey-patching `io_utils.load_hourly_weather` at
call time — has been folded back into this project's `run_case.py` and
`monte_carlo.py`, and the reported metrics were split to match Tamil
Nadu's finer granularity (`p_temperature_violation` — any flagged
safety sub-hour — kept separate from `p_exceeds_max_safe_temp` — the
reported annual max actually clearing the hard limit — plus added
`pump_energy_p05/p95_kWh` and `pcm_mass_p05/p95_kg` percentiles). Column
names below (`p_meets_delivery_temp`, `p_meets_annual_demand`, etc.) are
the result of that alignment.

**A bug the original monkey-patch approach never actually had, worth
recording anyway**: Tamil Nadu's first Phase 8 pass computed
`p_exceeds_max_safe_temp` by checking `max_pcm_temp_C > 65°C` on
**every** design, including plain-tank ones — wrongly flagging ordinary
hot water (which only needs to respect the 75°C water limit) as a *PCM*
over-temperature, because `tank_model.py` sets `T_pcm = T_w` exactly when
there is no PCM. This project's `summarize_design()` already guarded that
check with `if has_pcm:` from the start (see `monte_carlo.py`), so the
bug never existed here — but it's worth stating explicitly, since the
guard is easy to remove by accident in a future edit and every one of
Rajasthan's 3 deployable designs is a plain tank, exactly the case that
would trip it.

## D2.7 — Light robustness (Bug-Fix 6, framework doc §11.1)

**120 Monte Carlo draws per regime** (360 total; framework band 100–200,
never < 50), each a full simulated year of the Phase 7 deployable design
with independent perturbations, driven through `run_case`'s
`weather_perturbation` keyword (per-hour numpy arrays for GHI multiplier
and ambient-temperature delta — the same override seam Phase 4's
`gates.py` uses for its own limiting-case tests, so `run_case` needed no
Phase-8-specific code path):

| Source | Distribution | Notes |
|---|---|---|
| Weather — GHI | annual scale ~ U(0.93, 1.07) × per-hour iid N(1, 0.04), clipped [0.5, 1.5] | "medoid + noise" — Rajasthan has no alternate member-point weather series (Objective 1 shipped medoid-only) |
| Weather — ambient temp | annual offset ~ U(−1.5, +1.5) °C + per-hour iid N(0, 0.4) °C | |
| Demand volume | `volume_multiplier` ~ U(0.80, 1.20) | ±20 % |
| Demand timing | `timing_shift_hours` ~ U(−0.5, +0.5) | ±30 min |
| Inlet / mains temperature | `T_mains_est_C` + U(−2, +2) °C | |
| PCM latent heat ±10 % | — | **not applicable**: every Phase 7 deployable design is the plain (no-PCM) tank, so there is no latent heat to perturb. Applied automatically if a future selection picks a real PCM. Stated, not silently dropped. |

**4 of the framework's 5 sources are covered; the 5th is structurally
inapplicable to the selected designs.** Both "meets …" thresholds are
FIXED and state-independent (Phase 3 doc's `solar_fraction` definition:
*"fraction of the ideal 300 L/day @ 45 °C demand actually delivered at or
above the 45 °C target"*): `p_meets_delivery_temp` = `solar_fraction ≥
0.45`, `p_meets_annual_demand` = `solar_fraction ≥ 0.50`. Two distinct
temperature-safety metrics are reported: `p_temperature_violation` (any
per-substep safety flag over the year, `n_safety_violations > 0`) and
`p_exceeds_max_safe_temp` (the reported annual max actually clearing the
75 °C water / 65 °C PCM hard limit) — for Rajasthan's plain-tank designs
these two are numerically identical by construction (only the water-limit
check applies), but they are computed independently and kept as separate
columns for cross-state comparability with PCM-bearing regimes elsewhere.

### Result

| Regime | P(meets delivery temp) | P(meets annual demand) | **P(temp-safe)** | P(exceeds max safe temp) | Useful energy P5–P50–P95 (kWh) | Max water T P95 | Robust? |
|---|---|---|---|---|---|---|---|
| 0 | 1.00 | 0.875 | **0.567** | 0.433 | 1454 – 1572 – 1673 | 84.6 °C | **No** |
| 1 | 1.00 | 0.992 | **0.450** | 0.550 | 1523 – 1664 – 1781 | 88.2 °C | **No** |
| 2 | 1.00 | 0.800 | **0.533** | 0.467 | 1447 – 1566 – 1692 | 84.6 °C | **No** |

Robust if `P(meets annual demand) ≥ ~0.75` **and** `P(temp-safe) ≥ ~0.95`.
**All three regimes clear the demand bar but fail temperature safety** —
badly (P(temp-safe) 0.45–0.57, i.e. roughly half of draws exceed the
75 °C water limit even with no PCM installed). Reported as a caveat, not
hidden (framework doc: "otherwise report as a caveat, don't hide it").

### What this means

The Phase 7 deployable designs are the *plain sensible-only tank* — and
even that, under realistic ±7 % GHI / ±20 % demand / ±2 °C mains
variability, exceeds the 75 °C water scald limit in **close to half of
all draws**. Regime 1 is worst (P(temp-safe) = 0.450) because its
nominal Phase 7 margin was only 2.6 °C, which a single +GHI or +mains
draw erases; its P95 max water temperature is 88.2 °C. This is the same
hot-dry-climate + frozen-1.5 m²-collector / 50 L-tank issue flagged since
the Phase 3 smoke runs, now quantified probabilistically: **an active
high-temperature bypass is a hard requirement for Rajasthan, not an
optimisation nicety** — and that control action belongs to Objective 3,
which is exactly why Phase 8 hands it off explicitly (below). See
`docs/plots/08_robustness_plots.md` for the visual version of this
result (Plot 1 makes the demand/temp-safety split visible at a glance).

Useful-energy spread is moderate (P5–P95 ≈ ±8 % around the median),
driven mostly by the GHI scale and demand-volume draws — no draw produced
a NaN/inf or a failed year. `pump_energy_p05/p95_kWh` and
`pcm_mass_p05/p95_kg` are also reported per regime (pump energy ~1e-9 kWh,
negligible at these flows; PCM mass 0 kg in every draw, since all three
deployable designs are the plain tank).

## D2.8 — Recommendation cards (`results/phase8_recommendation_cards.md`)

One card per regime, each carrying: regime/climate summary
(`cluster_profiles_rajasthan.csv`), the Objective 1 PCM shortlist with its
MCDM rank + Monte-Carlo top-3 inclusion, the selected geometry + flow, the
`sim_v1_rajasthan`-confirmed full-year performance, the Phase 8 robustness
probabilities (both temperature-safety metrics), the surrogate-vs-simulator
delta (0.06–0.10 %), an explicit decision rationale (why the plain tank,
not the PCM shortlist), and a caveats block (imputed PCM properties,
single-pass optimization, reduced Monte Carlo, single-state scope,
lumped-model ±15 %). The file recomputes nothing — every number is a
lookup from a frozen table or an earlier phase's output.

## D2.9 — Objective 3 environment contract (`results/obj3_environment_contract_rajasthan.json`)

`schema: obj3_environment_contract/v1`. One entry per regime plus shared
blocks:

- **`global_limits`** — delivery target 45 °C, max water 75 °C, max PCM
  65 °C, max pressure 3.5 bar, irradiance cutoff 10 W/m², pump flow
  0.010–0.050 kg/s (all from `system_config_shared.yaml`).
- **`control_skeleton`** — `actions: [charge, discharge, bypass]` with
  notes, the recommended continuous-flow hybrid action space, a
  10-element `state_vector`, and a **`safety_shield`** that forces
  `bypass` at `T_water ≥ 72 °C` (3 °C guard band), clamps flow to the
  pump envelope, cuts the pump below the irradiance cutoff, and now also
  states the dry-run and sensor-failure fallback rules explicitly. The
  shield's rationale cites the Phase 8 P(temp-safe) result directly.
- **`dynamic_state_schema`** *(new this pass, ported from Tamil Nadu)* —
  a fielded schema (10 fields: `GHI_Wm2`, `T_amb_C`, `T_water_C`,
  `T_pcm_C`, `f_melt`, `T_mains_C`, `draw_mass_kg_now`, `hour_of_day`,
  `minutes_since_last_draw`, `store_energy_above_mains_kWh`), each with
  unit, whether it's directly `measurable` or needs an estimator, and its
  source — replaces the earlier bare name-list `state_vector`.
- **`reset_scenarios`**, **`reward_components_suggested`**,
  **`acceptance_test_before_drl_training`**, **`weather_sequences`**
  *(all new this pass, ported from Tamil Nadu)* — three PCM-state reset
  scenarios (fully solid / partially charged / fully liquid), the
  suggested (unweighted) reward formula with weights explicitly marked
  "not yet chosen — Objective 3's decision", the 6-item pre-training
  acceptance-test checklist, and an explicit note that no train/val/test
  weather split exists yet (medoid-only, 40-hr cut list).
- **per regime** — `regime_id`, label, `regime_membership_rule`, medoid
  weather path, `T_mains_est_C`, `Tm_target_C`; `selected_design`
  (`pcm_id` — `null` for the plain tank — optional `pcm_properties`, full
  geometry, `flow_envelope_kg_s` = {nominal, min, max});
  `sim_confirmed_performance`; `robustness` (both temperature-safety
  probabilities + P5/P95 + `robust_per_framework_rule` flag);
  `sim_v1_rajasthan` tag.
- **`deferred_future_work`** — multi-state comparison, active-learning
  loop / full NSGA-II, full-draw robustness with real member-point
  weather, widened design bounds for 15–20 % PCM fraction, hardware
  validation (Objective 4 scope).

## Exit check

Every one of Rajasthan's 3 Level-A regimes has a recommendation card and
appears in the contract file. **This is the Objective 2 "done" line for
the ~40-hour version.** Explicitly deferred and named as future work (not
silently dropped, and now enumerated in the contract's own
`deferred_future_work` field): the full four-state comparison, the
active-learning optimization loop, and full-draw robustness with a
genuine alternate weather series. See
`docs/OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` for the full Objective 3
hand-off brief.

## The one caveat that must travel with these results

Objective 2's Rajasthan conclusion is **negative and load-bearing, with
two independent components**: (1) under the frozen shared collector/tank
config and the pre-declared selection rule, no Objective 1 shortlisted
PCM is deployable (0/45 cleared the 65 °C limit; energy gain < 0.15 %),
so the plain tank is selected in all 3 regimes; and (2) **no selected
design is robustly safe** without an active bypass (45–57 %
temperature-safe, all below the 95 % target, for the plain tank alone —
there being no PCM design to even compare against). Objective 3 must
treat overheat protection as a first-class control objective for every
Rajasthan regime, and any future PCM recommendation for hot-dry states
needs either widened design bounds **plus** a bypass shield, or a
hot-climate-specific revisit of the frozen 1.5 m² / 50 L sizing — the
same conclusion Tamil Nadu's independently-run audit reached (all 5
regimes fail the 95 % bar there too, 44–87 % temperature-safe), which is
itself evidence this is a climate-general finding, not a one-state
artifact.
