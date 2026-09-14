# Objective 2 Recommendation Cards — uttarakhand

Simulator version: `sim_v1_uttarakhand`. Generated from Phases 1-8 results; nothing below is a surrogate-only estimate -- every performance number is simulator-confirmed (Phase 7) and every robustness probability comes from real Monte Carlo simulator re-runs (Phase 8), not the surrogate.
## Regime 0 — regime 0 (7 pts, Ta_mean~22.6C, GHI~4.85 kWh/m2/day)

### Regime
- Population covered: 7 points, 2,026,629 people
- State: Uttarakhand | Medoid weather file: `data/weather/weather_regime_uttarakhand_cluster0_hourly.csv`
- Elevation: no dedicated elevation script; three inconsistent values coexist (0m in 00b_build_suntimes.py, flat 1200m DEFAULT_ALT_M in 02_combine, pressure-derived elev_proxy in 04b) (Objective 1 limitation, carried forward unchanged)
- Member-point robustness: NOT run (medoid-only for sub-daily/hourly shape; the annual weather magnitude below is now a real 10-year historical ensemble, not a noise proxy — see Caveats)

### Climate
- Tm_target_C (Objective 1, climate/delivery-anchored): 40.8
- Mains/inlet water temperature (population-weighted regime mean): 20.63 C
- L_required (Objective 1 sizing target): 122.9 kJ/kg
- Demand scenario: 300 L/day canonical dual-peak draw (`data/demand/demand_profile_uttarakhand.csv`)

### PCM shortlist (Objective 1, this regime)
  1. RT42 <- SELECTED
  2. RT44HC
  3. savE® OM42

### Selected design
- PCM: **RT42** (Tm=40.5 C, latent heat=165.0 kJ/kg, conductivity=0.1785 W/mK)
- Capsule shape/arrangement: sphere, staggered (frozen for all states)
- Capsule diameter: 0.0448 m (max PCM conduction distance = 0.0224 m)
- Capsule count: 12
- PCM mass: 0.496 kg
- Flow rate: 0.0337 kg/s (permitted range 0.010-0.050 kg/s)

### Performance (simulator-confirmed, sim_v1_uttarakhand)
- Useful annual energy: 1539.0 kWh/year
- Solar fraction: 39.06%
- Delivery-temperature hours (>= 45 C): 1072
- Unmet energy: 2285.2 kWh/year
- Pump energy: 0.0000 Wh/year
- Constraint margin (temperature): -6.48 C below the tightest safety limit

### Robustness (120 Monte Carlo draws — PCM latent heat, two-level weather noise [annual scale/offset + per-hour jitter], demand volume/timing, mains temperature)
- P(meets annual demand, solar_fraction>=50%): 0.0%
- P(meets delivery temperature, solar_fraction>=45%): 8.3%
- P(any safety-temperature violation): 100.0%
- P(exceeds max safe temperature limit): 100.0%
- Useful energy 5th-50th-95th percentile: [1472.5, 1542.1, 1624.0] kWh
- Solar fraction 5th-95th percentile: [34.3%, 46.1%]
- Max water temperature 95th percentile: 78.3 C
- **Framework rule (P(demand)>=75% and P(temp-safe)>=95%): NOT ROBUST BY THE FRAMEWORK RULE (report as caveat, not hidden)**

### Surrogate QA
- Hold-out RMSE (useful_energy_kWh, ExtraTrees, all regimes pooled): 0.615 kWh
- Surrogate-vs-simulator error for this selected design: 0.002%

### Decision
- This PCM's best found design reached the regime's own best useful-energy value (1540.2 kWh), winning outright before any tolerance tie-break was needed.
- Selection-rule pool size (candidates within 5% of best): 60

### Caveats
- The robustness section's annual GHI/temperature variability is drawn from Objective 1's real 10-year (2016-2025) daily weather archive for this regime (src/robustness/weather_ensemble.py) -- a genuine historical-year ensemble, not an assumed range. The within-year HOURLY shape still comes from a single medoid year plus synthetic per-hour jitter (no member-point/multi-year hourly data was pulled for this project, 40-hr cut list).
- Melting treated as a narrow +/-1 K band around a single reported Tm_C (no measured solidus/liquidus interval in the PCM database).
- Liquid natural convection inside the capsule is not resolved -- a fixed x2 effective-conductivity enhancement factor is assumed once liquid fraction >=50%.
- No auxiliary/backup heater modeled -- solar fraction here is the fraction of ideal 45 C demand met by solar+PCM alone, stricter than a real installed system with backup heating.
- No active high-temperature safety shield/bypass modeled -- see the robustness section's temperature-violation probability above.
- RT42 property provenance: check `any_property_imputed` in `data/objective1/pcm_database_uttarakhand.csv` for which fields are manufacturer-measured vs MICE/RF-imputed.


