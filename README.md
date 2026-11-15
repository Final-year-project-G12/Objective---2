# AI-Driven PCM Design Optimization

An AI-assisted framework for optimizing the **physical and operating design of Phase Change Material (PCM) thermal-storage systems** under different climate regimes.

This repository implements **Objective 2** of the project:

> **Design an AI-driven optimization framework that determines the optimal PCM configuration, capsule geometry, arrangement, PCM mass, and water-flow rate for each climate regime identified by Objective 1.**

The framework combines a physics-based grey-box thermal simulator, design-of-experiments, AI surrogate modelling, constrained multi-objective optimization, active learning, and uncertainty analysis.

---

## State folders and headline results

Each state has its own folder with its own `config.py`, pipeline, `docs/` and `results/`. Do not mix numbers across states. Gains are paired differences against a water-only tank in kWh/yr of energy delivered at or above the target between 18:00 and 09:00, on held-out years that were tested once.

| Folder | Status | Tank · collector | Held-out years | Held-out gain per regime (kWh/yr) | Start here |
|---|---|---|---|---|---|
| `objective2-rajasthan/` | Current method (v3, reference state) | 50 L · 1.5 m² | 2011–2015 | 137.5 / 145.7 / 149.3 | `README.md`, `docs/04_RESULTS.md` |
| `objective2-tamilnadu/` | Current method (ported from Rajasthan) | 100 L · 2.5 m² | 2011–2015 | 284.2 / 223.3 / 269.9 | `README.md`, `OVERVIEW.md`, `docs/04_RESULTS.md` |
| `objective2-uttarakhand/` | Current method (ported), K = 4, 50 °C target | 50 L · 1.5 m² | 2024–2025 | 76.0 / 61.8 / 56.4 / −6.1 (no PCM gain in regime 3) | `README.md`, `docs/04_RESULTS.md` |
| `objective2-assam/` | Being rebuilt on a 500 L, 5 m² chain; results pending | 500 L · 5 m² | not yet run | n/a | `README.md`, `docs/00_MASTER_OVERVIEW.md` |

Common findings: every chosen design sits at the edge of the searched box (capsule radius 39.5–40 mm, PCM fraction 28–30%), so each is the best inside the declared box, not a proven optimum; the highest PCM temperature in any held-out run is 64.2 °C against the 65 °C limit; a surrogate is used only to rank designs, and the simulator produces every reported number.

## CFD cross-checks (not validation)

- **OpenFOAM** (`openfoam_cfd/`, `objective2-rajasthan/rj_openfoam/`, `objective2-uttarakhand/openfoam_cfd/`): single-capsule melting. Neither Tan 2009 nor Dong 2022 is reproduced and the mesh is not grid-independent, so the CFD is an unvalidated upper bound.
- **ANSYS Fluent** (`objective2-tamilnadu/ansys/`): four PCMs in one capsule, a flow sweep, whole-tank and single-capsule discharge demos, regime contours, and a criteria study that runs 7 designs (optimal, maximum, minimum, 80 capsules, 30 capsules, 10%, 50%) through a 60-minute whole-tank discharge. Videos and figures are under `ansys/videos/` and `ansys/figures/`; see `ansys/CRITERIA_STUDY_README.md` and `ansys/HOW_TO_RUN_ANSYS.md`. Fluent never chooses a design.

## Where to read the results

