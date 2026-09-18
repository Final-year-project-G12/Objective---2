# Literature Reference Base (Objective 2)

This is the project's frozen citation source, carried over verbatim from
`vertopal.com_references.txt` (the shared bibliography also used by
Objective 1 and the audit report). Every phase doc in `docs_objective2/`
that says "Literature" links here by key (`[Author Year]`) rather than
re-typing the full citation — one master list, no drift between docs.

**How this list is used**: each entry below is tagged with the
Objective 2 phase(s) it actually grounds a design choice for (methodology,
benchmark number, or precedent), not every paper that is merely
thematically adjacent. A paper with no phase tag is background reading
only and is not cited from any specific step. Nothing here is invented —
every entry is a real, findable publication from the frozen reference
file the user supplied; no citation-count or impact metadata is claimed
beyond what the reference file itself states.

---

## PCM material data sheets (Phase 1, 12)

### Rubitherm2024
Rubitherm Technologies GmbH. 2024. "Rubitherm Phase Change Materials –
Product Categories." Product Database.
https://www.rubitherm.eu/en/productCategories.html
**Used for**: the `max_pcm_temp_C=65.0°C` material-stability limit in
`system_config_shared.yaml` (Phase 1), and several shortlisted PCM
property records (RT45HC, RT64HC) in `pcm_database_tamilnadu.csv` used
throughout Phases 5–8 and the Tm retargeting (doc 12).

### PLUSS2024
PLUSS Advanced Technologies Pvt. Ltd. 2024. "PLUSS Phase Change
Materials – Technical Data Sheets." Technical Documentation.
https://www.pluss.co.in/knowledge-center/data-sheets/
**Used for**: PlusICE-family PCM property records (e.g. PlusICE A52,
selected for regime 2/3 post-retargeting — doc 12) in
`pcm_database_tamilnadu.csv`.

---

## Solar collector / tank baseline & benchmark (Phase 1, 3, 4)

### Singh2025
Singh, Brihaspati. 2025. "Application of Phase Change Materials in Solar
Water Heating Systems—a Comprehensive Review." Solar Energy Materials
and Solar Cells 293 (December): 113888.
https://www.sciencedirect.com/science/article/pii/S0927024825004891
**Used for**: the domestic FPC baseline (`system_config_shared.yaml`,
Phase 1) and the 54–84% solar-fraction benchmark band Gate 4 checks
against (Phase 4) — this project's Gate 4 result (51.39%) is reported
honestly as below this band, not tuned to fit it.

### AlMamun2023
Al-Mamun, Md Rashid, Hridoy Roy, Md Shahinoor Islam, Md Romzan Ali, Md
Ikram Hossain, Mohamed Aly Saad Aly, Md Zaved Hossain Khan, et al. 2023.
"State-of-the-Art in Solar Water Heating Systems for Sustainable Solar
Energy Utilization: A Comprehensive Review." Solar Energy 264: 111998.
https://www.sciencedirect.com/science/article/pii/S0038092X23006321
**Used for**: general SWH system framing referenced in
`00_MASTER_OVERVIEW.md`'s background — the same "storage-to-demand ratio
drives solar fraction" pattern this project's Gate 4 caveat (no auxiliary
heater, smaller ratio than benchmark rigs) relies on.

### Rathore2024
Rathore, Pushpendra Kumar Singh, and Basant Singh Sikarwar. 2024.
"Thermal Energy Storage Using Phase Change Material for Solar Thermal
Technologies: A Sustainable and Efficient Approach." Solar Energy
Materials and Solar Cells 277: 113134.
**Used for**: general PCM-in-SWH framing corroborating Gate 3/Phase 7's
finding that PCM benefit is melting-point-and-operating-range dependent,
not automatic.

---

## Geometry, packing, and hydraulics (Phase 2)

