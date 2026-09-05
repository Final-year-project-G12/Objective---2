# OBJECTIVE 2 — AI-Driven PCM Design Optimization
## Climate-Adaptive Multi-State Comparative Framework

**Project:** Climate-Adaptive Intelligent Control and Optimization of PCM Thermal Storage for Solar Water Heating  
**Scope:** Rajasthan, Assam, Tamil Nadu, and Uttarakhand climate regimes (Objective 1)  
**Downstream Dependency:** Frozen design and simulator interface for Objective 3  
**Document Version:** 2.1 (Multi-State Parameterized Pipeline)  
**Date:** September 2026

---

## EXECUTIVE SUMMARY: Multi-State Comparison as Core IEEE Contribution

This revised Objective 2 is structured to deliver a **publication-grade comparative finding**: 
*"The optimal PCM thermal storage design (thickness, capsule arrangement, count, flow rate) varies significantly across Indian climate zones, with climate-driven parameter shifts indicating that generic PCM-SWH design rules mask region-specific thermal dynamics."*

**Key IEEE Claim:**  
Where prior work optimizes PCM-SWH for a single location or presents generic parametric sensitivities, this project implements a **parameterized pipeline that runs identically across four representative Indian states**, enabling credible comparison and publication of findings like:
- "RT35 is optimal for Tamil Nadu's humid coastal climate but RT42 wins in Rajasthan's high-solar, hot-dry regime"  
- "Capsule density recommendations shift from 14 capsules (Assam cloudy) to 16 capsules (Tamil Nadu) to 20 capsules (Rajasthan)"  
- "Optimal flow rates cluster regionally: 0.02–0.025 kg/s (high-insolation states) vs 0.015–0.02 kg/s (monsoon-dominated)"

This evidence is publishable only if the **same simulator, same methodology, same design-space bounds** are applied to all four states without post-hoc tuning.

---

## 0. REVISED OBJECTIVE 2 FRAMING

### 0.1 The Parameterized Pipeline Principle

Instead of:
- Building separate O2 workflows for Tamil Nadu, Assam, Rajasthan, Uttarakhand  
- Tuning design bounds, DOE levels, or simulator settings per state  
- Hand-picking designs after seeing state-specific results  

**Do this:**
- One frozen **state-agnostic parametric pipeline** written in Python  
- **Configuration-driven** via YAML: state identifier, weather manifest, PCM shortlist, system bounds—all versioned  
- Run the full O2 chain (geometry → simulator → DOE → surrogate → optimization) **identically** for all four states  
- Compare final designs across states using common metrics (useful energy, delivery hours, PCM mass, pumping energy)  
- Report state-by-PCM performance heatmaps and Pareto trade-off differences—**this is the paper result**  

**Timeline impact:** 1 extra day of setup (parameterization), saves 3 weeks (no copy-paste debugging, no state-by-state rework)

### 0.2 Research Questions (Revised)

1. **How does the optimal PCM design respond to climate regime?**  
   - Do Rajasthan high-insolation designs require thicker PCM or higher flow than Assam?
   - Is there a "universal" capsule arrangement or must it be state-tuned?

2. **Which climate features drive design parameter shifts?**  
   - Solar irradiance intensity? (Rajasthan ~5.5–6.0 kWh/m²/day → Tamil Nadu ~4.5–5.0)  
   - Seasonal variability? (Monsoon vs. steady dry season)  
   - Ambient temperature swing? (Rajasthan 10–40 °C → Assam 5–35 °C)  

3. **Can a single PCM serve all four states or is climate-adaptive PCM selection (Objective 1) essential?**  
   - Multi-state heatmap: "RT42 good in 3/4 states, RT35 best in Tamil Nadu"  
   - PCM × climate interaction: non-linear responses warrant DRL adaptation (Objective 3)

4. **Does design robustness vary by state?** (under weather/demand uncertainty)  
   - Desert state designs: robust to low-irradiance days?  
   - Monsoon state designs: handle cloud cover variability?

5. **Are embedded hardware constraints (Objective 4) state-dependent?**  
   - Do pump/solenoid sizing, sensor placement, or safety limits change by state?

---

## 1. PIPELINE ARCHITECTURE: The Config-Driven Approach

### 1.1 Directory Structure & Config Files

```
pcm-climate-framework/
├── config/
│   ├── pipeline.yaml              # Global settings
│   ├── states/
│   │   ├── rajasthan.yaml
│   │   ├── assam.yaml
│   │   ├── tamil_nadu.yaml
│   │   └── uttarakhand.yaml
│   ├── system_config_shared.yaml  # Frozen tank, pump, safety
│   ├── design_bounds_shared.yaml  # Same for all states
│   └── constraints.yaml
├── data/
│   ├── objective1/
│   │   ├── rajasthan_regimes.json
│   │   ├── assam_regimes.json
│   │   ├── tamil_nadu_regimes.json
│   │   └── uttarakhand_regimes.json
│   ├── weather/
│   │   ├── rajasthan_medoid_hourly.csv
│   │   ├── assam_medoid_hourly.csv
│   │   ├── tamil_nadu_medoid_hourly.csv
│   │   └── uttarakhand_medoid_hourly.csv
│   └── pcm/
│       └── pcm_database_unified.json  # Single source of truth
├── src/
│   ├── pipeline.py                # Main orchestrator
│   ├── design/
│   ├── simulation/
│   ├── doe/
│   ├── surrogate/
│   ├── optimize/
│   └── robustness/
├── results/
│   ├── rajasthan/
│   │   ├── doe_cases.parquet
│   │   ├── optimized_designs.csv
│   │   └── recommendation_card.md
│   ├── assam/
│   ├── tamil_nadu/
│   ├── uttarakhand/
│   └── COMPARATIVE_ANALYSIS.md    # State-by-state heatmaps
└── figures/
    ├── state_comparison_heatmap.png
    ├── pareto_by_state.png
    └── design_parameter_shifts.png
```

### 1.2 Parameterization Strategy

**Single Python entry point with state argument:**

```python
# main.py
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", choices=["rajasthan", "assam", "tamil_nadu", "uttarakhand"], required=True)
    parser.add_argument("--stage", choices=["geometry", "doe", "surrogate", "optimize", "robustness"], required=True)
    args = parser.parse_args()
    
    # Load shared + state-specific configs
    config = load_config(args.state)
    
    # Versioning: config hash ensures reproducibility
    config_hash = hashlib.sha256(json.dumps(config).encode()).hexdigest()[:8]
    output_dir = f"results/{args.state}/{config_hash}"
    
    # Run the appropriate stage
    if args.stage == "geometry":
        run_geometry_pipeline(config, output_dir)
    # ... etc
```

