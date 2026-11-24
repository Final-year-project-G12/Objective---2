# Common-plant rebuild log — Tamil Nadu Objective 2

Plan: `docs/plan/Unified_Objectives_2_3_Rebuild_Plan_Four_States_REVISED_v1.docx` (rules R1-R20) and `docs/plan/tamilnadu_new.docx`.

## Phase 1 — config, years, locks, weather (2026-11-20)

| Item | Change | Where |
|---|---|---|
| Collector area | 2.5 → **2.0 m²** (absorber-area basis stated; F_R·τα 0.75 and F_R·U_L 4.5 carried from legacy fit, to be re-checked) | `configs/system_config_shared.yaml` (config_v2.0) |
| Demand | 300 → **100 L/day** (profile shape unchanged, rescaled) | `configs/states/tamilnadu.yaml`, `data/demand/demand_profile_tamilnadu.csv` |
| PCM fraction cap | 0.30 → **0.40** | `configs/design_space.yaml` (v4) |
| Flow | searched 0.010-0.050 → **frozen 0.030 kg/s**; geometry validity range kept 0.010-0.050 for sensitivity runs | `configs/design_space.yaml`, `src/io_utils.py` |
| Stack anchor | declared `stack_anchors: [bottom, center, top]` (robust objective, rule R7). **Evaluator code not yet written (Phase 2).** | `configs/design_space.yaml` |
| Year roles | 2016-19 explore, 2020-21 select, **2006-10 test (once)**, 2022-25 report-only, 2011-15 legacy (no purpose) | `src/weather/roles.py` |
| Lock | keyed to a hash of plant/design/state/demand files: `results/common100L_<hash>/held_out_test.lock`; legacy lock path refused | `src/weather/roles.py` |
| Weather | 2006-2010 fetched from NASA POWER (UTC, 3 medoids x 5 yr), point-years + inventory rebuilt (60 point-years) | `scripts/c1_fetch_confirmatory_2006_2010.py`, `scripts/tn_rebuild_weather_from_raw.py` |
| Old results | archived, new empty `results/` | `archive/legacy_results_300L_2p5m2_2026-11-19/` |

### Verification notes (honest)
* `suntimes.csv` has no rows for 2006-2010, so the sunrise/sunset check in the rebuild script covered **0 days** for those years
  (it used to print "geometry OK" anyway; it now warns). Timing was verified independently against the 2017 clear-sky profile
  of the same point: 0-3 of ~4000 sunlit hours differ per year (a timestamp shift would give hundreds).
* NASA POWER 2006-2010 weather is not yet GHI-audited (weather-only audit is plan step O2-1, Phase 2).
* `test_our_copy_has_not_drifted_from_objective_1` fails: `data/objective1/mcdm_topk_by_cluster.csv` differs from Objective 1's
  own file. To be resolved at L1 (O1 alignment) before design search.
* Still legacy / to redo: F_R·τα, U_L basis, O3 contract builders (`src/handoff/*`) and `g10`/`g12`/`g25` scripts that read the old lock.

## L1 — O1 alignment (2026-11-20)
* The failing drift test was caused by Objective 1 being re-run on 2026-11-10 after our copy (2026-10-29). **The top-3 PCM shortlist per regime, the rankings and the hard cluster labels are identical**; the only change in `mcdm_topk` was a run-stamp column.
* Real differences found: membership probabilities/bootstrap stats, and O1's physics-validation medoid for regime 0 (TNP_0006 → TNP_0011). Regime 0 has 24 points tied at probability 1.0, so O1's "medoid" is a tie-break, not a finding. O2 keeps TNP_0006 / TNP_0007 / TNP_0001 (each in its tied set). Stated limitation.
* O1's rank-vs-physics Spearman moved 0.169 → −0.069 (weak, not significant either way): the shortlist must not be called physics-validated.
* Re-copied 11 O1 files into `data/objective1/` (old copies in `archive/o1_inputs_copy_2026-10-29/`). Manifest with hashes: `configs/o1_alignment_manifest_tamilnadu.json`.
* Decision: Option B (keep shortlist, 45 °C = service threshold). **Not yet done:** a 45 °C check that the shortlist would not change.
* Tests: 93 passed, 2 skipped, 0 failed.

