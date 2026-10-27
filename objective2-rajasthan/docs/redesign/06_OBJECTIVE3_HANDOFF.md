# 06 - Objective 3 hand-off (contract v2)

**File:** `results/redesign/obj3_environment_contract_rajasthan_v2.json`, written by `src/handoff/build_obj3_contract_v2.py`
(`PYTHONPATH=. python -m src.handoff.build_obj3_contract_v2`). It **supersedes** `results/obj3_environment_contract_rajasthan.json`, which was
built from the pre-redesign deployables (UTC-indexed demand, single-node tank, retargeted PCMs) and must not be used for training.
The older `docs/OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` describes that old contract and carries a banner.

## What changed in the contract

| Item | v2 |
|---|---|
| Simulator | multi-node tank N = 10, dt 150 s, local-time demand, inner-volume PCM mass with wall mass, O1 top-3 PCMs |
| State vector | adds `T_water_top_C`, `T_water_bottom_C`, `recoverable_energy_above_45C_kWh` (an estimator, not a sensor) and `minutes_since_last_draw`; delivery temperature is the TOP node, the collector inlet is the BOTTOM node |
| Actions | unchanged: charge / discharge / bypass plus a continuous flow within 0.010-0.050 kg/s |
| Safety shield | force bypass at top node 72 C (guard band below 75 C) and PCM 62 C; flow clamped to the envelope. A design is infeasible if its PCM peak exceeds 65 C in any simulated year. |
| Weather sequences | training 2016-2020, validation 2021-2023, held-out 2024-2025 (**O2 has used the held-out years once; O3 must not tune on them**) at points RJP_0132 / RJP_0192 / RJP_0083 |
| Regimes | for each regime: the chosen design, the best design of each other O1 PCM, their select-year results, the held-out results (every row), and the WP6 bands |
| Reward | a suggestion built from the WP1 metrics (delivered energy at 45 C, overheating hours, safety violation, bypass switching). **Weights are not chosen.** The pump-energy term and the old normalisation constants were removed. |
| Provenance | `generated_from` holds SHA-256 of the three selection logs, the band file and the held-out results; `config_hashes` holds SHA-256 of the five config files |
| Deferred | collector F_R(flow) correction, unapplied CFD closure, node-count uncertainty, O1 conductivity discrepancy |

## What O3 has to know about the O2 results

- The physical case for a controller is not "the best PCM changes with the weather" (O1's selection is stable per region; the seasonal
  re-ranking in the earlier work was a null). It is hour-by-hour operation: the PCM tank has fewer water-side shield hours than the
  water-only tank but a PCM-side throttle of about 420-1,140 h/yr (means over years, all kept designs) (section 1b of `04_RESULTS.md`), and it does not extend the volume or time at 45 C in the evening against the same tank (it does raise the evening energy delivered up to 45 C, section 5d of `04_RESULTS.md`). A controller could address the PCM-side throttle and the evening volume and time at 45 C.
- The gain from the passive design is 94-99 kWh per year of delivered energy in the 18:00-09:00 window and depends on the capsule-stack
  position assumption by more than the band (`05_LIMITATIONS_AND_OPEN_ITEMS.md`). A controller must be compared with the same-flow
  water-only twin and the passive PCM design, on the explore and select years only.
- `reset_scenarios`, `acceptance_test_before_drl_training` and the demand file are carried over unchanged from the earlier contract
  (`data/demand/demand_profile_rajasthan.csv`); the demand must be read as local time.
- Pump energy is not a meaningful quantity in the O2 simulator.
