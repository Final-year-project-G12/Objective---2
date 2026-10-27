# Objective 2 — Recommendation Cards (Rajasthan)

Simulator: `sim_v2_rajasthan` (Phase 4 GO). One card per Level-A climate regime. Every number here is traceable to a frozen Objective 1 table, the Phase 7 `deployable_design_per_regime` row, or the Phase 8 `robustness` summary — nothing is recomputed in this file.


---

## Regime 0 — cooler, arid/low-monsoon, erratic solar resource, medoid RJP_0132 -- Udaipur (109 pts)

**Medoid:** `rajasthan` cluster 0  ·  **Population covered:** 21,755,737  ·  **Regime size:** 109 grid points

### Climate summary (population-weighted, `cluster_profiles_rajasthan.csv`)

| GHI | Ta mean | Ta p95 | CDD24 | DTR | RH sunrise | monsoon idx |
|---|---|---|---|---|---|---|
| 5.16 kWh/m²/d | 27.1 °C | 35.6 °C | 12372 | 13.5 °C | 71.0 % | 0.93 |

Objective 1 design targets: `Tm_target_C` = 43.5 °C, `L_required` = 437.9 kJ/kg (ceiling), `T_mains_est` = 25.13 °C.

### Objective 1 PCM shortlist (MCDM)

| Rank | PCM | MC top-3 inclusion |
|---|---|---|
| 1 | savE® OM42 | n/a |
| 2 | RT44HC | n/a |
| 3 | RT47 | n/a |

### Selected deployable design (Phase 7)

**PCM: RT44HC**

| Capsule diameter | Capsule count | Flow rate | PCM volume fraction | PCM mass |
|---|---|---|---|---|
| 0.0429 m | 37 | 0.0428 kg/s | 0.0306 | 1.225 kg |


**Selected arrangement:** single-layer

**Arrangement rationale:** arrangements tied within noise in this regime — arrangement not decisive here (margin=-0.134 kWh / -0.01% <= noise band=0.04%; tied arrangements: ['radial', 'single-layer', 'staggered']).

**Match to Objective 1's ranking:** DIVERGES — O2 deploys **RT44HC**, but Objective 1's MCDM consensus rank-1 pick for this regime is **savE® OM42**. Objective 2's selection rule (useful-energy tolerance, then pump energy/PCM mass/capsule count/margin) does not weight O1's consensus rank, so a lower-ranked-but-still-shortlisted PCM can win on design-level performance. This is expected and reported, not a defect — see `docs/09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md` §2/§8.

### Simulator-confirmed performance (sim_v2_rajasthan, full year)

| Useful energy | Solar fraction | Unmet energy | Pump energy | Max water T | Safety-margin to 75 °C | Energy residual |
|---|---|---|---|---|---|---|
| 1588.1 kWh | 55.44 % | 1127.4 kWh | 0.0007 Wh | 68.9 °C | 2.9 °C | 0.000430 % |

### Surrogate vs simulator

Surrogate predicted useful energy 1587.8 kWh; simulator confirmed 1588.1 kWh — **delta 0.016 %** (well inside the 15 % large-error rule; the surrogate was a proposal ranker only, Bug-Fix 5).

### Robustness — 120 Monte Carlo draws (weather+noise, demand volume ±20 %, demand timing ±30 min, mains ±2 °C) — rule-based safety shield ACTIVE (bypass at 72.0 °C water / 62.0 °C PCM), the pipeline default since 2026-09-13 — see `src/simulation/tank_model.py`

| P(meet delivery temp) | P(meet annual demand) | P(temp-safe) | P(exceeds max safe temp) | Useful energy P5–P95 | Max water T P95 |
|---|---|---|---|---|---|
| 1.00 | 0.93 | 1.00 | 0.00 | 1451–1713 kWh | 72.2 °C |

Threshold: robust if P(meet annual demand) ≥ ~0.75 **and** P(temp-safe) ≥ ~0.95. Result: **ROBUST**.

### Decision rationale

Phase 7 searched 600 candidates per regime×PCM pair (arrangement sampled uniformly across single-layer/staggered/radial since 2026-09-17) and re-ran the top 5 per pair in the real simulator, with the safety shield active throughout search, confirmation, and selection (pipeline default since 2026-09-13). 135/135 PCM candidates (across all regimes) clear the 65 °C PCM safety limit. The pre-declared selection rule (reject temperature-unsafe → within 5 % of best useful energy → min pump energy → min PCM mass → min capsule count → max constraint margin) selects **RT44HC**, which meets temperature safety under the shield and is within the Pareto tolerance of (or beats) the best plain-tank useful energy.