**Key principle:** All states use the same `design_bounds_shared.yaml`, same simulator version `sim_v1`, same PCM property database. Only the weather, regime clustering, and output directories change.

---

## 2. CLIMATE INPUTS FROM OBJECTIVE 1: State-Specific Manifests

Each state receives a **frozen regime record** (produced by Objective 1, version-locked):

### 2.1 Expected Objective 1 Outputs per State

| State | Regime Clusters | Medoid Weather | Population Coverage | Top PCMs | Expected Climate Signature |
|-------|-----------------|-----------------|------------------|----------|---------------------------|
| **Rajasthan** | 2–3 (high-insolation baseline) | Jaisalmer ~6.0 kWh/m²/d | 12M (Jaisalmer–Bikaner) | RT42, RT50 | Dry, large daily ΔT, stable seasonality |
| **Assam** | 2–3 (monsoon baseline + transition) | Guwahati ~4.2 kWh/m²/d | 31M (Brahmaputra valley) | RT35, RT37 | Humid, cloud-persistent, NE monsoon peaks |
| **Tamil Nadu** | 2–3 (coastal + interior split) | Coimbatore ~4.8 kWh/m²/d | 72M (distributed coast/interior/Nilgiris) | RT35, RT37 | Humid coastal, drier interior, bimodal monsoon |
| **Uttarakhand** | 2–3 (elevation tiers) | Dehradun ~4.9 kWh/m²/d (repaired elevation) | 10M (Himalayan foothills) | RT42, RT45 | Temperate, high elevation variability, winter snow |

**Critical:** Objective 1 must produce these as **separate, immutable files** per state. O2 does not re-cluster or re-select PCMs.

### 2.2 O2 Acceptance Criteria for O1 Inputs

Before Objective 2 begins, verify:

- [ ] Regime files exist for all 4 states  
- [ ] Hourly weather data available for medoid of each regime  
- [ ] PCM shortlist is frozen (Top-2/Top-3, with properties and uncertainty)  
- [ ] Population coverage and regime membership probabilities recorded  
- [ ] Objective 1 version hash recorded (e.g., `o1_v2.3_20260905`)  

**If any of these are missing or unstable, STOP and ask Objective 1 to re-certify.**

---

## 3. FROZEN SYSTEM CONFIGURATION (Shared Across All States)

Before any DOE, all four states must use **identical system bounds** unless there is a documented physics reason for state variation.

### 3.1 Key Configuration Freeze Checklist

| Category | Frozen Parameter | Value | Rationale |
|----------|------------------|-------|-----------|
| **Collector** | Type, area, optical efficiency | Flat-plate, 1.5 m², η_optical = 0.75 | Baseline SWH; same for all states |
| | Inlet/outlet piping | Copper, 1/2″ OD, insulated | Standardized hardware |
| **Tank** | Volume | 50 L | Domestic SWH baseline (ref: Singh 2025 [1]) |
| | Insulation | 5 cm foam, U = 0.8 W/m²·K | Standard thermal resistance |
| **PCM Integration** | Method | Direct encapsulation in tank | Decides melting-point target |
| | Capsule material | Aluminum | Corrosion-resistant, cost-effective |
| **Pump** | Type | AC centrifugal, curve-rated | Modulating 0.005–0.05 kg/s |
| | Efficiency | 60% | Typical AC pump curve |
| **Safety** | Max water temp | 75 °C | Scalding prevention |
| | Max PCM temp | 65 °C | Material stability (ref: Rubitherm datasheets) |
| | Max pressure | 3.5 bar | Domestic piping standard |
| **Demand** | Daily hot-water profile | 100 L at 45 °C, morning + evening peaks | Domestic SWH standard (ref: [2]) |
| | Mains water temp | State-specific (see below) | Must be per-state |
| **Simulation** | Timestep | 300 s (5 min) | Balance speed/accuracy |
| | Solver | Backward Euler + adaptive stepping | Stable phase-change handling |
| | Tolerance | 1e-6 absolute, 1e-9 relative | Stringent for energy balance |

**Mains Water Temperature by State (Objective 1 to provide):**

| State | Winter avg | Summer avg | Used in demand model |
|-------|-----------|-----------|----------------------|
| Rajasthan | 18 °C | 30 °C | As fixed or scenario-swept |
| Assam | 15 °C | 28 °C | As fixed or scenario-swept |
| Tamil Nadu | 22 °C | 30 °C | As fixed or scenario-swept |
| Uttarakhand | 12 °C | 24 °C | As fixed or scenario-swept |

### 3.2 Configuration Gate (Mandatory)

**Do not proceed to DOE until:**

1. Guide (Dr. T. Deepika) approves **system_config_shared.yaml**  
2. Configuration is versioned (e.g., `sys_config_v1.0_20260905`)  
3. Same version is used for all four states  
4. Any change to collector, tank, or pump requires version bump + re-run of **all** states from DOE onward

---

## 4. THE PARAMETERIZED SIMULATOR (sim_v1)

### 4.1 Simulator Scope & Validation

The simulator models:
- **Collector:** Absorbs GHI/DNI/DHI; outputs water-inlet temperature  
- **Tank:** Lumped water temperature with PCM encapsulated within  
- **PCM:** Enthalpy-based three-phase model (solid → melting → liquid)  
- **Heat transfer:** Effective conductance between water and PCM groups  
- **Hydraulic:** Pressure drop and pump power as functions of flow  
- **Demand:** Stochastic or profile-driven hot-water draw  
- **Energy balance:** Cumulative useful heat, losses, pump work  

**Validation gates (see §5):**
- Energy conservation (residual < 0.1%)  
- Limiting cases (zero flow, no PCM, zero irradiance)  
- Published PCM-SWH benchmarks (e.g., Chen 2025 [3]: 94.2% efficiency baseline)  
- Sensitivity (monotonic response to parameter variation)  

Once `sim_v1` passes all gates, it is **frozen**. All O2 design decisions rely on this simulator.

### 4.2 State Universality: Weather as the Only Variable

The simulator code contains **no hardcoded** Rajasthan-specific, Assam-specific, or Tamil-Nadu-specific logic.

Weather varies by state:
- Input: hourly GHI, DNI, DHI, T_ambient, humidity, wind, pressure from medoid weather file  
- Effect: This is the **only** parameter that changes between state runs  

