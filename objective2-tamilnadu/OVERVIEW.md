# Objective 2 — what this folder is doing

**One sentence:** for each of Tamil Nadu's three climate regimes, find the PCM
capsule design and flow rate that make a 100 L solar water tank deliver the
most useful hot water in the evening — and prove it beats the same tank with
no PCM in it.

---

## The question, precisely

A solar water heater stores heat as hot water. Add sealed capsules of
**phase-change material (PCM)** and some of that heat is stored in the
material's melting instead, which can hold the tank warmer into the evening
when people actually want hot water.

Whether that helps depends on choices nobody can make by intuition:

| choice | range searched |
|---|---|
| capsule inner radius | 10–40 mm |
| PCM volume fraction of the tank | 2–30 % |
| flow rate | 0.010–0.050 kg/s |
| capsule arrangement | single-layer, staggered, radial |
| which PCM | Objective 1's shortlist for that regime |

Every candidate is judged against an **identical plain-water tank at the same
flow, weather and demand**. The number that matters is the *difference*, so a
design is never credited for something the plain tank would have done anyway.

---

## How the answer is reached

Thirty pipeline stages, run in order. The chain that actually decides a design:

1. **Convergence** — prove the solver's timestep is fine enough that halving it
   changes annual energy by < 0.05 %.
2. **Sensitivity** — one-factor sweeps to find which parameters matter at all.
3. **Screening** — a Taguchi L9 array with ANOVA.
4. **DOE** — a 128-point scrambled-Sobol design of experiments per regime and PCM.
5. **Surrogate bake-off** — five model families compared; the winner is used to
   guide the search.
6. **NSGA-II + active learning** — multi-objective search that simulates where
   the surrogate is least certain, then refits.
7. **Dense grid cross-check** — 720 designs, to confirm the search did not miss
   a region.
8. **Repeatability band** — how much a result moves under year-to-year scatter,
   timestep, node count and material-property perturbation. Anything smaller
   than this band is noise.
9. **Selection** — a documented S0/S1/S2 funnel with explicit tie-breaks.
10. **Held-out test** — five years reserved from the start, evaluated **once**,
    under a lock that cannot be released.

A separate **Bayesian optimisation** track runs the same problem independently
as a cross-check, and **ANSYS Fluent** checks the physics the fast model assumes.

---

## What it found

| regime | PCM | capsule Ø | PCM fraction | flow | capsules | PCM mass |
|---|---|---|---|---|---|---|
| 0 | PureTemp 58 | 81.6 mm | 29.6 % | 0.0388 kg/s | 104 | 24.8 kg |
| 1 | RT57HC | 81.6 mm | 27.9 % | 0.0295 kg/s | 98 | 23.6 kg |
| 2 | RT57HC | 81.6 mm | 29.9 % | 0.0267 kg/s | 105 | 25.3 kg |

All designs are staggered, in a 100 L tank with a 2.5 m² collector.

**Every gate passes, on years never used to choose anything:**

| gate | held-out result |
|---|---|
| beats the plain tank | **9 / 9** designs |
| PCM stays under 65 °C | 9 / 9 (63.4–64.0 °C) |
| water stays under 75 °C | 9 / 9 (72.2–72.9 °C) |

Nine, not three, because the test covered the chosen design **plus the best
design of every other shortlisted PCM** — so it could not be a cherry-pick.

The margins are 178–269 kWh/yr over a repeatability band of 26–30. That is
roughly 6–9× the noise floor, so the PCM advantage here is decisive rather
than marginal.

---

## Two simulators, and why

| | tank model | ANSYS Fluent |
|---|---|---|
| scope | whole tank, whole year | one capsule, six hours |
| runtime | seconds per simulated year | ~30 min per PCM |
| role | **the optimiser's evaluator** | model consistency cross-check (NOT experimental validation) |
| chooses the design | yes | **no** |

The search ran over 1,100 design evaluations; at CFD speed that is years of
compute. But the fast model buys its speed with assumptions, and Fluent is how
those get tested.

**Why Fluent and not OpenFOAM** (which the source Rajasthan study used):
OpenFOAM's standard solvers have **no native solidification/melting model**.
They resolve heat conduction into a solid capsule but with sensible heating
only — no latent heat. For a study whose premise is that a PCM stores heat *in
its phase change*, that solver can only show the uninteresting half. Fluent has
the enthalpy-porosity model built in.

---

## Where things are

