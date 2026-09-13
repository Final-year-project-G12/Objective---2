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

**PCM: RT50**

| Capsule diameter | Capsule count | Flow rate | PCM volume fraction | PCM mass |
|---|---|---|---|---|
| 0.0455 m | 12 | 0.0251 kg/s | 0.0118 | 0.519 kg |


### Simulator-confirmed performance (sim_v1_rajasthan, full year)

| Useful energy | Solar fraction | Unmet energy | Pump energy | Max water T | Safety-margin to 75 °C | Energy residual |
|---|---|---|---|---|---|---|
| 1586.8 kWh | 55.00 % | 1140.5 kWh | 0.0000 Wh | 68.7 °C | 2.9 °C | 0.000371 % |

### Surrogate vs simulator

Surrogate predicted useful energy 1586.8 kWh; simulator confirmed 1586.8 kWh — **delta 0.001 %** (well inside the 15 % large-error rule; the surrogate was a proposal ranker only, Bug-Fix 5).

### Robustness — 120 Monte Carlo draws (weather+noise, demand volume ±20 %, demand timing ±30 min, mains ±2 °C) — rule-based safety shield ACTIVE (bypass at 72.0 °C water / 62.0 °C PCM), the pipeline default since 2026-09-13 — see `src/simulation/tank_model.py`

| P(meet delivery temp) | P(meet annual demand) | P(temp-safe) | P(exceeds max safe temp) | Useful energy P5–P95 | Max water T P95 |
|---|---|---|---|---|---|
| 1.00 | 0.92 | 1.00 | 0.00 | 1450–1712 kWh | 72.2 °C |

Threshold: robust if P(meet annual demand) ≥ ~0.75 **and** P(temp-safe) ≥ ~0.95. Result: **ROBUST**.

### Decision rationale

Phase 7 searched 400 candidates per regime×PCM pair and re-ran the top 5 per pair in the real simulator, with the safety shield active throughout search, confirmation, and selection (pipeline default since 2026-09-13). 45/45 PCM candidates (across all regimes) clear the 65 °C PCM safety limit. The pre-declared selection rule (reject temperature-unsafe → within 5 % of best useful energy → min pump energy → min PCM mass → min capsule count → max constraint margin) selects **RT50**, which meets temperature safety under the shield and is within the Pareto tolerance of (or beats) the best plain-tank useful energy.

### Caveats

- **Missing / imputed PCM properties:** the Objective 1 database has imputed fields (`any_property_imputed`) for several shortlisted PCMs; the selected PCM's own imputed-property flags should be checked before quoting its properties as measured.
- **Single-pass optimization:** one surrogate search + confirmation, no active-learning loop, no NSGA-II Pareto front.
- **Reduced Monte Carlo:** 120 draws, medoid weather + noise (no alternate member-point weather series exists for Rajasthan) (PCM latent-heat ±10 % perturbation included).
- **Single-state scope:** Rajasthan only. The multi-state comparison (does this same shielded-selection outcome hold for Assam / Uttarakhand / Tamil Nadu too?) is future work.
- **Lumped grey-box model:** single water node, single capsule group, correlation-based heat transfer — treat absolute numbers as ±15 %.
- **Safety shield is the pipeline default (adopted 2026-09-13):** every number on this card (Phase 5-8) is computed WITH the rule-based safety shield active (`system_config_shared.yaml: safety_shield.enabled`), not as a separate what-if. IS 12976:2023 §8.2 validates this exact mechanism as the standard overheat-protection method for Indian SWH systems.
- **A further, not-yet-adopted mitigation exists:** the frozen 50 L tank / 1.5 m² collector sizing (33.3 L/m²) is itself below IS 12976:2023's cited 37.5-100 L/m² range; resizing the tank to the standard's 75 L/m² reference (112.5 L) makes every shortlisted PCM candidate pass safety AND raises solar fraction, with no shield needed — see `results/fix6_standards_compliant_sizing_supplementary.md` and `docs/09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md` §7. Not folded into this card's numbers (a frozen-shared-config change requires a coordinated 4-state re-run).

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
| 0.0438 m | 19 | 0.0150 kg/s | 0.0167 | 0.000 kg |

