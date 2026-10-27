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
  1. RT57HC
  2. n-Hexacosane (C26) <- SELECTED
  3. PureTemp 58

### Selected design
- PCM: **n-Hexacosane (C26)** (Tm=56.5 C, latent heat=256.0 kJ/kg, conductivity=0.238 W/mK)
- Capsule shape: sphere (frozen for all states)
- **Selected arrangement: radial** (searched 2026-09-17 — single-layer/staggered/radial were all compared; previously frozen to staggered-only)
- Arrangement rationale: arrangement radial won by -1.67% over next-best arrangement single-layer (surrogate-vs-sim noise band: 0.40%)
- Capsule diameter: 0.0722 m (max PCM conduction distance = 0.0361 m)
- Capsule count: 32
- PCM mass: 4.859 kg
- Flow rate: 0.0207 kg/s (permitted range 0.010-0.050 kg/s)

### Performance (simulator-confirmed, sim_v2_tamilnadu)
- Useful annual energy: 1668.7 kWh/year
- Solar fraction: 65.23%
- Delivery-temperature hours (>= 45 C): 3166
- Unmet energy: 734.2 kWh/year
- Pump energy: 0.0001 Wh/year
- Constraint margin (temperature): 2.70 C below the tightest safety limit

### Robustness (120 Monte Carlo draws — PCM latent heat, two-level weather noise [annual scale/offset + per-hour jitter], demand volume/timing, mains temperature)
- P(meets annual demand, solar_fraction>=50%): 100.0%
- P(meets delivery temperature, solar_fraction>=45%): 100.0%
- P(any safety-temperature violation): 0.0%
- P(exceeds max safe temperature limit): 0.0%
- Useful energy 5th-50th-95th percentile: [1536.5, 1659.4, 1790.3] kWh
- Solar fraction 5th-95th percentile: [57.1%, 72.3%]
- Max water temperature 95th percentile: 62.5 C
- **Framework rule (P(demand)>=75% and P(temp-safe)>=95%): ROBUST**

### Surrogate QA
- Hold-out RMSE (useful_energy_kWh, ExtraTrees, all regimes pooled): 4.052 kWh
- Surrogate-vs-simulator error for this selected design: 0.496%

### Decision
- This design (1668.7 kWh) is 1.84% below the regime's best-found candidate (1700.0 kWh, a different design within the selection rule's pre-declared tolerance band) — it was picked by the tie-break (safety first, then pump energy, then PCM mass, then capsule count) among candidates already within tolerance of the best, not because it had the highest useful energy in the regime.
- Selection-rule pool size (candidates within 5% of best): 60

### Caveats
- The robustness section's annual GHI/temperature variability is drawn from Objective 1's real 10-year (2016-2025) daily weather archive for this regime (src/robustness/weather_ensemble.py) -- a genuine historical-year ensemble, not an assumed range. The within-year HOURLY shape still comes from a single medoid year plus synthetic per-hour jitter (no member-point/multi-year hourly data was pulled for this project, 40-hr cut list).
- Melting treated as a narrow +/-1 K band around a single reported Tm_C (no measured solidus/liquidus interval in the PCM database).
- Liquid natural convection inside the capsule is not resolved -- a fixed x2 effective-conductivity enhancement factor is assumed once liquid fraction >=50%.
- No auxiliary/backup heater modeled -- solar fraction here is the fraction of ideal 45 C demand met by solar+PCM alone, stricter than a real installed system with backup heating.
- No active high-temperature safety shield/bypass modeled -- see the robustness section's temperature-violation probability above.
- n-Hexacosane (C26) property provenance: check `any_property_imputed` in `data/objective1/pcm_database_tamilnadu.csv` for which fields are manufacturer-measured vs MICE/RF-imputed.


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
- **Selected arrangement: radial** (searched 2026-09-17 — single-layer/staggered/radial were all compared; previously frozen to staggered-only)
- Arrangement rationale: arrangement radial won by -1.17% over next-best arrangement single-layer (surrogate-vs-sim noise band: 0.40%)
- Capsule diameter: 0.0753 m (max PCM conduction distance = 0.0377 m)
- Capsule count: 33
- PCM mass: 5.682 kg
- Flow rate: 0.0108 kg/s (permitted range 0.010-0.050 kg/s)

### Performance (simulator-confirmed, sim_v2_tamilnadu)
- Useful annual energy: 1763.4 kWh/year
- Solar fraction: 57.77%
- Delivery-temperature hours (>= 45 C): 2820
- Unmet energy: 1133.9 kWh/year
- Pump energy: 0.0000 Wh/year
- Constraint margin (temperature): 3.06 C below the tightest safety limit

