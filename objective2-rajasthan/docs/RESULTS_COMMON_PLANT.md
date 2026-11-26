# Results - Rajasthan Objective 2 on the common plant (100 L tank, 2.0 m2, 175 L/day)

Written 2026-11-25 from saved files only (named under each table). Decision record: `docs/REBUILD_COMMON100L.md` (section 8 = the demand deviation).
Gains are PAIRED differences against a water-only tank at the same flow (0.030 kg/s), weather, demand and shield. `g_window` = energy delivered at 45 C in the
18:00-09:00 window (kWh/yr), `g_annual` = whole year, `d_overheat` = overheat-guard hours of the PCM tank minus the water-only tank (h/yr).
The legacy 50 L / 1.5 m2 results (docs 01-07, PROGRESS) are NOT these results; see the banner on each.

## 1. Headline

PCM beats the water-only tank in all three regimes at 175 L/day, in the select years, in the one-shot 2006-2010 test and in the report-only years 2022-2025.
It does so only at this demand (section 6) and it always costs more overheat-guard hours (section 5).

## 2. Chosen design per regime (frozen funnel on 2020-2021)

Source: `results/g10_selection_r{0,1,2}.json`, `results/g9_band_r*.csv`, `results/wp6_band.csv`.

| regime | PCM | R_in mm | fraction | capsules | arrangement | select g_window | worst-anchor g_window | band g_window | d_overheat | S0 / S1 / S2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | savE OM55 | 40.0 | 0.398 | 140 | staggered | 140.8 | 127.0 (bottom) | 39.8 | +660 | 5 / 2 / 1 |
| 1 | PureTemp 60 | 39.1 | 0.335 | 126 | staggered | 59.9 | 42.2 (bottom) | 24.6 | +357 | 18 / 3 / 3 |
| 2 | PureTemp 58 | 40.0 | 0.398 | 140 | staggered | 107.9 | 97.8 (bottom) | 24.3 | +632 | 8 / 6 / 2 |

The band used by the funnel is Rajasthan's FULL pre-registered band (years, dt, nodes, properties, members, demand and mains), the stricter one. Tamil Nadu's funnel
used a core band and reported the full one next to it; here no such change was needed. Regime 0 has only 4 member points, so its band is calibrated on those 4 (project decision).
Flow is fixed at 0.030 kg/s (rule R6).

## 3. One-shot held-out test 2006-2010 (run once, lock `results/locks/o2_test_eb67320ff3cb.lock`, run `o2test_c5b9324ead83`)

Source: `results/o2_test_2006_2010.csv`, mean of 5 years x bottom/centre/top anchors, 37.5 s step.

| regime | g_window | g_annual | worst-anchor g_window | band | d_overheat | hours over limit | water peak C | PCM peak C |
|---|---|---|---|---|---|---|---|---|
| 0 | 158.2 | 167.7 | 145.2 | 39.8 | +797 | 0 | 72.1 | 62.2 |
| 1 | 70.8 | 76.0 | 52.6 | 24.6 | +416 | 0 | 72.1 | 62.1 |
| 2 | 125.2 | 132.5 | 115.4 | 24.3 | +739 | 0 | 72.1 | 62.3 |

Every year and every anchor has a positive gain. Test gains are above the select-year gains (140.8 / 59.9 / 107.9); the test was not used for any choice.
Hygiene (share of days with stored water at 60 C or more for 1 h): PCM tank 0.914 / 0.953 / 0.916 vs water-only 0.879 / 0.911 / 0.861 (`o2_test_2006_2010_plain_hygiene.csv`), so not worse.
Other O1 PCMs tested next to the chosen one (`role=best_of_pcm`): in regime 1 n-Heptacosane gave 94.8 and CrodaTherm 60 gave 80.3 against the chosen 70.8, and in regime 2 PlusICE A58
gave 115.5 against the chosen 125.2. The alternatives that gain more carry about +1000 overheat hours, which is why the frozen funnel did not pick them; this is a trade-off to report, not a defect.

## 4. Report-only years 2022-2025 (never used to choose)

Source: `results/o2_report_2022_2025.csv`, chosen designs.

| regime | g_window | g_annual | worst-anchor g_window | d_overheat | yearly g_annual 2022 / 23 / 24 / 25 |
|---|---|---|---|---|---|
| 0 | 137.8 | 147.6 | 122.8 | +605 | 161.1 / 147.9 / 139.4 / 142.2 |
| 1 | 54.6 | 60.1 | 36.9 | +319 | 67.2 / 61.8 / 56.2 / 55.1 |
| 2 | 101.2 | 109.2 | 91.2 | +567 | 118.8 / 114.9 / 98.9 / 104.1 |

