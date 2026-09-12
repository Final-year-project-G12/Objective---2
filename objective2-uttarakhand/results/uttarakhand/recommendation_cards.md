# Objective 2 Recommendation Cards — uttarakhand

Simulator version: `sim_v1_uttarakhand`. Generated from Phases 1-8 results; nothing below is a surrogate-only estimate -- every performance number is simulator-confirmed (Phase 7) and every robustness probability comes from real Monte Carlo simulator re-runs (Phase 8), not the surrogate.
## Regime 0 — regime 0 (15 pts, Ta_mean~21.4C, GHI~4.80 kWh/m2/day)

### Regime
- Population covered: 15 points, 2,729,553 people
- State: Uttarakhand | Medoid weather file: `data/weather/weather_regime_uttarakhand_cluster0_hourly.csv`
- Elevation: no dedicated elevation script; three inconsistent values coexist (0m in 00b_build_suntimes.py, flat 1200m DEFAULT_ALT_M in 02_combine, pressure-derived elev_proxy in 04b) (Objective 1 limitation, carried forward unchanged)
- Member-point robustness: NOT run (medoid-only for sub-daily/hourly shape; the annual weather magnitude below is now a real 10-year historical ensemble, not a noise proxy — see Caveats)

### Climate
- Tm_target_C (Objective 1, climate/delivery-anchored): 57.0
- Mains/inlet water temperature (population-weighted regime mean): 19.40 C
- L_required (Objective 1 sizing target): 128.0 kJ/kg
- Demand scenario: 300 L/day canonical dual-peak draw (`data/demand/demand_profile_uttarakhand.csv`)

### PCM shortlist (Objective 1, this regime)
  1. PureTemp 58
  2. n-Octacosane (C28)
  3. PlusICE A58
  -> Plain tank (no PCM) selected instead of all 3 shortlisted candidates (see Decision below)

### Selected design
- **Plain sensible-water tank — no PCM capsules.**
- Flow rate: 0.0119 kg/s (permitted range 0.010-0.050 kg/s)

### Performance (simulator-confirmed, sim_v1_uttarakhand)
- Useful annual energy: 1675.3 kWh/year
- Solar fraction: 40.71%
- Delivery-temperature hours (>= 45 C): 1148
- Unmet energy: 2316.5 kWh/year
- Pump energy: 0.0000 Wh/year
- Constraint margin (temperature): -0.14 C below the tightest safety limit

### Robustness (120 Monte Carlo draws — PCM latent heat, two-level weather noise [annual scale/offset + per-hour jitter], demand volume/timing, mains temperature)
- P(meets annual demand, solar_fraction>=50%): 0.0%
- P(meets delivery temperature, solar_fraction>=45%): 23.3%
- P(any safety-temperature violation): 55.8%
- P(exceeds max safe temperature limit): 55.8%
- Useful energy 5th-50th-95th percentile: [1576.5, 1678.5, 1755.4] kWh
- Solar fraction 5th-95th percentile: [36.6%, 48.1%]
- Max water temperature 95th percentile: 79.6 C
- **Framework rule (P(demand)>=75% and P(temp-safe)>=95%): NOT ROBUST BY THE FRAMEWORK RULE (report as caveat, not hidden)**

### Surrogate QA
- Hold-out RMSE (useful_energy_kWh, ExtraTrees, all regimes pooled): 0.540 kWh
- Surrogate-vs-simulator error for this selected design: 0.028%

### Decision
- Best PCM found in this regime's search reached 1676.0 kWh vs plain tank's 1675.3 kWh — within the pre-declared 5% Pareto tolerance, so the selection rule's next tie-breaker (minimize PCM mass, then pump energy, then capsule count) picked the zero-mass plain tank. See `docs_objective2/08_PHASE7_OPTIMIZATION.md` for the full comparison.
- Selection-rule pool size (candidates within 5% of best): 20

### Caveats
- The robustness section's annual GHI/temperature variability is drawn from Objective 1's real 10-year (2016-2025) daily weather archive for this regime (src/robustness/weather_ensemble.py) -- a genuine historical-year ensemble, not an assumed range. The within-year HOURLY shape still comes from a single medoid year plus synthetic per-hour jitter (no member-point/multi-year hourly data was pulled for this project, 40-hr cut list).
- Melting treated as a narrow +/-1 K band around a single reported Tm_C (no measured solidus/liquidus interval in the PCM database).
- Liquid natural convection inside the capsule is not resolved -- a fixed x2 effective-conductivity enhancement factor is assumed once liquid fraction >=50%.
- No auxiliary/backup heater modeled -- solar fraction here is the fraction of ideal 45 C demand met by solar+PCM alone, stricter than a real installed system with backup heating.
- No active high-temperature safety shield/bypass modeled -- see the robustness section's temperature-violation probability above.


