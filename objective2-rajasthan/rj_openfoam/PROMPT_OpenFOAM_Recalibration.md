# Prompt for Claude Code — OpenFOAM/ParaView recalibration and validation of O2 (Rajasthan, v3)

Paste everything below the line into Claude Code, started from
`OBJECTIVE2/Objective---2/objective2-rajasthan` on branch `o2-cleanup-v3`.

---

You are working on Objective 2 (Rajasthan, v3, PCM fraction cap 30 %) of my FYP. Read `CLAUDE.md`
and follow its §0 pre-flight (sources/ first, PDFs only as fallback, never answer paper-specific
facts from memory). Then read, fully, before planning:
`docs/O2_Rajasthan_Pipeline_Report.docx` (or its markdown twin), `docs/01_MODEL_AND_METRICS.md`,
`docs/PROGRESS.md` sections 27-30, `configs/system_config_shared.yaml`, `configs/design_space.yaml`,
`src/simulation/heat_transfer.py`, `src/simulation/capsule_enthalpy.py`, `results/g4_cfd_draw_case.csv`,
`results/g22_sensitivity_r*.csv`, and everything in `rj_openfoam/`.

## Goal
Use OpenFOAM + ParaView to (a) verify the CFD setup against a published experiment, (b) check the
two assumed constants of the lumped capsule model — conduction coefficient `c` in `R = r/(c k)`
(frozen 5) and liquid-convection factor `F` (frozen 2.0) — for the three chosen v3 designs, and
(c) report whether the O2 result changes. This closes, in part, plan item WP2-C ("CFD tier") which
the report lists as **Not done**.

## Hard rules
1. **Do not touch `results/held_out_test.lock`** and do not run any stage that refuses while it exists.
   Any re-simulation with recalibrated constants uses **explore years 2016-2020 only** (and select
   years 2021-2023 for a re-scored comparison), never 2011-2015.
2. Do not edit `configs/system_config_shared.yaml` frozen values. A recalibrated constant enters
   only as an **off-by-default option** (same pattern as the G24 flow-dependent F_R), with tests.
3. PCM properties in `rj_openfoam/configs/rj_cases.yaml` must be copied from **the same PCM
   database file the simulator reads** (report §10.2: not the O1 ranking table). Record the file and
   row. Fields with no value in the database (viscosity, expansion coefficient) must be sourced from a
   datasheet or paper in `sources/`, or I am asked — never invented. Mark each with its source.
4. Every number in docs comes from a saved file; print the file under each table, as the report does.
5. Ask me before installing anything system-wide (OpenFOAM, ParaView). Python packages via pip are fine.
6. CFD-to-model agreement is model-to-model, not measurement; say so wherever it is reported.

## Steps (create a task list, tick as you go)

**R0 — Environment.** Detect OpenFOAM (`foamVersion`, `which blockMesh buoyantPimpleFoam foamRun`)
and ParaView (`which pvpython`). Set `openfoam.distribution` in `rj_cases.yaml` to `esi` or `org`.
If neither is installed, stop and tell me the install command for my OS (WSL2 Ubuntu is the expected
route on Windows), then continue with everything that does not need it.

**R1 — Model parity.** Wire `scripts/calibrate_lumped.py --use-repo-model` to call the real capsule
update from `src/` (single capsule, fixed water temperature, no tank). Show that the standalone lumped
model and the repo model give the same melt-fraction curve with c = 5, F = 2 (max abs difference
< 0.01). If they differ, fix the standalone one to match the repo, not the other way round.

**R2 — Mesh sanity.** Fill properties, generate `r0 charge_70` at 20/40/80 cells, run `blockMesh` and
`checkMesh` (wedge + axis; fix the blockMeshDict generator if checkMesh fails — e.g. face orientation,
axis patch), then run the three. Grid-independence criterion: time to 50 % and 90 % melt changes
< 2 % between 40 and 80 cells. Save `results/of_mesh_study.csv`.

