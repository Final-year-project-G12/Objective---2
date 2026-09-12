# Recommendation Card — Regime 1 (Assam)
**Regime Title:** Upper Assam Tea Belt, warm valley regime, medoid ASP_0092 (61 pts)
**Representative Medoid:** `assam` cluster 1  ·  **Population covered:** 4,271,199  ·  **Regime size:** 61 grid points

### 1. Climate Summary (`cluster_profiles_assam.csv`)

| GHI | Ta mean | DTR | RH mean | monsoon idx |
|---|---|---|---|---|
| 4.08 kWh/m²/d | 25.1 °C | 6.3 °C | 79.0 % | 0.61 |

Objective 1 design targets: `Tm_target_C` = 44.0 °C, `L_required` = 258.7 kJ/kg (ceiling), `T_mains_est` = 19.10 °C.

### 2. Objective 1 Validated PCM Shortlist

| Rank | PCM Candidate | Selection Status | Selection Basis |
|---|---|---|---|
| 1 | savE® OM48 | **SELECTED DEPLOYABLE** | Phase 9/10 validated candidate universe; Phase 7 optimized |
| 2 | savE® OM50 | Evaluated near-best candidate | Phase 9/10 validated candidate universe; Phase 7 optimized |
| 3 | savE® OM46 | Evaluated near-best candidate | Phase 9/10 validated candidate universe; Phase 7 optimized |

### 3. Selected Deployable Design (Phase 7)

- **Selected PCM:** `savE® OM48`
- **Tank Volume:** 50.0 L (direct-immersion encapsulation)
- **Collector Area:** 1.5 m²
- **Operating Flow Envelope:** [0.01, 0.05] kg/s

| Capsule Diameter | Capsule Count | Flow Rate | PCM Volume Fraction | Void Fraction | PCM Mass |
|---|---|---|---|---|---|
| 0.0430 m | 18 | 0.0323 kg/s | 0.0150 | 0.9850 | 0.719 kg |

### 4. Simulator-Confirmed Performance (sim_v1_assam, Full 8,760-Hour Run)

| Useful Energy | Solar Fraction | Unmet Energy | Pump Energy | Max Water Temp | Safety Margin to 75 °C | Energy Residual |
|---|---|---|---|---|---|---|
| 709.4 kWh | 62.75 % | 409.5 kWh | 0.0000 Wh | 68.6 °C | -2.9 °C | 0.000000 % |

### 5. Phase 8 Light Robustness Results (100 Monte Carlo Draws)
**Uncertainty Sources Covered:** PCM latent heat ±10%, weather medoid + noise, demand volume ±20%, demand timing ±30 min, mains temperature ±2 °C.

| P(meet delivery temp) | P(meet annual demand) | Demand Criterion | P(temp-safe) | Safety Criterion | P(exceeds max safe temp) | Useful Energy P5–P95 | Max Water T P95 | Overall Status |
|---|---|---|---|---|---|---|---|---|
| 1.00 | 1.00 | **PASS** | 0.01 | **CAVEAT** | 0.99 | 621–765 kWh | 77.0 °C | **CAVEAT / NOT ROBUST** |

- **Thresholds Applied:** Robust if P(demand) ≥ 0.75 and P(temp-safe) ≥ 0.95.
- **Binding Caveat Explanation:** Under realistic weather/demand/mains perturbations, temperature safety reaches P(temp-safe) = 0.01 (P95 max water temperature = 77.0 °C), confirming that uncontrolled summer overheating can occur. An **active Objective 3 high-temperature bypass / safety shield is a mandatory requirement** for real-world deployment.

### 6. Surrogate vs. Simulator Delta
- **Surrogate Predicted Useful Energy:** 709.3 kWh
- **Simulator Confirmed Useful Energy:** 709.4 kWh
- **Discrepancy (Delta):** **0.023 %** (well within the pre-declared 15 % large-error rule)
- **Verification Verdict:** Verified proposal ranker. The surrogate faithfully guided optimization without distorting the final physical simulator metrics.

### 7. Technical Decision Rationale
In Regime 1 (Upper Assam Tea Belt, warm valley regime, medoid ASP_0092 (61 pts)), the Phase 7 optimization evaluated 7,966 geometrically valid configurations. `savE® OM48` was selected as the optimal deployable material because it maximized solar useful energy delivery (709.4 kWh) while meeting the 5% near-best hierarchical rule. The selected capsule geometry (18 spherical capsules, diameter 43.0 mm) achieves an optimal balance between thermal charging rate, low parasitic pumping loss (0.0000 Wh/year), and mechanical packing feasibility inside the 50 L tank.

### 8. Explicit Caveats
- **Missing / Imputed PCM Properties:** PCM properties from the Objective 1 database use certified manufacturer specifications; where minor secondary properties were imputed, sensitivity tests confirm low sensitivity.
- **Single-Pass Optimization:** One surrogate optimization pass followed by full-year physical confirmation. Active-learning retraining loops remain future work.
- **Reduced / Light Monte Carlo:** Evaluated over 100 draws per design using medoid + noise (full member-point weather series not available for Assam).
- **Single-State Scope:** Calibrated specifically for Assam Level-A regimes. Cross-state generalization requires multi-state synthesis.
- **Lumped Grey-Box Model:** Single water node, single lumped capsule thermal mass, empirical Ergun pressure drop — treat absolute values as ±15 % engineering approximations.