## L1 follow-up — does a 45 °C service change the PCM shortlist? (2026-11-20)  `scripts/c2_pcm_identity_check_45C.py`
O1 sized its target at 67 °C (capped to ~62 °C by climate). At a 45 °C service the target becomes ~52 °C, which puts O1's shortlist
(Tm 54–58 °C) above the ceiling, so Option B ("shortlist unchanged") was an assumption. Tested by simulation: one fixed design
(R_in 25 mm, 30 %, 0.030 kg/s, staggered), 34 database PCMs (Tm 44–59.5 °C, known conductivity) per regime, explore years 2017–18,
paired gain vs same-flow water-only at 45 °C (g_window, kWh/yr). Files: `results/c2_pcm_identity_45C_r{0,1,2}.csv`.
* O1 shortlist (RT57HC, n-Hexacosane, PureTemp 58, n-Pentacosane): g_window between **−1.4 and +0.3** kWh/yr (≈ 0).
* Best: RT45HC / n-Docosane (44.5–45 °C): **+1.6 / +5.8 / +3.4** (regimes 0/1/2); n-Tricosane, savE OM46, Lauric acid close behind.
* Caveats: one design, 2 years, small absolute energies; each PCM has its own optimum design; not a design result.
* **DECIDED (user, 2026-11-20): PCMs are taken only from Objective 1's shortlist.** No new PCMs are added in O2; the config is unchanged. The result above is kept as a stated limitation and as a pointer for a possible Objective 1 re-run at 45 °C.

## L2 — weather-only audit (2026-11-20)  `scripts/c3_weather_audit.py` → `results/c3_weather_audit.{csv,md}`
All 60 medoid-years: 8,760 h, 0 missing GHI, max |z| annual GHI = 1.7. Mean annual GHI (kWh/m²), regime 0/1/2:
explore 2012/1864/1898, select 1953/1828/1838, test 2025/1847/1911, report 1949/1829/1832. The select years are 3–4 % below explore;
test years sit close to explore. No data-quality defect → split kept as specified (plan 7.3). Not swapped after viewing outcomes.

## L3 — simulator verification (2026-11-20)  `scripts/c4_l3_verification.py` → `results/c4_l3_*`
Year 2017, PCM design (R 25 mm, f 30 % and 40 %) and same-flow water-only, per regime.
* Timestep halving, max change per halving: delivered 45 °C energy (window) 0.006 %, annual 0.0009 %; collector useful energy
  **0.134 % (150→75), 0.073 % (75→37.5), 0.039 % (37.5→18.75)** → the gate (<0.05 %) is met on useful energy only from 37.5 s,
  as in the legacy tank. Rule R5 stands: search 150 s, confirm/report 37.5 s. Shield hours shift by up to 29 h across dt.
* 10 vs 20 nodes (dt 150): delivered window energy shifts 0.02–0.21 %, useful energy 1.4–2.8 % → goes into the repeatability band.
* Energy closure: residual ≤ 7e-11 % of collector energy (gate 0.1 %).
* IS 12976:2023 cl. 4.2.3 standing loss (no draw/sun, 16 h): drop **2.05–4.82 °C** (limit 8 °C) for start 45/60 °C, ambient 20/28 °C.
* Note: peak water temperature reached 72.9 °C (guard 72, hard 75): the 2.0 m² collector overheats the 100 L tank often.
* G1 is therefore met for geometry/closure/timestep/standing loss on these cases; full per-regime × PCM re-check and the
  geometry gate at 2–40 % still to run before declaring G1 for the whole box.

## G1 — O2 physics gate (2026-11-20)  `scripts/c5_g1_geometry_gate.py`, `scripts/c6_g1_pairs.py`
**Geometry (step O2-3):** R_in 10–40 mm × fraction 2–40 % × 3 arrangements = 780 points, 702 valid. Every rejection has a code:
`passage_blocked` 57, `bounds_violation` 21. 40 % is reachable for staggered at 12 of 13 radii and single-layer at 9; radial packing mostly
blocks it (1 radius). Smallest radii (10 mm) cap near 26 % (count ceiling). Files `results/c5_g1_geometry_{grid,summary}.csv`.
**Per regime × O1 PCM** (9 pairs × fraction 30/40 %, R 25 mm staggered, 2017) `results/c6_g1_pairs_r*.csv`:
* dt 150 vs 37.5 s, delivered-window change 0.0001–0.0037 % (gate 0.05 %) — pass.
* 10 vs 20 nodes: 0.02–0.12 % → into the repeatability band.
* Energy-closure residual 0.0 % (gate 0.1 %); PCM peak ≤ 64.4 °C (≤ 65), water peak ≤ 72.7 °C (≤ 75); 0 hours over the hard limit.
* Deterministic rerun identical in all 18; zero-latent-heat control delivers 6–61 kWh/yr less than the real PCM → latent heat is doing something, as expected.
**G1 = passed** for the box on these cases (single year 2017 at the stated design; the unit-test suite covers invariance/limiting cases, 93 passing).
Still to run before the search: paired same-flow baselines at the final dt for select years (built), sensitivity (L4), Taguchi L9.

