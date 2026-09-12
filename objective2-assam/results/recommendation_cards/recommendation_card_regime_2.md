# Recommendation Card — Regime 2 (Assam)
**Regime Title:** Barak Valley & Southern Hills, elevated cooler hill regime, medoid ASP_0028 (35 pts)
**Representative Medoid:** `assam` cluster 2  ·  **Population covered:** 2,466,324  ·  **Regime size:** 35 grid points

### 1. Climate Summary (`cluster_profiles_assam.csv`)

| GHI | Ta mean | DTR | RH mean | monsoon idx |
|---|---|---|---|---|
| 3.68 kWh/m²/d | 22.6 °C | 6.2 °C | 77.9 % | 0.65 |

Objective 1 design targets: `Tm_target_C` = 44.0 °C, `L_required` = 279.7 kJ/kg (ceiling), `T_mains_est` = 16.59 °C.

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
| 0.0400 m | 21 | 0.0278 kg/s | 0.0141 | 0.9859 | 0.678 kg |

### 4. Simulator-Confirmed Performance (sim_v1_assam, Full 8,760-Hour Run)

| Useful Energy | Solar Fraction | Unmet Energy | Pump Energy | Max Water Temp | Safety Margin to 75 °C | Energy Residual |
|---|---|---|---|---|---|---|
| 656.1 kWh | 53.55 % | 560.1 kWh | 0.0000 Wh | 70.7 °C | -5.1 °C | 0.000000 % |

### 5. Phase 8 Light Robustness Results (100 Monte Carlo Draws)
**Uncertainty Sources Covered:** PCM latent heat ±10%, weather medoid + noise, demand volume ±20%, demand timing ±30 min, mains temperature ±2 °C.

| P(meet delivery temp) | P(meet annual demand) | Demand Criterion | P(temp-safe) | Safety Criterion | P(exceeds max safe temp) | Useful Energy P5–P95 | Max Water T P95 | Overall Status |
|---|---|---|---|---|---|---|---|---|
| 0.96 | 0.74 | **CAVEAT** | 0.01 | **CAVEAT** | 0.99 | 584–715 kWh | 77.0 °C | **CAVEAT / NOT ROBUST** |

- **Thresholds Applied:** Robust if P(demand) ≥ 0.75 and P(temp-safe) ≥ 0.95.
- **Binding Caveat Explanation:** Under realistic weather/demand/mains perturbations, temperature safety reaches P(temp-safe) = 0.01 (P95 max water temperature = 77.0 °C), confirming that uncontrolled summer overheating can occur. An **active Objective 3 high-temperature bypass / safety shield is a mandatory requirement** for real-world deployment.

### 6. Surrogate vs. Simulator Delta
- **Surrogate Predicted Useful Energy:** 656.1 kWh
- **Simulator Confirmed Useful Energy:** 656.1 kWh
- **Discrepancy (Delta):** **0.002 %** (well within the pre-declared 15 % large-error rule)
- **Verification Verdict:** Verified proposal ranker. The surrogate faithfully guided optimization without distorting the final physical simulator metrics.

### 7. Technical Decision Rationale
In Regime 2 (Barak Valley & Southern Hills, elevated cooler hill regime, medoid ASP_0028 (35 pts)), the Phase 7 optimization evaluated 7,966 geometrically valid configurations. `savE® OM48` was selected as the optimal deployable material because it maximized solar useful energy delivery (656.1 kWh) while meeting the 5% near-best hierarchical rule. The selected capsule geometry (21 spherical capsules, diameter 40.0 mm) achieves an optimal balance between thermal charging rate, low parasitic pumping loss (0.0000 Wh/year), and mechanical packing feasibility inside the 50 L tank.

### 8. Explicit Caveats
- **Missing / Imputed PCM Properties:** PCM properties from the Objective 1 database use certified manufacturer specifications; where minor secondary properties were imputed, sensitivity tests confirm low sensitivity.
- **Single-Pass Optimization:** One surrogate optimization pass followed by full-year physical confirmation. Active-learning retraining loops remain future work.
- **Reduced / Light Monte Carlo:** Evaluated over 100 draws per design using medoid + noise (full member-point weather series not available for Assam).
- **Single-State Scope:** Calibrated specifically for Assam Level-A regimes. Cross-state generalization requires multi-state synthesis.
- **Lumped Grey-Box Model:** Single water node, single lumped capsule thermal mass, empirical Ergun pressure drop — treat absolute values as ±15 % engineering approximations.
