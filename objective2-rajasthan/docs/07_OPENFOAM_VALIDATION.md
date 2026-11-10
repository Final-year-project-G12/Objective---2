# 07 - OpenFOAM check of the two lumped-capsule constants (plan item WP2-C), status 2026-10-29

> **Terminology (2026-11-10).** The file name says "validation" but this is a *CFD model-consistency cross-check*, not validation: the setup does not reproduce Tan et al. 2009, and no experiment of the project capsules exists. Simulator verification, CFD cross-checking and experimental validation are three separate claims; only the first two exist, and the CFD one is incomplete. Never write "CFD-validated".

**Status: started, stopped at the literature benchmark. The CFD setup does not reproduce Tan et al. 2009, and the mesh study is not grid-independent, so no design-capsule run, no fit of `c`/`F` and no re-score of O2 was done. Nothing in `results/` outside the `of_*` files and nothing in the O2 results depends on this work.** All agreement below is model-to-model (or model-to-one-published-experiment), not a measurement of the project capsules.

Code and run data: `rj_openfoam/` (README there). Software: OpenFOAM-v2406 (ESI) in WSL2 Ubuntu-24.04 (`buoyantPimpleFoam`, `solidificationMeltingSource`), ParaView 6.2 (`pvpython`). Nothing was installed. The held-out lock `results/held_out_test.lock` was not touched; no simulator run used 2011-2015.

## 1. What is compared