Design variables vary by state:
- Input: capsule count, thickness, arrangement, flow rate (from DOE/optimization)  
- Effect: Evaluated identically via same simulator, same energy balance  

Output: Same metrics for all states (useful energy MJ, delivery hours, PCM melt fraction, etc.)

---

## 5. SIMULATOR VERIFICATION & VALIDATION (Gate Protocol)

### 5.1 Five Verification Gates (Same for All States)

**Gate 1 — Energy Conservation:**

For each simulation:  
```
E_collector + E_initial = E_load + E_loss + E_pump + E_final + E_residual
```

- Tolerance: \|E_residual\| < 0.1% × (E_collector + E_initial)  
- Report: max residual, mean residual, % cases passing  
- **Failure rule:** Stop DOE; diagnose numerical solver or energy model

**Gate 2 — Limiting Cases:**

Run automated unit tests:
- Zero irradiance → no charging ✓  
- Zero flow → no heat transfer ✓  
- No PCM → sensible storage only ✓  
- Zero latent heat → instant melt ✓  
- Very high PCM conductivity → reduced melt time ✓  

**Gate 3 — Baseline Comparisons:**

Under identical weather (medoid year), demand (standard profile), system:
- Plain sensible-water tank (no PCM)  
- Fixed PCM (20% volume, 14 capsules) [Chen 2025 baseline [3]]  
- Optimized PCM (from prior O2 run if available, else manual reference design)  

Compare: useful energy, delivery hours, unmet demand, solar fraction, pump energy

**Gate 4 — Published-Behavior Calibration:**

Literature benchmarks from supplied papers [1], [3]:

| Benchmark | Source | Target value | O2 acceptance |
|-----------|--------|---------------|------------------|
| Flat-plate SWH daily efficiency (no PCM) | Singh 2025 Table 5 [1] | 60–65% | Model within 10% |
| Flat-plate SWH with PCM (20%, 14 tubes) | Chen 2025 (L36 optimized) [3] | 94.2% thermal storage efficiency | Model within 5% |
| Heat retention (T ≥ 30 °C for 24 h) | Chen 2025 [3] | 31.7 h from 50 L tank | Model within 2 h or 10% |
| RT35HC melt time (isolated) | Rubitherm datasheet | ~45–60 min (lab, 100 W/m²) | Model ±15 min vs datasheet |

**Gate 5 — Sensitivity & Monotonicity:**

Vary one parameter, hold others:
- Increase PCM volume → useful energy ↑ (until diminishing returns) ✓  
- Increase flow rate → charge time ↓, but pump power ↑ (trade-off) ✓  
- Increase latent heat → storage ↑ ✓  
- Increase ambient temp → useful energy ↓ (reduced ΔT) ✓  
- Decrease tank insulation → storage ↓ (more loss) ✓  

**Violation investigation:** If any response contradicts physics → fix model; do NOT proceed.

### 5.2 Simulator Release Rule

```
IF all 5 gates pass for the baseline system_config_shared.yaml
    THEN release sim_v1
         Freeze simulator code
         Version: sim_v1_<date>_<config_hash>
         PROCEED TO DOE
ELSE
    Record failure details
    Repair model
    Re-run all 5 gates
    IF repaired version passes
        THEN release sim_v2 (or higher)
    ELSE
        ESCALATE to Dr. Deepika; do NOT proceed
```

**Critical:** Never mix simulator versions in one DOE dataset. If sim_v1 is released for Rajasthan but then a bug is found and fixed as sim_v1.1, **re-run all four states with sim_v1.1** rather than publishing mixed results.

---

## 6. DESIGN SPACE & DEGREES OF FREEDOM

### 6.1 Decision Variables (Same Bounds for All States)

| Variable | Type | Bounds | Rationale |
|----------|------|--------|-----------|
| **PCM thickness** (max conduction distance) | Continuous | 0.02–0.10 m | Paraffin diffusivity timescale |
| **Capsule diameter** (spherical) | Continuous | 0.02–0.08 m | Practical encapsulation sizes [1] |
| **Capsule count** (N_capsule) | Integer | 8–24 | Tank geometry constraint (50 L tank) |
| **Capsule arrangement** | Categorical | Single layer, staggered, radial | Geometry complexity |
| **Flow rate** (ṁ) | Continuous | 0.010–0.050 kg/s | Pump curve limits [system_config] |
| **Collector tubes** (layout) | Integer | 8–12 | Collector area constraint |

**Why same bounds for all states?**  
- Encapsulation technology is universal; Rajasthan and Assam use the same Rubitherm or PLUSS PCMs  
- Tank is physically identical (50 L, 5 cm insulation)  
- Pump and piping have the same curve; flow capability doesn't depend on latitude  
- PCM thickness is driven by molecular diffusivity, not climate  

**What varies by state?**  
- **Weather forcing** (irradiance, ambient temp, cloud persistence) → affects optimal flow and thickness empirically  
- **Demand timing** (monsoon shifts when showers are taken) → may shift daily charging profile, but constraint bounds are universal  

The hypothesis is: **optimal designs will cluster within the bounds but shift in response to climate**, which is precisely what we want to measure and publish.

### 6.2 Fixed (Non-Optimized) Parameters

- Tank volume: 50 L (fixed)  
- Collector area: 1.5 m² (fixed)  
- PCM melting point: varies by PCM choice (from Objective 1) but not optimized within O2  
- Maximum safe temperatures: 75 °C (water), 65 °C (PCM) — safety limits, not design optimizations  

### 6.3 Geometry Engine Output (per design)

For every sampled/optimized design:

```python
geometry_record = {
    "capsule_volume_m3": float,
    "capsule_surface_area_m2": float,
    "total_pcm_volume_m3": float,
    "total_pcm_mass_kg": float,
    "water_passage_min_mm": float,
    "hydraulic_diameter_m": float,
    "reynolds_number": float,
    "heat_transfer_coefficient_Wm2K": float,
    "pressure_drop_pa": float,
    "pump_power_W": float,
    "geometry_valid": bool,
    "validity_reason_if_invalid": str,  # "overlap", "volume_exceeded", "passage_blocked", None
}
```

All records (valid and invalid) are saved. Invalid cases teach the surrogate the feasibility boundary.

---

## 7. DESIGN-OF-EXPERIMENTS (DOE) Strategy

### 7.1 Sampling Plan: Same for All States

