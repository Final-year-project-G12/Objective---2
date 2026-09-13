# Objective 2 Recommendation Cards — tamilnadu

Simulator version: `sim_v1_tamilnadu`. Generated from Phases 1-8 results; nothing below is a surrogate-only estimate -- every performance number is simulator-confirmed (Phase 7) and every robustness probability comes from real Monte Carlo simulator re-runs (Phase 8), not the surrogate.
## Regime 0 — coastal/high-humidity (small, 8 pts)

### Regime
- Population covered: 8 points, 12,658,861 people
- State: Tamil Nadu | Medoid weather file: `data/weather/weather_regime_tamilnadu_cluster0_hourly.csv`
- Elevation: flat 150 m approximation (Objective 1 limitation, carried forward unchanged)
- Member-point robustness: NOT run (medoid-only for sub-daily/hourly shape; the annual weather magnitude below is now a real 10-year historical ensemble, not a noise proxy — see Caveats)

### Climate
- Tm_target_C (Objective 1, climate/delivery-anchored): 48.9
- Mains/inlet water temperature (population-weighted regime mean): 26.00 C
- L_required (Objective 1 sizing target): 301.4 kJ/kg
- Demand scenario: 300 L/day canonical dual-peak draw (`data/demand/demand_profile_tamilnadu.csv`)

### PCM shortlist (Objective 1, this regime)
  1. savE® OM49
  2. n-Tricosane (C23)
  3. n-Tetracosane (C24) <- SELECTED

### Selected design
- PCM: **n-Tetracosane (C24)** (Tm=52.0 C, latent heat=255.0 kJ/kg, conductivity=0.2395 W/mK)
- Capsule shape/arrangement: sphere, staggered (frozen for all states)
- Capsule diameter: 0.0433 m (max PCM conduction distance = 0.0216 m)
- Capsule count: 11
- PCM mass: 0.373 kg
- Flow rate: 0.0235 kg/s (permitted range 0.010-0.050 kg/s)

### Performance (simulator-confirmed, sim_v1_tamilnadu)
- Useful annual energy: 1675.1 kWh/year
- Solar fraction: 52.32%
- Delivery-temperature hours (>= 45 C): 3823
- Unmet energy: 1156.7 kWh/year
- Pump energy: 0.0000 Wh/year
- Constraint margin (temperature): -5.25 C below the tightest safety limit

### Robustness (120 Monte Carlo draws — PCM latent heat, two-level weather noise [annual scale/offset + per-hour jitter], demand volume/timing, mains temperature)
- P(meets annual demand, solar_fraction>=50%): 80.8%
- P(meets delivery temperature, solar_fraction>=45%): 100.0%
- P(any safety-temperature violation): 100.0%
- P(exceeds max safe temperature limit): 100.0%
- Useful energy 5th-50th-95th percentile: [1592.0, 1681.7, 1782.6] kWh
- Solar fraction 5th-95th percentile: [47.7%, 61.7%]
- Max water temperature 95th percentile: 75.0 C
- **Framework rule (P(demand)>=75% and P(temp-safe)>=95%): NOT ROBUST BY THE FRAMEWORK RULE (report as caveat, not hidden)**

### Surrogate QA
- Hold-out RMSE (useful_energy_kWh, ExtraTrees, all regimes pooled): 0.565 kWh
- Surrogate-vs-simulator error for this selected design: 0.023%

### Decision
- This PCM's best found design reached the regime's own best useful-energy value (1678.6 kWh), winning outright before any tolerance tie-break was needed.
- Selection-rule pool size (candidates within 5% of best): 60

### Caveats
- The robustness section's annual GHI/temperature variability is drawn from Objective 1's real 10-year (2016-2025) daily weather archive for this regime (src/robustness/weather_ensemble.py) -- a genuine historical-year ensemble, not an assumed range. The within-year HOURLY shape still comes from a single medoid year plus synthetic per-hour jitter (no member-point/multi-year hourly data was pulled for this project, 40-hr cut list).
- Melting treated as a narrow +/-1 K band around a single reported Tm_C (no measured solidus/liquidus interval in the PCM database).
- Liquid natural convection inside the capsule is not resolved -- a fixed x2 effective-conductivity enhancement factor is assumed once liquid fraction >=50%.
- No auxiliary/backup heater modeled -- solar fraction here is the fraction of ideal 45 C demand met by solar+PCM alone, stricter than a real installed system with backup heating.
- No active high-temperature safety shield/bypass modeled -- see the robustness section's temperature-violation probability above.
- n-Tetracosane (C24) property provenance: check `any_property_imputed` in `data/objective1/pcm_database_tamilnadu.csv` for which fields are manufacturer-measured vs MICE/RF-imputed.