---

## Regime 1 — regime 1 (3 pts — SMALL SAMPLE, Ta_mean~9.4C, GHI~4.57 kWh/m2/day)

### Regime
- Population covered: 3 points, 330,780 people
- State: Uttarakhand | Medoid weather file: `data/weather/weather_regime_uttarakhand_cluster1_hourly.csv`
- Elevation: no dedicated elevation script; three inconsistent values coexist (0m in 00b_build_suntimes.py, flat 1200m DEFAULT_ALT_M in 02_combine, pressure-derived elev_proxy in 04b) (Objective 1 limitation, carried forward unchanged)
- Member-point robustness: NOT run (medoid-only for sub-daily/hourly shape; the annual weather magnitude below is now a real 10-year historical ensemble, not a noise proxy — see Caveats)

### Climate
- Tm_target_C (Objective 1, climate/delivery-anchored): 27.8
- Mains/inlet water temperature (population-weighted regime mean): 7.45 C
- L_required (Objective 1 sizing target): 178.1 kJ/kg
- Demand scenario: 300 L/day canonical dual-peak draw (`data/demand/demand_profile_uttarakhand.csv`)

### PCM shortlist (Objective 1, this regime)
  1. PureTemp 53
  2. n-Hexacosane (C26)
  3. Myristic acid (C14) <- SELECTED

### Selected design
- PCM: **Myristic acid (C14)** (Tm=53.0 C, latent heat=199.0 kJ/kg, conductivity=0.2329999999999999 W/mK)
- Capsule shape/arrangement: sphere, staggered (frozen for all states)
- Capsule diameter: 0.0452 m (max PCM conduction distance = 0.0226 m)
- Capsule count: 9
- PCM mass: 0.431 kg
- Flow rate: 0.0109 kg/s (permitted range 0.010-0.050 kg/s)

### Performance (simulator-confirmed, sim_v1_uttarakhand)
- Useful annual energy: 1525.9 kWh/year
- Solar fraction: 28.05%
- Delivery-temperature hours (>= 45 C): 79
- Unmet energy: 3908.6 kWh/year
- Pump energy: 0.0000 Wh/year
- Constraint margin (temperature): 11.88 C below the tightest safety limit

### Robustness (120 Monte Carlo draws — PCM latent heat, two-level weather noise [annual scale/offset + per-hour jitter], demand volume/timing, mains temperature)
- P(meets annual demand, solar_fraction>=50%): 0.0%
- P(meets delivery temperature, solar_fraction>=45%): 0.0%
- P(any safety-temperature violation): 0.0%
- P(exceeds max safe temperature limit): 0.0%
- Useful energy 5th-50th-95th percentile: [1417.6, 1531.9, 1654.4] kWh
- Solar fraction 5th-95th percentile: [24.3%, 34.3%]
- Max water temperature 95th percentile: 61.5 C
- **Framework rule (P(demand)>=75% and P(temp-safe)>=95%): NOT ROBUST BY THE FRAMEWORK RULE (report as caveat, not hidden)**

### Surrogate QA
- Hold-out RMSE (useful_energy_kWh, ExtraTrees, all regimes pooled): 0.615 kWh
- Surrogate-vs-simulator error for this selected design: 0.010%

### Decision
- This PCM's best found design reached the regime's own best useful-energy value (1526.6 kWh), winning outright before any tolerance tie-break was needed.
- Selection-rule pool size (candidates within 5% of best): 60

### Caveats
- The robustness section's annual GHI/temperature variability is drawn from Objective 1's real 10-year (2016-2025) daily weather archive for this regime (src/robustness/weather_ensemble.py) -- a genuine historical-year ensemble, not an assumed range. The within-year HOURLY shape still comes from a single medoid year plus synthetic per-hour jitter (no member-point/multi-year hourly data was pulled for this project, 40-hr cut list).
- Melting treated as a narrow +/-1 K band around a single reported Tm_C (no measured solidus/liquidus interval in the PCM database).
- Liquid natural convection inside the capsule is not resolved -- a fixed x2 effective-conductivity enhancement factor is assumed once liquid fraction >=50%.
- No auxiliary/backup heater modeled -- solar fraction here is the fraction of ideal 45 C demand met by solar+PCM alone, stricter than a real installed system with backup heating.
- No active high-temperature safety shield/bypass modeled -- see the robustness section's temperature-violation probability above.
- Myristic acid (C14) property provenance: check `any_property_imputed` in `data/objective1/pcm_database_uttarakhand.csv` for which fields are manufacturer-measured vs MICE/RF-imputed.


