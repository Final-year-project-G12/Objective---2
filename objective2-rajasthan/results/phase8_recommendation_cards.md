# Objective 2 — Recommendation Cards (Rajasthan)

Simulator: `sim_v1_rajasthan` (Phase 4 GO). One card per Level-A climate regime. Every number here is traceable to a frozen Objective 1 table, the Phase 7 `deployable_design_per_regime` row, or the Phase 8 `robustness` summary — nothing is recomputed in this file.


---

## Regime 0 — cooler arid / low-monsoon, erratic solar, medoid RJP_0132 (114 pts)

**Medoid:** `rajasthan` cluster 0  ·  **Population covered:** 22,568,150  ·  **Regime size:** 114 grid points

### Climate summary (population-weighted, `cluster_profiles_rajasthan.csv`)

| GHI | Ta mean | Ta p95 | CDD24 | DTR | RH sunrise | monsoon idx |
|---|---|---|---|---|---|---|
| 5.17 kWh/m²/d | 27.1 °C | 35.6 °C | 12348 | 13.5 °C | 70.9 % | 0.93 |

Objective 1 design targets: `Tm_target_C` = 57.0 °C, `L_required` = 312.8 kJ/kg (ceiling), `T_mains_est` = 25.09 °C.

### Objective 1 PCM shortlist (MCDM)

| Rank | PCM | MC top-3 inclusion |
|---|---|---|
| 1 | RT50 | 90.8% |
| 2 | RT45HC | 60.8% |
| 3 | Lauric acid (C12) | 62.3% |

### Selected deployable design (Phase 7)

**Plain (sensible-only) 50 L tank — no PCM.** The Objective 1 PCM shortlist did not survive the pre-declared selection rule (see rationale below).

| Capsule diameter | Capsule count | Flow rate | PCM volume fraction | PCM mass |
|---|---|---|---|---|
| 0.0441 m | 23 | 0.0349 kg/s | 0.0206 | 0.000 kg |

