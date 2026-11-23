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

## 15. OpenFOAM cases for Uttarakhand (2026-10-28)

New folder `openfoam_cfd/` (inside `objective2-uttarakhand/`): the project's shared OpenFOAM set-up (`../openfoam_cfd/`) adapted to
Uttarakhand. `scripts/make_uttarakhand_cases.py` writes 26 cases from the saved results (`results/g10_selection_r*.json`,
`results/g10_heldout_results.csv`, the state yaml): per regime the chosen capsule (KPI case and a ParaView animation case), for
regimes 0-2 a conduction-only twin and the runner-up PCM, and the 50 L tank (charge, draw, idle) at the regime's mains temperature,
judged at 50 C. Script changes against the shared copies: Uttarakhand project and PCM database, regime mains temperature in the tank
draw case (shared: fixed 25 C), 50 C target in the tank metrics, 12 K capsule drive (shared quick-start 15 K would exceed the 72 C
shield for PureTemp 58), configurable WSL distribution, LF line endings for the bash scripts. **Not run:** OpenFOAM and ParaView
are not installed on this machine; `scripts/run_all_cases.ps1` runs everything where they are.

## 2026-11-10 - Corrections applied (documentation and comments only)

- Applied the O1/O2 corrected-methodology note to the Uttarakhand O2 documents. Nothing was re-run; no result file and not `results/held_out_test.lock` was changed.
- Code: `src/weather/roles.py` module docstring no longer says the held-out years are untouched; it records run id `heldout_c75ac0e6fb78`, UTC 2026-10-28T13:18:41. Tests: 81 passed.
- Docs: `docs/README.md` (corrections section), `docs/02_WEATHER_AND_DESIGN_SPACE.md` and `docs/06_OBJECTIVE3_HANDOFF.md` (K = 4 inheritance, 50 L / 1.5 m2 / 50 C), `docs/05_LIMITATIONS_AND_OPEN_ITEMS.md` (open items), `README.md`.
- Held-out evidence re-read: 24 rows; regimes 0-2 `g_window` > 0; regime 3 all designs negative.

## 2026-11-11 - Objective 3 readiness (O3 plan check)

- Checked the consolidated O3 plan (2026-11-10) against this folder; findings and status in `docs/06_OBJECTIVE3_HANDOFF.md` (last section).
- Ported from `objective2-rajasthan`, unchanged except the state name: the conduction coefficient c of R_pcm (`src/simulation/heat_transfer.py`,
  `tank_model_multinode.py`), the named capsule closure (`src/simulation/cfd_closure.py`, `configs/cfd_closure_v1.yaml`, Rajasthan's unvalidated fit),
  the flow-dependent collector F_R (`src/simulation/collector_model.py`, `run_case.py`, disabled block in `configs/system_config_shared.yaml`), and their
  tests (`test_capsule_closure_option.py`, `test_cfd_closure.py`, `test_flow_dependent_fr.py`).
- All options are off by default. Regime 0 and regime 3 designs over the five explore years give bit-identical g_window, g_annual, d_overheat and PCM peak
  before and after. Tests: 95 passed. Nothing was re-run; no result file except the contract changed; `results/held_out_test.lock` untouched.
- Contract regenerated (`--stage handoff`): only the `system_config_shared.yaml` SHA-256 changed.

## 2026-11-12 - Objective 3 contract in the v3 schema (port of Rajasthan commit `ca23d0c`)

- New `src/handoff/build_obj3_contract_uttarakhand_v3.py` (port of `objective2-rajasthan/src/handoff/build_obj3_contract_rajasthan_v3.py`) writes
  `results/obj3_environment_contract_uttarakhand_v3.json`: the v2 contract re-expressed in the Tamil Nadu v3 schema the O3 code reads. Restructure only,
  no value changed; 33 copied fields checked against their sources. Uttarakhand-specific: four regimes, 50 C delivery target, held-out 2024-2025,
  regime 3 marked `degenerate_regime`, no B1 claim (not run for Uttarakhand). (Corrected 2026-11-13: the OpenFOAM note now says 1 of 10 capsule
  cases was run, `r0_chosen_puretemp_58`; it first said none.)
- `pipeline.py --stage handoff` runs v2 then v3. `scripts/g12_verify_docs.py`: Rajasthan's fix ported (a reference like `file.yaml:24,38` is checked
  as the file). Nothing was re-run; `results/held_out_test.lock` untouched.

