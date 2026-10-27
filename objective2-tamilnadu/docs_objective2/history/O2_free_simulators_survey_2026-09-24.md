# O2: Free, Student-Friendly Simulators (Survey, 24 Sep 2026)

**Objective 2:** Find the optimal PCM thickness, capsule arrangement, number of capsules and flow rate for a climate-specific SWH.
**Question:** Which free tools can generate the simulation data the O2 optimizer needs, and how do they fit the existing pipeline (Python grey-box simulator → LHS DoE → Extra Trees surrogate → re-check in the full simulator)?

---

## 1. What the project papers actually used (all 26 PDFs + O2 docs searched)

| Paper (project file) | Simulator | Free? | O2 variables covered |
|---|---|---|---|
| Eldokaishi 2022, *Modeling of water-PCM solar thermal storage system* | **Python script** running the Abdelsalam enthalpy model, then an ANN | Yes | PCM volume fraction, T_melt, tank volume (20 mm cylindrical modules) |
| Barqawi 2025, *Enhancing solar thermal collector systems…* (in the O1 master doc) | **Python SciPy `solve_ivp` (RK45)** with phase-event detection | Yes | PCM container volume and area, flow multiplier |
| Chen 2025, *Taguchi + GRA* | **TRNSYS** (36-run L36 array) | No (paid licence) | PCM volume 20 %, **14 PCM tubes**, **0.02 kg/s** |
| Madadi Avargani 2021, *Integrating paraffin PCM…* | **COMSOL Multiphysics** CFD, packed bed | No | 55 mm capsules, bed porosity 0.2–0.5, flow 0.005–0.15 kg/s |
| Li 2020, *Multi-objective optimal design… PCM* | **MATLAB** (finite difference) + TRNSYS 17 (Type 155), RSM + NSGA-II | No | PCM tank volume |
| Assareh 2023, *ML-driven MOO with PCM* | **MATLAB** + MOEA/D | No | tube diameter, contact area, flow rate |
| Yan 2025, *The potential of machine learning* | **ANSYS Fluent** (enthalpy-porosity) → XGBoost | Student version is free | fin width/angle (geometry → surrogate) |
| Abdellatif 2025 review, Table 9 | Fluent (most), **OpenFOAM** (Fertahi: cylindrical vs elliptical capsules in a tank), **Fortran** 1-D (Bouhal), COMSOL (Wu) | OpenFOAM and Fortran are free | capsule shape, L/D, stratification |

**Takeaway:** the free route the project already takes (a Python enthalpy model plus an ML surrogate) is the same method used in Eldokaishi 2022 and Barqawi 2025. Commercial CFD (Fluent or COMSOL) shows up only where the study resolves the **geometry and arrangement** of individual capsules.

## 2. Peer-reviewed support (Consensus)

- Capsule diameter and flow rate are the main levers in packed PCM beds. Smaller capsules charge and discharge faster [3][7][10]. Gao et al. rank the parameters as HTF inlet temperature > flow rate > capsule size [10]. All of these results come from **1-D non-equilibrium or concentric-dispersion models** that can be written in Python.
- Bouhal et al. simulated spherical PCM capsules in a solar DHW tank with **two self-written numerical codes** (apparent-Cp vs enthalpy method). The choice of method changed the predicted results [2]. This supports keeping one method frozen across all states.
- Majumdar et al. modelled bed height, porosity and capsule diameter in a hot-water tank using **simplified energy balances only, with no momentum equations** [8]. This is the same modelling class as our grey-box simulator.
- Nekoonam et al. used a GA on a 2-D concentric-dispersion model of cascaded PCM capsules [4]. He et al. found a 20–30 mm capsule mix gave the best performance [1].
- Surrogate benchmarks for solar DHW: symbolic regression and ANN surrogates reached MAPE of 0.8–2 %, versus about 1000 s for each full-year simulation [11]. This supports the surrogate step in O2.

## 3. Free simulators ranked for O2

| Rank | Tool | Cost / licence | Covers | Role in O2 | Effort |
|---|---|---|---|---|---|
| 1 | **Own Python grey-box model** (NumPy/SciPy) | Free | thickness, capsule count, volume fraction, flow rate, climate | **Primary simulator.** Already built and verified in 5 gates | Done |
| 2 | **OpenTerrace** (Python, Numba, `pip install openterrace`) | Free, GPL-3.0 | Packed bed with fluid and particle phases; sphere, cylinder, block or hollow-sphere particles; set the diameter and inflow | **Independent cross-check** of capsule diameter and flow-rate trends. PCM has to be added as a custom substance (enthalpy/Cp curve) | Medium |
| 3 | **OpenModelica + LBL Modelica Buildings library** | Free (BSD) | Stratified tank (`Buildings.Fluid.Storage`), collector, pump, controls; PCM conduction layers (`SolidsPCM`) | System-level cross-check, and a possible O3 environment through FMU export. There is no ready-made "PCM capsule in a tank" model: you would couple the tank node to a PCM layer | Medium–high |
| 4 | **Ansys Student** (Fluent) | Free, Windows, **1 M cell limit, 4 cores** | Full enthalpy-porosity CFD of a few capsules | **Capsule-arrangement calibration only.** Run about 3–6 2-D or small 3-D cases (staggered, inline, radial) to get an arrangement factor on h_pcm, then feed that factor into the grey-box model | Medium |
| 5 | **OpenFOAM** (`solidificationMelting` fvOption; community PCMsolver) | Free, GPL | Same job as rank 4, no cell limit | Alternative to Ansys Student. Much steeper learning curve (Linux, text case files) | High |
| – | NREL **SAM** (Solar Water Heating module) | Free | Collector, tank and demand, **no PCM** | Baseline for sanity-checking plain-tank solar fraction per state | Low |
| – | TRNSYS (Type 860), COMSOL, MATLAB | Paid | – | Only if the university lab has a licence. TRNSYS Type 860 is the best "industry" cross-check | – |
| ✗ | EnergyPlus | Free | PCM only in building walls | Already rejected in the O1 Plan v3, §10.1 | – |

