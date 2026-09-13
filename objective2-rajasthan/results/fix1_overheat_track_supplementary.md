# Fix 1 — Overheat-protection PCM track, supplementary check (Rajasthan)

0/6 (regime x candidate) combinations clear the 65 C PCM safety limit, vs. 0/45 for the original climate-only shortlist (Phase 7, pre-refresh) and the refreshed 55-61 C O1 shortlist (see phase7_deployable_design_per_regime.csv — plain tank selected in all 3 regimes post-refresh too).

Nominal geometry used (NOT re-optimized for these candidates — this is a feasibility check, not a design search): capsule_diameter_m=0.06, n_capsule=16, flow_rate_kg_s=0.03.

| cluster_id | pcm_name | Tm_C | valid | Tm_target_C_this_regime | solar_fraction | useful_energy_kWh | max_water_temp_C | max_pcm_temp_C | clears_65C_pcm_safety_limit | clears_75C_water_safety_limit | n_safety_violations | final_f_melt |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | RT80HC | 78.0 | True | 67.0 | 0.5474134327968017 | 1583.1502153421966 | 68.78594358652997 | 72.0 | False | True | 822 | 0.0 |
| 0 | RT82 | 82.0 | True | 67.0 | 0.5472736136962644 | 1584.0591370211075 | 68.84342375807059 | 76.0 | False | True | 1717 | 0.0 |
| 1 | RT80HC | 78.0 | True | 67.0 | 0.579707587219461 | 1670.6359975249688 | 72.60072697225803 | 72.56642723040831 | False | True | 2798 | 0.0 |
| 1 | RT82 | 82.0 | True | 67.0 | 0.5794591862318432 | 1671.568771201184 | 72.66330001720416 | 76.0 | False | True | 5675 | 0.0 |
| 2 | RT80HC | 78.0 | True | 67.0 | 0.5365813192645722 | 1589.6906088089845 | 68.94152393210412 | 72.0 | False | True | 515 | 0.0 |
| 2 | RT82 | 82.0 | True | 67.0 | 0.5364509783550014 | 1590.6171163265876 | 69.00580017678054 | 76.0 | False | True | 1073 | 0.0 |
