# Rajasthan Objective 2 rebuild on the common 100 L plant

This file is the decision record and level tracker for the rebuild. The plan is the project's
"Unified Objective 2 + Objective 3 Rebuild Plan" (Revision 14, 22 November 2026; `.claude/Unified_Objectives_2_3_Rebuild_Plan_Four_States_REVISED_rev14.docx`).
Work started on 2026-11-24 on git branch `rajasthan-o2-common100L`. The method and code are the Uttarakhand rebuild's (commits
c18945ab..7e393262, 2026-11-22/23), ported file by file; only the state data differ (3 regimes, 9 (regime, PCM) pairs, Rajasthan
medoids and weather). Only Objective 2 is done here. Objective 3 follows after the Objective 2 release (plan L9); see section 7.

## 1. What happened to the old results

The finished 50 L / 1.5 m2 / 300 L/day run (v3, cap 30 %, K = 3, 45 C, held-out 2011-2015) is **legacy**. It is kept unchanged in
`results_legacy_50L_v3/`, including its spent lock `held_out_test.lock` (run id `heldout_3242a7f4fd8a`), the Objective 3 contracts
v2/v3 and the supplementary studies g20-g24. It is never used to select the new design (plan section 2.2). The documents `01`-`07`
and `PROGRESS.md` in this folder still describe that legacy run; their `results/...` paths now point to `results_legacy_50L_v3/...`.
They are updated level by level (section 6, last row).

## 2. Frozen decisions (plan section 0.3 rules, with the Rajasthan choices)

| Item | Value | Source |
|---|---|---|
| Plant | 100 L tank, 2.0 m2 collector, 100 L/day | R1 |
| Collector area basis | **open**: the F_R(tau alpha) 0.75 and F_R U_L 4.5 are "typical flat-plate" values with no stated area basis | plan 1.1 |
| Delivery threshold | 45 C primary (selection). 50 C is an optional secondary report (plan 1.2; required only for Uttarakhand); never pooled | R2 |
| O1 basis | Option B: the K = 3 shortlists are kept unchanged | R2, decision 9 |
| Regimes | K = 3 (RJP_0132 Udaipur, RJP_0192 Nagaur, RJP_0083 Jaipur); membership from O1 Level A (109 / 83 / 128 points) | L1 |
| Year roles | 2016-2019 explore; 2020-2021 select; 2022-2023 and 2024-2025 report-only; 2006-2010 one-shot confirmatory test | R3 |
| Design box | inner radius 10-40 mm (kept from the legacy box as a declared limit); PCM fraction 2-40 %; arrangements single-layer / staggered / radial | R4 |
| Flow | fixed at 0.030 kg/s, not a search variable; F_R(flow) only as a sensitivity study | R6 |
| Stack anchor | robust objective over bottom / centre / top: rank on the mean paired gain; reject a design whose worst-anchor gain is below zero or inside the band | R7 |
| Solver | 10-node tank; search dt 150 s; confirmation and report dt 37.5 s unless the halving gate says otherwise | R5 |
| Safety | water guard 72 C / hard 75 C; PCM guard 62 C / hard 65 C | R8 |
| Hygiene | share of days with stored water >= 60 C for >= 1 h, and the longest run without it; PCM tank AND water-only tank reported | R9 |
| Method | Taguchi L9, Sobol DOE, surrogate comparison, NSGA-II + active learning, Pareto front, dense grid (240 designs per regime, rank-1 PCM), band, frozen funnel, one-shot test | R10 |
| Locks | lock path keyed to the plant hash: `results/locks/o2_test_<hash>.lock`; the legacy lock stays in the archive and is never read | R20, plan 7.5 |
| Compute | at most 3 parallel simulator workers; never alongside the WSL OpenFOAM runs (memory failures on 2026-11-14) | plan 14.2 |

## 3. Interpretations of the plan

- **Test years:** where the plan text still names 2022-2023 or 2024-2025 as a test, Revision 10 wins: 2006-2010 is the only test.
- **Exposure:** 2006-2010 is unseen for Objective 2. The legacy Rajasthan Objective 3 test used it (50 L plant), so it is not unseen
  for Objective 3. 2011-2015 (legacy O2 v3 test) and 2024-2025 (legacy O2 v1 test) are exposed and are not used for any choice;
  the 2011-2015 point-year files remain on disk but have no role in `src/weather/roles.py`, so they cannot be loaded.
