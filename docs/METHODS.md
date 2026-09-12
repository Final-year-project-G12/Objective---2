# Objective 2 — Methods and Their Justification

This document collects, in one place, **why each method used across
Phases 1–8 was chosen**, for all four states (Tamil Nadu, Rajasthan,
Assam, Uttarakhand). It is written for the methodology section of the
IEEE paper — each subsection names the method, the alternative(s) it was
chosen over, and the specific citation(s) backing the choice (keys refer
to `../../references.bib`). See `00_MASTER_OVERVIEW.md` for what each
phase actually produced per state, and the per-phase docs (`01`–`11`)
for full numeric results.

---

## 1. Frozen shared configuration, not per-state tuning (Phase 1)

**What**: collector area, tank volume/proportions, safety limits, and
the Pareto-tolerance selection rule are frozen once in
`system_config_shared.yaml`/`design_bounds_shared.yaml`, identical
across all four states, rather than tuned per state.

**Why**: the project's goal is a *climate-aware* comparison across
regions — if the hardware itself also varied per state, any performance
difference between states would be confounded with a hardware
difference, making no state-to-state claim defensible. Freezing the
hardware isolates climate as the only varying factor.

**Justification for the specific frozen values**: the 1.5 m²
flat-plate-collector baseline and its `F_R(τα)`/`F_R·U_L` values follow
the domestic-scale FPC baseline reviewed in Singh et al. (2025,
`Singh2025PCMSWH`); the 50 L tank at height:diameter = 2:1 follows Chen
et al. (2025, `Chen2025TaguchiGRAPCM`, Table 1) — the same recent
(2025), PCM-SWH-specific experimental/optimization study whose 10/15/20%
PCM-volume sweep is the benchmark Phase 2's bounds-interaction finding
is measured against. The safety limits (75 °C water, 65 °C PCM) reflect
the material-stability temperatures documented in commercial PCM
datasheets (Rubitherm's RT-series and PLUSS's OM-series,
`RubithermPCM`, `PlussPCM`), not an arbitrary round number.

## 2. Grey-box (not black-box, not full CFD) enthalpy simulator (Phase 3)

**What**: a one-dimensional, lumped/semi-lumped enthalpy-method PCM
model coupled to a Hottel-Whillier-Bliss flat-plate collector and a
Wakao-Kaguei packed-bed heat-transfer correlation, solved with a
linear-implicit backward-Euler scheme and adaptive sub-stepping.

**Why grey-box over black-box (pure ML) or full CFD**: a pure black-box
model (e.g., train a neural network directly on hardware measurements)
has no data to train from at this project's design stage — there is no
hardware yet. Full CFD (resolving the PCM solid-liquid interface
explicitly, 3D flow) is far too expensive to run the thousands of design
cases Phase 5/7 require within a 40-hour-per-state budget. A grey-box
model — known governing equations (energy balance, heat transfer) with
a small number of fitted/assumed parameters (e.g., `melting_half_width_K`)
— is the standard compromise in this literature, matching the approach
Barqawi et al. (2025, `Barqawi2025PCMSim`) and Eldokaishi et al. (2022,
`Eldokaishi2022ANNPCMSWHModel`) take in their own PCM-SWH studies (the
latter pairs a similar grey-box core with an ANN correction layer, a
natural extension this project's Phase 6 surrogate parallels at the
design-optimization level instead).

**Component-level justification**:
- **Collector**: the Hottel-Whillier-Bliss useful-heat-gain equation
  (Hottel & Whillier, 1958, `HottelWhillier1958Collector`; Bliss, 1959,
  `Bliss1959CollectorFactor`; standard modern form in Duffie & Beckman,
  2013, `DuffieBeckman2013SolarEngineering`) is the textbook-standard
  flat-plate-collector model, chosen for being closed-form, well-validated,
  and computationally cheap enough for thousands of full-year runs.
- **Packed-bed heat transfer**: the Wakao & Kaguei (1982) correlation
  (`WakaoKaguei1982PackedBeds`) for the water-to-capsule heat-transfer
  coefficient is a standard, widely-cited packed-bed correlation, chosen
  for the same reasons as the collector model.
- **Packed-bed pressure drop**: the Ergun equation (Ergun, 1952,
  `Ergun1952PackedColumns`) is the standard closed-form correlation for
  pressure drop through a packed bed of spheres, combining viscous and
  inertial terms — used rather than a bespoke CFD-derived correlation
  for the same tractability reason.
- **Solver**: backward-Euler for the fast (water) state, with the PCM
  state lagged one sub-step (a semi-implicit/IMEX coupling), follows the
  numerical scheme Barqawi et al. (2025, §4c) uses for the same reason —
  it keeps the fast state unconditionally stable without needing
  sub-second global timesteps, while the lagged PCM coupling stays
  accurate as long as each sub-step is short relative to the PCM's own
  thermal time constant (a condition this project's adaptive
  sub-stepping fix explicitly enforces after a divergence was found and
  fixed during Phase 4 testing).

