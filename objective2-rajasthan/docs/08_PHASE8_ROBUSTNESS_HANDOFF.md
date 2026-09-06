# 08 — Phase 8 Audit: Light Robustness + Recommendation Cards + Objective 3 Handoff (Rajasthan)

Files: `src/robustness/monte_carlo.py`, `src/handoff/recommendation_card.py`,
`src/handoff/obj3_contract.py`.
Run: `python pipeline.py --state rajasthan --stage handoff [--mc-draws 120]`.
Output:
- `results/phase8_robustness.csv` (per-regime summary) + `results/phase8_robustness_draws.csv` (every draw, for audit)
- `results/phase8_recommendation_cards.md` (one card per regime — D2.8)
- `results/obj3_environment_contract_rajasthan.json` (D2.9)

> **No Tamil Nadu reference to port.** `objective2-tamilnadu` stopped at
> Phase 7 (`objective2-tamilnadu/docs/09_NEXT_STEPS.md`: "`src/robustness/`,
> `src/handoff/` … Phase 8 is not started"). These three modules are built
> fresh, but along the seams that doc names: the Monte Carlo perturbs
> only through `run_case`'s existing knobs (`volume_multiplier`,
> `timing_shift_hours`, `mains_temp_override_C`, `pcm_record_overrides`)
> plus a temporary wrap of `load_hourly_weather` for weather noise (the
> same override seam `gates.py` uses), so `run_case` stays byte-identical
> and every robustness metric is computed by its own code path — the
> Phase 8 numbers are directly comparable to the Phase 7 `sim_*` columns.

## D2.7 — Light robustness (Bug-Fix 6, framework doc §11.1)

**120 Monte Carlo draws per regime** (360 total; framework band 100–200,
never < 50), each a full simulated year of the Phase 7 deployable design
with independent perturbations:

| Source | Distribution | Notes |
|---|---|---|
| Weather | annual GHI scale ~ U(0.93, 1.07) × per-hour iid N(1, 0.04); annual T_amb offset ~ U(−1.5, +1.5) °C + per-hour iid N(0, 0.4) °C | "medoid + noise" — Rajasthan has no alternate member-point weather series (Objective 1 shipped medoid-only) |
| Demand volume | `volume_multiplier` ~ U(0.80, 1.20) | ±20 % |
| Demand timing | `timing_shift_hours` ~ U(−0.5, +0.5) | ±30 min |
| Inlet / mains temperature | `T_mains_est_C` + U(−2, +2) °C | |
| PCM latent heat ±10 % | — | **not applicable**: every Phase 7 deployable design is the plain (no-PCM) tank, so there is no latent heat to perturb. Applied automatically if a future selection picks a real PCM. Stated, not silently dropped. |

**4 of the framework's 5 sources are covered; the 5th is structurally
inapplicable to the selected designs.** The two "meet …" probabilities
both key off `run_case`'s `solar_fraction`, which is defined (Phase 3 doc)
as *"fraction of the ideal 300 L/day @ 45 °C demand actually delivered at
or above the 45 °C target"* — i.e. it is already a
delivery-temperature-weighted demand-met fraction. Thresholds (project
assumptions): `meet_delivery_temp` = `solar_fraction ≥ 0.45`,
`meet_annual_demand` = `solar_fraction ≥ 0.50`. A safety-temperature
violation = max water > 75 °C **or** max PCM > 65 °C (PCM designs) **or**
any per-substep violation over the year.

### Result

| Regime | P(meet delivery temp) | P(meet annual demand) | **P(temp-safe)** | Useful energy P5–P50–P95 (kWh) | Max water T P95 | Robust? |
|---|---|---|---|---|---|---|
| 0 | 1.00 | 0.875 | **0.51** | 1444 – 1576 – 1685 | 83.0 °C | **No** |
| 1 | 1.00 | 0.983 | **0.33** | 1534 – 1647 – 1770 | 86.6 °C | **No** |
| 2 | 1.00 | 0.775 | **0.50** | 1454 – 1574 – 1694 | 83.2 °C | **No** |

Robust if `P(meet annual demand) ≥ ~0.75` **and** `P(temp-safe) ≥ ~0.95`.
**All three regimes clear the demand bar but fail temperature safety** —
badly (P(temp-safe) 0.33–0.51). Reported as a caveat, not hidden
(framework doc: "otherwise report as a caveat, don't hide it").

### What this means