### Chen2025
Chen, Guan-Rong, Ting-Wei Liao, Chien-Chun Hsieh, Jagadish Barman,
Chao-Yang Huang, and Chung-Feng Jeffrey Kuo. 2025. "Using the Taguchi
Method and Grey Relational Analysis to Optimize the Parameter Design of
Flat-Plate Collectors with Nanofluids and Phase Change Materials in an
Integrated Solar Water Heating System." Energy Conversion and
Management: X 26 (April): 100910.
https://www.sciencedirect.com/science/article/pii/S259017452500042X
**Used for**: the tank sizing baseline (`system_config_shared.yaml`
Table 1, Phase 1) and the 15%/20% PCM-volume-fraction test levels Phase 2
checked reachability against (found not reachable at the old
`capsule_count.max=24` bound, hence doc 13's widening to 37).

### Kou2025
Kou, Fangcheng et al. 2025. "A Novel Solar Heating Building Integrated
Heat Pipes and PCMs: Optimizing Thermophysical Properties and Reducing
Energy Consumption." Building and Environment 285 (B): 113674.
https://www.sciencedirect.com/science/article/pii/S036013232501145X
**Used for**: independent confirmation that capsule/geometry parameter
interactions (thermophysical property vs. packing geometry trade-offs)
are a recurring, real design constraint in this literature — the same
class of diameter/count/PCM-fraction interaction Phase 2 documents.

---

## Grey-box simulator & numerical method (Phase 3)

### Barqawi2025
Barqawi, Hamza et al. 2025. "ML-Driven PCM-SWH Optimization and Dynamic
Simulation." Muthanna Journal of Engineering and Technology 13 (3).
https://www.muthuni-ojs.org/index.php/mjet/article/view/946
**Used for**: the backward-Euler / dynamic-simulation-then-ML-optimize
solver pattern this project's Phase 3 simulator and Phase 5→6→7 pipeline
follow (`system_config_shared.yaml` solver entry, Phase 1).

### Abdellatif2025
Abdellatif, Houssam Eddine et al. 2025. "Modeling and Performance
Analysis of Phase Change Materials in Advanced Thermal Energy Storage
Systems: A Comprehensive Review." Journal of Energy Storage 121 (June):
116517.
https://www.sciencedirect.com/science/article/abs/pii/S2352152X25012307
**Used for**: the enthalpy-method / piecewise-`h(T)` PCM modeling
approach `capsule_enthalpy.py` implements, and the documented-simplification
practice (state every correlated/assumed term explicitly) Phase 3 follows.

### Eldokaishi2022
Eldokaishi, A. O. et al. 2022. "Modeling of Water-PCM Solar Thermal
Storage System for Domestic Hot Water Application Using Artificial
Neural Networks." Applied Thermal Engineering 204 (March): 118009.
https://www.sciencedirect.com/science/article/abs/pii/S1359431121014290
**Used for**: precedent for a water-PCM DHW tank model paired with a
learned (ANN) proxy — the same "physics simulator + ML surrogate" split
Phases 3/6/7 enforce (surrogate as ranker, simulator as ground truth).

### Yan2025
Yan, Peiliang, Chuang Wen, Hongbing Ding, Xuehui Wang, and Yan Yang.
2025. "The Potential of Machine Learning to Predict Melting Response
Time of Phase Change Materials in Triplex-Tube Latent Thermal Energy
Storage Systems." Applied Energy 390 (July): 125863.
https://doi.org/10.1016/j.apenergy.2025.125863
**Used for**: independent confirmation that PCM melting-response
timing (mean liquid fraction, cycling behavior) is a first-class ML
prediction target — directly relevant to Gate 3's melt-fraction
diagnostic and the retargeting method's "median charging-hour
temperature" logic (doc 12).

---

## Surrogate modeling & AI-driven design optimization (Phase 6, 7)

### Liu2025
Liu, Shuli et al. 2025. "The Contribution of Artificial Intelligence to
Phase Change Materials in Thermal Energy Storage: From Prediction to
Optimization." Renewable Energy 238 (January): 121973.
https://www.sciencedirect.com/science/article/pii/S096014812402041X
**Used for**: the "prediction then optimization" framing Phase 6→7's
surrogate-then-search structure follows.

### Assareh2023
Assareh, Ehsanolah et al. 2023. "Enhancing Solar Thermal Collector
Systems Through Machine Learning-Driven Multi-Objective Optimization
with PCM." Journal of Energy Storage 73 (December): 108990.
https://www.sciencedirect.com/science/article/abs/pii/S2352152X23023885
**Used for**: direct precedent for ML-driven multi-objective design
optimization of a PCM-augmented solar thermal collector — the same
problem shape as Phase 7's Pareto-tolerance selection rule.

### BarghiJahromi2026
Barghi Jahromi, Mohammad Saleh et al. 2026. "Thermal Energy
Storage-Centric Solar Drying with Phase Change Materials: Intelligent
Optimization via Neural and Evolutionary Regression Models." Journal of
Energy Storage 141 (C): 119192.
https://www.sciencedirect.com/science/article/pii/S2352152X25039052
**Used for**: precedent for tree/ensemble-family regression models
being competitive for PCM-TES design targets, supporting Phase 6's
choice of Extra Trees over a from-scratch neural architecture given the
project's dataset size (215 cases).

### Mohammed2025
Mohammed, Hayder I. et al. 2025. "The Role of Nanotechnology and
Artificial Intelligence in Optimizing Thermal Energy Systems." Applied
Energy 400: 126576.
https://www.sciencedirect.com/science/article/pii/S0306261925013066
**Used for**: general AI-for-thermal-systems framing referenced in
`00_MASTER_OVERVIEW.md`.

### Nemes2025
Nemés, Artur et al. 2025. "A Review of Artificial Intelligence to
Thermal Energy Storage and Heat Transfer Improvement in Phase Change
Materials." Sustainable Materials and Technologies 44 (July): e01348.
https://www.sciencedirect.com/science/article/pii/S2214993725001162
**Used for**: general AI/TES review background for Phase 6's
methodology framing.

### OdoiYorke2025
Odoi-Yorke, Flavio. 2025. "Artificial Intelligence for Solar Water
Heating Systems: A Review of Global Research Trends, Advances, and
Future Perspectives." Energy Conversion and Management: X 28 (October):
101378.
https://www.sciencedirect.com/science/article/pii/S2590174525005100
**Used for**: general AI-for-SWH review background, `00_MASTER_OVERVIEW.md`.

---

## Monte Carlo robustness (Phase 8)

### Chopra2023
Chopra, K., V. V. Tyagi, Sakshi Popli, and A. K. Pandey. 2023.
"Technical & Financial Feasibility Assessment of Heat Pipe Evacuated
Tube Collector for Water Heating Using Monte Carlo Technique for
Buildings." Energy 267: 126338.
https://www.sciencedirect.com/science/article/pii/S0360544222032248
**Used for**: direct methodological precedent for using Monte Carlo
sampling (rather than a single deterministic run) to assess a solar
water-heating system's real-world feasibility/reliability — the same
role Phase 8's 120-draws-per-design Monte Carlo plays here.

### Mansouri2025
Mansouri, Majdi, Khadija Attouri, and Shady S. Refaat. 2025. "Multimodal
Learning Techniques for Time Series Forecasting in Renewable Energy
Systems: A Comprehensive Survey." IEEE Access 13: 151970–92.
https://ieeexplore.ieee.org/document/11141790
**Used for**: background on time-series-forecasting uncertainty in
renewable systems, relevant to Phase 8's weather-ensemble perturbation
design (`src/robustness/weather_ensemble.py`).

### Ghodusinejad2026
Ghodusinejad, Mohammad Hasan et al. 2026. "A Systematic Review of Solar
Irradiance Forecasting Across Time Horizons Using Physical, Satellite,
and AI-Based Methods." Solar Compass 17 (March): 100154.
https://www.sciencedirect.com/science/article/pii/S2772940025000499
**Used for**: background on irradiance-forecast uncertainty sources,
relevant to Phase 8's per-hour GHI noise model.

---

## Weather / climate data sources (Phase 1, Objective 1 upstream)

### GlobalSolarAtlas2024
World Bank Group and Solargis. 2024. "Global Solar Atlas – India
Dataset." Online Database. https://globalsolaratlas.info/download/india
**Used for**: one of the upstream Objective 1 GHI data sources feeding
`daily_aggregates_tamilnadu.csv`, which both the climate signature (Phase
1) and the historical weather ensemble (Phase 8, doc 13) are built from.

### RenewablesNinja2024
Open Energy Analytics Platform. 2024. "Renewables.ninja: Renewable
Energy Time Series Generator." Online Tool. https://renewables.ninja/
**Used for**: upstream hourly-weather generation feeding Objective 1's
medoid-year traces that Phase 3's simulator consumes.

### ICED2026
NITI Aayog, Government of India. 2026. "India Climate & Energy Dashboard
(ICED)." Online Portal. https://iced.niti.gov.in/
**Used for**: upstream India-specific climate context for Objective 1's
regionalization, inherited unchanged by Objective 2.

### ISROSolarCalc2024
Space Applications Centre (SAC), Indian Space Research Organisation.
2024. "ISRO Solar Energy Calculator." Vedas Platform.
https://vedas.sac.gov.in/solar-calculator/
**Used for**: upstream solar-resource cross-check for Objective 1's
climate signature, inherited unchanged by Objective 2.

---

## Deep reinforcement learning / adaptive control (Objective 3 handoff)

### Sivaraj2023
Sivaraj, Sivaraman, Awanish Dubey, and Suresh Rajendran. 2023. "On the
Performance of Different Deep Reinforcement Learning Based Controllers
for the Path-Following of a Ship." Ocean Engineering 286: 115607.
https://doi.org/10.1016/j.oceaneng.2023.115607
**Used for**: a general, non-thermal DRL-controller-comparison precedent
cited in `OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` for the practice of
benchmarking multiple DRL algorithm families against the same
environment/reward before picking one — directly transferable to
Objective 3's choice among DQN/PPO/SAC-family controllers for the PCM
bypass problem.

### Emami2026
Emami, Araz et al. 2026. "Deep Reinforcement Learning-Based Smart
Control of Solar-Driven Power Cycle with Thermal Energy Storage: A Los
Angeles Case Study." Energy Conversion and Management: X 29 (January):
101478.
https://www.sciencedirect.com/science/article/pii/S2590174525006105
**Used for**: direct precedent for a DRL controller coordinating a
solar-driven system with thermal storage — the same problem shape as
Objective 3's charge/discharge/bypass controller, supporting the
`obj3_environment_contract_tamilnadu.json` action-space design.

### Terfai2025
Terfai, Abdelkrim et al. 2025. "Experimental Validation and Enhanced
Thermal Prediction of a Shallow Solar Pond Using ANN-Based Model
Predictive Control." Unconventional Resources 8 (October): 100240.
https://www.sciencedirect.com/science/article/pii/S2666519025001062
**Used for**: precedent for ANN-based MPC as an alternative control
family for a solar-thermal storage system, relevant background for
Objective 3's controller-family choice (contrasted with DRL).

---

## General / background (not cited from a specific Objective 2 step)

Duraivel & Muthuswamy (2025); Hamza (2025); Martínez et al. (2025);
Rajamurugu et al. (2025); the Elsevier special issues (2025, 2026). These
inform general project framing (why PCM-augmented SWH matters, India
policy/deployment context) but are not tied to a specific Phase's design
choice or number, so they are not cross-linked from individual phase
docs.

---

## Full original bibliography

Every entry above (including the "General / background" list) was already
copied verbatim from the project's original `vertopal.com_references.txt`
— nothing has been added, reworded, or invented. That file was folded
entirely into this one during the 2026-09-17 docs consolidation (see
`docs_objective2/16_OBJECTIVE1_DATA_REFRESH.md`) and removed from the
project root as a redundant duplicate; this file is now the single
citation source for Objective 2.
