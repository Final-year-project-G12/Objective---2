# 06 - Objective 3 hand-off (contract v2)

**File:** `results/obj3_environment_contract_uttarakhand_v2.json`, written by `src/handoff/build_obj3_contract_v2.py`
(`PYTHONPATH=. python -m src.handoff.build_obj3_contract_v2`, or `python pipeline.py --state uttarakhand --stage handoff`). It **supersedes**
the legacy K = 5 contract (UTC-indexed demand, single-node tank; removed in the cleanup, git history only), which must not be used for training.
The structure is Rajasthan's contract v2 (template `data/legacy/obj3_environment_contract_template_from_rajasthan.json`) with the Uttarakhand values.

## What is in the contract

| Item | Uttarakhand v2 |
|---|---|
| Simulator | multi-node tank N = 10, dt 150 s, local-time demand, inner-volume PCM mass with wall mass, O1 top-3 PCMs |
| State vector | Rajasthan v2's, including `T_water_top_C`, `T_water_bottom_C`, `recoverable_energy_above_45C_kWh` (here computed above the **50 C** target; the field keeps its cross-state name) and `minutes_since_last_draw` |
| Actions | charge / discharge / bypass plus a continuous flow within 0.010-0.050 kg/s |
| Limits | delivery target 50 C, water 75 C, PCM 65 C; shield bypass at top node 72 C and PCM 62 C |
| Weather | training 2016-2020, validation 2021-2023, held-out 2024-2025 (**used once by O2; O3 must not tune on them**), points UKP_0014 / UKP_0029 / UKP_0025 / UKP_0041 |
| Regimes | 4: per regime the chosen design, the best design of each other O1 PCM, their select-year and held-out results, the WP6 bands |
| Reward | a suggestion built from the WP1 metrics; **weights are not chosen** |
| Provenance | SHA-256 of the four selection logs, the band file, the held-out results and the config files |

## What O3 has to know about the O2 results

- Regimes 0-2: the passive PCM design gains 63-80 kWh/yr on the select years and 56-76 kWh/yr on the 2024-2025 test years in the 18:00-09:00 window,
  against the same-flow water-only tank (bands about 20 kWh). The level depends on the capsule-stack position by 35-54 kWh (`05_LIMITATIONS_AND_OPEN_ITEMS.md`).
- **Regime 3: PCM gives no gain** (about -6 kWh/yr, select and test). Its contract entry holds the least-PCM design the selection rule picked, with
  `selection.meaningful_on_primary_metric = false` (not better than water-only); O3 should treat regime 3 as a water-only tank, or as a case where a controller has nothing passive to build on.
- The case for a controller is hour-by-hour operation: the PCM-side throttle (about 90-820 h/yr over the kept designs) and the evening serve time,
  which the passive design does not extend against the same 50 L tank.
- Compare any controller against the same-flow water-only twin and the passive PCM design, on the explore and select years only.
- The demand file `data/demand/demand_profile_uttarakhand.csv` must be read as local time (morning peak 07:30). Pump energy is not meaningful in the O2 simulator.
