# Uttarakhand Objective 2 rebuild on the common 100 L plant

This file is the decision record and level tracker for the rebuild. The plan is the project's
"Unified Objective 2 + Objective 3 Rebuild Plan" (Revision 13, 20 November 2026), adopted by the student on 2026-11-22.
Only Objective 2 for Uttarakhand is done here. Objective 3 and Objective 4 follow after the Objective 2 release (plan L9).

## 1. What happened to the old results

The finished 50 L / 1.5 m2 / 300 L/day run (v3, cap 30 %, K = 4, 50 C, held-out 2024-2025) is **legacy**. It is kept unchanged in
`results_legacy_50L_v3/`, including its spent lock `held_out_test.lock`, the Objective 3 contracts v2/v3 and 36 figures.
It is never used to select the new design (plan section 2.2). The documents `01`-`06` in this folder still describe that legacy run;
their `results/...` paths now point to `results_legacy_50L_v3/...`. They will be replaced level by level.

The supplementary legacy studies g20-g24 (GP-BO comparison, tank sizing, extra sensitivity, Chen benchmark, flow-dependent F_R) finished
on 2026-11-14/15 and are in the archive; g18 (search variants) and B1 (widened box) were not run on the legacy plant.

## 2. Frozen decisions (plan section 0.3 rules, with the Uttarakhand choices)

| Item | Value | Source |
|---|---|---|
| Plant | 100 L tank, 2.0 m2 collector, 100 L/day | R1 |
| Collector area basis | **open**: the model's F_R(tau alpha) 0.75 and F_R U_L 4.5 are "typical flat-plate" values with no stated area basis | plan 1.1; see section 4 |
| Delivery threshold | 45 C primary (selection); 50 C secondary, reported separately, never pooled | R2 |
| O1 basis | Option B: the K = 4 shortlists are kept unchanged | R2, decision 9 |
| Regimes | K = 4 (UKP_0014, UKP_0029, UKP_0025, UKP_0041) | decision of 2026-11-12 |
| Year roles | 2016-2019 explore; 2020-2021 select; 2022-2023 and 2024-2025 report-only; 2006-2010 one-shot confirmatory test | R3 |
| Design box | inner radius 10-40 mm (student choice 2026-11-22: kept as a declared limit); PCM fraction 2-40 %; arrangements single-layer / staggered / radial | R4 |
| Flow | fixed at 0.030 kg/s, not a search variable; F_R(flow) only as a sensitivity study | R6 |
| Stack anchor | robust objective over bottom / centre / top: rank on the mean paired gain; reject a design whose worst-anchor gain is below zero or inside the band | R7 |
| Solver | 10-node tank; search dt 150 s; confirmation and report dt 37.5 s unless the halving gate says otherwise | R5 |
| Safety | water guard 72 C / hard 75 C; PCM guard 62 C / hard 65 C | R8 |
| Hygiene | share of days with stored water >= 60 C for >= 1 h, and the longest run without it; PCM tank AND water-only tank reported | R9 |
| Method | Taguchi L9, Sobol DOE, surrogate comparison, NSGA-II + active learning, Pareto front, 720-point grid, band, frozen funnel, one-shot test | R10 |
| Locks | lock path keyed to the hardware hash; the legacy lock stays in the archive and cannot be reused | R20, plan 7.5 |
| Compute | at most 3 parallel simulator workers; never alongside the WSL OpenFOAM runs (memory failures on 2026-11-14) | plan 14.2 |

## 3. Interpretations of the plan (from the plan review of 2026-11-22)

- **Test years:** where the plan text still names 2022-2023 or 2024-2025 as a test, Revision 10 wins: 2006-2010 is the only test.
- **Exposure:** 2006-2010 is unseen for Objective 2. The old Uttarakhand Objective 3 test used it, so it is not unseen for Objective 3.
- **2006-2010 weather:** fetched from NASA POWER with the same request (point, community RE, parameters, UTC) and passed through
  the same inventory and acceptance rule as 2016-2025, so the test years come from the same source and processing.
- **Repeatability band:** components fixed before any run (section 5). The stack anchor is in the objective (R7), so it is **not**
  also a band component.
- **Pareto front:** paired gain, overheating and PCM mass. No cost source exists, so "cost" is not used.
- **Flow:** fixed at 0.030 kg/s in the SEARCH only (`configs/design_space.yaml` variables). The geometry/validity check uses the pump's
  physical range 0.010-0.050 kg/s (`src/io_utils.load_design_bounds`), so sensitivity and verification cases at other flows stay valid.
- **50 C secondary:** the delivery target enters only the accounting in the kernel (delivered, unmet and recoverable energy), never the
  physics, so the 50 C numbers are obtained by re-running a design with `delivery.target_temp_C` overridden to 50 (identical temperatures).

## 3b. L2 findings (2026-11-22)

- 2006-2010 fetched (`scripts/r2_fetch_test_weather.py`, 20 files); all 60 point-years (4 medoids x 15 years) pass the acceptance rule
  (`data/weather/point_years/weather_inventory.csv`); the 40 existing 2016-2025 hourly files are byte-identical after the rebuild.
