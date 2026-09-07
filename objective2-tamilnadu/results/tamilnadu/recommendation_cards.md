# Objective 2 Recommendation Cards — tamilnadu

Simulator version: `sim_v1_tamilnadu`. Generated from Phases 1-8 results; nothing below is a surrogate-only estimate -- every performance number is simulator-confirmed (Phase 7) and every robustness probability comes from real Monte Carlo simulator re-runs (Phase 8), not the surrogate.
## Regime 0 — coastal/high-humidity (small, 8 pts)

### Regime
- Population covered: 8 points, 12,658,861 people
- State: Tamil Nadu | Medoid weather file: `data/weather/weather_regime_tamilnadu_cluster0_hourly.csv`
- Elevation: flat 150 m approximation (Objective 1 limitation, carried forward unchanged)
- Member-point robustness: NOT run (medoid-only for sub-daily/hourly shape; the annual weather magnitude below is now a real 10-year historical ensemble, not a noise proxy — see Caveats)

### Climate
- Tm_target_C (Objective 1, climate/delivery-anchored): 57.0
- Mains/inlet water temperature (population-weighted regime mean): 26.00 C
- L_required (Objective 1 sizing target): 301.4 kJ/kg
- Demand scenario: 300 L/day canonical dual-peak draw (`data/demand/demand_profile_tamilnadu.csv`)

### PCM shortlist (Objective 1, this regime)
  1. n-Octacosane (C28)
  2. n-Hexacosane (C26)
  3. PureTemp 58
  -> Plain tank (no PCM) selected instead of all 3 shortlisted candidates (see Decision below)

### Selected design
- **Plain sensible-water tank — no PCM capsules.**
- Flow rate: 0.0159 kg/s (permitted range 0.010-0.050 kg/s)

### Performance (simulator-confirmed, sim_v1_tamilnadu)
- Useful annual energy: 1673.3 kWh/year
- Solar fraction: 52.26%
- Delivery-temperature hours (>= 45 C): 3821
- Unmet energy: 1158.1 kWh/year
- Pump energy: 0.0000 Wh/year
- Constraint margin (temperature): 4.72 C below the tightest safety limit

### Robustness (120 Monte Carlo draws — PCM latent heat, two-level weather noise [annual scale/offset + per-hour jitter], demand volume/timing, mains temperature)
- P(meets annual demand, solar_fraction>=50%): 89.2%
- P(meets delivery temperature, solar_fraction>=45%): 100.0%
- P(any safety-temperature violation): 7.5%
- P(exceeds max safe temperature limit): 7.5%
- Useful energy 5th-50th-95th percentile: [1567.8, 1667.8, 1763.0] kWh
- Solar fraction 5th-95th percentile: [47.9%, 61.1%]
- Max water temperature 95th percentile: 75.1 C
- **Framework rule (P(demand)>=75% and P(temp-safe)>=95%): NOT ROBUST BY THE FRAMEWORK RULE (report as caveat, not hidden)**

### Surrogate QA
- Hold-out RMSE (useful_energy_kWh, ExtraTrees, all regimes pooled): 0.708 kWh
- Surrogate-vs-simulator error for this selected design: 0.049%

### Decision
- Best PCM found in this regime's search reached 1673.3 kWh vs plain tank's 1673.3 kWh — within the pre-declared 5% Pareto tolerance, so the selection rule's next tie-breaker (minimize PCM mass, then pump energy, then capsule count) picked the zero-mass plain tank. See `docs_objective2/08_PHASE7_OPTIMIZATION.md` for the full comparison.
- Selection-rule pool size (candidates within 5% of best): 5

### Caveats
- The robustness section's annual GHI/temperature variability is drawn from Objective 1's real 10-year (2016-2025) daily weather archive for this regime (src/robustness/weather_ensemble.py) -- a genuine historical-year ensemble, not an assumed range. The within-year HOURLY shape still comes from a single medoid year plus synthetic per-hour jitter (no member-point/multi-year hourly data was pulled for this project, 40-hr cut list).
- Melting treated as a narrow +/-1 K band around a single reported Tm_C (no measured solidus/liquidus interval in the PCM database).
- Liquid natural convection inside the capsule is not resolved -- a fixed x2 effective-conductivity enhancement factor is assumed once liquid fraction >=50%.
- No auxiliary/backup heater modeled -- solar fraction here is the fraction of ideal 45 C demand met by solar+PCM alone, stricter than a real installed system with backup heating.
- No active high-temperature safety shield/bypass modeled -- see the robustness section's temperature-violation probability above.


