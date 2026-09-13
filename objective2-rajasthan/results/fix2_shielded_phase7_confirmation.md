# Fix 2 follow-up — shielded Phase 7 re-confirmation (Rajasthan)

Raised in review: the shield (Fix 2) was only turned on at Phase 8's Monte Carlo call site, so Phase 5-7's design search, surrogate training, and deployable-design selection -- including Gate 4's reported 55.07% solar fraction -- were all computed against UNSHIELDED physics. This re-runs the exact 60 surrogate-proposed candidates through the real confirm_candidates()/apply_selection_rule() pipeline functions with the shield enabled (not a full DOE/surrogate re-run -- see module docstring for why that full re-run was judged unnecessary).


**Deployable-design selection unchanged in all 3 regimes: False.** Largest solar-fraction shift from enabling the shield: 0.0541 percentage points (shield only clips a rare high-temperature tail, so this is expected to be small, and is now a measured confirmation rather than an assumption).

| regime_id | pcm_id_unshielded | pcm_id_shielded | selection_unchanged | solar_fraction_unshielded_pct | solar_fraction_shielded_pct | solar_fraction_delta_pp | useful_energy_unshielded_kWh | useful_energy_shielded_kWh | max_water_temp_unshielded_C | max_water_temp_shielded_C | max_pcm_temp_unshielded_C | max_pcm_temp_shielded_C | n_safety_violations_unshielded | n_safety_violations_shielded | meets_temperature_safety_unshielded | meets_temperature_safety_shielded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | NONE_plain_tank | savE® OM55 | False | 54.9656 | 54.9454 | -0.0202233 | 1585.7 | 1585.61 | 68.5891 | 68.6585 | 68.5891 | 62.7654 | 0 | 0 | True | True |
| 1 | NONE_plain_tank | CrodaTherm 60 | False | 58.2277 | 58.1736 | -0.0541129 | 1673.36 | 1674.46 | 72.3797 | 72.005 | 72.3797 | 63.323 | 0 | 0 | True | True |
| 2 | NONE_plain_tank | PlusICE A58 | False | 53.8823 | 53.8457 | -0.0365585 | 1592.27 | 1592.95 | 68.7193 | 68.5006 | 68.7193 | 63.3145 | 0 | 0 | True | True |
