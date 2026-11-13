# Objective 2 - Uttarakhand: current pipeline (2026-10-28)

**Status: current.** Port of the Rajasthan current chain (v3, PCM fraction cap 30 %) to Uttarakhand with Objective 1's K = 4 regimes (final, confirmed 2026-11-12; see the corrections section below).
`docs/PROGRESS.md` is the log of the port and every gate. The legacy K = 5 chain (UTC-indexed demand, single-node tank) was removed in the
cleanup of 2026-10-28, as in Rajasthan; it is in git history only. The full report is `Objective2_Uttarakhand_Report_v3.docx` (PDF beside it). `Objective2_Uttarakhand_Algorithms_Explained.docx` (PDF beside it) explains what the simulation includes, every algorithm, why it was chosen over the alternatives, and how to run the steps in parallel and faster; `Objective2_Uttarakhand_Summary.docx` (PDF beside it) is its 3-page summary.

## Corrections applied 2026-11-10

Source: `.claude/Objective_1_and_Objective_2_corrected_methodology_.docx`, each item checked against the file named. **Documentation and comments only:** no pipeline stage was re-run, no result file or the held-out lock was touched. The only code edit is the module docstring of `src/weather/roles.py` (it said Uttarakhand "has never run a held-out test"; the test ran once, see below). 81 tests pass.

