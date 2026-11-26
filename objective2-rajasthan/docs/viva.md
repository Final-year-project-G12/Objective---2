# Objective 2 (Rajasthan) - viva quick reference

Numbers are from `docs/RESULTS_COMMON_PLANT.md`; every one traces to a CSV in `results/`.

## 1) What Objective 2 does - in 7 points

1. Takes Objective 1's three Rajasthan climate regimes and its Top-3 PCMs for each.
2. Fixes one plant: 100 L tank, 2.0 m2 collector, pump flow 0.030 kg/s, 175 L/day of 45 C water.
3. Searches PCM, capsule inner radius (10-40 mm), PCM fraction (2-40 %) and arrangement with Taguchi screening, a Sobol DOE, five surrogate families, and NSGA-II with active learning. Surrogates propose; the simulator decides.
4. Measures how much the gain moves with year, time step, node count, properties, member point, demand and mains (the repeatability band) and only trusts a gain above it.
5. Picks one design per regime with a funnel frozen before it saw the select years (2020-2021).
6. Tests it once on 2006-2010 (locked) and reports 2022-2025.
7. Hands Objective 3 a contract: the plant, the designs, the limits and the baseline to beat.

## 2) The result in one table

| regime | PCM | capsules | test g_window | worst anchor | band | extra guard hours |
|---|---|---|---|---|---|---|
| 0 | savE OM55 | 140 | 158.2 kWh/yr | 145.2 | 39.8 | +797 h/yr |
| 1 | PureTemp 60 | 126 | 70.8 | 52.6 | 24.6 | +416 |
| 2 | PureTemp 58 | 140 | 125.2 | 115.4 | 24.3 | +739 |

## 3) The questions you should expect

**Why 175 L/day, not 100?** At 100 L/day the plain tank covers 98-99 % of the demand, so a PCM cannot add energy (-1 to -5 kWh/yr). 175 L/day is the 45 C equivalent of a 100 LPD heater rated at 60 C and is what Tamil Nadu uses. We chose it after the scan, on explore years only, and say so. The PCM gain disappears again with a 150 L tank.

**So does PCM really help?** It helps a tank that is too small for its demand: it stores surplus heat for the evening. It is not a general claim. The cost is more overheat-guard hours (+300 to +800 h/yr) because capsules displace water.

**Is the chosen design optimal?** No: best found inside the declared box. The 40 mm radius end binds in nearly every Pareto front. A larger box could do better.

**Why were alternatives with higher test gain not chosen?** In regimes 1 and 2 other O1 PCMs gained more on the test (regime 1 n-Heptacosane 94.8 vs 70.8 kWh/yr), but with about +1000 guard hours. The funnel, frozen in advance, prefers the lowest guard hours and PCM mass among designs the band cannot tell apart. Report the trade-off.

**How do you know the gain is not noise?** The worst of the bottom, centre and top anchors must beat the band; all do, in select, test and report years. Regime 1 is the thinnest (worst-anchor report gain 36.9 vs band 24.6) and fragile to weaker sun or colder mains (supplementary study).

**Was the test fair?** 2006-2010 was untouched until the lock was set; selection used 2020-2021 only; the lock is keyed to the plant hash. Afterwards nothing may be re-chosen from it.

**Is the simulator validated?** No. It is verified (time-step, node and energy-closure checks pass) and cross-checked against CFD for single capsules (incomplete, does not reproduce the literature benchmark). There is no experiment. Never say "CFD-validated".

**What about the capsule constants?** c = 5 and F = 2 are frozen. The lumped model melts slower than CFD and single-capsule experiments (conservative for charging); at tank level the Objective 4 benchmark supports the constants.

**Regime 0 has only four points?** Yes; its band is calibrated on those four. Disclosed.

**What does Objective 3 get?** The contract; its job is to cut guard hours while delivering at least 95 % of the always-charge baseline.

## 4) Handy facts

- Search box: R_in 10-40 mm, fraction 2-40 %, single-layer or staggered; flow fixed.
- Years: explore 2016-2019, select 2020-2021, report 2022-2025, test 2006-2010.
- Thresholds: 45 C primary, 50 C secondary; shield bypass 72 C water / 62 C PCM; hard limits 75 C / 65 C.
- Search effort: DOE 128 points per (regime, PCM) pair, 9 pairs; 3-5 active-learning rounds per pair.
- Grid check: 240 designs per regime; search within 0 / 0.96 / 0 kWh of the grid best, inside the band.
- M1 MATLAB gate: PASS, 12 of 12 runs match Python (relative difference 1e-13), energy balance closed.