| path | what |
|---|---|
| `src/` | the simulator, design space, surrogates, optimiser, CFD helpers |
| `scripts/` | the 30 pipeline stages (`g2`…`g24`) plus `tn_*` helpers |
| `configs/` | tank, collector, solver and per-state settings |
| `data/` | frozen inputs: Objective 1 outputs, weather, demand profile |
| `results/` | every stage's output, plus `plots/` |
| `ansys/` | Fluent cases, meshes, the live demo, `figures/` |
| `docs/` | results, CFD history, how to run, data provenance |
| `tests/` | 89 tests |
| `archive/` | superseded work — nothing deleted, only retired |

### Start here

| question | file |
|---|---|
| What was corrected, and what is still wrong? | `docs/CORRECTIONS.md` (and `../tamilnadu_pipeline/docs/era5_tamilnadu/CORRECTIONS.md` for O1) |
| What were the results? | `docs/RESULTS.md` (hand-written, layered: read only above the 2026-10-28 superseded banner) |
| The same results, generated from `results/` with no hand-typed numbers | `docs/04_RESULTS.md` (`scripts/g12_results_doc.py`) |
| Which algorithms actually run? | `../documentation/OBJECTIVES_AND_ALGORITHMS.md` — `docs/RESULTS.md`'s own "Algorithms used" table sits **below** the superseded banner and describes the retired architecture |
| Why two simulators? | `docs/SIMULATOR_AND_CFD.md` |
| What does the CFD show, and what went wrong? | `docs/CFD_VERIFICATION.md` |
| How do I run it? | `README.md`, `ansys/HOW_TO_RUN_ANSYS.md` |
| How does weather enter the model? | `O2_Climate_Parameters_and_Simulators.docx` |
| The full write-up | `O2_TamilNadu_Pipeline_Report.docx` |

```bash
python scripts/tn_run_all.py --all --keep-going --workers 6   # the pipeline
python scripts/tn_final_summary.py                            # designs + gates
python -m src.plots.make_plots_results                        # figures
python -m pytest tests/ -q                                    # 89 tests
cd ansys && python fluent_live_demo.py                        # live CFD demo
```

---

## Inherited from Objective 1 - read before quoting any validation claim

Objective 1's corrections pass (2026-11-09) is recorded in
`../tamilnadu_pipeline/docs/era5_tamilnadu/CORRECTIONS.md`. Two items bear
directly on how Objective 2's results may be described:

- **Objective 1 is not "physics-validated".** Its Phase 7 tested whether the
  MCDM ranking tracks simulated solar fraction and largely found it does not:
  mean Spearman rho = +0.169, and **no per-cluster value is statistically
  significant** (n=8-10, p = 0.12-0.96). The PCM shortlist Objective 2
  inherited is an MCDM consensus ranking, not a physics-confirmed one. This
  does not weaken Objective 2's own held-out result, which is a paired
  comparison against a plain tank - but it does mean the *shortlist* carries no
  physics endorsement.
- **The 60 C / 45 C service mismatch.** Objective 1 sized PCM latent heat for a
  **60 C** delivery service; Objective 2 scores delivered energy at **45 C**.
  The comparison Objective 2 reports is sound, since both arms of every paired
  run use the same 45 C metric. What is unquantified is whether Objective 1
  would have shortlisted different PCMs had it sized against 45 C. Open item.

Also settled there, against an external review that claimed otherwise: the
67 C / 65 C / 45 C figures are **not** contradictory safety limits, and
**Objective 3 inherits no safety risk** from them. `TM_TARGET_C = 67 C` never
binds; every shortlisted PCM melts at 54.0-58.0 C and held-out PCM peaks were
63.4-64.0 C, inside the 65 C ceiling.

---

## Pareto front vs selected design - they are different things (added 2026-11-09)

NSGA-II returns a *set*, not a winner. The front and the pick are reported
separately here so the selection rule is auditable.

**The front** (from `g9_grid_check.csv`). Every one of the 9 (regime, PCM-rank)
pairs is cross-checked against a 720-point dense grid. Until 2026-11-09 only
the rank-1 pairs were — 3 of 9 — so this claim now covers the whole design
space that was searched, not a third of it (see `docs/CORRECTIONS.md` O2-14):

| regime | PCM rank | designs on final front | dense-grid front | hypervolume ratio final/grid | worst energy epsilon vs grid (band 28.0) |
|---|---|---|---|---|---|
| 0 | 1 | 65 | 11 | 1.103 | +0.62 pass |
| 0 | 2 | 52 | 9 | 1.107 | -0.26 pass |
| 0 | 3 | 62 | 10 | 1.098 | +5.19 pass |
| 1 | 1 | 50 | 10 | 1.095 | +3.63 pass |
| 1 | 2 | 50 | 9 | 1.107 | +0.30 pass |
| 1 | 3 | 54 | 13 | 1.148 | +0.22 pass |
| 2 | 1 | 53 | 11 | 1.016 | +13.23 pass |
| 2 | 2 | 65 | 8 | 1.086 | +8.37 pass |
| 2 | 3 | 53 | 10 | 1.014 | +11.18 pass |