| Lumped model (simulator) | CFD case (`rj_openfoam/scripts/make_capsule_case.py`) |
|---|---|
| one enthalpy node per capsule, melting band Tm +/- 1 K | 2-D axisymmetric 5 degree wedge, axis vertical, liquid and solid in one momentum equation with a Darcy sink (Voller-Prakash) |
| `R = r/(c k_eff)`, `c = 5`; `k_eff = k F` once melt fraction >= 0.5, `F = 2.0` | natural convection solved (Boussinesq), constrained melting, no volume change |
| mass = `density_solid` x inner volume, one `TC_W_mK`, `Cp_solid` / `Cp_liquid` | `rho0 = density_solid`, one k, mean Cp, melting isothermal at Tm (ESI's option has a single `Tmelt`) |

PCM properties of the three chosen PCMs are copied from `data/objective1/pcm_database_rajasthan.csv` (csv lines 34 savE OM55, 44 PureTemp 60, 39 PureTemp 58), the file the simulator reads (`configs/states/rajasthan.yaml: pcm_database_file`), into `rj_openfoam/configs/rj_cases.yaml`. **Liquid viscosity (3.5e-3 Pa s) and expansion coefficient (7.0e-4 1/K) are not in the database; no datasheet value is in `../Sources/` or was found. They are typical paraffin magnitudes copied from `../openfoam_cfd/config/o2_cfd_config.yaml` (itself marked ASSUMED), used only because the student chose that route on 2026-10-29, and every result that depends on them would be provisional. No design-capsule case was run, so none does.** The benchmark PCM uses the paper's own Table 1.

## 2. Step results

### 2.1 R1 model parity (done)

`rj_openfoam/scripts/calibrate_lumped.py --parity <design> <scenario>` runs the standalone lumped capsule and a version that calls the repo's own `_h_of_T`, `_T_f_of_h` and `_ua_node` from `src/simulation/tank_model_multinode.py` (water-side and wall resistance switched off, wall heat capacity off). The first draft of the standalone model used a mean density and a solid/liquid conductivity split that the repo does not have; it was corrected to the repo's rules. Maximum absolute difference in melt fraction over 3 designs x 3 scenarios x (c, F) = (5, 2), (5, 1), (8, 3): 0.000000 in all 27 cases (the criterion was < 0.01).

Source: `rj_openfoam/results/of_model_parity.csv` (r0 rows):

| design | scenario | c | F | max abs diff | t50 lumped (s) | t90 lumped (s) |
|---|---|---|---|---|---|---|
| r0 | charge_70 | 5 | 2 | 0.000000 | 6376 | 8303 |
| r0 | charge_70 | 5 | 1 | 0.000000 | 6376 | 10230 |
| r0 | charge_70 | 8 | 3 | 0.000000 | 3985 | 4788 |

`F` has no effect before 50 % melt by construction, which is why t50 does not move with F. Note: with c = 5, F = 2 the lumped model needs 6376 s to reach 50 % in r0 at a 70 C wall; `r1` at a 62 C wall (Tm 61 C) does not reach 50 % in 6 h.

### 2.2 R2 mesh study (done; criterion NOT met)

Case `r0 charge_70` (savE OM55, R = 39.5 mm, wall 70 C, start 30 C), 20 / 40 / 80 cells across the radius (400 / 1600 / 6400 cells). `checkMesh -allGeometry -allTopology` passed ("Mesh OK") on the V0 mesh at 20 cells; the generator needed no fix of the mesh itself, but its first draft used keys that OpenFOAM-ESI does not have and was rewritten from the case that already ran on this machine (`../openfoam_cfd/scripts/make_case.py`).

| cells | t50 (s) | t90 (s) | max U (m/s) | wall energy / dH - 1 (%) |
|---|---|---|---|---|
| 20 | 960 | 1760 | 0.0074 | -1.1 |
| 40 | 980 | 2020 | 0.0069 | -0.9 |
| 80 | 1120 | 2340 | 0.0119 | -1.0 |

Source: `rj_openfoam/results/of_mesh_study.csv` (the 80-cell run was stopped at 2900 s, after full melt; dH uses the state at the stop time). Change 40 -> 80 cells: t50 +14.3 %, t90 +15.8 % (criterion < 2 %): **not grid-independent.** The melt is a few millimetres of convecting liquid layer and the front is unsteady; it needs a finer mesh or a different treatment before any t50 / t90 is quoted. Energy closure (wall heat-flux integral against the PCM enthalpy change) is within 1.1 % in all three, inside the 2 % criterion, and the maximum velocity is 7-12 mm/s (laminar, plausible). The CFD melts 50 % in about 1000 s where the frozen lumped model needs 6376 s; this is not interpreted, because the benchmark below is not met.

### 2.3 V0 literature benchmark, Tan et al. 2009 (done; NOT reproduced)

Tan, Hosseinizadeh, Khodadadi and Fan, Int. J. Heat Mass Transfer 52 (2009) 3464-3472 (PDF added to `../Sources/` by the student on 2026-10-29). Taken from the paper: n-octadecane, Table 1 (Tm 28.2 C, 772 kg/m3, nu 5e-6 m2/s, Cp 2330, k 0.1505, L 243.5 kJ/kg, beta 0.00091); sphere diameter 101.66 mm (Fig. 1; radius 50.83 mm, which also reproduces the paper's Ra = 2.63e8); solid initially 1 C below Tm, outer surface held at 40 C (Pr 59.5, Ste 0.113); Darcy constant C = 1e5. The paper's glass wall (about 1.5 mm in Fig. 1, properties not given) is not modelled; 40 C is applied on the PCM surface. The experimental points and the Fluent curve are read **by eye** from Fig. 4 (WebPlotDigitizer was not used, estimated error +/-0.02 in liquid fraction and +/-1 min); Table 2 of the paper is printed numbers.

Time in minutes to reach the liquid fraction (source `rj_openfoam/results/of_v0_benchmark.csv`, curves in `rj_openfoam/results/tan2009_fig4_digitised.csv`):

| series | 25 % | 50 % | 75 % | 90 % | RMSE vs experiment | RMSE vs Fluent |
|---|---|---|---|---|---|---|
| Tan experiment | 40 | 60 | 90 | 120 | | |
| Tan Fluent | 30 | 50 | 70 | 90 | | |
| OpenFOAM, 20 cells, Cu 1e5 | 11.7 | 23.7 | 33.7 | 41.3 | 0.328 | 0.209 |
| OpenFOAM, 40 cells, Cu 1e5 | 11.3 | 23.0 | 34.3 | 45.3 | 0.320 | 0.200 |
| OpenFOAM, 80 cells, Cu 1e5 | 12.0 | 25.3 | 40.3 | 53.7 | 0.286 | 0.163 |
| OpenFOAM, 40 cells, + 1.5 mm glass layer | 13.3 | 27.0 | 41.7 | 55.0 | 0.278 | 0.153 |
| OpenFOAM, 80 cells, + 1.5 mm glass layer | 14.0 | 29.3 | 47.3 | 63.0 | 0.245 | 0.118 |
| OpenFOAM, 20 cells, Cu 1e8 (run crashed at 36 min) | 13.3 | 30.0 | | | 0.191* | 0.107* |
| OpenFOAM, 20 cells, no convection (g = 0) | 19.7 | 89.0 | | | | |

\* over the 0-36 min that ran only, so not comparable with the other rows. Cu 1e10 diverged at 0.03 s in OpenFOAM-ESI (negative temperature in the first steps); Cu 1e8 diverged at 2164.6 s (Courant number rising to 930) with both the default time step and a smaller start step. Those are the Cu 1e5 / 1e8 / 1e10 sensitivity the plan allowed; Cu and q were not tuned further.

Checks that were made:
- The latent-heat source is implemented correctly: with gravity off the CFD gives 19.7 / 89.0 min to 25 / 50 %, an independent 1-D spherical enthalpy solution (`rj_openfoam/scripts/stefan_sphere_1d.py`) gives 19.0 / 88.4 min (`rj_openfoam/results/of_v0_conduction_check.csv`).
- Energy closes to 1.3 % (wall heat flux against enthalpy change, V0 20 cells).
- 20 to 40 cells changes t50 by 3 % and t90 by 10 %.
- ParaView 6.2 (`rj_openfoam/postprocess/paraview_capsule.py`, fixed for the ESI field name and the ParaView 6 `AxisAlignedReflect` filter) renders the liquid-fraction field; at 20 min the solid is displaced downward with the thicker liquid layer on top, the same qualitative pattern as Tan Fig. 2 (`rj_openfoam/results/paraview_v0_n40/`).

Second attempt (student choice 2026-10-29: glass wall and finer mesh). A 1.5 mm glass layer (the thickness read from Fig. 1; its conductivity, 1.1 W/mK, is ASSUMED borosilicate and not in the paper) was put between the fixed 40 C outer surface and the PCM, and the mesh was refined to 80 cells. The glass slows t50 by about 17 % (23.0 -> 27.0 min at 40 cells, 25.3 -> 29.3 at 80); refining slows it by about 10 % and t90 by 15-18 %, so the mesh is still not converged (a 160-cell run would take about 40 h by scaling the 5 h of the 80-cell run, outside the 12 h limit). Best case, 80 cells with glass: t50 29.3 min against 50 (Fluent) and 60 (experiment), i.e. still 1.7 and 2.0 times fast. A bath warm-up was not tried: the paper gives no data for it and a ramp would be invented. Run times: 80 cells about 5 h each.

Verdict (first attempt, bare wall): with natural convection the CFD melts the sphere about 2.5 times faster than the experiment at 50 % (23 against 60 min) and about 2.2 times faster than the paper's own Fluent calculation (50 min), with a mesh that is not converged. The gap to Fluent is larger than the gap between Fluent and the experiment (1.2 times), so the discrepancy cannot be assigned to the thermocouple support the paper blames. Two observations point to the boundary condition rather than the convection model alone: the paper's experimental and Fluent curves are both slower than pure conduction with a step wall temperature would be at 25 % (30 and 40 min against 19 min), i.e. the real wall did not jump to 40 C; and the paper itself links the delay to stratification of the "constant-temperature bath". Not tested here: a glass wall and bath warm-up, the Fluent mushy band, a finer mesh. **Because the benchmark is still not reproduced after the second attempt (best t50 29.3 min against 50 and 60 min, mesh trend not converged), the work stays stopped before R4, as the task instructions require.**

### 2.4 The two papers added on 2026-10-30 (read, not run)

- **Turski 2025** (`../Sources/PCM-Filled Capsules (RT44HC) for Heat Storage—Laboratory Scale Pilot Study.pdf`, Energies 18(2), 345): a tank-level experiment (water cooling with and without RT44HC capsules of 22 mm thickness). It has no melt fraction against time for one capsule, so it cannot serve as a single-capsule benchmark.
- **Jia 2024** (`../Sources/Numerical and three-factor design investigation ... .pdf`, J. Energy Storage 85, 111094): a COMSOL study with no new experiment. Its validation reuses Tan 2009 (deviation within 10 % in its Fig. 3b, with the mushy-zone constant and phase-change range not stated in the text) plus Dong et al. and Al-Abidi et al. It reports that the 2-D axisymmetric model melts slower than the 3-D sphere, by 509.7 s at R = 50 mm, so the axisymmetric simplification does not explain an over-fast CFD melt. It ranks the mushy-zone constant second in importance after the radius, which means the constant is a tuning parameter whose best value depends on the case; fitting it to Tan would not make the c and F fit transferable (the project's own note on Rocha 2023 says a constant validated on one geometry failed by up to 38 % on another). The Rocha 2023 paper was not supplied.
- Result: neither paper gives an independent sphere benchmark, so V0 is unchanged and the work stays before R4.

### 2.5 V1 literature benchmark, Dong et al. 2022 (done; NOT reproduced)

Dong, Wang, Zhang, Shi, Zhang, Shuai, "Experimental and numerical study on flow characteristic and thermal performance of macro-capsules phase change material with biomimetic oval structure", *Energy* 238 (2022) 121830 (`../Sources/Experimental and numerical study on flow characteristic ... .pdf`). Its sphere is a real single-capsule experiment: n-octadecane (Table 2: rho 774.5, Tm 301.35 K, cp 2330, L 243.5 kJ/kg, k 0.1505, mu 3.86e-3, beta 9.42e-4, so nothing assumed), PCM radius 34.3 mm (Table 1), 2 mm resin shell (k 0.4, Table 2), start 300.35 K, bath 311.35 K (Sec. 3.3), constrained melting, total melt time 143 min (Sec. 4.1). The sphere curve of Fig. 7 was read by eye (`rj_openfoam/results/dong2022_fig7_sphere_digitised.csv`, about +/-0.03). The paper gives no CFD curve for the sphere and no outer heat-transfer coefficient of the bath. Rocha 2023 (also supplied) has no sphere case (horizontal enclosure and shell-and-tube), so it is not a benchmark.

Model: `rj_openfoam/configs/rj_cases.yaml` scenario `V1_dong2022`, 40 cells, same generator, Cu 1e5, with the 2 mm resin layer; outer h is 1e5 (ideal bath) or 300 W/m2K (my guess, not from the paper). Model-to-experiment, one sphere.

| Series | t25 (min) | t50 (min) | t75 (min) | t90 (min) | RMSE vs experiment |
|---|---|---|---|---|---|
| experiment (coarse points) | 40 | 60 | 120 | 143 | - |
| CFD, ideal bath | 13.7 | 29.7 | 47.7 | 63 | 0.27 |
| CFD, h = 300 | 17 | 37 | 59 | 78.3 | 0.20 |
| CFD, conduction only (g = 0) | 15.3 | 52.3 | 102 | 142.3 | 0.07 |

Table source: `rj_openfoam/results/of_v1_benchmark.csv` (the experiment row reads the first sample at or above each fraction, so it is coarse; interpolating the 7 points gives about 28 / 58 / 100 / 125 min).

```
series,case,t25_min,t50_min,t75_min,t90_min,rmse_vs_experiment
experimental,,40,60,120,143,nan
openfoam,lit_V1_dong2022_n40_glass,13.67,29.67,47.67,63,0.2656
openfoam,lit_V1_dong2022_n40_glass_h300,17,37,59,78.33,0.2036
openfoam,lit_V1_dong2022_n40_cond_glass,15.33,52.33,102,142.3,0.06959
```

Reading: with natural convection the CFD melts about 1.6 to 2 times faster than the measurement, the same direction and size as against Tan 2009 (CFD t50 23 to 29 min vs 60). Only the run with convection switched off is near the measured curve, which is not a physical model of a liquid layer. Two independent experiments now agree that this CFD set-up is too fast; the likely candidates are the mushy-zone constant (Jia and Rocha both say it is case-dependent), the isothermal-melting assumption, and the unknown bath resistance, none of which was tuned. **Benchmark rule applied: R4 is not run.**

Frozen lumped model against the same two experiments (model-to-experiment, no resin wall, fixed outer T; `rj_openfoam/results/of_lumped_vs_benchmarks.csv`):

```
scenario,c,F,t25_min,t50_min,t75_min,t90_min
V0_tan2009,5,2,71.5,nan,nan,nan
V0_tan2009,5,1,71.5,nan,nan,nan
V1_dong2022,5,2,38.1,78.1,99.1,112.2
V1_dong2022,5,1,38.1,78.1,120.1,146.4
```

Tan: the frozen model has not reached 50 % at 140 min (experiment t50 60 min), so it is much slower. Dong: t50 78 vs about 58 min and t90 112 to 146 vs about 125 min, so it is within roughly 35 % at half melt and close at 90 %. The lumped model is on the slow (conservative for charging) side of both experiments; this is the only direct evidence so far about its constants, and it was obtained without fitting anything.

## 3. What was not done and why

| Step | State |
|---|---|
| R4 design capsules (charge 70 / 62, discharge, convective, ParaView on each) | not run (benchmark not met; mu and beta also unsourced) |
| R5 fit of (c, F) per design and the choice (a) keep / (b) per PCM / (c) Nusselt-type | not run; decision needed (section 5) |
| R6 re-score of the chosen designs with fitted constants | not run; **the option itself exists** (section 4) |
| R7 G4 tank draw case and water-side h | not run; the old tank cases are in `../openfoam_cfd/cases_tank/`, outside this project folder |

Whether the selection or the 21.1 / 14.4 / 21.9 kWh bands would change is therefore **not known**; no claim is made either way. What G22 already shows is unchanged: F = 1 and F = 4 move `g_window` by at most 13.7 kWh, inside the bands (`results/g22_sensitivity_r*.csv`).

## 4. Code added to the simulator (off by default, with tests)

`pcm_integration.conduction_coefficient_c` (default 5.0 when the key is absent, which is the case in the frozen `configs/system_config_shared.yaml`, left unedited) is read by `src/simulation/heat_transfer.py` and by `src/simulation/tank_model_multinode.py` (`_ua_node(..., c_cond=5.0)`, kernel parameter `P[34]`). A recalibrated `c` and `F` can only be passed through `system_config_overrides` (`pcm_integration.conduction_coefficient_c`, `pcm_integration.liquid_convection_enhancement`), like the conv 1 / conv 4 variants of G22. Tests: `tests/test_capsule_closure_option.py` (5 tests: key absent in the frozen config; explicit c = 5 equals the default in both code paths; a hand calculation of the changed PCM resistance; Python and numba paths agree for c = 8; a one-year run with explicit c = 5 is bit-identical to the default, c = 10 differs, energy still closes).

## 5. Open items for Dr. Deepika

1. Liquid viscosity and expansion coefficient of savE OM55, PureTemp 58 and PureTemp 60 (datasheets or a measurement); until then every CFD number that uses them is provisional.
2. Benchmark route: **decided 2026-10-30 by the student: report the CFD as an unvalidated upper bound on the melt rate.** Neither Tan 2009 (section 2.3) nor Dong 2022 (section 2.5) is reproduced, so no CFD-derived value of c or F is proposed, the frozen c = 5 and F = 2 stay, R4 to R6 are not run, and the simulator option of section 4 stays off. Stated result: the CFD melts about 1.6 to 2 times faster than both experiments, and the frozen lumped model is slower than both experiments (conservative for charging), so the frozen constants are not contradicted by the only measurements available. A sweep of the mushy-zone constant (Cu 3e5 to 3e6) was offered and not taken; it would be tuning and would not transfer to the design capsules.
3. Whether a CFD-derived correction should enter the simulator at all before the benchmark is reproduced; the lumped model currently makes melting about 6 times slower than this (unconverged) CFD at 50 % for r0, which would raise the PCM benefit if the CFD were right.

## 6. Files

| File | Content |
|---|---|
| `rj_openfoam/results/of_model_parity.csv` | R1 parity, 27 rows |
| `rj_openfoam/results/of_mesh_study.csv` | R2 |
| `rj_openfoam/results/of_v0_benchmark.csv`, `.png` | V0 table and figure (the .png predates the glass and 80-cell runs) |
| `rj_openfoam/results/of_v0_conduction_check.csv` | conduction-only check against the 1-D solution |
| `rj_openfoam/results/of_v1_benchmark.csv`, `.png`, `rj_openfoam/results/dong2022_fig7_sphere_digitised.csv`, `rj_openfoam/results/of_lumped_vs_benchmarks.csv` | V1 table, figure, reference curve, lumped-model comparison |
| `rj_openfoam/results/tan2009_fig4_digitised.csv`, `rj_openfoam/results/tan2009_table2.csv` | reference data from the paper (Fig. 4 read by eye; Table 2 as printed) |
| `rj_openfoam/results/runs/<case>/` | `meltAndTemp.dat`, `wallQ.dat`, `maxU.dat`, case metadata, `controlDict`, `log.checkMesh`, wall time of each run (the 900 MB case folders were deleted; regenerate with `rj_openfoam/scripts/run_batch.py`) |
| `rj_openfoam/results/paraview_v0_n40/` | ParaView snapshots and front contours of the 40-cell V0 run |

## 6. cfd_closure_v1 switch (B2, 2026-11-10)

`pcm_integration.closure` selects a named capsule closure (`src/simulation/cfd_closure.py`): absent or `legacy` keeps c = 5, F = 2 bit-for-bit; `cfd_closure_v1` (`configs/cfd_closure_v1.yaml`) sets c = 10, F = 5, the best fit to the r0 charge_70 case at 40 cells (`rj_openfoam/results/calib_r0_charge_70_n40.csv`, RMSE 0.2519 against 0.4739 for c = 5, F = 2). The fitted c is on the edge of the search grid at 20, 40 and 80 cells and the CFD is not grid-independent (section 2.2), so v1 is UNVALIDATED and is not used for any reported result. One-year effect: annual E_del45 961.6 kWh (legacy) against 931.4 kWh (v1), `results/b2_closure_v1_check.csv`. Test: `tests/test_cfd_closure.py`.

## 7. B3 OpenFOAM checks: GCI, time step, freezing, design spot-checks (2026-11-10)

All numbers below are read from `rj_openfoam/results/` (files named per line). OpenFOAM v2406 in WSL2, 16 logical cores, one case per core. Model-to-model only: the CFD does not reproduce Tan 2009 or Dong 2022 (sections 2.3, 2.5), so every CFD number here is an unvalidated upper bound on the melt rate. Fluent is not installed: the OpenFOAM-versus-Fluent comparison (C2) is **not done**. C4 (packed bed) and C6 (collector) were left out by agreement.

- **Richardson / GCI (`results/of_gci.csv`, `scripts/gci.py`):** from the existing 20 / 40 / 80-cell r0 charge_70 meshes (refinement ratio 2). t50 960 / 980 / 1120 s gives an observed order p = -2.81 and t90 1760 / 2020 / 2340 s gives p = -0.30: the times grow with refinement, so the study is **not in the asymptotic range**, no extrapolated value and no GCI can be quoted, and the earlier finding (40 -> 80 cells changes t50 by +14.3 % and t90 by +15.8 %, criterion < 2 %) stands. A 160-cell mesh was not run: the measured cost of 40 -> 80 cells in the Tan case is 1152 s -> 18683 s (`results/runs/lit_V0_tan2009_n40` and `_n80` wall_time.txt), about 16x.
- **Time-step check (`results/runs/r0_charge_70_n20_co025/`):** maximum Courant number 0.5 -> 0.25 and initial step halved on the 20-cell mesh: t50 960 s -> 940 s (-2.1 %), t90 1760 s -> 1760 s (0 %); wall time 554 s -> 1457 s. The time step is not the cause of the mesh sensitivity.
- **Freezing (discharge) check (`results/of_freeze_check.csv`, `scripts/freeze_compare.py`):** r0 (savE OM55, R 39.5 mm), liquid at 64 C, fixed wall 25.13 C (regime-0 mains), 6 h. Minutes until the liquid fraction falls to 0.9 / 0.5 / 0.1: CFD 20 cells 2.0 / 25.7 / 105; CFD 40 cells 1.7 / 26.7 / 111 (wall time 112 s and 750 s); lumped frozen closure (c 5, F 2) 7.8 / 23.3 / 55; lumped `cfd_closure_v1` (c 10, F 5) 1.6 / 4.7 / 20.5. So the frozen lumped model matches the CFD at half freeze (within 15 %) but freezes the last 10 % about twice as fast as the CFD, and the melt-fitted v1 closure freezes far too fast. 20 -> 40 cells changes the CFD t50 by +3.9 % and the 10 % time by +5.7 %.
- **Spot-checks of the chosen designs (S9 / C5; `results/of_spotcheck.csv`, `scripts/spotcheck_compare.py`):** one capsule per v3 design, fixed 70 C wall from 30 C, 40 cells. Minutes to 50 % / 90 % liquid fraction: r0 CFD 16.3 / 33.7, lumped frozen 106.3 / 138.4, lumped v1 53.1 / 59.6; r1 (PureTemp 60, R 40 mm) CFD 28.7 / 54.0, lumped frozen 123.0 / 166.7, lumped v1 61.5 / 70.3; r2 (PureTemp 58, R 40 mm) CFD 19.3 / 37.7, lumped frozen 93.2 / 123.9, lumped v1 46.6 / 52.8. Melt-fraction RMSE against the CFD curve: frozen 0.474 / 0.446 / 0.406, v1 0.252 / 0.187 / 0.185 (r0 / r1 / r2). Wall times 2678 s (r0, existing run), 2156 s (r1), 2594 s (r2). The frozen lumped model is 4.3 to 6.5 times slower than this CFD at t50 in all three designs, the same side (slow, conservative for charging) already stated in section 3; the CFD itself melts about 1.6 to 2 times faster than the experiments it was tested on, so the true gap is smaller than these ratios. Not re-run with the v1 closure: any selection, band or held-out result.
- **Generator fix:** `scripts/make_capsule_case.py` wrote the liquid-start field as `0/solidificationMeltingSource1:alpha1`; a colon in a file name is an NTFS stream on Windows and the file was lost on copy to WSL, so the first freezing run silently started with the PCM treated as solid. The generator now writes `0/alpha1_init` and `Allrun` renames it on Linux. That first run was discarded; only the corrected runs are used. Melting cases start solid and were not affected.
- **Run mechanics:** `scripts/run_wsl.sh` has CRLF line endings in this checkout and `run_batch.py` passes the case path with spaces badly; the runs above were started with `bash -c "tr -d '\r' < run_wsl.sh > /tmp/x.sh; bash /tmp/x.sh ../cases/<case>"` from the `scripts` folder. Raw case folders were archived into `results/runs/<case>/` (same files as before) and the 957 MB `cases/` folder was deleted.