---

## Regime 1 — interior plains (largest, 42 pts)

### Regime
- Population covered: 42 points, 19,812,760 people
- State: Tamil Nadu | Medoid weather file: `data/weather/weather_regime_tamilnadu_cluster1_hourly.csv`
- Elevation: flat 150 m approximation (Objective 1 limitation, carried forward unchanged)
- Member-point robustness: NOT run (medoid-only for sub-daily/hourly shape; the annual weather magnitude below is now a real 10-year historical ensemble, not a noise proxy — see Caveats)

### Climate
- Tm_target_C (Objective 1, climate/delivery-anchored): 57.0
- Mains/inlet water temperature (population-weighted regime mean): 24.39 C
- L_required (Objective 1 sizing target): 321.6 kJ/kg
- Demand scenario: 300 L/day canonical dual-peak draw (`data/demand/demand_profile_tamilnadu.csv`)

### PCM shortlist (Objective 1, this regime)
  1. n-Octacosane (C28)
  2. RT64HC
  3. n-Hexacosane (C26)
  -> Plain tank (no PCM) selected instead of all 3 shortlisted candidates (see Decision below)

### Selected design
- **Plain sensible-water tank — no PCM capsules.**
- Flow rate: 0.0124 kg/s (permitted range 0.010-0.050 kg/s)

### Performance (simulator-confirmed, sim_v1_tamilnadu)
- Useful annual energy: 1809.9 kWh/year
- Solar fraction: 53.11%
- Delivery-temperature hours (>= 45 C): 3935
- Unmet energy: 1233.7 kWh/year
- Pump energy: 0.0000 Wh/year
- Constraint margin (temperature): 4.56 C below the tightest safety limit

### Robustness (120 Monte Carlo draws — PCM latent heat, two-level weather noise [annual scale/offset + per-hour jitter], demand volume/timing, mains temperature)
- P(meets annual demand, solar_fraction>=50%): 90.0%
- P(meets delivery temperature, solar_fraction>=45%): 100.0%
- P(any safety-temperature violation): 20.0%
- P(exceeds max safe temperature limit): 20.0%
- Useful energy 5th-50th-95th percentile: [1699.9, 1800.2, 1930.6] kWh
- Solar fraction 5th-95th percentile: [49.0%, 61.8%]
- Max water temperature 95th percentile: 77.3 C
- **Framework rule (P(demand)>=75% and P(temp-safe)>=95%): NOT ROBUST BY THE FRAMEWORK RULE (report as caveat, not hidden)**

### Surrogate QA
- Hold-out RMSE (useful_energy_kWh, ExtraTrees, all regimes pooled): 0.708 kWh
- Surrogate-vs-simulator error for this selected design: 0.048%

### Decision
- Best PCM found in this regime's search reached 1809.9 kWh vs plain tank's 1809.9 kWh — within the pre-declared 5% Pareto tolerance, so the selection rule's next tie-breaker (minimize PCM mass, then pump energy, then capsule count) picked the zero-mass plain tank. See `docs_objective2/08_PHASE7_OPTIMIZATION.md` for the full comparison.
- Selection-rule pool size (candidates within 5% of best): 5

### Caveats
- The robustness section's annual GHI/temperature variability is drawn from Objective 1's real 10-year (2016-2025) daily weather archive for this regime (src/robustness/weather_ensemble.py) -- a genuine historical-year ensemble, not an assumed range. The within-year HOURLY shape still comes from a single medoid year plus synthetic per-hour jitter (no member-point/multi-year hourly data was pulled for this project, 40-hr cut list).
- Melting treated as a narrow +/-1 K band around a single reported Tm_C (no measured solidus/liquidus interval in the PCM database).
- Liquid natural convection inside the capsule is not resolved -- a fixed x2 effective-conductivity enhancement factor is assumed once liquid fraction >=50%.
- No auxiliary/backup heater modeled -- solar fraction here is the fraction of ideal 45 C demand met by solar+PCM alone, stricter than a real installed system with backup heating.
- No active high-temperature safety shield/bypass modeled -- see the robustness section's temperature-violation probability above.