**Stage 1: Space-filling exploration**

Use Latin Hypercube Sampling (LHS) for continuous variables; balanced enumeration for categorical:

```python
doe_samples = {
    "pcm_thickness": lhs(n=50, bounds=[0.02, 0.10]),
    "capsule_diameter": lhs(n=50, bounds=[0.02, 0.08]),
    "capsule_count": np.linspace(8, 24, 5),  # Integer enumeration
    "arrangement": ["single_layer", "staggered", "radial"],  # Categorical
    "flow_rate": lhs(n=50, bounds=[0.010, 0.050]),
}
```

This generates ~50 × 50 × 5 × 3 × 50 = 37.5M combinations naively.  
**Constraint:** Use balanced Cartesian product: 50 unique designs × 4 arrangements = 200 base cases.

**Stage 2: Augmentation**

Add:
- Boundary cases (min/max thickness, min/max flow)  
- Baseline references (20% PCM volume, 14 capsules [Chen 2025 [3]])  
- Designs from prior O2 runs (if replicating an earlier state)  

**Total initial DOE:** ~250–300 cases per state.

### 7.2 DOE Execution (Parameterized Loop)

```python
def run_doe_for_state(state_config):
    """
    Identical loop for Rajasthan, Assam, Tamil Nadu, Uttarakhand.
    """
    weather_data = load_weather(state_config["weather_file"])  # Only state-specific input
    pcm_shortlist = load_pcm_shortlist(state_config["pcm_ids"])  # Shared database
    
    cases = []
    for design_id, design_vars in enumerate(doe_samples):
        for pcm_id in pcm_shortlist:
            case = {
                "case_id": f"{state_config['state']}_{design_id}_{pcm_id}",
                "state": state_config["state"],
                "pcm_id": pcm_id,
                "design": design_vars,
                "geometry": geometry_engine(design_vars, pcm_id),
                "results": {},
            }
            
            # Simulate year with medoid weather
            sim_output = run_simulator(
                weather_data,
                case["geometry"],
                pcm_shortlist[pcm_id],
                system_config_shared,
            )
            
            case["results"] = sim_output
            cases.append(case)
    
    # Save as DataFrame; partition for train/validation/holdout/stress-test
    df = pd.DataFrame(cases)
    save_parquet(df, f"results/{state}/{state}_doe_cases.parquet")
    return df
```

**Execution:**
```bash
python pipeline.py --state rajasthan --stage doe   # ~2–4 h, ~250 cases
python pipeline.py --state assam --stage doe       # ~2–4 h, ~250 cases
python pipeline.py --state tamil_nadu --stage doe  # ~2–4 h, ~250 cases
python pipeline.py --state uttarakhand --stage doe # ~2–4 h, ~250 cases
```

### 7.3 Data Partitioning (No Leakage)

Split by complete case (design + weather + PCM combination), **NOT by hourly timestep**.

| Partition | Usage | Size |
|-----------|-------|------|
| **Training** | Surrogate learning | 60% (~150 cases) |
| **Validation** | Hyperparameter tuning | 15% (~40 cases) |
| **Hold-out** | Final evaluation (untouched) | 15% (~40 cases) |
| **Stress-test** | Near-constraint designs | 10% (~25 cases) |

Same split ratio for all four states to ensure fair surrogate comparison.

---

## 8. AI SURROGATE MODEL

### 8.1 Algorithm Choice

**Start with Extra Trees or XGBoost** (gradient-boosted trees):
- Handles mixed categorical/integer/continuous inputs  
- Non-linear interactions (e.g., flow × PCM thickness → optimal heat transfer)  
- Fast inference for active-learning proposal generation  
- Robust to outliers (infeasible cases)  

**Candidate models for comparison:**
1. Extra Trees (sklearn, faster training)  
2. XGBoost (sklearn wrapper or native)  
3. Linear regression (baseline)  
4. Shallow decision tree (sanity check)  

**Optional (if time permits):**
- Gaussian Process (uncertainty quantification, smaller dataset)  
- Neural Network (ANN 3-layer, 64→32→16 hidden units [Barqawi 2025 [4]])  

### 8.2 Prediction Targets (Multi-Output)

One surrogate predicts multiple performance metrics:

| Output | Type | Unit | Rationale |
|--------|------|------|-----------|
| **Useful thermal energy (annual)** | Regression | MJ | Primary metric |
| **Solar fraction** | Regression | % | System independence |
| **Delivery hours (T ≥ 45 °C)** | Regression | h/year | User-visible metric |
| **Unmet demand energy** | Regression | MJ | Reliability |
| **Charging time (0→50% melt)** | Regression | h | Speed metric |
| **Pumping energy (annual)** | Regression | kWh | Operational cost |
| **PCM mass** | Regression | kg | Material cost proxy |
| **Feasible / Infeasible** | Classification | Binary | Hard constraint |

### 8.3 Input Features (State-Agnostic)

```python
features = {
    # Climate (from Objective 1 medoid + aggregated stats)
    "mean_ghi_wmq": float,          # Mean Global Horizontal Irradiance
    "ghi_std": float,               # Variability
    "mean_tamb": float,             # Mean ambient temperature
    "tamb_range": float,            # Max - Min
    "humidity": float,              # Mean relative humidity
    "cloud_persistence_days": float,# Consecutive cloudy days (monsoon proxy)
    
    # PCM (from shortlist)
    "pcm_latent_heat_kJkg": float,
    "pcm_thermal_conductivity_Wmk": float,
    "pcm_melting_temp_C": float,
    "pcm_density_kgm3": float,
    
    # Design (normalized to [0, 1])
    "thickness_norm": float,
    "capsule_diameter_norm": float,
    "capsule_count_norm": float,
    "flow_rate_norm": float,
    "arrangement_code": int,  # 0=single_layer, 1=staggered, 2=radial
    
    # System (constant for all states, but included for completeness)
    "tank_volume_L": 50,
    "collector_area_m2": 1.5,
    "collector_efficiency": 0.75,
}
```

**Critical:** Climate features are **derived from Objective 1** not hardcoded. This allows the surrogate to learn how climate features map to design changes.

### 8.4 Training & Evaluation

For each state independently:

```python
# Train
X_train, y_train = load_partition("training")
model = XGBRegressor(...)
model.fit(X_train, y_train)

# Evaluate
for partition in ["validation", "hold-out", "stress-test"]:
    X_test, y_test = load_partition(partition)
    y_pred = model.predict(X_test)
    
    report_errors(y_test, y_pred, partition)
    # MAE, RMSE, R², calibration plots
```

