# AI-driven design optimisation of PCM thermal storage for solar water heating
## Detailed plan using 2023–2026 literature and suitable simulators

**Objective (verbatim):** develop an AI-driven design optimisation model to
determine the optimal **PCM thickness, capsule arrangement, number of PCM
capsules and flow rate** for maximising thermal energy storage under
location-specific climatic conditions, using suitable simulators.

Date: 2026-10-16. Literature window: **2023–2026 only** (papers older than 2023 in
the project's `sources/` — Avargani 2021, Li 2020, Eldokaishi 2022 — are
treated as background, not as evidence for this plan).

**Evidence tags**
* **[P]** read in the project's own sources (summary and/or extracted PDF text).
* **[C]** found via Consensus; abstract only. **[W]** found via web search; snippet only.
  → Do not quote numbers from [C]/[W] papers until the PDF is read (list in §9).
* **[OURS]** produced in this project (`openfoam_cfd/results/`).

---

## 1. What 2023–2026 papers have done

### 1.1 OpenFOAM + PCM (and OpenFOAM + hot-water/solar tanks)

| Paper | Year | What | Relevance |
|---|---|---|---|
| Fetsov & Lutsenko, *J. Energy Storage* 65:107294 — “A novel computational model and OpenFOAM solver for simulating thermal energy storages based on granular phase change materials: Advantages and applicability” [P][C][W] | 2023 | **OpenFOAM solver `porousHeatTransferFoam`** for packed-bed granular/encapsulated PCM; interpenetrating continua; minutes for 1-D, minutes–hours for 2-D; validated against experiments; works down to a tank-to-particle ratio of ~7–8 | The only 2023+ OpenFOAM packed-bed-PCM solver found. It is the bed-scale tool (our "tier 2") and a possible code-sharing contact |
| Fetsov & Kim, *AIP Conf. Proc.* 2504:030107 — “A novel OpenFOAM solver for modelling thermo- and fluid dynamic processes in porous media” [W] | 2023 | Companion paper: OpenFOAM solver for thermo-fluid processes in porous media | Method detail |
| Hummel et al. (OTH), abstract at the 2022 OpenFOAM Conference (ESI Group file “07_Abstract_OpenFOAM_2022_Hummel_OTH.pdf”; exact title not captured in the search snippet) [W] | 2022 | Unconstrained melting in macrocapsules; confirms `solidificationMeltingSource` is the enthalpy-porosity route in OpenFOAM | Confirms our model choice |
| Fick et al., *J. Energy Storage* — “Efficiency enhancement of complex thermal energy storages under multiple transient loads” [C] | 2026 | **OpenFOAM** CFD of a large stratified tank fed by solar collectors; thermocline thickness −22 % (summer) / −42 % (winter) with matched inlet temperature/height | OpenFOAM is used for solar-thermal storage tanks, not PCM capsules |
| Abdellatif et al., *J. Energy Storage* 121:116517 — “Modeling and performance analysis of phase change materials in advanced thermal energy storage systems: A comprehensive review” [P] | 2025 | Table 9 lists numerical studies of PCM hot-water tanks: almost all ANSYS Fluent/COMSOL; **one** 2-D OpenFOAM study (Fertahi et al., review ref. [335]; its title is not given in the table — look it up in the review's reference list) | Confirms OpenFOAM is rare in PCM-tank work |

**Finding:** in a targeted search (three web queries, three Consensus queries,
the project's 26 sources) I found **no 2023–2026 paper that combines OpenFOAM,
encapsulated PCM and a solar water heater with climate-dependent AI optimisation.**
This supports a novelty claim *with the caveat that the search was not
exhaustive* (conference papers and theses may exist).

### 1.2 PCM capsules in hot-water / solar water-heater tanks (any solver)

| Paper | Year | What |
|---|---|---|
| Turski, *Energies* — “PCM-Filled Capsules (RT44HC) for Heat Storage—Laboratory Scale Pilot Study” [C] | 2025 | **RT44HC capsules**, 40 % of tank volume, lab pilot; heat accumulation 3.85× faster at start, more heat stored |
| Bianqui et al., Int. Conf. on Energy Harvesting, Storage, and Transfer — “Study of the Performance of a Hybrid Thermal Energy Storage System with Cylindrical PCM Encapsulations under Real Solar Conditions” [C] | 2025 | Hybrid tank, 85 cylindrical encapsulations in 5 cascaded levels, three Rubitherm paraffins with **measured** properties, EN 50440 test, Cartagena summer day; cascade improves stratification |
| Patel et al., *Energy Storage* — “Enhancing Solar Water Heater Performance Using Phase Change Materials and Modified Encapsulation Geometry” [C] | 2024 | India: RT60 spherical capsules in SWH tank; temperature drop 4.5 → 1.4 °C; +5.13 % stored energy; rectangular capsules 0.9 °C |
| Faisal et al., *Energies* — “Numerical Investigation of Solar Collector Performance with Encapsulated PCM: A Transient, 3D Approach” [C] | 2024 | 3-D transient solar collector with encapsulated paraffin vs RT60, seasons, inlet velocity/temperature |
| Kolsi et al., *Mathematics* — “Numerical Study of a Phase Change Material Energy Storage Tank Working with Carbon Nanotube–Water Nanofluid under Ha’il City Climatic Conditions” [C] | 2023 | Encapsulated paraffin tank with CNT nanofluid under Ha'il climate (real weather, 3 months) |
| Ramesh et al., *Mech. Based Des. Struct. Mach.* — “Advancing solar thermal energy efficiency with role of phase change materials in heat pipe evacuated tube collectors for superior storage” [C] | 2025 | Metaheuristic optimisation of **HTF flow rate, PCM melting point, glass-tube diameter** in a heat-pipe evacuated-tube collector; TIPNN forecast |
| Tank-stratification set [C] (6 papers, titles listed in §10) | 2024–26 | Validated CFD of hot-water tanks (mostly Fluent/COMSOL) |
| Krol et al., *Energies* — “Thermal Stratification in Solar Storage Tanks: Long-Term Modelling and Efficiency Analysis” [C] | 2026 | Multi-node tank, Kraków annual: **degree of stratification has a small effect on solar fraction**; stabilising outlet temperature matters more than volume |

The Krol result matters: it argues that a **single-node tank assumption costs less
than I assumed in the earlier plan**; stratification should be treated as a
check, not a main lever.

### 1.3 Spherical-capsule melting — physics, correlations, model reliability

| Paper | Year | Finding |
|---|---|---|
| Jia et al., *J. Energy Storage* — “Numerical and three-factor design investigation for melting process of phase-change spherical capsules in a solar thermal energy storage system” [C] | 2024 | **3-D sphere vs 2-D circular vs 2-D axisymmetric**: 2-D circular over-predicts melt time by 23–36 %; axisymmetric simplification error **grows with radius**; three-factor design (R, A_mush, ΔT): importance R > A_mush > R×A_mush > ΔT; **correlation for complete-melt time** |
| Li (M.-J.) et al., *Int. J. Green Energy* — “An effective thermal conductivity correlation for three high-temperature chloride salts melting in a spherical thermal storage capsule” [C] | 2023 | 2-D axisymmetric sphere: **λ_eff/λ_l = 0.38 Ra^0.26 (δ/R_i)^0.25** — the form needed to replace the grey-box's fixed ×2 |
| Yusuf et al., *J. King Saud Univ. – Eng. Sci.* — “Determining the phase change characteristics of lauric acid to realise its optimum performance in latent thermal energy storage” [C] | 2025 | **Lauric acid** (our regime-2 PCM), Fluent, shells 5–75 mm, Ste 0.22–0.47; convection intensifies up to ~30 mm, specific melting time constant above ~30 mm |
| Chen et al., *J. Fluid Mech.* — “Constrained melting of spherically encapsulated phase-change materials with natural convection: regime transition and predictive correlations” [C] | 2026 | Lattice-Boltzmann sphere melting; **Ra_c ≈ 1.9×10⁴** separates conduction- from convection-dominated regimes; two liquid-fraction correlations |
| Rocha et al., *Therm. Sci. Eng. Prog.* — “The role of the phase-change material properties, porosity constant, and their combination for melting problems using the enthalpy-porosity scheme” [C] | 2023 | Validated on two experimental datasets; carrying A_mush to another geometry gave up to **38 %** error (5.7 % re-tuned); **β matters more than ρ** (7.5 % vs 0.5 % in liquid fraction) |
| Rosa et al., *Inventions* — “Validation of a Simplified Numerical Model for Predicting Solid–Liquid Phase Change with Natural Convection in Ansys CFX” [C] | 2023 | A simplified source-term model (CFX) reproduced a PCM experiment with RMSE 2.6 %/3.7 % |
| Li (J.) et al., *Appl. Therm. Eng.* — “Analysis of heat transfer and fluid flow during the melting process of PCM within tubular thermal energy storage unit” [C] | 2024 | Numerical + experimental horizontal-cylinder paraffin: correlations in Fo·Ste·Gr; natural convection negligible for Ste < 0.093 |

### 1.4 AI / surrogate optimisation around CFD (2023–2026)

| Paper | Year | Method | Take-away |
|---|---|---|---|
| Anagnostopoulos et al., *Energy* — “An integrated machine learning and metaheuristic approach for advanced packed bed latent heat storage system design and optimization” [C] | 2024 | DL surrogate trained on validated CFD (R² 0.975, MAPE < 9.1 %) + metaheuristics (Harmony Search best); up to +85 % efficiency vs optimised experimental designs | Direct template: CFD → DL → metaheuristic for packed-bed latent storage |
| Xenitopoulos et al., *Int. J. Heat Mass Transf.* — “Insights into advanced packed bed latent heat storage systems through explainable artificial intelligence techniques” [C] | 2025 | LightGBM/XGBoost/RF on CFD data (R² 0.966/0.92) + **SHAP/LIME**; inlet flow rate and tank geometry most influential; −63 % computing effort | XAI on the CFD surrogate |
| Zheng et al., *J. Energy Storage* — “Performance optimization of latent heat storage device based on surrogate-assisted multi-objective evolutionary algorithm and CFD method” [C] | 2024 | **Surrogate-assisted multi-objective EA**: GP models from **80 CFD cases**, batch recommendation, −91 % cost | Sequential design with uncertainty |
| Han et al., *J. Energy Storage* — “Physics-informed neural networks for multi-objective design optimization of latent heat thermal energy storage systems” [C] | 2026 | **PINN on a 0-D lumped-capacitance model, 15 CFD cases, R² > 0.999**, then NSGA-II | Same structure as our grey-box + CFD correction |
| Zhang (J.) et al., *Appl. Therm. Eng.* — “Optimization of capsule diameters in cascade packed-bed thermal energy storage tank with radial porosity oscillations based on genetic algorithm” [C] | 2023 | GA over 4 000+ **capsule-diameter arrangements**, 3 layers, 15–40 mm; −33.9 % charging time, +37 % TES rate density, but **+92 % cost per unit heat** | Diameter below our 40 mm floor, and a cost trade-off |
| Singh (D.) et al., *Appl. Energy* — “Computationally effective machine learning approach for modular thermal energy storage design” [C] | 2024 | CFD → ML (NN best) → modular design; −99 % compute | Surrogate-to-system design workflow |
| Anand et al., *J. Energy Storage* — “Design analysis and performance prediction of packed bed latent heat storage system employing machine learning models” [C] | 2023 | XGBoost best (R² 0.982) on literature PBTES data | Data-driven benchmark |
| Isania et al., *Energies* — “Machine Learning for Design Optimization and PCM-Based Storage in Plate Heat Exchangers: A Review” [C] | 2025 | Review of ML + PCM + plate HX; calls for hybrid ML-physics, XAI, benchmarking | Positioning |
| Hiris et al., *Energy* — “Cross-validation of numerical methods for investigating the heating process in large-volume thermal storage tanks” [C] | 2025 | **Cross-validation of CFD vs finite-difference vs nodal models** on one hot-water tank; method-selection guidance by cost/accuracy | Validates a multi-fidelity ladder |
| Untrau et al., *Appl. Energy* — “A fast and accurate 1-dimensional model for dynamic simulation and optimization of a stratified thermal energy storage” [C] | 2023 | 1-D tank model by orthogonal collocation, built for optimisation | Fast tank model option |

### 1.5 What the project's own 2023–2026 sources add [P]
* **Assareh et al. 2023**, *J. Energy Storage* 73:108990 — “Enhancing Solar Thermal Collector Systems for Hot Water Production Through Machine Learning-Driven Multi-Objective Optimization with Phase Change Material (PCM)” (MATLAB MOEA/D + RSM + TOPSIS/LINMAP/AHP; Pareto of discharge time vs stored energy; 1-D flow).
* **Barqawi 2025**, *Muthanna J. Eng. Technol.* 13(3):1–14 — “Dynamic Simulation of Phase Change Material-Integrated Solar Water Heating Systems: A Machine Learning Approach to Energy Conversion Optimization” (Python `solve_ivp`, ANN flow multiplier, +2.5–4.1 % storage, −12–18 % pump energy, simulation-only).
* **Chen et al. 2025**, *Energy Convers. Manag.: X* 26:100910 — “Using the Taguchi Method and Grey Relational Analysis to Optimize the Parameter Design of Flat-Plate Collectors with Nanofluids and Phase Change Materials in an Integrated Solar Water Heating System” (TRNSYS L36 + GRA; flow 0.02 kg/s; PCM material only 2.6 % of heat-retention variance).
* **Yan et al. 2025**, *Appl. Energy* 390:125863 — “The Potential of Machine Learning to Predict Melting Response Time of Phase Change Materials in Triplex-Tube Latent Thermal Energy Storage Systems” (60 CFD cases, XGBoost 92 %, SVR overfits).
* **Kou et al. 2025**, *Build. Environ.* 285:113674 — “A Novel Solar Heating Building Integrated Heat Pipes and PCMs: Optimizing Thermophysical Properties and Reducing Energy Consumption” (PSO over ρH, Tm, λ for 61 cities; savings ratio linear in a climate index, R² > 0.98).
* Reviews: **Liu et al. 2025**, *Renew. Energy* 238:121973 — “The Contribution of Artificial Intelligence to Phase Change Materials in Thermal Energy Storage: From Prediction to Optimization”; **Abdellatif et al. 2025** (title in §1.1); **Singh et al. 2025**, *Sol. Energy Mater. Sol. Cells* 293:113888 — “Application of Phase Change Materials in Solar Water Heating Systems — A Comprehensive Review”; **Hamzat et al. 2025**, *J. Energy Storage* 114:115762 — “Phase Change Materials in Solar Energy Storage: Recent Progress, Environmental Impact, Challenges, and Perspectives”. Common message: ML for PCM-TES is "embryonic"; CFD-coupled optimisation is expensive; field validation rare; mushy-zone ML is open.
* **Martínez et al. 2025**, *Heliyon* 11:e41025 — “Phase Change Materials for Thermal Energy Storage in Industrial Applications” (datasheet vs measured: RT 55 ΔH −28 %, k +34 %; RT 64 HC ΔH −31 %).

---

## 2. Suitable simulators — decision

| Tier | Tool | Resolves | Cost / run | Use in this project |
|---|---|---|---|---|
| T0 | **Python grey-box** (`src/simulation`, existing) | Annual single-node tank, lumped capsules | ~7 s | All annual / climate-dependent evaluation; the optimisation objective |
| T1 | **1-D packed-bed (Schumann / LTNE) model** in Python, capsule closure from T2 | Axial stratification, flow direction, N, arrangement via void fraction and Nu | seconds–minutes | **New.** Bridges T0 and T2; Fetsov & Lutsenko 2023, Hiris et al. 2025 and Sponagle et al. 2025 (§10) [C] support this step |
| T2 | **OpenFOAM v2406 single-capsule** (`buoyantPimpleFoam` + `solidificationMeltingSource`, built) | Natural convection and melting inside one capsule | 1–40 min | High-fidelity truth for the capsule closure; DOE already run (48 cases) [OURS] |
| T2b | OpenFOAM **porous-media bed** (Fetsov-type LTNE solver) | Bed-scale 1-D/2-D with phase change | minutes–hours | **Built and smoke-tested 2026-10-16** (public repo, OpenFOAM v2406); see `docs/PHT_SOLVER_NOTES.md` |
| T3 | OpenFOAM unit-cell (2-D periodic cylinders) | Nu and ΔP per arrangement | hours (mesh) | Closes the arrangement question with data; expected effect small |
| – | TRNSYS / SAM | plain-tank baseline | – | SAM only as an independent plain-tank check (no PCM) |
| – | Fluent/COMSOL | – | licence | Not used; not required |

Recommendation: **T0 + T1 + T2** as the working chain; T2b and T3 only if time
allows. This keeps all tooling free (Python + OpenFOAM) and runnable on the
student laptop (16 threads, 7 GB RAM in WSL).

---

## 3. Architecture

```
                 O1 output (per regime): climate features, PCM shortlist, Tm target
                                      │
              ┌───────────────────────┴────────────────────────┐
              │  DESIGN VECTOR  x = (d, N, ṁ, arrangement, PCM)  │
              └───────────────────────┬────────────────────────┘
                                      │ constraints: src/design/constraints.py
        ┌─────────────────────────────┼───────────────────────────────┐
        │                             │                               │
   T2 OpenFOAM capsule          T1 1-D bed model               T0 grey-box annual
   (d, h_w, ΔT, PCM)            (x, hourly weather)            (x, climate regime)
        │ melt-fraction curves,        ▲ closure φ(Fo·Ste,Ra,Bi)       ▲ closure + bed
        └── closure fit ───────────────┴───────────────────────────────┘
                                      │
                        multi-fidelity surrogate (GP / ET / PINN residual)
                                      │ sequential acquisition (uncertainty)
                        NSGA-II + TOPSIS  →  Pareto set per climate regime
                                      │
                        confirm top-k in T0 (and T2 for the winner)
                                      │
                        recommendation cards → O3 environment contract
```

---

## 4. Variables, bounds and where each is resolved

| Variable | Bound used now | Where resolved | Issue to settle |
|---|---|---|---|
| PCM thickness (= d/2) | d ∈ [40, 80] mm (frozen; derived from `pcm_thickness_m ≥ 0.02`) | T2 directly | Zhang 2023 [C] reports optima at **15–40 mm**; Yusuf 2025 [C] shows convection saturates ≈ 30 mm. Check the origin of the 20 mm thickness floor before keeping it |
| Capsule count N | 8–37 | T0/T1 (mass loading, UA) | Interacts with PCM fraction ≤ 20 % |
| Arrangement | single-layer, staggered, radial | T0 (void fraction, ΔP) · T1 (Nu_arr, porosity) · T3 (optional) | Effect predicted < 0.02 % [project G0] — confirm or refute |
| Flow rate ṁ | 0.010–0.050 kg/s | T2 via `h_w`; T1/T0 via Re and pump power | Chen 2025 [P] optimum 0.02 kg/s |
| PCM | O1 Top-3 | T2 (props) | Use measured ΔH, k when available (Martinez 2025 [P]) |
| Climate | 3 Rajasthan regimes (+ 3 other states) | T0 hourly weather | – |

---

## 5. AI method stack (what to implement, in order)

1. **Sampling** — Sobol (not LHS) for new points; keep the existing LHS for paired comparison.
2. **Closure model** `φ(d, ṁ, ΔT, props)` or, better, a **dimensionless correlation**
   `Nu_eff, f_melt = F(Fo·Ste, Ra, Bi)` fitted on the T2 data; compare its form with
   Li 2023 `λ_eff/λ_l = 0.38 Ra^0.26 (δ/R)^0.25` and Jia 2024.
3. **Physics-informed residual surrogate** (Han 2026 pattern): predict the *correction*
   to the grey-box's output from T2/T1, not the whole response.
4. **Surrogate for the objective**: ExtraTrees (kept for continuity with Phase 6) **and**
   a GP for predictive variance; compare on held-out designs.
5. **Sequential / active learning** (Zheng 2024 pattern): batch acquisition on GP
   uncertainty × expected improvement; stop at a declared budget (e.g. 80 CFD cases).
6. **Multi-fidelity**: choose T0 vs T1 vs T2 by information per cost.
7. **Multi-objective selection**: NSGA-II over {useful energy, delivery-temperature
   stability, pump energy, PCM mass/cost}, then TOPSIS/LINMAP; keep the frozen
   "5 % tolerance" rule only for the headline comparison.
8. **XAI**: permutation importance + SHAP on the final surrogate (Xenitopoulos 2025).
9. **Uncertainty propagation**: sample μ, β, k, ΔH, mains temperature, GHI noise;
   report P(constraint met) per Pareto design (extends Phase 8 to the CFD tier).

**Objectives that discriminate** (annual useful energy differs < 0.5 % between designs):
tank-volume reduction at equal solar fraction; hours within ±2 K of target
(delivery stability); backup/unmet energy; latent-utilisation fraction; pump energy.

---

## 6. Code plan

Existing (built and run) → **keep**: `config/o2_cfd_config.yaml`,
`scripts/make_case.py`, `run_one.sh`, `run_doe.py`, `postprocess.py`,
`cfd_calibrated_greybox.py`, `validate_sphere.py`.

New modules (all under `openfoam_cfd/`, none touch frozen `src/` or configs):

```
openfoam_cfd/
├─ closure/
│   ├─ fit_correlation.py        # F(Fo·Ste, Ra, Bi) from results/cfd_doe_results*.csv
│   └─ closure_api.py            # ua_eff(...) drop-in variants: "frozen" | "phi" | "corr"
├─ bed1d/
│   ├─ bed_model.py              # 1-D two-temperature packed-bed (Schumann/LTNE)
│   └─ test_bed_model.py         # energy balance, limiting cases, vs T0 single node
├─ opt/
│   ├─ design_space.py           # bounds, constraints (wraps src.design.constraints)
│   ├─ objectives.py             # KPIs: ΔV_tank@SF, hours±2K, unmet, pump, mass
│   ├─ fidelity_chain.py         # evaluate(x, level) -> dict ; level in {T0,T1,T2}
│   ├─ sequential_design.py      # GP + batch acquisition, budget, resume
│   ├─ pareto.py                 # NSGA-II + TOPSIS/LINMAP
│   └─ uq.py                     # property/weather sampling, P(constraint)
├─ reports/
│   └─ make_cards.py             # recommendation cards, SHAP plots, tables
└─ tests/                        # pytest: reproducibility, QC gates, paired harness
```

Key interfaces:

```python
# opt/fidelity_chain.py
from dataclasses import dataclass
from typing import Literal, Mapping

Level = Literal["T0_greybox", "T1_bed1d", "T2_openfoam"]

@dataclass(frozen=True)
class Design:
    d_m: float            # capsule diameter (PCM thickness = d/2)
    n: int                # number of capsules
    mdot_kg_s: float      # flow rate
    arrangement: str      # single-layer | staggered | radial
    pcm: str              # O1 shortlist member

def evaluate(x: Design, regime: int, level: Level, *,
             closure: str = "corr", seed: int = 0) -> Mapping[str, float]:
    """Return KPIs: useful_energy_kWh, solar_fraction, hours_within_2K,
    unmet_kWh, pump_kWh, pcm_mass_kg, latent_utilisation, max_pcm_C, valid."""
```

```python
# opt/sequential_design.py
def run(regime: int, budget: dict[Level, int], seed: int) -> "Archive":
    """Sobol init -> fit GP (per KPI) -> batch acquisition (EI x P(feasible))
    -> evaluate at the cheapest level whose predicted information gain/cost is
    highest -> refit -> stop at budget; archive is resumable (kpi.json per run)."""
```

```python
# closure/closure_api.py
def ua_eff_total_w_k(n, d, area, u_sup, props, f_melt, cfg, *, variant="corr") -> float:
    """variant 'frozen' reproduces src/simulation/heat_transfer.py exactly (checked
    to 1e-10 kWh); 'phi' = CFD-calibrated scale; 'corr' = F(Fo·Ste, Ra, Bi)."""
```

Reproducibility rules (inherited from the project): every results file gets a
manifest sidecar (config hashes, seed, mesh size, solver version); no table in the
paper without a saved file; paired frozen-vs-new runs for every closure change.

---

## 7. Work plan with gates

| Phase | Work | Output | Gate (decide before running) |
|---|---|---|---|
| A (1 wk) | Mesh 0.8 mm DOE [running]; μ, β from datasheets; validation against a **2023+ experimental dataset** (§9: Turski 2025, Rocha 2023 data, Li 2024) | validated T2 | t50/t90 error ≤ 15 % on a held-out case; else retune A_mush on one geometry and test on another |
| B (1 wk) | `closure/`: fit F(Fo·Ste, Ra, Bi); compare with Li 2023, Jia 2024, Chen 2026 | closure variants + test | correlation reduces t90 error vs constant φ by ≥ 30 % |
| C (1–2 wk) | `bed1d/` model + tests; compare with T0 on Phase-5 designs | stratification effect quantified | If ranking shifts by > noise band, report as a model-form finding (Krol 2026 predicts small) |
| D (1 wk) | Objectives that discriminate; reconcile 17 % loading result with the loading sweep | new KPI set | Iso-performance volume reduction differs between designs by > noise |
| E (1–2 wk) | `opt/`: Sobol → GP → batch acquisition → NSGA-II/TOPSIS; SHAP; UQ | Pareto sets per regime | Pareto designs re-confirmed in T0/T2 within 3 % |
| F (1 wk) | Extend diameter bound below 40 mm (15–40 mm) if justified; cascade (2 layers) as optional design variable | extended space | Only keep if an iso-performance KPI improves > noise |
| G | Experiment design for O4 (single-capsule melting bath; Turski 2025 tank protocol) | protocol | – |

Fast path if time is short: **A → B → D → E**.

---

## 8. Claims to avoid / state carefully
* "CFD-validated" — not until Phase A passes on external data.
* Absolute melt times — the 1.2 mm mesh under-predicts t90 by ~9 % [OURS]; the fine-mesh DOE is running.
* "Optimal diameter / count / flow" — designs differ by < 0.5 % annual energy; report Pareto sets and iso-performance metrics.
* Arrangement conclusions from CFD — not resolved by the capsule model.
* Any number from a [C]/[W] paper before its PDF is read.
* Axisymmetry: Jia 2024 [C] reports a growing 2-D-axisymmetric vs 3-D discrepancy with radius — state it and, if possible, quantify with one 3-D wedge-less case.

---

## 9. PDFs I need you to supply (2023–2026 only), in priority order

| # | Paper | Why |
|---|---|---|
| 1 | Fetsov & Lutsenko, "A novel computational model and OpenFOAM solver for simulating thermal energy storages based on granular phase change materials…", *J. Energy Storage* 65 (2023) 107294 | OpenFOAM packed-bed PCM solver and its validation data |
| 2 | Jia et al., "Numerical and three-factor design investigation for melting process of phase-change spherical capsules in a solar thermal energy storage system", *J. Energy Storage* (2024) | 3-D vs axisymmetric bias; A_mush selection; melt-time correlation |
| 3 | Rocha et al., "The role of the phase-change material properties, porosity constant, and their combination for melting problems using the enthalpy-porosity scheme", *Therm. Sci. Eng. Prog.* (2023) | Experimental datasets + A_mush protocol |
| 4 | Turski, "PCM-Filled Capsules (RT44HC) for Heat Storage—Laboratory Scale Pilot Study", *Energies* (2025) | Experimental capsule data for RT44HC (our regime-0 PCM) — validation candidate; open access |
| 5 | Li, M.-J. et al., "An effective thermal conductivity correlation for three high-temperature chloride salts melting in a spherical thermal storage capsule", *Int. J. Green Energy* (2023) | λ_eff correlation form for spheres |
| 6 | Yusuf et al., "Determining the phase change characteristics of lauric acid…", *J. King Saud Univ. Eng. Sci.* (2025) | Lauric-acid spheres 5–75 mm, Ste 0.22–0.47 |
| 7 | Chen et al., "Constrained melting of spherically encapsulated phase-change materials with natural convection…", *J. Fluid Mech.* (2026) | Regime criterion and correlations |
| 8 | Anagnostopoulos et al. (2024), *Energy* — “An integrated machine learning and metaheuristic approach for advanced packed bed latent heat storage system design and optimization”; Xenitopoulos et al. (2025), *Int. J. Heat Mass Transf.* — “Insights into advanced packed bed latent heat storage systems through explainable artificial intelligence techniques” | CFD → DL → metaheuristic and XAI workflow for packed beds |
| 9 | Zheng et al. (2024), *J. Energy Storage* — “Performance optimization of latent heat storage device based on surrogate-assisted multi-objective evolutionary algorithm and CFD method”; Han et al. (2026), *J. Energy Storage* — “Physics-informed neural networks for multi-objective design optimization of latent heat thermal energy storage systems” | GP batch acquisition; PINN on 0-D model |
| 10 | Zhang et al. (2023), *Appl. Therm. Eng.* — “Optimization of capsule diameters in cascade packed-bed thermal energy storage tank with radial porosity oscillations based on genetic algorithm” | Diameters 15–40 mm; cost trade-off |
| 11 | Fick et al. (2026), *J. Energy Storage* — “Efficiency enhancement of complex thermal energy storages under multiple transient loads”; Hiris et al. (2025), *Energy* — “Cross-validation of numerical methods for investigating the heating process in large-volume thermal storage tanks”; Untrau et al. (2023), *Appl. Energy* — “A fast and accurate 1-dimensional model for dynamic simulation and optimization of a stratified thermal energy storage” | OpenFOAM tank; CFD/FDM/nodal cross-validation; 1-D tank model |
| 12 | Bianqui et al. (2025) — “Study of the Performance of a Hybrid Thermal Energy Storage System with Cylindrical PCM Encapsulations under Real Solar Conditions”; Patel et al. (2024), *Energy Storage* — “Enhancing Solar Water Heater Performance Using Phase Change Materials and Modified Encapsulation Geometry”; Ramesh et al. (2025) — “Advancing solar thermal energy efficiency with role of phase change materials in heat pipe evacuated tube collectors for superior storage” | Experimental cascaded tank; Indian SWH capsule study; ML-optimised collector |
| 13 | Isania et al. (2025), *Energies* — “Machine Learning for Design Optimization and PCM-Based Storage in Plate Heat Exchangers: A Review” | Positioning |

For **#4** and any other open-access item (Energies, MDPI), the PDFs can simply
be downloaded; the rest may need institutional access. Put them in
`.claude/Sources/pdfs/` and I will extract each to `sources/<Name>_summary.md`
(CLAUDE.md §5) before using any number.

---

## 10. Full titles for papers cited only by author in the tables

**Tank-stratification set (§1.2)** — all [C], abstract only
* Izgi et al. (2026), *Thermal Science and Engineering Progress* — “A numerical investigation of the influence of an obstacle inside the vertical mantled hot water storage tank on the thermal stratification under discharging operation condition for domestic solar energy applications”
* Idrissi et al. (2025), *International Journal of Thermofluids* — “Effect of Plate Configurations on Thermal Stratification and Energy Efficiency in Solar Hot Water Storage Tanks: A CFD-Based Analysis”
* Li et al. (2024), *Applied Thermal Engineering* — “Thermal performance of a solar water tank with variable inlet/outlet under various charging strategies”
* Abdidin et al. (2024), *Energies* — “Three-Dimensional CFD Analysis of a Hot Water Storage Tank with Various Inlet/Outlet Configurations”
* Van Schalkwyk et al. (2024), *Applied Thermal Engineering* — “Numerical modelling of thermal stratification scenarios in horizontal electric hot water storage tanks”
* Wang et al. (2024), *Journal of Energy Storage* — “CFD analysis and optimization of thermal stratification in a Thermal Diode Tank (TDT)”

**Other papers named in the text**
* Sponagle et al. (2025), *Int. J. Heat Mass Transf.* — “Experimental validation of a novel modelling technique for packed bed thermal storage systems containing non-spherical phase change material capsules” [C]
* Fertahi et al. — 2-D OpenFOAM study of cylindrical vs elliptical PCM capsules in a vertical water tank; cited as ref. [335] in Abdellatif et al. 2025 (title not in the extracted table; check that reference list) [P]

**Pre-2023 background papers mentioned (not used as evidence)**
* Madadi Avargani et al. (2021), *Sustainable Energy Technologies and Assessments* 47:101350 — “Integrating paraffin phase change material in the storage tank of a solar water heater to maintain a consistent hot water output temperature” [PDF read]
* Li et al. (2020), *Journal of Energy Storage* 29:101371 — “A multi-objective optimal design method for thermal energy storage systems with PCM: A case study for outdoor swimming pool heating application” [PDF read]
* Eldokaishi et al. (2022), *Applied Thermal Engineering* 204:118009 — “Modeling of Water-PCM Solar Thermal Storage System for Domestic Hot Water Application Using Artificial Neural Networks” [P]
* Nallusamy, Sampath, Velraj (2007), *Renewable Energy* 32(7):1206–1227 — “Experimental investigation on a combined sensible and latent heat storage system integrated with constant/varying (solar) heat sources” (the experiment reproduced in Fetsov & Lutsenko §4.3)

---

## 11. Progress against this plan (updated 2026-10-17)

| Plan item | State |
|---|---|
| §2 tier T2 capsule CFD | done: 48-case DOE at 1.2 mm and 0.8 mm, 48 conduction twins, mesh, Courant and property-sensitivity studies (`CFD_FINDINGS.md`) |
| §2 tier T2b packed-bed OpenFOAM | done: solver built on v2406, paper §4.3 case reproduced (by eye against its Fig. 7), Rajasthan 1-D bed, driven by hourly grey-box temperatures (`PHT_SOLVER_NOTES.md`) |
| §2 tier T1 (own 1-D bed in Python) | **replaced** by the OpenFOAM bed solver; no separate Python model written |
| §5 steps 2–4 closure model, physics-informed residual, surrogate | partial: constant φ(d, ṁ, ΔT, props) with ExtraTrees; the dimensionless correlation F(Fo·Ste, Ra, Bi) is **not** fitted |
| §5 steps 5–9 sequential GP design, multi-fidelity, NSGA-II/TOPSIS, SHAP, UQ | **not done** |
| §7 phase A validation vs a 2023+ experiment | harness ready (`validate_sphere.py`), **no experiment compared**; Fetsov 2023 extracted; the other papers in §9 not yet supplied; mesh part done (0.8 mm) |
| §7 phase C bed vs single node | done; stratification effect small for the Phase-7 designs |
| §4 variable bounds (d < 40 mm, cascades) | not explored |
| Components beyond the plan (tank, collector) | done for water-only tank and collector strip (`COMPONENT_CFD_NOTES.md`) |
| §8 claims to avoid | still in force: nothing is validated against measurements |

Fetsov & Lutsenko 2023 was supplied and extracted to `.claude/Sources/Fetsov2023_OpenFOAM_GranularPCM_summary.md`;
papers #2–#13 of §9 are still outstanding.
