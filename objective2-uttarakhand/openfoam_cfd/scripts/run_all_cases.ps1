# run_all_cases.ps1 -- run every Uttarakhand OpenFOAM case in WSL, post-process it and make the ParaView files.
#
#   cd objective2-uttarakhand\openfoam_cfd\scripts
#   python make_uttarakhand_cases.py                    # (re)write the cases from the saved O2 results
#   .\run_all_cases.ps1                                 # everything
#   .\run_all_cases.ps1 -Only capsule                   # capsule | viz | tank
#
# Needs: WSL with OpenFOAM v2406 at /usr/lib/openfoam/openfoam2406 (distribution name in $env:O2_WSL_DISTRO,
# default Ubuntu-24.04), Windows Python with numpy/matplotlib/pyyaml, and ParaView (pvbatch.exe) for the images and
# .pvsm state files ($env:PVBATCH, default "D:\Program Files\ParaView 6.2.0\bin\pvbatch.exe"; skipped if not found).
# Run time (shared set-up): a capsule case minutes to tens of minutes; a tank case about 75 min per simulated hour.
param([ValidateSet("all", "capsule", "viz", "tank")] [string]$Only = "all")

$ErrorActionPreference = "Continue"
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $Here
$Distro = if ($env:O2_WSL_DISTRO) { $env:O2_WSL_DISTRO } else { "Ubuntu-24.04" }
$PvBatch = if ($env:PVBATCH) { $env:PVBATCH } else { "D:\Program Files\ParaView 6.2.0\bin\pvbatch.exe" }
$HavePv = Test-Path $PvBatch

function To-Wsl([string]$p) {
    $full = (Resolve-Path $p).Path -replace '\\', '/'
    return "/mnt/" + $full.Substring(0, 1).ToLower() + $full.Substring(2)
}

function Run-Wsl([string]$script, [string]$case) {
    wsl -d $Distro -e bash (To-Wsl (Join-Path $Here $script)) (To-Wsl $case)
    return $LASTEXITCODE
}

if ($Only -in @("all", "capsule")) {
    foreach ($c in Get-ChildItem (Join-Path $Root "cases") -Directory) {
        Write-Host "== capsule $($c.Name)"
        if ((Run-Wsl "run_one.sh" $c.FullName) -eq 0) {
            python (Join-Path $Here "postprocess.py") $c.FullName --window-h 6
        }
    }
}

if ($Only -in @("all", "viz")) {
    foreach ($c in Get-ChildItem (Join-Path $Root "cases_viz") -Directory) {
        Write-Host "== viz $($c.Name)"
        if ((Run-Wsl "viz_run.sh" $c.FullName) -eq 0) {
            python (Join-Path $Here "plot_capsule_fields.py") $c.FullName
            if ($HavePv) {
                & $PvBatch (Join-Path $Here "capsule_paraview.py") (Join-Path $c.FullName "$($c.Name).foam") (Join-Path $c.FullName "paraview")
            }
        }
    }
}

if ($Only -in @("all", "tank")) {
    foreach ($c in Get-ChildItem (Join-Path $Root "cases_tank") -Directory) {
        Write-Host "== tank $($c.Name)"
        if ((Run-Wsl "tank_run.sh" $c.FullName) -eq 0) {
            python (Join-Path $Here "tank_postprocess.py") $c.FullName --T-target 50
            if ($HavePv) {
                $foam = Join-Path $c.FullName "$($c.Name).foam"
                & $PvBatch (Join-Path $Here "component_paraview.py") tank $foam (Join-Path $c.FullName "paraview")
                & $PvBatch (Join-Path $Here "make_pv_state.py") tank $foam (Join-Path $c.FullName "$($c.Name)_T.pvsm")
            }
        }
    }
}

if (-not $HavePv) { Write-Host "pvbatch not found at $PvBatch : ParaView images and .pvsm files skipped (set `$env:PVBATCH)." }
python (Join-Path $Here "summarise_results.py")