---

## Regime 1 — regime 1 (9 pts, Ta_mean~19.0C, GHI~4.90 kWh/m2/day)

### Regime
- Population covered: 9 points, 2,451,044 people
- State: Uttarakhand | Medoid weather file: `data/weather/weather_regime_uttarakhand_cluster1_hourly.csv`
- Elevation: no dedicated elevation script; three inconsistent values coexist (0m in 00b_build_suntimes.py, flat 1200m DEFAULT_ALT_M in 02_combine, pressure-derived elev_proxy in 04b) (Objective 1 limitation, carried forward unchanged)
- Member-point robustness: NOT run (medoid-only for sub-daily/hourly shape; the annual weather magnitude below is now a real 10-year historical ensemble, not a noise proxy — see Caveats)

### Climate
- Tm_target_C (Objective 1, climate/delivery-anchored): 57.0
- Mains/inlet water temperature (population-weighted regime mean): 17.00 C
- L_required (Objective 1 sizing target): 138.0 kJ/kg
- Demand scenario: 300 L/day canonical dual-peak draw (`data/demand/demand_profile_uttarakhand.csv`)

### PCM shortlist (Objective 1, this regime)
  1. PureTemp 58
  2. Palmitic-stearic acid/Expanded graphite
  3. n-Octacosane (C28)
  -> Plain tank (no PCM) selected instead of all 3 shortlisted candidates (see Decision below)

### Selected design
- **Plain sensible-water tank — no PCM capsules.**
- Flow rate: 0.0293 kg/s (permitted range 0.010-0.050 kg/s)

### Performance (simulator-confirmed, sim_v1_uttarakhand)
- Useful annual energy: 1625.3 kWh/year
- Solar fraction: 37.38%
- Delivery-temperature hours (>= 45 C): 767
- Unmet energy: 2638.2 kWh/year
- Pump energy: 0.0000 Wh/year
- Constraint margin (temperature): 4.80 C below the tightest safety limit

### Robustness (120 Monte Carlo draws — PCM latent heat, two-level weather noise [annual scale/offset + per-hour jitter], demand volume/timing, mains temperature)
- P(meets annual demand, solar_fraction>=50%): 0.0%
- P(meets delivery temperature, solar_fraction>=45%): 1.7%
- P(any safety-temperature violation): 8.3%
- P(exceeds max safe temperature limit): 8.3%
- Useful energy 5th-50th-95th percentile: [1522.6, 1629.0, 1727.5] kWh
- Solar fraction 5th-95th percentile: [32.9%, 44.2%]
- Max water temperature 95th percentile: 76.1 C
- **Framework rule (P(demand)>=75% and P(temp-safe)>=95%): NOT ROBUST BY THE FRAMEWORK RULE (report as caveat, not hidden)**

### Surrogate QA
- Hold-out RMSE (useful_energy_kWh, ExtraTrees, all regimes pooled): 0.540 kWh
- Surrogate-vs-simulator error for this selected design: 0.013%

### Decision
- Best PCM found in this regime's search reached 1625.3 kWh vs plain tank's 1625.3 kWh — within the pre-declared 5% Pareto tolerance, so the selection rule's next tie-breaker (minimize PCM mass, then pump energy, then capsule count) picked the zero-mass plain tank. See `docs_objective2/08_PHASE7_OPTIMIZATION.md` for the full comparison.
- Selection-rule pool size (candidates within 5% of best): 5

### Caveats
- The robustness section's annual GHI/temperature variability is drawn from Objective 1's real 10-year (2016-2025) daily weather archive for this regime (src/robustness/weather_ensemble.py) -- a genuine historical-year ensemble, not an assumed range. The within-year HOURLY shape still comes from a single medoid year plus synthetic per-hour jitter (no member-point/multi-year hourly data was pulled for this project, 40-hr cut list).
- Melting treated as a narrow +/-1 K band around a single reported Tm_C (no measured solidus/liquidus interval in the PCM database).
- Liquid natural convection inside the capsule is not resolved -- a fixed x2 effective-conductivity enhancement factor is assumed once liquid fraction >=50%.
- No auxiliary/backup heater modeled -- solar fraction here is the fraction of ideal 45 C demand met by solar+PCM alone, stricter than a real installed system with backup heating.
- No active high-temperature safety shield/bypass modeled -- see the robustness section's temperature-violation probability above.