## 2026-11-12 - K = 4 confirmed final

- The student confirmed that Objective 1 has been changed to K = 4 regimes for Uttarakhand and that the project continues with K = 4 (no K = 5).
  Open decision (a) is closed. Updated: `README.md`, `docs/README.md`, `docs/02_WEATHER_AND_DESIGN_SPACE.md`, `docs/05_LIMITATIONS_AND_OPEN_ITEMS.md`,
  `docs/06_OBJECTIVE3_HANDOFF.md`. Documentation only; no result, contract or code changed.

## 2026-11-12 - 50 C delivery basis confirmed final

- The student confirmed 50 C as the Uttarakhand delivery basis (O1 and O2 already both use it). Open decision (b), the 60 C O1 basis, is closed:
  the shortlisted PCMs melt at about 53-58 C and the PCM limit is 65 C (shield bypass 62 C). Updated `docs/05_LIMITATIONS_AND_OPEN_ITEMS.md` and
  `docs/README.md`. Documentation only; no result, contract or code changed.

## 2026-11-13 - All figures in one run (port of Rajasthan commit `7f2f701`)

- New `make_all_plots.py` (port of `objective2-rajasthan/make_all_plots.py`): `python make_all_plots.py` draws fig1-fig9 (from
  `src/plots/make_plots_results.py`) and fig10-fig50 into `results/plots/`, reading saved files only (nothing simulated, held-out loader not called).
  Adapted to four regimes, the 50 C target, held-out 2024-2025 and the UKP weather points; no claim in a figure title is typed by hand.
- Result: 30 figures written, 9 skipped because their study was not run for Uttarakhand (fig28 g21 sizing, fig29 g22 input sensitivity, fig30 g24
  flow F_R, fig31 g20 GP-BO, fig32 g18 search variants, fig33 B1 widened box, fig35 g23 Chen benchmark, fig41/fig42 OpenFOAM closure and mesh studies).
  fig21 shows the v3 box only (no B1); fig26 has no 40 L water-only case; fig40 is Uttarakhand's own OpenFOAM figure (the one capsule case run).
- Contract v3 regenerated: its OpenFOAM note now says 1 of 10 capsule cases was run (it said none). No design value changed.

## 2026-11-13 - OpenFOAM: Rajasthan's findings applied to Uttarakhand (documentation only)

- Compared `openfoam_cfd/` with `../objective2-rajasthan/rj_openfoam/` and its `docs/07_OPENFOAM_VALIDATION.md`. Same solver set-up and assumed liquid
  properties, so Rajasthan's results carry over: the set-up does not reproduce Tan 2009 or Dong 2022 (melts 1.6-2 x faster) and is not mesh-converged.
- `openfoam_cfd/README.md` section 4: CFD numbers are an unvalidated upper bound; the one run case (grey-box t90 2.05 x CFD) does not change the
  simulator (c = 5, F = 2 kept, `cfd_closure_v1` off); not comparable with Rajasthan's fixed-wall ratios. Rajasthan's colon-filename generator bug,
  CRLF and space-in-path problems do not affect this folder (checked). `docs/README.md`: OpenFOAM status stated (1 of 10 capsule cases run).
- No code, case or result changed.

## 2026-11-22 - Common-plant rebuild, L0 (decide and freeze)

- The student adopted the Unified O2+O3 Rebuild Plan (Revision 13): 100 L / 2.0 m2 / 100 L/day, 45 C primary + 50 C secondary,
  flow 0.030 kg/s, PCM fraction 2-40 %, robust stack anchor, 2006-2010 one-shot test. Student choices: inner radius kept at 10-40 mm,
  legacy results archived, commit per level. Decision record and level tracker: `docs/REBUILD_COMMON100L.md`.
- `results/` moved to `results_legacy_50L_v3/` (233 files, the spent lock included); a fresh `results/` holds the rebuild.
- Legacy supplementary studies g20-g24 (finished 2026-11-14/15, all 20 jobs exit 0) archived with the rest; `make_all_plots.py` now
  draws fig28-fig31 and fig35 for real (they were stubs that only checked the input file), so the legacy set has 36 figures
  (`results_legacy_50L_v3/plots/`; fig32, fig33, fig41, fig42 need studies never run). `scripts/g18_issue1_compare.py`: the
  Rajasthan-only r0_p1 special case removed (it pointed at a file Uttarakhand never had).