The search front dominates the dense grid in **all 9 pairs** (hypervolume ratio
1.014–1.148) and every epsilon value on every objective is inside the
repeatability band, several of them negative (the search front strictly covers
the grid front). So the front itself is trustworthy before any selection
happens. This is a search-adequacy check at reduced fidelity, not a proof of
global optimality — see "Honest limits".

**The selection funnel** (from `g10_selection_r{0,1,2}.json`), applied to 90
candidates per regime:

| regime | candidates | S0 within band on g_window | S1 | S2 | chosen | g_window | band |
|---|---|---|---|---|---|---|---|
| 0 | 90 | 14 | 5 | 3 | PureTemp 58 | 276.6 | 28.4 |
| 1 | 90 | 10 | 3 | 3 | RT57HC | 225.5 | 26.0 |
| 2 | 90 | 12 | 5 | 2 | RT57HC | 262.9 | 29.5 |

**The tie-breaks were declared before the results were seen** (plan WP6,
decisions D9/D10): designs whose `g_window` differ by less than the measured
repeatability band are treated as indistinguishable (S0), then the funnel
selects on overheating, then PCM mass, capsule count and temperature margin.

**Regime 0 is the case that shows the rule doing real work.** RT57HC scores
*higher* on window energy than the chosen PureTemp 58 (297.1 vs 283.4 kWh/yr),
but the gap is inside the band, so S0 treats them as tied and the next
criterion decides: overheating, where PureTemp 58 is clearly better (856 vs
1059 shield-hours). The higher-energy design was **not** chosen, and the
documented rule is why.

---

## Three kinds of checking - do not call any of them validation (added 2026-11-09)

"Validation" was being used for three different things. Use these terms:

| what it actually is | call it | status |
|---|---|---|
| Energy-balance and unit tests in code (89 tests, Gate-1 residual) | **simulator verification** | done |
| ANSYS Fluent runs against the fast model's assumptions | **model consistency cross-check** | done, with caveats below |
| Physical measurement on real hardware | **experimental validation** | **NOT DONE** - Objective 4 scope |

**The CFD is not experimental validation and must not be cited as such.** It is
a one-capsule, six-hour model check. Three of the v3 cases returned **0 % liquid
fraction**, which `docs/CFD_VERIFICATION.md` records as the honest result rather
than hiding it; melt fractions elsewhere are conservative because first-order
upwind is the only scheme under which all four PCMs converge; and the mesh is a
symmetry half-slice that excludes buoyancy-driven melt convection. Say "CFD
cross-check of selected modelling assumptions", never "CFD-validated design".

## This is not a global optimum (added 2026-11-09)

The selected designs are **the best found within the declared search bounds**,
and two bounds are known to matter:

- **The 30 % PCM-fraction cap is binding, not slack.** The `g17` widened-bound
  diagnostic shows that at 40 % the window gain is higher by more than the
  repeatability band in **every** regime, with PCM and water peaks still inside
  65 C and 75 C. The cap is administrative: the packing engine accepts 28-48 %
  at R 40 mm, and the only literature in the files read (Chen 2025) covers
  10-20 %. A 40 % run is planned, not done.
- **The flow optimum may be a model artefact.** The collector's F_R is
  flow-independent in this model, so any optimum sitting at the low flow bound
  is suspect. `g17` does show the *upper* bound is not limiting (0.080 kg/s
  moves `g_window` by less than the band in every regime).

Write "best design within the declared 2-30 % PCM-fraction and
0.010-0.050 kg/s search bounds", never "optimal design". For Objective 3 this
matters directly: it inherits a design that is **good and verified**, not one
proven optimal, so it must not treat the inherited flow value as a physical
optimum to defend.

---

## The box-vertex step turned out not to matter (added 2026-11-10)

During the original search, regime 0 PCM 1 failed the dense-grid check twice.
The response was to add a step that simulates the 24 corners of the design box
before three further active-learning rounds. That step was **not
pre-declared** - it was added in reaction to a result - so it needed testing
rather than assuming.

All nine (regime, PCM-rank) pairs were therefore re-run in three states, same
code and same budget:

