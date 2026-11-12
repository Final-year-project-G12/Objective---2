# Commands to run

## Contents

1. [Rajasthan O2: full pipeline, as fast as possible](#rajasthan-o2-full-pipeline-as-fast-as-possible)
   - [Read this first](#read-this-first)
   - [Option A: one command (simple, slower)](#option-a-one-command-simple-slower)
   - [Option B: overlapping parallel waves (fastest)](#option-b-overlapping-parallel-waves-fastest)
   - [Watching a run](#watching-a-run)
   - [Why the waves are split this way](#why-the-waves-are-split-this-way)
2. [OpenFOAM / ParaView](#openfoam--paraview)
3. [Troubleshooting](#troubleshooting)

---

## Rajasthan O2: full pipeline, as fast as possible

All commands are **PowerShell**, run from the `objective2-rajasthan` folder.

### Read this first

- **A full rerun overwrites the frozen designs.** It rewrites the outputs of `baseline`, `screening`, `doe`,
  `surrogate`, `band`, `optimize` and `select` in `results/`. The held-out test (`g10_heldout_results.csv`, 2011–2015)
  was run on the *current* designs, so after a rerun it no longer describes the designs you have.
- **Never run `scripts/g10_test.py`.** The one-shot held-out test is spent; `results/held_out_test.lock` is set.
- **Back up `results/` first.** Calling the scripts directly (Option B) skips the lock check in `pipeline.py`.
  ```powershell
  Copy-Item -Recurse results "results_backup_$(Get-Date -Format yyyyMMdd_HHmm)"
  ```
  Or, safer: copy the whole `objective2-rajasthan` folder and run the commands inside the copy. All paths are
  relative, so a copy works without any changes.
- **This machine:** i5-1340P, 12 cores / 16 threads (4 performance + 8 efficiency cores), 15.6 GB RAM.
  Every simulator script uses **one core**, so the speed-up comes from running many scripts at once.
  The limit is RAM: 9 parallel jobs ran out of memory once (README). Start with **8 at a time**. If wave 2 stays
  under about 10 GB in total (see [Watching a run](#watching-a-run)), you can raise it to 10–12. More than 12
  gains little on this CPU.
- **Check the code works before the long run** (about 2 minutes):
  ```powershell
  python -m pytest -q tests
  $env:G9_FAST="1"; python scripts/g9_s4_s5.py 0 1; Remove-Item Env:G9_FAST    # optimiser smoke test, writes to results/_smoke/
  ```

### Option A: one command (simple, slower)

```powershell
python pipeline.py --state rajasthan --stage all --dry-run                      # print the plan, run nothing
python pipeline.py --state rajasthan --stage all --allow-invalidate --jobs 8    # the real run
```

`--jobs 8` runs up to 8 scripts at once **inside** a stage, but each stage still waits for the previous one to
finish. It stops at the first failure and never runs `heldout`. Run `python run_all_rajasthan.py` at the end
for the tests and `status`.

### Option B: overlapping parallel waves (fastest)

This version also runs **independent stages at the same time**. For example, the dense grid (S6), Taguchi screening
(S1) and sensitivity (G7) all run alongside the Sobol DOE (S2), which takes several hours, instead of waiting for it.

**Step 1: paste this helper once per PowerShell window.** `Run-Wave` starts the jobs, keeps at most `-Max` running,
waits until all of them have finished, and stops with an error if any of them failed. Logs go to `logs/`.

```powershell
# one BLAS thread per process, so 8 processes don't each start 16 threads and slow each other down
$env:OMP_NUM_THREADS="1"; $env:MKL_NUM_THREADS="1"; $env:OPENBLAS_NUM_THREADS="1"
New-Item -ItemType Directory -Force logs | Out-Null

function Run-Wave {
    param([string[]]$Jobs, [int]$Max = 8, [hashtable]$Env = @{}, [string]$Tag = "")
    foreach ($k in $Env.Keys) { Set-Item "Env:$k" $Env[$k] }
    $procs = @()
    foreach ($j in $Jobs) {
        while (@($procs | Where-Object { -not $_.HasExited }).Count -ge $Max) { Start-Sleep -Seconds 5 }
        $name = $Tag + (($j -replace '^scripts/', '' -replace '\.py', '' -replace '\W+', '_').Trim('_'))
        $p = Start-Process python -ArgumentList $j -NoNewWindow -PassThru `
             -RedirectStandardOutput "logs/$name.out.txt" -RedirectStandardError "logs/$name.err.txt"
        $null = $p.Handle                       # keeps ExitCode readable in Windows PowerShell 5.1
        $p | Add-Member NoteProperty Job $j
        $procs += $p
        Write-Host ("{0:HH:mm}  started  {1}" -f (Get-Date), $j)
    }
    foreach ($p in $procs) { $p.WaitForExit() }
    foreach ($k in $Env.Keys) { Remove-Item "Env:$k" }
    $bad = @($procs | Where-Object { $_.ExitCode -ne 0 })
    if ($bad.Count) {
        $bad | ForEach-Object { Write-Host "FAILED (exit $($_.ExitCode)): $($_.Job)" -ForegroundColor Red }
        throw "wave failed; see the matching logs/*.err.txt"
    }
    Write-Host ("{0:HH:mm}  wave done ({1} jobs)" -f (Get-Date), $Jobs.Count) -ForegroundColor Green
}
```

**Step 2: run the whole chain.** Paste the block as a whole. The `& { ... }` wrapper makes it stop at the
first failed wave instead of carrying on.

```powershell
& {
$M = 8                                     # max parallel jobs; raise to 10-12 only if RAM allows
$P = foreach ($r in 0,1,2) { foreach ($k in 1,2,3) { "$r $k" } }       # the 9 (regime, PCM rank) pairs

# Wave 1: no inputs needed. Water-only baseline (everything else needs it) + G6 verification
Run-Wave -Max $M -Jobs (@(0,1,2 | % { "scripts/g8_build_plain_baseline.py $_" }) + "scripts/g6_phase4_o1.py")

# Wave 2: needs only the baseline. S2 DOE (longest, so it starts first), S6 dense grid, S1 screening, G7 sensitivity
Run-Wave -Max $M -Jobs (@($P | % { "scripts/g8_s2_doe.py $_" }) +
                        @(0,1,2 | % { "scripts/g9_s6_grid.py $_ 1" }) +
                        @($P | % { "scripts/g8_s1_screening.py $_" }) +
                        @(0,1,2 | % { "scripts/g7_sensitivity.py $_" }))

# Wave 3: S2 repair pass + G7 flow/packing supplement (reads the G7 output)
Run-Wave -Max $M -Jobs "scripts/g8_s2_repair.py", "scripts/g7_flow_baseline_and_packing.py"

# Wave 4: S3 surrogate comparison, alone: it starts 9 worker processes itself
Run-Wave -Max 1 -Jobs "scripts/g8_s3_compare.py"

# Wave 5: S4/S5 NSGA-II + active learning (9 pairs, 40-80 min each) + WP6 repeatability band
Run-Wave -Max $M -Jobs (@($P | % { "scripts/g9_s4_s5.py $_" }) + @(0,1,2 | % { "scripts/g9_band.py $_" }))

# Wave 6: box-vertex step + 3 more rounds, continuing each pair's saved state (writes the *_ext2 files)
Run-Wave -Max $M -Tag "ext2_" -Env @{ G9_WARM = "1"; G9_VERTICES = "1" } -Jobs @($P | % { "scripts/g9_s4_s5.py $_" })

# Wave 7: G9 assessment, then G10 final selection on the select years 2021-2023
Run-Wave -Max 1  -Jobs "scripts/g9_assess.py"
Run-Wave -Max $M -Jobs @(0,1,2 | % { "scripts/g10_select.py $_" })

# Wave 8: G11 ablations + the diagnostics that read the new g10_selection files (G13-G17, G20-G22)
Run-Wave -Max $M -Jobs (@(0,1,2 | % { "scripts/g11_ablation.py $_" }) +
                        @("g20_gp_bo_comparison", "g13_issue4_shield_split", "g14_issue5_controls", "g15_issue6_anchor",
                          "g16_issue3_serve", "g17_issue2_widen", "g21_sizing_study", "g22_sensitivity_extra" |
                          % { $s = $_; 0,1,2 | % { "scripts/$s.py $_" } }))

# Wave 9: tests, results registry, generated docs, doc check, Objective 3 hand-off, plots, status
python run_all_rajasthan.py
}
```

Notes:

- **Running one wave at a time.** Each `Run-Wave` line also works on its own. If one fails, fix the cause and
  rerun from that wave; earlier waves don't need repeating. If you do this, set `$M` and `$P` first (the first
  two lines inside the block).
- **Wave 8 is optional.** It adds 24 diagnostic jobs (G20 is the slowest, about 15–20 min per regime). If you only
  need the main chain, keep the `g11_ablation` part and delete the rest of that wave. `g17_issue2_widen.py`
  overwrites `g17_widen_r*.csv`, which `docs/04` section 5e quotes as a v1 diagnostic, so that section needs
  relabelling after it runs.
- **G18 is left out on purpose.** It needs a separate 9-pair "no-vertex" run in `results/issue1_novert/` (see
  README, section "Issue diagnostics").
- **Not measured:** the total time. The stage times in the README (S2 "hours", optimize "many hours") were measured
  with 3 jobs. With 8 jobs and the overlaps above, expect the run to be limited by wave 2 (S2) and waves 5–6
  (S4/S5), but I haven't timed it.

### Watching a run

In a **second** PowerShell window, in the same folder:

```powershell
Get-Process python -ErrorAction SilentlyContinue | Measure-Object | Select-Object Count            # how many are running
"{0:N1} GB" -f ((Get-Process python -ErrorAction SilentlyContinue | Measure-Object WorkingSet64 -Sum).Sum / 1GB)   # their total RAM
Get-ChildItem logs | Sort-Object LastWriteTime | Select-Object -Last 5 Name, LastWriteTime          # most recently active logs
Get-Content logs/g8_s2_doe_0_1.out.txt -Tail 5                                                       # tail one log
python pipeline.py --state rajasthan --stage status                                                 # which outputs exist
```

If the total RAM gets close to 14 GB, stop with `Ctrl+C` in the first window (or `Stop-Process -Name python`),
lower `$M`, and rerun from the wave that was interrupted.

### Why the waves are split this way

What each script reads (checked in the code):

| Script | Needs | Wave |
|---|---|---|
| `g8_build_plain_baseline.py`, `g6_phase4_o1.py` | nothing | 1 |
| `g8_s1_screening.py`, `g8_s2_doe.py`, `g9_s6_grid.py` | baseline (through `evaluate_design`) | 2 |
| `g7_sensitivity.py` | nothing (could go in wave 1; in wave 2 it fills free cores while S2 runs) | 2 |
| `g8_s2_repair.py` | all 9 S2 files | 3 |
| `g7_flow_baseline_and_packing.py` | G7 sensitivity | 3 |
| `g8_s3_compare.py` | repaired S2 files | 4 |
| `g9_band.py` | baseline + repaired S2 (rank 1) | 5 |
| `g9_s4_s5.py` | S2 + `g8_s3_selection.csv` | 5 |
| `g9_s4_s5.py` with `G9_WARM=1 G9_VERTICES=1` | that pair's wave-5 state | 6 |
| `g9_assess.py` | band, all `g9_points_*`, S6 grid | 7 |
| `g10_select.py` | `g9_points_*`, band | 7 |
| `g11_ablation.py`, G13–G17, G20–G22 | `g10_selection_r*.json`, band | 8 |
| `run_all_rajasthan.py` (report, handoff, plots) | everything above | 9 |

Compared with Option A, the time saved comes from: S6 and S1 no longer waiting for S2 to finish, G7 running in the
gaps, band running alongside S4/S5, and more jobs at once (8 instead of 3).

---

## OpenFOAM / ParaView

> **Note:** these commands have not been run from here. They write into `openfoam_cfd/`, which is outside this
> project, and the GUI commands open windows on your screen. Run them yourself in your WSL shell.
> The Rajasthan simulator does **not** read any CFD result yet; it still uses the lumped `r/(5k)` closure with
> `liquid_convection_enhancement: 2.0`.

### Setup

Set these two variables before running any block below:

```bash
OF="/mnt/d/Final Year Project/OBJECTIVE2/Objective---2/openfoam_cfd"
PV="/mnt/d/Program Files/ParaView 6.2.0/bin"
```

`wslpath -w` (used below) turns a Linux path into the Windows path that `paraview.exe` needs. After ParaView opens,
press the green **Play** button.

### Case 1: capsule melting (RT44HC, 60 mm)

```bash
"$PV/paraview.exe" --state="$(wslpath -w "$OF/cases_viz/rt44_d060/rt44_d060_T.pvsm")" &
```

| | |
|---|---|
| **What is simulated** | One aluminium sphere, 60 mm in diameter, filled with RT44HC. Water 15 K above the melting point flows past it at 0.03 kg/s. |
| **Colours** | Temperature (K). The saved state colours by T; for liquid fraction, use the PNG snapshots or `capsule_paraview.py`. |
| **Geometry** | A thin 5° wedge of the sphere. Add the **Reflect** filter to see the full shape. |

**What happens over time**

- The PCM melts from the outside inward.
- The top melts first because liquid wax rises; the cooler solid core sinks to the bottom.
- Melt times from `kpi.json`: 50 % melted at about 1,000 s, 90 % at about 1,890 s, 99 % at about 2,240 s.
  The README says a 60 mm capsule is fully melted in about 40 minutes.

**Why it matters:** the Rajasthan simulator models the inside of a capsule with a simple formula, r/(5k) with a
convection factor of 2. This CFD solves the melting and natural convection directly; comparing the two gives a
correction factor (the closure in `cfd_closure_v1.yaml`, not yet validated).

### Case 2: tank charge

```bash
"$PV/paraview.exe" --state="$(wslpath -w "$OF/cases_tank/charge/charge_T.pvsm")" &
```

| | |
|---|---|
| **What it shows** | A water tank filling with hot water from the top port, 0–3,600 s (31 steps). |
| **Colours** | Water temperature. |

**What you should see:** a hot layer grows downward from the top, with a sharp boundary (thermocline) between hot
and cold water. The outlet stays cold until about 24 minutes. This layering is why the Rajasthan model uses a 10-node
stratified tank instead of one mixed temperature.

### Case 3: tank draw

```bash
"$PV/paraview.exe" --state="$(wslpath -w "$OF/cases_tank/draw/draw_T.pvsm")" &
```

**What it shows:** hot water being drawn off, i.e. the user's hot-water use. The hot layer shrinks, and a cold plume
rises along the axis from the bottom inlet port. This mixing lowers the delivered temperature.

### Case 4: collector riser

```bash
"$PV/paraview.exe" --state="$(wslpath -w "$OF/cases_collector/test_T30/collector_T.pvsm")" &
```

| | |
|---|---|
| **What it shows** | A strip of the solar collector riser over 5 time steps, with the cross-section stretched 12× so it is visible. |
| **What you should see** | The plate and fin hot, the channel core cooler near the outlet, and the water warming along the length. |
| **Regions** | Separate water and copper regions. When opening the case by hand, tick `/water/internalMesh` and `/copper/internalMesh`. |

### Pictures without the GUI

```bash
cd "$OF/scripts" && python.exe plot_capsule_fields.py ../cases_viz/rt44_d060 --times 0 300 600 900 1200 1800 2400
```

This writes two PNGs into `cases_viz/rt44_d060/` and **overwrites** the ones already there
(`snapshots_liquid_fraction.png`, `snapshots_temperature.png`). To just look at them, open those files; no command
is needed. `python.exe` is Windows Python, which has the packages the README lists.

### Making a new animatable case

```bash
cd "$OF/scripts"
python.exe viz_case.py --name om49_d055 --pcm "savE® OM49" --d 0.055 --mdot 0.03 --dT 15 --t-end-h 1.5
"$PV/pvbatch.exe" make_pv_state.py tank "..\\cases_viz\\om49_d055\\om49_d055.foam" "..\\cases_viz\\om49_d055\\om49_d055.pvsm" 300 335
"$PV/paraview.exe" --state="$(wslpath -w "$OF/cases_viz/om49_d055/om49_d055.pvsm")" &
```

`viz_case.py` runs the solver inside Ubuntu-24.04 with OpenFOAM v2406, and the case takes a while. The doubled `\\`
in the `pvbatch` line is needed in bash.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| A wave prints `FAILED (exit 1)` | Open the matching `logs/<script>_<args>.err.txt`. Fix it, then rerun from that wave. |
| Out of memory / PC freezes during a wave | Lower `$M` (for example to 6) and rerun that wave. |
| `refusing [...]: results/held_out_test.lock exists` | Option A without `--allow-invalidate`. Expected; add the flag only if you mean to re-decide the designs. |
| `ModuleNotFoundError: src` | You are not in the `objective2-rajasthan` folder. `cd` there and rerun. |
| A `G9_*` variable leaks into a later run | `Remove-Item Env:G9_WARM, Env:G9_VERTICES, Env:G9_MAX_ROUNDS, Env:G9_OUTDIR -ErrorAction SilentlyContinue` |
| `g12_verify_docs.py` exits 1 (wave 9) | A doc names a file or function that does not exist; fix the doc (or the name) it prints. |
| `.exe` not found (WSL) | Check that `ls "$PV/paraview.exe"` finds the file. |
| ParaView opens blank | Press **Reset Camera**, then **Play**. |
| `python.exe` reports missing packages | Install the packages the README lists: `numpy scipy pandas scikit-learn pyyaml`. |
| Windows line endings in a `.sh` file | `sed -i 's/\r$//' run_one.sh` (in WSL). |