- **K = 4 inheritance (resolved 2026-11-12).** The O1 inputs here have four regimes (`data/objective1/cluster_profiles_uttarakhand.csv`: 10 / 23 / 9 / 3 points) and come from O1 commit `6be0dcd` (2026-10-03), which is on `origin/tamilnadu-data` only and is **not an ancestor of O1 main**; O1 main's `05_cluster_uttarakhand.py:73` still has `K_FINAL = 5`. Earlier text calling K = 4 "Objective 1's new regimes" should be read with this caveat (open decision a). **Resolved 2026-11-12:** the student confirmed that Objective 1 has been changed to K = 4 for Uttarakhand and that the project continues with K = 4; there will be no move to K = 5.
- **Method wording.** "Surrogate-assisted, constrained multi-objective search" (simulator-evaluated; surrogates only rank and propose; hand-written NSGA-II; committee-disagreement active learning; dense-grid check; selection funnel fixed before the held-out run). Chain with result files on disk: g2, g3, g4, g7, g8_s1, g8_s2, g8_s3, g9_s4_s5, g9_s6, g9_band and the g9 checks, g10_select, g10_test (held-out), g11 and g13-g17; there are no result files for g18 or g20-g24 in this state.
- **Surrogate winners** (`results/g8_s3_selection.csv`): XGBoost 11, quadratic RSM 1 of the 12 (regime, PCM) pairs; candidates are NN ensemble / XGBoost / quadratic RSM, the same three as in Rajasthan (XGBoost 6, RSM 3 of 9), so the counts differ because the pairs and their DOE data differ (Tamil Nadu used five candidates and picked the stacked ensemble 9 of 9). No file supports "XGBoost won 21 of 27".
- **Held-out test.** `results/held_out_test.lock`: run id `heldout_c75ac0e6fb78`, UTC 2026-10-28T13:18:41, selection fingerprint recorded; `results/g10_heldout_results.csv`: 12 designs (chosen plus the best design of each other shortlisted PCM, 4 regimes) x 2 years (2024-2025) = 24 rows. Outcome: the 9 designs of regimes 0-2 have `g_window` > 0 in both years (chosen designs: mean `g_window` 76.0 / 61.8 / 56.4 kWh for regimes 0 / 1 / 2), while **all 3 designs of regime 3 are negative** (-4.8 / -10.1 / -6.2 kWh mean over the two years: no gain over the water-only twin). PCM peak 62.01-64.21 C (limit 65), water peak 72.08-73.09 C (limit 75). It ran once; **2024-2025 are now used and cannot be reused as untouched data (e.g. by Objective 3).**
- **Pareto front versus selected compromise.** Different objects: the front is the final NSGA-II set per pair (`g9_seed_front_*`); the compromise is one design per regime from up to 30 re-simulated front designs by the fixed D9/D10 rule (`g10_select.py`, `g10_selection_r*.json`). The funnel and its fingerprint were fixed before `g10_test.py` ran.
- **"Best within the declared box", never "optimal".** Box: PCM fraction 2-30 %, flow 0.010-0.050 kg/s. `04_RESULTS.md` section 5e and item 2 of `05_LIMITATIONS_AND_OPEN_ITEMS.md` state that the 30 % cap is still limiting in regimes 0-2 (those figures were not re-verified in this pass). The collector F_R is flow-independent (`configs/system_config_shared.yaml`), so a 0.010 kg/s optimum is a model artefact; no G24 flow-dependent-F_R study exists for this state (its result for Rajasthan is a sensitivity of at most 1.43 kWh, not part of the released model).
- **Tank sizing.** 50 L with 1.5 m2 (`configs/system_config_shared.yaml:38,24`) = 33.3 L/m2, below the 40-100 L/m2 of IS 12976:2023 section 4.2 (O2 decision D8, recorded in `../objective2-rajasthan/docs/05_LIMITATIONS_AND_OPEN_ITEMS.md` item 2); the 112.5 L resizing study is Rajasthan legacy-model only. This limitation was not previously written in the Uttarakhand docs.
- **Delivery target.** 50 C (`configs/system_config_shared.yaml:93`) versus 45 C in Rajasthan; O1 Uttarakhand also uses 50 C (own constants), not the 60 C basis of `pcm_shared_config.py` (open decision b, resolved 2026-11-12: 50 C is final).
- **Terminology (three separate claims).** (1) *Simulator verification* - done: energy balance, timestep convergence (`g2_*`), multi-node check (`g4_*`). (2) *CFD model-consistency cross-check* - this state has OpenFOAM cases in `openfoam_cfd/`; 1 of 10 capsule cases was run (`r0_chosen_puretemp_58`, 2026-10-29) and none of the 12 tank cases. The solver set-up is Rajasthan's, which does not reproduce the Tan 2009 or Dong 2022 experiments and is not mesh-converged, so every CFD number is an unvalidated upper bound on the melt rate (`openfoam_cfd/README.md` section 4); no experimental data exist. (3) *Experimental validation* - **NOT DONE** (no hardware or field data exist; that is Objective 4). Never write "CFD-validated".
- **Citations.** NSGA-II: Deb et al. 2002 (`Deb2002NSGA2` in `.claude/Sources/references.bib`; cited in `src/optimize/nsga2.py`). Comparing several surrogates per pair: Bhattacharjee et al. 2016 (`Bhattacharjee2016MultiSurrogateMOO`). Kumar and Srinivas 2024 (`Kumar2024PMaSynRM_Kriging_NSGA2`) is a motor-design paper and a weak fit for a Taguchi-type screening step; prefer the in-domain precedents already in `.claude/Sources/`: Li 2020 (`Li2020`), Assareh 2023 (`Assareh2023`), Chen 2025 (`Chen2025`), Eldokaishi 2022 (`Eldokaishi2022`). Bradford et al. 2018 (`Bradford2018GP_MOO`) is a multi-objective GP method and must NOT be cited for a single-objective expected-improvement search. Not in the bib, so not cited here (none invented): the Sobol sequence, XGBoost, committee-disagreement active learning, and a standard expected-improvement Bayesian-optimisation reference ("EI reference needed").

Scope: this folder only. Fixed and not optimised: 50 L tank, collector area, the Uttarakhand demand profile, the O1 PCM top-3, **delivery target 50 C**
(`configs/system_config_shared.yaml`). Held-out test years 2024-2025, used once. Nothing is committed to git by this work.

## Contents

| File | What it covers |
|---|---|
| [`01_MODEL_AND_METRICS.md`](01_MODEL_AND_METRICS.md) | simulator, repairs, WP1 metrics at the 50 C target, paired baseline |
| [`02_WEATHER_AND_DESIGN_SPACE.md`](02_WEATHER_AND_DESIGN_SPACE.md) | K = 4 regimes and medoids, weather inventory, year roles, shortlist, design space |
| [`03_OPTIMISATION_PIPELINE.md`](03_OPTIMISATION_PIPELINE.md) | screening, DOE, surrogates, NSGA-II + active learning, dense grid, selection, ablations, code changes for Uttarakhand |
| [`04_RESULTS.md`](04_RESULTS.md) | generated tables and readings (chosen designs, held-out test, optimiser checks, ablations, diagnostics) |
| [`05_LIMITATIONS_AND_OPEN_ITEMS.md`](05_LIMITATIONS_AND_OPEN_ITEMS.md) | what the results do not support, deviations from Rajasthan, items for the guide |
| [`06_OBJECTIVE3_HANDOFF.md`](06_OBJECTIVE3_HANDOFF.md) | the Objective 3 environment contract v2 |
| [`plots/10_PLOTS.md`](plots/10_PLOTS.md) | the nine result figures |
| `PROGRESS.md` | the progress log, gates G1-G12 |
| [`../openfoam_cfd/README.md`](../openfoam_cfd/README.md) | Uttarakhand OpenFOAM capsule and tank cases, ParaView scripts (case files written, not run) |
| `../results/results_registry.csv` | every headline number with its source file (`scripts/g12_registry.py`) |