| state | what it is | points |
|---|---|---|
| `base` | the original 5 active-learning rounds | 251 |
| `novert` | base + 3 more rounds, **no** vertex step | 281 |
| `vert` | base + the 24 box corners + 3 more rounds | 297 |

**Finding: the step makes no difference that the acceptance criterion can
see.** All 27 rows (9 pairs x 3 states) are inside the repeatability band on
every objective. The best hypervolume per pair goes to `vert` in 6 pairs and
`novert` in 3; across every pair and state hypervolume spans 0.983 to 1.000 of
that pair's best, a **total spread of 1.7 %**.

Two things do follow from it:

* **The extra rounds help a little.** `base` is the best state in *no* pair;
  both extended states beat it everywhere. So three more rounds were worth
  running.
* **How you spend them is irrelevant.** Seeding box corners and simply running
  three more committee-disagreement rounds land within 1.7 % of each other.

And one thing that does *not* follow, which is the point of the exercise:
**the step is not what fixed regime 0 PCM 1.** That pair now passes in all
three states, worst epsilon 0.6 against a band of 28.0 - including `base`,
the state that originally failed. The original failure does not reproduce once
the pair is run against the full nine-pair dense grid of O2-14. So the honest
account is that an unplanned step was added for a reason that no longer holds,
and keeping it is harmless but not load-bearing.

Source: `results/g18_issue1_with_without.csv`, generated by
`scripts/g18_issue1_compare.py`; reported in `docs/04_RESULTS.md` section 5f,
where every figure is computed rather than typed.

## Honest limits

These are stated here rather than left for a reader to find:

- **CFD melt fractions are conservative.** First-order upwind is the only
  discretisation under which all four PCMs converge, and it is more diffusive
  than second order. The *ordering* of the PCMs is the result; the absolute
  values are low.
- **The CFD mesh is a symmetry half-slice**, so buoyancy-driven convection in
  the melt is excluded. That enhancement is carried empirically by the tank
  model — a division of labour, not an oversight.
- **Wind and humidity do not affect any result.** They are in the weather files
  but reach no equation; the collector and tank loss coefficients are fixed. For
  coastal regimes that is a real simplification.
- **Irradiance is used as plane-of-array directly**, with no tilt model. It
  applies equally to the PCM tank and its plain twin, so the reported
  *difference* is largely insulated — the absolute energies are not.
- **`g12_verify_docs` now passes: 0 missing of 310 references** (2026-11-09).
  It had never passed before. The count went 68 → 0 in three groups: ~25 were
  checker bugs (template placeholders like `{state}` treated as literals, the
  project's own folder name as a prefix, sibling repos outside the tree), 20
  were genuine renames, and 16 are genuinely gone and now **say so in the
  document**, since the checker only excuses a path whose line declares it
  deleted/retired/renamed. Details in `docs/CORRECTIONS.md` → O2-13.

- **`docs/HOW_TO_RUN.md` was entirely unusable and is only partly repaired.**
  Its banner named `run_rajasthan_pipeline.py` and `pipeline.py` as the two
  pipelines; **neither exists**, nor do `src/doe/`, `src/surrogate/` or
  `src/robustness/`. Its legacy sections also report results the current run
  contradicts — "radial won in all 3 regimes" (they are staggered) and
  "P(temperature-safe) = 0 %/18 %/0 %" (held-out is 9/9 safe). The top of the
  file now documents the real pipeline (`scripts/tn_run_all.py`, stages
  `g2`…`g25`) and flags the wrong claims; **the body below it is still the old
  guide, kept as history.** A full rewrite is open.

---

## A defect worth knowing about

Partway through, every Objective-2 result had to be thrown away and re-run.

The per-point-year weather cache carried its solar columns **shifted +5 hours**
against their own timestamps — IST truncated to whole hours, written onto
local-clock stamps but labelled UTC. That moved collector gain from about 11:30
to about 16:30 local, far closer to the 19:00 demand peak than reality, which
systematically flattered PCM on the study's primary objective.

It was found by checking irradiance against computed sunrise and sunset, and
confirmed three independent ways. The cause turned out to be a second raw data
set whose header declares **Local Solar Time**, not UTC, read as though its keys
were UTC.

All 45 point-years were rebuilt from raw with a **mandatory ephemeris gate**:
the rebuild refuses to write unless clearsky daylight brackets true sunrise and
sunset on every day. The lesson is in `docs/CFD_VERIFICATION.md` and the
progress log, and it is the reason the inventory now records *how* each year's
timestamps were derived rather than just asserting a time standard:

> Provenance metadata is not verification.