The documentation portal shows all of this with figures and videos: [https://Final-year-project-G12.github.io/Documentation-Portal](https://Final-year-project-G12.github.io/Documentation-Portal).

---

## 1. Objective 2

Objective 1 determines **which PCM is suitable for a given climate regime**.

Objective 2 determines **how that PCM should be physically configured and operated** to achieve the best thermal-storage performance.

The main design variables include:

* PCM thickness
* Capsule shape
* Capsule dimensions
* Capsule arrangement
* Number of capsules
* Number of layers
* Capsule spacing
* PCM mass
* Water mass-flow rate

The optimization considers:

* Useful thermal energy delivered
* Solar fraction
* Delivery-temperature availability
* PCM melt-fraction utilization
* Charging and discharging time
* Unmet hot-water demand
* Heat loss
* Pumping energy
* PCM mass
* System cost
* Reliability and robustness

---

## 2. Relationship with Other Objectives

The project is divided into sequential objectives:

```text
Objective 1
Climate-regime identification
        +
PCM candidate selection
        │
        ▼
Objective 2
PCM physical design optimization
        │
        ▼
Objective 3
Real-time adaptive control using DRL
        │
        ▼
Objective 4
Embedded-system validation
```

Objective 2 consumes the **frozen climate regimes and Top-2/Top-3 PCM candidates from Objective 1** and produces a frozen optimized design for Objective 3.

---

## 3. Overall Pipeline

```text
Objective 1 Outputs
        │
        ▼
Climate + PCM Input Preparation
        │
        ▼
Design-Space Generator
        │
        ▼
Geometry & Constraint Validation
        │
        ▼
Grey-Box Enthalpy Thermal Simulator
        │
        ▼
Simulator Verification
        │
        ▼
Design-of-Experiments Dataset
        │
        ▼
AI Surrogate Model
        │
        ▼
Constrained Multi-Objective Optimization
        │
        ▼
Active-Learning Refinement
        │
        ▼
Physics-Based Simulator Re-evaluation
        │
        ▼
Uncertainty & Robustness Analysis
        │
        ▼
Final Deployable Design
        │
        ▼
Frozen Input to Objective 3
```

The physics-based simulator is the **ground-truth evaluator**. The AI model is used to accelerate design exploration and optimization rather than replacing physical verification.

---

## 4. Inputs

### 4.1 Climate Regime

Each climate regime generated by Objective 1 provides:

* Regime ID
* Population coverage
* Representative/medoid climate point
* Hourly weather data
* Seasonal statistics
* Ambient temperature
* GHI
* DNI/DHI where available
* Relative humidity
* Wind speed
* Elevation
* Day length
* Daily clearness index
* Cloudy-day fraction
* Consecutive-cloudy-day index
* Diurnal temperature range
* Representative mains-water temperature

The original hourly weather sequence is retained because the simulator requires time-varying forcing rather than only a climate label.

### 4.2 PCM Candidates

For every Top-2/Top-3 PCM candidate:

* PCM identifier
* PCM family
* Melting temperature / phase-change interval
* Latent heat
* Density
* Solid specific heat
* Liquid specific heat
* Thermal conductivity
* Supercooling
* Corrosion class
* Cycling stability
* Cost
* Property uncertainty

Missing material properties are explicitly represented as **unreported** rather than being silently guessed.

### 4.3 Fixed System Parameters

The system configuration is frozen before optimization:

* Collector type and area
* Tank volume
* Insulation
* Heat-exchanger configuration
* Inlet-water temperature model
* Required delivery temperature
* Maximum tank temperature
* Pump characteristics
* Maximum pressure drop
* Safety limits
* Domestic hot-water demand profile

---

## 5. Design Space

The design vector is represented as:

```text
x = [
    t_pcm,
    capsule_shape,
    capsule_dimensions,
    arrangement,
    N_capsule,
    N_layer,
    spacing,
    m_dot,
    m_pcm
]
```

Continuous, integer, and categorical variables are handled separately.

### Continuous variables

* PCM thickness
* Capsule dimensions
* Capsule spacing
* Water-flow rate

### Integer variables

* Number of capsules
* Number of layers

### Categorical variables

* Capsule shape
* Capsule arrangement

The geometry module ensures that generated designs satisfy tank-volume, spacing, overlap, water-passage, and manufacturability constraints.

---

## 6. Physics-Based Thermal Simulator

The primary simulation environment is a transparent **Python grey-box lumped enthalpy tank model**.

The simulator tracks:

* Water temperature
* Collector inlet/outlet temperature
* PCM temperature
* PCM melt fraction
* Sensible + latent stored energy
* Hot-water load
* Thermal losses
* Pumping energy

PCM phase change is represented using an **enthalpy formulation** rather than an abrupt solid/liquid switch.

### Heat Transfer

The capsule heat-transfer model considers:

* Water-side convection
* Capsule-wall conduction
* PCM conduction
* Wetted surface area
* Capsule arrangement
* Flow rate
* Pressure drop

The flow rate therefore influences both thermal performance and hydraulic cost.

---

## 7. Weather and Demand Simulation

The initial simulator uses the available **hourly weather sequence**.

A complete year is simulated for each climate regime, followed by testing with unseen weather sequences or resampled conditions.

A cited domestic hot-water demand profile is used rather than an invented demand profile.

---

## 8. Simulator Verification

The AI dataset is generated only after the physics simulator passes verification.

### Verification stages

1. **Energy conservation**
2. **Limiting-case tests**
3. **Baseline comparison**
4. **Published benchmark calibration**
5. **Sensitivity analysis**

Important limiting cases include:

* Zero irradiance
* Zero flow
* No PCM
* Zero latent heat
* Very high conductivity
* Perfect insulation
* Empty demand
* Fully solid PCM
* Fully liquid PCM

The project specifies an approximate **±10% model-versus-experiment accuracy target** for published benchmark comparison.

---

## 9. Design-of-Experiments

The initial AI dataset is generated through deliberate exploration of the design space rather than starting directly with an optimizer.

A space-filling approach such as **Latin Hypercube Sampling (LHS)** is used for continuous variables, with balanced combinations for categorical and integer variables.

Boundary cases are explicitly included:

* Minimum/maximum PCM thickness
* Minimum/maximum flow rate
* Minimum/maximum capsule count
* All capsule arrangements
* Representative mixed designs

Every simulation case receives a unique design ID and stores its inputs, outputs, constraints, solver status, runtime, weather seed, demand seed, and simulator version.

---

## 10. AI Surrogate Model

The surrogate model learns the relationship:

```text
Climate
   +
PCM Properties
   +
System Parameters
   +
Design Variables
   +
Weather/Demand Features
        │
        ▼
   AI Surrogate
        │
        ▼
Predicted Thermal Performance
```

The surrogate predicts metrics such as:

* Annual useful energy
* Solar fraction
* Delivery-temperature hours
* Unmet energy
* Charging time
* Discharging time
* Mean melt fraction
* Pumping energy
* Heat loss
* Feasibility

A tree-based model such as **Extra Trees** or gradient-boosted trees is recommended as the initial surrogate because the problem contains nonlinear interactions, categorical variables, and integer variables.

---

## 11. Surrogate Evaluation

The surrogate is evaluated using:

* Mean Absolute Error (MAE)
* Root Mean Square Error (RMSE)
* Maximum Error

Performance is evaluated separately:

* Across all test designs
* Near the Pareto front
* Near feasibility boundaries

An ablation experiment also evaluates the effect of including the Objective 1 PCM confidence score.

---

## 12. Active Learning

The optimization uses an iterative active-learning loop:

```text
Train Surrogate
      │
      ▼
Optimize Surrogate
      │
      ▼
Select Promising / Uncertain Designs
      │
      ▼
Run Physics Simulator
      │
      ▼
Append Verified Results
      │
      ▼
Retrain Surrogate
      │
      └──────────────► Repeat
```

High-uncertainty designs and designs close to constraint boundaries are prioritized.

If the surrogate predicts a high-performing design that the physics simulator rejects, the rejected case is retained and used for retraining.

---

## 13. Multi-Objective Optimization

Objective 2 formulates the design problem as a **constrained multi-objective optimization problem**.

### Maximize

* Annual useful heat delivered
* Solar fraction
* Delivery-temperature availability
* Usable PCM melt fraction

### Minimize

* Unmet hot-water energy
* Charging time
* Discharging time
* Heat loss
* Pumping energy
* PCM mass
* System cost

### Constraints

* Capsule geometry
* PCM volume
* Tank volume
* PCM temperature safety
* Melting-temperature feasibility
* Collector charging capability
* Water-flow limits
* Pressure-drop limits
* Pump capacity
* Minimum delivery temperature
* Maximum tank temperature
* Material safety
* Reliability

A mixed-variable evolutionary optimizer such as **NSGA-II** may be used.

---

## 14. Pareto Optimization

The framework first generates a **Pareto-optimal set** rather than immediately selecting one design.

Example trade-offs:

```text
Useful Energy
      ▲
      │       ●
      │     ●
      │   ●
      │ ●
      └──────────────────► PCM Mass
```

Additional trade-offs include:

* Energy vs PCM mass
* Energy vs pumping energy
* Energy vs charging time
* Capsule count vs flow rate
* Energy vs melt-fraction utilization

The final deployable design is selected using a predefined decision rule rather than simply selecting the maximum-energy design.

---

## 15. Physics-Based Re-evaluation

The selected designs are **always re-run through the original physics simulator**.

The surrogate prediction is not accepted as the final result.

The final evaluation uses unseen weather and demand sequences and recalculates:

* Useful energy
* Solar fraction
* Delivery-temperature hours
* Unmet demand
* Charging time
* Discharging time
* Melt fraction
* Pumping energy
* Thermal losses

---

## 16. Uncertainty & Robustness

The optimized design is evaluated under uncertainty in:

* PCM latent heat
* Thermal conductivity
* Melting interval
* Irradiance
* Ambient temperature
* Hot-water demand
* Draw timing
* Inlet-water temperature
* Heat-transfer coefficient
* Insulation losses
* Flow rate

Robustness metrics include:

* Probability of meeting delivery temperature
* Probability of satisfying annual demand
* Useful-energy interval
* Pumping-energy interval
* PCM-mass interval
* Probability of violating temperature limits
* Probability of violating pressure limits

A slightly lower nominal-energy design may be preferred if it provides substantially higher feasibility probability.

---

## 17. Repository Structure

```text
Objective---2/
├── config.py, references.bib, openfoam_commands.md
├── data/                      shared inputs (Objective 1 outputs, PCM table)
├── openfoam_cfd/              shared OpenFOAM case files
├── obj2_revised/              earlier revised plan material
├── Objective2 Consolidated plan.md, O2_O3_COMPREHENSIVE_AUDIT_REPORT.md
├── objective2-rajasthan/      reference state
├── objective2-tamilnadu/      adds ansys/ (Fluent) and objective3/ hand-off
├── objective2-uttarakhand/    K = 4 regimes, adds openfoam_cfd/
└── objective2-assam/          500 L chain, results pending

each objective2-<state>/
├── config.py                  all constants for that state
├── pipeline.py / run_all_<state>.py   end-to-end runner (see its README for --stage options)
├── src/                       design space, geometry, simulator, surrogate, optimiser, validation
├── scripts/                   stage scripts and checks
├── tests/                     unit tests
├── data/, results/            inputs and generated outputs
├── docs/                      numbered write-up: model, weather, pipeline, results, limitations, Objective 3 hand-off
└── make_all_plots.py          regenerates the result figures
```

The end-to-end `--stage all` run has not been executed for every state; each state's `docs/05_LIMITATIONS_AND_OPEN_ITEMS.md` lists what is still open.

---

## 18. End-to-End Execution

The recommended execution sequence is:

```text
1. Freeze Objective 1 climate regimes
             ↓
2. Freeze Top-2/Top-3 PCM candidates
             ↓
3. Freeze system configuration
             ↓
4. Implement geometry generator
             ↓
5. Implement grey-box simulator
             ↓
6. Verify simulator
             ↓
7. Generate DOE dataset
             ↓
8. Train surrogate
             ↓
9. Validate surrogate
             ↓
10. Run constrained optimization
             ↓
11. Perform active-learning refinement
             ↓
12. Re-evaluate selected designs
             ↓
13. Perform uncertainty analysis
             ↓
14. Select final deployable design
             ↓
15. Generate optimized-design catalogue
             ↓
16. Pass frozen design to Objective 3
```

---

## 19. Expected Outputs

### Optimized Design Database

One record per climate regime and shortlisted PCM containing:

* Design variables
* PCM properties
* Performance metrics
* Constraint status
* Simulator confirmation
* Robustness metrics

### Design Recommendation Cards

Each card should contain:

* Climate regime
* Population coverage
* Selected PCM
* Competing PCM candidates
* PCM properties
* Capsule geometry
* Arrangement
* PCM thickness
* Capsule count
* Number of layers
* PCM mass
* Water-flow rate
* Useful energy
* Solar fraction
* Delivery-temperature hours
* Unmet demand
* Pumping energy
* Robustness probability

### Validation Outputs

The repository should generate:

* Simulator vs surrogate parity plots
* Pareto fronts
* PCM temperature histories
* Water temperature histories
* Melt-fraction histories
* Energy-balance plots
* Capsule-count/flow-rate trade-off plots
* Robustness distributions

---

## 20. Reproducibility

All experiments should preserve:

* Configuration files
* PCM database
* Climate-regime records
* Demand profiles
* DOE samples
* Simulator version
* Surrogate model
* Optimizer settings
* Random seeds
* Validation results

The complete pipeline should be reproducible from the saved configuration so that all reported results can be regenerated.

---

## 21. Objective 2 → Objective 3 Interface

The final output of Objective 2 is a **frozen physical design**.

Objective 2 determines:

> **Which PCM configuration and operating point should be built?**

Objective 3 determines:

> **What should the system do at each time step?**

The frozen interface passed to Objective 3 includes:

* Selected PCM
* Capsule geometry
* PCM mass
* Flow-rate limits
* Temperature limits
* Safety constraints
* Simulator interface
* Optimized system parameters

Objective 3 can then use these parameters for real-time charge, discharge, and bypass control.

---

## 22. Current Status

Updated 2026-11-15.

| Stage | Rajasthan | Tamil Nadu | Uttarakhand | Assam |
|---|---|---|---|---|
| Objective 1 inputs integrated | done | done | done (K = 4) | done (K = 3) |
| Grey-box simulator and verification gates | done | done | done | in rebuild |
| Taguchi screening, Sobol DOE, surrogate comparison | done | done | done | pending |
| NSGA-II with active learning, dense-grid check | done | done | done | pending |
| One-shot held-out test | done | done | done | pending |
| CFD cross-check | OpenFOAM (unvalidated upper bound) | ANSYS Fluent (consistency check) | OpenFOAM, 1 of 10 capsule cases run | pending |
| Objective 3 hand-off (contract v3) | written | written | written | not a valid input |

Open items shared by all states: designs sit at the search-box edge, sizing is below IS 12976:2023 for the 50 L states, monthly mains temperature, PCM volume change and supercooling are not modelled, and there are no hardware measurements.

---

## 23. Results

Headline numbers are in the state table near the top of this file. Full per-regime tables are in each state's `docs/04_RESULTS.md`, and the result figures (chosen designs, held-out PCM comparison, held-out gain by year, search front against dense grid, ablations, response to PCM fraction) are generated by each state's `make_all_plots.py`. The documentation portal shows them side by side: [https://Final-year-project-G12.github.io/Documentation-Portal](https://Final-year-project-G12.github.io/Documentation-Portal).

---

## 24. Key Design Principle

The central principle of this implementation is:

```text
AI proposes
     ↓
Physics verifies
     ↓
Optimization selects
     ↓
Uncertainty tests robustness
     ↓
Final design is frozen
```

The AI surrogate is therefore an **acceleration and search mechanism**, while the physics-based simulator remains the final authority for thermal performance and feasibility.

---

## 25. Citation / Project Reference

This repository implements the methodology specified in the **Objective 2: AI-Driven PCM Design Optimization Implementation Guide**.

Further experimental and material-property studies are required before assigning numerical bounds that are not explicitly supported by the project data.

## Project links

| Part | Repository |
|---|---|
| Objective 1: PCM selection | [https://github.com/Final-year-project-G12/PCM-Selection-ML-model](https://github.com/Final-year-project-G12/PCM-Selection-ML-model) |
| Objective 2: design optimisation | [https://github.com/Final-year-project-G12/Objective---2](https://github.com/Final-year-project-G12/Objective---2) |
| Objective 3: DRL controller | [https://github.com/Final-year-project-G12/solar-pcm-control--Objective3](https://github.com/Final-year-project-G12/solar-pcm-control--Objective3) |
| Objective 4: software-in-the-loop | [https://github.com/Final-year-project-G12/Objective--4_software-in-loop](https://github.com/Final-year-project-G12/Objective--4_software-in-loop) |
| Documentation portal | [https://github.com/Final-year-project-G12/Documentation-Portal](https://github.com/Final-year-project-G12/Documentation-Portal) · [live site](https://Final-year-project-G12.github.io/Documentation-Portal) |
| Objective 3 live dashboard | [Streamlit app](https://solar-pcm-control--objective3-ohrrdnt9lzp2fgngxmmjdb.streamlit.app/) |
