# Objective 2 (Rajasthan): data flow from input to output

Written 2026-11-26. Paths are relative to `objective2-rajasthan/`. Stage names are those of `pipeline.py`.

## 1. Inputs

| input | file | comes from |
|---|---|---|
| climate regimes, member points, medoids, PCM Top-3 per regime | `data/objective1/` (`manifest.json`, `mcdm_topk_by_cluster.csv`, `cluster_assignments_rajasthan.csv`, `pcm_database_rajasthan.csv`) | Objective 1 output, copied; hashed in `results/o1_manifest_rajasthan.json` |
| hourly weather per member point and year (2006-2025) | `data/weather/point_years/rajasthan/`, raw 2006-2010 in `data/weather/raw_test_2006_2010/` | NASA POWER (same request for every year), inventory in `data/weather/weather_inventory.csv` |
| demand profile | `data/demand/demand_profile_rajasthan.csv` (175 L/day); legacy 100 and 300 L/day in `data/legacy/` | local-time hourly shape, rescaled |
| system constants | `configs/system_config_shared.yaml` (tank, collector, pump, safety, PCM integration c = 5, F = 2), `configs/design_space.yaml` (the search box), `configs/states/rajasthan.yaml` | frozen; edited only through the declared deviation in `docs/REBUILD_COMMON100L.md` section 8 |
| year roles | `src/weather/roles.py` | explore 2016-2019, select 2020-2021, report-only 2022-2025, test 2006-2010 (lock) |

## 2. Stage by stage

| stage | reads | writes |
|---|---|---|
| o1 | `data/objective1/` | `results/o1_manifest_rajasthan.json` |
| weather | weather files | `results/l2_input_manifest.json`, `l2_weather_audit_*.csv`, `data/weather/member_inventory.csv` |
| verify | kernel, weather | `results/l3_timestep*.csv`, `l3_nodes*.csv`, `l3_standing_loss*.csv` (time-step halving, 10 vs 20 nodes, energy closure, IS 12976 standing loss) |
| baseline | weather, demand | `results/plain_baseline_{explore,select}_dt{150,37p5}_r*.csv` (water-only tank, exact, per year) |
| screening | baselines, kernel | `results/g8_s1_r*_p*.csv`, `g8_s1_anova_*.csv` (Taguchi L9 per regime and PCM) |
| doe | baselines, kernel | `results/g8_s2_r*_p*.csv` (128 Sobol designs per pair, three anchors) |
| surrogate | DOE files | `results/g8_s3_comparison.csv`, `g8_s3_selection.csv` (five model families, 5-fold errors) |
| optimize | DOE, surrogates, kernel | `results/g9_points_r*_p*.csv` (every simulated design), `g9_al_log_*.csv` (active-learning rounds) |
| grid | kernel | `results/g9_s6_grid_r*_p1.csv` (240 designs per regime, rank-1 PCM) |
| band | kernel | `results/g9_band_r*.csv` (one row per design, variant and objective) |
| assess | optimize, grid, band outputs | `results/g9_grid_check.csv`, `g9_boundary_check.csv`, `g9_al_summary.csv`, `wp6_band.csv` (band table: per regime and pooled) |
| select | optimize, band, kernel on 2020-2021 | `results/g10_selection_candidates_r*.csv`, `g10_selection_r*.json` (chosen design, funnel counts, fingerprint) |
| test | selection files, lock | `results/o2_test_2006_2010.csv`, `o2_test_2006_2010_plain_hygiene.csv`, `o2_test_night.csv`, `results/locks/o2_test_<hash>.lock` |
| report | selection files, lock | `results/o2_report_2022_2025.csv`, `o2_report_night.csv` |
| handoff | all of the above, configs | `results/obj3_environment_contract_rajasthan_common100L.json` (copied to `objective3/`) |
| m1 | kernel, selection | `results/m1_matlab/hourly_r*_*.csv`, `summary.csv`, then MATLAB: `m1_gate.csv/.txt`, `figures/m1_r*_*.png` |
| figures | the CSVs above | `results/plots_common100L/rb1-rb5` |
| supplementary | kernel, selection | `results/supp_*.csv` (sensitivities, plant cases, auxiliary heater, bound below 2 %) |
| manifest | every output | `results/o2_output_manifest.json` (SHA-256 per file) |

Not part of the chain: `results/r12_plant_scan_r*.csv` (script `scripts/r12_plant_scan.py`), the explore-years plant scan behind the demand decision.

## 3. How one number is built

A design (regime, PCM, inner radius, PCM fraction, arrangement) is simulated by the grey-box kernel (`src/simulation/`): a 10-node stratified water tank, a collector (F_R tau alpha 0.75, F_R U_L 4.5, no flow dependence), a lumped enthalpy capsule model per node, and a safety shield (bypass at 62 C PCM and 72 C water). It runs hourly weather and the demand profile for a year at bottom, centre and top anchors. The same weather and demand run with a water-only tank gives the baseline. `g_window` = PCM-tank E_del,45 minus water-only E_del,45 in the 18:00-09:00 window; `g_annual` is the whole year; `d_overheat` = guard hours of the PCM tank minus the water-only tank.

## 4. Output to claim

Everything quoted in `docs/RESULTS_COMMON_PLANT.md` is a direct read of the files in the table above. `results/o2_output_manifest.json` fixes their hashes; `scripts/r24_check_o3_contract.py` re-derives the contract numbers from the CSVs.