---

## Regime 1 — interior plains (largest, 42 pts)

### Regime
- Population covered: 42 points, 19,812,760 people
- State: Tamil Nadu | Medoid weather file: `data/weather/weather_regime_tamilnadu_cluster1_hourly.csv`
- Elevation: flat 150 m approximation (Objective 1 limitation, carried forward unchanged)
- Member-point robustness: NOT run (medoid-only for sub-daily/hourly shape; the annual weather magnitude below is now a real 10-year historical ensemble, not a noise proxy — see Caveats)

### Climate
- Tm_target_C (Objective 1, climate/delivery-anchored): 49.5
- Mains/inlet water temperature (population-weighted regime mean): 24.39 C
- L_required (Objective 1 sizing target): 321.6 kJ/kg
- Demand scenario: 300 L/day canonical dual-peak draw (`data/demand/demand_profile_tamilnadu.csv`)

### PCM shortlist (Objective 1, this regime)
  1. n-Tricosane (C23)
  2. n-Tetracosane (C24) <- SELECTED
  3. n-Pentacosane (C25)

### Selected design
- PCM: **n-Tetracosane (C24)** (Tm=52.0 C, latent heat=255.0 kJ/kg, conductivity=0.2395 W/mK)
- Capsule shape/arrangement: sphere, staggered (frozen for all states)
- Capsule diameter: 0.0495 m (max PCM conduction distance = 0.0248 m)
- Capsule count: 9
- PCM mass: 0.457 kg
- Flow rate: 0.0160 kg/s (permitted range 0.010-0.050 kg/s)

### Performance (simulator-confirmed, sim_v1_tamilnadu)
- Useful annual energy: 1811.3 kWh/year
- Solar fraction: 53.18%
- Delivery-temperature hours (>= 45 C): 3949
- Unmet energy: 1232.0 kWh/year
- Pump energy: 0.0000 Wh/year
- Constraint margin (temperature): -5.36 C below the tightest safety limit

### Robustness (120 Monte Carlo draws — PCM latent heat, two-level weather noise [annual scale/offset + per-hour jitter], demand volume/timing, mains temperature)
- P(meets annual demand, solar_fraction>=50%): 91.7%
- P(meets delivery temperature, solar_fraction>=45%): 100.0%
- P(any safety-temperature violation): 100.0%
- P(exceeds max safe temperature limit): 100.0%
- Useful energy 5th-50th-95th percentile: [1705.9, 1825.2, 1939.4] kWh
- Solar fraction 5th-95th percentile: [49.3%, 63.4%]
- Max water temperature 95th percentile: 78.4 C
- **Framework rule (P(demand)>=75% and P(temp-safe)>=95%): NOT ROBUST BY THE FRAMEWORK RULE (report as caveat, not hidden)**

### Surrogate QA
- Hold-out RMSE (useful_energy_kWh, ExtraTrees, all regimes pooled): 0.565 kWh
- Surrogate-vs-simulator error for this selected design: 0.007%

### Decision
- This PCM's best found design reached the regime's own best useful-energy value (1815.0 kWh), winning outright before any tolerance tie-break was needed.
- Selection-rule pool size (candidates within 5% of best): 60

### Caveats
- The robustness section's annual GHI/temperature variability is drawn from Objective 1's real 10-year (2016-2025) daily weather archive for this regime (src/robustness/weather_ensemble.py) -- a genuine historical-year ensemble, not an assumed range. The within-year HOURLY shape still comes from a single medoid year plus synthetic per-hour jitter (no member-point/multi-year hourly data was pulled for this project, 40-hr cut list).
- Melting treated as a narrow +/-1 K band around a single reported Tm_C (no measured solidus/liquidus interval in the PCM database).
- Liquid natural convection inside the capsule is not resolved -- a fixed x2 effective-conductivity enhancement factor is assumed once liquid fraction >=50%.
- No auxiliary/backup heater modeled -- solar fraction here is the fraction of ideal 45 C demand met by solar+PCM alone, stricter than a real installed system with backup heating.
- No active high-temperature safety shield/bypass modeled -- see the robustness section's temperature-violation probability above.
- n-Tetracosane (C24) property provenance: check `any_property_imputed` in `data/objective1/pcm_database_tamilnadu.csv` for which fields are manufacturer-measured vs MICE/RF-imputed.