---

## Regime 2 — regime 2 (3 pts — SMALL SAMPLE, Ta_mean~9.4C, GHI~4.57 kWh/m2/day)

### Regime
- Population covered: 3 points, 330,780 people
- State: Uttarakhand | Medoid weather file: `data/weather/weather_regime_uttarakhand_cluster2_hourly.csv`
- Elevation: no dedicated elevation script; three inconsistent values coexist (0m in 00b_build_suntimes.py, flat 1200m DEFAULT_ALT_M in 02_combine, pressure-derived elev_proxy in 04b) (Objective 1 limitation, carried forward unchanged)
- Member-point robustness: NOT run (medoid-only for sub-daily/hourly shape; the annual weather magnitude below is now a real 10-year historical ensemble, not a noise proxy — see Caveats)

### Climate
- Tm_target_C (Objective 1, climate/delivery-anchored): 57.0
- Mains/inlet water temperature (population-weighted regime mean): 7.40 C
- L_required (Objective 1 sizing target): 178.0 kJ/kg
- Demand scenario: 300 L/day canonical dual-peak draw (`data/demand/demand_profile_uttarakhand.csv`)

### PCM shortlist (Objective 1, this regime)
  1. PureTemp 58 <- SELECTED
  2. n-Octacosane (C28)
  3. PlusICE A58

### Selected design
- PCM: **PureTemp 58** (Tm=58.0 C, latent heat=225.0 kJ/kg, conductivity=0.2 W/mK)
- Capsule shape/arrangement: sphere, staggered (frozen for all states)
- Capsule diameter: 0.0438 m (max PCM conduction distance = 0.0219 m)
- Capsule count: 10
- PCM mass: 0.392 kg
- Flow rate: 0.0116 kg/s (permitted range 0.010-0.050 kg/s)

### Performance (simulator-confirmed, sim_v1_uttarakhand)
- Useful annual energy: 1527.2 kWh/year
- Solar fraction: 28.04%
- Delivery-temperature hours (>= 45 C): 78
- Unmet energy: 3913.6 kWh/year
- Pump energy: 0.0000 Wh/year
- Constraint margin (temperature): 7.97 C below the tightest safety limit

### Robustness (120 Monte Carlo draws — PCM latent heat, two-level weather noise [annual scale/offset + per-hour jitter], demand volume/timing, mains temperature)
- P(meets annual demand, solar_fraction>=50%): 0.0%
- P(meets delivery temperature, solar_fraction>=45%): 0.0%
- P(any safety-temperature violation): 0.0%
- P(exceeds max safe temperature limit): 0.0%
- Useful energy 5th-50th-95th percentile: [1435.4, 1514.6, 1650.1] kWh
- Solar fraction 5th-95th percentile: [24.2%, 33.5%]
- Max water temperature 95th percentile: 62.1 C
- **Framework rule (P(demand)>=75% and P(temp-safe)>=95%): NOT ROBUST BY THE FRAMEWORK RULE (report as caveat, not hidden)**

### Surrogate QA
- Hold-out RMSE (useful_energy_kWh, ExtraTrees, all regimes pooled): 0.540 kWh
- Surrogate-vs-simulator error for this selected design: 0.010%

### Decision
- This PCM's best found design reached the regime's own best useful-energy value (1527.7 kWh), winning outright before any tolerance tie-break was needed.
- Selection-rule pool size (candidates within 5% of best): 20

### Caveats
- The robustness section's annual GHI/temperature variability is drawn from Objective 1's real 10-year (2016-2025) daily weather archive for this regime (src/robustness/weather_ensemble.py) -- a genuine historical-year ensemble, not an assumed range. The within-year HOURLY shape still comes from a single medoid year plus synthetic per-hour jitter (no member-point/multi-year hourly data was pulled for this project, 40-hr cut list).
- Melting treated as a narrow +/-1 K band around a single reported Tm_C (no measured solidus/liquidus interval in the PCM database).
- Liquid natural convection inside the capsule is not resolved -- a fixed x2 effective-conductivity enhancement factor is assumed once liquid fraction >=50%.
- No auxiliary/backup heater modeled -- solar fraction here is the fraction of ideal 45 C demand met by solar+PCM alone, stricter than a real installed system with backup heating.
- No active high-temperature safety shield/bypass modeled -- see the robustness section's temperature-violation probability above.
- PureTemp 58 property provenance: check `any_property_imputed` in `data/objective1/pcm_database_uttarakhand.csv` for which fields are manufacturer-measured vs MICE/RF-imputed.


