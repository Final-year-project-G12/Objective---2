# Objective 2 (Rajasthan) - what this folder is doing

Written 2026-11-26 for the common-plant rebuild. Results: `docs/RESULTS_COMMON_PLANT.md`. Decisions: `docs/REBUILD_COMMON100L.md`. The older v3 text (50 L plant) is kept in docs 01-07 and `docs/PROGRESS.md` under a LEGACY banner.

## The question, precisely

For each of Rajasthan's three Objective 1 climate regimes, which PCM (from O1's own Top-3) and which capsule design (inner radius, PCM fraction, arrangement) make a 100 L solar tank on a 2.0 m2 collector deliver more 45 C hot water than the same tank filled with water only, and is that gain bigger than the noise in the simulator?

Fixed: tank 100 L, collector 2.0 m2, pump flow 0.030 kg/s, daily demand 175 L of 45 C water. Searched: inner radius 10-40 mm, PCM fraction 2-40 %, arrangement (single-layer, staggered). The stack position of the capsules is not chosen; every design is simulated at the bottom, centre and top and ranked on the mean, and it is rejected if its worst position does not beat the band.

## How the answer is reached (stages in `pipeline.py`)

1. **O1 manifest, weather, verification** (`o1`, `weather`, `verify`): which regimes, which PCMs, which member weather points, and checks that the simulator converges (time step, node count, energy closure).
2. **Baseline and screening** (`baseline`, `screening`): the water-only tank is simulated exactly for every year, then a Taguchi L9 screen shows which factors matter.
3. **DOE, surrogates, search** (`doe`, `surrogate`, `optimize`): 128 Sobol designs per (regime, PCM) pair, five surrogate families compared, then NSGA-II with committee active learning. Surrogates only rank and propose; every reported number comes from the simulator.
4. **Grid, band, assessment** (`grid`, `band`, `assess`): a dense grid checks the search, and a repeatability band measures how much the gain moves with year, time step, node count, properties, member point, demand and mains.
5. **Selection** (`select`): a frozen funnel on the 2020-2021 select years picks one design per regime (written down before any select-year run: `docs/REBUILD_COMMON100L.md` section 4b, code in `scripts/g10_select.py`).
6. **One-shot test and report** (`test`, `report`): 2006-2010 is simulated once under a lock; 2022-2025 are report-only years.
7. **Hand-off, M1, figures, supplementary, manifest**: Objective 3 contract, MATLAB checkpoint, plots, post-result studies, SHA-256 of every output.

## What it found

| regime | PCM | capsules x radius | test g_window (kWh/yr) | worst anchor | band | overheat-guard change |
|---|---|---|---|---|---|---|
| 0 | savE OM55 | 140 x 40.0 mm | 158.2 | 145.2 | 39.8 | +797 h/yr |
| 1 | PureTemp 60 | 126 x 39.1 mm | 70.8 | 52.6 | 24.6 | +416 h/yr |
| 2 | PureTemp 58 | 140 x 40.0 mm | 125.2 | 115.4 | 24.3 | +739 h/yr |

PCM wins in all three regimes, in the select years, the test and the report-only years, with no hard-limit hours. Regime 1 is the thinnest margin. PCM always costs overheat-guard hours because capsules displace water.

## Read this before quoting anything

- **The win is conditional on the demand.** At 100 L/day the plain tank already meets 98-99 % of the demand and PCM gains about 0 (-1 to -5 kWh/yr in the scan). 175 L/day was chosen after that scan, on explore years only, to match Tamil Nadu; it is the 45 C equivalent of a 100 LPD heater rated at 60 C. A 150 L tank at 175 L/day also removes the gain. This is declared in `docs/REBUILD_COMMON100L.md` section 8.
- **Not a global optimum.** The 40 mm radius end binds in nearly every Pareto front and the 40 % cap in many. A wider box is untested.
- **Three kinds of checking, none of them validation:** (1) the simulator is verified against its own convergence and closure checks; (2) a model-to-model CFD check exists for single capsules (`docs/CFD_VERIFICATION.md`), incomplete and not reproducing the literature benchmark; (3) there is no experiment. Never write "CFD-validated".
- **Frozen constants:** capsule conduction constant c = 5 and liquid-convection factor F = 2 stay; `cfd_closure_v1` is unvalidated and off.
- **Pareto front vs selected design are different things.** The front is what the search found; the selected design is the funnel's pick inside the set the band cannot tell apart on g_window (S0), so the exact capsule count should not be over-read.
- **Regime 0 band** rests on 4 member points (project decision: accept the calibrated band).
- **Collector parameters** (F_R tau alpha 0.75, F_R U_L 4.5, area basis) have no project source.

## Where things are

| path | what |
|---|---|
| `pipeline.py` | entry point; `--stage status` shows what exists |
| `configs/` | frozen system, design space, funnel, state (`states/rajasthan.yaml`, demand 175) |
| `data/` | O1 outputs, weather point-years, demand profile (legacy 100 L and 300 L files in `data/legacy/`) |
| `src/` | simulator kernel, design space, optimiser, metrics, weather roles, hand-off builder |
| `scripts/` | one script per stage (`g*`, `r*`, `m1_export.py`) |
| `results/` | all outputs; `locks/` holds the spent one-shot lock; `m1_matlab/` the MATLAB checkpoint; `plots_common100L/` figures; `archive_100Lday_2026-11-24/` stale 100 L/day files |
| `matlab/` | `m1_checkpoint.m` |
| `objective3/` | contract for Objective 3 |
| `rj_openfoam/` | OpenFOAM single-capsule checks (legacy 50 L designs, see the CFD doc) |
| `results_legacy_50L_v3/` | the old chain, kept for reference |
| `docs/` | `REBUILD_COMMON100L.md`, `RESULTS_COMMON_PLANT.md`, `HOW_TO_RUN.md`, `OBJ2_DATA_FLOW_INPUT_TO_OUTPUT.md`, `CORRECTIONS.md`, `CFD_VERIFICATION.md`, `PLAN_DEVIATIONS.md`, `viva.md` |

## Honest limits

- Simulation only: no hardware experiment, no measured PCM data for the project capsules.
- The lumped capsule model is slower than single-capsule experiments and CFD at melting (conservative for charging) but is supported at tank level in the Objective 4 benchmark; see the CFD doc.
- 175 L/day on a 100 L tank is still below IS 12976:2023 storage guidance (1.5-2x daily volume).
- The held-out years 2006-2010 are spent for Objective 2 and cannot be reused for choosing anything.
