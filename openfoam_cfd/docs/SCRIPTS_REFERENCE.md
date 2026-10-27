# Scripts reference

All scripts live in `openfoam_cfd/scripts/`. Windows Python 3.10 unless stated; OpenFOAM runs in WSL
(`Ubuntu-24.04`, OpenFOAM v2406). Run Windows commands from a **PowerShell** window; `$b` below is
`/mnt/d/Final Year Project/OBJECTIVE2/Objective---2/openfoam_cfd`.

`_paths.py` finds the project (`objective2-rajasthan`) whether `openfoam_cfd/` sits inside it or next to it
(override with `O2_PROJECT_ROOT`).

## Capsule CFD (tier T2)

| Script | Purpose | Example |
|---|---|---|
| `make_case.py` | writes one axisymmetric capsule case (mesh, BCs, melting source, numerics); `--viz` keeps all times; `bc_mode=isothermal` for benchmarks | `python make_case.py --out ..\cases\x --pcm RT44HC --d 0.06 --mdot 0.03 --dT 15 --t-end-h 3` |
| `run_one.sh` | runs one case in WSL on the Linux disk, early-stops at full melt, copies results back (atomic `controlDict` edit) | `wsl -d Ubuntu-24.04 -e bash "$b/scripts/run_one.sh" "$b/cases/x"` |
| `postprocess.py` | KPIs (t50/t90/t99, energy at window, energy-balance QC) and comparison with the grey-box (φ) | `python postprocess.py ..\cases\x --window-h 6` |
| `run_doe.py` | LHS DOE / mesh / sensitivity / conduction twins, parallel via WSL, retry on transient launch failures; `--tag`, `--cell-size` | `python run_doe.py --mode all --workers 8` |
| `cfd_calibrated_greybox.py` | fits φ(d, ṁ, ΔT, props), re-runs the project's Phase-5 designs (frozen vs calibrated, paired), ExtraTrees search + confirmation | `python cfd_calibrated_greybox.py --workers 8` |
| `validate_sphere.py` + `../validation/benchmark_template.yaml` | reproduce a published sphere-melting experiment; refuses to run with unfilled values | `python validate_sphere.py ..\validation\x.yaml --calibrate-cu` |
| `_extra_mesh.py`, `_run_pending.py` | one-off drivers used for the 0.6 mm / Courant checks and the batch chain | – |

## Packed-bed solver (tier T2b)

| Script | Purpose | Example |
|---|---|---|
| `install_pht_solver.sh` | clone and build `porousHeatTransferFoam` against v2406 (CC BY-NC) | `wsl -d Ubuntu-24.04 -e bash "$b/scripts/install_pht_solver.sh"` |
| `pht_make_case.py` (runs in WSL) | `nallusamy` (paper §4.3 water case) and `rajasthan` (1-D bed in the 50 L tank, optional time-varying inlet) | called by the runner |
| `pht_run_case.sh` | generate → blockMesh → solve → summarise one bed case | `wsl ... bash "$b/scripts/pht_run_case.sh" name rajasthan --pcm RT44HC --d 0.06 --n 30 --mdot 0.03 --dT 15 --phi 0.47` |
| `pht_postprocess.py` | probe times, `summary.json`, `hourly_bed.csv` | – |
| `pht_vs_greybox.py` | drives the bed with the grey-box's hourly temperatures (V1, V2, V3) for the 3 regimes and compares | `python pht_vs_greybox.py --dt 5` |
| `plot_pht_vs_greybox.py` | figure of the comparison | `python plot_pht_vs_greybox.py` |

## Tank and collector

| Script | Purpose | Example |
|---|---|---|
| `tank_make_case.py` | 50 L axisymmetric tank; modes `idle`, `charge`, `draw` | `python tank_make_case.py --out ..\cases_tank\charge --mode charge --mdot 0.03 --T-in 60 --T-init 25 --t-end-s 3600 --write-every 120 --dz 0.005 --viz` |
| `tank_run.sh` | blockMesh, setFields, checkMesh, solve, copy back (≈ 75 min per simulated hour at 0.03 kg/s) | `wsl ... bash "$b/scripts/tank_run.sh" "$b/cases_tank/charge"` |
| `tank_postprocess.py` | MIX number, thermocline thickness, delivered volume, `tank_profiles.png` | `python tank_postprocess.py ..\cases_tank\charge` |
| `collector_make_case.py` | one riser strip (copper + water), conjugate heat transfer, with the textbook estimate stored in `case_meta.json` | `python collector_make_case.py --out ..\cases_collector\x --T-in 50 --mdot-loop 0.03` |
| `collector_run.sh` | blockMesh, splitMeshRegions, `chtMultiRegionFoam` (~ 2.5 min). **Never run two jobs on the same case folder** | `wsl ... bash "$b/scripts/collector_run.sh" "$b/cases_collector/x"` |
| `collector_postprocess.py` | outlet T, gain, efficiency, F_R vs textbook | `python collector_postprocess.py ..\cases_collector\x` |
| `collector_sweep.py` | 5 inlet temperatures + 2 flows, line fit | `python collector_sweep.py --workers 3` |

## Visualisation

| Script | Purpose |
|---|---|
| `viz_case.py` / `viz_run.sh` | run one capsule case keeping every 30 s, in `cases_viz/<name>/` |
| `plot_capsule_fields.py` | quick-look PNGs of liquid fraction and T (matplotlib, no ParaView) |
| `capsule_paraview.py` | ParaView script for a capsule case (pvbatch images or GUI) |
| `capsule_movie.py` | frames + GIF of a capsule case (pvbatch). Written, **not run** |
| `component_paraview.py` | tank / collector images (pvbatch) |
| `make_pv_state.py` | builds a ready-to-play `.pvsm` ParaView state file |

## Results files (in `../results/`)

`cfd_doe_results.csv` (1.2 mm DOE), `cfd_doe_results_fine.csv` (0.8 mm), `cfd_doe_results_pilot8.csv`,
`cfd_conduction_results.csv`, `cfd_convection_gain.csv`, `cfd_mesh_results.csv`, `cfd_mesh_extra_results.csv`,
`cfd_sens_results.csv`, `o2_cfd_paired_annual.csv`, `o2_cfd_paired_summary.csv/.md`,
`o2_cfd_calibrated_recommendation.csv` (+ `_pilot8` copies), `pht_vs_greybox.csv/.png/_context.json`,
`collector_cfd_sweep.csv`, `collector_cfd_fit.json`, `_selftest_plumbing.*` (code check only).
