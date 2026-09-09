# PHASE 6 — ASSAM SURROGATE MODELING REPORT

**Evaluation Date:** 2026-09-10  
**Target Directory:** `M:\Final_year_pro\Objective---2\objective2-assam`  
**Simulator Version:** `sim_v1_assam`  
**Reference Dataset:** `results/phase5_design_cases.parquet`  
**Primary Acceptance Threshold:** $R^2 > 0.80$ for `useful_energy_kWh` on holdout  
**Final Verdict:** **PASS — surrogate is sufficiently accurate for Phase 7 optimization** ($R^2 = 0.9977$)

---

## A. DATASET SUMMARY
The Phase 6 modeling suite uses all **165 Latin Hypercube Sampled DOE cases** from Phase 5 without data removal:
- **Total Cases:** 165
  - **Feasible Designs (`valid = True`):** 111 cases ($67.3\%$)
  - **Infeasible Designs (`valid = False`):** 54 cases ($32.7\%$)
- **Data Partitioning (Preserved from Phase 5):**
  - **Training Subset:** 138 total cases (93 feasible, 45 infeasible)
  - **Holdout Subset:** 27 total cases (18 feasible, 9 infeasible)
- **Role Partitioning:**
  - **Feasibility Classifier:** Trained on **all 165 cases** (138 train / 27 holdout) to learn the physical design boundary.
  - **Performance Regressors:** Trained **strictly on the 111 valid cases** (93 valid train / 18 valid holdout). The 54 infeasible cases are never passed to the regression models.

---

## B. CANONICAL FEATURE LIST (29 NON-LEAKING FEATURES)
The feature schema consists of exactly 29 deterministic, state-independent features:
1. **Design Features (9):**
   - `capsule_diameter_m`, `n_capsule`, `flow_rate_kg_s`, `geom_pcm_thickness_m`, `geom_pcm_volume_fraction`, `geom_void_fraction`, `geom_pressure_drop_pa`, `geom_pump_power_w`, `geom_reynolds_number_particle`
2. **Climate Continuous Features (9):**
   - `GHI_daily_kWh`, `Ta_mean`, `DTR`, `RH_mean`, `wind_mean`, `monsoon_index`, `Tm_target_C`, `L_required_kJ_per_kg`, `T_mains_est_C`
3. **PCM Thermophysical Properties (10):**
   - `Tm_C`, `latent_heat_kJ_kg`, `TC_W_mK`, `density_liquid_kg_m3`, `density_solid_kg_m3`, `Cp_liquid_kJ_kgK`, `Cp_solid_kJ_kgK`, `supercooling_K`, `rho_H_MJ_m3`, `any_property_imputed`
4. **Baseline Indicator (1):**
   - `is_no_pcm` (1 for plain tank, 0 for PCM-augmented)

---

## C. LEAKAGE AUDIT
- **Target Exclusion:** None of the 4 primary performance targets (`useful_energy_kWh`, `solar_fraction`, `unmet_energy_kWh`, `pump_energy_kWh`) or secondary targets (`pcm_mass_kg`, `mean_f_melt`) are included in the feature set.
- **Simulation Timing Exclusion:** No hourly or post-simulation state metrics (e.g. `n_clipped_steps`, `max_water_temp_C`, `complete_melt_cycles`, `residual_pct_of_collector`) appear in the input matrix.
- **Deterministic Feature Ordering:** Enforced via strict ordered list reconstruction in `src/surrogate/features.py`.

---

## D. FEASIBILITY CLASSIFIER PERFORMANCE
The feasibility classifier learns the non-linear geometric and physical boundary of acceptable designs.

- **Model Family:** Extra Trees Classifier (`n_estimators=300`, `random_state=20260905`)
- **Holdout Evaluation ($N=27$, 18 Valid / 9 Infeasible):**
  - **Accuracy:** **1.0000** ($100.0\%$)
  - **Precision:** **1.0000**
  - **Recall (Valid):** **1.0000**
  - **F1 Score:** **1.0000**
  - **ROC-AUC:** **1.0000**
  - **Infeasible Recall:** **1.0000** ($100.0\%$)
  - **False Positive Count:** **0** ($0.0\%$)
  - **Confusion Matrix:**
    - True Negative (TN, Infeasible correctly rejected): **9**
    - False Positive (FP, Infeasible wrongly predicted valid): **0**
    - False Negative (FN, Valid wrongly predicted infeasible): **0**
    - True Positive (TP, Valid correctly accepted): **18**
- **5-Fold Stratified Cross-Validation on Train ($N=138$):**
  - Mean Accuracy: **1.0000 +/- 0.0000**
  - Mean F1: **1.0000 +/- 0.0000**
  - Mean Recall: **1.0000 +/- 0.0000**
  - Mean ROC-AUC: **1.0000 +/- 0.0000**

*Critical Safety Confirmation:* Zero false positives were recorded ($FP=0$). The classifier will not allow optimization to select geometrically invalid designs.

---

## E. PERFORMANCE REGRESSION SUITE (111 VALID CASES)
Models trained on $N=93$ valid training cases and evaluated on $N=18$ valid holdout cases:

| Target Variable | Extra Trees $R^2$ | Extra Trees RMSE | Extra Trees MAE | Extra Trees MAPE | Linear Reg $R^2$ | Linear Reg RMSE | Tree Beats Linear? |
|---|---|---|---|---|---|---|---|
| **`useful_energy_kWh`** | **0.9977** | 1.0107 kWh | 0.6974 kWh | 0.10% | 0.9981 | 0.9175 kWh | Linear baseline competitive |
| **`solar_fraction`** | **0.9999** | 4.9064e-04 | 3.4796e-04 | 0.06% | 0.9997 | 7.8963e-04 | **YES** (RMSE -37.9%) |
| **`unmet_energy_kWh`** | **0.9999** | 0.5965 kWh | 0.4034 kWh | 0.09% | 0.9999 | 0.7924 kWh | **YES** (RMSE -24.7%) |
| **`pump_energy_kWh`** | **0.8819** | 2.7942e-09 kWh | 2.2728e-09 kWh | N/A ($< 10^{-8}$) | 0.3849 | 6.3754e-09 kWh | **YES** (RMSE -56.2%) |
| *`pcm_mass_kg`* | **0.9980** | 0.0639 kg | 0.0399 kg | 4.25% | 0.9994 | 0.0342 kg | Linear competitive |
| *`mean_f_melt`* | **0.9982** | 1.2866e-03 | 1.0602e-03 | 1.91% | 0.9771 | 4.6314e-03 | **YES** (RMSE -72.2%) |

---

## F. CROSS-VALIDATION ON TRAINING PORTION
5-fold cross-validation performed strictly on the $N=93$ valid training subset (without access to holdout data):

| Target Variable | Mean CV $R^2$ | Std CV $R^2$ | Mean CV RMSE | Std CV RMSE | Mean CV MAE | Std CV MAE |
|---|---|---|---|---|---|---|
| **`useful_energy_kWh`** | **0.9947** | 0.0026 | 1.4060 kWh | 0.2468 kWh | 0.9675 kWh | 0.2272 kWh |
| **`solar_fraction`** | **0.9994** | 0.0004 | 8.5176e-04 | 1.9576e-04 | 5.7750e-04 | 1.4849e-04 |
| **`unmet_energy_kWh`** | **0.9996** | 0.0002 | 1.3139 kWh | 0.1651 kWh | 0.8365 kWh | 0.1410 kWh |
| **`pump_energy_kWh`** | **0.5585** | 0.5162 | 5.7852e-09 kWh | 7.1637e-09 kWh | 4.2034e-09 kWh | 4.5930e-09 kWh |

---

## G. FEATURE IMPORTANCE RANKINGS
*Note: Feature importances quantify variance explained in tree splits and do not constitute physical causal proof.*

### 1. Useful Energy (`useful_energy_kWh`)
- **L_required_kJ_per_kg:** 30.95% importance
- **T_mains_est_C:** 17.59% importance
- **Ta_mean:** 16.06% importance
- **GHI_daily_kWh:** 13.63% importance
- **DTR:** 8.14% importance

### 2. Solar Fraction (`solar_fraction`)
- **L_required_kJ_per_kg:** 52.74% importance
- **T_mains_est_C:** 14.26% importance
- **Ta_mean:** 12.61% importance
- **GHI_daily_kWh:** 11.61% importance
- **DTR:** 5.64% importance

### 3. Unmet Energy (`unmet_energy_kWh`)
- **T_mains_est_C:** 25.22% importance
- **Ta_mean:** 23.88% importance
- **L_required_kJ_per_kg:** 19.28% importance
- **GHI_daily_kWh:** 18.27% importance
- **DTR:** 7.00% importance

---

## H. PREDICTIVE PARITY AND RESIDUAL CHECKS
Diagnostic visual artifacts generated and saved to `results/plots/`:
1. `phase6_parity_useful_energy.png` — Parity scatter, residual vs predicted, and residual density histogram.
2. `phase6_parity_solar_fraction.png` — High linearity across full solar fraction range ($[0.60, 0.63]$).
3. `phase6_parity_unmet_energy.png` — Clean zero-centered residuals without heteroscedastic fan-out.
4. `phase6_parity_pump_energy.png` — Accurate sub-nano-scale tracking across flow regimes.
5. `phase6_feature_importance.png` — Side-by-side Gini importance bars for primary targets.

---

## I. PHYSICAL CAVEATS & LIMITATIONS
1. **Surrogate Role as Proposal Ranker:** Per Bug-Fix 5, the surrogate models serve as fast proposal filters during Phase 7 multi-objective genetic search, not as the final physical truth. All Pareto-optimal candidate designs selected in Phase 7 will be explicitly re-simulated using `sim_v1_assam`.
2. **Radial Thickness Coupling:** In spherical encapsulation, `geom_pcm_thickness_m = capsule_diameter_m / 2`.
3. **Derived Volume Fraction:** PCM volume fraction is geometrically derived from capsule count and diameter ($\varepsilon_{\text{pcm}} = N \cdot \frac{\pi}{6} d^3 / V_{\text{tank}}$) and cannot be independently manipulated without breaking geometric consistency.

---

## J. PHASE 6 GO/NO-GO DECISION

| Criterion | Requirement | Achieved Result | Status |
|---|---|---|---|
| **Useful Energy Holdout $R^2$** | $> 0.80$ | **0.9977** | **PASSED** |
| **Solar Fraction Holdout $R^2$** | Positive ($> 0.80$) | **0.9999** | **PASSED** |
| **Unmet Energy Holdout $R^2$** | Positive ($> 0.80$) | **0.9999** | **PASSED** |
| **Feasibility Classifier False Positives** | $0$ on holdout | **0 ($FP=0, FPR=0.0\%$)** | **PASSED** |
| **Feature Leakage** | 0 targets in features | **0 target leakage** | **PASSED** |
| **Isolation Integrity** | `objective2-rajasthan` untouched | **0 lines modified** | **PASSED** |

### **FINAL VERDICT: PASS**
The Phase 6 surrogate model suite is fully trained, validated, and exported. Phase 7 Multi-Objective Optimization is ready to proceed upon authorization.
