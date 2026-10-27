# Objective 2 (Rajasthan) — OpenFOAM capsule CFD + AI optimisation

> **Current status and file map: `docs/00_INDEX.md`.** Scripts: `docs/SCRIPTS_REFERENCE.md`; visualisation: `docs/VISUALISATION.md`; history: `docs/CHANGELOG.md`.


This folder adds a **CFD tier** to the existing Objective-2 pipeline
(`../src`, Python grey-box → DOE → ExtraTrees → search). It does **not**
replace the grey-box and it does **not** edit any frozen config. It answers the
one question the project's own documents say was never validated:

> *The grey-box models heat flow inside a PCM capsule with a lumped
> `R_pcm = r/(5k)` and a `×2` "liquid-convection enhancement"
> (`configs/system_config_shared.yaml`, `heat_transfer.py` docstring:
> "ASSUMED … no CFD/experimental validation performed"). Is that right, and does
> fixing it change the Objective-2 design?*

OpenFOAM resolves the melting and the natural convection of **one capsule**;
the results calibrate the grey-box; the project's annual simulator and an
ExtraTrees surrogate then re-run the optimisation of the four O2 variables.

| O2 variable | Where it is handled |
|---|---|
| PCM thickness (= capsule diameter / 2) | **CFD-resolved** (DOE variable `d`, 40–80 mm) |
| Flow rate | CFD via the water-side `h_w` (Wakao–Kaguei at that flow); system level via pump power |
| Capsule count | System level (grey-box / optimiser). CFD gives per-capsule energy |
| Arrangement | System level (packing void fraction → Ergun pressure drop) — see "What this does **not** do" |

---

## 0. What you need (already done on your machine)