---

## Regime 2 — regime 2 (9 pts, Ta_mean~19.0C, GHI~4.90 kWh/m2/day)

### Regime
- Population covered: 9 points, 2,451,044 people
- State: Uttarakhand | Medoid weather file: `data/weather/weather_regime_uttarakhand_cluster2_hourly.csv`
- Elevation: no dedicated elevation script; three inconsistent values coexist (0m in 00b_build_suntimes.py, flat 1200m DEFAULT_ALT_M in 02_combine, pressure-derived elev_proxy in 04b) (Objective 1 limitation, carried forward unchanged)
- Member-point robustness: NOT run (medoid-only for sub-daily/hourly shape; the annual weather magnitude below is now a real 10-year historical ensemble, not a noise proxy — see Caveats)

### Climate
- Tm_target_C (Objective 1, climate/delivery-anchored): 38.7
- Mains/inlet water temperature (population-weighted regime mean): 17.01 C
- L_required (Objective 1 sizing target): 138.1 kJ/kg
- Demand scenario: 300 L/day canonical dual-peak draw (`data/demand/demand_profile_uttarakhand.csv`)

### PCM shortlist (Objective 1, this regime)
  1. RT42 <- SELECTED
  2. RT44HC
  3. savE® OM42

### Selected design
- PCM: **RT42** (Tm=40.5 C, latent heat=165.0 kJ/kg, conductivity=0.1785 W/mK)
- Capsule shape/arrangement: sphere, staggered (frozen for all states)
- Capsule diameter: 0.0432 m (max PCM conduction distance = 0.0216 m)
- Capsule count: 13
- PCM mass: 0.482 kg
- Flow rate: 0.0105 kg/s (permitted range 0.010-0.050 kg/s)

### Performance (simulator-confirmed, sim_v1_uttarakhand)
- Useful annual energy: 1626.4 kWh/year
- Solar fraction: 37.42%
- Delivery-temperature hours (>= 45 C): 759
- Unmet energy: 2636.0 kWh/year
- Pump energy: 0.0000 Wh/year
- Constraint margin (temperature): -5.12 C below the tightest safety limit

### Robustness (120 Monte Carlo draws — PCM latent heat, two-level weather noise [annual scale/offset + per-hour jitter], demand volume/timing, mains temperature)
- P(meets annual demand, solar_fraction>=50%): 0.0%
- P(meets delivery temperature, solar_fraction>=45%): 3.3%
- P(any safety-temperature violation): 100.0%
- P(exceeds max safe temperature limit): 100.0%
- Useful energy 5th-50th-95th percentile: [1514.0, 1617.9, 1716.7] kWh
- Solar fraction 5th-95th percentile: [32.9%, 44.3%]
- Max water temperature 95th percentile: 76.0 C
- **Framework rule (P(demand)>=75% and P(temp-safe)>=95%): NOT ROBUST BY THE FRAMEWORK RULE (report as caveat, not hidden)**

### Surrogate QA
- Hold-out RMSE (useful_energy_kWh, ExtraTrees, all regimes pooled): 0.615 kWh
- Surrogate-vs-simulator error for this selected design: 0.002%

### Decision
- This PCM's best found design reached the regime's own best useful-energy value (1626.9 kWh), winning outright before any tolerance tie-break was needed.
- Selection-rule pool size (candidates within 5% of best): 60

### Caveats
- The robustness section's annual GHI/temperature variability is drawn from Objective 1's real 10-year (2016-2025) daily weather archive for this regime (src/robustness/weather_ensemble.py) -- a genuine historical-year ensemble, not an assumed range. The within-year HOURLY shape still comes from a single medoid year plus synthetic per-hour jitter (no member-point/multi-year hourly data was pulled for this project, 40-hr cut list).
- Melting treated as a narrow +/-1 K band around a single reported Tm_C (no measured solidus/liquidus interval in the PCM database).
- Liquid natural convection inside the capsule is not resolved -- a fixed x2 effective-conductivity enhancement factor is assumed once liquid fraction >=50%.
- No auxiliary/backup heater modeled -- solar fraction here is the fraction of ideal 45 C demand met by solar+PCM alone, stricter than a real installed system with backup heating.
- No active high-temperature safety shield/bypass modeled -- see the robustness section's temperature-violation probability above.
- RT42 property provenance: check `any_property_imputed` in `data/objective1/pcm_database_uttarakhand.csv` for which fields are manufacturer-measured vs MICE/RF-imputed.