### Caveats

- **Missing / imputed PCM properties:** the Objective 1 database has imputed fields (`any_property_imputed`) for several shortlisted PCMs; the selected PCM's own imputed-property flags should be checked before quoting its properties as measured.
- **Single-pass optimization:** one surrogate search + confirmation, no active-learning loop, no NSGA-II Pareto front.
- **Reduced Monte Carlo:** 120 draws, medoid weather + noise (no alternate member-point weather series exists for Rajasthan) (PCM latent-heat ±10 % perturbation included).
- **Single-state scope:** Rajasthan only. The multi-state comparison (does this same shielded-selection outcome hold for Assam / Uttarakhand / Tamil Nadu too?) is future work.
- **Lumped grey-box model:** single water node, single capsule group, correlation-based heat transfer — treat absolute numbers as ±15 %.
- **Safety shield is the pipeline default (adopted 2026-09-13):** every number on this card (Phase 5-8) is computed WITH the rule-based safety shield active (`system_config_shared.yaml: safety_shield.enabled`), not as a separate what-if. IS 12976:2023 §8.2 validates this exact mechanism as the standard overheat-protection method for Indian SWH systems.
- **A further, not-yet-adopted mitigation exists:** the frozen 50 L tank / 1.5 m² collector sizing (33.3 L/m²) is itself below IS 12976:2023's cited 37.5-100 L/m² range; resizing the tank to the standard's 75 L/m² reference (112.5 L) makes every shortlisted PCM candidate pass safety AND raises solar fraction, with no shield needed — see `results/fix6_standards_compliant_sizing_supplementary.md` and `docs/09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md` §7. Not folded into this card's numbers (a frozen-shared-config change requires a coordinated 4-state re-run).

---

## Regime 1 — hot, monsoon-influenced, steady solar resource, long low-clearness runs (high autonomy demand), medoid RJP_0192 -- Nagaur (83 pts)

**Medoid:** `rajasthan` cluster 1  ·  **Population covered:** 14,033,429  ·  **Regime size:** 83 grid points

### Climate summary (population-weighted, `cluster_profiles_rajasthan.csv`)

| GHI | Ta mean | Ta p95 | CDD24 | DTR | RH sunrise | monsoon idx |
|---|---|---|---|---|---|---|
| 5.38 kWh/m²/d | 28.0 °C | 36.6 °C | 16440 | 13.8 °C | 67.2 % | 1.05 |

Objective 1 design targets: `Tm_target_C` = 47.9 °C, `L_required` = 427.2 kJ/kg (ceiling), `T_mains_est` = 25.98 °C.

### Objective 1 PCM shortlist (MCDM)

| Rank | PCM | MC top-3 inclusion |
|---|---|---|
| 1 | n-Tricosane (C23) | n/a |
| 2 | savE® OM49 | n/a |
| 3 | RT45HC | n/a |

### Selected deployable design (Phase 7)

**PCM: savE® OM49**

| Capsule diameter | Capsule count | Flow rate | PCM volume fraction | PCM mass |
|---|---|---|---|---|
| 0.0410 m | 25 | 0.0420 kg/s | 0.0181 | 0.738 kg |


**Selected arrangement:** radial

**Arrangement rationale:** arrangements tied within noise in this regime — arrangement not decisive here (margin=-0.185 kWh / -0.01% <= noise band=0.04%; tied arrangements: ['radial', 'single-layer', 'staggered']).

**Match to Objective 1's ranking:** DIVERGES — O2 deploys **savE® OM49**, but Objective 1's MCDM consensus rank-1 pick for this regime is **n-Tricosane (C23)**. Objective 2's selection rule (useful-energy tolerance, then pump energy/PCM mass/capsule count/margin) does not weight O1's consensus rank, so a lower-ranked-but-still-shortlisted PCM can win on design-level performance. This is expected and reported, not a defect — see `docs/09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md` §2/§8.

### Simulator-confirmed performance (sim_v2_rajasthan, full year)

| Useful energy | Solar fraction | Unmet energy | Pump energy | Max water T | Safety-margin to 75 °C | Energy residual |
|---|---|---|---|---|---|---|
| 1845.6 kWh | 61.84 % | 926.5 kWh | 0.0002 Wh | 72.1 °C | 2.9 °C | 0.000313 % |

### Surrogate vs simulator

Surrogate predicted useful energy 1845.7 kWh; simulator confirmed 1845.6 kWh — **delta 0.005 %** (well inside the 15 % large-error rule; the surrogate was a proposal ranker only, Bug-Fix 5).

