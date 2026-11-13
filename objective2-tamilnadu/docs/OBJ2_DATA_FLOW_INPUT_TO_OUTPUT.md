# Objective 2 — how every input travels to the final optimal design

*Written from the code and result files in this folder (nothing here is typed from memory;
each hop names the file that does it). Regime 0 / PureTemp 58 is used as the running example.*

**One-line story.** Objective 1 hands over *which PCMs, which climate regimes and what water temperature*.
Objective 2 takes **weather + a 300 L/day draw profile + a 100 L tank/2.5 m² collector**, builds a *simulator*,
searches the 4-variable design space with that simulator, **picks one design per regime with a documented
funnel**, proves it on years never used for choosing, and finally lets **ANSYS Fluent** check the physics the
fast simulator assumed.

```
 OBJECTIVE 1 outputs                      FROZEN SYSTEM INPUTS
 ───────────────────                      ────────────────────
 regimes (K=3), medoid point              demand_profile_tamilnadu.csv  (24 hourly draws, 300 L/day)
 PCM shortlist per regime (top-3)         weather point-years  (NASA POWER hourly, 2011-2025)
 PCM properties (Tm, L, k, cp, ρ)         system_config_shared.yaml    (100 L tank, 2.5 m² collector…)
 mains temperature per regime             design_space.yaml            (4 variables + bounds + limits)
          │                                        │
          └───────────────┬────────────────────────┘
                          ▼
   LEVEL 1  design vector  (R_in, fraction→N, flow, arrangement)  ──►  geometry engine (valid? D, N, void, Ergun Δp)
                          ▼
   LEVEL 2  SIMULATOR  run_case → multinode tank  (weather → collector → tank ⇄ PCM capsules → draw)   8760 h
                          ▼
   LEVEL 3  METRICS   hourly series → g_window, g_annual, d_overheat, t_pcm_max …  (PAIRED vs plain-water tank)
                          ▼
   LEVEL 4  SEARCH    screening (L9) → 128-pt Sobol DOE → surrogate bake-off → NSGA-II + active learning → 720-grid check
                          ▼
   LEVEL 5  NOISE BAND  (how big must a gain be to be real?)  →  wp6_band.csv
                          ▼
   LEVEL 6  SELECTION funnel  Rule A → S0 → S1 → S2 → tie-breaks      (select years 2021-23)
                          ▼
   LEVEL 7  HELD-OUT test  (years 2011-15, run once, locked)   → tn_optimal_designs.csv / threshold report
                          ▼
   LEVEL 8  ANSYS Fluent  (capsule melt + whole-tank discharge) — consistency cross-check, never chooses
                          ▼
   LEVEL 9  Objective-3 contract (obj3_environment_contract_tamilnadu_v3.json)
```

---

## Level 0 — the inputs, and where each file is read