- Demand: 100 L/day with the same hourly shape (peak at hour 19); the 300 L/day profile is `data/legacy/demand_profile_uttarakhand_300L.csv`.
- `geometry_engine.capsule_count` max raised 5000 -> 10000: at 100 L the old bound (meant never to bind) rejected 10 mm capsules at
  30-40 % (5700-7600 capsules). Now only packing rejects designs (radial at 30-40 %, single-layer 10 mm at 40 %: passage blocked).
- **Weather-only audit (plan 7.3; `results/l2_weather_audit_*.csv`): the 2006-2010 test years are sunnier than 2016-2025 in every regime**
  (annual GHI +31 to +64 kWh/m2 on the period mean; 2009, the Indian monsoon-drought year, and 2006 are the sunniest, z up to +5 in
  regime 0). Clear-sky GHI is only about 1 % higher, clearness about 2.5 % higher, and clearness also falls within 2016-2025 (regime 0:
  0.855 in 2016 to 0.816 in 2025): fewer clouds and less aerosol, a real climate/aerosol difference, not a data defect. Per plan 7.3
  the split is kept as declared; the test is reported as somewhat sunnier than the design years (not a harsher-than-average test).
- Input manifest (gate G0): `results/l2_input_manifest.json`, plant hash `ad1135145a63`, 67 files hashed; test lock path
  `results/locks/o2_test_ad1135145a63.lock`.

## 3c. L3 findings (2026-11-22; `scripts/r3_verification.py`, `results/l3_*.csv`)

Four regimes, rank-1 PCM, flow 0.030, 10-node tank, explore year 2018; designs V30 (R 30 mm, 30 %) and V40 (R 30 mm, 40 %), staggered.

- **Energy closure:** largest residual 5e-11 % of collector energy (limit 0.1 %). Pass.
- **Time step:** change per halving of the primary metric E_del45_window, worst case: 0.088 % (150->75), 0.044 % (75->37.5),
  0.022 % (37.5->18.75); annual useful energy 0.136 / 0.076 / 0.037 %. Feasibility identical at every step (PCM peak up to 1.7 K
  higher at 150 s). Decision (plan R5 default): search at 150 s, confirm and report at 37.5 s.
- **Nodes 10 -> 20** (37.5 s): useful energy +2.4 to +2.6 %, paired gain 2-8 kWh/yr more negative; much larger than on the 50 L tank
  (0.7-1.0 %), so it is a large band component.
- **IS 12976 standing loss** (100 L water-only, 60 C start, 16 h): 4.8 K at 20 C ambient (limit 8 K, pass, all regimes); with each
  regime's coldest explore-year hour held for 16 h: 6.9 / 7.4 / 7.6 K (regimes 0-2, pass) and **9.4 K in regime 3 at -18.3 C (fail)**.
  The standard gives no ambient for the check; the 20 C case is the reference, the cold case is reported as a cold-climate limitation.
- **PCM gain on the common plant (`scripts/r3_probe_pcm_gain.py`, exploratory, 2018 only):** no design gains. Both verification designs
  are below the water-only tank in every regime (-7 to -25 kWh/yr; more PCM is worse). Over 108 designs (R 20/40 mm; 5/15/30 %;
  single-layer/staggered; bottom/centre/top) the best is -0.5 kWh/yr in regimes 0 and 1 and +4.2 kWh/yr in regime 3 (5 % PCM, top).
  Diagnostic (regimes 1 and 3, R 40 mm staggered centre, 5/15/30 % PCM): regime 1 gains only once the draw exceeds the tank
  (150 L/day: +3 / +10 / +15; 300 L/day: +3 / +15 / +25 kWh/yr) and is about zero at 50 C; regime 3 is negative in every case.
  Reading: at 100 L/day a 100 L tank with 2.0 m2 already stores a full day's hot water, so PCM only displaces water.

## 3d. Search protocol, declared 2026-11-23 BEFORE any L4-L7 run (`src/design/box.py`)

- **Fidelities:** cheap = 150 s on the representative explore year (closest annual GHI to the 2016-2019 mean, weather only:
  regime 0 -> 2018, 1 -> 2018, 2 -> 2017, 3 -> 2018); full = 37.5 s on every year of the role. Screening (L9) uses all four explore
  years at 150 s; DOE, NSGA-II and the dense grid use cheap; finalists, selection, test and report years use full.
- **Cheap-vs-full acceptance:** on the finalists the Spearman correlation of the mean paired g_window, cheap against full, must be
  >= 0.7; otherwise the cheap screen is not used for selection and the finalists are re-ranked at full fidelity only.
- **Robust anchor (R7):** every PCM evaluation at bottom, centre and top; objectives are means over anchors (and years); the
  worst-anchor gain is stored. The water-only twin does not depend on the anchor and is simulated once per year (exact, flow 0.030).
