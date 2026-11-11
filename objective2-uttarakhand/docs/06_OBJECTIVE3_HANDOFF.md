# 06 - Objective 3 hand-off (contract v2)

**File:** `results/obj3_environment_contract_uttarakhand_v2.json`, written by `src/handoff/build_obj3_contract_v2.py`
(`PYTHONPATH=. python -m src.handoff.build_obj3_contract_v2`, or `python pipeline.py --state uttarakhand --stage handoff`). It **supersedes**
the legacy K = 5 contract (UTC-indexed demand, single-node tank; removed in the cleanup, git history only), which must not be used for training.
The structure is Rajasthan's contract v2 (template `data/legacy/obj3_environment_contract_template_from_rajasthan.json`) with the Uttarakhand values.

**Hand-off design basis (checked 2026-11-10 against `configs/system_config_shared.yaml`):** tank 50 L (line 30), collector 1.5 m2 (line 24), delivery target 50 C (line 84), PCM limit 65 C (line 55). That is 33.3 L per m2, below the 40-100 L/m2 of IS 12976:2023. **K = 4 inheritance:** the four regimes come from O1 commit `6be0dcd`, which is not on O1 main (K = 5); the contract is not valid against O1 main's five-cluster outputs. The held-out years 2024-2025 were used once (run id `heldout_c75ac0e6fb78`) and are not available to O3.

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

## Check against the Objective 3 plan (consolidated 2026-11-10), done 2026-11-11

The O3 plan starts with Rajasthan and lists Uttarakhand as "later". What it needs from this folder, and its status:

| O3 plan item | Uttarakhand status |
|---|---|
| Hourly stepping of the unchanged kernel with carried state | Supported: `run_year_multinode(..., initial_state={"T_nodes", "h_nodes"})`; the end-of-hour node states are in `hourly.attrs["node_T"]`, `["node_h"]` (`src/simulation/tank_model_multinode.py`) |
| Same kernel and options as Rajasthan ("no conduction-coefficient option") | **Fixed 2026-11-11**: the conduction coefficient c, the named closure and the flow-dependent F_R option were ported (all off by default; results bit-identical; 95 tests pass). The kernel files now differ from Rajasthan's only in the state name |
| Contract hashes checked by the O3 environment | Contract regenerated 2026-11-11; only the `configs/system_config_shared.yaml` hash changed (the F_R block was added, disabled) |
| Years already used by O2 | 2024-2025 (lock `heldout_c75ac0e6fb78`); the docstring in `src/weather/roles.py` says so (fixed 2026-11-10). O3 must not use 2016-2025 as its own test; like Rajasthan it would need earlier years (2006-2010) for the four UK medoids, downloaded and quality-checked by O3 |
| Delivery temperature | 50 C, not 45 C: every O3 metric and reward term for Uttarakhand must use the contract's `delivery_temp_target_C` (columns named 45 are computed at 50 C) |
| Regime 3 ("degenerate") | `meaningful_on_primary_metric = false`; the contract design has 4 capsules (2 % PCM). Treat it as a water-only tank; a controller there has no PCM to manage |
| Action space | The contract's `control_skeleton` (charge / discharge / bypass + continuous flow) is the generic text inherited from the template. The O3 plan's correction applies here too: the only controllable input is collector loop on/off; flow should stay fixed unless the F_R(flow) option is switched on as a declared physics change |
| Q8: K = 4 vs K = 5 | Still open **in Objective 1**, not here: O1 `main` has `K_FINAL = 5` for Uttarakhand; the K = 4 switch (O1 commit `6be0dcd`) is only on the `tamilnadu-data` branch. O2 uses K = 4. The O1 team must merge it into O1 `main` |