| input | file | what it contains | consumed by |
|---|---|---|---|
| **Demand** | `data/demand/demand_profile_tamilnadu.csv` | 24 rows: `hour, draw_fraction, draw_volume_L, draw_mass_kg`. Sums to **300 L/day**; peaks at 19:00 (51.9 L), 18:00 and 20:00 (41.6 L each), morning peak 08:00 (26.4 L). Declared in `configs/states/tamilnadu.yaml → demand_profile`. | `io_utils.load_demand_profile()` → `src/simulation/demand_profile.py::DemandModel` → `draw_mass_kg_for_hour()`; the same 24-hour day is repeated for all 365 days. |
| **Weather** | `data/weather/point_years/tamilnadu/cluster<c>_<medoid>_<year>.csv` (inventory: `weather_inventory.csv`) | hourly `GHI_Wm2`, `T_amb_C`, `RH_pct`, `wind_ms`, local hour. Medoid point per regime: **TNP_0006 / TNP_0007 / TNP_0001**. | `src/weather/roles.py::load_point_year()` – which also **enforces the year roles**: 2016-20 *explore*, 2021-23 *select*, 2011-15 *test* (locked). |
| **Regimes, PCM shortlist, mains T** | `configs/states/tamilnadu.yaml` (copied verbatim from Objective 1's `cluster_profiles_tamilnadu.csv` and `mcdm_topk_by_cluster.csv`) | per regime: `pcm_shortlist` (Regime 0 = RT57HC, n-Hexacosane, PureTemp 58), `T_mains_est_C` (28.46 / 23.97 / 27.77 °C), medoid id. | `io_utils.get_regime()`; mains T is the **inlet temperature of every draw**. |
| **PCM properties** | `data/objective1/pcm_database_tamilnadu.csv` | Tm, latent heat, cp(s/l), k, ρ(s/l) | `io_utils.get_pcm_properties()` → `capsule_enthalpy.pcm_props_from_record()` (melting is a narrow band Tm ± 1 K). |
| **System** | `configs/system_config_shared.yaml` | tank 100 L (H/D = 2, U = 0.8 W/m²K), collector 2.5 m² (F_R·τα = 0.75, F_R·U_L = 4.5, pump off below 10 W/m²), 0.8 mm Al capsule wall, delivery target 45 °C, safety shield (bypass at 72 °C water / 62 °C PCM), time step 150 s (search) / 37.5 s (reporting) | every module via `io_utils.load_system_config()` |
| **Design space + limits** | `configs/design_space.yaml` | R_in 10-40 mm, PCM fraction 2-30 %, flow 0.010-0.050 kg/s, arrangement ∈ {single-layer, staggered, radial}; hard limits PCM ≤ 65 °C, water ≤ 75 °C; `n_nodes = 10`; `stack_anchor = center` | `src/design/space.py` |

## Level 1 — the design vector becomes a geometry

`src/design/space.py::to_design(R_in, fraction, flow, arrangement)` →

* capsule outer volume `V = 4/3·π·(R_in + 0.8 mm)³`
* **count rule:** `N = clip( round(fraction · 0.100 m³ / V), ceil(0.02·0.1/V), floor(0.30·0.1/V) )`
  (this is why `N` is *derived*, not searched: e.g. R_in = 40 mm, 29.6 % → **N = 104**).

`src/design/constraints.py::check_design` → `src/design/geometry.py::compute_geometry` then returns, or
**rejects with a reason** (`overlap`, `volume_exceeded`, `passage_blocked`, `pressure_drop_limit`,
`flow_out_of_range`): capsule surface area, layers, stack height, void fraction (feeds Ergun Δp), tank
dimensions (D = 0.399 m, H = 0.799 m). An invalid design is **never simulated**.

## Level 2 — the simulator (`src/simulation/run_case.py`)

`run_case(state, regime, PCM, design, weather, tank_model="multinode", n_nodes=10, stack_anchor="center")`

Each simulated hour, for 8 760 hours:

1. **Weather → collector.** `I = GHI_Wm2` (horizontal irradiance is used directly; no tilt transposition — a known
   simplification). `Q_c = A·[F_Rτα·I − F_RU_L·(T_in − T_amb)]` (`collector_model.py`), only if `I > 10 W/m²`
   (pump on).
2. **Flow acts on stratification, not on Q.** Water leaves the bottom node at the *design flow*, is heated by
   `Q_c`, and re-enters at the node whose temperature is the highest one not above the outlet temperature
   (`tank_model_multinode.py`). Lower flow → hotter, better-stratified return.
3. **Tank ⇄ PCM.** The 10 nodes exchange heat by upwind advection + axial conduction + ambient loss
   (`U = 0.8 W/m²K`). Capsules sit in the nodes the packing places them in, and exchange heat with each node's
   water through `UA_eff` (Wakao-Kaguei convection + Al wall + `r/(5k)` PCM conduction,
   `heat_transfer.py`); inside the capsule the **enthalpy model** (`capsule_enthalpy.py`) gives temperature and
   **melt fraction `f_melt`**.
4. **Demand.** `DemandModel` draws `draw_mass_kg` from the **top node**; mains water (regime's `T_mains`) enters the
   bottom.
5. **Safety shield.** If the top water > 72 °C or PCM > 62 °C the collector loop is bypassed (counted as
   `shield_water_h`, `shield_pcm_h`).
6. **Output.** An hourly frame: `T_w_C` (outlet/top), `T_w_mean_C`, `T_pcm_C`, `f_melt`, `Q_collector`, `Q_load`,
   `Q_loss`, `E_stored`, `E_rec45`, … plus a summary and an energy-balance residual (≈ 1e-11 % — the gate that
   proves the simulator conserves energy).

## Level 3 — metrics: the numbers an optimiser can compare

`src/metrics/tes_metrics.py` turns the hourly frame into threshold-aware metrics. The optimiser always
uses **paired gains** — the same weather year, flow, demand and tank model with the **capsules removed**
(`src/optimize/baseline.py::plain_at`, a monotone PCHIP interpolation of 17 pre-simulated plain-tank flows per
year):

| objective | meaning | direction |
|---|---|---|
| `g_window` | extra heat delivered at ≥ 45 °C between 18:00 and 09:00, vs the plain tank (kWh/yr) | **max** (primary) |
| `g_annual` | same, over the whole year | max |
| `d_overheat` | extra shield-hours vs the plain tank | min |
| `t_pcm_max`, `t_water_max` | peak temperatures — **hard constraints** ≤ 65 °C / ≤ 75 °C in *every* year | feasibility |

`src/optimize/evaluate.py::evaluate_design` = *design → geometry check → simulate every year of a role →
paired differences → mean over years*. **This is the single function every later stage calls.**

## Level 4 — the search (all of it calls the Level-2 simulator)

| step | script | what changes |
|---|---|---|
| Sensitivity | `g7_sensitivity.py` | one-factor sweeps → which variables matter, approve the box |
| Plain baselines | `g8_build_plain_baseline.py` | 17 flows × explore/select years → `plain_baseline_*_r<c>.csv` |
| Screening | `g8_s1_screening.py` | Taguchi **L9**, 3 levels × 4 factors × 5 explore years + ANOVA |
| DOE | `g8_s2_doe.py` | **128 scrambled-Sobol points** (seed 20261026) per (regime, PCM) pair × 5 years; `u∈[0,1)⁴ → (R_in, fraction, flow, arrangement)` |
| Surrogates | `g8_s3_compare.py` | NN-ensemble vs XGBoost vs quadratic RSM, validated by 5-fold and leave-one-year-out; best Spearman wins. *A surrogate only proposes; it never reports.* |
| Optimise | `g9_s4_s5.py` | **NSGA-II** (pop 100 × 100 gen × 3 seeds) on the surrogate, objectives `(-g_window, -g_annual, d_overheat)`; then **active learning**: simulate the 10 designs the model committee disagrees on most, refit, repeat (≤ 5 rounds, stop when hypervolume moves < 1 %) |
| Cross-check | `g9_s6_grid.py` | **720-design dense grid** (6 R × 8 fractions × 5 flows × 3 arrangements) to prove NSGA-II did not miss a region |
| BO track | `g20_gp_bo_comparison.py` | independent GP + Bayesian optimisation of the same problem |

*Where the final parameters end up:* radius and fraction go **to the bounds (40 mm, ~30 %)** because more PCM
mass monotonically increases `g_window`; the interior trade-off is **flow** and the funnel's tie-breaks.

## Level 5 — how big must a gain be to count? (`g9_band.py`, `g9_assess.py` → `results/wp6_band.csv`)

`band = √( (sd_year/√5)² + Δ_dt² + Δ_nodes² + Δ_props² )` — year-to-year scatter, time step 150→75 s, nodes 10→20,
latent heat ±10 %, conductivity ±20 %. For Regime 0: **g_window band = 28.4 kWh/yr**, d_overheat band = 115 h.
*Any difference smaller than the band is declared noise.* This number drives the whole funnel.

## Level 6 — final selection (`g10_select.py`, select years 2021-23, dt = 37.5 s)

Candidates: for every O1 PCM of the regime, the non-dominated feasible designs (≤ 30 per PCM), **re-simulated on
years the search never saw**.

```
hard gates   PCM ≤ 65 °C, water ≤ 75 °C, exact geometry
Rule A       g_window > band            else "no meaningful benefit" (indistinguishable from a plain tank)
S0           within one band of the best g_window          ("statistically tied for best")
S1           within one overheating-band of the lowest d_overheat inside S0
S2           within the measured serve-time (τ_serve) band of the best gain in S1
tie-breaks   lowest PCM mass  →  fewest capsules  →  largest margin to 65 °C
```

Regime 0 result: 90 candidates → 14 in S0 → 5 in S1 → 3 in S2 → **PureTemp 58, R_in = 40 mm, N = 104,
29.6 %, 0.0388 kg/s, staggered, 24.8 kg PCM** (`results/g10_selection_r0.json`, SHA-256 fingerprint inside).
*RT57HC has a slightly higher g_window (297 vs 277), but within the 28.4 band, and PureTemp has lower
overheating/mass, so the funnel treats them as tied and prefers it.*

## Level 7 — held-out test (`g10_test.py`)

The frozen design **plus the best design of every other shortlisted PCM** (9 designs) is run **once** on
2011-15 under an atomic lock (`results/held_out_test.lock`). Output `results/g10_heldout_results.csv`;
`tn_final_summary.py` writes `tn_optimal_designs.csv` and `tn_threshold_report.csv` — all gates passed (9/9
beat plain water, PCM 62.3–62.5 °C, water 72.0–72.2 °C).

## Level 8 — ANSYS Fluent: "is the fast model's physics reasonable?"

| Fluent case | what goes in (from Objective 2) | what comes out | where |
|---|---|---|---|
| Single capsule melt | optimal R_in, PCM properties from `pcm_database_tamilnadu.csv`, 70 °C charging water | liquid-fraction vs time, melt-front contours | `ansys/fluent_live_demo.py`, `docs/CFD_VERIFICATION.md` |
| Whole-tank discharge | chosen PCM, capsule count/radius (2-D proxy: 34 drawn ≙ 104 real), capsules hot, water 30 °C, no sun | water/capsule temperature and liquid fraction vs time, contours | `ansys/fluent_tank_discharge.py` and the new `ansys/criteria_*/` folders |

Role: *model-consistency cross-check* of the assumptions in Level 2 (lumped `r/(5k)` conduction, melt band, the
liquid-convection factor). **It does not choose the design, and it is not experimental validation.**

## Level 9 — hand-off to Objective 3 (`g25_obj3_contract.py`)

`results/obj3_environment_contract_tamilnadu_v3.json`: per-regime static design, action space, reset scenarios,
limits, repeatability band, held-out status — every number read from `results/`/`configs/`.

---

## One parameter, end to end (worked example: **capsule count**)

1. **Search variable** `pcm_volume_fraction ∈ [0.02, 0.30]`, with `R_in`. → 2. `to_design` → `N = 104` (R = 40 mm, f = 29.6 %).
3. `compute_geometry` → layers, stack height, void fraction, Ergun Δp (valid). → 4. `run_case` → PCM mass **24.8 kg**, `UA_eff`
total = N × per-capsule conductance, capsules distributed over nodes. → 5. Hourly `T_pcm`, `f_melt` → latent storage.
6. `evaluate_design` → `g_window = 276.6 kWh/yr` over the plain tank. → 7. Surrogate/NSGA-II learn `N ↑ → g_window ↑` until the 30 % cap.
8. Band 28.4 kWh → 14 designs are statistically tied (S0); overheating and serve-time filters leave 3 (S2); the tie-break "lowest PCM mass, then fewest capsules" picks **104**.
9. Held-out: 283.4 kWh/yr on 2011-15. → 10. Fluent: the drawn 34-capsule slice reproduces the discharge shape.

## Where to look when you need to *show* each level

| level | one file to open |
|---|---|
| 0 inputs | `configs/states/tamilnadu.yaml`, `data/demand/demand_profile_tamilnadu.csv` |
| 1-2 | `src/design/space.py`, `src/simulation/run_case.py` |
| 3 | `src/optimize/evaluate.py` |
| 4 | `results/g8_s2_r0_p3.csv`, `results/g9_points_r0_p3*.csv`, `results/g8_s3_selection.csv` |
| 5 | `results/wp6_band.csv` |
| 6 | `results/g10_selection_r0.json`, `results/g10_selection_candidates_r0.csv` |
| 7 | `results/g10_heldout_results.csv`, `results/tn_optimal_designs.csv` |
| 8 | `ansys/criteria_*/…` (new), `ansys/figures/`, `docs/CFD_VERIFICATION.md` |
| what-if study | `ansys/criteria_common/SUMMARY_all_criteria.{csv,png}` |