- **2006-2010 weather:** the 15 files were built for the old Objective 3 test from NASA POWER with the same request as 2016-2025
  (`solar-pcm-control--Objective3/rajasthan/data/weather_test_2006_2010/`); they were copied here (CSV and raw JSON,
  `data/weather/raw_test_2006_2010/`) and re-run through this tree's own inventory and acceptance rule. The O3 CSVs and the CSVs
  rebuilt here are byte-identical for the three medoids.
- **Repeatability band:** components fixed before any run (section 5). The stack anchor is in the objective (R7), so it is **not**
  also a band component.
- **Pareto front:** paired gain, overheating and PCM mass. No cost source exists, so "cost" is not used.
- **Flow:** fixed at 0.030 kg/s in the SEARCH only (`configs/design_space.yaml` variables). The geometry/validity check uses the pump's
  physical range 0.010-0.050 kg/s (`src/io_utils.load_design_bounds`), so sensitivity and verification cases at other flows stay valid.
- **50 C secondary:** the delivery target enters only the accounting in the kernel, so the 50 C numbers come from re-running a design
  with `delivery.target_temp_C` overridden to 50 (identical temperatures).
- **Demand profile (superseded by section 8, now 175 L/day):** 100 L/day with the legacy hourly shape (the `draw_fraction` column is unchanged; volume and mass are 100 x
  fraction). The 300 L/day file is `data/legacy/demand_profile_rajasthan_300L.csv`.

## 3b. L1 and L2 findings (2026-11-24)

- **O1 manifest** (`scripts/r1_o1_manifest.py`, `results/o1_manifest_rajasthan.json`): the Level A assignments (109 / 83 / 128 points,
  population 21.8 / 14.0 / 34.5 million) were copied into `data/objective1/cluster_assignments_rajasthan.csv`. O1's current
  `cluster_profiles_rajasthan.csv` equals the frozen copy in every column except `HDD18` and `CDD24`, which O1 corrected after the O2
  input freeze (`pre_hdd_cdd_fix_backup_2026-09-19` in O1); they are not clustering inputs for O2, and the finding is stored in the
  manifest. Shortlists as in the state yaml: r0 savE OM55 / Palmitic-stearic acid-expanded graphite / Myristic acid-NBR-0.5;
  r1 PureTemp 60 / CrodaTherm 60 / n-Heptacosane; r2 n-Heptacosane / PureTemp 58 / PlusICE A58. The regime-0 candidate pool of 4
  and its Monte Carlo percentages are the already-decided O1 issue (accepted, calibrated kappa); nothing is re-ranked (Option B).
- **Weather** (`data/weather/point_years/weather_inventory.csv`): 45 point-years (3 medoids x 15 years), all accepted, 100 % valid
  hours, no gaps; the 30 existing 2016-2025 hourly files are byte-identical after the rebuild.
- **Weather-only audit** (plan 7.3; `scripts/r2_weather_audit.py`, `results/l2_weather_audit_*.csv`): **the 2006-2010 test years are
  sunnier than 2016-2025 in every regime**: mean annual GHI 1998 / 2079 / 1994 kWh/m2 against 1903 / 2010 / 1925 (explore), +105 /
  +69 / +69; 2009 is the sunniest (z up to +2.6 on annual GHI, +3.8 on monsoon GHI in regime 0); six point-years have |z| > 2.5 on at
  least one measure. Per plan 7.3 the split is kept as declared; the test is reported as somewhat sunnier than the design years.
- **Plant hash and input manifest** (gate G0): `results/l2_input_manifest.json`, plant hash `77375efae097`, 52 files hashed; test
  lock path `results/locks/o2_test_77375efae097.lock`.
- Tests: 94 pass, 5 skip (they need the L4 baseline).

## 4. Search protocol (declared 2026-11-24, BEFORE any L4-L7 run; identical to the Uttarakhand rebuild, `src/design/box.py`)

- **Fidelities:** cheap = 150 s on the representative explore year (closest annual GHI to the 2016-2019 mean, weather only:
  regime 0 -> 2018 (1886 against a mean of 1903), regime 1 -> 2017 (2012 against 2010), regime 2 -> 2018 (1902 against 1925));
  full = 37.5 s on every year of the role. Screening (L4) uses all four explore years at 150 s; DOE, NSGA-II and the dense grid use
  cheap; finalists, selection, test and report years use full.
- **Cheap-vs-full acceptance:** on the finalists the Spearman correlation of the mean paired g_window, cheap against full, must be
  >= 0.7; otherwise the cheap screen is not used for selection and the finalists are re-ranked at full fidelity only.
