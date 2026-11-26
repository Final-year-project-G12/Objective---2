# How to run Objective 2 (Rajasthan, common plant)

Written 2026-11-26. All commands run from the `objective2-rajasthan` folder with the project environment (`D:\Final Year Project\.venv`). The older `commands to run.md` describes the legacy v3 chain and must not be used.

## Read this first

- **The one-shot test is spent.** `results/locks/o2_test_eb67320ff3cb.lock` is set. The stages that decide the frozen design (`baseline` ... `select`) refuse while the lock exists. `--allow-invalidate` overrides that and makes the 2006-2010 test describe designs you no longer have. Do not use it unless you mean to restart the whole study with a new plant hash.
- **Never run `scripts/g10_test.py` by hand.**
- **Stale files are resumed.** The DOE and grid scripts continue from existing CSVs. After any change to the plant, demand, weather or box, archive `results/` first (see `results/archive_100Lday_2026-11-24/` for the pattern) or you will silently reuse old runs.
- **Memory:** during the rebuild about 1.3 GB of RAM was free and at most 4 jobs were run at once, and do not run pytest at the same time (that caused an out-of-memory failure in the supplementary stage once).
- Set `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`.

## Check what exists

```powershell
python pipeline.py --state rajasthan --stage status
```

## Stages and measured run times (4 jobs unless noted, this machine)

| stage | command | time |
|---|---|---|
| o1, weather, verify, baseline | `python pipeline.py --state rajasthan --stage <name>` | not timed |
| screening | `--stage screening --jobs 4` | 15 min |
| doe | `--stage doe --jobs 4` | 3.2 h |
| surrogate | `--stage surrogate` | 9 min |
| optimize | `--stage optimize --jobs 4` | 1.0 h |
| grid | `--stage grid --jobs 4` | 32 min |
| band | `--stage band --jobs 4` | 30 min |
| assess | `--stage assess` | 4 s |
| select | `--stage select --jobs 4` | 35 min |
| test (once only) | `--stage test --include-test --jobs 3` | 26.5 min |
| report | `--stage report --jobs 3` | 23.5 min |
| handoff | `--stage handoff` | seconds |
| m1 | `--stage m1 --matlab "D:/Program Files/MATLAB/R2026b/bin/matlab.exe"` | 7.7 min |
| figures | `--stage figures` | seconds |
| supplementary | `--stage supplementary --jobs 2` | 57 min |
| manifest | `--stage manifest` | seconds |

The deciding chain (`screening` to `select`, about 5.7 h in total) can be run unattended with `sh run_chain_l4_l7.sh` (logs to `logs/chain.txt`, stops at the first failure, never runs the test).

## Quick checks

```powershell
python pipeline.py --state rajasthan --stage simulate --cluster 1 --pcm-rank 1 --radius-mm 30 --fraction 0.1 --arrangement staggered
python -m pytest tests -q
python scripts/r24_check_o3_contract.py
```

`simulate` runs one design at the cheap fidelity and writes no files. The test suite takes about 2 minutes (99 tests).

## Objective 3 hand-off

```powershell
python pipeline.py --state rajasthan --stage handoff
python scripts/r23_publish_o3_contract.py
python scripts/r24_check_o3_contract.py
```

## MATLAB checkpoint M1

Needs MATLAB (R2026b with the default toolboxes is enough; it uses no Simulink here). The stage first exports the frozen designs (`scripts/m1_export.py`: per regime a water-only run, the chosen PCM design and the best design of each other O1 PCM, select year 2021, 37.5 s step) and then `matlab/m1_checkpoint.m` recomputes the numbers from the hourly records alone and draws the figures. The gate passes when the MATLAB numbers match the Python numbers, the energy balance closes and the ranking is identical: result in `results/m1_matlab/m1_gate.txt` (PASS, 12 of 12 runs, largest relative difference 1.0e-13).

## Troubleshooting

| symptom | cause and fix |
|---|---|
| `ArrayMemoryError` in a stage | too many parallel jobs or another heavy process running; lower `--jobs` and re-run (stages resume) |
| a stage refuses with "lock exists" | intended; see the first section |
| `IndexError` from `r3_verification.py` run by hand | it needs a regime argument; run it through `pipeline.py --stage verify` |
| figures stage: "No objects to concatenate" | the figure script was ported from a four-regime state; Rajasthan has three regimes (already fixed, `REG = (0, 1, 2)`) |
| paths with spaces break OpenFOAM | see `rj_openfoam/README.md`; runs happen in WSL under `~/rj_runs` |
