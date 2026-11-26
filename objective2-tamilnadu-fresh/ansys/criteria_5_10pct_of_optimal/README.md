# 5. 10 % of the optimal PCM

**Rule:** N = 10 % of 104 = 10 capsules (R_in, flow, arrangement kept optimal: 10 % of the radius or flow would fall below the design-space / pump bounds).

## Parameters

| parameter | this criteria | optimal |
|---|---|---|
| capsule inner radius | 40.0 mm | 40.0 mm |
| capsules (real, 3-D) | 10 (10 % of optimal) | 104 |
| PCM volume fraction | 2.8 % | 29.6 % |
| flow | 0.0388 kg/s | 0.0388 kg/s |
| arrangement | staggered | staggered |
| PCM | PureTemp 58 (Regime 0) | PureTemp 58 |
| **drawn in Fluent (2-D proxy)** | **3 capsules, inner R 20.0 mm** | 34, 20 mm |

## Result of the optimiser's own simulator (select years 2021-23, vs plain water tank)

| metric | this criteria | optimal | difference |
|---|---|---|---|
| PCM mass | 2.4 kg | 24.8 kg | -22.4 |
| **g_window** (extra evening heat) | **26.9 kWh/yr** | 276.6 | -249.7  (10 % of optimal) |
| g_annual | 27.7 kWh/yr | 283.1 | -255.4 |
| d_overheat (lower better) | 799 h/yr | 829 | -29 |
| peak PCM T | 62.37 C (limit 65) | | PASS |
| peak water T | 72.05 C (limit 75) | | PASS |

## How the final design is selected - and where this one stops

* Rule A (gain > 28.4 kWh noise band): **FAIL**
* S0 (within the band of the best g_window 297.1): **OUT**
* S1 (low overheating, only for S0 members): **n/a**
* **Verdict:** eliminated at Rule A (gain inside the noise band = no better than a plain tank)

**Why it is not optimal:** Only 2.4 kg of PCM: the latent store is almost negligible - the ~27 kWh/yr gain is below the 28.4 kWh repeatability band, i.e. not distinguishable from a plain tank.

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

water 30.00 -> 30.55 C; capsules 70.00 -> 52.49 C; liquid fraction 1.00 -> 0.21; heat given to the water 709 kJ per metre of depth.

![criteria_5_10pct_of_optimal_liqfrac_END.png](figures/criteria_5_10pct_of_optimal_liqfrac_END.png)
![criteria_5_10pct_of_optimal_liqfrac_MID.png](figures/criteria_5_10pct_of_optimal_liqfrac_MID.png)
![criteria_5_10pct_of_optimal_liqfrac_START.png](figures/criteria_5_10pct_of_optimal_liqfrac_START.png)
![criteria_5_10pct_of_optimal_temp_END.png](figures/criteria_5_10pct_of_optimal_temp_END.png)
![criteria_5_10pct_of_optimal_temp_MID.png](figures/criteria_5_10pct_of_optimal_temp_MID.png)
![criteria_5_10pct_of_optimal_temp_START.png](figures/criteria_5_10pct_of_optimal_temp_START.png)