* WSL2 + **Ubuntu-24.04** (distro name must match `DISTRO` in `scripts/run_doe.py`)
* OpenFOAM **v2406** at `/usr/lib/openfoam/openfoam2406`
* Windows Python 3.10 with `numpy scipy pandas scikit-learn pyyaml` (the
  project's venv already has them)

Check:

```powershell
wsl -d Ubuntu-24.04 -e bash -lc "source /usr/lib/openfoam/openfoam2406/etc/bashrc; foamVersion; which buoyantPimpleFoam"
python -c "import numpy,scipy,pandas,sklearn,yaml; print('python deps ok')"
```

## 1. Folder map

```
openfoam_cfd/
├─ README.md                      <- this file
├─ config/o2_cfd_config.yaml      <- ONE place for every CFD input (each tagged FROZEN / O1-DB / CORR / ASSUMED)
├─ scripts/
│  ├─ make_case.py                <- writes a complete OpenFOAM case (mesh, BCs, fvOptions, numerics)
│  ├─ run_one.sh                  <- runs ONE case in WSL on the fast disk, early-stops, copies results back
│  ├─ run_doe.py                  <- LHS DOE / mesh study / sensitivity / conduction twins, parallel
│  ├─ postprocess.py              <- KPIs + energy-balance QC + comparison with the grey-box
│  └─ cfd_calibrated_greybox.py   <- calibrate grey-box, re-run O2 optimisation, AI recommendation
├─ cases/                         <- generated OpenFOAM cases (open any in ParaView)
└─ results/                       <- CSV/MD outputs
```

## 2. What one case models

One PCM-filled aluminium sphere, **axisymmetric 5° wedge**, axis vertical.
Tank water is a boundary condition (not meshed):

`q″ = (T_inner − T_water) / (1/h_w + t_Al/k_Al)`  with `h_w` from the same
Wakao–Kaguei correlation as `src/simulation/heat_transfer.py` at the design flow
rate and tank cross-section, and `t_Al = 0.8 mm`, `k_Al = 205 W/mK` (frozen).

Solver `buoyantPimpleFoam`, Boussinesq buoyancy, Voller–Prakash enthalpy–porosity
via the `solidificationMeltingSource` fvOption. Natural convection in the melt
is **solved**, not multiplied in.

Mesh: butterfly (core square + three arc blocks), ≈ 1.2 mm cells, 250–1500 cells.

## 3. Quick start (5 minutes) — prove everything works

From `openfoam_cfd/scripts` in PowerShell:

```powershell
# 1. write a case (60 mm RT44HC capsule, 0.03 kg/s, 15 K above Tm, 3 h max)
python make_case.py --out ..\cases\my_first --pcm RT44HC --d 0.06 --mdot 0.03 --dT 15 --t-end-h 3

# 2. run it in WSL (meshes, solves, early-stops when fully melted)
$b = "/mnt/d/Final Year Project/OBJECTIVE2/Objective---2/objective2-rajasthan/openfoam_cfd"
wsl -d Ubuntu-24.04 -e bash "$b/scripts/run_one.sh" "$b/cases/my_first"

# 3. KPIs + comparison with the grey-box
python postprocess.py ..\cases\my_first --window-h 1
```

Expected for this exact case (verified): `t_melt_50 ≈ 1.0e3 s`, `t_melt_90 ≈ 1.9e3 s`,
`energy_residual_pct < 1`, `qc_energy_ok: true`, grey-box t90 ≈ 1.7× the CFD value.

Look at it: copy `cases\my_first\last_time` into ParaView
(`touch cases/my_first/case.foam`, open `case.foam`), colour by
`solidificationMeltingSource1:alpha1` (liquid fraction) and `T`.
For a wedge case use **Filters → Reflect/Rotational Extrusion** to see the sphere.

## 4. The full workflow

All commands from `openfoam_cfd/scripts`. Every step is **resumable** (cases with
a `kpi.json` are skipped; `--force` redoes).

### Step A — verification (do this before trusting any number)

```powershell
python run_doe.py --mode mesh --workers 3     # 3 meshes: 2.0, 1.2, 0.8 mm
python run_doe.py --mode sens --workers 6     # ×0.5/×2 viscosity, expansion; ×0.1/×10 Darcy Cu
```

Outputs `results/cfd_mesh_results.csv`, `results/cfd_sens_results.csv`.
Accept the production mesh only when t_melt_90 changes by less than your
stated tolerance; **report the mesh and sensitivity table in the paper**.
(`viscosity` and `expansion` are `[ASSUMED]` — the O1 database does not contain
them. Replace with datasheet values and cite.)

### Step B — the CFD design of experiments

```powershell
python run_doe.py --mode doe --n-per-pcm 16 --workers 8        # 3 PCMs × 16 = 48 cases
python run_doe.py --mode conduction --n-per-pcm 16 --workers 8 # g = 0 twins -> convection gain
```

Latin-hypercube over `d ∈ [40, 80] mm`, `ṁ ∈ [0.010, 0.050] kg/s`,
`ΔT_drive ∈ [5, min(25, 72 − Tm)] K` for each Phase-7 deployable PCM
(`RT44HC`, `savE® OM49`, `Lauric acid (C12)`). Output `results/cfd_doe_results.csv`
(+ `cfd_convection_gain.csv`).

Use `--tank-L 112.5` to evaluate the IS 12976:2023 "Case A" tank (changes the
superficial velocity, hence `h_w`) without touching frozen YAML.

### Step C — close the loop with the grey-box and optimise

```powershell
python cfd_calibrated_greybox.py --workers 6
```

1. fits `φ(d, ṁ, ΔT, Tm, L, k)` — the factor on `R_pcm` that reproduces CFD;
2. re-runs the project's Phase-5 designs in the annual simulator twice (frozen
   vs CFD-calibrated closure, **paired**);
3. reports whether rankings, the best design, or the PCM-vs-plain-tank margin move;
4. trains ExtraTrees on the calibrated runs, searches 6 000 constrained designs
   (`check_design`: diameter, count, flow, arrangement, packing, pressure drop),
   confirms the top 5 per regime in the simulator.

Outputs: `results/o2_cfd_paired_annual.csv`, `o2_cfd_paired_summary.csv/.md`,
`o2_cfd_calibrated_recommendation.csv`.

## 4b. Validation against published experiments (do this before the paper)

The CFD tier has **not** been validated against experiment yet (see
`docs/IMPROVEMENT_PLAN.md` P0). The harness is ready; it needs the papers' data:

```powershell
copy ..alidationenchmark_template.yaml ..alidationenchmark1.yaml   # fill every null from the paper (2023+ dataset)
python validate_sphere.py ..alidationenchmark1.yaml --workers 4 --cell-size 0.001
python validate_sphere.py ..alidationenchmark1.yaml --calibrate-cu --workers 4   # Darcy-constant sweep
```

* The spec refuses to run while any value is `null` — nothing is estimated.
* `calibrate` cases tune the Darcy constant; `test` cases are held out and scored
  (a constant tuned on one geometry failed by up to 38 % on another, Rocha 2023).