---

## Regime 2 — coastal belt (39 pts)

### Regime
- Population covered: 39 points, 18,057,220 people
- State: Tamil Nadu | Medoid weather file: `data/weather/weather_regime_tamilnadu_cluster2_hourly.csv`
- Elevation: flat 150 m approximation (Objective 1 limitation, carried forward unchanged)
- Member-point robustness: NOT run (medoid-only for sub-daily/hourly shape; the annual weather magnitude below is now a real 10-year historical ensemble, not a noise proxy — see Caveats)

### Climate
- Tm_target_C (Objective 1, climate/delivery-anchored): 50.4
- Mains/inlet water temperature (population-weighted regime mean): 25.93 C
- L_required (Objective 1 sizing target): 302.2 kJ/kg
- Demand scenario: 300 L/day canonical dual-peak draw (`data/demand/demand_profile_tamilnadu.csv`)

### PCM shortlist (Objective 1, this regime)
  1. savE® OM49
  2. PlusICE A52 <- SELECTED
  3. n-Tetracosane (C24)

### Selected design
- PCM: **PlusICE A52** (Tm=52.0 C, latent heat=220.0 kJ/kg, conductivity=0.18 W/mK)
- Capsule shape/arrangement: sphere, staggered (frozen for all states)
- Capsule diameter: 0.0496 m (max PCM conduction distance = 0.0248 m)
- Capsule count: 8
- PCM mass: 0.414 kg
- Flow rate: 0.0227 kg/s (permitted range 0.010-0.050 kg/s)

### Performance (simulator-confirmed, sim_v1_tamilnadu)
- Useful annual energy: 1751.3 kWh/year
- Solar fraction: 53.36%
- Delivery-temperature hours (>= 45 C): 4031
- Unmet energy: 1135.3 kWh/year
- Pump energy: 0.0000 Wh/year
- Constraint margin (temperature): -7.07 C below the tightest safety limit

### Robustness (120 Monte Carlo draws — PCM latent heat, two-level weather noise [annual scale/offset + per-hour jitter], demand volume/timing, mains temperature)
- P(meets annual demand, solar_fraction>=50%): 95.0%
- P(meets delivery temperature, solar_fraction>=45%): 100.0%
- P(any safety-temperature violation): 100.0%
- P(exceeds max safe temperature limit): 100.0%
- Useful energy 5th-50th-95th percentile: [1631.9, 1742.7, 1844.1] kWh
- Solar fraction 5th-95th percentile: [50.0%, 62.9%]
- Max water temperature 95th percentile: 78.1 C
- **Framework rule (P(demand)>=75% and P(temp-safe)>=95%): NOT ROBUST BY THE FRAMEWORK RULE (report as caveat, not hidden)**

### Surrogate QA
- Hold-out RMSE (useful_energy_kWh, ExtraTrees, all regimes pooled): 0.565 kWh
- Surrogate-vs-simulator error for this selected design: 0.000%

### Decision
- This PCM's best found design reached the regime's own best useful-energy value (1755.6 kWh), winning outright before any tolerance tie-break was needed.
- Selection-rule pool size (candidates within 5% of best): 60

### Caveats
- The robustness section's annual GHI/temperature variability is drawn from Objective 1's real 10-year (2016-2025) daily weather archive for this regime (src/robustness/weather_ensemble.py) -- a genuine historical-year ensemble, not an assumed range. The within-year HOURLY shape still comes from a single medoid year plus synthetic per-hour jitter (no member-point/multi-year hourly data was pulled for this project, 40-hr cut list).
- Melting treated as a narrow +/-1 K band around a single reported Tm_C (no measured solidus/liquidus interval in the PCM database).
- Liquid natural convection inside the capsule is not resolved -- a fixed x2 effective-conductivity enhancement factor is assumed once liquid fraction >=50%.
- No auxiliary/backup heater modeled -- solar fraction here is the fraction of ideal 45 C demand met by solar+PCM alone, stricter than a real installed system with backup heating.
- No active high-temperature safety shield/bypass modeled -- see the robustness section's temperature-violation probability above.
- PlusICE A52 property provenance: check `any_property_imputed` in `data/objective1/pcm_database_tamilnadu.csv` for which fields are manufacturer-measured vs MICE/RF-imputed.