- **Robust anchor (R7):** every PCM evaluation at bottom, centre and top; objectives are means over anchors (and years); the
  worst-anchor gain is stored. The water-only twin does not depend on the anchor and is simulated once per year (exact, flow 0.030).
- **Search objectives:** maximise mean g_window and g_annual, minimise d_overheat; the Pareto front is reported with PCM mass.
  Surrogates: nn_ensemble, xgboost, rsm_quadratic, gp_ard, stacked (R10), validated by 5-fold over designs and by rank quality on
  the better half of the designs.

## 4b. Selection funnel, frozen BEFORE any select-year evaluation (`scripts/g10_select.py`)

1. Finalists: per (regime, PCM) the non-dominated feasible cheap-fidelity designs (g_window, g_annual, d_overheat), thinned evenly
   along g_annual to at most 12; each re-simulated at the FULL fidelity on 2020-2021 at all three anchors.
2. Hard constraints on the select years: PCM peak <= 65 C and water peak <= 75 C in every year at every anchor; exact geometry.
3. Plan R7: a design is eligible as "better than water-only" only if its worst-anchor mean select-year g_window exceeds the regime
   band (section 5). If no design is eligible, the regime's recommendation is **water-only** (plan decision 4); the funnel below
   is then applied to all feasible finalists and its pick is recorded and tested as the "best PCM design", not as a recommendation.
4. Funnel on the eligible (or, if none, the feasible) set: S0 = within band(g_window) of the best mean g_window; S1 = those within
   band(d_overheat) of the lowest overheating; S2 = those within the measured tau_serve standard error of the best tau_serve gain
   (night scenarios at 37.5 s, centre anchor, top 12 by g_window); pick the lowest PCM mass, then fewest capsules, then the largest
   margin to 65 C. Everything left in S0 is reported as indistinguishable.
5. Frozen for the test: the pick plus the best g_window design of every other O1 PCM of the regime; SHA-256 fingerprint per regime.

## 5. Repeatability band recipe (frozen before the band is computed and before any select-year evaluation, `scripts/g9_band.py`)

- **Designs:** per regime, 4 designs of the rank-1 PCM from the cheap DOE: the 20 %, 50 % and 80 % quantiles of g_annual among
  feasible designs, and the best feasible g_window. All at the centre anchor (the anchor is in the objective, not the band), flow
  0.030, the four explore years 2016-2019, 150 s unless the term says otherwise. Every variant's water-only twin gets the same change.
- **Terms** (each the RMS over the 4 designs of the change in the 4-year mean paired gain against the base variant):
  1. year scatter: mean over designs of the per-year sd of the paired gain divided by sqrt(2) (the selection judges 2-year means);
  2. time step: 37.5 s against 18.75 s;
  3. node count: 10 against 20 nodes, at 37.5 s;
  4. PCM properties: the larger of latent heat +-10 % and conductivity +-20 %;
  5. medoid versus member points: the same design on the two most-populated non-medoid members of the regime
     (`scripts/r7_member_weather.py`, `data/weather/point_years/member_inventory.csv`);
  6. demand: 100 L/day x 0.8 and x 1.2; 7. mains: regime estimate -2 K and +2 K.
- **Band** = sqrt(sum of the squared terms), per regime and pooled ("all"), for g_window, g_annual and d_overheat. A gain counts as
  meaningful only if it exceeds the band (plan section 5). Stack position is not a term (R7 puts it in the objective).
- **Deviation record:** the band includes the demand term, as the plan defines it (compare Assam deviation D1, plan Revision 14, where
  the term was removed after the result was seen). Rajasthan keeps the pre-registered band; there is no D1-style deviation here.

## 6. Level tracker

| Level | Content | Status |
|---|---|---|
| L0 | decide and freeze; archive legacy; new results namespace | done 2026-11-24 |
| L1 | O1 alignment (Option B, manifest hashes) | done 2026-11-24: section 3b |
| L2 | config, weather (incl. 2006-2010), year roles, locks, hashes | done 2026-11-24: section 3b; 94 tests pass, 5 skip |
| L3 | simulator verification (geometry 2-40 %, dt halving, 10 vs 20 nodes, energy closure, IS 12976 standing loss) | done, re-run at 175 L/day 2026-11-25 |
| L4 | baselines and sensitivity; Taguchi L9 | done 2026-11-25 (175 L/day) |
| L5 | Sobol DOE, surrogates, cheap-vs-full fidelity screen | done 2026-11-25 |
| L6 | NSGA-II + active learning; Pareto fronts | done 2026-11-25 |
| L7 | dense grid (rank-1 PCM), band, funnel frozen and run | done 2026-11-25: PCM in all three regimes |
| L8 | (Tamil Nadu only: ANSYS Fluent) | n/a |
| L9 | one-shot 2006-2010 test, report-only years, O3 contract | done 2026-11-25: `docs/RESULTS_COMMON_PLANT.md` |
| M1 | MATLAB checkpoint | done 2026-11-26: gate PASS, 12 of 12 runs (`results/m1_matlab/m1_gate.txt`) |
| O3 hand-off | `objective3/` folder, contract check script | done 2026-11-26: `scripts/r24_check_o3_contract.py` 25 of 25 |