- **Search objectives** (unchanged method, rebuild box): maximise mean g_window and g_annual, minimise d_overheat; the Pareto front is
  reported with PCM mass. Surrogates: nn_ensemble, xgboost, rsm_quadratic, gp_ard, stacked (R10); validated by 5-fold over designs and
  by rank quality on the better half of the designs (a leave-one-year-out check is not possible on the one-year cheap DOE; year
  generalisation is tested by the cheap-vs-full check).

## 3e. Selection funnel, frozen 2026-11-23 BEFORE any select-year evaluation (`scripts/g10_select.py`)

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
6. Cheap-vs-full: Spearman(cheap g_window, full select-year g_window) over the finalists >= 0.7, else the cheap screen is reported
   as not usable for selection.

## 3f. L4-L5 findings (2026-11-23)

- **Baseline** (`scripts/g8_build_plain_baseline.py`): exact water-only runs at 0.030 kg/s, explore and select roles, 150 s and 37.5 s.
- **Taguchi L9** (`scripts/g8_s1_screening.py`, 12 pairs, 2016-2019, three anchors): PCM fraction carries 68-98 % of the g_window
  variance in every pair, inner radius 9-22 %, arrangement 10-16 %, anchor 0-4 %. Two of the nine L9 runs (radial at 10 mm / 40 % and
  at 40 mm / 21 %) cannot be packed in the 100 L tank, so the array is unbalanced and the per-factor sums of squares overlap (the
  "error" share comes out negative); the shares are indicative only. The ranking itself (fraction first) is the same in every pair.
- **Sobol DOE** (`scripts/g8_s2_doe.py`, 128 points x 12 pairs, cheap fidelity, three anchors): 116 of 128 simulated per pair, 12
  geometry-rejected, no errors. Best mean g_window over all 1,392 designs: +1.7 kWh/yr (regime 3, PureTemp 53); best in regimes
  0-2: -0.2 / -0.2 / +0.8 kWh/yr; median design -2 to -18 kWh/yr. This confirms the L3 probe: on the common plant no PCM design
  delivers meaningfully more than the water-only tank at 45 C. The search (L6) and selection continue as declared.
- Compute: one cheap design about 15 s (three anchors); the PC slept 10:05-11:57 on 2026-11-23 and the jobs resumed unharmed.

## 4. Open items

- Collector parameters and area basis for 2.0 m2 (needs a source before the L3 gate is signed).

## 5. Repeatability band recipe (to be frozen at L7, before the select-year evaluation)

Frozen 2026-11-23, before the band is computed and before any select-year evaluation (`scripts/g9_band.py`):

- **Designs:** per regime, 4 designs of the rank-1 PCM from the cheap DOE: the 20 %, 50 % and 80 % quantiles of g_annual among
  feasible designs, and the best feasible g_window. All at the centre anchor (the anchor is in the objective, not the band), flow
  0.030, the four explore years 2016-2019, 150 s unless the term says otherwise. Every variant's water-only twin gets the same change.
- **Terms** (each the RMS over the 4 designs of the change in the 4-year mean paired gain against the base variant):
  1. year scatter: mean over designs of the per-year sd of the paired gain divided by sqrt(2) (the selection judges 2-year means);
  2. time step: 37.5 s against 18.75 s (the remaining discretisation error at the report step);
  3. node count: 10 against 20 nodes, at 37.5 s;
  4. PCM properties: the larger of latent heat +-10 % and conductivity +-20 %;
  5. medoid versus member points: the same design on the two most-populated non-medoid members of the regime
     (`scripts/r7_member_weather.py`, `data/weather/point_years/member_inventory.csv`);
  6. demand: 100 L/day x 0.8 and x 1.2; 7. mains: regime estimate -2 K and +2 K.
- **Band** = sqrt(sum of the squared terms), per regime and pooled ("all"), for g_window, g_annual and d_overheat. A gain counts as
  meaningful only if it exceeds the band (plan section 5). Stack position is not a term (R7 puts it in the objective).

## 6. Level tracker

| Level | Content | Status |
|---|---|---|
| L0 | decide and freeze; archive legacy; new results namespace | done 2026-11-22 |
| L1 | O1 alignment (Option B, manifest hashes) | done 2026-11-22: `results/o1_manifest_uttarakhand.json` (`scripts/r1_o1_manifest.py`) |
| L2 | config, weather (incl. 2006-2010), year roles, locks, hashes | done 2026-11-22: section 3b; 94 tests pass, 5 skip (need the L4 baseline) |
| L3 | simulator verification (geometry 2-40 %, dt halving to 18.75 s, 10 vs 20 nodes, energy closure, IS 12976 standing loss) | done 2026-11-22: section 3c (gate passed; regime-3 cold standing-loss case fails, reported). Collector area basis still open |
| L4 | baselines and sensitivity; Taguchi L9 | done 2026-11-23: section 3f |
| L5 | Sobol DOE, surrogates, cheap-vs-full fidelity screen | DOE done 2026-11-23 (section 3f); surrogates running |
| L6 | NSGA-II + active learning; Pareto fronts | |
| L7 | 720-point grid, band, funnel frozen | |
| L8 | (Tamil Nadu only: ANSYS Fluent) | n/a |
| L9 | one-shot 2006-2010 test, report-only years, O3 contract | |
