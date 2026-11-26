# PHASE 7 -- ASSAM MULTI-OBJECTIVE OPTIMIZATION REPORT (safety-verified)

**Simulator:** `sim_v1_assam`  
**Safety limits (frozen `system_config_shared.yaml`):** PCM <= 65.0 C, water <= 75.0 C, 0 safety-violation sub-hours  
**Screened surrogate pool:** 7,966 designs; **simulator-verified:** 60; **safe:** 60  
**Verdict:** PASS -- every regime has a simulator-verified design inside the 65 C PCM / 75 C water limits  
**Max surrogate-vs-simulator useful-energy error (selected rows):** 0.12%

## Method

1,000 random designs per regime x PCM pair (3 PCMs + plain tank), geometry check + feasibility classifier (p >= 0.5), Phase 6 surrogates for ranking. The surrogates do not predict temperature safety, so each pair is walked in descending predicted useful energy through the real simulator until 5 safe designs are found or 40 simulations are spent. The 5% near-best rule and the hierarchy (unmet energy, solar fraction, pump energy, PCM mass, capsule count, safety margin) are then applied to the SAFE simulator-confirmed pool using simulated values. Plain tank is a reference row only.

## Search outcome per regime x PCM

| Regime | PCM | Simulated | Safe |
|---|---|---|---|
| 0 | NONE_plain_tank | 5 | 5 |
| 0 | savE® OM46 | 5 | 5 |
| 0 | savE® OM48 | 5 | 5 |
| 0 | savE® OM50 | 5 | 5 |
| 1 | NONE_plain_tank | 5 | 5 |
| 1 | savE® OM46 | 5 | 5 |
| 1 | savE® OM48 | 5 | 5 |
| 1 | savE® OM50 | 5 | 5 |
| 2 | NONE_plain_tank | 5 | 5 |
| 2 | savE® OM46 | 5 | 5 |
| 2 | savE® OM48 | 5 | 5 |
| 2 | savE® OM50 | 5 | 5 |

## Selected designs (simulator values)

| Role | Regime | PCM | d (mm) | N | Flow (kg/s) | Useful (kWh) | Solar frac | Unmet (kWh) | Max PCM (C) | PCM margin (C) | Max water (C) | Violations | Surrogate err (%) | Safe |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Optimal Regime 0 Candidate (safety-verified) | 0 | savE® OM46 | 40.9 | 12 | 0.0128 | 638.05 | 56.11% | 467.78 | 63.03 | 1.97 | 72.35 | 0 | 0.01 | PASS |
| Optimal Regime 1 Candidate (safety-verified) | 1 | savE® OM46 | 42.9 | 8 | 0.0323 | 652.08 | 55.58% | 488.33 | 63.11 | 1.89 | 72.39 | 0 | 0.12 | PASS |
| Optimal Regime 2 Candidate (safety-verified) | 2 | savE® OM46 | 43.1 | 8 | 0.0390 | 607.31 | 48.26% | 623.82 | 62.67 | 2.33 | 72.36 | 0 | 0.07 | PASS |
| Universal Cross-Regime Candidate (R0 OM48, safety-verified) | 0 | savE® OM48 | 41.0 | 9 | 0.0258 | 638.41 | 55.98% | 469.09 | 62.88 | 2.12 | 72.19 | 0 | 0.05 | PASS |
| Regime 0 Plain Tank Baseline | 0 | NONE_plain_tank | 40.0 | 12 | 0.0201 | 637.39 | 56.03% | 468.61 | 72.31 | n/a | 72.31 | 0 | 0.11 | PASS |

## Acceptance checks (computed)

| Check | Standard | Result |
|---|---|---|
| Max water temp | <= 75.0 C | PASS (max 72.39 C) |
| Max PCM temp | <= 65.0 C | PASS (max 63.11 C) |
| Safety violations | exactly 0 | PASS (max 0) |
| Energy residual | < 0.05% of collector input | PASS (max 0.0000%) |
| Every regime has a safe PCM design | 3 of 3 | PASS (3 of 3) |

Full candidate-level data: `phase7_safety_verified_candidates.csv`.

## Final verdict

**PASS -- every regime has a simulator-verified design inside the 65 C PCM / 75 C water limits**