## 7. Open items

- Collector parameters and area basis for 2.0 m2: still no source (F_R(tau alpha) 0.75, F_R U_L 4.5 are typical flat-plate values).
- Objective 3 for Rajasthan (plan L10-L16) is not started; its repository still points to the legacy 50 L contract. The new contract is `results/obj3_environment_contract_rajasthan_common100L.json` (PCM designs, 175 L/day).
- The 40 mm radius end and the 40 % fraction cap bind in the Pareto fronts (`g9_boundary_check.csv`); a wider box is untested.
- Results are in `docs/RESULTS_COMMON_PLANT.md`. Docs 01-07, PROGRESS and the root README describe the legacy v3 50 L pipeline and carry a banner saying so.

## 8. Declared deviation 2026-11-25: demand 100 -> 175 L/day (same as Tamil Nadu)

OUTCOME (2026-11-25): the one-shot test and the report-only years both favour PCM in all three regimes; see `docs/RESULTS_COMMON_PLANT.md`. The chosen designs are at 126-140 capsules, R_in 39-40 mm, fraction 0.34-0.40.

Declared BEFORE any L3-L9 result was produced on this plant; the test years 2006-2010 were not touched.

- **What changed:** `configs/states/rajasthan.yaml` `daily_total_L` 100 -> 175; `data/demand/demand_profile_rajasthan.csv` rescaled (same hourly shape, `draw_volume_L`
  and `draw_mass_kg` = 175 x `draw_fraction`); the 100 L/day file is kept as `data/legacy/demand_profile_rajasthan_100L.csv`. Tank 100 L and collector 2.0 m2 are unchanged.
  `scripts/r10_supplementary.py` cases are now absolute (d70, d100, d150, legacy 300 L/day, t150). Plan rule R1 (100 L/day) is therefore amended for this state.
- **Why:** the plant scan `scripts/r12_plant_scan.py` (regime rank-1 O1 PCM, fixed design R 40 mm / 30 % / staggered / 0.030 kg/s, explore years 2017-2018 only,
  `results/r12_plant_scan_r{0,1,2}.csv`) gives, at 2.0 m2, a paired g_window of -1.1 / -3.6 / -4.6 kWh/yr at 100 L/day (the plain tank meets 98-99 % of the demand,
  so there is nothing for a PCM to add), +76 / +31 / +39 at 150, +149 / +61 / +69 at 200 and +185 / +80 / +93 at 300 L/day (regimes 0 / 1 / 2). The same rule was found for
  Tamil Nadu (`objective2-tamilnadu/docs/COMMON_PLANT_REBUILD_LOG.md`, "Plant scan"). 175 L/day is the 45 C equivalent of a 100 LPD heater rated at about 60 C
  (Tamil Nadu plan note, Rev 9); it is the value Tamil Nadu used, so the states stay comparable. Mains temperature differs by state, so the equivalence is approximate.
- **What this does NOT show:** it does not prove that PCM wins in Rajasthan. The scan interpolates to roughly +110 / +45 / +55 kWh/yr at 175 L/day for the fixed design;
  regimes 1 and 2 may land inside the repeatability band. The one-shot 2006-2010 test decides, under the lock. PCM tanks hold less water, so overheat-guard hours are expected
  to be higher with PCM at every demand (Tamil Nadu: +627 to +998 h/yr). Sunny Rajasthan has more surplus heat than Tamil Nadu, so the overheating cost is reported, not hidden.
- **Honest limits:** 175 L/day on a 100 L tank is still below the IS 12976:2023 1.5-2x storage guidance; choosing demand after seeing that PCM does not help at 100 L/day is
  a plant-definition decision made on explore years, and it is disclosed here and in the final report.
- Everything produced before this change on the 100 L/day plant (the L3 verification, the scan itself) is superseded; L3 is re-run at 175 L/day.
