# Objective 2 - Rajasthan: pipeline documentation (v3, 2026-10-28)

These documents describe what is in the code and the saved results (`docs/PROGRESS.md` is the day-by-day log with every gate).

> **Current version: v3 (PCM fraction cap 30 %), completed 2026-10-28** (`docs/PROGRESS.md` section 26). The cap was raised from 20 % as a declared change;
> G8-G11 were re-run, the designs re-selected on 2021-2023 and tested once on the untouched years 2011-2015. The v1 (cap 20 %) held-out test used 2024-2025
> (now labelled used). A 40 % cap / 50 mm radius test was run on 2026-11-10 as a diagnostic on explore/select years only (fronts still touch the new bounds; v3 stays the approved design space; `docs/PROGRESS.md` section 'B1 boundary test', `results/b1_*`). Sections 1b and 5b-5f of `04_RESULTS.md` are the six-issue diagnostics, run on
> the v1 designs and not re-run on v3.

## Corrections applied 2026-11-10

Source: `.claude/Objective_1_and_Objective_2_corrected_methodology_.docx`, each item checked against the file named. **Documentation and comments only:** no pipeline stage was re-run, no result file or the held-out lock was touched. The only code edits were the held-out error message in `src/weather/roles.py` (it said 2024-2025; the test years are 2011-2015, now derived from `YEAR_ROLES`) and a figure title in `src/plots/make_plots_results.py` (the already-rendered PNG still carries the old title until the plots are regenerated). 90 tests pass.

