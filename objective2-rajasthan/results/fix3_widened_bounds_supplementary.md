# Fix 3 — Widened-bounds supplementary check (Rajasthan)

One supplementary case per regime (not a full Phase 5-7 DOE/surrogate/optimizer re-run), comparing the frozen design_bounds_shared.yaml ceiling against a widened envelope (capsule_diameter_m max 0.12 m, capsule_count max 40) built purely as an in-memory `design_bounds` override to `run_case()` — design_bounds_shared.yaml itself is untouched (frozen, identical across all 4 states).


## Cluster 0

| cluster_id | pcm_name | bounds | valid | capsule_diameter_m | n_capsule | pcm_volume_fraction | reaches_15pct_chen_comparable | solar_fraction | useful_energy_kWh | max_water_temp_C | max_pcm_temp_C | n_safety_violations |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | savE® OM55 | frozen_bounds | True | 0.08 | 24 | 0.1286796350910379 | False | 0.546823822124037 | 1577.826283696574 | 66.04846780989463 | 65.19114434808272 | 14 |
| 0 | savE® OM55 | widened_bounds | True | 0.12 | 10 | 0.18095573684677202 | True | 0.5398858564000562 | 1566.6543425630575 | 68.42791359194246 | 57.40200542013656 | 0 |


## Cluster 1

| cluster_id | pcm_name | bounds | valid | capsule_diameter_m | n_capsule | pcm_volume_fraction | reaches_15pct_chen_comparable | solar_fraction | useful_energy_kWh | max_water_temp_C | max_pcm_temp_C | n_safety_violations |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | PureTemp 60 | frozen_bounds | True | 0.08 | 24 | 0.1286796350910379 | False | 0.5756103632952418 | 1664.371204103118 | 71.160486392701 | 66.48426231360041 | 46 |
| 1 | PureTemp 60 | widened_bounds | True | 0.12 | 10 | 0.18095573684677202 | True | 0.5709486269753301 | 1656.8035754416633 | 72.50399313402575 | 61.472096904250286 | 0 |


## Cluster 2

| cluster_id | pcm_name | bounds | valid | capsule_diameter_m | n_capsule | pcm_volume_fraction | reaches_15pct_chen_comparable | solar_fraction | useful_energy_kWh | max_water_temp_C | max_pcm_temp_C | n_safety_violations |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2 | n-Heptacosane (C27) | frozen_bounds | True | 0.08 | 24 | 0.1286796350910379 | False | 0.5314991333363543 | 1582.8148621650503 | 67.60730041757797 | 64.25669511096712 | 0 |
| 2 | n-Heptacosane (C27) | widened_bounds | True | 0.12 | 10 | 0.18095573684677202 | True | 0.5275458661970647 | 1576.4937959696435 | 68.87002911037713 | 59.71813652007404 | 0 |