## 3. Canonical demand curve tied to Madadi Avargani et al. (2021)

**What**: a fixed 300 L/day (Assam: 100 L/day) daily draw profile,
applied identically to every design evaluated in every phase.

**Why**: the demand profile determines `L_required`, which every
Objective 1 PCM-ranking decision and every Objective 2 solar-fraction
number is computed against — using the same demand assumption Objective
1 already used (Madadi Avargani et al., 2021,
`MADADIAVARGANI2021101350`, a PCM-tank hot-water-output study) keeps
Objective 1's PCM sizing target and Objective 2's simulated performance
evaluating the *same* household, rather than silently comparing a
PCM ranked for one demand scenario against a simulator testing a
different one.

## 4. Latin Hypercube Sampling for the Design-of-Experiments (Phase 5)

**What**: `scipy.stats.qmc.LatinHypercube` over (capsule diameter, flow
rate, capsule count), combined with fixed boundary and no-PCM-baseline
cases, per regime×PCM pair.

**Why LHS over full-factorial or simple random sampling**: with 3
continuous/near-continuous design variables and a per-case cost of a
full-year physics simulation (2–5 s), a full-factorial grid dense enough
to train an accurate surrogate would need far more than the ~150–300
cases this project's 40-hour-per-state budget allows. Latin Hypercube
Sampling (McKay, Beckman & Conover, 1979, `McKayBeckmanConover1979LHS`)
guarantees each variable's marginal range is evenly stratified in a
sample of any size, giving markedly better space-filling coverage per
sample than simple random sampling — the standard choice for
expensive-simulation design-of-experiments in this size regime.

**Why infeasible cases are kept, not discarded**: Phase 6's feasibility
classifier needs negative (infeasible) examples to learn the
feasibility boundary at all — discarding `bounds_violation` rows would
make that classifier untrainable. This also lets the DOE-scale
infeasibility rate (~32.6–32.7% in every state) serve as an independent
cross-check that the same geometric bound interaction fires at the same
rate regardless of climate (`06_PHASE5_DOE.md`).

## 5. Extremely Randomized Trees surrogate, honestly compared to a linear baseline (Phase 6)

**What**: one `ExtraTreesRegressor` (300 trees) per performance target,
plus one `ExtraTreesClassifier` for feasibility, each compared against a
`LinearRegression` baseline on the identical train/holdout split.

**Why Extra Trees over Random Forest, gradient boosting, or a neural
network**: Extra Trees (Geurts, Ernst & Wehenkel, 2006,
`Geurts2006ExtraTrees`) extends Random Forests (Breiman, 2001,
`Breiman2001RandomForests`) by drawing split thresholds randomly rather
than optimizing them, which further reduces variance at negligible bias
cost — a good fit for this project's small training sets (~90–170 rows
per state). A gradient-boosted tree family (e.g. XGBoost) or a neural
network would need careful hyperparameter tuning to avoid overfitting at
this sample size, and Extra Trees already reaches R² ≥ 0.98 on every
primary target in every state, so there was no signal that a more
complex model family was needed.

**Why report the linear baseline honestly, including when it wins**:
per the framework's explicit instruction, every state's Phase 6 doc
reports at least one target (typically `pump_energy_kWh` or
`pcm_mass_kg`) where linear regression ties or beats the tree — a
finding kept in the record rather than hidden, and explained physically
(the sampled design region is close to linear in those specific
targets) rather than dismissed. Implementation throughout uses
scikit-learn (Pedregosa et al., 2011, `Pedregosa2011ScikitLearn`).

**Why the surrogate is never the final answer**: every design the
surrogate favors is re-run in the real simulator in Phase 7 before being
reported anywhere (Bug-Fix 5) — the same caution against trusting an
ML surrogate as ground truth that Barqawi et al. (2025) and Assareh et
al. (2023, `Assareh2023ML_PCM_SolarCollector`) raise for ML-driven
PCM-SWH optimization pipelines.

## 6. Random-search-then-confirm optimization, not full NSGA-II (Phase 7)

**What**: 400 (Assam: 1,000) random candidates per regime×PCM pair,
filtered by the real geometry gate, scored by the surrogate, top-5/pair
re-run in the real simulator, then a pre-declared multi-tier selection
rule (safety filter → 5% Pareto tolerance on useful energy → minimize
pump energy/PCM mass/capsule count → maximize constraint margin).

**Why this instead of a full multi-objective genetic algorithm**: a
proper NSGA-II or active-learning (retrain-and-repeat) loop would find a
more thoroughly-explored Pareto front, but at a cost — many more
simulator calls — outside this project's 40-hour-per-state scope. A
single random-search pass, validated by re-confirming every proposed
design in the real simulator (never trusting the surrogate alone), is
the reduced substitute this framework adopts throughout; the low
surrogate-vs-simulator error achieved (0.02–0.51% across all four
states) suggests the design space is smooth enough in this region that
the reduced approach finds designs close to what iterative
active-learning would likely find, though this was not independently
verified by running the more expensive alternative.

