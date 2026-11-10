# B5 port to Assam: local-time demand and optional shield (2026-11-10)

Scope: the two fixes from `objective2-rajasthan` named in WP7 of the O2 redesign plan, applied to `src/simulation/tank_model.py` and `src/simulation/run_case.py` of this folder. Nothing else was ported and no Assam phase result was re-run.

## What changed
- `_demand_hour_of_day(row, i)` (copied from Rajasthan) indexes the demand profile by the weather file's `local_hour` column. A frame with `timestamp_utc` and no `local_hour` raises `ValueError`; a frame with neither keeps the row-index fallback. Before, line 148 used `row["timestamp_utc"].hour`, so the 07:00 / 19:00 demand peaks fell at the wrong local time (Assam is UTC+5:30).
- Safety shield (water-side pump stop, PCM-side charge-only block) added behind `system_config["safety_shield"]["enabled"]`. **Default off**: Assam's `configs/system_config_shared.yaml` has no such block (Rajasthan's has `enabled: true`), and that file was not edited, so the shield is switched on only through `system_config_overrides`. Thresholds default to the safety maxima minus 3.0 C. `run_case` metrics gain `n_shield_water_activations` and `n_shield_pcm_activations`.
- `tests/test_local_hour_port.py`, 2 tests, pass.

## Effect on one Assam case (`results/b5_local_hour_check.csv`)
Cluster 0, savE OM48, d 0.05 m, N 14, flow 0.030 kg/s (the case of `scripts/test_single_case_assam.py`):

| run | useful energy (kWh) | solar fraction | max water T (C) | max PCM T (C) | substeps over the safety limit |
|---|---|---|---|---|---|
| before (UTC demand index) | 681.6 | 0.624 | 66.5 | 66.0 | 5 |
| after (local-hour demand) | 636.9 | 0.559 | 79.2 | 79.2 | 6182 |
| after, shield on | 634.3 | 0.558 | 72.4 | 63.4 | 0 |

Energy residual 0 % in all three.

## What this means
- **Every earlier Assam result was produced with the UTC demand index** (Phases 3 to 10, including the Phase 7 selection and the recommendation cards). For this case the corrected demand timing lowers delivered energy by about 6.6 % and pushes the tank above the 75 C water limit in thousands of substeps, which the old timing hid. These results are not re-run here and should not be quoted as local-time results.
- Assam has no shield in its current runs, so with correct timing an unshielded design can overheat. Enabling the shield removes the violations in this case at a cost of 2.6 kWh.
- Not ported (not done): the multi-node tank, TES metrics, weather-year roles, the design-space box and the optimisation chain of the Rajasthan rework. Assam remains on the phase-based pipeline.

## Checks run
`scripts/test_single_case_assam.py` passes. `scripts/final_phase0_regression_check.py`: all 10 checks passed. `scripts/phase0_smoke_test_assam.py` fails at `surrogate_features` because `configs/states/rajasthan.yaml` is not in this folder (not touched by this change); it also needs `PYTHONIOENCODING=utf-8` on a Windows console.