- **Method wording.** "Surrogate-assisted, constrained multi-objective search": the simulator evaluates every reported number; surrogates only rank and propose; hand-written NSGA-II with constrained domination; committee-disagreement active learning; dense-grid check; a selection funnel fixed before the held-out run. Chain with result files on disk: g2 (timestep convergence), g3 (metrics), g4 (multi-node tank), g7 (sensitivity, packing, flow baseline), g8_s1 (screening / ANOVA), g8_s2 (Sobol DOE), g8_s3 (surrogate comparison), g9_s4_s5 (NSGA-II + committee-disagreement active learning), g9_s6 (dense grid), g9_band and the g9 checks, g10_select, g10_test (held-out), g11 (ablations), g13-g18 (shield split, controls, stack anchor, evening scenario, widened bounds, box vertices) and g20-g24 (GP-BO comparison, tank sizing, extra sensitivity, Chen benchmark, flow-dependent F_R); `g19` is only the weather download script and has no result file.
- **Surrogate winners** (`results/g8_s3_selection.csv`): XGBoost 6, quadratic RSM 3 of the 9 (regime, PCM) pairs; the NN ensemble won none. The candidate set in this file is NN ensemble / XGBoost / quadratic RSM, the same three as in Uttarakhand (XGBoost 11, RSM 1 of 12), so the counts differ because the pairs and their DOE data differ; Tamil Nadu's own file lists five candidates (GP-ARD, NN ensemble, RSM, stacked, XGBoost) and picks the stacked ensemble 9 of 9. No file supports an "XGBoost won 21 of 27" claim.
- **Held-out test.** `results/held_out_test.lock`: run id `heldout_3242a7f4fd8a`, UTC 2026-10-27T22:08:05, selection fingerprint recorded; `results/g10_heldout_results.csv`: 9 designs (the chosen design and the best design of every other shortlisted PCM, 3 regimes) x 5 years (2011-2015) = 45 rows, `g_window` > 0 in all 45; PCM peak 62.29-64.07 C (limit 65), water peak 72.18-73.29 C (limit 75). It ran once; **these years, and 2024-2025 (the used v1 test), cannot be reused as untouched data for Objective 3.**
- **Pareto front versus selected compromise.** They are different objects. The front is the final NSGA-II set per (regime, PCM) pair (`g9_seed_front_*`, `g9_points_*`); the selected compromise is one design per regime picked from up to 30 re-simulated front designs by the fixed rule of decisions D9/D10 (`g10_select.py`, `g10_selection_r*.json`, `g10_selection_candidates_r*.csv`). The funnel and its fingerprint were fixed before `g10_test.py` ran (the lock stores `selection_fingerprint`).
- **"Best within the declared box", never "optimal".** The box is PCM fraction 2-30 % and flow 0.010-0.050 kg/s (`configs/design_space.yaml`). The 30 % cap is limiting: `04_RESULTS.md` section 5e (`results/g17_widen_r*.csv`) gives +47.2 / +37.9 / +40.6 kWh at a 40 % fraction against bands of 21.1 / 14.4 / 21.9 kWh (the CSVs also give 179.96 / 176.82 / 186.92 kWh at 40 % against 135.96 / 141.74 / 149.27 kWh at 30 %). The radius edge and the upper flow bound are not limiting.
- **Flow.** The collector F_R is flow-independent by default (`configs/system_config_shared.yaml:28-29`) and a 0.010 kg/s optimum is flagged a model artefact (`configs/design_space.yaml:31`). G24 (`results/g24_flow_fr_r*.csv`) switched on a flow-dependent F_R and `g_window` changed by at most 1.43 kWh at any flow (`PROGRESS.md` rounds this to 1.4). It is a **sensitivity, not part of the released model**; whether to adopt it is open decision (d).
- **Tank sizing.** 50 L with 1.5 m2 (`configs/system_config_shared.yaml:24,38`) = 33.3 L/m2, below the 40-100 L/m2 of IS 12976:2023 section 4.2 (decision D8; `05_LIMITATIONS_AND_OPEN_ITEMS.md` item 2). The 112.5 L resizing result is from the legacy model only and is not usable for the current model; `g21_sizing_r*.csv` is the current-model tank-size study.
- **Terminology (three separate claims).** (1) *Simulator verification* - done: energy balance, timestep convergence (`g2_*`), multi-node check (`g4_*`). (2) *CFD model-consistency cross-check* - Rajasthan's OpenFOAM work stopped at the literature benchmark: the setup does not reproduce Tan et al. 2009, the mesh study is not grid-independent, and no design-capsule run or O2 re-scoring was done (`07_OPENFOAM_VALIDATION.md`, status 2026-10-29; decision 2026-10-30: report the CFD as an unvalidated upper bound). (3) *Experimental validation* - **NOT DONE** (no hardware or field data exist; that is Objective 4). Never write "CFD-validated".
- **Citations.** NSGA-II: Deb et al. 2002 (`Deb2002NSGA2` in `.claude/Sources/references.bib`; cited in `src/optimize/nsga2.py`). Comparing several surrogates per pair: Bhattacharjee et al. 2016 (`Bhattacharjee2016MultiSurrogateMOO`). Kumar and Srinivas 2024 (`Kumar2024PMaSynRM_Kriging_NSGA2`) is a motor-design paper and a weak fit for a Taguchi-type screening step; prefer the in-domain precedents already in `.claude/Sources/`: Li 2020 (`Li2020`), Assareh 2023 (`Assareh2023`), Chen 2025 (`Chen2025`), Eldokaishi 2022 (`Eldokaishi2022`). Bradford et al. 2018 (`Bradford2018GP_MOO`) is a multi-objective GP method and must NOT be cited for a single-objective expected-improvement search (the g20 study, `scripts/g20_gp_bo_comparison.py`, is single-objective expected improvement on a Matern-5/2 GP). Not in the bib, so not cited here (none invented): the Sobol sequence, XGBoost, committee-disagreement active learning, and a standard expected-improvement Bayesian-optimisation reference ("EI reference needed").
- **Hand-off values.** 50 L / 1.5 m2 / delivery 45 C (`configs/system_config_shared.yaml:24,38,84`); see `06_OBJECTIVE3_HANDOFF.md`.

Scope: this folder only (Rajasthan). Fixed and not optimised: 50 L tank, 1.5 m2 collector, 300 L/day demand, the O1 PCM top-3
(`configs/system_config_shared.yaml`).

## Contents

