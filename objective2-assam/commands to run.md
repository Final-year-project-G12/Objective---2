# Commands to run

## Contents

1. [Assam O2: full pipeline](#assam-o2-full-pipeline)
   - [Read this first](#read-this-first)
   - [Step 0: make a fresh working copy](#step-0-make-a-fresh-working-copy)
   - [Option A: one stage at a time](#option-a-one-stage-at-a-time)
   - [Option B: parallel waves](#option-b-parallel-waves)
   - [Watching a run](#watching-a-run)
   - [Why the waves are split this way](#why-the-waves-are-split-this-way)
2. [Troubleshooting](#troubleshooting)

---

## Assam O2: full pipeline

All commands are **PowerShell**, run from the `objective2-assam` folder. This is the Assam version of
`../objective2-rajasthan/commands to run.md`, but **Assam is not on the Rajasthan/Tamil Nadu gate chain** (g2-g24). It is
the older phase chain (Phases 2-8: geometry, simulate, verify, DOE, surrogate, optimise, robustness, hand-off, plots), so there is
no S1/S2/S4/S5 search to spread over many processes and the whole chain is short.

### Read this first

- **What this run is.** The legacy Assam method: single-node tank, 300 s step, a Phase 6 Extra Trees surrogate and a bespoke
  Phase 7 script (`scripts/run_phase7_optimization.py`). It is **not** the current method (NSGA-II, active learning, held-out
  test); the README lists re-running Assam on the current method as an open decision (c). There is no held-out lock and no
  g-chain result for Assam.
- **Known problems that a rerun does not fix.** `results/phase7_optimization_report.md` reports "PASSED" for temperature safety
  against 95 C / 90 C limits, not the frozen 75 C / 65 C; the old selected designs exceeded the 65 C PCM limit (README, "Corrections
  applied 2026-11-10"). Check `phase7_deployable_design_per_regime.csv` against 65 C before using any design. The O1 inputs in
  `data/objective1/` are the older 129-point set, not O1's current 80-point result.
- **Run in a fresh copy (Step 0), not in place.** Every phase rewrites its files in `results/` (DOE, surrogate, Phase 7, Phase 8,
  plots). The copy keeps the existing Assam results as they are.
- **Time:** the DOE is 165 cases; the saved `runtime_s` add up to about 3 minutes in one process. Phase 8a uses 6 worker
  processes (`N_JOBS = 6` in `src/robustness/monte_carlo.py`). The saved runs were not timed end to end here.
- **This machine:** 15.6 GB RAM, about 2 GB free with other apps open. The helper waits while free RAM is under 700 MB.

### Step 0: make a fresh working copy

```powershell
$src = (Get-Location).Path                  # run this from the objective2-assam folder
$dst = "$src-fresh"                         # sibling folder, e.g. objective2-assam-fresh
robocopy $src $dst /E /XD "results_backup_*" "__pycache__" "logs" /XF "*.pyc" /NFL /NDL /NJH /NJS /NP | Out-Null   # exit codes 0-7 are fine
Set-Location $dst
Get-ChildItem results -File | Where-Object { $_.Name -notlike "b5_local_hour_check*" } | Remove-Item
Get-ChildItem results -Directory | Remove-Item -Recurse -Force
Set-Content max_parallel.txt "4"            # live limit on parallel jobs (see "Watching a run")
```

The copy keeps only `b5_local_hour_check*`; everything else in `results/` is rebuilt by the waves below.

### Option A: one stage at a time

```powershell
python pipeline.py --state assam --stage geometry
python pipeline.py --state assam --stage verify
python pipeline.py --state assam --stage doe
python pipeline.py --state assam --stage surrogate
python scripts/build_phase6_models_and_report.py       # writes models/*.pkl that Phase 7 loads
python scripts/run_phase7_optimization.py              # Phase 7 (bespoke script)
python pipeline.py --state assam --stage robustness    # --mc-draws N to change the 100 draws per regime
python pipeline.py --state assam --stage handoff
python pipeline.py --state assam --stage plots
```

### Option B: parallel waves

Only wave 1 has independent parts (geometry, verify and the DOE do not read each other), and robustness parallelises itself with 6 workers.

**Step 1: paste this helper once per PowerShell window.** Same helper as the other states.

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

**Step 2: run the whole chain.**

```powershell
& {
$S = "--state assam"

# Wave 1: Phase 2 geometry self-test, Phase 4 verification gates and the Phase 5 DOE (165 cases, one process) are independent
Wave 1 { Run-Wave -Max 3 -Jobs "pipeline.py $S --stage geometry", "pipeline.py $S --stage doe", "pipeline.py $S --stage verify" }

# Wave 2: Phase 6 surrogate (pipeline stage), then the Phase 6 model files that Phase 7 loads (models/*.pkl), one after the other
Wave 2 { Run-Wave -Max 1 -Jobs "pipeline.py $S --stage surrogate", "scripts/build_phase6_models_and_report.py" }

# Wave 3: Phase 7 optimisation (bespoke script; needs the Phase 6 models)
Wave 3 { Run-Wave -Max 1 -Jobs "scripts/run_phase7_optimization.py" }

# Wave 4: Phase 8a Monte Carlo robustness (starts 6 worker processes itself), then 8b recommendation cards + Objective 3 contract
Wave 4 { Run-Wave -Max 1 -Jobs "pipeline.py $S --stage robustness", "pipeline.py $S --stage handoff" }

# Wave 5: Phase 2-8 figures (needs plotly + kaleido; they are installed here)
Wave 5 { Run-Wave -Max 1 -Jobs "pipeline.py $S --stage plots" }
}
```

The same text is in `run_parallel.ps1`: `powershell -NoProfile -ExecutionPolicy Bypass -File .\run_parallel.ps1`.

Notes:

- **Wave 2 order matters.** `build_phase6_models_and_report.py` reads `results/phase5_design_cases.parquet`, which wave 1 writes.
- **`handoff`** writes `results/obj3_environment_contract_assam.json` (schema v1) and the recommendation cards. They carry the same
  caveats as before (older O1 inputs, no train/validation/test years); they are not a valid Objective 3 input.

### Watching a run

In a **second** PowerShell window, in the same (fresh) folder:

```powershell
Get-Process python -ErrorAction SilentlyContinue | Measure-Object | Select-Object Count            # how many are running
"{0:N1} GB" -f ((Get-Process python -ErrorAction SilentlyContinue | Measure-Object WorkingSet64 -Sum).Sum / 1GB)   # their total RAM
(Get-Counter '\Memory\Available MBytes').CounterSamples[0].CookedValue                              # free RAM in MB
Get-ChildItem logs | Sort-Object LastWriteTime | Select-Object -Last 5 Name, LastWriteTime          # most recently active logs
Get-Content logs/pipeline_state_assam_stage_doe.out.txt -Tail 5                                                       # tail one log
Set-Content max_parallel.txt "6"                                                                    # change the job limit while running
```

`max_parallel.txt` only **lowers** the limit set by `$M` (8). Raise it step by step while the total RAM stays under about 10 GB.


### Why the waves are split this way

| Script | Needs | Wave |
|---|---|---|
| `pipeline.py --stage geometry` | nothing | 1 |
| `pipeline.py --stage verify` | nothing (runs its own simulator cases) | 1 |
| `pipeline.py --stage doe` | nothing; writes `phase5_design_cases.parquet/.csv` | 1 |
| `pipeline.py --stage surrogate`, `build_phase6_models_and_report.py` | Phase 5 file | 2 |
| `scripts/run_phase7_optimization.py` | `models/*.pkl`, Phase 5 file | 3 |
| `pipeline.py --stage robustness`, `--stage handoff` | `phase7_deployable_design_per_regime.csv` | 4 |
| `pipeline.py --stage plots` | everything above | 5 |

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
| Plots fail with a `kaleido` / `plotly` error | `pip install plotly kaleido`; both import fine on this machine. |
| Phase 4 `verify` exits 1 | Read `results/phase4_simulator_verification_report_assam.txt`. The exit code is 0 only when the overall verdict is GO (the saved run was GO with Gate 3 failing: plain water beat every PCM). |
