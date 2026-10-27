# Fix — O1<->O2 delivery-temperature reconciliation, supplementary check (Rajasthan)

Objective 1's `T_DELIVERY_C` is **60 C** (corrected 2026-09-13, Avargani et al. 2021-anchored, CLAUDE.md §3.2). Objective 2's frozen `system_config_shared.yaml` `delivery.target_temp_C` is **45 C**, chosen before O1's correction — documented as an unresolved divergence in `docs/09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md` §1. This supplementary check quantifies the effect of scoring the SAME Phase-7-confirmed designs against O1's 60 C target instead of the frozen 45 C target, using each (regime, pcm) case's own Phase 7 simulator-confirmed geometry (not re-searched — a fresh optimization at 60 C would require a full DOE/surrogate/optimizer re-run, out of scope for a supplementary check per this project's own precedent). `system_config_shared.yaml` itself is untouched (frozen, identical across all 4 states) — the 60 C config exists only as an in-memory `system_config_overrides` dict to `run_case()`. Gate 4 benchmark band: 54-84% (Singh et al. 2025, cited).


## Regime 0

| config_label | delivery_target_temp_C | pcm_id | capsule_diameter_m | n_capsule | flow_rate_kg_s | valid | solar_fraction_pct | in_gate4_band | useful_energy_kWh | unmet_energy_kWh | delivery_temp_hours | max_water_temp_C | max_pcm_temp_C | n_safety_violations | meets_temperature_safety |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| frozen_45C | 45 | NONE_plain_tank | 0.04091 | 11 | 0.02671 | True | 54.97 | True | 1586 | 1142 | 2910 | 68.59 | 68.59 | 0 | True |
| frozen_45C | 45 | Lauric acid (C12) | 0.04411 | 37 | 0.02328 | True | 55.28 | True | 1588 | 1133 | 2855 | 68.87 | 62.12 | 0 | True |
| frozen_45C | 45 | RT45HC | 0.04303 | 34 | 0.02696 | True | 55.34 | True | 1588 | 1132 | 2853 | 68.83 | 62.1 | 0 | True |
| frozen_45C | 45 | RT50 | 0.04091 | 11 | 0.02671 | True | 54.99 | True | 1587 | 1141 | 2913 | 68.7 | 62.1 | 0 | True |
| o1_reconciled_60C | 60 | NONE_plain_tank | 0.04091 | 11 | 0.02671 | True | 35.65 | False | 1586 | 2860 | 430 | 68.59 | 68.59 | 0 | True |
| o1_reconciled_60C | 60 | Lauric acid (C12) | 0.04411 | 37 | 0.02328 | True | 35.69 | False | 1588 | 2858 | 427 | 68.87 | 62.12 | 0 | True |
| o1_reconciled_60C | 60 | RT45HC | 0.04303 | 34 | 0.02696 | True | 35.71 | False | 1588 | 2858 | 425 | 68.83 | 62.1 | 0 | True |
| o1_reconciled_60C | 60 | RT50 | 0.04091 | 11 | 0.02671 | True | 35.67 | False | 1587 | 2859 | 435 | 68.7 | 62.1 | 0 | True |

## Regime 1

| config_label | delivery_target_temp_C | pcm_id | capsule_diameter_m | n_capsule | flow_rate_kg_s | valid | solar_fraction_pct | in_gate4_band | useful_energy_kWh | unmet_energy_kWh | delivery_temp_hours | max_water_temp_C | max_pcm_temp_C | n_safety_violations | meets_temperature_safety |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| frozen_45C | 45 | NONE_plain_tank | 0.04125 | 8 | 0.03595 | True | 58.23 | True | 1673 | 1022 | 3447 | 72.03 | 72.03 | 0 | True |
| frozen_45C | 45 | Paraffin/HDPE PCM3 | 0.04092 | 23 | 0.03907 | True | 58.32 | True | 1675 | 1020 | 3459 | 72.05 | 62.16 | 0 | True |
| frozen_45C | 45 | Paraffin/HDPE PCM6 | 0.04014 | 25 | 0.04011 | True | 58.32 | True | 1675 | 1020 | 3459 | 72.07 | 62.13 | 0 | True |
| frozen_45C | 45 | savE® OM50 | 0.04035 | 17 | 0.0262 | True | 58.33 | True | 1675 | 1020 | 3455 | 72.01 | 62.16 | 0 | True |
| o1_reconciled_60C | 60 | NONE_plain_tank | 0.04125 | 8 | 0.03595 | True | 38.32 | False | 1673 | 2687 | 610 | 72.03 | 72.03 | 0 | True |
| o1_reconciled_60C | 60 | Paraffin/HDPE PCM3 | 0.04092 | 23 | 0.03907 | True | 38.36 | False | 1675 | 2686 | 599 | 72.05 | 62.16 | 0 | True |
| o1_reconciled_60C | 60 | Paraffin/HDPE PCM6 | 0.04014 | 25 | 0.04011 | True | 38.35 | False | 1675 | 2686 | 597 | 72.07 | 62.13 | 0 | True |
| o1_reconciled_60C | 60 | savE® OM50 | 0.04035 | 17 | 0.0262 | True | 38.36 | False | 1675 | 2685 | 604 | 72.01 | 62.16 | 0 | True |

## Regime 2

| config_label | delivery_target_temp_C | pcm_id | capsule_diameter_m | n_capsule | flow_rate_kg_s | valid | solar_fraction_pct | in_gate4_band | useful_energy_kWh | unmet_energy_kWh | delivery_temp_hours | max_water_temp_C | max_pcm_temp_C | n_safety_violations | meets_temperature_safety |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| frozen_45C | 45 | NONE_plain_tank | 0.04253 | 31 | 0.02439 | True | 53.88 | False | 1592 | 1202 | 2752 | 68.72 | 68.72 | 0 | True |
| frozen_45C | 45 | Paraffin/HDPE PCM3 | 0.04217 | 30 | 0.03077 | True | 53.96 | False | 1593 | 1200 | 2773 | 68.93 | 62.16 | 0 | True |
| frozen_45C | 45 | Paraffin/HDPE PCM6 | 0.04034 | 29 | 0.04156 | True | 53.94 | False | 1593 | 1201 | 2772 | 68.92 | 62.1 | 0 | True |
| frozen_45C | 45 | savE® OM50 | 0.04043 | 33 | 0.02775 | True | 54.02 | True | 1594 | 1199 | 2767 | 68.91 | 62.12 | 0 | True |
| o1_reconciled_60C | 60 | NONE_plain_tank | 0.04253 | 31 | 0.02439 | True | 35.22 | False | 1592 | 2926 | 320 | 68.72 | 68.72 | 0 | True |
| o1_reconciled_60C | 60 | Paraffin/HDPE PCM3 | 0.04217 | 30 | 0.03077 | True | 35.24 | False | 1593 | 2925 | 312 | 68.93 | 62.16 | 0 | True |
| o1_reconciled_60C | 60 | Paraffin/HDPE PCM6 | 0.04034 | 29 | 0.04156 | True | 35.24 | False | 1593 | 2925 | 313 | 68.92 | 62.1 | 0 | True |
| o1_reconciled_60C | 60 | savE® OM50 | 0.04043 | 33 | 0.02775 | True | 35.26 | False | 1594 | 2924 | 310 | 68.91 | 62.12 | 0 | True |
