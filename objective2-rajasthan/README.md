# Objective 2 — Rajasthan

Design optimisation of the PCM storage unit (capsule inner radius, PCM amount via capsule count, flow rate, arrangement) for
Rajasthan's three Objective 1 climate regimes, on a grey-box simulator.

**All documentation is in [`docs/README.md`](docs/README.md)**: model and metrics, weather and design space, the optimisation
pipeline, results, limitations, and the Objective 3 hand-off. `docs/PROGRESS.md` is the step-by-step log with the evidence for every gate.

Current version: v3 (PCM fraction cap 30 %), designs selected on 2021-2023 and tested once on the untouched years 2011-2015.

## Contents

1. [Layout](#layout)
2. [Before you run anything](#before-you-run-anything)
3. [Quick start](#quick-start)
4. [Tests](#tests)
5. [The pipeline, stage by stage](#the-pipeline-stage-by-stage)
6. [Running the deciding stages by hand (parallel)](#running-the-deciding-stages-by-hand-parallel)
7. [Evidence and diagnostic scripts](#evidence-and-diagnostic-scripts)
8. [Reports, hand-off and plots](#reports-hand-off-and-plots)
9. [Quick single-design check](#quick-single-design-check)
10. [OpenFOAM / ParaView (outside this folder)](#openfoam--paraview-outside-this-folder)
11. [Troubleshooting](#troubleshooting)

## Layout

```
objective2-rajasthan/
├── pipeline.py               # entry point for the current chain (stages: status, verify ... plots; see its docstring)
├── run_all_rajasthan.py      # tests + report + handoff + plots from saved results; --full runs the whole chain (hours)
├── config.py                 # shared paths
├── configs/
│   ├── system_config_shared.yaml   # shared system config (tank, collector, safety limits, solver step 150 s)
│   ├── design_space.yaml           # the approved design space (radius, PCM fraction, flow, arrangement) + geometry-engine bounds
│   └── states/rajasthan.yaml       # regimes, weather paths, mains temperature, O1 PCM top-3
├── src/
│   ├── simulation/           # single-node and multi-node tank, capsule enthalpy, collector, heat transfer, run_case
│   ├── metrics/              # thermal-storage metrics (E_del,45, tau_serve, ...)
│   ├── weather/              # point-year inventory, year roles, held-out lock
│   ├── design/               # design space, geometry engine, constraints
│   ├── optimize/             # paired baseline, evaluation, ANOVA, surrogates, NSGA-II
│   ├── handoff/              # Objective 3 environment contract v2
│   ├── plots/                # make_plots_results.py (figures 1-9)
│   └── verify/               # Phase-4 verification battery (gates.py)
├── scripts/g*.py             # one script per gate step (G2-G22)
├── tests/                    # python -m pytest tests
├── data/                     # objective1/ inputs, weather/point_years/, demand/, legacy/ (tables read by g2-g4)
├── results/                  # all outputs; results_registry.csv lists every headline number with its source
└── docs/                     # documentation (start at docs/README.md)
```

## Before you run anything

- **Run every command from this folder** (`objective2-rajasthan/`). The scripts use relative paths (`results/`, `data/`).
- **The held-out test is already spent.** `results/held_out_test.lock` exists. Never run `scripts/g10_test.py` again.
- **Deciding stages overwrite the frozen designs.** These are `baseline`, `screening`, `doe`, `surrogate`, `band`, `optimize` and `select`.
  `pipeline.py` refuses them while the lock exists, unless you pass `--allow-invalidate`. **Calling a script directly bypasses the lock**,
  so back up `results/` first.
- **Safe at any time:** `status`, `report`, `handoff`, `plots`, `simulate`, the tests, and the diagnostic scripts G13–G22. The diagnostic
  scripts read only the explore and select years and write their own files.
- Arguments: `<regime>` = cluster id `0`, `1` or `2`; `<pcm_rank>` = O1 rank `1`, `2` or `3`.
- Command blocks are PowerShell unless they are marked `bash`.

## Quick start

```powershell
python -m pytest tests                              # unit tests
python pipeline.py --state rajasthan --stage status # which outputs exist, and whether the lock is set
python run_all_rajasthan.py                         # tests -> report -> handoff -> plots from saved results (minutes)
```

`run_all_rajasthan.py` options:

| Command | What it does | Time |
|---|---|---|
| `python run_all_rajasthan.py` | tests, then `report`, `handoff`, `plots`, `status` | minutes |
| `python run_all_rajasthan.py --skip-tests` | the same without the tests | minutes |
| `python run_all_rajasthan.py --full --dry-run` | print every command of the full chain, run nothing | seconds |
| `python run_all_rajasthan.py --full --allow-invalidate --jobs 3` | the whole chain from the simulator up (**overwrites the frozen designs**) | many hours |

## Tests

```powershell
python -m pytest tests                       # all
python -m pytest -q tests/test_tes_metrics.py   # one file
```

| Test file | Checks |
|---|---|
| `test_level1_repairs.py` | WP2 Level-1 simulator repairs (PCM mass from geometry, energy closure) |
| `test_multinode_tank.py` | 10-node stratified tank, including the CFD draw case |
| `test_tes_metrics.py` | metric definitions (E_del,45, tau_serve, ...) |
| `test_demand_timing.py` | demand peaks at local 07:00 / 19:00 (UTC fix) |
| `test_weather_roles.py` | explore / select / test year roles and the held-out lock |
| `test_design_space.py` | design-space bounds and geometry |
| `test_flow_dependent_fr.py` | optional flow-dependent collector F_R (off by default) |
| `test_anova.py`, `test_nsga2.py` | ANOVA and NSGA-II helpers |
| `test_o1_shortlist.py` | `configs/states/rajasthan.yaml` agrees with the O1 top-3 CSV |

## The pipeline, stage by stage

General form:

```powershell
python pipeline.py --state rajasthan --stage <stage> [--jobs 3] [--dry-run] [--allow-invalidate]
```

`--dry-run` prints the exact script calls without running them. `--jobs N` runs that many jobs in parallel inside a stage.
Keep N at 3 or below on a normal machine: 9 parallel jobs ran out of memory once.

| # | Stage | Gate | Command | Scripts it runs | Main outputs (`results/`) | Time |
|---|---|---|---|---|---|---|
| 1 | `verify` | G6 | `python pipeline.py --state rajasthan --stage verify` | `g6_phase4_o1.py` | `phase4_verification_o1_pcms.txt` | minutes |
| 2 | `sensitivity` | G7 | `... --stage sensitivity` | `g7_sensitivity.py <regime>` ×3, `g7_flow_baseline_and_packing.py` | `g7_sensitivity_r*.csv`, `g7_sensitivity_paired.csv`, `g7_flow_same_flow_gain.csv`, `g7_plain_flow_baseline.csv`, `g7_max_packing_fraction.csv` | ~1 h |
| 3 | `baseline` 🔒 | G8 | `... --stage baseline --allow-invalidate` | `g8_build_plain_baseline.py <regime>` ×3 | `plain_baseline_*_r*.csv` | ~30 min |
| 4 | `screening` 🔒 | G8 S1 | `... --stage screening --allow-invalidate` | `g8_s1_screening.py <regime> <rank>` ×9 | `g8_s1_r*_p*.csv`, `g8_s1_anova_r*_p*.csv` | ~1 h |
| 5 | `doe` 🔒 | G8 S2 | `... --stage doe --allow-invalidate` | `g8_s2_doe.py <regime> <rank>` ×9, then `g8_s2_repair.py` | `g8_s2_r*_p*.csv` | hours |
| 6 | `surrogate` 🔒 | G8 S3 | `... --stage surrogate --allow-invalidate` | `g8_s3_compare.py` | `g8_s3_comparison.csv`, `g8_s3_selection.csv` | ~30 min |
| 7 | `band` 🔒 | G9 | `... --stage band --allow-invalidate` | `g9_band.py <regime>` ×3 | `wp6_band.csv` | ~30 min |
| 8 | `optimize` 🔒 | G9 S4–S6 | `... --stage optimize --allow-invalidate` | `g9_s4_s5.py` ×9, again with `G9_WARM=1 G9_VERTICES=1` ×9, `g9_s6_grid.py <regime> 1` ×3, `g9_assess.py` | `g9_*_r*_p*.csv`, `*_ext2.csv`, `g9_s6_grid_r*_p1.csv`, `g9_grid_check.csv`, `g9_boundary_check.csv` | many hours |
| 9 | `select` 🔒 | G10 | `... --stage select --allow-invalidate` | `g10_select.py <regime>` ×3 | `g10_selection_r*.json`, `g10_selection_candidates_r*.csv` | ~30 min |
| — | `heldout` ⛔ | G10 S8 | **do not run** (already used; the lock refuses it) | `g10_test.py --confirm-run-once` | `g10_heldout_results.csv`, `held_out_test.lock` | — |
| 10 | `ablation` | G11 | `... --stage ablation` | `g11_ablation.py <regime>` ×3 | `g11_ablation_r*.csv` | ~1 h |
| 11 | `report` | G12 | `... --stage report` | `g12_registry.py`, `g12_results_doc.py`, `g12_verify_docs.py` | `results_registry.csv`, `docs/04_RESULTS.md` | seconds |
| 12 | `handoff` | G12 | `... --stage handoff` | `src.handoff.build_obj3_contract_v2` | `obj3_environment_contract_rajasthan_v2.json` | seconds |
| 13 | `plots` | G12 | `... --stage plots` | `src.plots.make_plots_results` | `plots/fig1…fig9.png` | seconds |

🔒 = a deciding stage, refused while the lock exists unless you pass `--allow-invalidate`. ⛔ = never run again.

Run the whole chain in order (stops at the first failure; never includes `heldout`):

```powershell
python pipeline.py --state rajasthan --stage all --dry-run                       # see the plan first
python pipeline.py --state rajasthan --stage all --allow-invalidate --jobs 3     # overwrites the frozen designs
```

## Running the deciding stages by hand (parallel)

Use this when you want all 9 (regime, PCM) pairs running at once (one core each, so more than 9 buys nothing).
**Back up `results/` first**: these write straight into it and the lock does not protect direct script calls.

```powershell
Copy-Item -Recurse results results_backup_$(Get-Date -Format yyyyMMdd_HHmm)
```

**Step 0: water-only baseline, 3 regimes**
```powershell
foreach ($r in 0,1,2) { Start-Process python -ArgumentList "scripts/g8_build_plain_baseline.py $r" -NoNewWindow -RedirectStandardOutput "results/log_base_r$r.txt" }
```

**Step 1: Taguchi screening (S1), 9 pairs**
```powershell
foreach ($r in 0,1,2) { foreach ($p in 1,2,3) { Start-Process python -ArgumentList "scripts/g8_s1_screening.py $r $p" -NoNewWindow -RedirectStandardOutput "results/log_s1_r${r}_p${p}.txt" } }
```

**Step 2: Sobol DOE (S2), 9 pairs, then the repair pass**
```powershell
foreach ($r in 0,1,2) { foreach ($p in 1,2,3) { Start-Process python -ArgumentList "scripts/g8_s2_doe.py $r $p" -NoNewWindow -RedirectStandardOutput "results/log_s2_r${r}_p${p}.txt" } }
# when all 9 have finished:
python scripts/g8_s2_repair.py
```

**Step 3: surrogate comparison (S3).** It already uses 9 workers, so run it once:
```powershell
python scripts/g8_s3_compare.py
```

**Step 4: repeatability band (WP6), 3 regimes**
```powershell
foreach ($r in 0,1,2) { Start-Process python -ArgumentList "scripts/g9_band.py $r" -NoNewWindow -RedirectStandardOutput "results/log_band_r$r.txt" }
```

**Step 5: NSGA-II + active learning (S4/S5), 9 pairs** (40–80 min)
```powershell
foreach ($r in 0,1,2) { foreach ($p in 1,2,3) { Start-Process python -ArgumentList "scripts/g9_s4_s5.py $r $p" -NoNewWindow -RedirectStandardOutput "results/log_g9_r${r}_p${p}.txt" } }
```

**Step 5b: box-vertex step + 3 more rounds (`_ext2` files).** These continue from Step 5's saved state. With `G9_WARM` set,
the script runs 3 rounds beyond the saved one (`MAX_ROUNDS_EFF = start + 3`), so `G9_MAX_ROUNDS` is not needed here.
```powershell
$env:G9_WARM="1"; $env:G9_VERTICES="1"
foreach ($r in 0,1,2) { foreach ($p in 1,2,3) { Start-Process python -ArgumentList "scripts/g9_s4_s5.py $r $p" -NoNewWindow -RedirectStandardOutput "results/log_g9ext_r${r}_p${p}.txt" } }
Remove-Item Env:G9_WARM, Env:G9_VERTICES      # clear them afterwards
```

**Step 6: dense grid (S6), rank-1 PCM only, 3 regimes**
```powershell
foreach ($r in 0,1,2) { Start-Process python -ArgumentList "scripts/g9_s6_grid.py $r 1" -NoNewWindow -RedirectStandardOutput "results/log_s6_r$r.txt" }
```

**Step 7: G9 assessment, then final selection (G10)**
```powershell
python scripts/g9_assess.py
foreach ($r in 0,1,2) { Start-Process python -ArgumentList "scripts/g10_select.py $r" -NoNewWindow -RedirectStandardOutput "results/log_g10_r$r.txt" }
```

**Step 8: ablations (G11), then report/hand-off/plots**
```powershell
foreach ($r in 0,1,2) { Start-Process python -ArgumentList "scripts/g11_ablation.py $r" -NoNewWindow -RedirectStandardOutput "results/log_g11_r$r.txt" }
python run_all_rajasthan.py --skip-tests
```

**Waiting for a step to finish.** `Start-Process` returns immediately. Wait until no `python` process is left before you start the next step:
```powershell
Get-Process python -ErrorAction SilentlyContinue | Measure-Object | Select-Object Count
Get-Content results/log_g9_r0_p1.txt -Tail 5      # tail any log
```

**`g9_s4_s5.py` environment variables**

| Variable | Effect |
|---|---|
| `G9_FAST=1` | smoke test: tiny budget, writes to `results/_smoke/` (safe) |
| `G9_OUTDIR=<dir>` | write outputs somewhere other than `results/` (saved states are still read from `results/`) |
| `G9_WARM=1` | continue from the saved state |
| `G9_VERTICES=1` | simulate the design-box vertices before the extra rounds |
| `G9_MAX_ROUNDS=<n>` | round limit for a cold start (default 5) |
| `G9_FROM_SUFFIX=_ext` | which saved state to continue from (`""` = original) |

Safe smoke test of the optimiser (about a minute):
```powershell
$env:G9_FAST="1"; python scripts/g9_s4_s5.py 0 1; Remove-Item Env:G9_FAST
```

## Evidence and diagnostic scripts

These are not part of `pipeline.py`. Each one writes its own file in `results/`.

### Simulator evidence (G2–G4)

These use the legacy Phase-7 designs in `data/legacy/` as fixed test inputs. They are illustrative, not O1 designs.

| Gate | Command | What it checks | Output |
|---|---|---|---|
| G2 | `python scripts/g2_timestep_convergence.py` | annual energy change when dt halves (300/150/75 s) | `g2_timestep_convergence.csv` |
| G2 | `python scripts/g2_timestep_convergence.py 150,75,37.5 results/g2_timestep_convergence_150_75_37p5.csv` | same, at a finer set of dt | named file |
| G3 | `python scripts/g3_metrics_report.py` | full metric set + night hold/serve on every day | `g3_metrics_report.csv`, `g3_night_daily_r*_*.csv` |
| G4 | `python scripts/g4_multinode_report.py` | single- vs multi-node runtime; CFD stratified-draw case | `g4_multinode_report.csv`, `g4_cfd_draw_case.csv` |

### Issue diagnostics around the frozen designs (G13–G18)

Run per regime (`0 1 2`). All read explore/select years only.

```powershell
foreach ($r in 0,1,2) { python scripts/g13_issue4_shield_split.py $r }   # water vs PCM shield hours      -> g13_shield_split_r*.csv
foreach ($r in 0,1,2) { python scripts/g14_issue5_controls.py $r }       # thickness/fraction controls    -> g14_controls_r*.csv
foreach ($r in 0,1,2) { python scripts/g15_issue6_anchor.py $r }         # stack at bottom/centre/top     -> g15_anchor_r*.csv
foreach ($r in 0,1,2) { python scripts/g16_issue3_serve.py $r }          # night-serve, latent-off, 40 L  -> g16_serve_r*.csv
foreach ($r in 0,1,2) { python scripts/g17_issue2_widen.py $r }          # widened-bound diagnostic       -> g17_widen_r*.csv
python scripts/g18_issue1_compare.py                                     # with/without box-vertex step   -> g18_issue1_with_without.csv
```

Re-run a single G16 case only (the output file gets the case name appended):
```powershell
$env:G16_ONLY="plain_40L"; python scripts/g16_issue3_serve.py 0; Remove-Item Env:G16_ONLY
```

G18 reads a "no-vertex" run from `results/issue1_novert/`. To regenerate that run (9 pairs, one core each):
```powershell
$env:G9_WARM="1"; $env:G9_MAX_ROUNDS="8"; $env:G9_OUTDIR="results/issue1_novert"
foreach ($r in 0,1,2) { foreach ($p in 1,2,3) { Start-Process python -ArgumentList "scripts/g9_s4_s5.py $r $p" -NoNewWindow -RedirectStandardOutput "results/issue1_novert/log_r${r}_p${p}.txt" } }
Remove-Item Env:G9_WARM, Env:G9_MAX_ROUNDS, Env:G9_OUTDIR
```

### Weather, comparisons and supplementary studies (G19–G22)

G20–G22 have no saved outputs in `results/` yet, so these are the first runs.

| Gate | Command | Purpose | Output |
|---|---|---|---|
| G19 | `python scripts/g19_fetch_test2_weather.py` | download NASA POWER 2011–2015 for the 3 medoid points (internet needed; already done) | `data/weather/raw_test_2011_2015/*.json` |
| G20 | `python scripts/g20_gp_bo_comparison.py <regime> [pcm_rank=1] [n_init=20] [n_iter=40] [seed=20261028]` | GP Bayesian optimisation, a comparison against NSGA-II | `g20_gpbo_r<c>_p<rank>.csv` |
| G21 | `python scripts/g21_sizing_study.py <regime>` | supplementary tank-size sensitivity (50–150 L, IS 12976) | `g21_sizing_r<c>.csv` |
| G22 | `python scripts/g22_sensitivity_extra.py <regime>` | mains, demand, shield-off, convection factor, μ/β, ρ, Cp sensitivities | `g22_sensitivity_r<c>.csv` |

All three regimes at once:
```powershell
foreach ($r in 0,1,2) { python scripts/g20_gp_bo_comparison.py $r }
foreach ($r in 0,1,2) { python scripts/g21_sizing_study.py $r }
foreach ($r in 0,1,2) { python scripts/g22_sensitivity_extra.py $r }
```

## Reports, hand-off and plots

All of these only read saved files in `results/`, so they are always safe.

```powershell
# results registry -> generated results doc -> check that every file/function the docs name exists
python scripts/g12_registry.py
python scripts/g12_results_doc.py          # rewrites docs/04_RESULTS.md (run g12_registry.py first)
python scripts/g12_verify_docs.py          # exits 1 and lists misses if a doc names a missing file

# Objective 3 environment contract
$env:PYTHONPATH="."; python -m src.handoff.build_obj3_contract_v2; Remove-Item Env:PYTHONPATH

# all figures
python -m src.plots.make_plots_results
```

Or the same through the pipeline:
```powershell
python pipeline.py --state rajasthan --stage report
python pipeline.py --state rajasthan --stage handoff
python pipeline.py --state rajasthan --stage plots
```

**Figures** (written to `results/plots/`; details in [`docs/plots/10_PLOTS.md`](docs/plots/10_PLOTS.md)):

| File | Shows |
|---|---|
| `fig1_front_vs_grid.png` | optimiser points vs the dense grid, chosen design starred (rank-1 PCM) |
| `fig2_g9_grid_check.png` | G9 epsilon gap as a share of the band, 9 pairs |
| `fig3_gain_by_year_role.png` | chosen design's g_window on explore / select / held-out years |
| `fig4_heldout_pcm_comparison.png` | held-out g_window of the chosen vs the other O1 PCMs |
| `fig5_heldout_nulls_and_costs.png` | night-serve gain, extra shield hours, PCM peak |
| `fig6_ablations.png` | G11 changes in g_window vs the band |
| `fig7_surrogate_comparison.png` | G8 surrogate families by rank agreement |
| `fig8_fraction_response.png` | gain vs PCM fraction |
| `fig9_boundary_share.png` | fronts sitting at a bound of the design box |

## Quick single-design check

Simulates one design on the explore (or select) years, paired against the same-flow water-only tank. It writes no files.

```powershell
python pipeline.py --state rajasthan --stage simulate --cluster 0 --pcm-rank 1 --radius-mm 40 --fraction 0.2 --flow 0.025 --arrangement staggered
python pipeline.py --state rajasthan --stage simulate --cluster 2 --pcm-rank 2 --radius-mm 25 --fraction 0.1 --flow 0.03 --arrangement radial --purpose select
```

| Option | Values (default) |
|---|---|
| `--cluster` | 0, 1, 2 (0) |
| `--pcm-rank` | 1, 2, 3 (1) |
| `--radius-mm` | inner radius in mm (40) |
| `--fraction` | outer PCM volume fraction (0.20) |
| `--flow` | kg/s (0.025) |
| `--arrangement` | `single-layer`, `staggered`, `radial` (staggered) |
| `--purpose` | `explore`, `select` (explore); held-out years are not reachable |

## OpenFOAM / ParaView (outside this folder)

The CFD cases live in `../openfoam_cfd/` and run in WSL (Ubuntu-24.04, OpenFOAM v2406). The Rajasthan simulator does **not** read
any CFD result yet: it still uses the lumped `r/(5k)` closure with `liquid_convection_enhancement: 2.0`. Full notes are in
[`commands to run.md`](commands%20to%20run.md).

```bash
# bash (WSL), set once
OF="/mnt/d/Final Year Project/OBJECTIVE2/Objective---2/openfoam_cfd"
PV="/mnt/d/Program Files/ParaView 6.2.0/bin"

# view saved cases (then press Play)
"$PV/paraview.exe" --state="$(wslpath -w "$OF/cases_viz/rt44_d060/rt44_d060_T.pvsm")" &              # capsule melting
"$PV/paraview.exe" --state="$(wslpath -w "$OF/cases_tank/charge/charge_T.pvsm")" &                    # tank charge
"$PV/paraview.exe" --state="$(wslpath -w "$OF/cases_tank/draw/draw_T.pvsm")" &                        # tank draw
"$PV/paraview.exe" --state="$(wslpath -w "$OF/cases_collector/test_T30/collector_T.pvsm")" &          # collector riser

# pictures without the GUI (overwrites the PNGs in that case folder)
cd "$OF/scripts" && python.exe plot_capsule_fields.py ../cases_viz/rt44_d060 --times 0 300 600 900 1200 1800 2400

# a new animatable capsule case
cd "$OF/scripts"
python.exe viz_case.py --name om49_d055 --pcm "savE® OM49" --d 0.055 --mdot 0.03 --dT 15 --t-end-h 1.5
"$PV/pvbatch.exe" make_pv_state.py tank "..\\cases_viz\\om49_d055\\om49_d055.foam" "..\\cases_viz\\om49_d055\\om49_d055.pvsm" 300 335
"$PV/paraview.exe" --state="$(wslpath -w "$OF/cases_viz/om49_d055/om49_d055.pvsm")" &
```

## Troubleshooting

| Problem | Fix |
|---|---|
| `refusing [...]: results/held_out_test.lock exists` | Expected for the deciding stages. Use `--allow-invalidate` only if you mean to re-decide the designs. |
| `ModuleNotFoundError: src` | Run from this folder; for `-m src.handoff...` set `$env:PYTHONPATH="."`. |
| Out of memory with many jobs | Lower `--jobs` (3 is safe) or launch fewer `Start-Process` jobs at once. |
| A `G9_*` variable leaks into a later run | `Remove-Item Env:G9_WARM, Env:G9_VERTICES, Env:G9_MAX_ROUNDS, Env:G9_OUTDIR -ErrorAction SilentlyContinue` |
| `g12_verify_docs.py` exits 1 | A doc names a file or function that does not exist; fix the doc (or the name) it prints. |
| ParaView opens blank | Press **Reset Camera**, then **Play**. |
| Windows line endings in a `.sh` file | `sed -i 's/\r$//' run_one.sh` (in WSL). |
