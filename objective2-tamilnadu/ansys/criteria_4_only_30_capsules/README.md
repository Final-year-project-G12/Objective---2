# 4. YOUR WISH: only 30 capsules

**Rule:** Only 30 real capsules (R_in 40 mm, optimal flow, staggered) = 8.5 % PCM fraction.

## Parameters

| parameter | this criteria | optimal |
|---|---|---|
| capsule inner radius | 40.0 mm | 40.0 mm |
| capsules (real, 3-D) | 30 (29 % of optimal) | 104 |
| PCM volume fraction | 8.5 % | 29.6 % |
| flow | 0.0388 kg/s | 0.0388 kg/s |
| arrangement | staggered | staggered |
| PCM | PureTemp 58 (Regime 0) | PureTemp 58 |
| **drawn in Fluent (2-D proxy)** | **10 capsules, inner R 20.0 mm** | 34, 20 mm |

## Result of the optimiser's own simulator (select years 2021-23, vs plain water tank)

| metric | this criteria | optimal | difference |
|---|---|---|---|
| PCM mass | 7.2 kg | 24.8 kg | -17.7 |
| **g_window** (extra evening heat) | **83.6 kWh/yr** | 276.6 | -193.0  (30 % of optimal) |
| g_annual | 85.7 kWh/yr | 283.1 | -197.4 |
| d_overheat (lower better) | 730 h/yr | 829 | -98 |
| peak PCM T | 62.35 C (limit 65) | | PASS |
| peak water T | 72.05 C (limit 75) | | PASS |

## How the final design is selected - and where this one stops

* Rule A (gain > 28.4 kWh noise band): **pass**
* S0 (within the band of the best g_window 297.1): **OUT**
* S1 (low overheating, only for S0 members): **n/a**
* **Verdict:** works and beats plain water, but eliminated at S0 (too far below the best g_window)

**Why it is not optimal:** Under a third of the optimal PCM mass (7.2 kg vs 24.8 kg): the store is used up quickly in the evening, so only ~30 % of the optimal benefit is delivered.

## Files

| file | what |
|---|---|
| `criteria.json` | design, 2-D proxy, run settings |
| `fluent_tank_discharge_criteria.py` | copy of `../fluent_tank_discharge.py` driven by this criteria (builds its own mesh, runs Fluent, prints the time table, saves pictures) |
| `make_system_mesh.py` | mesh builder with an exact `n_capsules` argument |
| `run_node_model.py`, `scenarios.py` | the objective-value side (gates, funnel verdict, one-day time behaviour) |
| `node_model_terminal.txt`, `node_model_results.json`, `node_model_day.csv/.png` | its output |
| `fluent_terminal.log`, `*_discharge_timeseries.csv`, `figures/*.png` | Fluent output (after `python fluent_tank_discharge_criteria.py`) |

## Fluent whole-tank discharge (this run)

water 30.00 -> 31.63 C; capsules 70.00 -> 55.05 C; liquid fraction 1.00 -> 0.32; heat given to the water 2050 kJ per metre of depth.

![criteria_4_only_30_capsules_liqfrac_END.png](figures/criteria_4_only_30_capsules_liqfrac_END.png)
![criteria_4_only_30_capsules_liqfrac_MID.png](figures/criteria_4_only_30_capsules_liqfrac_MID.png)
![criteria_4_only_30_capsules_liqfrac_START.png](figures/criteria_4_only_30_capsules_liqfrac_START.png)
![criteria_4_only_30_capsules_temp_END.png](figures/criteria_4_only_30_capsules_temp_END.png)
![criteria_4_only_30_capsules_temp_MID.png](figures/criteria_4_only_30_capsules_temp_MID.png)
![criteria_4_only_30_capsules_temp_START.png](figures/criteria_4_only_30_capsules_temp_START.png)