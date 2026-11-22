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

## 4. Open items

- Collector parameters and area basis for 2.0 m2 (needs a source before the L3 gate is signed).

## 5. Repeatability band recipe (to be frozen at L7, before the select-year evaluation)

Placeholder: year scatter, time step, node count, PCM properties, medoid versus member points, demand and mains. To be written in full
before the band is computed.

## 6. Level tracker

| Level | Content | Status |
|---|---|---|
| L0 | decide and freeze; archive legacy; new results namespace | done 2026-11-22 |
| L1 | O1 alignment (Option B, manifest hashes) | done 2026-11-22: `results/o1_manifest_uttarakhand.json` (`scripts/r1_o1_manifest.py`) |
| L2 | config, weather (incl. 2006-2010), year roles, locks, hashes | done 2026-11-22: section 3b; 94 tests pass, 5 skip (need the L4 baseline) |
| L3 | simulator verification (geometry 2-40 %, dt halving to 18.75 s, 10 vs 20 nodes, energy closure, IS 12976 standing loss) | |
| L4 | baselines and sensitivity; Taguchi L9 | |
| L5 | Sobol DOE, surrogates, cheap-vs-full fidelity screen | |
| L6 | NSGA-II + active learning; Pareto fronts | |
| L7 | 720-point grid, band, funnel frozen | |
| L8 | (Tamil Nadu only: ANSYS Fluent) | n/a |
| L9 | one-shot 2006-2010 test, report-only years, O3 contract | |
