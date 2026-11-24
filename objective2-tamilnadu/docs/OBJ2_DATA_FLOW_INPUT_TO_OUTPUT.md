# Objective 2 — how every input travels to the final optimal design

*Rewritten 2026-11-24 for the **common-plant** run (100 L tank, 2.0 m² collector, 175 L/day). The previous version described the legacy
plant (2.5 m², 300 L/day, 104/98/105 capsules, 2011–15 test) and is superseded. Each hop below names the file that does it; every number
is read from `results/`, `configs/` or `data/`. Regime 0 / PureTemp 58 is the running example.*

**One-line story.** Objective 1 hands over *which PCMs, which climate regimes and what water temperature*. Objective 2 takes **weather +
a 175 L/day draw profile + a 100 L tank with a 2.0 m² collector**, builds a *simulator*, first asks **under what conditions a PCM can help at
all**, searches a 3-variable box with that simulator, **picks one design per regime with a funnel frozen before any select-year run**, tests
it **once** on years never used for choosing, and finally lets **ANSYS Fluent** check the physics the fast simulator assumed.

```
 OBJECTIVE 1 outputs                      FROZEN SYSTEM INPUTS
 ───────────────────                      ────────────────────
 regimes (K=3), medoid point              demand_profile_tamilnadu.csv  (24 hourly draws, 175 L/day)
 PCM shortlist per regime (top-3)         weather point-years  (NASA POWER hourly, 2006-2025, 3 medoids)
 PCM properties (Tm, L, k, cp, ρ)         system_config_shared.yaml    (100 L tank, 2.0 m² collector…)
 mains temperature per regime             design_space.yaml            (3 variables + bounds + limits)
          │                                        │
          └───────────────┬────────────────────────┘
                          ▼
   L1-L2  checks on the inputs   O1 alignment (shortlist unchanged) · weather audit (60 medoid-years)
                          ▼
   LEVEL 1  design vector (R_in, fraction→N, arrangement)  ──►  geometry engine (valid? N, void, Ergun Δp)
                          ▼
   LEVEL 2  SIMULATOR  run_case → multinode tank  (weather → collector → tank ⇄ PCM capsules → draw)   8760 h
                          ▼
   LEVEL 3  METRICS   g_window, g_annual, d_overheat, t_pcm_max …  PAIRED vs same-flow plain tank, at 3 stack anchors
                          ▼
   L3-G1    SIMULATOR VERIFICATION   energy closure · timestep halving · 10 vs 20 nodes · IS 12976 standing loss · geometry gate
                          ▼
   LEVEL 4  PLANT SCAN + SENSITIVITY + TAGUCHI   → "when can PCM help at all?"  → demand set to 175 L/day
                          ▼
   LEVEL 5  DOE (128 Sobol/pair) → fidelity screen (failed) → surrogate bake-off (stacked wins 9/9)
                          ▼
   LEVEL 6  SEARCH  NSGA-II + active learning on the surrogate; every reported number is a simulator run
                          ▼
   LEVEL 7  DENSE GRID + NOISE BAND  →  FUNNEL (frozen) on select years 2020-21  →  winners
                          ▼
   LEVEL 8  ANSYS Fluent  (capsule melt · discharge · whole tank · seven criteria) — consistency cross-check, never chooses
                          ▼
   LEVEL 9  ONE-SHOT TEST 2006-2010 under a hash-keyed lock  →  report-only 2022-25  →  immutable record + Objective-3 environment contract
```

---

## Level 0 — the inputs, and where each file is read

