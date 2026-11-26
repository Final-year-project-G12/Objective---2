# run_parallel.ps1 - the overlapping parallel waves from 'commands to run.md', as a script.
# Run from the (fresh copy of the) state folder:  powershell -NoProfile -ExecutionPolicy Bypass -File .\run_parallel.ps1
$ErrorActionPreference = "Stop"

# one BLAS thread per process, so several processes don't each start 16 threads and slow each other down
$env:OMP_NUM_THREADS="1"; $env:MKL_NUM_THREADS="1"; $env:OPENBLAS_NUM_THREADS="1"
$env:PYTHONIOENCODING="utf-8"; $env:PYTHONUTF8="1"        # the log files hold PCM names with the (R) sign
New-Item -ItemType Directory -Force logs | Out-Null
$DryRun   = $false     # $true: print every job, start nothing
$FromWave = 2          # after a failure: set this to the wave that failed, then paste the chain again

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

$M = 8                                     # max parallel jobs per wave (max_parallel.txt can lower it live)
$P = foreach ($r in 0,1,2,3) { foreach ($k in 1,2,3) { "$r $k" } }     # the 12 (regime, PCM rank) pairs

# Wave 1: no inputs needed. Water-only baseline (everything else needs it) + G6 verification
Wave 1 { Run-Wave -Max $M -Jobs (@(0,1,2,3 | % { "scripts/g8_build_plain_baseline.py $_" }) + "scripts/g6_phase4_o1.py") }

# Wave 2: needs only the baseline. S2 DOE (longest, so it starts first), S6 dense grid, S1 screening, G7 sensitivity
Wave 2 { Run-Wave -Max $M -Jobs (@($P | % { "scripts/g8_s1_screening.py $_" }) +
                                 @(0,1,2,3 | % { "scripts/g7_sensitivity.py $_" })) }   # RESUME: s2_doe and s6_grid already done

# Wave 3: S2 repair pass + G7 flow/packing supplement + the paired G7 file (both read the G7 output)
Wave 3 { Run-Wave -Max $M -Jobs "scripts/g8_s2_repair.py", "scripts/g7_flow_baseline_and_packing.py", "scripts/g7_paired.py" }

# Wave 4: S3 surrogate comparison, alone: it starts 9 worker processes itself
Wave 4 { Run-Wave -Max 1 -Jobs "scripts/g8_s3_compare.py" }

# Wave 5: S4/S5 NSGA-II + active learning (12 pairs, 40-80 min each) + WP6 repeatability band
Wave 5 { Run-Wave -Max $M -Jobs (@($P | % { "scripts/g9_s4_s5.py $_" }) + @(0,1,2,3 | % { "scripts/g9_band.py $_" })) }

# Wave 6: box-vertex step + 3 more rounds, continuing each pair's saved state (writes the *_ext2 files)
Wave 6 { Run-Wave -Max $M -Tag "ext2_" -Env @{ G9_WARM = "1"; G9_VERTICES = "1" } -Jobs @($P | % { "scripts/g9_s4_s5.py $_" }) }

# Wave 7: G9 assessment, then G10 final selection on the select years 2021-2023
Wave 7 { Run-Wave -Max 1  -Jobs "scripts/g9_assess.py"
         Run-Wave -Max $M -Jobs @(0,1,2,3 | % { "scripts/g10_select.py $_" }) }

# Wave 8: G11 ablations + the diagnostics that read the new g10_selection files (G13-G17)
Wave 8 { Run-Wave -Max $M -Jobs (@(0,1,2,3 | % { "scripts/g11_ablation.py $_" }) +
                                 @("g13_issue4_shield_split", "g14_issue5_controls", "g15_issue6_anchor",
                                   "g16_issue3_serve", "g17_issue2_widen" |
                                   % { $s = $_; 0,1,2,3 | % { "scripts/$s.py $_" } })) }

# Wave 9: tests, results registry, generated docs, doc check, Objective 3 hand-off (v2 + v3), plots, status
Wave 9 { Run-Wave -Max 1 -Jobs "run_all_uttarakhand.py" }

Write-Host "`nALL WAVES DONE" -ForegroundColor Green