---

## Regime 3 — regime 3 (10 pts, Ta_mean~23.8C, GHI~4.75 kWh/m2/day)

### Regime
- Population covered: 10 points, 3,700,876 people
- State: Uttarakhand | Medoid weather file: `data/weather/weather_regime_uttarakhand_cluster3_hourly.csv`
- Elevation: no dedicated elevation script; three inconsistent values coexist (0m in 00b_build_suntimes.py, flat 1200m DEFAULT_ALT_M in 02_combine, pressure-derived elev_proxy in 04b) (Objective 1 limitation, carried forward unchanged)
- Member-point robustness: NOT run (medoid-only for sub-daily/hourly shape; the annual weather magnitude below is now a real 10-year historical ensemble, not a noise proxy — see Caveats)

### Climate
- Tm_target_C (Objective 1, climate/delivery-anchored): 42.1
- Mains/inlet water temperature (population-weighted regime mean): 21.82 C
- L_required (Objective 1 sizing target): 118.0 kJ/kg
- Demand scenario: 300 L/day canonical dual-peak draw (`data/demand/demand_profile_uttarakhand.csv`)

### PCM shortlist (Objective 1, this regime)
  1. RT44HC
  2. RT42 <- SELECTED
  3. savE® OM42

### Selected design
- PCM: **RT42** (Tm=40.5 C, latent heat=165.0 kJ/kg, conductivity=0.1785 W/mK)
- Capsule shape/arrangement: sphere, staggered (frozen for all states)
- Capsule diameter: 0.0491 m (max PCM conduction distance = 0.0245 m)
- Capsule count: 31
- PCM mass: 1.689 kg
- Flow rate: 0.0143 kg/s (permitted range 0.010-0.050 kg/s)

### Performance (simulator-confirmed, sim_v1_uttarakhand)
- Useful annual energy: 1565.5 kWh/year
- Solar fraction: 40.91%
- Delivery-temperature hours (>= 45 C): 1483
- Unmet energy: 2125.8 kWh/year
- Pump energy: 0.0000 Wh/year
- Constraint margin (temperature): -7.79 C below the tightest safety limit

### Robustness (120 Monte Carlo draws — PCM latent heat, two-level weather noise [annual scale/offset + per-hour jitter], demand volume/timing, mains temperature)
- P(meets annual demand, solar_fraction>=50%): 0.0%
- P(meets delivery temperature, solar_fraction>=45%): 29.2%
- P(any safety-temperature violation): 100.0%
- P(exceeds max safe temperature limit): 100.0%
- Useful energy 5th-50th-95th percentile: [1470.9, 1548.2, 1645.0] kWh
- Solar fraction 5th-95th percentile: [36.8%, 47.4%]
- Max water temperature 95th percentile: 79.8 C
- **Framework rule (P(demand)>=75% and P(temp-safe)>=95%): NOT ROBUST BY THE FRAMEWORK RULE (report as caveat, not hidden)**

### Surrogate QA
- Hold-out RMSE (useful_energy_kWh, ExtraTrees, all regimes pooled): 0.615 kWh
- Surrogate-vs-simulator error for this selected design: 0.000%

### Decision
- This PCM's best found design reached the regime's own best useful-energy value (1567.1 kWh), winning outright before any tolerance tie-break was needed.
- Selection-rule pool size (candidates within 5% of best): 60

### Caveats
- The robustness section's annual GHI/temperature variability is drawn from Objective 1's real 10-year (2016-2025) daily weather archive for this regime (src/robustness/weather_ensemble.py) -- a genuine historical-year ensemble, not an assumed range. The within-year HOURLY shape still comes from a single medoid year plus synthetic per-hour jitter (no member-point/multi-year hourly data was pulled for this project, 40-hr cut list).
- Melting treated as a narrow +/-1 K band around a single reported Tm_C (no measured solidus/liquidus interval in the PCM database).
- Liquid natural convection inside the capsule is not resolved -- a fixed x2 effective-conductivity enhancement factor is assumed once liquid fraction >=50%.
- No auxiliary/backup heater modeled -- solar fraction here is the fraction of ideal 45 C demand met by solar+PCM alone, stricter than a real installed system with backup heating.
- No active high-temperature safety shield/bypass modeled -- see the robustness section's temperature-violation probability above.
- RT42 property provenance: check `any_property_imputed` in `data/objective1/pcm_database_uttarakhand.csv` for which fields are manufacturer-measured vs MICE/RF-imputed.


