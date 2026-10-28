# Progress log - Objective 2, Uttarakhand (current chain)

Single log of the port of the Rajasthan current chain (v3, PCM fraction cap 30 %) to Uttarakhand, 2026-10-28. Gate numbering follows
`../objective2-rajasthan/docs/PROGRESS.md`; only what differs for Uttarakhand, and the Uttarakhand evidence, is written here. Nothing was committed to git.

## 1. Starting point

- `git pull` (fast-forward to 96bbfd7) brought the Rajasthan redesign (`objective2-rajasthan`, PR #5).
- Objective 1 had reduced Uttarakhand from K = 5 to K = 4 regimes (O1 commit 6be0dcd). The Uttarakhand O2 folder still held K = 5 frozen inputs,
  the legacy single-node chain (`results/uttarakhand/`, `docs_objective2/`) and no current-chain code.
- Decisions taken with the user: held-out test years **2024-2025** (explore 2016-2020, select 2021-2023); run the **full chain** with
  Rajasthan's approved v3 design space, stopping only if a gate fails.

## 2. Port (code and inputs)

- Copied from `objective2-rajasthan`: `src/`, `scripts/`, `tests/`, `pipeline.py`, `run_all_uttarakhand.py` (from `run_all_rajasthan.py`),
  `configs/design_space.yaml`, `configs/cfd_closure_v1.yaml`, the two shared configs. State names replaced in every `.py` file (196 replacements).
- `configs/system_config_shared.yaml`: Rajasthan's version with the safety-shield block, but the **delivery target stays at Uttarakhand's 50 C**
  (Rajasthan 45 C). All WP1 metrics read this value.
- Frozen O1 inputs refreshed (`build_input_package.py`, 61 files, `data/objective1/manifest.json`); `configs/states/uttarakhand.yaml` regenerated for 4 regimes.
- Medoids: the O1 recommendation-card medoids UKP_0014 / UKP_0029 / UKP_0025 / UKP_0041 (`src/weather/inventory.py: CURRENT_MEDOIDS`). The build script's
  earlier pick (highest membership probability: UKP_0001 / 0004 / 0002 / 0023) is NOT the card medoid and was replaced; both build scripts now take `CURRENT_MEDOIDS`.
- `build_regime_weather.py` now also writes `WS_ms`, `local_hour` and `local_date` (IST), which the demand-timing repair requires. The K = 5 regime-4
  weather files were moved to `data/legacy/k5_weather/`.
- `src/io_utils.py: o1_top3` accepts the Uttarakhand O1 column `name` (Rajasthan: `pcm_id`).
- Regime loops: `REGIMES = (0, 1, 2, 3)` in `pipeline.py` (12 pairs), `scripts/g10_test.py`, `scripts/g12_registry.py`, both plot modules and the hand-off.
- `src/verify/gates.py`: O1 rank-1 PCM per regime, plus a Gate 1 case for regime 3 (cold mains).
- `data/legacy/g2_g4_illustrative_designs.csv` (new): Uttarakhand has no K = 4 legacy deployables, so G2-G4 use one mid design (R 25 mm, 14 capsules,
  0.030 kg/s, staggered) with the O1 rank-1 PCM of each regime. These are illustrative, not O1 or chosen designs.
- `scripts/g14_issue5_controls.py` reads the fraction cap from the design space (30 %) instead of a hard-coded 20 %.
- `src/handoff/build_obj3_contract_v2.py` uses `data/legacy/obj3_environment_contract_template_from_rajasthan.json` as its template (Uttarakhand had no
  legacy v1 contract of the same shape) and overrides state, demand file, delivery target, weather points and years.
- New: `scripts/g7_paired.py` builds `results/g7_sensitivity_paired.csv` (Rajasthan made that file by hand).
- Tests adapted: morning peak at 07:30 (hours 7-8), configured 50 C target in the tau_hold and closure tests, 45 C override for the CFD draw test,
  UKP medoids, 4 regimes, 2024-2025 test years. Result: 84 tests pass after the chain (one test skips until the G8 baseline files exist).

## 3. G2 - time step

`results/g2_timestep_convergence_150_75_37p5.csv`: largest change on any halving 150 -> 75 -> 37.5 s is 0.029 % (criterion 0.05 %), largest
closure residual 0.076 % (criterion 0.1 %). **PASS**; dt 150 s kept.

## 4. G3 - WP1 metrics at the 50 C target

`results/g3_metrics_report.csv` (mid design, single-node): closure residual 0.035-0.071 %. tau_hold and tau_serve are close to zero for both tanks in
regimes 1-3, because the outlet rarely holds 50 C through the night at this design. The PCM peak at the mid design is 65.4-66.3 C, above the 65 C limit;
the limit is a feasibility constraint in the optimisation, so such designs are excluded there.

## 5. G4 - multi-node tank

`results/g4_cfd_draw_case.csv`: 22.5 L at or above 45 C at N = 10, 26.1 L at N = 40, 0 L for the mixed tank (CFD 27 L; run with a 45 C override).
`results/g4_multinode_report.csv`: residual below 1e-11 %; a year takes 0.7-0.9 s at N = 10; N = 10 to 20 adds 0.83-0.99 % useful energy. **PASS**.

## 6. G5 - weather inventory and year roles

40 / 40 point-years accepted, 100 % valid, no gaps. Rajasthan's "test years are the two lowest-GHI years" does not hold here (2023 is the lowest year
in regime 3 and below 2024 in regime 0); the corresponding test was replaced by "test-year mean below the other years in every regime". **PASS**.