| input | file | what it contains | consumed by |
|---|---|---|---|
| **Demand** | `data/demand/demand_profile_tamilnadu.csv` | 24 rows: `hour, draw_fraction, draw_volume_L, draw_mass_kg`. Sums to **175 L/day** of 45 °C water; peaks at 19:00 (30.3 L), 18:00 and 20:00 (24.3 L each), morning peak 07:00–08:00 (15.4 L each). Declared in `configs/states/tamilnadu.yaml → demand_profile`. The profile *shape* is unchanged from the legacy 300 L/day file; only the total was rescaled (300 → 100 → 175). | `io_utils.load_demand_profile()` → `src/simulation/demand_profile.py::DemandModel`; the same 24-hour day is repeated for all 365 days. |
| **Weather** | `data/weather/point_years/tamilnadu/cluster<c>_<medoid>_<year>.csv` (`weather_inventory.csv`) | hourly `GHI_Wm2`, `T_amb_C`, humidity, wind, local hour. Medoid point per regime: **TNP_0006 / TNP_0007 / TNP_0001**. 60 point-years = 3 medoids × 2006–2025. | `src/weather/roles.py::load_point_year()`, which **enforces the year roles** (below). |
| **Regimes, PCM shortlist, mains T** | `configs/states/tamilnadu.yaml`, re-synced from Objective 1 on 2026-11-20 (11 files, hashes in `configs/o1_alignment_manifest_tamilnadu.json`) | per regime: `pcm_shortlist` (regime 0 = RT57HC, n-Hexacosane, PureTemp 58), `T_mains_est_C` (28.46 / 23.97 / 27.77 °C), medoid id. | `io_utils.get_regime()`; mains T is the **inlet temperature of every draw**. |
| **PCM properties** | `data/objective1/pcm_database_tamilnadu.csv` | Tm, latent heat, cp (solid/liquid), k, ρ (solid/liquid) | `io_utils.get_pcm_properties()` → `capsule_enthalpy.pcm_props_from_record()` (melting is a narrow band Tm ± 1 K). |
| **System** | `configs/system_config_shared.yaml` (v2.0) | tank 100 L (H/D = 2, U = 0.8 W/m²K), **collector 2.0 m²** (F_R·τα = 0.75, F_R·U_L = 4.5, pump off below 10 W/m²), 0.8 mm Al capsule wall, delivery target 45 °C, safety shield (bypass 72 °C water / 62 °C PCM), step 150 s (search) / 37.5 s (reporting) | every module via `io_utils.load_system_config()` |
| **Design space + limits** | `configs/design_space.yaml` (v4) | R_in 10–40 mm, PCM fraction 2–**40 %**, arrangement ∈ {single-layer, staggered, radial}; **flow frozen at 0.030 kg/s**; stack anchors {bottom, centre, top}; hard limits PCM ≤ 65 °C, water ≤ 75 °C; `n_nodes = 10` | `src/design/space.py` |

**Year roles** (`src/weather/roles.py`, enforced in code): 2016–2019 *explore* · 2020–2021 *select* · **2006–2010 *test*, run exactly once** ·
2022–2025 *report-only* (2024–25 are project-exposed) · 2011–2015 *legacy* (spent by the old test; accepted for no purpose).

## Level 1 — the design vector becomes a geometry

`src/design/space.py::to_design(R_in, fraction, flow, arrangement)` →

* capsule outer volume `V = 4/3·π·(R_in + 0.8 mm)³` (R_in = 40 mm → 2.845·10⁻⁴ m³)
* **count rule:** `N = clip( round(fraction · 0.100 m³ / V), ceil(0.02·0.1/V), floor(0.40·0.1/V) )`
  (so `N` is *derived*, not searched: R_in = 40 mm at the 40 % cap → **N = 140**, a realised fraction of 39.83 %).

`src/design/constraints.py::check_design` → `geometry.py::compute_geometry` returns, or **rejects with a reason**
(`passage_blocked`, `bounds_violation`, `overlap`, `pressure_drop_limit`, …): layers, stack height, void fraction (feeds Ergun Δp),
tank D = 0.399 m, H = 0.799 m. An invalid design is **never simulated**. Over the whole box: **780 grid points, 702 valid**
(`results/c5_g1_geometry_summary.csv`); 57 rejections are `passage_blocked`, 21 `bounds_violation`.

## Level 2 — the simulator (`src/simulation/run_case.py`)

`run_case(state, regime, PCM, design, weather, tank_model="multinode", n_nodes=10, stack_anchor=…)`. Each simulated hour, for 8 760 hours:

1. **Weather → collector.** `I = GHI_Wm2` (no tilt transposition, a known simplification). `Q_c = A·[F_Rτα·I − F_RU_L·(T_in − T_amb)]`
   (`collector_model.py`), only if `I ≥ 10 W/m²`.
2. **Flow acts on stratification, not on Q.** `F_R` is flow-independent here (`flow_dependent_fr` is off), so flow only changes where
   the heated water re-enters the tank (`tank_model_multinode.py`).
3. **Tank ⇄ PCM.** The 10 nodes exchange heat by advection, axial conduction and ambient loss. Capsules exchange heat with each node's
   water through `UA_eff` (Wakao–Kaguei convection + Al wall + `r/(5k)` PCM conduction, with the PCM's effective conductivity ×2.0 once
   the capsule is at least half melted, a stated stand-in for unresolved natural convection);
   the **enthalpy model** (`capsule_enthalpy.py`) gives temperature and melt fraction.