---

## Regime 3 — regime 3 (10 pts, Ta_mean~23.8C, GHI~4.75 kWh/m2/day)

### Regime
- Population covered: 10 points, 3,700,876 people
- State: Uttarakhand | Medoid weather file: `data/weather/weather_regime_uttarakhand_cluster3_hourly.csv`
- Elevation: no dedicated elevation script; three inconsistent values coexist (0m in 00b_build_suntimes.py, flat 1200m DEFAULT_ALT_M in 02_combine, pressure-derived elev_proxy in 04b) (Objective 1 limitation, carried forward unchanged)
- Member-point robustness: NOT run (medoid-only for sub-daily/hourly shape; the annual weather magnitude below is now a real 10-year historical ensemble, not a noise proxy — see Caveats)

### Climate
- Tm_target_C (Objective 1, climate/delivery-anchored): 57.0
- Mains/inlet water temperature (population-weighted regime mean): 21.80 C
- L_required (Objective 1 sizing target): 118.0 kJ/kg
- Demand scenario: 300 L/day canonical dual-peak draw (`data/demand/demand_profile_uttarakhand.csv`)

### PCM shortlist (Objective 1, this regime)
  1. PureTemp 58
  2. Palmitic-stearic acid/Expanded graphite
  3. n-Octacosane (C28)
  -> Plain tank (no PCM) selected instead of all 3 shortlisted candidates (see Decision below)

### Selected design
- **Plain sensible-water tank — no PCM capsules.**
- Flow rate: 0.0396 kg/s (permitted range 0.010-0.050 kg/s)

### Performance (simulator-confirmed, sim_v1_uttarakhand)
- Useful annual energy: 1563.8 kWh/year
- Solar fraction: 40.75%
- Delivery-temperature hours (>= 45 C): 1505
- Unmet energy: 2133.2 kWh/year
- Pump energy: 0.0000 Wh/year
- Constraint margin (temperature): 2.04 C below the tightest safety limit

### Robustness (120 Monte Carlo draws — PCM latent heat, two-level weather noise [annual scale/offset + per-hour jitter], demand volume/timing, mains temperature)
- P(meets annual demand, solar_fraction>=50%): 0.0%
- P(meets delivery temperature, solar_fraction>=45%): 22.5%
- P(any safety-temperature violation): 35.8%
- P(exceeds max safe temperature limit): 35.8%
- Useful energy 5th-50th-95th percentile: [1479.9, 1557.8, 1659.1] kWh
- Solar fraction 5th-95th percentile: [36.2%, 46.8%]
- Max water temperature 95th percentile: 78.9 C
- **Framework rule (P(demand)>=75% and P(temp-safe)>=95%): NOT ROBUST BY THE FRAMEWORK RULE (report as caveat, not hidden)**

### Surrogate QA
- Hold-out RMSE (useful_energy_kWh, ExtraTrees, all regimes pooled): 0.540 kWh
- Surrogate-vs-simulator error for this selected design: 0.045%

### Decision
- Best PCM found in this regime's search reached 1563.8 kWh vs plain tank's 1563.8 kWh — within the pre-declared 5% Pareto tolerance, so the selection rule's next tie-breaker (minimize PCM mass, then pump energy, then capsule count) picked the zero-mass plain tank. See `docs_objective2/08_PHASE7_OPTIMIZATION.md` for the full comparison.
- Selection-rule pool size (candidates within 5% of best): 5

### Caveats
- The robustness section's annual GHI/temperature variability is drawn from Objective 1's real 10-year (2016-2025) daily weather archive for this regime (src/robustness/weather_ensemble.py) -- a genuine historical-year ensemble, not an assumed range. The within-year HOURLY shape still comes from a single medoid year plus synthetic per-hour jitter (no member-point/multi-year hourly data was pulled for this project, 40-hr cut list).
- Melting treated as a narrow +/-1 K band around a single reported Tm_C (no measured solidus/liquidus interval in the PCM database).
- Liquid natural convection inside the capsule is not resolved -- a fixed x2 effective-conductivity enhancement factor is assumed once liquid fraction >=50%.
- No auxiliary/backup heater modeled -- solar fraction here is the fraction of ideal 45 C demand met by solar+PCM alone, stricter than a real installed system with backup heating.
- No active high-temperature safety shield/bypass modeled -- see the robustness section's temperature-violation probability above.