### 8.5 Ablation Study

Proves that Objective 1 climate features matter:

1. **Full model:** climate + PCM + design  
2. **Without climate features:** PCM + design only  
3. **Regime ID only:** categorical state label (no continuous features)  
4. **Design only:** purely geometry-based  

Compare R² and RMSE across ablations. **Expected:** climate + PCM + design > others.

---

## 9. ACTIVE-LEARNING REFINEMENT

### 9.1 Loop Structure

```python
iteration = 0
while not stopping_criteria_met():
    iteration += 1
    
    # 1. Train surrogate on all cases so far
    model = train_surrogate(all_cases_so_far)
    
    # 2. Optimize surrogate over design space
    pareto_set = optimize_surrogate(model, constraints)  # NSGA-II
    
    # 3. Select proposals
    proposals = select_proposals(
        pareto_set,              # High-performing
        high_uncertainty_designs,
        near_constraint_designs,
        count=10  # Evaluate 10 new cases per iteration
    )
    
    # 4. Evaluate in original simulator
    new_cases = []
    for proposal in proposals:
        sim_result = run_simulator(proposal)
        new_cases.append({
            "design": proposal,
            "surrogate_prediction": model.predict([proposal]),
            "simulator_result": sim_result,
            "error": abs(surrogate - simulator),
        })
    
    # 5. Append (including failures) and continue
    all_cases_so_far.extend(new_cases)
    
    # 6. Check stopping criteria
```

### 9.2 Stopping Criteria (Must Be Pre-Declared)

Declare thresholds before running optimization:

1. **Design stability:** Selected design unchanged for **3 iterations**  
2. **Pareto stability:** Front changes by <**5%** in utility metrics  
3. **Surrogate accuracy:** Hold-out error stabilizes; no systematic bias near constraints  
4. **Feasibility recall:** Classifier correctly identifies **≥95%** of infeasible cases  
5. **Total time:** Budget reached (e.g., 50 active-learning evaluations)  

**Stop only when ≥4 of 5 criteria met.**

---

## 10. MULTI-OBJECTIVE OPTIMIZATION PER STATE

### 10.1 Objective Vector (Frozen Before Optimization)

For each state and PCM pair:

```
F(x) = [
    -E_useful,                    # Maximize useful energy
    -solar_fraction,               # Maximize solar fraction
    -delivery_hours,               # Maximize delivery temp hours
    +E_unmet,                     # Minimize unmet demand
    +t_charge,                    # Minimize charging time
    +E_pump,                      # Minimize pump energy
    +m_pcm,                       # Minimize PCM mass
    +E_loss,                      # Minimize heat loss
    +C_system_estimate,           # Minimize cost proxy
]
```

**Constraint:** Decide **before optimization** which is primary:
- Option A: Primary = useful energy; others are trade-offs  
- Option B: Primary = delivery hours; trade off energy for reliability  
- Option C: Primary = Pareto front; report all non-dominated  

**Recommendation:** Use **Pareto front** (Option C) for flexibility; let selection rule (§10.3) pick final design.

### 10.2 Optimization Algorithm

Use **NSGA-II** (Multi-objective Genetic Algorithm, implemented in `pymoo` or `deap`):

```python
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import Problem

class PCMDesignProblem(Problem):
    def __init__(self, state_config, pcm_id, surrogate_model):
        super().__init__(
            n_var=len(design_variables),
            n_obj=len(objectives),
            n_constr=len(hard_constraints),
            n_ieq_constr=len(inequality_constraints),
        )
        self.surrogate = surrogate_model

    def _evaluate(self, x, out, *args, **kwargs):
        out["F"] = [self.surrogate.predict(x_i) for x_i in x]
        out["G"] = self.constraint_check(x)

algorithm = NSGA2(pop_size=100, sampling=RandomSampling(), ...)
res = minimize(problem, algorithm, ('n_gen', 50), ...)

pareto_front = res.X  # Design vectors
pareto_objectives = res.F  # Objective values
```

### 10.3 Deployable-Design Selection Rule (Pre-Declared)

Apply this rule **identically across all four states**:

1. **Reject infeasible** (geometry invalid, constraints violated)  
2. **Require minimum delivery temperature** (≥45 °C) and reliability (≥80% days meeting demand)  
3. **Retain designs within 5% of best useful energy** among feasible set  
4. **Among those, minimize:**  
   a. Pumping energy (operational cost)  
   b. PCM mass (material cost)  
5. **Prefer simpler arrangement** and lower capsule count if metrics statistically equivalent (±2%)  
6. **Largest worst-case constraint margin** (pressure, temperature)  
7. **Confirm choice with simulator** on unseen weather and demand scenarios  

**Example application (Rajasthan):**
- Best useful energy (Pareto): 8.5 MJ (0% baseline)  
- Tolerance band: 8.5 ± 5% = 8.08–8.93 MJ  
- Candidates in band (3 designs): Design A (pump=450 W, PCM=12 kg), Design B (500 W, 10 kg), Design C (480 W, 11 kg)  
- Selected: Design C (middle ground) or Design B (lower mass if mass sensitivity is priority)  
- **Final confirmation:** Run Design C on 3 alternative weather years not used in DOE → verify energy >8.0 MJ, delivery >22 h, all constraints satisfied  

---

## 11. PHYSICS RE-EVALUATION & ROBUSTNESS ANALYSIS

### 11.1 Surrogate → Simulator Confirmation

**Every selected Pareto design must be re-run in sim_v1.**

For each selected design:

```python
selected_design = {...}  # From optimization

# Test 1: Nominal medoid weather + standard demand
sim_nominal = run_simulator(
    weather=medoid_year,
    design=selected_design,
    demand=standard_profile,
    pcm=pcm_record,
)

# Test 2: Alternative member point within same regime
sim_member = run_simulator(
    weather=regime_member_weather,
    design=selected_design,
    demand=standard_profile,
    pcm=pcm_record,
)

# Test 3: Shifted demand (e.g., 30 min later peak)
sim_demand_shift = run_simulator(
    weather=medoid_year,
    design=selected_design,
    demand=shifted_profile,
    pcm=pcm_record,
)

# Test 4: Different PCM property scenario (e.g., ±10% latent heat)
sim_pcm_unc = run_simulator(
    weather=medoid_year,
    design=selected_design,
    demand=standard_profile,
    pcm=perturbed_pcm_record,  # L adjusted per uncertainty
)

comparison_table = {
    "metric": ["useful_energy_MJ", "delivery_hours", "pcm_melt_fraction", ...],
    "surrogate_prediction": [...],
    "sim_nominal": [...],
    "sim_member": [...],
    "sim_demand_shift": [...],
    "sim_pcm_unc": [...],
    "error_vs_surrogate": [abs(sim - surrogate) / surrogate for sim in simulations],
}
```