* Gate (declared in the spec before running): |t50| and |t90| error ≤ 15 %.
* Model differences to disclose: no volumetric expansion, no solid sinking /
  close-contact melting, mass-weighted melt fraction.
* `bc_mode="isothermal"` in `make_case.build_case` is the benchmark wall
  condition (wall = Tm + ΔT, no aluminium shell, no water-side `h`).
* The plumbing was checked once with project-database properties and its own
  output as reference (0.0 % error, energy residual 2.6 %) — that is a code check,
  **not** a validation (`results/_selftest_plumbing.*`).

### Fine-mesh DOE

```powershell
python run_doe.py --mode doe --n-per-pcm 16 --workers 8 --cell-size 0.0008 --tag fine
```

Writes `cases_fine/` and `results/cfd_doe_results_fine.csv` — the same 48 design
points as the 1.2 mm DOE (same seed), so the two meshes are paired case by case.

## 5. How to read the KPIs (`kpi.json`)

| KPI | Meaning |
|---|---|
| `t_melt_50/90/99_s` | time for the mass-weighted liquid fraction to reach 50/90/99 % |
| `E_window_kJ` | energy stored in one capsule at the end of the charging window (6 h) |
| `f_melt_window` | liquid fraction at window end (< 0.95 → capsule did not finish melting) |
| `P_mean_window_W` | mean charging power over the window |
| `energy_residual_pct` | wall-heat-flux integral vs stored energy — **QC gate, must be < 3 %** |
| `greybox_over_cfd_t90` | grey-box melt time ÷ CFD melt time, same scenario (>1 = grey-box too slow) |
| `R_pcm_scale_equivalent` | φ: factor on the grey-box `r/(5k)` that reproduces CFD (1 = grey-box right) |
| `Bi`, `Ste`, `Re_p` | Biot (`h R/k_PCM`), Stefan (`cp ΔT/L`), particle Reynolds number |

## 6. What this does **not** do (state these in the paper)

* **Arrangement is not CFD-resolved.** One capsule has no neighbours. The
  project's own sensitivity (`.claude/O2_Implementation_Plan_FreeSimulators.md`
  §2.1, Gate G0) shows scaling `h_w` over 16× moves annual useful energy by
  < 0.07 %, so a CFD arrangement factor cannot change the answer; arrangement
  enters through packing → pressure drop → pump power only. A multi-capsule 2-D/3-D
  array case is the next module if G0 is re-opened (needs `snappyHexMesh`).
* No tank-scale stratification, no volume change on melting, no supercooling.
* Melting is isothermal at `Tm`; the grey-box uses a ±1 K band.
* The wall-temperature drive is **constant** (`ΔT_drive` above `Tm`) for each
  case; in a real tank it varies hour by hour. φ is therefore an *effective*
  closure, evaluated at a reference `ΔT = 15 K`.
* Liquid viscosity and expansion are assumed (see §4 Step A).
* Axisymmetry assumes a vertical capsule axis and no wall-contact melting.

## 7. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `wsl: Failed to translate 'F:\…'` lines | harmless PATH warnings from Android Studio; ignore |
| `$'\r': command not found` in a `.sh` file | file was saved with Windows line endings: `sed -i 's/\r$//' run_one.sh` |
| `[case] blockMesh failed` | read `cases/<id>/log.blockMesh`; usually `d` so small that cell counts hit the floor |
| case never ends | raise `numerics.max_delta_t_s`/lower `scenario.t_end_h`; or the case is conduction-limited (small ΔT, big d): normal |
| `qc_energy_ok: false` | wall-flux and stored-energy disagree > 3 %: mesh too coarse or `sample_every_s` too large |
| very slow | copy the project to the Linux disk and run there; `/mnt/d` I/O is 5–10× slower (`run_one.sh` already runs on `~/o2_runs`) |
| `pgrep … longer than 15 characters` | use `pgrep -f` (process name `buoyantPimpleFoam` is 17 chars) |

## 8. Provenance of every number

`config/o2_cfd_config.yaml` tags each input. Nothing was invented silently:
PCM properties come from `data/objective1/pcm_database_rajasthan.csv`, tank,
wall, collector, flow and safety limits from the frozen shared configs, and the
two liquid properties that no project file contains are explicitly `[ASSUMED]`.