**Supporting free libraries:** `pvlib` (plane-of-array irradiance from ERA5 GHI), `CoolProp` (water properties), `pymoo` (NSGA-II), `optuna` (Bayesian search), `scikit-learn`/`xgboost` (surrogate), `SALib` (Sobol sensitivity).

## 4. Recommended plan (fits the existing O2 execution framework)

1. **Keep** the Python grey-box model as the only simulator used to generate DoE data. The frozen configs stay unchanged.
2. **Fix the weak spot in "capsule arrangement".** A lumped or 1-D model cannot tell staggered from inline beds except through the heat-transfer coefficient. Use Ansys Student (or OpenFOAM) on a few small cases to derive an arrangement multiplier on h, cite it, and treat arrangement as a categorical feature. This makes the "arrangement" variable in the O2 title defensible in a viva.
3. **Cross-validate** capsule diameter and flow-rate trends with OpenTerrace on 5–10 matched cases. Report the trend agreement, for example as a Spearman ρ.
4. Optional: compare plain-tank solar fraction against SAM for each state. Tamil Nadu and Uttarakhand currently fall outside the 54–84 % benchmark band, and SAM helps show whether the cause is the climate or the model.

## References (Consensus)

[1] [Optimization design and performance investigation on the cascaded packed-bed TES system with spherical capsules](https://consensus.app/papers/details/5982b0fe20d95c7892959b24481ec836/?utm_source=claude_desktop) (He et al., 2023, Appl. Therm. Eng.)
[2] [PCM addition inside solar water heaters: Numerical comparative approach](https://consensus.app/papers/details/b1e439b2727a5d44bcf3b53e7a62ba0b/?utm_source=claude_desktop) (Bouhal et al., 2018, J. Energy Storage)
[3] [Effect of capsule size and wall thickness of packed bed TES with cylindrical PCM encapsulations](https://consensus.app/papers/details/320533d7f2fb564fa9a3417794bf2fa7/?utm_source=claude_desktop) (Kumar et al., 2024, ICHMT)
[4] [Modeling and optimization of a TES unit with cascaded PCM capsules connected to a solar collector](https://consensus.app/papers/details/ba261e84030958f1bccc61063d9b49ce/?utm_source=claude_desktop) (Nekoonam et al., 2022, SETA)
[7] [Modelling and experimental study of LHTES with encapsulated PCMs for solar thermal applications](https://consensus.app/papers/details/ae0b36bd83d259bea5161f90c5c89d5e/?utm_source=claude_desktop) (Raul et al., 2018, Appl. Therm. Eng.)
[8] [Effect of varying extent of PCM capsule filling on thermal stratification of a storage tank](https://consensus.app/papers/details/b1faaf1b5c6d5f74986657eeadd47c9d/?utm_source=claude_desktop) (Majumdar et al., 2019, Energy)
[10] [Parametric analysis of a packed bed thermal storage device with PCM capsules in a solar heating system](https://consensus.app/papers/details/079fefaca7015034bcb9e39367f0af61/?utm_source=claude_desktop) (Gao et al., 2020, Building Simulation)
[11] [Investigating ML surrogates for the design of a solar thermal DHW system with a heat pump auxiliary](https://consensus.app/papers/details/7648e030045f5386aff965ac8c659f6a/?utm_source=claude_desktop) (Sourgoutsidis et al., 2026, Energies)

## Tool sources
[OpenTerrace JOSS paper (Hærvig, 2024)](https://joss.theoj.org/papers/10.21105/joss.06411) · [OpenTerrace GitHub](https://github.com/OpenTerrace/openterrace-python) · [Modelica Buildings library](https://simulationresearch.lbl.gov/modelica/) · [Buildings SolidsPCM](https://simulationresearch.lbl.gov/modelica/releases/v3.0.0/help/Buildings_HeatTransfer_Data_SolidsPCM.html) · [Ansys Student](https://ansys.synopsys.com/academic/students/ansys-student) · [OpenFOAM solidificationMelting](https://cpp.openfoam.org/v13/classFoam_1_1fv_1_1solidificationMelting.html) · [PCMsolver (OpenFOAM)](https://github.com/skyopener/PCMsolver) · [NREL SAM Solar Water Heating](https://sam.nlr.gov/solar-water-heating.html) · [TRNSYS pricing](https://www.trnsys.com/order/pricing.php.html)
