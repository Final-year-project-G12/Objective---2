# OpenFOAM CFD and ParaView - Objective 2, Uttarakhand

Uttarakhand's own CFD cases, built with the project's shared OpenFOAM set-up (`../../openfoam_cfd/`) but for the
**Uttarakhand designs and data**: the chosen capsule of each of the four regimes, the runner-up PCM where the PCM choice is
not resolved, and the 50 L tank at each regime's mains temperature, judged at the **50 C** delivery target.

**Status (2026-10-28): case files written, not run.** OpenFOAM and ParaView are not installed on the machine that wrote
them, so there are no solver results, KPIs or images yet. Every case is complete and ready to run (section 3).

## 1. What is here

```
openfoam_cfd/
├── config/o2_cfd_config_uttarakhand.yaml   all CFD inputs, each tagged FROZEN / O1-DB / CORR / ASSUMED / O2-SEL
├── scripts/
│   ├── make_uttarakhand_cases.py   writes every case below from the saved O2 results (start here)
│   ├── run_all_cases.ps1           runs all cases in WSL, post-processes them, makes the ParaView images and states
│   ├── summarise_results.py        collects the results into results/cfd_*_results_uttarakhand.csv
│   ├── make_case.py, run_one.sh, postprocess.py          capsule case: generate, run, KPIs + comparison with the grey-box
│   ├── viz_run.sh, plot_capsule_fields.py, capsule_paraview.py, capsule_movie.py   capsule visualisation
│   ├── tank_make_case.py, tank_run.sh, tank_postprocess.py   50 L tank: generate, run, metrics at 50 C
│   ├── component_paraview.py, make_pv_state.py              tank images and ready-to-play .pvsm state files
│   └── _paths.py                   finds objective2-uttarakhand and its PCM database
├── cases/        capsule cases (KPIs)
├── cases_viz/    capsule cases that keep every 30 s for the ParaView melt animation
├── cases_tank/   tank cases (charge, draw, idle) per regime
└── results/cases_index.csv   one row per case with every input
```

The scripts are copies of the shared ones with these Uttarakhand changes: `_paths.py` finds `objective2-uttarakhand` and
`pcm_database_uttarakhand.csv`; `make_case.py` reads `config/o2_cfd_config_uttarakhand.yaml`; `tank_make_case.py` takes the
regime's mains temperature (`--T-mains`; the shared version fixes 25 C, Rajasthan's value); `tank_postprocess.py` judges
delivery at 50 C and uses the case's mains temperature; the WSL distribution is `$env:O2_WSL_DISTRO` (default `Ubuntu-24.04`).

## 2. The cases (`results/cases_index.csv`)

Capsule = one PCM sphere of the chosen inner radius (the CFD sphere diameter is 2 x inner radius; the 0.8 mm aluminium wall is in
the boundary condition), charged by tank water **12 K above its melting point** at the design's flow rate (water-side h from the
same Wakao-Kaguei correlation as the grey-box). The shared quick-start uses 15 K; for PureTemp 58 that is 73 C, above the 72 C
water-side shield, so 12 K (67-70 C) is used here.

| Regime | Capsule cases | Why |
|---|---|---|
| 0 | `r0_chosen_puretemp_58` (R 39.8 mm, 0.019 kg/s), `_cond` twin, `r0_alt_plusice_a58` | chosen design; conduction-only twin calibrates the x2 convection factor; PlusICE A58 was 10 kWh ahead on the test years (inside the band) |
| 1 | `r1_chosen_puretemp_58` (R 39.3 mm, 0.031 kg/s), `_cond`, `r1_alt_plusice_a58` | same |
| 2 | `r2_chosen_save_om55` (R 39.7 mm, 0.020 kg/s), `_cond`, `r2_alt_puretemp_58` | same |
| 3 | `r3_chosen_n_hexacosane_c26` (R 38.4 mm, 0.010 kg/s) | regime 3 is water-only in O2 (PCM gives no gain); one case for completeness, no twin or runner-up |

Each chosen capsule also has a `cases_viz/` copy (6 h, fields every 30 s) for the ParaView animation.

Tank (no capsules; shared tank generator): per regime `r<c>_charge` (60 C collector return into a tank at the mains temperature),
`r<c>_draw` (30 L at 55 C over 20 L at the mains temperature, drawn at 0.03 kg/s; litres delivered at or above 50 C) and
`r<c>_idle` (standing losses to ambient = mains + 2 C). Mains: 21.8 / 18.6 / 17.0 / 7.4 C (regimes 0-3).

## 3. How to run (needs OpenFOAM v2406 in WSL)

Same requirements as the shared set-up (`../../openfoam_cfd/README.md` section 0): WSL with OpenFOAM v2406 at
`/usr/lib/openfoam/openfoam2406`, Windows Python with numpy / scipy / pandas / matplotlib / pyyaml, and ParaView for images.

```powershell
cd objective2-uttarakhand\openfoam_cfd\scripts
python make_uttarakhand_cases.py              # (re)write all cases; already done
$env:O2_WSL_DISTRO = "Ubuntu-24.04"           # the WSL distribution that has OpenFOAM
$env:PVBATCH = "D:\Program Files\ParaView 6.2.0\bin\pvbatch.exe"
.\run_all_cases.ps1                           # or -Only capsule | viz | tank
```

Outputs: `cases/*/kpi.json` (melt times t50 / t90 / t99, energy stored in the 6 h window, energy-balance QC, grey-box melt time
and the equivalent R_pcm scale), `cases_tank/*/tank_metrics.json` + `tank_profiles.png`, ParaView images in `*/paraview/`,
`.pvsm` states for the tank cases, and the two summary tables `results/cfd_capsule_results_uttarakhand.csv` and
`results/cfd_tank_results_uttarakhand.csv`. Open any case in ParaView through its `<case>.foam` file, or load a `.pvsm` state
(File -> Load State, "Use File Paths from State") and press Play. Run time: capsule cases minutes to tens of minutes each; a tank
case about 75 min per simulated hour (shared set-up).

## 4. What the CFD is for, and what it is not

It checks the grey-box capsule model at the Uttarakhand designs: the lumped `R_pcm = r/(5k)` with the x2 liquid-convection factor
(compare `greybox_over_cfd_t90` and `R_pcm_scale_equivalent`), and the 50 L tank's stratification at the colder Uttarakhand mains.
It does not model the tank with capsules, arrangement, supercooling or volume change; liquid viscosity and expansion are [ASSUMED]
(not in the O1 database). As with the shared tank draw case, any agreement is model-to-model, not a measurement.