**Why a pre-declared, multi-tier tie-break rule rather than a single
scalar objective**: when two designs are statistically indistinguishable
on useful energy (within the 5% tolerance), preferring the cheaper,
simpler, and safer design is standard engineering practice, mirrored in
how Chen et al. (2025) and Assareh et al. (2023) balance multiple
PCM-SWH design objectives rather than collapsing them into one number.
Declaring the rule *before* running the search (rather than picking a
winner and rationalizing a rule after the fact) is what makes the
resulting "plain tank wins in most regimes" finding a defensible,
non-cherry-picked result.

## 7. Monte Carlo robustness with fixed, cross-state-comparable thresholds (Phase 8)

**What**: 120 independent full-year simulator re-runs per selected
design, perturbing PCM latent heat, weather (two-level: annual scale/
offset + per-hour jitter), demand volume/timing, and mains temperature;
reported against fixed absolute thresholds
(`solar_fraction ≥ 0.45`/`0.50`).

**Why Monte Carlo over reporting only nominal performance**: a single
medoid-weather-year simulation says nothing about how a design performs
under realistic year-to-year and day-to-day variability. Running a
Monte Carlo ensemble and re-simulating every draw in the *real* simulator
(never the surrogate) follows the same logic as Chopra et al. (2023,
`Chopra2023MonteCarloETC`)'s Monte Carlo techno-economic assessment of a
solar collector-storage system.

**Why fixed thresholds, not self-referential ones**: an earlier version
of this project's own Phase 8 (Tamil Nadu) used a threshold defined
relative to each design's own nominal performance and found every
regime trivially scored ~100% reliable — hiding real cross-regime
differences. Switching to fixed, state-independent thresholds is what
actually reveals findings like Uttarakhand's structurally-unreachable
50% demand bar and Tamil Nadu's PCM regime failing both reliability axes
at once — a deliberate methodological choice to prioritize
informativeness and cross-state comparability over each state "looking
good" on its own terms.

**Why a real 10-year historical weather ensemble (Tamil Nadu,
Uttarakhand) is preferred over an assumed distribution**: an external
audit correctly flagged that sampling the annual weather-noise component
from an assumed uniform range, when a real 10-year ERA5/POWER archive
already existed from Objective 1, was a missed opportunity to make a
stronger empirical claim. Drawing from the 10 real observed years
instead — while keeping per-hour jitter synthetic, since sub-daily
multi-year data was not pulled — is the more defensible claim for a
methodology section, even in cases (Tamil Nadu) where the real
variability turned out to be narrower than originally assumed and moved
the numbers only slightly.

---

## Method-to-citation quick index

| Method | Primary citation(s) |
|---|---|
| Flat-plate collector energy balance | `HottelWhillier1958Collector`, `Bliss1959CollectorFactor`, `DuffieBeckman2013SolarEngineering` |
| Packed-bed heat transfer coefficient | `WakaoKaguei1982PackedBeds` |
| Packed-bed pressure drop | `Ergun1952PackedColumns` |
| Canonical demand/night-draw profile | `MADADIAVARGANI2021101350` |
| Design-of-Experiments sampling | `McKayBeckmanConover1979LHS` |
| Surrogate model family | `Geurts2006ExtraTrees`, `Breiman2001RandomForests` |
| ML implementation library | `Pedregosa2011ScikitLearn` |
| PCM-SWH collector/tank sizing baseline | `Singh2025PCMSWH`, `Chen2025TaguchiGRAPCM` |
| PCM-SWH dynamic simulation methodology | `Barqawi2025PCMSim`, `Barqawi2025MLPCMSWH` |
| ML-driven PCM-SWH optimization caution (surrogate ≠ oracle) | `Assareh2023ML_PCM_SolarCollector`, `Eldokaishi2022ANNPCMSWHModel` |
| Monte Carlo robustness methodology | `Chopra2023MonteCarloETC` |
| PCM material-stability / datasheet limits | `RubithermPCM`, `PlussPCM` |
| MCDM PCM selection (Objective 1, inherited context) | `HwangYoon1981MADM`, `OpricovicTzeng2004VIKOR`, `Saaty1980AHP`, `Deng1982GreySystems` |
| PCM sensible+latent volume-share design basis (Phase 5, CLAUDE.md decision — **citation details incomplete, verify before final submission**) | `Zhao2022PCMShare`, `Huang2020PCMVolumeRatio`, `Abdelsalam2020PCMVolume`, `Kozelj2021PCMFraction`, `Xu2017MCDMMaterialAssessment` |

The last row's entries are marked incomplete in `references.bib` — they
are carried forward from this project's own `CLAUDE.md` design-basis
note, which cites them by author/year/finding only. Locate and verify
the full bibliographic record (journal, volume, DOI) against the
original PDFs before using them in the final IEEE submission.