The Phase 7 deployable designs are the *plain sensible-only tank* — and
even that, under realistic ±7 % GHI / ±20 % demand / ±2 °C mains
variability, exceeds the 75 °C water scald limit in **half to two-thirds
of draws**. Regime 1 is worst (P(temp-safe) = 0.33) because its nominal
Phase 7 margin was only 2.6 °C, which a single +GHI or +mains draw erases;
its P95 max water temperature is 86.6 °C. This is the same hot-dry-climate
+ frozen-1.5 m²-collector / 50 L-tank issue flagged since the Phase 3
smoke runs, now quantified probabilistically: **an active
high-temperature bypass is a hard requirement for Rajasthan, not an
optimisation nicety** — and that control action belongs to Objective 3,
which is exactly why Phase 8 hands it off explicitly (below).

Useful-energy spread is moderate (P5–P95 ≈ ±8 % around the median),
driven mostly by the GHI scale and demand-volume draws — no draw produced
a NaN/inf or a failed year.

## D2.8 — Recommendation cards (`results/phase8_recommendation_cards.md`)

One card per regime, each carrying: regime/climate summary
(`cluster_profiles_rajasthan.csv`), the Objective 1 PCM shortlist with its
MCDM rank + Monte-Carlo top-3 inclusion, the selected geometry + flow, the
`sim_v1_rajasthan`-confirmed full-year performance, the Phase 8 robustness
probabilities, the surrogate-vs-simulator delta (0.06–0.10 %), an explicit
decision rationale (why the plain tank, not the PCM shortlist), and a
caveats block (imputed PCM properties, single-pass optimization, reduced
Monte Carlo, single-state scope, lumped-model ±15 %). The file recomputes
nothing — every number is a lookup from a frozen table or an earlier
phase's output.

## D2.9 — Objective 3 environment contract (`results/obj3_environment_contract_rajasthan.json`)

`schema: obj3_environment_contract/v1`. One entry per regime plus a shared
block:

- **`global_limits`** — delivery target 45 °C, max water 75 °C, max PCM
  65 °C, max pressure 3.5 bar, irradiance cutoff 10 W/m², pump flow
  0.010–0.050 kg/s (all from `system_config_shared.yaml`).
- **`control_skeleton`** — `actions: [charge, discharge, bypass]` with
  notes; a 10-element `state_vector` (`T_water_C`, `T_pcm_C`, `f_melt`,
  `GHI_Wm2`, `T_amb_C`, `hour_of_day`, `draw_mass_kg_now`, `T_mains_C`,
  `store_energy_above_mains_kWh`, `minutes_since_last_draw`); a
  **`safety_shield`** that forces `bypass` at `T_water ≥ 72 °C` (3 °C guard
  band), clamps flow to the pump envelope, and cuts the pump below the
  irradiance cutoff. The shield's rationale cites the Phase 8 P(temp-safe)
  result directly.
- **per regime** — `regime_id`, label, medoid weather path, `T_mains_est_C`,
  `Tm_target_C`; `selected_design` (pcm_id — `null` for the plain tank —
  optional `pcm_properties`, full geometry, `flow_envelope_kg_s` =
  {nominal, min, max}); `sim_confirmed_performance`; `robustness` (the
  Phase 8 probabilities + P5/P95 + `robust` flag); `sim_v1_rajasthan` tag.
- **`deferred_future_work`** — multi-state comparison, active-learning
  loop / full NSGA-II, full-draw robustness with real member-point
  weather, widened design bounds for 15–20 % PCM fraction.

## Exit check

Every one of Rajasthan's 3 Level-A regimes has a recommendation card and
appears in the contract file. **This is the Objective 2 "done" line for
the ~40-hour version.** Explicitly deferred and named as future work (not
silently dropped): the full four-state comparison, the active-learning
optimization loop, and full-draw robustness with a genuine alternate
weather series.

## The one caveat that must travel with these results

Objective 2's Rajasthan conclusion is **negative and load-bearing**:
under the frozen shared collector/tank config and the pre-declared
selection rule, no Objective 1 shortlisted PCM is deployable (0/45
cleared the 65 °C limit; energy gain < 0.15 %), and the fallback plain
tank is **not robustly safe** without an active bypass. Objective 3 must
treat overheat protection as a first-class control objective for
Rajasthan, and any future PCM recommendation for hot-dry states needs
either widened design bounds **plus** a bypass shield, or a
hot-climate-specific revisit of the frozen 1.5 m² / 50 L sizing.