---

## Regime 2 — coastal belt (39 pts)

### Regime
- Population covered: 39 points, 18,057,220 people
- State: Tamil Nadu | Medoid weather file: `data/weather/weather_regime_tamilnadu_cluster2_hourly.csv`
- Elevation: flat 150 m approximation (Objective 1 limitation, carried forward unchanged)
- Member-point robustness: NOT run (medoid-only for sub-daily/hourly shape; the annual weather magnitude below is now a real 10-year historical ensemble, not a noise proxy — see Caveats)

### Climate
- Tm_target_C (Objective 1, climate/delivery-anchored): 57.0
- Mains/inlet water temperature (population-weighted regime mean): 25.93 C
- L_required (Objective 1 sizing target): 302.2 kJ/kg
- Demand scenario: 300 L/day canonical dual-peak draw (`data/demand/demand_profile_tamilnadu.csv`)

### PCM shortlist (Objective 1, this regime)
  1. n-Octacosane (C28)
  2. PureTemp 58
  3. n-Hexacosane (C26)
  -> Plain tank (no PCM) selected instead of all 3 shortlisted candidates (see Decision below)

### Selected design
- **Plain sensible-water tank — no PCM capsules.**
- Flow rate: 0.0127 kg/s (permitted range 0.010-0.050 kg/s)

### Performance (simulator-confirmed, sim_v1_tamilnadu)
- Useful annual energy: 1749.8 kWh/year
- Solar fraction: 53.30%
- Delivery-temperature hours (>= 45 C): 4021
- Unmet energy: 1136.6 kWh/year
- Pump energy: 0.0000 Wh/year
- Constraint margin (temperature): 2.91 C below the tightest safety limit

### Robustness (120 Monte Carlo draws — PCM latent heat, two-level weather noise [annual scale/offset + per-hour jitter], demand volume/timing, mains temperature)
- P(meets annual demand, solar_fraction>=50%): 94.2%
- P(meets delivery temperature, solar_fraction>=45%): 100.0%
- P(any safety-temperature violation): 28.3%
- P(exceeds max safe temperature limit): 28.3%
- Useful energy 5th-50th-95th percentile: [1658.9, 1743.8, 1867.0] kWh
- Solar fraction 5th-95th percentile: [49.3%, 62.6%]
- Max water temperature 95th percentile: 77.6 C
- **Framework rule (P(demand)>=75% and P(temp-safe)>=95%): NOT ROBUST BY THE FRAMEWORK RULE (report as caveat, not hidden)**

### Surrogate QA
- Hold-out RMSE (useful_energy_kWh, ExtraTrees, all regimes pooled): 0.708 kWh
- Surrogate-vs-simulator error for this selected design: 0.056%

### Decision
- Best PCM found in this regime's search reached 1749.8 kWh vs plain tank's 1749.8 kWh — within the pre-declared 5% Pareto tolerance, so the selection rule's next tie-breaker (minimize PCM mass, then pump energy, then capsule count) picked the zero-mass plain tank. See `docs_objective2/08_PHASE7_OPTIMIZATION.md` for the full comparison.
- Selection-rule pool size (candidates within 5% of best): 5

### Caveats
- The robustness section's annual GHI/temperature variability is drawn from Objective 1's real 10-year (2016-2025) daily weather archive for this regime (src/robustness/weather_ensemble.py) -- a genuine historical-year ensemble, not an assumed range. The within-year HOURLY shape still comes from a single medoid year plus synthetic per-hour jitter (no member-point/multi-year hourly data was pulled for this project, 40-hr cut list).
- Melting treated as a narrow +/-1 K band around a single reported Tm_C (no measured solidus/liquidus interval in the PCM database).
- Liquid natural convection inside the capsule is not resolved -- a fixed x2 effective-conductivity enhancement factor is assumed once liquid fraction >=50%.
- No auxiliary/backup heater modeled -- solar fraction here is the fraction of ideal 45 C demand met by solar+PCM alone, stricter than a real installed system with backup heating.
- No active high-temperature safety shield/bypass modeled -- see the robustness section's temperature-violation probability above.