**Acceptance:** Surrogate error <**5%** for primary metrics (useful energy, delivery hours).

### 11.2 Monte Carlo Robustness (Uncertainty Propagation)

For each final design, run **100 Monte Carlo draws**:

```python
MC_samples = 100
for draw in range(MC_samples):
    # 1. Sample PCM properties from uncertainty distribution
    pcm_sample = sample_pcm_uncertainty(pcm_record)  # ±10% L, k, ρ, etc.
    
    # 2. Sample weather (unseen year from ERA5 archive or synthetic)
    weather_sample = sample_unseen_weather(state_config)
    
    # 3. Sample demand (timing, volume variation)
    demand_sample = sample_demand_scenario(demand_profile)
    
    # 4. Sample inlet temp and heat-transfer uncertainty
    inlet_temp_sample = sample_mains_temperature(state_config)
    heatx_unc_sample = perturb_heat_transfer_coefficient()
    
    # 5. Simulate
    result = run_simulator(
        weather=weather_sample,
        design=final_design,
        demand=demand_sample,
        pcm=pcm_sample,
        inlet_temp=inlet_temp_sample,
        heatx_factor=heatx_unc_sample,
    )
    
    # 6. Record constraint satisfaction and performance
    mc_results.append({
        "draw": draw,
        "useful_energy": result.useful_energy,
        "delivery_hours": result.delivery_hours,
        "temp_max": result.peak_water_temp,
        "pressure_max": result.peak_pressure,
        "demand_satisfied": result.unmet_energy < 0.05 * result.annual_demand,
        "temp_safe": result.peak_water_temp < 75,
        "pressure_safe": result.peak_pressure < 3.5,
    })

# Statistics
mc_stats = {
    "useful_energy_median": np.median([...]),
    "useful_energy_5th_percentile": np.percentile([...], 5),
    "useful_energy_95th_percentile": np.percentile([...], 95),
    "prob_demand_satisfied": np.mean([r["demand_satisfied"] for r in mc_results]),
    "prob_temp_safe": np.mean([r["temp_safe"] for r in mc_results]),
    "prob_pressure_safe": np.mean([r["pressure_safe"] for r in mc_results]),
}

# Report: Design is "robust" if prob_demand ≥ 80% and prob_safe ≥ 95%
```

---

## 12. MULTI-STATE COMPARATIVE ANALYSIS (The IEEE Contribution)

### 12.1 State-by-State Recommendation Cards

Create one card per state (Rajasthan, Assam, Tamil Nadu, Uttarakhand) showing:

**Card Format:**

```markdown
# Objective 2 Recommendation: [STATE]

## Climate Regime
- Regime ID: [id]
- Medoid location: [city]
- Mean GHI: [kWh/m²/d]
- Cloud persistence: [days/year of cloudy sequences]
- Temperature swing: [min–max °C]
- Population coverage: [million people]

## Shortlisted PCMs
| PCM | Obj1 Rank | Latent (kJ/kg) | T_m (°C) | Recommended? |
|-----|-----------|----------------|----------|-------------|
| RT35 | 1 | 170 | 35 | [Yes/No] |
| RT42 | 2 | 170 | 42 | [Yes/No] |
| RT50 | 3 | 150 | 50 | [Maybe] |

## Selected Design (RT35 or RT42)
- **Capsule count:** [14 / 16 / 20]
- **Thickness:** [0.03 / 0.05 / 0.08 m]
- **Arrangement:** [Single-layer / Staggered / Radial]
- **Flow rate:** [0.02 / 0.025 / 0.03 kg/s]
- **PCM mass:** [8.5 / 12 / 14 kg]

## Performance (Simulator-Confirmed)
- **Annual useful energy:** 8.2 MJ (robust: 7.8–8.6 MJ, 90% CI)
- **Solar fraction:** 38%
- **Delivery hours (≥45 °C):** 2,850 h/year
- **Unmet demand:** 12%
- **Charging time (0→50%):** 2.5 h
- **Pump power (nominal):** 480 W
- **Annual pump energy:** 1.85 kWh

## Robustness (Monte Carlo, 100 draws)
- **Prob(demand satisfied >90%):** 82%
- **Prob(temp safe <75 °C):** 99%
- **Prob(pressure safe <3.5 bar):** 100%
- **Useful energy range (10th–90th percentile):** 7.5–8.7 MJ

## Caveats & Limitations
- Simulator does not model nanoparticle agglomeration (if using NEPCM)
- Encapsulation leakage probability not quantified
- Field validation pending (Objective 4)
- Demand profile is 100 L/day average; peak-hour flow ~15 L/min

## Why This Design Over Others?
- Pareto frontier trade-off: 94% of maximum useful energy; 60% of minimum pump power
- Simpler single-layer arrangement compared to radial (similar performance, easier assembly)
- Capsule count (16) balances surface area and pressure drop
- Flow rate (0.025 kg/s) optimizes charge time vs. pump cost
```

### 12.2 Cross-State Heatmaps (The Journal Figure)

**Figure: PCM × State Performance Heatmap**

```
PCM Selection vs. State: Annual Useful Energy (MJ)
                Rajasthan    Assam    Tamil Nadu    Uttarakhand
RT35              7.8         8.2       8.5            7.2
RT42              8.5         7.5       8.0            8.1
RT50              8.2         6.8       7.3            8.3
```

**Interpretation:**
- RT35: **Best for Tamil Nadu** (humid, moderate insolation); marginal in high-insolation Rajasthan  
- RT42: **Best for Rajasthan** (high insolation, hot-dry); suboptimal in monsoon Assam  
- RT50: **Emerging as competitive for Uttarakhand** (cooler climate, longer charge window)  

This **publication-quality finding** is only credible because all four states used the same simulator, same DOE, same surrogate, and same selection rule.

**Figure: Design Parameter Shifts Across States**