## L4 — baselines, sensitivity, Taguchi L9 (2026-11-20)
**Code:** `evaluate_design(..., stack_anchor=)` and `evaluate_design_robust()` implement rule R7 (all three anchors; ranking = mean paired gain;
reject if worst-anchor gain ≤ 0 or inside the band) with a unit test. Paired baseline grids rebuilt for explore/select at the final dt.
**One-at-a-time sensitivity** (`scripts/c7_l4_sensitivity.py`, `results/c7_l4_sensitivity_r*.csv`): reference design R 25 mm, 30 %, staggered,
0.030 kg/s, 3 O1 PCMs, explore 2017–18, every case paired with a water-only twin under the same perturbation. Paired gain g_window (kWh/yr, regimes 0/1/2):
| case | gain | note |
|---|---|---|
| reference (100 L/day, 2.0 m²) | −0.15 / −0.69 / −0.16 | ≈ 0 |
| 70 L/day | +0.1 / +0.2 / +0.3 | ≈ 0 |
| **150 L/day** | **+68 / +73 / +67** | demand sensitivity |
| **300 L/day (legacy)** | **+165 / +106 / +148** | |
| collector F_R·τα, F_R·U_L ±10 %, area 2.5 m² | within −1.8 … +0.1 | |
| mains ±3 °C, flow 0.015/0.050 (± F_R(flow)), anchor, PCM latent ±10 %, Tm ±1.5 K, k ±20 % | all within about ±1.8 | |
**Finding:** demand is the only parameter that matters. The water-only tank already delivers 568/717/588 kWh/yr in the 45 °C window at
100 L/day, so there is no unmet energy for PCM to add; the 2.0 m² collector oversupplies the 100 L tank (water-only shield ≈ 2,300–2,800 h/yr).
PCM only pays off once demand exceeds what the plain tank meets (≥ 150 L/day). Every other sensitivity moves the gain by < 1.5 kWh.
**Taguchi L9** (`scripts/c8_l4_taguchi.py`; factors R_in 10/25/40 mm, fraction 2/21/40 %, anchor, arrangement; flow frozen; 9 pairs × 4 explore years;
2 of 9 runs per pair are geometry-invalid): paired g_window −3.0 … +1.0 kWh/yr in every pair. Fraction is the dominant factor
(10–81 % of variance, more PCM = worse), then arrangement (5–17 %); anchor matters mainly for overheat hours (44–67 %).
**Implication for the O2 search:** with the plant fixed at 100 L/day the PCM gain is inside any plausible repeatability band, so the
expected O2 outcome is "water-only is as good" (a legitimate result under the plan, section 4.3). Needs a decision before L5.

## Plant scan — when does PCM beat the plain tank? (2026-11-23)  `scripts/c12_plant_scan.py`, `results/c12_plant_scan_r*.csv`
Fixed design (R 40 mm, 30 %, staggered), rank-1 O1 PCM, explore 2017–18, same 100 L total tank. Mean over 3 regimes, paired g_window (kWh/yr) and
the water-only solar fraction (SF = share of demand the plain tank already meets):
| collector | 100 L/day | 150 | 200 | 300 |
|---|---|---|---|---|
| 1.0 m² | −14 (SF .94) | −29 (.76) | −46 (.62) | −60 (.44) |
| 1.5 m² | −2.6 (.98) | +47 (.84) | +78 (.70) | +90 (.51) |
| **2.0 m²** | **−0.6 (.99)** | **+75 (.88)** | **+154 (.74)** | **+212 (.55)** |
| 2.5 m² | −0.1 (.99) | +80 (.90) | +182 (.77) | +269 (.58) |
**Rule found:** PCM adds delivered energy only when the plain tank leaves demand unmet (SF below ~0.9). At 100 L/day SF = 0.99, so there is nothing to add; the
legacy run (2.5 m², 300 L/day, SF 0.58–0.59) was demand-limited, which is why PCM won there (+269 here, legacy +178…+269). A smaller collector makes PCM worse
(capsules displace water and less heat arrives). Shield hours are higher with PCM at every setting (less water in the same tank).
The L5 DOE was stopped (81–97 of 128 designs, pair 1 only) because it ran at 100 L/day; those partial files must be archived if the demand changes.