---

## Regime 3 — semi-arid interior / Coimbatore-Tiruppur-like (22 pts)

### Regime
- Population covered: 22 points, 10,252,760 people
- State: Tamil Nadu | Medoid weather file: `data/weather/weather_regime_tamilnadu_cluster3_hourly.csv`
- Elevation: flat 150 m approximation (Objective 1 limitation, carried forward unchanged)
- Member-point robustness: NOT run (medoid-only for sub-daily/hourly shape; the annual weather magnitude below is now a real 10-year historical ensemble, not a noise proxy — see Caveats)

### Climate
- Tm_target_C (Objective 1, climate/delivery-anchored): 57.0
- Mains/inlet water temperature (population-weighted regime mean): 25.79 C
- L_required (Objective 1 sizing target): 304.1 kJ/kg
- Demand scenario: 300 L/day canonical dual-peak draw (`data/demand/demand_profile_tamilnadu.csv`)

### PCM shortlist (Objective 1, this regime)
  1. n-Octacosane (C28)
  2. PureTemp 58
  3. n-Hexacosane (C26)
  -> Plain tank (no PCM) selected instead of all 3 shortlisted candidates (see Decision below)

### Selected design
- **Plain sensible-water tank — no PCM capsules.**
- Flow rate: 0.0185 kg/s (permitted range 0.010-0.050 kg/s)

### Performance (simulator-confirmed, sim_v1_tamilnadu)
- Useful annual energy: 1816.5 kWh/year
- Solar fraction: 54.42%
- Delivery-temperature hours (>= 45 C): 4250
- Unmet energy: 1118.0 kWh/year
- Pump energy: 0.0000 Wh/year
- Constraint margin (temperature): 4.63 C below the tightest safety limit

### Robustness (120 Monte Carlo draws — PCM latent heat, two-level weather noise [annual scale/offset + per-hour jitter], demand volume/timing, mains temperature)
- P(meets annual demand, solar_fraction>=50%): 95.0%
- P(meets delivery temperature, solar_fraction>=45%): 100.0%
- P(any safety-temperature violation): 20.8%
- P(exceeds max safe temperature limit): 20.8%
- Useful energy 5th-50th-95th percentile: [1715.6, 1809.6, 1919.6] kWh
- Solar fraction 5th-95th percentile: [50.2%, 63.3%]
- Max water temperature 95th percentile: 77.1 C
- **Framework rule (P(demand)>=75% and P(temp-safe)>=95%): NOT ROBUST BY THE FRAMEWORK RULE (report as caveat, not hidden)**

### Surrogate QA
- Hold-out RMSE (useful_energy_kWh, ExtraTrees, all regimes pooled): 0.708 kWh
- Surrogate-vs-simulator error for this selected design: 0.043%

### Decision
- Best PCM found in this regime's search reached 1816.5 kWh vs plain tank's 1816.5 kWh — within the pre-declared 5% Pareto tolerance, so the selection rule's next tie-breaker (minimize PCM mass, then pump energy, then capsule count) picked the zero-mass plain tank. See `docs_objective2/08_PHASE7_OPTIMIZATION.md` for the full comparison.
- Selection-rule pool size (candidates within 5% of best): 5

### Caveats
- The robustness section's annual GHI/temperature variability is drawn from Objective 1's real 10-year (2016-2025) daily weather archive for this regime (src/robustness/weather_ensemble.py) -- a genuine historical-year ensemble, not an assumed range. The within-year HOURLY shape still comes from a single medoid year plus synthetic per-hour jitter (no member-point/multi-year hourly data was pulled for this project, 40-hr cut list).
- Melting treated as a narrow +/-1 K band around a single reported Tm_C (no measured solidus/liquidus interval in the PCM database).
- Liquid natural convection inside the capsule is not resolved -- a fixed x2 effective-conductivity enhancement factor is assumed once liquid fraction >=50%.
- No auxiliary/backup heater modeled -- solar fraction here is the fraction of ideal 45 C demand met by solar+PCM alone, stricter than a real installed system with backup heating.
- No active high-temperature safety shield/bypass modeled -- see the robustness section's temperature-violation probability above.


---

## Regime 4 — high-humidity / highest HSI (22 pts)