## Headline findings (all in `04_RESULTS.md`, with the files they come from)

1. **Regimes 0-2: PCM helps.** Chosen designs PureTemp 58 / PureTemp 58 / savE OM55 at inner radius about 40 mm and fraction 26-30 %. Gain in the 18:00-09:00
   window over the same-flow water-only tank: 80.0 / 72.1 / 63.0 kWh/yr on the select years and 76.0 / 61.8 / 56.4 kWh/yr on the 2024-2025 test years
   (weakest test year 74.6 / 60.7 / 49.6), against bands of 22.0 / 19.4 / 20.0 kWh. All 4 dense-grid checks and all 12 seed-stability checks pass.
2. **Regime 3 (cold, high altitude): PCM does not help.** No design of PureTemp 53, n-Hexacosane or Myristic acid beats the water-only tank beyond the
   6.1 kWh band; the gain falls as PCM is added. The selection log says `meaningful_on_primary_metric: false`; the honest recommendation is water-only.
3. **Still boundary-limited at the 30 % cap** in regimes 0-2: 30 % to 40 % adds +23 to +30 kWh in a diagnostic run, beyond the band. The best PCM amount is not found.
4. **PCM choice inside a regime is not resolved.** On the test years the runner-up PCM is within the band of the chosen one in every regime (in regime 0 PlusICE A58
   is 10.4 kWh ahead, inside the 22 kWh band).
5. Nulls and costs: night-serve duration is shorter with PCM than in the same 50 L tank (water displacement); evening energy up to 50 C is higher. `d_overheat`
   is positive, but the water-side shield hours are lower with PCM in every design-year; the positive part is the PCM-side throttle. The gain level depends on
   the capsule-stack position by 35-54 kWh, the sign does not.

## Entry points

```
python pipeline.py --state uttarakhand --stage status                 # which outputs exist, is the held-out lock set
python pipeline.py --state uttarakhand --stage <stage>                # verify sensitivity baseline screening doe surrogate band optimize
                                                                      # select ablation report handoff plots (heldout refuses: lock set)
python run_all_uttarakhand.py                                         # tests + report + handoff + plots from saved results
python run_all_uttarakhand.py --full --dry-run                        # print the whole chain; --full itself is about 6 h
```

Stages that would re-decide the frozen designs refuse while `results/held_out_test.lock` exists unless `--allow-invalidate` is passed.

## Figures (`results/plots/`)

`fig1`-`fig9` from `src/plots/make_plots_results.py` (front vs grid, G9 check, gain by year role, held-out PCM comparison, nulls and costs, ablations,
surrogates, G7 fraction response, boundary share), listed in `plots/10_PLOTS.md`.

## How to reproduce (Python 3.12, from this folder)

```
python -m pytest tests
python scripts/g2_timestep_convergence.py 150,75,37.5 results/g2_timestep_convergence_150_75_37p5.csv
python scripts/g3_metrics_report.py ; python scripts/g4_multinode_report.py
python -c "from src.weather.inventory import build_inventory; build_inventory()"
python pipeline.py --state uttarakhand --stage verify                  # ... then sensitivity baseline screening doe surrogate band optimize select
python scripts/g7_paired.py                                             # paired G7 file for fig8
python scripts/g10_test.py --confirm-run-once                           # held-out test: ONLY ONCE (already done; refuses now)
python scripts/g11_ablation.py <regime>                                 # and scripts/g13 ... g17 with <regime> = 0 1 2 3
python scripts/g12_registry.py ; python scripts/g12_results_doc.py ; python scripts/g12_verify_docs.py
```