---

## Regime 3 — semi-arid interior / Coimbatore-Tiruppur-like (22 pts)

### Regime
- Population covered: 22 points, 10,252,760 people
- State: Tamil Nadu | Medoid weather file: `data/weather/weather_regime_tamilnadu_cluster3_hourly.csv`
- Elevation: flat 150 m approximation (Objective 1 limitation, carried forward unchanged)
- Member-point robustness: NOT run (medoid-only for sub-daily/hourly shape; the annual weather magnitude below is now a real 10-year historical ensemble, not a noise proxy — see Caveats)

### Climate
- Tm_target_C (Objective 1, climate/delivery-anchored): 51.5
- Mains/inlet water temperature (population-weighted regime mean): 25.79 C
- L_required (Objective 1 sizing target): 304.1 kJ/kg
- Demand scenario: 300 L/day canonical dual-peak draw (`data/demand/demand_profile_tamilnadu.csv`)

### PCM shortlist (Objective 1, this regime)
  1. n-Tetracosane (C24)
  2. PlusICE A52
  3. PureTemp 53 <- SELECTED

### Selected design
- PCM: **PureTemp 53** (Tm=53.0 C, latent heat=225.0 kJ/kg, conductivity=0.2 W/mK)
- Capsule shape/arrangement: sphere, staggered (frozen for all states)
- Capsule diameter: 0.0430 m (max PCM conduction distance = 0.0215 m)
- Capsule count: 36
- PCM mass: 1.375 kg
- Flow rate: 0.0109 kg/s (permitted range 0.010-0.050 kg/s)

### Performance (simulator-confirmed, sim_v1_tamilnadu)
- Useful annual energy: 1818.7 kWh/year
- Solar fraction: 54.75%
- Delivery-temperature hours (>= 45 C): 4292
- Unmet energy: 1109.9 kWh/year
- Pump energy: 0.0000 Wh/year
- Constraint margin (temperature): -4.91 C below the tightest safety limit

### Robustness (120 Monte Carlo draws — PCM latent heat, two-level weather noise [annual scale/offset + per-hour jitter], demand volume/timing, mains temperature)
- P(meets annual demand, solar_fraction>=50%): 98.3%
- P(meets delivery temperature, solar_fraction>=45%): 100.0%
- P(any safety-temperature violation): 100.0%
- P(exceeds max safe temperature limit): 100.0%
- Useful energy 5th-50th-95th percentile: [1711.7, 1807.0, 1900.3] kWh
- Solar fraction 5th-95th percentile: [50.9%, 64.0%]
- Max water temperature 95th percentile: 78.0 C
- **Framework rule (P(demand)>=75% and P(temp-safe)>=95%): NOT ROBUST BY THE FRAMEWORK RULE (report as caveat, not hidden)**

### Surrogate QA
- Hold-out RMSE (useful_energy_kWh, ExtraTrees, all regimes pooled): 0.565 kWh
- Surrogate-vs-simulator error for this selected design: 0.001%

### Decision
- This PCM's best found design reached the regime's own best useful-energy value (1819.0 kWh), winning outright before any tolerance tie-break was needed.
- Selection-rule pool size (candidates within 5% of best): 60

### Caveats
- The robustness section's annual GHI/temperature variability is drawn from Objective 1's real 10-year (2016-2025) daily weather archive for this regime (src/robustness/weather_ensemble.py) -- a genuine historical-year ensemble, not an assumed range. The within-year HOURLY shape still comes from a single medoid year plus synthetic per-hour jitter (no member-point/multi-year hourly data was pulled for this project, 40-hr cut list).
- Melting treated as a narrow +/-1 K band around a single reported Tm_C (no measured solidus/liquidus interval in the PCM database).
- Liquid natural convection inside the capsule is not resolved -- a fixed x2 effective-conductivity enhancement factor is assumed once liquid fraction >=50%.
- No auxiliary/backup heater modeled -- solar fraction here is the fraction of ideal 45 C demand met by solar+PCM alone, stricter than a real installed system with backup heating.
- No active high-temperature safety shield/bypass modeled -- see the robustness section's temperature-violation probability above.
- PureTemp 53 property provenance: check `any_property_imputed` in `data/objective1/pcm_database_tamilnadu.csv` for which fields are manufacturer-measured vs MICE/RF-imputed.