## All-category check, PCM minus plain (2026-11-23)  `scripts/c13_categories_check.py`, `results/c13_categories_r*.csv`
2.0 m², 100 L tank, design R 40 mm/30 %/staggered, 3 regimes, 2017. Mean PCM − plain: delivered window kWh / hold h / serve h / serve frac / shield h:
100 L/day −0.5 / +0.5 / 0.0 / 0.00 / +2180 · 150: +74 / +0.9 / +4.9 / +0.19 / +1149 · 175: +120 / +1.0 / +6.2 / +0.13 / +989 · 200: +153 / +1.1 / +3.2 / +0.10 / +881 ·
300: +211 / +1.3 / +0.1 / +0.02 / +648. Shield (overheat-guard) hours are WORSE with PCM at every demand in all 3 regimes; peak water temperature is lower with PCM.
Conclusion: no plant setting makes PCM better in every category.

## DECISION — demand amended to 175 L/day (2026-11-23)
User decision after the plant scan: main O2 run uses **175 L/day of 45 °C water** (tank 100 L and collector 2.0 m² unchanged). Basis: a 100 LPD heater rated at ~60 °C stored water
delivers ≈171–191 L/day at 45 °C with Tamil Nadu mains (24–28.5 °C); the plan's own Rev 9 note gives ≈175. At 100 L/day the plain tank met 99 % of demand, so PCM could not add energy.
Sensitivity cases (never for selection): 100, 150 and 300 L/day. Changed: `configs/states/tamilnadu.yaml` (v5.0), `data/demand/demand_profile_tamilnadu.csv` (sums to 175),
test updated. The hardware hash changed, so the lock namespace is new. Everything run at 100 L/day (L3 checks, L4 sensitivity/Taguchi, PCM screen, baselines, partial DOE) is archived in
`archive/diagnostics_100Lday_2026-11-23/` and `archive/l5_doe_partial_100Lday_2026-11-23/`; baselines, G1 checks and the L5 DOE are re-run at 175 L/day.
Plan documents in `docs/plan/` still say 100 L/day (rule R1): this log is the amendment of record; the docs are regenerated at the end.
Honest expectation: PCM should beat the plain tank on delivered energy, hold and serve metrics (+≈120 kWh/yr at 175 L/day in the scan) in all three regimes,
but NOT on overheat-guard hours, and nothing is guaranteed until the 2006–2010 one-shot test.

## Unattended pipeline launched (2026-11-23 ~22:40) — L5 → L9, L8 Fluent, M1 MATLAB, docs
Driver `scripts/run_o2_pipeline.py` (status: `results/pipeline_status.json`, log: `results/logs/pipeline.log`), then `scripts/run_post_o2.py` (status: `results/post_o2_status.json`).
Stages: DOE (c9, 9 pairs, 6 parallel workers) → fidelity check c10 (pre-registered rule) → surrogates c11 → NSGA-II + active learning c14 → dense grid + repeatability band c15 →
funnel freeze + select-year evaluation + winners c16 → ONE-SHOT test 2006-2010 under the hash-keyed lock + report-only years + O3 contract c17 → L4 sensitivity/Taguchi at 175 L/day (c7, c8) →
Fluent seven criteria around the new optimum (ansys/criteria_common/regen_scenarios.py, build_criteria_folders.py, run_node_model.py, run_all_fluent.py) → MATLAB M1 (c20 export, matlab_m1/m1_main.m) →
docs (c21: RESULTS_COMMON_PLANT.md, PLAN_DEVIATIONS.md, Word report, README status, legacy banners; c22: plan documents Revision 11).
Smoke-tested end to end on partial data (real test lock never touched). Parallelism: pooled workers (RAM-limited, ~1.7 GB free of 15.7 GB measured; the simulator is memory-bound beyond ~4-6 jobs).
**Decision disclosed:** repeatability band for the funnel = CORE (years, timestep, nodes, PCM properties, anchor); mains and demand are separate scenario sensitivities; both bands are reported.
It was decided after a smoke test showed demand +/-20 % moves the gain by ~99 kWh; the core definition matches the legacy 26-30 kWh band.
MATLAB dev run (stand-in optimum): figures A-E built; heat-balance residual about -0.1 % of collector energy over 48 h windows.