## 2026-11-22 - Rebuild L1 (O1 alignment, Option B)

- `scripts/r1_o1_manifest.py --copy` copied Objective 1's `cluster_assignments_uttarakhand.csv` (O1 project, `K_FINAL = 4`) into
  `data/objective1/` after checking it belongs to the same O1 run as the profiles already here (values agree to 3.6e-15; the only
  differences are float noise and two columns the O2 port added; elevations identical).
- `results/o1_manifest_uttarakhand.json`: per regime the medoid, member point ids, population, shortlist (checked equal to the state
  yaml and to `mcdm_topk_by_cluster.csv`), Tm target and mains estimate, plus SHA-256 of the five O1 files. Regimes: 10 / 23 / 9 / 3
  points; medoids UKP_0014 / UKP_0029 / UKP_0025 / UKP_0041, each a member of its own regime. Shortlists unchanged (Option B).

## 2026-11-22 - Rebuild L2 (config, weather, year roles, locks, hashes; gate G0)

- Plant: `configs/system_config_shared.yaml` tank 100 L, collector 2.0 m2 (area basis still open), delivery 45 C primary with
  `secondary_report_temp_C: 50`; demand 100 L/day (`configs/states/uttarakhand.yaml`, profile rescaled, 300 L/day file in `data/legacy/`).
- Design space: fraction cap 40 %, flow fixed 0.030 kg/s in the search, `robust_anchors: [bottom, center, top]`, `report_timestep_s: 37.5`,
  capsule-count bound 10000. `src/io_utils.load_design_bounds` now takes the validity flow range from the pump (0.010-0.050).
- Year roles (`src/weather/roles.py`, plan R3): 2016-2019 explore, 2020-2021 select, 2022-2025 report-only (need the O2 test lock),
  2006-2010 test; lock `results/locks/o2_test_<plant hash>.lock`, never the archived legacy lock.
- 2006-2010 weather fetched and inventoried (60 point-years, all accepted). Weather-only audit: the test years are sunnier than
  2016-2025 (real cloud/aerosol difference, not a data defect; split kept). Details: `docs/REBUILD_COMMON100L.md` section 3b.
- Tests updated to the rebuild (roles, locks, 40 % cap, pump range, 2.0 m2 in the F_R hand calculation, the 50 L CFD draw case pinned
  to 50 L): 94 passed, 5 skipped.

## 2026-11-22 - Rebuild L3 (simulator verification, gate G1)

- `scripts/r3_verification.py` (4 regimes): energy closure, time-step halving 150 -> 18.75 s, 10 vs 20 nodes, IS 12976 standing loss.
  Search at 150 s, confirm/report at 37.5 s. Node effect 2.4-2.6 % on useful energy (large band term). Standing loss passes at 20 C;
  regime 3 at its coldest hour (-18.3 C held 16 h) loses 9.4 K (> 8 K), reported. Outputs `results/l3_timestep.csv`,
  `l3_nodes.csv`, `l3_standing_loss.csv`.
- `scripts/r3_probe_pcm_gain.py` (exploratory, 2018): on the common plant no PCM design beats the water-only tank (best +4.2 kWh/yr,
  regime 3); PCM gains in regime 1 only at 150-300 L/day. Details: `docs/REBUILD_COMMON100L.md` section 3c. Decision on how to
  continue (L4-L9) pending with the student.

## 2026-11-23 - Rebuild L4-L5 (baseline, screening, DOE) and the search code

- Code for L4-L9 on the rebuild box: `src/design/box.py` (box, fidelities, robust anchors, hygiene), exact fixed-flow baseline
  (`src/optimize/baseline.py`), `evaluate_design` with fidelity and robust anchors, surrogates + gp_ard + stacked, stage scripts
  g8/g9/g10 ported (3-D box, vertices from the start, 720-run grid, rebuild band recipe, funnel with the R7 rule and a water-only
  verdict, one-shot 2006-2010 test with worker processes that can only join the locked run). Protocols frozen before the runs:
  `docs/REBUILD_COMMON100L.md` sections 3d, 3e and 5. `scripts/run_jobs.py` runs at most 3 jobs.