| File | What it covers |
|---|---|
| [`01_MODEL_AND_METRICS.md`](01_MODEL_AND_METRICS.md) | simulator (single-node and multi-node tank), the repairs, the WP1 metrics, paired baseline |
| [`02_WEATHER_AND_DESIGN_SPACE.md`](02_WEATHER_AND_DESIGN_SPACE.md) | weather inventory, year roles and the held-out lock, approved design space |
| [`03_OPTIMISATION_PIPELINE.md`](03_OPTIMISATION_PIPELINE.md) | screening, DOE, surrogates, NSGA-II + active learning, dense-grid check, selection, ablations |
| [`04_RESULTS.md`](04_RESULTS.md) | generated tables of the results (chosen designs, held-out test, optimiser checks, ablations) |
| [`05_LIMITATIONS_AND_OPEN_ITEMS.md`](05_LIMITATIONS_AND_OPEN_ITEMS.md) | what the results do not support, deviations, items for Dr. Deepika |
| [`06_OBJECTIVE3_HANDOFF.md`](06_OBJECTIVE3_HANDOFF.md) | the regenerated environment contract for Objective 3 |
| [`07_OPENFOAM_VALIDATION.md`](07_OPENFOAM_VALIDATION.md) | OpenFOAM check of the capsule constants c and F (WP2-C): status, benchmark, mesh study, what was not done |
| `PROGRESS.md` | the progress log, gates G1-G19 with evidence |
| `../results/results_registry.csv` | every headline number with its source file (`scripts/g12_registry.py`) |

## Headline findings (all in `04_RESULTS.md`, with the files they come from)

1. The old demand-timing bug (UTC instead of local time) changed the plain-tank annual energy by about 31 % in regime 0 (log section 3).
2. With the repaired model and the 30 % cap (v3), the best designs sit at the edge of the box again: inner radius 39.5-40 mm and PCM fraction 28-30 %, the same PCM as in v1 in every regime
   (savE OM55, PureTemp 60, PureTemp 58). The gain in the night-and-morning window over the same-flow water-only tank is 130 / 137 / 141 kWh per year on the select years (v1: 99 / 94 / 95) and
   137.5 / 145.7 / 149.3 kWh per year on the untouched test years 2011-2015 (weakest single test year 130-147 kWh), far above the bands of 14-22 kWh. In regime 0 the chosen design and the
   runner-up PCM are tied on the test years (137.5 against 138.0 kWh, inside the band). The optimiser still asks for the maximum PCM: the fraction sweep keeps rising by +17 to +21 kWh
   from 25 % to 30 %, so the cap is still limiting at 30 % (sections 1 and 4 of `04_RESULTS.md`); the true best amount is not found and is not claimed.
3. Nulls and negatives: the night-serve duration (tau_serve) is not improved against the same fixed 50 L tank (water displacement cancels the PCM benefit; the evening E_del45 energy is higher with PCM by about 0.25 kWh per scenario night, section 5d of `04_RESULTS.md`), `d_overheat` is positive for every PCM design but mixes a water-side term (lower with PCM in every design-year checked) with a PCM-side throttle
   (section 1b of `04_RESULTS.md`), and thickness at constant mass (v1 diagnostic) is informative only from an interior anchor: small radii are worse and R 30-40 mm are within the band of R 25 mm (section 5b of `04_RESULTS.md`).
4. (v1 diagnostic, not re-run on v3.) The level of the result depends on a modelling assumption (where the capsule stack sits in the tank) by more than the band: 46 / 56 / 55 kWh range for the chosen designs over bottom / centre / top, against bands of 10-16 kWh; the sign of the gain does not (section 5c of `04_RESULTS.md`).

## Entry points

`pipeline.py` and `run_all_rajasthan.py` run the chain described here.

