# run_parallel.ps1 - the overlapping parallel waves from 'commands to run.md', as a script.
# Run from the (fresh copy of the) state folder:  powershell -NoProfile -ExecutionPolicy Bypass -File .\run_parallel.ps1
$ErrorActionPreference = "Stop"

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

Write-Host "`nALL WAVES DONE" -ForegroundColor Green