*(For the plain-tank selection the capsule diameter/count are the search's nominal values; `run_case` forces `n_capsule_effective = 0`, so the tank is simulated as plain sensible-water storage.)*

### Simulator-confirmed performance (sim_v1_rajasthan, full year)

| Useful energy | Solar fraction | Unmet energy | Pump energy | Max water T | Safety-margin to 75 °C | Energy residual |
|---|---|---|---|---|---|---|
| 1673.3 kWh | 58.23 % | 1022.1 kWh | 0.0000 Wh | 72.0 °C | 3.0 °C | 0.000449 % |

### Surrogate vs simulator

Surrogate predicted useful energy 1674.6 kWh; simulator confirmed 1673.3 kWh — **delta 0.077 %** (well inside the 15 % large-error rule; the surrogate was a proposal ranker only, Bug-Fix 5).

### Robustness — 120 Monte Carlo draws (weather+noise, demand volume ±20 %, demand timing ±30 min, mains ±2 °C) — rule-based safety shield ACTIVE (bypass at 72.0 °C water / 62.0 °C PCM), the pipeline default since 2026-09-13 — see `src/simulation/tank_model.py`

| P(meet delivery temp) | P(meet annual demand) | P(temp-safe) | P(exceeds max safe temp) | Useful energy P5–P95 | Max water T P95 |
|---|---|---|---|---|---|
| 1.00 | 0.99 | 1.00 | 0.00 | 1502–1771 kWh | 72.8 °C |

Threshold: robust if P(meet annual demand) ≥ ~0.75 **and** P(temp-safe) ≥ ~0.95. Result: **ROBUST**.

### Decision rationale

Phase 7 searched 400 candidates per regime×PCM pair and re-ran the top 5 per pair in the real simulator, with the safety shield active throughout search, confirmation, and selection (pipeline default since 2026-09-13). 45/45 PCM candidates (across all regimes) clear the 65 °C PCM safety limit. The pre-declared selection rule (reject temperature-unsafe → within 5 % of best useful energy → min pump energy → min PCM mass → min capsule count → max constraint margin) selects the plain tank, since no PCM candidate in this regime both met temperature safety and useful energy within tolerance.

### Caveats

- **Missing / imputed PCM properties:** the Objective 1 database has imputed fields (`any_property_imputed`) for several shortlisted PCMs; not material here because no PCM was selected, but it would matter if the bounds are widened.
- **Single-pass optimization:** one surrogate search + confirmation, no active-learning loop, no NSGA-II Pareto front.
- **Reduced Monte Carlo:** 120 draws, medoid weather + noise (no alternate member-point weather series exists for Rajasthan); PCM latent-heat ±10 % perturbation is inapplicable (plain tank selected).
- **Single-state scope:** Rajasthan only. The multi-state comparison (does this same shielded-selection outcome hold for Assam / Uttarakhand / Tamil Nadu too?) is future work.
- **Lumped grey-box model:** single water node, single capsule group, correlation-based heat transfer — treat absolute numbers as ±15 %.
- **Safety shield is the pipeline default (adopted 2026-09-13):** every number on this card (Phase 5-8) is computed WITH the rule-based safety shield active (`system_config_shared.yaml: safety_shield.enabled`), not as a separate what-if. IS 12976:2023 §8.2 validates this exact mechanism as the standard overheat-protection method for Indian SWH systems.
- **A further, not-yet-adopted mitigation exists:** the frozen 50 L tank / 1.5 m² collector sizing (33.3 L/m²) is itself below IS 12976:2023's cited 37.5-100 L/m² range; resizing the tank to the standard's 75 L/m² reference (112.5 L) makes every shortlisted PCM candidate pass safety AND raises solar fraction, with no shield needed — see `results/fix6_standards_compliant_sizing_supplementary.md` and `docs/09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md` §7. Not folded into this card's numbers (a frozen-shared-config change requires a coordinated 4-state re-run).

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
| 0.0447 m | 9 | 0.0259 kg/s | 0.0084 | 0.000 kg |

*(For the plain-tank selection the capsule diameter/count are the search's nominal values; `run_case` forces `n_capsule_effective = 0`, so the tank is simulated as plain sensible-water storage.)*

### Simulator-confirmed performance (sim_v1_rajasthan, full year)

| Useful energy | Solar fraction | Unmet energy | Pump energy | Max water T | Safety-margin to 75 °C | Energy residual |
|---|---|---|---|---|---|---|
| 1592.3 kWh | 53.88 % | 1202.3 kWh | 0.0000 Wh | 68.7 °C | 6.3 °C | 0.001628 % |

### Surrogate vs simulator

Surrogate predicted useful energy 1593.4 kWh; simulator confirmed 1592.3 kWh — **delta 0.069 %** (well inside the 15 % large-error rule; the surrogate was a proposal ranker only, Bug-Fix 5).

### Robustness — 120 Monte Carlo draws (weather+noise, demand volume ±20 %, demand timing ±30 min, mains ±2 °C) — rule-based safety shield ACTIVE (bypass at 72.0 °C water / 62.0 °C PCM), the pipeline default since 2026-09-13 — see `src/simulation/tank_model.py`

| P(meet delivery temp) | P(meet annual demand) | P(temp-safe) | P(exceeds max safe temp) | Useful energy P5–P95 | Max water T P95 |
|---|---|---|---|---|---|
| 1.00 | 0.80 | 1.00 | 0.00 | 1445–1689 kWh | 72.7 °C |

Threshold: robust if P(meet annual demand) ≥ ~0.75 **and** P(temp-safe) ≥ ~0.95. Result: **ROBUST**.

### Decision rationale

Phase 7 searched 400 candidates per regime×PCM pair and re-ran the top 5 per pair in the real simulator, with the safety shield active throughout search, confirmation, and selection (pipeline default since 2026-09-13). 45/45 PCM candidates (across all regimes) clear the 65 °C PCM safety limit. The pre-declared selection rule (reject temperature-unsafe → within 5 % of best useful energy → min pump energy → min PCM mass → min capsule count → max constraint margin) selects the plain tank, since no PCM candidate in this regime both met temperature safety and useful energy within tolerance.

### Caveats

- **Missing / imputed PCM properties:** the Objective 1 database has imputed fields (`any_property_imputed`) for several shortlisted PCMs; not material here because no PCM was selected, but it would matter if the bounds are widened.
- **Single-pass optimization:** one surrogate search + confirmation, no active-learning loop, no NSGA-II Pareto front.
- **Reduced Monte Carlo:** 120 draws, medoid weather + noise (no alternate member-point weather series exists for Rajasthan); PCM latent-heat ±10 % perturbation is inapplicable (plain tank selected).
- **Single-state scope:** Rajasthan only. The multi-state comparison (does this same shielded-selection outcome hold for Assam / Uttarakhand / Tamil Nadu too?) is future work.
- **Lumped grey-box model:** single water node, single capsule group, correlation-based heat transfer — treat absolute numbers as ±15 %.
- **Safety shield is the pipeline default (adopted 2026-09-13):** every number on this card (Phase 5-8) is computed WITH the rule-based safety shield active (`system_config_shared.yaml: safety_shield.enabled`), not as a separate what-if. IS 12976:2023 §8.2 validates this exact mechanism as the standard overheat-protection method for Indian SWH systems.
- **A further, not-yet-adopted mitigation exists:** the frozen 50 L tank / 1.5 m² collector sizing (33.3 L/m²) is itself below IS 12976:2023's cited 37.5-100 L/m² range; resizing the tank to the standard's 75 L/m² reference (112.5 L) makes every shortlisted PCM candidate pass safety AND raises solar fraction, with no shield needed — see `results/fix6_standards_compliant_sizing_supplementary.md` and `docs/09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md` §7. Not folded into this card's numbers (a frozen-shared-config change requires a coordinated 4-state re-run).