- Results: baseline 4 regimes; L9 12 pairs; DOE 12 pairs (1,392 designs). No design beats the water-only tank meaningfully
  (best +1.7 kWh/yr). Section 3f. Tests: 31 design-space tests and 16 role/lock tests pass.

## 2026-11-23 - Rebuild L5-L7 and the selection funnel

- Surrogates (5 families), NSGA-II + active learning (12 pairs), 720-run dense grid and the rebuild band (4 regimes), assessment,
  selection on 2020-2021 at full fidelity. First search launch crashed in all 12 pairs (variable name clash F0 in g9_s4_s5.py after
  the vertex step, no result written); fixed (box bounds renamed RMIN/RMAX/FMIN/FMAX), smoke-tested and re-run; the other jobs were
  unaffected. Grid and seed checks pass; cheap-vs-full Spearman 0.88-0.98.
- Selection: water-only recommended in all four regimes (no worst-anchor gain above the band). Details `docs/REBUILD_COMMON100L.md` 3g.
- The one-shot 2006-2010 test was started after this commit.

## 2026-11-23 - Rebuild L9: one-shot 2006-2010 test, report-only years, Objective 3 contract (Objective 2 rebuild complete)

- One-shot test run `o2test_b04c9c047f2f` (lock `results/locks/o2_test_ad1135145a63.lock`): 12 frozen designs, 2006-2010, 37.5 s, three
  anchors. Water-only confirmed in all four regimes (every gain inside the band; zero hard-limit violations). Report-only 2022-2025 agree.
- Correction to the previous entry: it says the test was started after the selection commit; it was launched at 15:15, about one minute
  before that commit was pushed. The selection files were already final (15:14) and their fingerprints were verified by the test.
- Released `results/obj3_environment_contract_uttarakhand_common100L.json` and `docs/07_OBJECTIVE3_HANDOFF_COMMON100L.md`.
  Figures `results/plots_common100L/`. Details `docs/REBUILD_COMMON100L.md` section 3h.

## 2026-11-23 - Rebuild: M1 MATLAB checkpoint and the post-result items of the plan

- M1 (`scripts/m1_export.py` + `matlab/m1_checkpoint.m`, MATLAB R2026b, trial licence): gate PASS (16 runs, numbers match to 4.9e-14,
  closure <= 5e-11 %, ranking identical). `src/simulation/run_case.py` now also returns `E_stored_initial_kWh` (additive; no number changed).
- `scripts/r10_supplementary.py`: one-at-a-time sensitivity (collector, F_R(flow), manufacturing, cold mains, low sun), auxiliary-heater
  scenario, bound diagnostic below 2 %, plant cases 70 / 150 L/day, legacy 2.5 m2 / 300 L/day, 150 L tank. Nothing changes the
  water-only result; PCM pays only when the daily draw exceeds the tank volume. Details `docs/REBUILD_COMMON100L.md` section 3i.
- `pipeline.py` and `run_all_uttarakhand.py` rewritten for the rebuild chain; `docs/README.md` separates rebuild and legacy documents;
  `scripts/r11_output_manifest.py` hashes every output (plan R20).

## 2026-11-23 - Back to the 50 L pipeline (student decision); the rebuild is kept on a branch

- The student chose to continue with the earlier 50 L / 1.5 m2 / 300 L/day pipeline (PCM in regimes 0-2), after seeing that the
  common-plant rebuild gives water-only at 100 L/day and PCM in regimes 0 and 2 only at 150-200 L/day.
- The complete rebuild (L0-L9, M1, supplementary studies, demand diagnostics) is preserved on branch `uttarakhand-o2-common100L`
  (commit dc3d3d0). On `main` the Uttarakhand folder was restored to the last 50 L state (commit f3000aa), plus the later 50 L work:
  the g20-g24 study outputs and their figures (36 figures in `results/plots/`), `make_all_plots.py` with real fig28-fig35, the g18
  fix and the g20-g24 scripts. 243 result files are byte-identical to the archive; 25 added. Tests: 95 passed.
- Objective 3 uses `results/obj3_environment_contract_uttarakhand_v3.json`. Note for the report: the unified plan's common plant and
  its findings (`docs/REBUILD_COMMON100L.md` on the branch) can be cited as a sensitivity: PCM pays only when the daily draw exceeds the
  tank volume.
