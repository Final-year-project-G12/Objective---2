# Commands to run

## Contents

1. [Tamil Nadu O2: full pipeline, as fast as possible](#tamilnadu-o2-full-pipeline-as-fast-as-possible)
   - [Read this first](#read-this-first)
   - [Step 0: make a fresh working copy](#step-0-make-a-fresh-working-copy)
   - [Option A: the existing runner (simple, slower)](#option-a-the-existing-runner-simple-slower)
   - [Option B: overlapping parallel waves (fastest)](#option-b-overlapping-parallel-waves-fastest)
   - [Watching a run](#watching-a-run)
   - [Why the waves are split this way](#why-the-waves-are-split-this-way)
2. [Troubleshooting](#troubleshooting)

---

## Tamil Nadu O2: full pipeline, as fast as possible

All commands are **PowerShell**, run from the `objective2-tamilnadu` folder. This file is the Tamil Nadu version of
`../objective2-rajasthan/commands to run.md`: same waves, same helper, with this state's scripts and sizes
(3 regimes (0-2), 9 (regime, PCM rank) pairs).

### Read this first

- **A full rerun overwrites the frozen designs.** It rewrites the outputs of baseline, screening, DOE, surrogate, band,
  optimize and select in `results/`. The held-out test (`g10_heldout_results.csv`) was run on the *current* designs, so
  after a rerun it no longer describes the designs you have. Years: explore 2016-2020, select 2021-2023, held-out 2011-2015 (spent).
- **Never run `scripts/g10_test.py`.** The one-shot held-out test is spent; `results/held_out_test.lock` is set. Option B calls
  the scripts directly and skips the lock check in the pipeline runner, so this is on you.
- **Run in a fresh copy (Step 0), not in place.** Two things make an in-place rerun pointless or risky: the DOE
  (`g8_s2_doe.py`) and the dense grid (`g9_s6_grid.py`) **resume** from the CSV files already in `results/`, so with the old
  files present they skip everything and finish at once; and the new run overwrites the old results. The copy leaves
  `objective2-tamilnadu` exactly as it is, and the spent held-out files (`g10_heldout_results.csv`, `held_out_test.lock`) are copied
  into it because the hand-off step reads them.
- **This machine:** i5-1340P, 12 cores / 16 threads (4 performance + 8 efficiency cores), 15.6 GB RAM. Every simulator
  script uses **one core** (about 230 MB each in a quick measurement; S4/S5 may use more), so the speed-up comes from running many scripts
  at once. The limit is RAM: 9 parallel jobs ran out of memory once in Rajasthan, and with Chrome and other apps open
  only about 2 GB was free here. The helper below therefore also **waits while free RAM is under 700 MB**, and reads a live
  limit from `max_parallel.txt` (see [Watching a run](#watching-a-run)). Start at 4 and raise it while RAM allows.
  If you run two states at the same time, give each its own `max_parallel.txt` so that the numbers add up to what the machine can take.
- **Check the code works before the long run** (about 2 minutes):
  ```powershell
  python -m pytest -q tests
  ```

### Step 0: make a fresh working copy

```powershell
$src = (Get-Location).Path                  # run this from the objective2-tamilnadu folder
$dst = "$src-fresh"                         # sibling folder, e.g. objective2-tamilnadu-fresh
robocopy $src $dst /E /XD "results_backup_*" "__pycache__" "logs" /XF "*.pyc" /NFL /NDL /NJH /NJS /NP | Out-Null   # exit codes 0-7 are fine
Set-Location $dst
Get-ChildItem results -File | Where-Object { $_.Name -match '^(g7_|g8_|g9_|g10_selection|g11_|g13_|g14_|g15_|g16_|g17_|g20_|g21_|g22_|g23_|g24_|plain_baseline|wp6_|phase4_verification|results_registry|obj3_)' } | Remove-Item
Remove-Item -Recurse -Force results\plots -ErrorAction SilentlyContinue
Set-Content max_parallel.txt "4"            # live limit on parallel jobs (see "Watching a run")
```

The copy keeps the G2/G3/G4 simulator checks and the held-out files; it deletes every output that Option B rewrites
(g7-g11, g13-g17, g20-g24, plain baselines, band, registry, hand-off files, plots). All paths in the project are relative, so the copy
runs without any change. Do everything below inside the copy.

### Option A: the existing runner (simple, slower)

```powershell
python scripts/tn_run_all.py --list                  # the stage list and each stage's shape
python scripts/tn_run_all.py --all --dry-run         # print the commands, run nothing
python scripts/tn_run_all.py --all --workers 8       # the real run; skips g10_test; stops at the first failed stage
```

`scripts/tn_run_all.py` runs the stages one after another and parallelises only **inside** a stage (its logs go to
`results/_log_*.log`). It also runs g2-g4 and g18, which Option B leaves out, and it does **not** run `g8_s2_repair.py`
or `g7_build_paired.py`. It never runs `g10_test` (needs `--i-mean-it`; do not).

### Option B: overlapping parallel waves (fastest)

This version also runs **independent stages at the same time**. For example, the dense grid (S6), Taguchi screening (S1)
and sensitivity (G7) all run alongside the Sobol DOE (S2), which takes hours, instead of waiting for it.

**Step 1: paste this helper once per PowerShell window.** `Run-Wave` starts the jobs, keeps at most `-Max` running
(and fewer if `max_parallel.txt` says so or free RAM is low), waits until all of them have finished, and stops with an error if any
of them failed. `Wave N Ellipsis` runs a wave only when `N >= $FromWave`. Logs go to `logs/`.

```powershell
# one BLAS thread per process, so several processes don't each start 16 threads and slow each other down
$env:OMP_NUM_THREADS="1"; $env:MKL_NUM_THREADS="1"; $env:OPENBLAS_NUM_THREADS="1"
$env:PYTHONIOENCODING="utf-8"; $env:PYTHONUTF8="1"        # the log files hold PCM names with the (R) sign
New-Item -ItemType Directory -Force logs | Out-Null
$DryRun   = $false     # $true: print every job, start nothing
$FromWave = 1          # after a failure: set this to the wave that failed, then paste the chain again

function Run-Wave {
    param([string[]]$Jobs, [int]$Max = 8, [hashtable]$Env = @{}, [string]$Tag = "", [int]$MinFreeMB = 700)
    if ($DryRun) { $Jobs | ForEach-Object { Write-Host "  [dry] $Tag$_" }; return }
    foreach ($k in $Env.Keys) { Set-Item "Env:$k" $Env[$k] }
    $procs = @()
    foreach ($j in $Jobs) {
        while ($true) {
            $limit = $Max
            # max_parallel.txt (one number) is a live upper limit: edit it during a run to slow down or speed up
            if (Test-Path max_parallel.txt) { $cap = [int](Get-Content max_parallel.txt -TotalCount 1); if ($cap -lt $limit) { $limit = $cap } }
            $running = @($procs | Where-Object { -not $_.HasExited }).Count
            try { $free = (Get-Counter '\Memory\Available MBytes').CounterSamples[0].CookedValue } catch { $free = 99999 }
            if ($running -lt $limit -and ($free -ge $MinFreeMB -or $running -eq 0)) { break }   # also waits while RAM is short
            Start-Sleep -Seconds 5
        }
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

# Wave N runs only when N >= $FromWave
function Wave([int]$n, [scriptblock]$Body) { if ($n -ge $FromWave) { Write-Host ("`n=== wave {0}  {1:HH:mm}" -f $n, (Get-Date)); & $Body } }
```

**Step 2: run the whole chain.** Paste the block as a whole. The `& { ... }` wrapper makes it stop at the first failed
wave instead of carrying on.

```powershell
& {
$M = 8                                     # max parallel jobs per wave (max_parallel.txt can lower it live)
$P = foreach ($r in 0,1,2) { foreach ($k in 1,2,3) { "$r $k" } }       # the 9 (regime, PCM rank) pairs

# Wave 1: no inputs needed. Water-only baseline (everything else needs it) + G6 verification
Wave 1 { Run-Wave -Max $M -Jobs (@(0,1,2 | % { "scripts/g8_build_plain_baseline.py $_" }) + "scripts/g6_phase4_o1.py") }

# Wave 2: needs only the baseline. S2 DOE (longest, so it starts first), S6 dense grid, S1 screening, G7 sensitivity
Wave 2 { Run-Wave -Max $M -Jobs (@($P | % { "scripts/g8_s2_doe.py $_" }) +
                                 @(0,1,2 | % { "scripts/g9_s6_grid.py $_ 1" }) +
                                 @($P | % { "scripts/g8_s1_screening.py $_" }) +
                                 @(0,1,2 | % { "scripts/g7_sensitivity.py $_" })) }

# Wave 3: S2 repair pass + G7 flow/packing supplement + the paired G7 file (both read the G7 output)
Wave 3 { Run-Wave -Max $M -Jobs "scripts/g8_s2_repair.py", "scripts/g7_flow_baseline_and_packing.py", "scripts/g7_build_paired.py" }

# Wave 4: S3 surrogate comparison, alone: it starts 9 worker processes itself
Wave 4 { Run-Wave -Max 1 -Jobs "scripts/g8_s3_compare.py" }

# Wave 5: S4/S5 NSGA-II + active learning (9 pairs, 40-80 min each) + WP6 repeatability band
Wave 5 { Run-Wave -Max $M -Jobs (@($P | % { "scripts/g9_s4_s5.py $_" }) + @(0,1,2 | % { "scripts/g9_band.py $_" })) }

# Wave 6: box-vertex step + 3 more rounds, continuing each pair's saved state (writes the *_ext2 files)
Wave 6 { Run-Wave -Max $M -Tag "ext2_" -Env @{ G9_WARM = "1"; G9_VERTICES = "1" } -Jobs @($P | % { "scripts/g9_s4_s5.py $_" }) }

# Wave 7: G9 assessment, then G10 final selection on the select years 2021-2023
Wave 7 { Run-Wave -Max 1  -Jobs "scripts/g9_assess.py"
         Run-Wave -Max $M -Jobs @(0,1,2 | % { "scripts/g10_select.py $_" }) }

# Wave 8: G11 ablations + the diagnostics that read the new g10_selection files (G13-G17, G20-G24)
Wave 8 { Run-Wave -Max $M -Jobs (@(0,1,2 | % { "scripts/g11_ablation.py $_" }) +
                                 @("g20_gp_bo_comparison", "g13_issue4_shield_split", "g14_issue5_controls", "g15_issue6_anchor",
                                   "g16_issue3_serve", "g17_issue2_widen", "g21_sizing_study", "g22_sensitivity_extra",
                                   "g23_chen_benchmark", "g24_flow_fr_study" |
                                   % { $s = $_; 0,1,2 | % { "scripts/$s.py $_" } })) }

# Wave 9, one job at a time and in this order: tests, results registry, results document, Objective 3 hand-off, plots, doc check
Wave 9 { Run-Wave -Max 1 -Jobs "-m pytest -q tests", "scripts/g12_registry.py", "scripts/g12_results_doc.py",
                                "scripts/g25_obj3_contract.py", "make_all_plots.py", "scripts/g12_verify_docs.py" }
}
```

The same text is in `run_parallel.ps1` (generated from this file's blocks): `powershell -NoProfile -ExecutionPolicy Bypass -File .\run_parallel.ps1`.
Set `$DryRun = $true` first to print every job without starting anything.

Notes:

- **Running one wave at a time.** Each `Wave N` line also works on its own, or set `$FromWave = N` to continue after a failure.
  Earlier waves do not need repeating. If you paste a single wave, set `$M` and `$P` first.
- **Wave 8 is optional.** It adds 30 diagnostic jobs (G20 is the slowest). For the main chain only, keep the `g11_ablation`
  part and delete the rest of that wave. `g17_issue2_widen.py` overwrites `g17_widen_r*.csv`.
- **Left out on purpose:** G2/G3/G4 (simulator checks, their saved files are kept in the copy), G18 (needs a separate
  no-vertex run, `results/issue1_novert/`, kept from the original), G19 and the `tn*_` data-rebuild scripts (weather is
  already built).
- **Not measured:** the total time. The stage times in the README were measured with 3 jobs. Expect the run to be limited by wave 2
  (S2) and waves 5-6 (S4/S5).
- **Hand-off:** wave 9 rebuilds `results/obj3_environment_contract_tamilnadu_v3.json` from the *new* designs. It still reads the old held-out files, so
  treat it as a draft for Objective 3, not as validated.

### Watching a run

In a **second** PowerShell window, in the same (fresh) folder:

```powershell
Get-Process python -ErrorAction SilentlyContinue | Measure-Object | Select-Object Count            # how many are running
"{0:N1} GB" -f ((Get-Process python -ErrorAction SilentlyContinue | Measure-Object WorkingSet64 -Sum).Sum / 1GB)   # their total RAM
(Get-Counter '\Memory\Available MBytes').CounterSamples[0].CookedValue                              # free RAM in MB
Get-ChildItem logs | Sort-Object LastWriteTime | Select-Object -Last 5 Name, LastWriteTime          # most recently active logs
Get-Content logs/g8_s2_doe_0_1.out.txt -Tail 5                                                       # tail one log
Set-Content max_parallel.txt "6"                                                                    # change the job limit while running
```

`max_parallel.txt` only **lowers** the limit set by `$M` (8). Raise it step by step while the total RAM stays under about 10 GB.


### Why the waves are split this way

What each script reads (checked in the code):

| Script | Needs | Wave |
|---|---|---|
| `g8_build_plain_baseline.py`, `g6_phase4_o1.py` | nothing | 1 |
| `g8_s1_screening.py`, `g8_s2_doe.py`, `g9_s6_grid.py` | baseline (through `evaluate_design`) | 2 |
| `g7_sensitivity.py` | nothing (fills free slots while S2 runs) | 2 |
| `g8_s2_repair.py` | all 9 S2 files | 3 |
| `g7_flow_baseline_and_packing.py`, `g7_build_paired.py` | G7 sensitivity | 3 |
| `g8_s3_compare.py` | repaired S2 files | 4 |
| `g9_band.py` | baseline + repaired S2 (rank 1) | 5 |
| `g9_s4_s5.py` | S2 + `g8_s3_selection.csv` | 5 |
| `g9_s4_s5.py` with `G9_WARM=1 G9_VERTICES=1` | that pair's wave-5 state | 6 |
| `g9_assess.py` | band, all `g9_points_*`, S6 grid | 7 |
| `g10_select.py` | `g9_points_*`, band | 7 |
| `g11_ablation.py`, G13-G17, G20-G24 | `g10_selection_r*.json`, band | 8 |
| `g12_*`, `g25_obj3_contract.py`, `make_all_plots.py` | everything above (`g25` also reads the saved held-out files) | 9 |

Compared with Option A, the time saved comes from: S6 and S1 no longer waiting for S2 to finish, G7 running in the gaps,
band running alongside S4/S5, and more jobs at once.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| A wave prints `FAILED (exit 1)` | Open the matching `logs/<script>_<args>.err.txt`. Fix it, set `$FromWave` to that wave number, paste the chain again. |
| Out of memory / PC freezes during a wave | `Set-Content max_parallel.txt "3"` (takes effect within 5 s), or stop with `Stop-Process -Name python` and rerun from that wave. |
| `ModuleNotFoundError: src` | You are not in the state folder. `cd` there and rerun. |
| A `G9_*` variable leaks into a later run | `Remove-Item Env:G9_WARM, Env:G9_VERTICES, Env:G9_MAX_ROUNDS, Env:G9_OUTDIR -ErrorAction SilentlyContinue` |
| `UnicodeEncodeError` in a log | The helper sets `PYTHONIOENCODING=utf-8`; if you start a job by hand, set it too. |
| `running scripts is disabled` | `powershell -NoProfile -ExecutionPolicy Bypass -File .\run_parallel.ps1` |
| `g12_verify_docs.py` exits 1 (wave 9) | A doc names a file or function that does not exist; fix the doc (or the name) it prints. |
