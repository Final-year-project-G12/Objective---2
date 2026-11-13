# 3. NOT optimal, but working

**Rule:** A real evaluated candidate from the optimiser's own list (results/g10_selection_candidates_r0.csv): N = 80 capsules, flow 0.0227.  Passes every hard gate and beats the plain tank clearly.

## Parameters

| parameter | this criteria | optimal |
|---|---|---|
| capsule inner radius | 40.0 mm | 40.0 mm |
| capsules (real, 3-D) | 80 (77 % of optimal) | 104 |
| PCM volume fraction | 22.8 % | 29.6 % |
| flow | 0.0227 kg/s | 0.0388 kg/s |
| arrangement | staggered | staggered |
| PCM | PureTemp 58 (Regime 0) | PureTemp 58 |
| **drawn in Fluent (2-D proxy)** | **26 capsules, inner R 20.0 mm** | 34, 20 mm |

## Result of the optimiser's own simulator (select years 2021-23, vs plain water tank)

| metric | this criteria | optimal | difference |
|---|---|---|---|
| PCM mass | 19.1 kg | 24.8 kg | -5.7 |
| **g_window** (extra evening heat) | **187.5 kWh/yr** | 276.6 | -89.2  (68 % of optimal) |
| g_annual | 190.6 kWh/yr | 283.1 | -92.4 |
| d_overheat (lower better) | 360 h/yr | 829 | -469 |
| peak PCM T | 62.13 C (limit 65) | | PASS |
| peak water T | 72.05 C (limit 75) | | PASS |

## How the final design is selected - and where this one stops

* Rule A (gain > 28.4 kWh noise band): **pass**
* S0 (within the band of the best g_window 297.1): **OUT**
* S1 (low overheating, only for S0 members): **n/a**
* **Verdict:** works and beats plain water, but eliminated at S0 (too far below the best g_window)

**Why it is not optimal:** Falls outside S0 (not within the tie-band of the best g_window): ~23 % less PCM and a slower flow (0.0227 vs 0.0388), so it delivers ~32 % less extra evening heat. Trade-off: far less overheating (shield-hours) - so it is a genuinely working, cheaper design.

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

water 30.00 -> 34.10 C; capsules 70.00 -> 56.17 C; liquid fraction 1.00 -> 0.38; heat given to the water 4785 kJ per metre of depth.

![criteria_3_ok_not_optimal_liqfrac_END.png](figures/criteria_3_ok_not_optimal_liqfrac_END.png)
![criteria_3_ok_not_optimal_liqfrac_MID.png](figures/criteria_3_ok_not_optimal_liqfrac_MID.png)
![criteria_3_ok_not_optimal_liqfrac_START.png](figures/criteria_3_ok_not_optimal_liqfrac_START.png)
![criteria_3_ok_not_optimal_temp_END.png](figures/criteria_3_ok_not_optimal_temp_END.png)
![criteria_3_ok_not_optimal_temp_MID.png](figures/criteria_3_ok_not_optimal_temp_MID.png)
![criteria_3_ok_not_optimal_temp_START.png](figures/criteria_3_ok_not_optimal_temp_START.png)