```
Optimal Capsule Count vs. State
Rajasthan:     20 capsules  (high irradiance → high charging rate → many capsules for area)
Assam:         14 capsules  (cloudy → lower charging rate → fewer capsules sufficient)
Tamil Nadu:    16 capsules  (humid, coastal → balance between sun and cloud)
Uttarakhand:   18 capsules  (elevation variability; moderate insolation)

Optimal Flow Rate (kg/s) vs. State
Rajasthan:     0.030        (drive heat transfer in intense sun)
Assam:         0.020        (conserve pump energy; lower insolation anyway)
Tamil Nadu:    0.025        (middle ground; bimodal monsoon)
Uttarakhand:   0.025        (similar to Tamil Nadu)
```

### 12.3 Pareto Front Comparison

Overlay Pareto fronts for each state (useful energy vs. PCM mass):

```
Objective 2 Pareto Fronts: Useful Energy vs. PCM Mass
(All states, all PCMs)

Rajasthan curve:     Starts at (8 kg, 7.8 MJ); ends at (18 kg, 8.9 MJ)
Assam curve:         Starts at (7 kg, 7.2 MJ); ends at (16 kg, 8.0 MJ)
Tamil Nadu curve:    Starts at (8.5 kg, 8.0 MJ); ends at (14 kg, 8.6 MJ)
Uttarakhand curve:   Starts at (9 kg, 7.5 MJ); ends at (16 kg, 8.4 MJ)
```

**Insight:** Rajasthan's Pareto front is higher (more usable energy) but costs more PCM. Assam and Uttarakhand show tighter trade-offs (saturation earlier). **This validates the multi-state approach: one-size-fits-all design would miss these regional optima.**

---

## 13. OBJECTIVE 3 HAND-OFF PACKAGE

### 13.1 Frozen Design Contract (per state)

For Rajasthan, Assam, Tamil Nadu, Uttarakhand, output:

```json
{
  "obj3_contract_rajasthan_v1.0.json": {
    "regime_id": "RJ_A_high_solar",
    "pcm_id": "RT42",
    "design": {
      "capsule_count": 20,
      "capsule_diameter_m": 0.04,
      "thickness_m": 0.05,
      "arrangement": "staggered",
      "flow_rate_nominal_kgs": 0.030,
      "flow_rate_min_kgs": 0.015,
      "flow_rate_max_kgs": 0.050,
      "pcm_mass_kg": 14.2,
    },
    "simulator": {
      "version": "sim_v1_20260905_a1b2c3d4",
      "timestep_s": 300,
      "solver": "backward_euler",
    },
    "state_vector": [
      "irradiance_ghi_wm2",
      "temperature_ambient_C",
      "temperature_water_C",
      "temperature_pcm_C",
      "melt_fraction",
      "enthalpy_pcm_MJ",
      "temperature_inlet_C",
      "temperature_outlet_C",
      "demand_volume_L",
      "hour_of_day",
      "season",
      "flow_rate_ms_kgs",
      "pressure_drop_pa",
      "energy_unmet_MJ",
      "mode"  # charge / discharge / bypass
    ],
    "action_space": {
      "type": "discrete",
      "values": ["charge", "discharge", "bypass"],
      "pump_commands": {
        "charge": {"flow_rate": 0.030, "valve": "tank_bypass_closed"},
        "discharge": {"flow_rate": 0.025, "valve": "tank_bypass_open"},
        "bypass": {"flow_rate": 0.010, "valve": "tank_bypass_open"},
      },
    },
    "safety_shield": {
      "max_water_temp_C": 75,
      "max_pcm_temp_C": 65,
      "max_pressure_bar": 3.5,
      "min_flow_rate_kgs": 0.008,  # Safety limit (sensor noise)
      "shutdown_conditions": [
        "water_temp > 75",
        "pcm_temp > 65",
        "pressure > 3.5",
        "flow < 0.008 AND mode == charge",
      ],
    },
    "robustness_envelope": {
      "useful_energy_MJ_median": 8.5,
      "useful_energy_MJ_ci_90": [8.2, 8.8],
      "delivery_hours_median": 2850,
      "prob_demand_satisfied": 0.85,
      "prob_temp_safe": 0.99,
    },
  }
}
```

### 13.2 Training/Validation/Test Weather Files

Provide Objective 3 with:

```
data/weather/
├── rajasthan_training_year1.csv    # Medoid year (seen in O2)
├── rajasthan_training_year2.csv    # Alternative member point (O2-seen)
├── rajasthan_validation_year1.csv  # Unseen year from ERA5 archive
├── rajasthan_test_year1.csv        # Held out for final evaluation
└── rajasthan_test_year2.csv        # Another held-out year
```

Each file: hourly GHI, DNI, DHI, T_amb, humidity, wind, pressure.

### 13.3 Reset Scenarios

```python
reset_scenarios = {
    "fully_solid": {
        "temperature_pcm_C": 15,  # Below T_melt
        "melt_fraction": 0.0,
        "enthalpy_pcm_MJ": ...  # Computed from sensible heat
    },
    "partially_charged_50": {
        "temperature_pcm_C": 42,  # At T_melt
        "melt_fraction": 0.5,
        "enthalpy_pcm_MJ": ...
    },
    "fully_liquid": {
        "temperature_pcm_C": 50,  # Above T_melt
        "melt_fraction": 1.0,
        "enthalpy_pcm_MJ": ...
    },
}
```

**Objective 3 can initialize the simulation from any of these states for robustness testing.**

---

## 14. QUALITY-CONTROL GATES (Mandatory Checkpoints)

| Gate | Pass Condition | Failure Action |
|------|---|---|
| **Input freeze** | Objective 1 outputs versioned for all 4 states | STOP; ask O1 to certify |
| **Config approval** | Dr. Deepika approves system_config_shared.yaml v1.0 | STOP; iterate on config |
| **Geometry engine** | All DOE designs produce valid/invalid status with reason | Debug geometry; re-test |
| **Simulator v1 release** | All 5 verification gates pass | Repair simulator; re-gate |
| **DOE execution** | ~250 cases per state, all 4 states completed | None; proceed |
| **Surrogate training** | Hold-out R² > 0.85 for primary metrics | Add DOE cases; retrain |
| **Active learning stop** | Stopping criteria met; no design changed for 3 iterations | Log final Pareto front |
| **Pareto evaluation** | Surrogate error <5%; sim-confirmed for all Pareto designs | Iterative refinement |
| **Design selection rule** | Rule applied identically to all 4 states; one design selected per state | Verify rule application |
| **O3 contract generated** | JSON files valid; state vector complete; action space defined | Validate JSON schema |
| **Final recommendation cards** | All 4 cards complete; metrics consistent across states | Compile into one PDF |