---

## Regime 4 — high-humidity / highest HSI (22 pts)

### Regime
- Population covered: 22 points, 10,445,170 people
- State: Tamil Nadu | Medoid weather file: `data/weather/weather_regime_tamilnadu_cluster4_hourly.csv`
- Elevation: flat 150 m approximation (Objective 1 limitation, carried forward unchanged)
- Member-point robustness: NOT run (medoid-only for sub-daily/hourly shape; the annual weather magnitude below is now a real 10-year historical ensemble, not a noise proxy — see Caveats)

### Climate
- Tm_target_C (Objective 1, climate/delivery-anchored): 46.5
- Mains/inlet water temperature (population-weighted regime mean): 24.04 C
- L_required (Objective 1 sizing target): 326.0 kJ/kg
- Demand scenario: 300 L/day canonical dual-peak draw (`data/demand/demand_profile_tamilnadu.csv`)

### PCM shortlist (Objective 1, this regime)
  1. n-Tricosane (C23) <- SELECTED
  2. RT45HC
  3. n-Docosane (C22)

### Selected design
- PCM: **n-Tricosane (C23)** (Tm=47.5 C, latent heat=232.0 kJ/kg, conductivity=0.239 W/mK)
- Capsule shape/arrangement: sphere, staggered (frozen for all states)
- Capsule diameter: 0.0454 m (max PCM conduction distance = 0.0227 m)
- Capsule count: 36
- PCM mass: 1.404 kg
- Flow rate: 0.0223 kg/s (permitted range 0.010-0.050 kg/s)

### Performance (simulator-confirmed, sim_v1_tamilnadu)
- Useful annual energy: 1624.3 kWh/year
- Solar fraction: 51.45%
- Delivery-temperature hours (>= 45 C): 3471
- Unmet energy: 1299.3 kWh/year
- Pump energy: 0.0000 Wh/year
- Constraint margin (temperature): 0.01 C below the tightest safety limit

### Robustness (120 Monte Carlo draws — PCM latent heat, two-level weather noise [annual scale/offset + per-hour jitter], demand volume/timing, mains temperature)
- P(meets annual demand, solar_fraction>=50%): 73.3%
- P(meets delivery temperature, solar_fraction>=45%): 100.0%
- P(any safety-temperature violation): 75.0%
- P(exceeds max safe temperature limit): 75.0%
- Useful energy 5th-50th-95th percentile: [1532.7, 1617.4, 1703.2] kWh
- Solar fraction 5th-95th percentile: [47.1%, 59.7%]
- Max water temperature 95th percentile: 74.3 C
- **Framework rule (P(demand)>=75% and P(temp-safe)>=95%): NOT ROBUST BY THE FRAMEWORK RULE (report as caveat, not hidden)**

### Surrogate QA
- Hold-out RMSE (useful_energy_kWh, ExtraTrees, all regimes pooled): 0.565 kWh
- Surrogate-vs-simulator error for this selected design: 0.000%

### Decision
- This PCM's best found design reached the regime's own best useful-energy value (1630.4 kWh), winning outright before any tolerance tie-break was needed.
- Selection-rule pool size (candidates within 5% of best): 60

### Caveats
- The robustness section's annual GHI/temperature variability is drawn from Objective 1's real 10-year (2016-2025) daily weather archive for this regime (src/robustness/weather_ensemble.py) -- a genuine historical-year ensemble, not an assumed range. The within-year HOURLY shape still comes from a single medoid year plus synthetic per-hour jitter (no member-point/multi-year hourly data was pulled for this project, 40-hr cut list).
- Melting treated as a narrow +/-1 K band around a single reported Tm_C (no measured solidus/liquidus interval in the PCM database).
- Liquid natural convection inside the capsule is not resolved -- a fixed x2 effective-conductivity enhancement factor is assumed once liquid fraction >=50%.
- No auxiliary/backup heater modeled -- solar fraction here is the fraction of ideal 45 C demand met by solar+PCM alone, stricter than a real installed system with backup heating.
- No active high-temperature safety shield/bypass modeled -- see the robustness section's temperature-violation probability above.
- n-Tricosane (C23) property provenance: check `any_property_imputed` in `data/objective1/pcm_database_tamilnadu.csv` for which fields are manufacturer-measured vs MICE/RF-imputed.