4. **Demand.** `DemandModel` draws `draw_mass_kg` from the **top node**; mains water enters the bottom.
5. **Safety shield.** If top water > 72 °C or PCM > 62 °C the collector loop is bypassed (counted as shield hours).
6. **Output.** An hourly frame plus an energy-balance residual (≤ 4.3·10⁻¹¹ % of collector energy; gate 0.1 %).

## Level 3 — metrics: the numbers an optimiser can compare

The optimiser always uses **paired gains**: the same year, flow, demand and tank model with the **capsules removed**
(`src/optimize/baseline.py`). Since the rebuild every design is also simulated at **three stack positions** (capsule bank at the bottom,
centre or top of the tank; `evaluate_design_robust`, rule R7): rank on the mean, reject if the worst-anchor gain is ≤ 0 or inside the band.

| objective | meaning | direction |
|---|---|---|
| `g_window` | extra heat delivered at ≥ 45 °C between 18:00 and 09:00, vs the plain tank (kWh/yr) | **max** (primary) |
| `g_annual` | same, whole year | max |
| `d_overheat` | extra overheat-guard hours vs the plain tank | min |
| `t_pcm_max`, `t_water_max` | peak temperatures — **hard constraints** ≤ 65 / ≤ 75 °C in *every* year and anchor | feasibility |

## L3 / G1 — simulator verification (`scripts/c4_l3_verification.py`, `c5`, `c6`)

At 175 L/day, 9 regime × PCM pairs × 2 fractions: timestep change per halving ≤ 0.047 % (gate 0.05 %), 10 vs 20 nodes ≤ 0.71 %,
energy closure ≤ 4.3·10⁻¹¹ %, PCM peak ≤ 64.3 °C, water peak ≤ 72.6 °C, deterministic rerun identical. IS 12976:2023 cl. 4.2.3 standing loss
2.05–4.82 °C over 16 h (limit 8 °C). The test suite: **95 passed, 1 skipped**.

## Level 4 — can a PCM help at all? (`c7`, `c8`, `c12`, `c13`)

This level changed the plant. At the first target (**100 L/day**) a one-at-a-time sensitivity found every input moves the PCM gain by
less than 1.5 kWh/yr, and a Taguchi L9 found the gain between −3.0 and +1.0 kWh/yr in every pair: the plain tank already met 99 % of
demand, so there was no unmet energy for PCM to add. A plant scan (`c12`) found the rule:

| collector 2.0 m² | 100 L/day | 150 | 200 | 300 |
|---|---|---|---|---|
| PCM gain (kWh/yr) | −0.6 | +75 | +154 | +212 |
| plain-tank solar fraction | 0.99 | 0.88 | 0.74 | 0.55 |

**PCM adds delivered energy only when the plain tank leaves demand unmet.** A category check (`c13`) also showed PCM is *worse* on
overheat-guard hours at every demand, so **no plant setting makes PCM better in every category**. Decision (user, 2026-11-23):
**175 L/day** of 45 °C water (the 45 °C equivalent of a 100 LPD heater rated at 60 °C). 100, 150 and the legacy 300 L/day stay as
sensitivity cases, never used for selection. Everything run at 100 L/day was archived and re-run at 175 L/day.

## Level 5 — DOE, fidelity screen, surrogates (`c9`, `c10`, `c11`)

* **DOE** (`c9`): 128 scrambled-Sobol points (seed 20261026) per (regime, PCM) pair, 9 pairs, over `(R_in, fraction, arrangement)`; flow
  frozen; cheap fidelity (dt 150 s, explore year 2017, 3 anchors). Infeasible points are recorded with a reason, not simulated.
* **Fidelity screen** (`c10`, pre-registered: Spearman ≥ 0.8, max difference ≤ 0.5 kWh, ≥ 7 of 9 pairs): **0 of 9 pass**. The cheap screen
  ranked perfectly (Spearman 1.00) but differed by 3.7–4.3 kWh. As pre-registered, it was *not used for selection*: every finalist is
  re-evaluated at full fidelity (dt 37.5 s).
* **Surrogates** (`c11`): Gaussian-process (ARD), NN ensemble, quadratic RSM, XGBoost and a **stacked ensemble**, scored by 5-fold Spearman.
  **Stacked wins in all 9 pairs** (0.975–0.984 vs XGBoost 0.969–0.976). *A surrogate only proposes; it never reports a number.*

## Level 6 — the search (`c14`)

**NSGA-II** on the surrogate, objectives `(−robust gain, overheat hours, PCM volume)`, then **committee active learning** (NN / XGBoost / RSM
disagreement; up to 3 rounds of 6, plus a box-vertex step; stop when the simulated-front hypervolume moves < 1 % twice), 3 seeds. Every
reported number is a simulator run.