### Robustness — 120 Monte Carlo draws (weather+noise, demand volume ±20 %, demand timing ±30 min, mains ±2 °C) — rule-based safety shield ACTIVE (bypass at 72.0 °C water / 62.0 °C PCM), the pipeline default since 2026-09-13 — see `src/simulation/tank_model.py`

| P(meet delivery temp) | P(meet annual demand) | P(temp-safe) | P(exceeds max safe temp) | Useful energy P5–P95 | Max water T P95 |
|---|---|---|---|---|---|
| 1.00 | 1.00 | 1.00 | 0.00 | 1652–1962 kWh | 72.2 °C |

Threshold: robust if P(meet annual demand) ≥ ~0.75 **and** P(temp-safe) ≥ ~0.95. Result: **ROBUST**.

### Decision rationale

Phase 7 searched 600 candidates per regime×PCM pair (arrangement sampled uniformly across single-layer/staggered/radial since 2026-09-17) and re-ran the top 5 per pair in the real simulator, with the safety shield active throughout search, confirmation, and selection (pipeline default since 2026-09-13). 135/135 PCM candidates (across all regimes) clear the 65 °C PCM safety limit. The pre-declared selection rule (reject temperature-unsafe → within 5 % of best useful energy → min pump energy → min PCM mass → min capsule count → max constraint margin) selects **savE® OM49**, which meets temperature safety under the shield and is within the Pareto tolerance of (or beats) the best plain-tank useful energy.

### Caveats

- **Missing / imputed PCM properties:** the Objective 1 database has imputed fields (`any_property_imputed`) for several shortlisted PCMs; the selected PCM's own imputed-property flags should be checked before quoting its properties as measured.
- **Single-pass optimization:** one surrogate search + confirmation, no active-learning loop, no NSGA-II Pareto front.
- **Reduced Monte Carlo:** 120 draws, medoid weather + noise (no alternate member-point weather series exists for Rajasthan) (PCM latent-heat ±10 % perturbation included).
- **Single-state scope:** Rajasthan only. The multi-state comparison (does this same shielded-selection outcome hold for Assam / Uttarakhand / Tamil Nadu too?) is future work.
- **Lumped grey-box model:** single water node, single capsule group, correlation-based heat transfer — treat absolute numbers as ±15 %.
- **Safety shield is the pipeline default (adopted 2026-09-13):** every number on this card (Phase 5-8) is computed WITH the rule-based safety shield active (`system_config_shared.yaml: safety_shield.enabled`), not as a separate what-if. IS 12976:2023 §8.2 validates this exact mechanism as the standard overheat-protection method for Indian SWH systems.
- **A further, not-yet-adopted mitigation exists:** the frozen 50 L tank / 1.5 m² collector sizing (33.3 L/m²) is itself below IS 12976:2023's cited 37.5-100 L/m² range; resizing the tank to the standard's 75 L/m² reference (112.5 L) makes every shortlisted PCM candidate pass safety AND raises solar fraction, with no shield needed — see `results/fix6_standards_compliant_sizing_supplementary.md` and `docs/09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md` §7. Not folded into this card's numbers (a frozen-shared-config change requires a coordinated 4-state re-run).

---

## Regime 2 — cooler, arid/low-monsoon, erratic solar resource, largest population, medoid RJP_0083 -- Jaipur (128 pts)

**Medoid:** `rajasthan` cluster 2  ·  **Population covered:** 34,514,036  ·  **Regime size:** 128 grid points

### Climate summary (population-weighted, `cluster_profiles_rajasthan.csv`)

| GHI | Ta mean | Ta p95 | CDD24 | DTR | RH sunrise | monsoon idx |
|---|---|---|---|---|---|---|
| 5.03 kWh/m²/d | 26.7 °C | 35.9 °C | 14590 | 13.7 °C | 72.1 % | 1.03 |

Objective 1 design targets: `Tm_target_C` = 45.7 °C, `L_required` = 443.4 kJ/kg (ceiling), `T_mains_est` = 24.70 °C.

### Objective 1 PCM shortlist (MCDM)

| Rank | PCM | MC top-3 inclusion |
|---|---|---|
| 1 | RT45HC | n/a |
| 2 | Lauric acid (C12) | n/a |
| 3 | n-Docosane (C22) | n/a |

### Selected deployable design (Phase 7)

**PCM: Lauric acid (C12)**

| Capsule diameter | Capsule count | Flow rate | PCM volume fraction | PCM mass |
|---|---|---|---|---|
| 0.0403 m | 37 | 0.0305 kg/s | 0.0254 | 1.217 kg |