### Regime
- Population covered: 22 points, 10,445,170 people
- State: Tamil Nadu | Medoid weather file: `data/weather/weather_regime_tamilnadu_cluster4_hourly.csv`
- Elevation: flat 150 m approximation (Objective 1 limitation, carried forward unchanged)
- Member-point robustness: NOT run (medoid-only for sub-daily/hourly shape; the annual weather magnitude below is now a real 10-year historical ensemble, not a noise proxy — see Caveats)

### Climate
- Tm_target_C (Objective 1, climate/delivery-anchored): 57.0
- Mains/inlet water temperature (population-weighted regime mean): 24.04 C
- L_required (Objective 1 sizing target): 326.0 kJ/kg
- Demand scenario: 300 L/day canonical dual-peak draw (`data/demand/demand_profile_tamilnadu.csv`)

### PCM shortlist (Objective 1, this regime)
  1. n-Octacosane (C28) <- SELECTED
  2. RT64HC
  3. n-Hexacosane (C26)

### Selected design
- PCM: **n-Octacosane (C28)** (Tm=61.6 C, latent heat=253.0 kJ/kg, conductivity=0.2665 W/mK)
- Capsule shape/arrangement: sphere, staggered (frozen for all states)
- Capsule diameter: 0.0406 m (max PCM conduction distance = 0.0203 m)
- Capsule count: 17
- PCM mass: 0.544 kg
- Flow rate: 0.0105 kg/s (permitted range 0.010-0.050 kg/s)

### Performance (simulator-confirmed, sim_v1_tamilnadu)
- Useful annual energy: 1622.9 kWh/year
- Solar fraction: 50.96%
- Delivery-temperature hours (>= 45 C): 3403
- Unmet energy: 1312.4 kWh/year
- Pump energy: 0.0000 Wh/year
- Constraint margin (temperature): 3.25 C below the tightest safety limit

### Robustness (120 Monte Carlo draws — PCM latent heat, two-level weather noise [annual scale/offset + per-hour jitter], demand volume/timing, mains temperature)
- P(meets annual demand, solar_fraction>=50%): 69.2%
- P(meets delivery temperature, solar_fraction>=45%): 100.0%
- P(any safety-temperature violation): 59.2%
- P(exceeds max safe temperature limit): 59.2%
- Useful energy 5th-50th-95th percentile: [1530.9, 1615.6, 1702.6] kWh
- Solar fraction 5th-95th percentile: [46.7%, 58.9%]
- Max water temperature 95th percentile: 73.8 C
- **Framework rule (P(demand)>=75% and P(temp-safe)>=95%): NOT ROBUST BY THE FRAMEWORK RULE (report as caveat, not hidden)**

### Surrogate QA
- Hold-out RMSE (useful_energy_kWh, ExtraTrees, all regimes pooled): 0.708 kWh
- Surrogate-vs-simulator error for this selected design: 0.001%

### Decision
- This PCM's best found design reached the regime's own best useful-energy value (1623.5 kWh), winning outright before any tolerance tie-break was needed.
- Selection-rule pool size (candidates within 5% of best): 15

### Caveats
- The robustness section's annual GHI/temperature variability is drawn from Objective 1's real 10-year (2016-2025) daily weather archive for this regime (src/robustness/weather_ensemble.py) -- a genuine historical-year ensemble, not an assumed range. The within-year HOURLY shape still comes from a single medoid year plus synthetic per-hour jitter (no member-point/multi-year hourly data was pulled for this project, 40-hr cut list).
- Melting treated as a narrow +/-1 K band around a single reported Tm_C (no measured solidus/liquidus interval in the PCM database).
- Liquid natural convection inside the capsule is not resolved -- a fixed x2 effective-conductivity enhancement factor is assumed once liquid fraction >=50%.
- No auxiliary/backup heater modeled -- solar fraction here is the fraction of ideal 45 C demand met by solar+PCM alone, stricter than a real installed system with backup heating.
- No active high-temperature safety shield/bypass modeled -- see the robustness section's temperature-violation probability above.
- n-Octacosane (C28) property provenance: check `any_property_imputed` in `data/objective1/pcm_database_tamilnadu.csv` for which fields are manufacturer-measured vs MICE/RF-imputed.