*Where the parameters end up:* in **all 9 pairs the best design sits on the box boundary** (R_in = 40 mm, count at the 40 % cap).
More PCM mass keeps increasing the gain until the allowed limit, so the box, not the physics, stops the search.

## Level 7 — dense grid, noise band, funnel (`c15`, `c16`)

* **Dense grid** (162 points: 6 radii × 9 fractions × 3 arrangements, centre anchor): ε = best grid point − search best is within the band in
  all 9 pairs (largest 1.63 kWh).
* **Repeatability band** — how big must a gain be to count? `band = √(years² + timestep² + nodes² + PCM properties² + anchor²)` (**core**) and
  the same plus mains ±3 °C and demand ±20 % (**full**). Regime 0 / PureTemp 58: components 4.48, 3.63, 22.60, 16.23, 10.90 → **core 30.4 kWh/yr**;
  adding 23.9 (mains) and 91.6 (demand) → **full 99.4 kWh/yr**. The funnel uses the core band; mains and demand are *scenario shifts*, not noise.
  This choice was made after a smoke test, and is disclosed in `docs/PLAN_DEVIATIONS.md`.
* **Funnel**, frozen in `configs/funnel_frozen.json` (hash `36060c23…`) **before any select-year run**; top 6 designs per pair re-evaluated at dt 37.5 s on
  select years 2020–21, three anchors:

```
S0   feasible: geometry valid, PCM ≤ 65 °C, water ≤ 75 °C, zero hours over the limit — in every anchor and year
S1   worst-anchor gain > the pair's core band (else "no PCM benefit" → WATER-ONLY); designs within one band of the leader are TIED
S2   among the tied: lowest overheat hours → smallest PCM volume → highest robust gain
```

Regime 0 result: 18 designs tied with the leader (138.3 kWh) → **PureTemp 58, R_in = 40 mm, N = 140, 39.8 %, staggered** (select gain 129.5 kWh,
848 overheat hours). The single-layer design with 141 capsules scored 129.7 kWh, a 0.2 kWh difference that is pure noise, but with 1090 overheat hours:
the **arrangement is decided by the S2 tie-break, not by a performance gap**.

## Level 8 — ANSYS Fluent: "is the fast model's physics reasonable?"

| Fluent case | what goes in (from Objective 2) | what comes out | where |
|---|---|---|---|
| Single-capsule melt | optimal R_in, PCM properties from `pcm_database_tamilnadu.csv`, 70 °C charging water | liquid fraction vs time, melt-front contours | `ansys/fluent_live_demo.py`, `docs/CFD_VERIFICATION.md` |
| Single-capsule discharge | capsule hot and melted, water 30 °C, no sun | water/capsule temperature, liquid fraction | `ansys/fluent_discharge_demo.py` |
| Whole-tank discharge | chosen PCM, capsule count/radius (**2-D proxy: 34 drawn ≙ 140 real**), capsules hot, water 30 °C, no sun | temperature and liquid-fraction contours, time series | `ansys/fluent_tank_discharge.py`, `ansys/criteria_0…6/` |
| **Seven criteria** | the optimum + six alternatives (max, min, a real finalist, 30 capsules, 10 %, 50 %) | per criterion: node-model verdict (which funnel step removes it), Fluent time series and contours | `ansys/criteria_*/`, `ansys/criteria_common/` |

The criteria are defined once, in `ansys/criteria_common/scenarios.py`; the MATLAB checkpoint reads the same file, so both sets describe the same
seven designs. Role: *model-consistency cross-check* of Level-2's assumptions (lumped conduction, melt band, liquid-convection factor).
**It does not choose the design, and it is not experimental validation.**

## Level 9 — the one-shot test and the hand-off

`scripts/c17_l9_test_and_contract.py` runs the three funnel winners **once** on 2006–2010 under `results/common100L_<hash>/held_out_test.lock`
(an atomic file keyed to a hash of the plant, design-space, state and demand files; a second run fails closed). Then the report-only years
2022–2025, then the **immutable result record** `o3_contract_tamilnadu.json` (hashes of every config and weather file).
`scripts/c23_build_o3_environment_contract.py` writes the **environment contract** Objective 3 reads, which points at the record by hash;
`scripts/c24_check_o3_environment_contract.py` re-checks it against the sources (33 checks).