**R3 — V0 literature benchmark (constrained melting in a sphere).** Tan, Hosseinizadeh, Khodadadi &
Fan 2009, IJHMT 52:3464-3472, n-octadecane in a glass sphere. Find the paper (check `sources/`, then
the web; DOI 10.1016/j.ijheatmasstransfer.2009.02.043). Take the sphere diameter, wall/bath
temperature, initial temperature and properties from the paper itself, fill `V0_tan2009`, run it,
and compare melt fraction vs time with the paper's experimental and Fluent curves (digitise the
figure with WebPlotDigitizer if no table; store the digitised CSV in `rj_openfoam/results/` with the
figure number). Expected known behaviour: enthalpy-porosity CFD melts the bottom faster than the
experiment (the paper links this to the thermocouple support). Report the mismatch, do not tune
`Cu`/`q` beyond one documented sensitivity (Cu 1e5 / 1e8 / 1e10). If the benchmark cannot be
reproduced within reason, say so and stop before R4 — the later numbers would not be trustworthy.

**R4 — Design capsules.** For r0/r1/r2 run `charge_70`, `charge_62` and `discharge_mains`
(fixed-wall), plus `charge_conv` with `h` taken from the simulator's water-side coefficient at each
design flow (0.0155 / 0.0493 / 0.0236 kg/s). Run ParaView `postprocess/paraview_capsule.py` on each
(melt-front and T snapshots, alpha1 = 0.5 contour CSVs). Check max |U| is laminar-plausible and the
energy stored by the CFD (wallHeatFlux integral) matches ΔH of the PCM within 2 %.

**R5 — Recalibration.** Run `calibrate_lumped.py` on every fixed-wall case. Report frozen vs fitted
(c, F), RMSE of melt fraction and t50/t90. Decide with me which of these to propose:
(a) keep frozen constants (if fitted changes stay inside what G22 already covers: F = 1-4),
(b) one fitted (c, F) per PCM, (c) a Nusselt-type correlation for F from the runs.
Note discharge (solidification) is conduction-dominated; F should only affect melting.

**R6 — Effect on O2 results (explore + select years only).** Add the chosen constants as an
off-by-default option, with unit tests. Re-run, for the three chosen designs and the best design of
each other O1 PCM: explore-year g_window/g_annual/d_overheat and the select-year re-score. Compare
with the band (21.1 / 14.4 / 21.9 kWh). State plainly whether the selection would change. Do **not**
re-run the held-out test. Save `results/of_recalibration_effect_r*.csv`.

**R7 — Optional tank check.** Re-run the existing G4 draw case (30 L at 55 C over 20 L at 25 C,
50 L tank) if its OpenFOAM case is in the repo, at two mesh levels, and refresh
`results/g4_cfd_draw_case.csv` only if the 27 L value changes. Optional, only if time allows:
one capsule layer in a water channel (chtMultiRegionFoam) to check the simulator's water-side `h`.
Flag compute time before starting; anything over ~12 h on a laptop is out of scope.

**R8 — Docs.** Update, keeping each file's style:
- `docs/07_OPENFOAM_VALIDATION.md` (fill the TBD tables from saved files),
- `docs/01_MODEL_AND_METRICS.md` §3.6 (CFD status of c and F),
- `docs/PROGRESS.md` (new dated section),
- `docs/05_*` limitations and `results/results_registry.csv` via `scripts/g12_registry.py` (add the
  new files), then `scripts/g12_verify_docs.py`,
- `docs/O2_Rajasthan_Pipeline_Report.docx` Section 13 and Table 47 (WP2-C row) with the real numbers,
- `rj_openfoam/README.md` run log.
Run `python -m pytest tests -q` at the end and report the count.

## Deliverable back to me
A short summary: OpenFOAM version, mesh study verdict, V0 agreement, frozen vs fitted (c, F) per
design, effect on g_window vs band, whether the selection changes, files written, and anything that
needs Dr. Deepika's decision.