---

## Regime 4 — regime 4 (16 pts, Ta_mean~18.5C, GHI~4.84 kWh/m2/day)

### Regime
- Population covered: 16 points, 1,966,385 people
- State: Uttarakhand | Medoid weather file: `data/weather/weather_regime_uttarakhand_cluster4_hourly.csv`
- Elevation: no dedicated elevation script; three inconsistent values coexist (0m in 00b_build_suntimes.py, flat 1200m DEFAULT_ALT_M in 02_combine, pressure-derived elev_proxy in 04b) (Objective 1 limitation, carried forward unchanged)
- Member-point robustness: NOT run (medoid-only for sub-daily/hourly shape; the annual weather magnitude below is now a real 10-year historical ensemble, not a noise proxy — see Caveats)

### Climate
- Tm_target_C (Objective 1, climate/delivery-anchored): 38.4
- Mains/inlet water temperature (population-weighted regime mean): 16.47 C
- L_required (Objective 1 sizing target): 140.4 kJ/kg
- Demand scenario: 300 L/day canonical dual-peak draw (`data/demand/demand_profile_uttarakhand.csv`)

### PCM shortlist (Objective 1, this regime)
  1. RT42
  2. RT44HC
  3. savE® OM42 <- SELECTED

### Selected design
- PCM: **savE® OM42** (Tm=44.0 C, latent heat=199.0 kJ/kg, conductivity=0.145 W/mK)
- Capsule shape/arrangement: sphere, staggered (frozen for all states)
- Capsule diameter: 0.0445 m (max PCM conduction distance = 0.0222 m)
- Capsule count: 11
- PCM mass: 0.458 kg
- Flow rate: 0.0107 kg/s (permitted range 0.010-0.050 kg/s)

### Performance (simulator-confirmed, sim_v1_uttarakhand)
- Useful annual energy: 1625.9 kWh/year
- Solar fraction: 37.00%
- Delivery-temperature hours (>= 45 C): 543
- Unmet energy: 2697.0 kWh/year
- Pump energy: 0.0000 Wh/year
- Constraint margin (temperature): -4.21 C below the tightest safety limit

### Robustness (120 Monte Carlo draws — PCM latent heat, two-level weather noise [annual scale/offset + per-hour jitter], demand volume/timing, mains temperature)
- P(meets annual demand, solar_fraction>=50%): 0.0%
- P(meets delivery temperature, solar_fraction>=45%): 0.8%
- P(any safety-temperature violation): 92.5%
- P(exceeds max safe temperature limit): 92.5%
- Useful energy 5th-50th-95th percentile: [1538.7, 1630.8, 1704.2] kWh
- Solar fraction 5th-95th percentile: [32.5%, 43.6%]
- Max water temperature 95th percentile: 72.5 C
- **Framework rule (P(demand)>=75% and P(temp-safe)>=95%): NOT ROBUST BY THE FRAMEWORK RULE (report as caveat, not hidden)**

### Surrogate QA
- Hold-out RMSE (useful_energy_kWh, ExtraTrees, all regimes pooled): 0.615 kWh
- Surrogate-vs-simulator error for this selected design: 0.009%

### Decision
- This PCM's best found design reached the regime's own best useful-energy value (1627.3 kWh), winning outright before any tolerance tie-break was needed.
- Selection-rule pool size (candidates within 5% of best): 60

### Caveats
- The robustness section's annual GHI/temperature variability is drawn from Objective 1's real 10-year (2016-2025) daily weather archive for this regime (src/robustness/weather_ensemble.py) -- a genuine historical-year ensemble, not an assumed range. The within-year HOURLY shape still comes from a single medoid year plus synthetic per-hour jitter (no member-point/multi-year hourly data was pulled for this project, 40-hr cut list).
- Melting treated as a narrow +/-1 K band around a single reported Tm_C (no measured solidus/liquidus interval in the PCM database).
- Liquid natural convection inside the capsule is not resolved -- a fixed x2 effective-conductivity enhancement factor is assumed once liquid fraction >=50%.
- No auxiliary/backup heater modeled -- solar fraction here is the fraction of ideal 45 C demand met by solar+PCM alone, stricter than a real installed system with backup heating.
- No active high-temperature safety shield/bypass modeled -- see the robustness section's temperature-violation probability above.
- savE® OM42 property provenance: check `any_property_imputed` in `data/objective1/pcm_database_uttarakhand.csv` for which fields are manufacturer-measured vs MICE/RF-imputed.