```
python pipeline.py --state rajasthan --stage status                 # which outputs exist, is the held-out lock set
python pipeline.py --state rajasthan --stage <stage>                # verify sensitivity baseline screening doe surrogate band optimize
                                                                    # select ablation report handoff plots (heldout refuses: lock set)
python pipeline.py --state rajasthan --stage simulate --cluster 0 --pcm-rank 1 --radius-mm 40 --fraction 0.2 --flow 0.025 --purpose select
python run_all_rajasthan.py                                         # tests + report + handoff + plots from saved results (about 1 min)
python run_all_rajasthan.py --full --dry-run                        # print the whole chain; --full itself is hours
```

Stages that would re-decide the frozen designs (baseline ... select) refuse while `results/held_out_test.lock` exists unless
`--allow-invalidate` is passed, because a re-run would make the one held-out evaluation meaningless. Details at the top of `pipeline.py`.
Figures: see the table below and `docs/plots/10_PLOTS.md`.

## Figures (`results/plots/`, code `src/plots/make_plots_results.py`)

| File | Shows |
|---|---|
| `fig1_front_vs_grid.png` | optimiser points against the 720-design grid, selected design starred (grid exists for the rank-1 PCM only) |
| `fig2_g9_grid_check.png` | G9 epsilon gap as a share of the band, 9 pairs |
| `fig3_gain_by_year_role.png` | chosen design g_window on explore / select / held-out years with the band |
| `fig4_heldout_pcm_comparison.png` | held-out g_window of the chosen and the other O1 PCMs |
| `fig5_heldout_nulls_and_costs.png` | night-serve gain, extra shield hours, PCM peak (65 C line) |
| `fig6_ablations.png` | G11 changes in g_window against the band |
| `fig7_surrogate_comparison.png` | G8 surrogate families by rank agreement |
| `fig8_fraction_response.png` | G7 gain against PCM fraction |
| `fig9_boundary_share.png` | fronts sitting at a bound of the design box |

## How to reproduce (from this folder)

The individual scripts behind each stage:

```
python -m pytest tests                                              # 80 tests
python scripts/g2_timestep_convergence.py 150,75,37.5 out.csv       # G2 time step (arguments: dt list, output file)
python scripts/g3_metrics_report.py                                 # G3 metrics
python scripts/g4_multinode_report.py                               # G4 multi-node tank
python -c "from src.weather.inventory import build_inventory; build_inventory()"   # G5 weather (writes data/weather/point_years/)
python scripts/g6_phase4_o1.py                                      # G6 verification on the O1 PCMs
python scripts/g7_sensitivity.py <regime>                           # G7 sensitivity study (regimes 0 1 2)
python scripts/g7_flow_baseline_and_packing.py                      # G7 same-flow baseline and packing limits
python scripts/g8_build_plain_baseline.py <regime>                  # plain-tank flow grid (explore and select years)
python scripts/g8_s1_screening.py <regime> <pcm_rank>               # S1 Taguchi L9 (rank 1..3)
python scripts/g8_s2_doe.py <regime> <pcm_rank>                     # S2 Sobol DOE
python scripts/g8_s3_compare.py                                     # S3 surrogate comparison
python scripts/g9_band.py <regime>                                  # WP6 repeatability band
python scripts/g9_s4_s5.py <regime> <pcm_rank>                      # S4/S5 active learning (see 03 for the follow-up variants)
python scripts/g9_s6_grid.py <regime> [pcm_rank]                    # S6 dense grid
python scripts/g9_assess.py                                         # G9 checks
python scripts/g10_select.py <regime>                               # selection, regimes 0 1 2
python scripts/g10_test.py --confirm-run-once                       # held-out test: ONLY ONCE, refuses if the lock exists
python scripts/g11_ablation.py <regime>                             # ablations
python scripts/g12_registry.py ; python scripts/g12_results_doc.py  # registry and results tables
python -m src.handoff.build_obj3_contract_v2                        # Objective 3 contract v2 (needs PYTHONPATH=. if config is not found)
```

Exact arguments of each script are in its docstring. Runtimes on the development machine: one year of the multi-node tank takes a few
seconds; the nine active-learning runs took about 40-80 minutes in parallel, the selection about 5 minutes per regime.
