# Fix — Standards-compliant collector:tank sizing, supplementary check (Rajasthan)

The frozen `system_config_shared.yaml` (`tank.volume_L=50`, `collector.area_m2=1.5` -> storage/collector ratio = **33.3 L/m2**) is verified NON-COMPLIANT with IS 12976:2023 Sec 4.2/7.1 (40-100 L/m2 general range; 75 L/m2 reference ratio; 37.5 L/m2 floor below which the standard's own f-chart correction is undefined) -- quotes checked directly against `PCM-Selection-ML-model/Sources/pdfs/IS12976_2023.pdf` this session, not taken from a paraphrase. Two resize directions tested, both anchored to the standard's 75 L/m2 reference ratio, using each (regime, pcm) case's own Phase 7 simulator-confirmed geometry (not re-searched -- this checks whether resizing changes the safety outcome for designs Phase 7 already found, not a fresh optimization at the new sizing). `system_config_shared.yaml` itself is untouched (frozen, identical across all 4 states) -- both resized configs exist only as in-memory `system_config_overrides` to `run_case()`.


## Regime 0

| config_label | collector_area_m2 | tank_volume_L | storage_collector_ratio_Lm2 | pcm_id | capsule_diameter_m | n_capsule | flow_rate_kg_s | valid | solar_fraction_pct | useful_energy_kWh | max_water_temp_C | max_pcm_temp_C | n_safety_violations | meets_temperature_safety |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| frozen_33.3_Lm2 | 1.5 | 50 | 33.33 | NONE_plain_tank | 0.04094 | 9 | 0.01588 | True | 54.97 | 1586 | 68.59 | 68.59 | 0 | True |
| frozen_33.3_Lm2 | 1.5 | 50 | 33.33 | Myristic acid/NBR-0.5 | 0.0401 | 9 | 0.0315 | True | 54.96 | 1587 | 68.66 | 68.61 | 2265 | False |
| frozen_33.3_Lm2 | 1.5 | 50 | 33.33 | Palmitic-stearic acid/Expanded graphite | 0.0407 | 10 | 0.03575 | True | 54.96 | 1587 | 68.66 | 68.6 | 2208 | False |
| frozen_33.3_Lm2 | 1.5 | 50 | 33.33 | savE® OM55 | 0.04006 | 12 | 0.02679 | True | 54.97 | 1587 | 68.64 | 68.58 | 1437 | False |
| caseA_tank_resize_75.0_Lm2 | 1.5 | 112.5 | 75 | NONE_plain_tank | 0.04094 | 9 | 0.01588 | True | 60.65 | 1615 | 60.35 | 60.35 | 0 | True |
| caseA_tank_resize_75.0_Lm2 | 1.5 | 112.5 | 75 | Myristic acid/NBR-0.5 | 0.0401 | 9 | 0.0315 | True | 60.67 | 1616 | 60.33 | 60.3 | 0 | True |
| caseA_tank_resize_75.0_Lm2 | 1.5 | 112.5 | 75 | Palmitic-stearic acid/Expanded graphite | 0.0407 | 10 | 0.03575 | True | 60.67 | 1616 | 60.3 | 60.23 | 0 | True |
| caseA_tank_resize_75.0_Lm2 | 1.5 | 112.5 | 75 | savE® OM55 | 0.04006 | 12 | 0.02679 | True | 60.63 | 1615 | 60.3 | 60.08 | 0 | True |
| caseB_collector_resize_75.0_Lm2 | 0.6667 | 50 | 75 | NONE_plain_tank | 0.04094 | 9 | 0.01588 | True | 31.55 | 800.1 | 48.67 | 48.67 | 0 | True |
| caseB_collector_resize_75.0_Lm2 | 0.6667 | 50 | 75 | Myristic acid/NBR-0.5 | 0.0401 | 9 | 0.0315 | True | 31.56 | 800.3 | 48.71 | 48.68 | 0 | True |
| caseB_collector_resize_75.0_Lm2 | 0.6667 | 50 | 75 | Palmitic-stearic acid/Expanded graphite | 0.0407 | 10 | 0.03575 | True | 31.56 | 800.3 | 48.71 | 49.2 | 0 | True |
| caseB_collector_resize_75.0_Lm2 | 0.6667 | 50 | 75 | savE® OM55 | 0.04006 | 12 | 0.02679 | True | 31.56 | 800.3 | 48.71 | 49 | 0 | True |

## Regime 1

| config_label | collector_area_m2 | tank_volume_L | storage_collector_ratio_Lm2 | pcm_id | capsule_diameter_m | n_capsule | flow_rate_kg_s | valid | solar_fraction_pct | useful_energy_kWh | max_water_temp_C | max_pcm_temp_C | n_safety_violations | meets_temperature_safety |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| frozen_33.3_Lm2 | 1.5 | 50 | 33.33 | NONE_plain_tank | 0.04004 | 8 | 0.01828 | True | 58.23 | 1673 | 72.38 | 72.38 | 0 | True |
| frozen_33.3_Lm2 | 1.5 | 50 | 33.33 | CrodaTherm 60 | 0.04124 | 13 | 0.01662 | True | 58.16 | 1674 | 72.23 | 72.21 | 10800 | False |
| frozen_33.3_Lm2 | 1.5 | 50 | 33.33 | PureTemp 60 | 0.04154 | 9 | 0.03776 | True | 58.19 | 1674 | 72.24 | 72.22 | 7935 | False |
| frozen_33.3_Lm2 | 1.5 | 50 | 33.33 | n-Heptacosane (C27) | 0.04004 | 13 | 0.01829 | True | 58.18 | 1675 | 72.34 | 72.33 | 9631 | False |
| caseA_tank_resize_75.0_Lm2 | 1.5 | 112.5 | 75 | NONE_plain_tank | 0.04004 | 8 | 0.01828 | True | 65.28 | 1707 | 63.17 | 63.17 | 0 | True |
| caseA_tank_resize_75.0_Lm2 | 1.5 | 112.5 | 75 | CrodaTherm 60 | 0.04124 | 13 | 0.01662 | True | 65.3 | 1708 | 63.11 | 62.79 | 0 | True |
| caseA_tank_resize_75.0_Lm2 | 1.5 | 112.5 | 75 | PureTemp 60 | 0.04154 | 9 | 0.03776 | True | 65.3 | 1708 | 63.16 | 61.79 | 0 | True |
| caseA_tank_resize_75.0_Lm2 | 1.5 | 112.5 | 75 | n-Heptacosane (C27) | 0.04004 | 13 | 0.01829 | True | 65.3 | 1708 | 63.07 | 63.03 | 0 | True |
| caseB_collector_resize_75.0_Lm2 | 0.6667 | 50 | 75 | NONE_plain_tank | 0.04004 | 8 | 0.01828 | True | 34.52 | 845.9 | 51.67 | 51.67 | 0 | True |
| caseB_collector_resize_75.0_Lm2 | 0.6667 | 50 | 75 | CrodaTherm 60 | 0.04124 | 13 | 0.01662 | True | 34.53 | 846.1 | 51.75 | 53.8 | 0 | True |
| caseB_collector_resize_75.0_Lm2 | 0.6667 | 50 | 75 | PureTemp 60 | 0.04154 | 9 | 0.03776 | True | 34.53 | 846.1 | 51.72 | 55 | 0 | True |
| caseB_collector_resize_75.0_Lm2 | 0.6667 | 50 | 75 | n-Heptacosane (C27) | 0.04004 | 13 | 0.01829 | True | 34.53 | 846.2 | 51.74 | 53 | 0 | True |

## Regime 2

| config_label | collector_area_m2 | tank_volume_L | storage_collector_ratio_Lm2 | pcm_id | capsule_diameter_m | n_capsule | flow_rate_kg_s | valid | solar_fraction_pct | useful_energy_kWh | max_water_temp_C | max_pcm_temp_C | n_safety_violations | meets_temperature_safety |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| frozen_33.3_Lm2 | 1.5 | 50 | 33.33 | NONE_plain_tank | 0.04276 | 10 | 0.01255 | True | 53.88 | 1592 | 68.72 | 68.72 | 0 | True |
| frozen_33.3_Lm2 | 1.5 | 50 | 33.33 | PlusICE A58 | 0.04113 | 8 | 0.01839 | True | 53.86 | 1593 | 68.62 | 68.59 | 1223 | False |
| frozen_33.3_Lm2 | 1.5 | 50 | 33.33 | PureTemp 58 | 0.04001 | 11 | 0.02589 | True | 53.86 | 1593 | 68.56 | 68.53 | 1184 | False |
| frozen_33.3_Lm2 | 1.5 | 50 | 33.33 | n-Heptacosane (C27) | 0.04058 | 8 | 0.01119 | True | 53.86 | 1593 | 68.63 | 68.6 | 1539 | False |
| caseA_tank_resize_75.0_Lm2 | 1.5 | 112.5 | 75 | NONE_plain_tank | 0.04276 | 10 | 0.01255 | True | 59.65 | 1625 | 60.44 | 60.44 | 0 | True |
| caseA_tank_resize_75.0_Lm2 | 1.5 | 112.5 | 75 | PlusICE A58 | 0.04113 | 8 | 0.01839 | True | 59.68 | 1626 | 60.42 | 59.9 | 0 | True |
| caseA_tank_resize_75.0_Lm2 | 1.5 | 112.5 | 75 | PureTemp 58 | 0.04001 | 11 | 0.02589 | True | 59.68 | 1626 | 60.41 | 59.88 | 0 | True |
| caseA_tank_resize_75.0_Lm2 | 1.5 | 112.5 | 75 | n-Heptacosane (C27) | 0.04058 | 8 | 0.01119 | True | 59.68 | 1626 | 60.44 | 59.43 | 0 | True |
| caseB_collector_resize_75.0_Lm2 | 0.6667 | 50 | 75 | NONE_plain_tank | 0.04276 | 10 | 0.01255 | True | 30.92 | 806.3 | 49.14 | 49.14 | 0 | True |
| caseB_collector_resize_75.0_Lm2 | 0.6667 | 50 | 75 | PlusICE A58 | 0.04113 | 8 | 0.01839 | True | 30.93 | 806.5 | 49.18 | 52 | 0 | True |
| caseB_collector_resize_75.0_Lm2 | 0.6667 | 50 | 75 | PureTemp 58 | 0.04001 | 11 | 0.02589 | True | 30.92 | 806.5 | 49.18 | 52 | 0 | True |
| caseB_collector_resize_75.0_Lm2 | 0.6667 | 50 | 75 | n-Heptacosane (C27) | 0.04058 | 8 | 0.01119 | True | 30.93 | 806.6 | 49.19 | 53 | 0 | True |