All positive at every anchor and year. Regime 1 is the weakest: its worst-anchor gain (36.9 kWh/yr) clears its band (24.6) by only about 12 kWh/yr.
The two lowest years (2024, 2025) are the lowest-gain years in every regime.

## 5. The cost: overheat-guard hours

PCM tanks hold less water in the same 100 L, so they reach the guard more often. d_overheat is positive in every regime and every period (select +660 / +357 / +632,
test +797 / +416 / +739, report +605 / +319 / +567 h/yr). No design exceeded a hard limit (hours over limit = 0). Sunny Rajasthan has more surplus heat than Tamil Nadu, so this cost is real and is reported, not hidden.
Objective 3 (collector ENABLE/BYPASS control) is the lever meant to cut it.

## 6. What this does and does not show

- The win depends on the DECLARED demand of 175 L/day (same as Tamil Nadu). At 100 L/day the explore-year plant scan gives about -1 to -5 kWh/yr (`results/r12_plant_scan_r*.csv`,
  `REBUILD_COMMON100L.md` section 8). The demand was chosen after that scan, on explore years only; this is a plant-definition decision and is disclosed.
- 175 L/day on a 100 L tank is still below IS 12976:2023 storage guidance (1.5-2x daily volume).
- The design is the best found inside the declared box (R_in 10-40 mm, fraction 2-40 %, three arrangements). The 40 mm radius end binds in almost every Pareto front and the 40 % cap in many
  (`results/g9_boundary_check.csv`), so a larger box could do better; this is a stated limitation.
- The dense grid check covers rank-1 PCM only (`results/g9_grid_check.csv`: epsilon vs search 0 / 0.96 / 0 kWh, all inside the band).
- The lumped capsule model and the grey-box tank are verified (L3) but not experimentally validated; CFD is not described as validated.
- Collector parameters and area basis still have no source (`REBUILD_COMMON100L.md` section 7).

## 7. Files

`results/g10_selection_r*.json`, `o2_test_2006_2010*.csv`, `o2_report_2022_2025*.csv`, `wp6_band.csv`, `obj3_environment_contract_rajasthan_common100L.json`,
`results/plots_common100L/` (rb1-rb5), `logs/chain.txt`, `logs/stage_*.txt`.

## 8. Supplementary studies (post-result, never used for selection)

Source: `results/supp_case_*.csv`, `supp_sensitivity_r*.csv`, `supp_aux_heater_r*.csv`, `supp_boundary_below_2pct.csv` (script `scripts/r10_supplementary.py`, select years, the chosen PCM, a grid of designs per case).
Best paired g_window over the designs tried, regimes 0 / 1 / 2 (kWh/yr):

| plant case | best g_window | reading |
|---|---|---|
| 70 L/day | 0.3 / 0.0 / 0.2 | no gain |
| 100 L/day | 0.4 / -0.4 / 0.1 | no gain |
| 150 L/day | 85.0 / 43.9 / 58.9 | gain returns |
| 175 L/day (this plant) | 140.8 / 59.9 / 107.9 (selection) | |
| 300 L/day on 2.5 m2 (legacy demand) | 243.7 / 146.9 / 196.1 | largest gain |
| 175 L/day on a 150 L tank | -0.4 / -2.3 / -2.4 | no gain: a bigger tank leaves nothing for PCM to add |

So the PCM gain is a statement about an undersized-storage plant. Increase the tank to 150 L and it vanishes at this demand.

One-at-a-time sensitivity of the chosen design (regime base g_window 137.9 / 57.8 / 109.0):
- Collector F_R(tau alpha) -10 % costs 26.4 / 17.9 / 29.3 kWh/yr; GHI -15 % costs 42.4 / 28.5 / 46.4; coldest mains (18 C) costs 22.7 / 37.4 / 24.7. Regime 0 and 2 stay well above their bands.
- Regime 1 is fragile: at GHI -15 %, mains -4 K, or mains 18 C its worst-anchor gain falls to 16.0 / 16.9 / -7.9 kWh/yr, which is inside or below its band (24.6). Its win should be read as conditional on the simulated climate and collector.
- Flow-dependent collector efficiency (not in the main model) at 0.010 kg/s removes most of the gain (63.7 / -28.8 / 15.5); flow at or above 0.030 kg/s keeps it. Flow is fixed at 0.030 kg/s in this study.
- Capsule radius +0.5 mm is infeasible in regimes 0 and 2 (the design sits on the 40 mm bound); PCM fill 95 % costs 9.1 / 6.8 / 9.0 kWh/yr.
- Auxiliary-heater saving by the PCM tank is in `supp_aux_heater_r*.csv` (45 C and 50 C thresholds).