### Robustness (120 Monte Carlo draws — PCM latent heat, two-level weather noise [annual scale/offset + per-hour jitter], demand volume/timing, mains temperature)
- P(meets annual demand, solar_fraction>=50%): 94.2%
- P(meets delivery temperature, solar_fraction>=45%): 100.0%
- P(any safety-temperature violation): 0.0%
- P(exceeds max safe temperature limit): 0.0%
- Useful energy 5th-50th-95th percentile: [1622.6, 1760.7, 1876.2] kWh
- Solar fraction 5th-95th percentile: [49.8%, 65.5%]
- Max water temperature 95th percentile: 62.3 C
- **Framework rule (P(demand)>=75% and P(temp-safe)>=95%): ROBUST**

### Surrogate QA
- Hold-out RMSE (useful_energy_kWh, ExtraTrees, all regimes pooled): 4.052 kWh
- Surrogate-vs-simulator error for this selected design: 0.076%

### Decision
- This design (1763.4 kWh) is 2.13% below the regime's best-found candidate (1801.8 kWh, a different design within the selection rule's pre-declared tolerance band) — it was picked by the tie-break (safety first, then pump energy, then PCM mass, then capsule count) among candidates already within tolerance of the best, not because it had the highest useful energy in the regime.
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
- Arrangement rationale: arrangements tied within noise in this regime (margin -0.13% is inside the 0.40% surrogate-vs-sim noise band) -- arrangement not decisive here; next-best was radial
- Capsule diameter: 0.0798 m (max PCM conduction distance = 0.0399 m)
- Capsule count: 35
- PCM mass: 7.449 kg
- Flow rate: 0.0237 kg/s (permitted range 0.010-0.050 kg/s)

### Performance (simulator-confirmed, sim_v2_tamilnadu)
- Useful annual energy: 1679.4 kWh/year
- Solar fraction: 64.66%
- Delivery-temperature hours (>= 45 C): 3074
- Unmet energy: 777.5 kWh/year
- Pump energy: 0.0001 Wh/year
- Constraint margin (temperature): 2.71 C below the tightest safety limit

### Robustness (120 Monte Carlo draws — PCM latent heat, two-level weather noise [annual scale/offset + per-hour jitter], demand volume/timing, mains temperature)
- P(meets annual demand, solar_fraction>=50%): 100.0%
- P(meets delivery temperature, solar_fraction>=45%): 100.0%
- P(any safety-temperature violation): 0.0%
- P(exceeds max safe temperature limit): 0.0%
- Useful energy 5th-50th-95th percentile: [1499.3, 1650.8, 1762.7] kWh
- Solar fraction 5th-95th percentile: [56.4%, 72.8%]
- Max water temperature 95th percentile: 62.6 C
- **Framework rule (P(demand)>=75% and P(temp-safe)>=95%): ROBUST**

### Surrogate QA
- Hold-out RMSE (useful_energy_kWh, ExtraTrees, all regimes pooled): 4.052 kWh
- Surrogate-vs-simulator error for this selected design: 1.276%

### Decision
- This design (1679.4 kWh) is 0.13% below the regime's best-found candidate (1681.5 kWh, a different design within the selection rule's pre-declared tolerance band) — it was picked by the tie-break (safety first, then pump energy, then PCM mass, then capsule count) among candidates already within tolerance of the best, not because it had the highest useful energy in the regime.
- Selection-rule pool size (candidates within 5% of best): 60

### Caveats
- The robustness section's annual GHI/temperature variability is drawn from Objective 1's real 10-year (2016-2025) daily weather archive for this regime (src/robustness/weather_ensemble.py) -- a genuine historical-year ensemble, not an assumed range. The within-year HOURLY shape still comes from a single medoid year plus synthetic per-hour jitter (no member-point/multi-year hourly data was pulled for this project, 40-hr cut list).
- Melting treated as a narrow +/-1 K band around a single reported Tm_C (no measured solidus/liquidus interval in the PCM database).
- Liquid natural convection inside the capsule is not resolved -- a fixed x2 effective-conductivity enhancement factor is assumed once liquid fraction >=50%.
- No auxiliary/backup heater modeled -- solar fraction here is the fraction of ideal 45 C demand met by solar+PCM alone, stricter than a real installed system with backup heating.
- No active high-temperature safety shield/bypass modeled -- see the robustness section's temperature-violation probability above.
- n-Pentacosane (C25) property provenance: check `any_property_imputed` in `data/objective1/pcm_database_tamilnadu.csv` for which fields are manufacturer-measured vs MICE/RF-imputed.