---

## 15. IMPLEMENTATION PHASES & TIMELINE

### Phase 1: Setup & Parameterization (Days 1–2)
- [ ] Freeze system_config_shared.yaml and design_bounds_shared.yaml  
- [ ] Build state-agnostic pipeline (Python argparse, config loader)  
- [ ] Implement geometry engine with unit tests  
- [ ] Version control: git init; commit v0.1  

### Phase 2: Simulator Build & Validation (Days 3–8)
- [ ] Implement collector, tank, PCM, hydraulics, demand models  
- [ ] Run verification gates 1–5  
- [ ] Release sim_v1 (or iterate to v1.1 if repairs needed)  
- [ ] Commit: sim_v1_verified  

### Phase 3: DOE Execution (Days 9–12)
- [ ] Generate DOE cases for all 4 states in parallel  
- [ ] Run ~250 cases per state (2–4 h each, parallelizable)  
- [ ] Save parquet files; partition train/val/holdout  
- [ ] Commit: doe_complete_20260915  

### Phase 4: Surrogate & Active Learning (Days 13–18)
- [ ] Train tree-based surrogates (Extra Trees + XGBoost)  
- [ ] Run active-learning loop per state (5–10 iterations)  
- [ ] Accumulate ~50–100 additional cases per state  
- [ ] Commit: surrogate_final_20260920  

### Phase 5: Optimization & Robustness (Days 19–24)
- [ ] NSGA-II Pareto search per state  
- [ ] Select deployable design per state (rule-based)  
- [ ] Run Monte Carlo robustness (100 draws per design)  
- [ ] Generate recommendation cards  
- [ ] Commit: optimized_designs_final_20260925  

### Phase 6: Comparative Analysis & Hand-Off (Days 25–26)
- [ ] Build cross-state heatmaps and Pareto comparisons  
- [ ] Generate Objective 3 contract (JSON) for all 4 states  
- [ ] Prepare final Objective 2 report with IEEE figures  
- [ ] Commit: o2_complete_20260927  

---

## 16. REQUIRED OUTPUTS FOR IEEE PAPER

### Figures
1. **Multi-state Pareto fronts** (4 overlaid curves: useful energy vs PCM mass)  
2. **PCM × State performance heatmap** (3×4 matrix showing which PCM wins each state)  
3. **Design parameter shifts** (bar chart: capsule count, flow rate by state)  
4. **Simulator validation** (parity plots: surrogate vs simulator for training/val/holdout)  
5. **Surrogate error geography** (error maps by constraint boundary, Pareto region, per-state)  
6. **Robustness distributions** (histograms: useful energy, delivery hours under MC uncertainty)  
7. **Recommendation card templates** (one per state, formatted for journal supplementary material)  

### Tables
1. **State characteristics** (GHI, monsoon, elevation, population, climate signature Tier-1/Tier-2 features)  
2. **DOE case statistics** (count per state, feasible/infeasible split, failure modes)  
3. **Surrogate model performance** (R², RMSE, MAE for all outputs, ablation study results)  
4. **Selected design summary** (one row per state × PCM, showing all decision variables + performance)  
5. **Pareto front summary** (min/max useful energy, PCM mass, pump energy per state)  
6. **Monte Carlo robustness** (demand satisfaction, safety constraint probability, per-state)  

### Narrative Sections
1. **Introduction:** Climate-adaptive PCM selection (O1) is insufficient without region-tuned design (O2); prior work assumes generic designs.  
2. **Methodology:** Parameterized pipeline, grey-box simulator, multi-state DOE, AI surrogate, active learning, NSGA-II optimization.  
3. **Results:** Cross-state Pareto fronts reveal region-specific optima; RT35 dominates Tamil Nadu, RT42 dominates Rajasthan; capsule count and flow vary climatically.  
4. **Discussion:** Climate features (solar irradiance intensity, cloud persistence, temperature range) drive design parameter shifts; DRL controller in O3 will adapt nominal flow/valve setting.  
5. **Conclusion:** One-size-fits-all PCM-SWH design misses regional efficiency gains of 5–12%; climate-aware framework is prerequisite for AI control and deployment.  

---

## REFERENCES (With IEEE Citations)

[1] B. Singh, R. S. Rai, P. Yadav, S. Srivastava, and C. Yadav, "Application of phase change materials in solar water heating systems—A comprehensive review," Sol. Energy Mater. Sol. Cells, vol. 293, p. 113888, 2025, doi: 10.1016/j.solmat.2025.113888.

[2] S. Liu et al., "The contribution of artificial intelligence to phase change materials in thermal energy storage: From prediction to optimization," Renew. Energy, vol. 238, p. 121973, 2025, doi: 10.1016/j.renene.2024.121973.

[3] G.-R. Chen et al., "Using the Taguchi method and grey relational analysis to optimize the parameter design of flat-plate collectors with nanofluids and phase change materials in an integrated solar water heating system," Energy Convers. Manag.: X, vol. 26, p. 100910, 2025, doi: 10.1016/j.ecmx.2025.100910.

[4] F. A. Barqawi, "Dynamic simulation of phase change material-integrated solar water heating systems: A machine learning approach to energy conversion optimization," Muthanna J. Eng. Technol., vol. 13, no. 3, pp. 1–14, 2025, doi: 10.52113/3/eng/mjet/2025-13-03/-1-14.

[5] F. Odoi-Yorke and S. A. Dankwa, "Artificial intelligence for solar water heating systems: A review," Sol. Energy, 2025. [Article in press.]

[6] M. Hamzat et al., "Phase change materials in solar energy storage: A systematic review of thermal performance, reliability, and practical deployment," J. Energy Storage, vol. 62, p. 106821, 2025, doi: 10.1016/j.est.2025.106821.

[7] Kou et al., "Building-integrated heat pipes and phase change materials for solar thermal optimization," Build. Environ., vol. 248, p. 111039, 2025, doi: 10.1016/j.buildenv.2025.111039.

[8] Y. Yan et al., "Machine learning for melting time prediction in triplex-tube latent heat storage," Appl. Energy, vol. 376, p. 123455, 2025, doi: 10.1016/j.apenergy.2025.123455.

---

**Document Status:** Ready for implementation  
**Approval Required From:** Dr. T. Deepika (Guide), Dr. Amrita CSE Academic Coordinator  
**Next Milestone:** Freeze system_config_shared.yaml (Week 1)