---

## Regime 4 — regime 4 (8 pts, Ta_mean~18.8C, GHI~4.93 kWh/m2/day)

### Regime
- Population covered: 8 points, 1,263,461 people
- State: Uttarakhand | Medoid weather file: `data/weather/weather_regime_uttarakhand_cluster4_hourly.csv`
- Elevation: no dedicated elevation script; three inconsistent values coexist (0m in 00b_build_suntimes.py, flat 1200m DEFAULT_ALT_M in 02_combine, pressure-derived elev_proxy in 04b) (Objective 1 limitation, carried forward unchanged)
- Member-point robustness: NOT run (medoid-only for sub-daily/hourly shape; the annual weather magnitude below is now a real 10-year historical ensemble, not a noise proxy — see Caveats)

### Climate
- Tm_target_C (Objective 1, climate/delivery-anchored): 57.0
- Mains/inlet water temperature (population-weighted regime mean): 16.80 C
- L_required (Objective 1 sizing target): 139.0 kJ/kg
- Demand scenario: 300 L/day canonical dual-peak draw (`data/demand/demand_profile_uttarakhand.csv`)

### PCM shortlist (Objective 1, this regime)
  1. PureTemp 58
  2. n-Octacosane (C28)
  3. PlusICE A58
  -> Plain tank (no PCM) selected instead of all 3 shortlisted candidates (see Decision below)

### Selected design
- **Plain sensible-water tank — no PCM capsules.**
- Flow rate: 0.0175 kg/s (permitted range 0.010-0.050 kg/s)

### Performance (simulator-confirmed, sim_v1_uttarakhand)
- Useful annual energy: 1624.0 kWh/year
- Solar fraction: 37.20%
- Delivery-temperature hours (>= 45 C): 795
- Unmet energy: 2661.9 kWh/year
- Pump energy: 0.0000 Wh/year
- Constraint margin (temperature): 5.49 C below the tightest safety limit

### Robustness (120 Monte Carlo draws — PCM latent heat, two-level weather noise [annual scale/offset + per-hour jitter], demand volume/timing, mains temperature)
- P(meets annual demand, solar_fraction>=50%): 0.0%
- P(meets delivery temperature, solar_fraction>=45%): 2.5%
- P(any safety-temperature violation): 16.7%
- P(exceeds max safe temperature limit): 16.7%
- Useful energy 5th-50th-95th percentile: [1541.9, 1630.7, 1718.5] kWh
- Solar fraction 5th-95th percentile: [32.4%, 43.9%]
- Max water temperature 95th percentile: 76.6 C
- **Framework rule (P(demand)>=75% and P(temp-safe)>=95%): NOT ROBUST BY THE FRAMEWORK RULE (report as caveat, not hidden)**

### Surrogate QA
- Hold-out RMSE (useful_energy_kWh, ExtraTrees, all regimes pooled): 0.540 kWh
- Surrogate-vs-simulator error for this selected design: 0.019%

### Decision
- Best PCM found in this regime's search reached 1624.0 kWh vs plain tank's 1624.0 kWh — within the pre-declared 5% Pareto tolerance, so the selection rule's next tie-breaker (minimize PCM mass, then pump energy, then capsule count) picked the zero-mass plain tank. See `docs_objective2/08_PHASE7_OPTIMIZATION.md` for the full comparison.
- Selection-rule pool size (candidates within 5% of best): 5

### Caveats
- The robustness section's annual GHI/temperature variability is drawn from Objective 1's real 10-year (2016-2025) daily weather archive for this regime (src/robustness/weather_ensemble.py) -- a genuine historical-year ensemble, not an assumed range. The within-year HOURLY shape still comes from a single medoid year plus synthetic per-hour jitter (no member-point/multi-year hourly data was pulled for this project, 40-hr cut list).
- Melting treated as a narrow +/-1 K band around a single reported Tm_C (no measured solidus/liquidus interval in the PCM database).
- Liquid natural convection inside the capsule is not resolved -- a fixed x2 effective-conductivity enhancement factor is assumed once liquid fraction >=50%.
- No auxiliary/backup heater modeled -- solar fraction here is the fraction of ideal 45 C demand met by solar+PCM alone, stricter than a real installed system with backup heating.
- No active high-temperature safety shield/bypass modeled -- see the robustness section's temperature-violation probability above.