| regime | PCM | test gain (kWh/yr) | worst anchor | years PCM wins | × core band | × full band | extra overheat h/yr |
|---|---|---|---|---|---|---|---|
| 0 | PureTemp 58 | 137.3 | 132.4 | 5 of 5 | 4.5 | 1.38 | +937 |
| 1 | RT57HC | 122.4 | 108.8 | 5 of 5 | 4.5 | 1.84 | +627 |
| 2 | RT57HC | 134.0 | 127.9 | 5 of 5 | 6.3 | 1.49 | +998 |

---

## Every parameter, start to finish

| parameter | status | start (Level 0) | what moved it | final |
|---|---|---|---|---|
| tank volume | **fixed** | 100 L | project instruction; never optimised | 100 L |
| collector area | **fixed** | 2.0 m² (was 2.5) | common-plant rule; reduced 2026-11-20 | 2.0 m² (50 L per m²) |
| daily demand | **fixed** | 175 L/day (was 300) | plant scan (Level 4) showed 100 L/day leaves no PCM benefit | 175 L/day |
| PCM | chosen from O1's top-3 | 3 per regime | funnel S1/S2 across the regime's PCMs | PureTemp 58 / RT57HC / RT57HC |
| capsule inner radius | **searched** 10–40 mm | DOE spans the range | search pushes it up (more PCM) | **40 mm**, at the bound |
| PCM fraction | **searched** 2–40 % | DOE spans the range | search pushes it up | **39.83 %**, at the cap |
| capsule count N | **derived** | — | `N = floor(0.40·V_tank/V_capsule)` at R = 40 mm | **140** |
| arrangement | **searched** (3) | DOE spans all three | tied on gain; S2 picks least overheating | staggered |
| flow rate | **frozen** | 0.030 kg/s | rule R6: not searched (F_R does not respond to flow) | 0.030 kg/s |
| stack anchor | not a variable | — | every design evaluated at bottom, centre and top | robust mean |
| weather years | roles fixed in code | 2006–2025 | explore → select → one-shot test | see Level 0 |

## One parameter, end to end (worked example: **capsule count**)

1. **Search variable** `pcm_volume_fraction ∈ [0.02, 0.40]` with `R_in ∈ [10, 40] mm` (Level 5 DOE). → 2. `to_design` → count rule (Level 1).
3. `compute_geometry` → layers, stack height, void fraction, Ergun Δp (valid). → 4. `run_case` → PCM mass **33.4 kg** (PureTemp 58), `UA_eff` = N × per-capsule conductance,
capsules distributed over nodes. → 5. Hourly `T_pcm`, `f_melt` → latent storage. → 6. `evaluate_design_robust` → paired gain at three anchors.
7. Surrogate / NSGA-II learn *more capsules → more gain* until the cap (Level 6). → 8. Band 30.4 kWh → **18 designs statistically tied**; S2 keeps the least-overheating one → **N = 140**.
9. One-shot test 2006–10: **137.3 kWh/yr**, positive in 5 of 5 years. → 10. Fluent: the 34-capsule 2-D slice (≙ 140 real) reproduces the discharge shape.

## Where to look when you need to *show* each level

| level | one file to open |
|---|---|
| 0 inputs | `configs/states/tamilnadu.yaml`, `data/demand/demand_profile_tamilnadu.csv`, `src/weather/roles.py` |
| 1–2 | `src/design/space.py`, `src/simulation/run_case.py` |
| 3 / G1 | `src/optimize/evaluate.py`, `results/c4_l3_r0_timestep.csv`, `results/c5_g1_geometry_summary.csv` |
| 4 | `results/c12_plant_scan_r0.csv`, `results/c13_categories_r0.csv`, `docs/COMMON_PLANT_REBUILD_LOG.md` |
| 5 | `results/c9_l5_doe_r0_p3.csv`, `results/c10_l5_fidelity_summary.csv`, `results/c11_*` |
| 6 | `results/c14_l6_points_r0_p3.csv`, `results/c14_l6_front_r0_p3.csv` |
| 7 | `results/c15_l7_band_r0_p3.csv`, `configs/funnel_frozen.json`, `results/c16_select_eval_all.csv`, `results/c16_funnel_winners.csv` |
| 8 | `ansys/criteria_*/…`, `ansys/criteria_common/SUMMARY_all_criteria.{csv,png}`, `docs/CFD_VERIFICATION.md` |
| 9 | `results/common100L_<hash>/c17_summary.csv`, `…/o3_contract_tamilnadu.json`, `…/o3_environment_contract_tamilnadu.json` |
| plain-language results | `docs/RESULTS_COMMON_PLANT.md`, `docs/PLAN_DEVIATIONS.md` |
