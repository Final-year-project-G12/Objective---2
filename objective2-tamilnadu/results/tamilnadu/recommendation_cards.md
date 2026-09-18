# Objective 2 Recommendation Cards — tamilnadu

Simulator version: `sim_v2_tamilnadu` (2026-09-17 — arrangement restored + fresh Objective 1 data, K=5->K=3 regimes; see docs_objective2/17_ARRANGEMENT_RESTORATION.md and 16_OBJECTIVE1_DATA_REFRESH.md). Generated from Phases 1-8 results; nothing below is a surrogate-only estimate -- every performance number is simulator-confirmed (Phase 7) and every robustness probability comes from real Monte Carlo simulator re-runs (Phase 8), not the surrogate.
## Regime 0 — coastal/interior lowland (46 pts, medoid elev 156 m)

### Regime
- Population covered: 46 points, 20,468,850 people
- State: Tamil Nadu | Medoid weather file: `data/weather/weather_regime_tamilnadu_cluster0_hourly.csv`
- Elevation: 155.7 m (real elevation via Objective 1's 00c_attach_elevation.py, 2026-09-17 refresh — supersedes the earlier flat 150 m approximation)
- Member-point robustness: NOT run (medoid-only for sub-daily/hourly shape; the annual weather magnitude below is now a real 10-year historical ensemble, not a noise proxy — see Caveats)

### Climate
- Tm_target_C (Objective 1's own climate/delivery-anchored formula — Objective 2 searches geometry/flow for Objective 1's actual shortlisted PCMs, it does not re-derive this target; see docs_objective2/18_OBJECTIVE1_SHORTLIST_RESTORED.md): 67.0
- Mains/inlet water temperature (population-weighted regime mean): 28.46 C
- L_required (Objective 1 sizing target): 406.0 kJ/kg
- Demand scenario: 300 L/day canonical dual-peak draw (`data/demand/demand_profile_tamilnadu.csv`)

### PCM shortlist (Objective 1's actual Top-3 MCDM consensus shortlist for this regime — Objective 2 searches geometry/arrangement/flow for these candidates only; see docs_objective2/18_OBJECTIVE1_SHORTLIST_RESTORED.md)
  1. RT57HC <- SELECTED
  2. n-Hexacosane (C26)
  3. PureTemp 58

### Selected design
- PCM: **RT57HC** (Tm=56.5 C, latent heat=240.0 kJ/kg, conductivity=0.239 W/mK)
- Capsule shape: sphere (frozen for all states)
- **Selected arrangement: radial** (searched 2026-09-17 — single-layer/staggered/radial were all compared; previously frozen to staggered-only)
- Arrangement rationale: arrangements tied within noise in this regime (margin -0.00% is inside the 0.03% surrogate-vs-sim noise band) -- arrangement not decisive here; next-best was single-layer
- Capsule diameter: 0.0420 m (max PCM conduction distance = 0.0210 m)
- Capsule count: 20
- PCM mass: 0.700 kg
- Flow rate: 0.0274 kg/s (permitted range 0.010-0.050 kg/s)

### Performance (simulator-confirmed, sim_v2_tamilnadu)
- Useful annual energy: 1756.3 kWh/year
- Solar fraction: 56.09%
- Delivery-temperature hours (>= 45 C): 4606
- Unmet energy: 927.1 kWh/year
- Pump energy: 0.0002 Wh/year
- Constraint margin (temperature): -6.86 C below the tightest safety limit

### Robustness (120 Monte Carlo draws — PCM latent heat, two-level weather noise [annual scale/offset + per-hour jitter], demand volume/timing, mains temperature)
- P(meets annual demand, solar_fraction>=50%): 100.0%
- P(meets delivery temperature, solar_fraction>=45%): 100.0%
- P(any safety-temperature violation): 100.0%
- P(exceeds max safe temperature limit): 100.0%
- Useful energy 5th-50th-95th percentile: [1662.7, 1755.5, 1874.0] kWh
- Solar fraction 5th-95th percentile: [51.2%, 66.1%]
- Max water temperature 95th percentile: 79.6 C
- **Framework rule (P(demand)>=75% and P(temp-safe)>=95%): NOT ROBUST BY THE FRAMEWORK RULE (report as caveat, not hidden)**

### Surrogate QA
- Hold-out RMSE (useful_energy_kWh, ExtraTrees, all regimes pooled): 0.726 kWh
- Surrogate-vs-simulator error for this selected design: 0.017%

### Decision
- This design reached the regime's own best useful-energy value (1756.4 kWh) outright.
- Selection-rule pool size (candidates within 5% of best): 60

### Caveats
- The robustness section's annual GHI/temperature variability is drawn from Objective 1's real 10-year (2016-2025) daily weather archive for this regime (src/robustness/weather_ensemble.py) -- a genuine historical-year ensemble, not an assumed range. The within-year HOURLY shape still comes from a single medoid year plus synthetic per-hour jitter (no member-point/multi-year hourly data was pulled for this project, 40-hr cut list).
- Melting treated as a narrow +/-1 K band around a single reported Tm_C (no measured solidus/liquidus interval in the PCM database).
- Liquid natural convection inside the capsule is not resolved -- a fixed x2 effective-conductivity enhancement factor is assumed once liquid fraction >=50%.
- No auxiliary/backup heater modeled -- solar fraction here is the fraction of ideal 45 C demand met by solar+PCM alone, stricter than a real installed system with backup heating.
- No active high-temperature safety shield/bypass modeled -- see the robustness section's temperature-violation probability above.
- RT57HC property provenance: check `any_property_imputed` in `data/objective1/pcm_database_tamilnadu.csv` for which fields are manufacturer-measured vs MICE/RF-imputed.


---

## Regime 1 — elevated/hill interior, Nilgiris-adjacent (41 pts, medoid elev 627 m)

### Regime
- Population covered: 41 points, 20,422,160 people
- State: Tamil Nadu | Medoid weather file: `data/weather/weather_regime_tamilnadu_cluster1_hourly.csv`
- Elevation: 626.9 m (real elevation via Objective 1's 00c_attach_elevation.py, 2026-09-17 refresh — supersedes the earlier flat 150 m approximation)
- Member-point robustness: NOT run (medoid-only for sub-daily/hourly shape; the annual weather magnitude below is now a real 10-year historical ensemble, not a noise proxy — see Caveats)

### Climate
- Tm_target_C (Objective 1's own climate/delivery-anchored formula — Objective 2 searches geometry/flow for Objective 1's actual shortlisted PCMs, it does not re-derive this target; see docs_objective2/18_OBJECTIVE1_SHORTLIST_RESTORED.md): 67.0
- Mains/inlet water temperature (population-weighted regime mean): 23.97 C
- L_required (Objective 1 sizing target): 438.2 kJ/kg
- Demand scenario: 300 L/day canonical dual-peak draw (`data/demand/demand_profile_tamilnadu.csv`)

### PCM shortlist (Objective 1's actual Top-3 MCDM consensus shortlist for this regime — Objective 2 searches geometry/arrangement/flow for these candidates only; see docs_objective2/18_OBJECTIVE1_SHORTLIST_RESTORED.md)
  1. RT57HC
  2. n-Hexacosane (C26) <- SELECTED
  3. n-Pentacosane (C25)

### Selected design
- PCM: **n-Hexacosane (C26)** (Tm=56.5 C, latent heat=256.0 kJ/kg, conductivity=0.238 W/mK)
- Capsule shape: sphere (frozen for all states)
- **Selected arrangement: single-layer** (searched 2026-09-17 — single-layer/staggered/radial were all compared; previously frozen to staggered-only)
- Arrangement rationale: only arrangement=single-layer was simulator-confirmed for this regime/PCM pool -- no other arrangement to compare.
- Capsule diameter: 0.0440 m (max PCM conduction distance = 0.0220 m)
- Capsule count: 26
- PCM mass: 0.895 kg
- Flow rate: 0.0219 kg/s (permitted range 0.010-0.050 kg/s)

### Performance (simulator-confirmed, sim_v2_tamilnadu)
- Useful annual energy: 1623.2 kWh/year
- Solar fraction: 50.86%
- Delivery-temperature hours (>= 45 C): 3394
- Unmet energy: 1319.5 kWh/year
- Pump energy: 0.0001 Wh/year
- Constraint margin (temperature): 0.12 C below the tightest safety limit

### Robustness (120 Monte Carlo draws — PCM latent heat, two-level weather noise [annual scale/offset + per-hour jitter], demand volume/timing, mains temperature)
- P(meets annual demand, solar_fraction>=50%): 71.7%
- P(meets delivery temperature, solar_fraction>=45%): 99.2%
- P(any safety-temperature violation): 80.8%
- P(exceeds max safe temperature limit): 80.8%
- Useful energy 5th-50th-95th percentile: [1524.6, 1632.0, 1732.4] kWh
- Solar fraction 5th-95th percentile: [47.1%, 60.5%]
- Max water temperature 95th percentile: 75.7 C
- **Framework rule (P(demand)>=75% and P(temp-safe)>=95%): NOT ROBUST BY THE FRAMEWORK RULE (report as caveat, not hidden)**

### Surrogate QA
- Hold-out RMSE (useful_energy_kWh, ExtraTrees, all regimes pooled): 0.726 kWh
- Surrogate-vs-simulator error for this selected design: 0.012%

### Decision
- This design (1623.2 kWh) is 0.12% below the regime's best-found candidate (1625.2 kWh, a different design within the selection rule's pre-declared tolerance band) — it was picked by the tie-break (safety first, then pump energy, then PCM mass, then capsule count) among candidates already within tolerance of the best, not because it had the highest useful energy in the regime.
- Selection-rule pool size (candidates within 5% of best): 60

### Caveats
- The robustness section's annual GHI/temperature variability is drawn from Objective 1's real 10-year (2016-2025) daily weather archive for this regime (src/robustness/weather_ensemble.py) -- a genuine historical-year ensemble, not an assumed range. The within-year HOURLY shape still comes from a single medoid year plus synthetic per-hour jitter (no member-point/multi-year hourly data was pulled for this project, 40-hr cut list).
- Melting treated as a narrow +/-1 K band around a single reported Tm_C (no measured solidus/liquidus interval in the PCM database).
- Liquid natural convection inside the capsule is not resolved -- a fixed x2 effective-conductivity enhancement factor is assumed once liquid fraction >=50%.
- No auxiliary/backup heater modeled -- solar fraction here is the fraction of ideal 45 C demand met by solar+PCM alone, stricter than a real installed system with backup heating.
- No active high-temperature safety shield/bypass modeled -- see the robustness section's temperature-violation probability above.
- n-Hexacosane (C26) property provenance: check `any_property_imputed` in `data/objective1/pcm_database_tamilnadu.csv` for which fields are manufacturer-measured vs MICE/RF-imputed.


---

## Regime 2 — coastal metro lowland, largest population (46 pts, medoid elev 44 m)

### Regime
- Population covered: 46 points, 30,335,760 people
- State: Tamil Nadu | Medoid weather file: `data/weather/weather_regime_tamilnadu_cluster2_hourly.csv`
- Elevation: 44.3 m (real elevation via Objective 1's 00c_attach_elevation.py, 2026-09-17 refresh — supersedes the earlier flat 150 m approximation)
- Member-point robustness: NOT run (medoid-only for sub-daily/hourly shape; the annual weather magnitude below is now a real 10-year historical ensemble, not a noise proxy — see Caveats)

### Climate
- Tm_target_C (Objective 1's own climate/delivery-anchored formula — Objective 2 searches geometry/flow for Objective 1's actual shortlisted PCMs, it does not re-derive this target; see docs_objective2/18_OBJECTIVE1_SHORTLIST_RESTORED.md): 67.0
- Mains/inlet water temperature (population-weighted regime mean): 27.77 C
- L_required (Objective 1 sizing target): 405.5 kJ/kg
- Demand scenario: 300 L/day canonical dual-peak draw (`data/demand/demand_profile_tamilnadu.csv`)

### PCM shortlist (Objective 1's actual Top-3 MCDM consensus shortlist for this regime — Objective 2 searches geometry/arrangement/flow for these candidates only; see docs_objective2/18_OBJECTIVE1_SHORTLIST_RESTORED.md)
  1. RT57HC
  2. n-Pentacosane (C25) <- SELECTED
  3. n-Hexacosane (C26)

### Selected design
- PCM: **n-Pentacosane (C25)** (Tm=54.0 C, latent heat=238.0 kJ/kg, conductivity=0.239 W/mK)
- Capsule shape: sphere (frozen for all states)
- **Selected arrangement: single-layer** (searched 2026-09-17 — single-layer/staggered/radial were all compared; previously frozen to staggered-only)
- Arrangement rationale: arrangements tied within noise in this regime (margin -0.00% is inside the 0.03% surrogate-vs-sim noise band) -- arrangement not decisive here; next-best was radial
- Capsule diameter: 0.0459 m (max PCM conduction distance = 0.0230 m)
- Capsule count: 10
- PCM mass: 0.406 kg
- Flow rate: 0.0119 kg/s (permitted range 0.010-0.050 kg/s)

### Performance (simulator-confirmed, sim_v2_tamilnadu)
- Useful annual energy: 1634.0 kWh/year
- Solar fraction: 53.41%
- Delivery-temperature hours (>= 45 C): 4085
- Unmet energy: 1025.1 kWh/year
- Pump energy: 0.0000 Wh/year
- Constraint margin (temperature): -6.29 C below the tightest safety limit

### Robustness (120 Monte Carlo draws — PCM latent heat, two-level weather noise [annual scale/offset + per-hour jitter], demand volume/timing, mains temperature)
- P(meets annual demand, solar_fraction>=50%): 95.0%
- P(meets delivery temperature, solar_fraction>=45%): 100.0%
- P(any safety-temperature violation): 100.0%
- P(exceeds max safe temperature limit): 100.0%
- Useful energy 5th-50th-95th percentile: [1516.8, 1628.1, 1726.0] kWh
- Solar fraction 5th-95th percentile: [50.1%, 63.1%]
- Max water temperature 95th percentile: 76.4 C
- **Framework rule (P(demand)>=75% and P(temp-safe)>=95%): NOT ROBUST BY THE FRAMEWORK RULE (report as caveat, not hidden)**

### Surrogate QA
- Hold-out RMSE (useful_energy_kWh, ExtraTrees, all regimes pooled): 0.726 kWh
- Surrogate-vs-simulator error for this selected design: 0.034%

### Decision
- This design (1634.0 kWh) is 0.02% below the regime's best-found candidate (1634.3 kWh, a different design within the selection rule's pre-declared tolerance band) — it was picked by the tie-break (safety first, then pump energy, then PCM mass, then capsule count) among candidates already within tolerance of the best, not because it had the highest useful energy in the regime.
- Selection-rule pool size (candidates within 5% of best): 60

### Caveats
- The robustness section's annual GHI/temperature variability is drawn from Objective 1's real 10-year (2016-2025) daily weather archive for this regime (src/robustness/weather_ensemble.py) -- a genuine historical-year ensemble, not an assumed range. The within-year HOURLY shape still comes from a single medoid year plus synthetic per-hour jitter (no member-point/multi-year hourly data was pulled for this project, 40-hr cut list).
- Melting treated as a narrow +/-1 K band around a single reported Tm_C (no measured solidus/liquidus interval in the PCM database).
- Liquid natural convection inside the capsule is not resolved -- a fixed x2 effective-conductivity enhancement factor is assumed once liquid fraction >=50%.
- No auxiliary/backup heater modeled -- solar fraction here is the fraction of ideal 45 C demand met by solar+PCM alone, stricter than a real installed system with backup heating.
- No active high-temperature safety shield/bypass modeled -- see the robustness section's temperature-violation probability above.
- n-Pentacosane (C25) property provenance: check `any_property_imputed` in `data/objective1/pcm_database_tamilnadu.csv` for which fields are manufacturer-measured vs MICE/RF-imputed.