## 7. G6 - verification on the O1 PCMs

`results/phase4_verification_o1_pcms.txt`: Gates 1, 2, 3 and 5 PASS, Gate 4 PASS-WITH-CAVEAT (solar fraction below the published benchmark band,
reported, not tuned). Regime 0's plain tank reaches 72.5 C on solar input alone (informational). **GO**.

## 8. G7 - sensitivity

`results/g7_sensitivity_r{0,1,2,3}.csv`: in regimes 0-2 the window gain rises with the PCM fraction; in regime 3 it is flat (PureTemp 53) or falls
(n-Hexacosane, Myristic acid). First sign that PCM may not help in regime 3.

## 9. G8 - screening, DOE, surrogates

- S2: 1,536 designs, 1,452 simulated, 84 geometry-rejected, 0 errors. Best DOE `g_window` per pair (kWh/yr): regime 0 97 / 37 / 87, regime 1 68 / 14 / 59,
  regime 2 59 / 67 / 48, regime 3 5.6 / -5 / -4 (PCM ranks 1 / 2 / 3).
- S3: XGBoost chosen in 11 pairs, quadratic RSM in r0_p2 (`results/g8_s3_selection.csv`).

## 10. G9 - band, active learning, dense grid

- Bands (`results/wp6_band.csv`, regime `g_window`): about 22 / 19 / 20 / 6 kWh for regimes 0-3.
- Active learning + box-vertex step + 3 rounds for all 12 pairs (193 min). Seed spread inside the band in all 12 pairs; dense-grid check within the band
  for all 4 rank-1 pairs (`results/g9_grid_check.csv`). **PASS**.

## 11. G10 - selection and the held-out test

- Selection on 2021-2023 (`results/g10_selection_r*.json`): regimes 0-2 beat the water-only tank beyond the band (PureTemp 58, PureTemp 58, savE OM55,
  at R about 40 mm and fraction 26-30 %); **regime 3 does not** (`meaningful_on_primary_metric: false`); its "chosen" design is the lowest-PCM design the rule picks.
- Held-out test run once on 2024-2025 (`scripts/g10_test.py --confirm-run-once`, run id `heldout_c75ac0e6fb78`): chosen designs 76.0 / 61.8 / 56.4 / -6.1 kWh/yr
  for regimes 0-3; peaks 64.2 C PCM, 73.1 C water. Full table: `docs/04_RESULTS.md` section 2.
- Reporting fixes found while generating the outputs: the fig3 axis clipped regime 3's negative bars (now shows below zero); the phase-4 gate-5 figure
  asked for a flow below the 0.010 floor for regime 0 (now clamped); fig8 reused colours beyond 10 lines.

## 12. G11 and the diagnostics

Ablations (`scripts/g11_ablation.py`) and the diagnostics g13-g17 ran for all four regimes on the chosen designs. g18 (with / without vertex step) was not run.
Results: `docs/04_RESULTS.md` sections 1b, 4, 5b-5e.

## 13. G12 - reporting

`scripts/g12_results_doc.py` was rewritten so that the numbers inside the reading sentences are computed from the files too (Rajasthan's version
had hand-written numbers for its three regimes). Registry, results document, Objective 3 contract v2 and figures regenerated.

## 14. Cleanup to match Rajasthan (2026-10-28, after `git pull` to 768ebb4)

Rajasthan's cleanup (PRs #6 and #7: "update and delete prev pipeline references") was applied here the same way. No result changed:
re-running the chosen designs of regimes 0 and 3 on the select years reproduces the saved `g_window`, `g_annual` and PCM peak to six decimals.

- Settings moved into the configs, as in Rajasthan: the 150 s step is now `solver.timestep_s` in `configs/system_config_shared.yaml`
  (the code override `PRODUCTION_SOLVER_OVERRIDE` is gone), and the geometry-engine bounds are the `geometry_engine` block of
  `configs/design_space.yaml` (`io_utils.load_design_bounds()`), replacing `configs/design_bounds_shared.yaml`.
- Code: Rajasthan's edits to `src/design/`, `src/io_utils.py`, `src/simulation/`, `src/verify/gates.py`, the contract builder,
  `scripts/g7_sensitivity.py` and `tests/test_o1_shortlist.py` applied (retired retargeted-shortlist switch removed).
- Removed (git history only; the earlier sections of this log mention some of them): the legacy K = 5 chain (its results, `docs_objective2/`,
  `configs/design_bounds_shared.yaml`, `configs/cfd_closure_v1.yaml`), the build scripts (`build_input_package.py`, `build_regime_weather.py`,
  `build_demand_profile.py`) and the old root notes, the O1 copies the pipeline does not read and their raw weather, `data/legacy/k5_weather/`,
  the unused legacy modules (`src/doe`, `src/robustness`, `src/surrogate`, old search / selection / plotting code), `tests/test_reproducibility.py`,
  `scripts/sweep_pcm_loading.py`, `scripts/g19_fetch_test2_weather.py`, and the 17 phase figures with their script and cache (Rajasthan keeps only
  `fig1`-`fig9`). The files were moved out of the repository rather than deleted on disk.
- Tests: 81 pass (the removed reproducibility test and the retargeted-shortlist checks account for the difference from 84).