**Selected arrangement:** radial

**Arrangement rationale:** arrangements tied within noise in this regime — arrangement not decisive here (margin=-0.291 kWh / -0.02% <= noise band=0.04%; tied arrangements: ['radial', 'single-layer', 'staggered']).

**Match to Objective 1's ranking:** DIVERGES — O2 deploys **Lauric acid (C12)**, but Objective 1's MCDM consensus rank-1 pick for this regime is **RT45HC**. Objective 2's selection rule (useful-energy tolerance, then pump energy/PCM mass/capsule count/margin) does not weight O1's consensus rank, so a lower-ranked-but-still-shortlisted PCM can win on design-level performance. This is expected and reported, not a defect — see `docs/09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md` §2/§8.

### Simulator-confirmed performance (sim_v2_rajasthan, full year)

| Useful energy | Solar fraction | Unmet energy | Pump energy | Max water T | Safety-margin to 75 °C | Energy residual |
|---|---|---|---|---|---|---|
| 1791.2 kWh | 58.54 % | 1074.8 kWh | 0.0002 Wh | 72.1 °C | 2.9 °C | 0.000276 % |

### Surrogate vs simulator

Surrogate predicted useful energy 1791.1 kWh; simulator confirmed 1791.2 kWh — **delta 0.006 %** (well inside the 15 % large-error rule; the surrogate was a proposal ranker only, Bug-Fix 5).

### Robustness — 120 Monte Carlo draws (weather+noise, demand volume ±20 %, demand timing ±30 min, mains ±2 °C) — rule-based safety shield ACTIVE (bypass at 72.0 °C water / 62.0 °C PCM), the pipeline default since 2026-09-13 — see `src/simulation/tank_model.py`

| P(meet delivery temp) | P(meet annual demand) | P(temp-safe) | P(exceeds max safe temp) | Useful energy P5–P95 | Max water T P95 |
|---|---|---|---|---|---|
| 1.00 | 1.00 | 1.00 | 0.00 | 1613–1892 kWh | 72.2 °C |

Threshold: robust if P(meet annual demand) ≥ ~0.75 **and** P(temp-safe) ≥ ~0.95. Result: **ROBUST**.

### Decision rationale

Phase 7 searched 600 candidates per regime×PCM pair (arrangement sampled uniformly across single-layer/staggered/radial since 2026-09-17) and re-ran the top 5 per pair in the real simulator, with the safety shield active throughout search, confirmation, and selection (pipeline default since 2026-09-13). 135/135 PCM candidates (across all regimes) clear the 65 °C PCM safety limit. The pre-declared selection rule (reject temperature-unsafe → within 5 % of best useful energy → min pump energy → min PCM mass → min capsule count → max constraint margin) selects **Lauric acid (C12)**, which meets temperature safety under the shield and is within the Pareto tolerance of (or beats) the best plain-tank useful energy.

### Caveats

- **Missing / imputed PCM properties:** the Objective 1 database has imputed fields (`any_property_imputed`) for several shortlisted PCMs; the selected PCM's own imputed-property flags should be checked before quoting its properties as measured.
- **Single-pass optimization:** one surrogate search + confirmation, no active-learning loop, no NSGA-II Pareto front.
- **Reduced Monte Carlo:** 120 draws, medoid weather + noise (no alternate member-point weather series exists for Rajasthan) (PCM latent-heat ±10 % perturbation included).
- **Single-state scope:** Rajasthan only. The multi-state comparison (does this same shielded-selection outcome hold for Assam / Uttarakhand / Tamil Nadu too?) is future work.
- **Lumped grey-box model:** single water node, single capsule group, correlation-based heat transfer — treat absolute numbers as ±15 %.
- **Safety shield is the pipeline default (adopted 2026-09-13):** every number on this card (Phase 5-8) is computed WITH the rule-based safety shield active (`system_config_shared.yaml: safety_shield.enabled`), not as a separate what-if. IS 12976:2023 §8.2 validates this exact mechanism as the standard overheat-protection method for Indian SWH systems.
- **A further, not-yet-adopted mitigation exists:** the frozen 50 L tank / 1.5 m² collector sizing (33.3 L/m²) is itself below IS 12976:2023's cited 37.5-100 L/m² range; resizing the tank to the standard's 75 L/m² reference (112.5 L) makes every shortlisted PCM candidate pass safety AND raises solar fraction, with no shield needed — see `results/fix6_standards_compliant_sizing_supplementary.md` and `docs/09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md` §7. Not folded into this card's numbers (a frozen-shared-config change requires a coordinated 4-state re-run).