*(For the plain-tank selection the capsule diameter/count are the search's nominal values; `run_case` forces `n_capsule_effective = 0`, so the tank is simulated as plain sensible-water storage.)*

### Simulator-confirmed performance (sim_v1_rajasthan, full year)

| Useful energy | Solar fraction | Unmet energy | Pump energy | Max water T | Safety-margin to 75 °C | Energy residual |
|---|---|---|---|---|---|---|
| 1585.7 kWh | 54.97 % | 1141.5 kWh | 0.0000 Wh | 68.6 °C | 6.4 °C | 0.000301 % |

### Surrogate vs simulator

Surrogate predicted useful energy 1587.3 kWh; simulator confirmed 1585.7 kWh — **delta 0.098 %** (well inside the 15 % large-error rule; the surrogate was a proposal ranker only, Bug-Fix 5).

### Robustness — 120 Monte Carlo draws (weather+noise, demand volume ±20 %, demand timing ±30 min, mains ±2 °C)

| P(meet delivery temp) | P(meet annual demand) | P(temp-safe) | P(exceeds max safe temp) | Useful energy P5–P95 | Max water T P95 |
|---|---|---|---|---|---|
| 1.00 | 0.88 | 0.57 | 0.43 | 1454–1673 kWh | 84.6 °C |

Threshold: robust if P(meet annual demand) ≥ ~0.75 **and** P(temp-safe) ≥ ~0.95. Result: **NOT ROBUST — reported as a caveat, not hidden**.

The binding failure is **P(temp-safe) = 0.57** (any flagged safety sub-hour) / **P(exceeds max safe temp) = 0.43** (the reported annual max clearing the hard limit): under realistic weather/demand/mains variability the tank exceeds the 75 °C water limit in a large fraction of draws. The deployable design's nominal margin is only 6.4 °C, which a +GHI / +mains draw erases. This is the same hot-dry-climate + frozen-collector-sizing issue flagged since Phase 3; it makes an **active high-temperature bypass (Objective 3) a requirement, not an option** for Rajasthan.

### Decision rationale

Phase 7 searched 400 candidates per regime×PCM pair and re-ran the top 5 per pair in the real simulator. In this regime the best PCM geometry the search found beat the best plain-tank geometry by only ~0.1 % useful energy — two orders of magnitude below the pre-declared 5 % Pareto tolerance — and **no PCM candidate cleared the 65 °C PCM safety limit** (0/45 across all regimes). The selection rule therefore keeps the design that (a) meets temperature safety and (b) has the lowest PCM mass → the plain tank.

### Caveats

- **Missing / imputed PCM properties:** the Objective 1 database has imputed fields (`any_property_imputed`) for several shortlisted PCMs; not material here because no PCM was selected, but it would matter if the bounds are widened.
- **Single-pass optimization:** one surrogate search + confirmation, no active-learning loop, no NSGA-II Pareto front.
- **Reduced Monte Carlo:** 120 draws, medoid weather + noise (no alternate member-point weather series exists for Rajasthan); PCM latent-heat ±10 % perturbation is inapplicable (plain tank selected).
- **Single-state scope:** Rajasthan only. The multi-state comparison (does plain-tank-wins hold for Assam / Uttarakhand / Tamil Nadu too?) is future work.
- **Lumped grey-box model:** single water node, single capsule group, correlation-based heat transfer — treat absolute numbers as ±15 %.

---

## Regime 1 — hot, monsoon-influenced, steady solar, high autonomy demand, medoid RJP_0202 (103 pts)

**Medoid:** `rajasthan` cluster 1  ·  **Population covered:** 17,959,813  ·  **Regime size:** 103 grid points

### Climate summary (population-weighted, `cluster_profiles_rajasthan.csv`)

| GHI | Ta mean | Ta p95 | CDD24 | DTR | RH sunrise | monsoon idx |
|---|---|---|---|---|---|---|
| 5.35 kWh/m²/d | 27.8 °C | 36.4 °C | 15837 | 13.8 °C | 67.4 % | 1.04 |

Objective 1 design targets: `Tm_target_C` = 57.0 °C, `L_required` = 304.1 kJ/kg (ceiling), `T_mains_est` = 25.78 °C.

### Objective 1 PCM shortlist (MCDM)

| Rank | PCM | MC top-3 inclusion |
|---|---|---|
| 1 | savE® OM50 | 83.2% |
| 2 | Paraffin/HDPE PCM3 | 69.6% |
| 3 | Paraffin/HDPE PCM6 | 37.7% |

### Selected deployable design (Phase 7)

**Plain (sensible-only) 50 L tank — no PCM.** The Objective 1 PCM shortlist did not survive the pre-declared selection rule (see rationale below).

| Capsule diameter | Capsule count | Flow rate | PCM volume fraction | PCM mass |
|---|---|---|---|---|
| 0.0407 m | 14 | 0.0298 kg/s | 0.0099 | 0.000 kg |

*(For the plain-tank selection the capsule diameter/count are the search's nominal values; `run_case` forces `n_capsule_effective = 0`, so the tank is simulated as plain sensible-water storage.)*

### Simulator-confirmed performance (sim_v1_rajasthan, full year)

| Useful energy | Solar fraction | Unmet energy | Pump energy | Max water T | Safety-margin to 75 °C | Energy residual |
|---|---|---|---|---|---|---|
| 1673.4 kWh | 58.23 % | 1022.1 kWh | 0.0000 Wh | 72.4 °C | 2.6 °C | 0.000449 % |

### Surrogate vs simulator

Surrogate predicted useful energy 1674.8 kWh; simulator confirmed 1673.4 kWh — **delta 0.087 %** (well inside the 15 % large-error rule; the surrogate was a proposal ranker only, Bug-Fix 5).

### Robustness — 120 Monte Carlo draws (weather+noise, demand volume ±20 %, demand timing ±30 min, mains ±2 °C)

| P(meet delivery temp) | P(meet annual demand) | P(temp-safe) | P(exceeds max safe temp) | Useful energy P5–P95 | Max water T P95 |
|---|---|---|---|---|---|
| 1.00 | 0.99 | 0.45 | 0.55 | 1523–1781 kWh | 88.2 °C |

Threshold: robust if P(meet annual demand) ≥ ~0.75 **and** P(temp-safe) ≥ ~0.95. Result: **NOT ROBUST — reported as a caveat, not hidden**.

The binding failure is **P(temp-safe) = 0.45** (any flagged safety sub-hour) / **P(exceeds max safe temp) = 0.55** (the reported annual max clearing the hard limit): under realistic weather/demand/mains variability the tank exceeds the 75 °C water limit in a large fraction of draws. The deployable design's nominal margin is only 2.6 °C, which a +GHI / +mains draw erases. This is the same hot-dry-climate + frozen-collector-sizing issue flagged since Phase 3; it makes an **active high-temperature bypass (Objective 3) a requirement, not an option** for Rajasthan.

### Decision rationale

Phase 7 searched 400 candidates per regime×PCM pair and re-ran the top 5 per pair in the real simulator. In this regime the best PCM geometry the search found beat the best plain-tank geometry by only ~0.1 % useful energy — two orders of magnitude below the pre-declared 5 % Pareto tolerance — and **no PCM candidate cleared the 65 °C PCM safety limit** (0/45 across all regimes). The selection rule therefore keeps the design that (a) meets temperature safety and (b) has the lowest PCM mass → the plain tank.

### Caveats

- **Missing / imputed PCM properties:** the Objective 1 database has imputed fields (`any_property_imputed`) for several shortlisted PCMs; not material here because no PCM was selected, but it would matter if the bounds are widened.
- **Single-pass optimization:** one surrogate search + confirmation, no active-learning loop, no NSGA-II Pareto front.
- **Reduced Monte Carlo:** 120 draws, medoid weather + noise (no alternate member-point weather series exists for Rajasthan); PCM latent-heat ±10 % perturbation is inapplicable (plain tank selected).
- **Single-state scope:** Rajasthan only. The multi-state comparison (does plain-tank-wins hold for Assam / Uttarakhand / Tamil Nadu too?) is future work.
- **Lumped grey-box model:** single water node, single capsule group, correlation-based heat transfer — treat absolute numbers as ±15 %.

---

## Regime 2 — cooler arid / low-monsoon, erratic solar, largest population, medoid RJP_0055 (103 pts)

**Medoid:** `rajasthan` cluster 2  ·  **Population covered:** 29,775,240  ·  **Regime size:** 103 grid points

### Climate summary (population-weighted, `cluster_profiles_rajasthan.csv`)

| GHI | Ta mean | Ta p95 | CDD24 | DTR | RH sunrise | monsoon idx |
|---|---|---|---|---|---|---|
| 5.00 kWh/m²/d | 26.5 °C | 35.9 °C | 14789 | 13.7 °C | 73.0 % | 1.03 |

Objective 1 design targets: `Tm_target_C` = 57.0 °C, `L_required` = 319.9 kJ/kg (ceiling), `T_mains_est` = 24.52 °C.

### Objective 1 PCM shortlist (MCDM)

| Rank | PCM | MC top-3 inclusion |
|---|---|---|
| 1 | savE® OM50 | 93.9% |
| 2 | Paraffin/HDPE PCM3 | 85.2% |
| 3 | Paraffin/HDPE PCM6 | 52.0% |

### Selected deployable design (Phase 7)

**Plain (sensible-only) 50 L tank — no PCM.** The Objective 1 PCM shortlist did not survive the pre-declared selection rule (see rationale below).

| Capsule diameter | Capsule count | Flow rate | PCM volume fraction | PCM mass |
|---|---|---|---|---|
| 0.0443 m | 8 | 0.0127 kg/s | 0.0073 | 0.000 kg |

*(For the plain-tank selection the capsule diameter/count are the search's nominal values; `run_case` forces `n_capsule_effective = 0`, so the tank is simulated as plain sensible-water storage.)*

### Simulator-confirmed performance (sim_v1_rajasthan, full year)

| Useful energy | Solar fraction | Unmet energy | Pump energy | Max water T | Safety-margin to 75 °C | Energy residual |
|---|---|---|---|---|---|---|
| 1592.3 kWh | 53.88 % | 1202.3 kWh | 0.0000 Wh | 68.7 °C | 6.3 °C | 0.001628 % |

### Surrogate vs simulator

Surrogate predicted useful energy 1593.3 kWh; simulator confirmed 1592.3 kWh — **delta 0.065 %** (well inside the 15 % large-error rule; the surrogate was a proposal ranker only, Bug-Fix 5).

### Robustness — 120 Monte Carlo draws (weather+noise, demand volume ±20 %, demand timing ±30 min, mains ±2 °C)

| P(meet delivery temp) | P(meet annual demand) | P(temp-safe) | P(exceeds max safe temp) | Useful energy P5–P95 | Max water T P95 |
|---|---|---|---|---|---|
| 1.00 | 0.80 | 0.53 | 0.47 | 1447–1692 kWh | 84.6 °C |

Threshold: robust if P(meet annual demand) ≥ ~0.75 **and** P(temp-safe) ≥ ~0.95. Result: **NOT ROBUST — reported as a caveat, not hidden**.

The binding failure is **P(temp-safe) = 0.53** (any flagged safety sub-hour) / **P(exceeds max safe temp) = 0.47** (the reported annual max clearing the hard limit): under realistic weather/demand/mains variability the tank exceeds the 75 °C water limit in a large fraction of draws. The deployable design's nominal margin is only 6.3 °C, which a +GHI / +mains draw erases. This is the same hot-dry-climate + frozen-collector-sizing issue flagged since Phase 3; it makes an **active high-temperature bypass (Objective 3) a requirement, not an option** for Rajasthan.

### Decision rationale

Phase 7 searched 400 candidates per regime×PCM pair and re-ran the top 5 per pair in the real simulator. In this regime the best PCM geometry the search found beat the best plain-tank geometry by only ~0.1 % useful energy — two orders of magnitude below the pre-declared 5 % Pareto tolerance — and **no PCM candidate cleared the 65 °C PCM safety limit** (0/45 across all regimes). The selection rule therefore keeps the design that (a) meets temperature safety and (b) has the lowest PCM mass → the plain tank.

### Caveats

- **Missing / imputed PCM properties:** the Objective 1 database has imputed fields (`any_property_imputed`) for several shortlisted PCMs; not material here because no PCM was selected, but it would matter if the bounds are widened.
- **Single-pass optimization:** one surrogate search + confirmation, no active-learning loop, no NSGA-II Pareto front.
- **Reduced Monte Carlo:** 120 draws, medoid weather + noise (no alternate member-point weather series exists for Rajasthan); PCM latent-heat ±10 % perturbation is inapplicable (plain tank selected).
- **Single-state scope:** Rajasthan only. The multi-state comparison (does plain-tank-wins hold for Assam / Uttarakhand / Tamil Nadu too?) is future work.
- **Lumped grey-box model:** single water node, single capsule group, correlation-based heat transfer — treat absolute numbers as ±15 %.
