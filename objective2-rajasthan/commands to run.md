# OpenFOAM / ParaView commands

> **Note:** these commands have not been run from here. They write into `openfoam_cfd/`, which is outside this
> project, and the GUI commands open windows on your screen. Run them yourself in your WSL shell.

## Contents

1. [Setup](#setup)
2. [Viewing the saved cases in ParaView](#viewing-the-saved-cases-in-paraview)
   - [Case 1: capsule melting (RT44HC, 60 mm)](#case-1-capsule-melting-rt44hc-60-mm)
   - [Case 2: tank charge](#case-2-tank-charge)
   - [Case 3: tank draw](#case-3-tank-draw)
   - [Case 4: collector riser](#case-4-collector-riser)
3. [Pictures without the GUI](#pictures-without-the-gui)
4. [Making a new animatable case](#making-a-new-animatable-case)
5. [Troubleshooting](#troubleshooting)

## Setup

Set these two variables before running any block below:

```bash
OF="/mnt/d/Final Year Project/OBJECTIVE2/Objective---2/openfoam_cfd"
PV="/mnt/d/Program Files/ParaView 6.2.0/bin"
```

`wslpath -w` (used below) turns a Linux path into the Windows path that `paraview.exe` needs. After ParaView opens,
press the green **Play** button.

## Viewing the saved cases in ParaView

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
correction factor (the closure in `cfd_closure_v1.yaml`).

### Case 2: tank charge

```bash
"$PV/paraview.exe" --state="$(wslpath -w "$OF/cases_tank/charge/charge_T.pvsm")" &
```

| | |
|---|---|
| **What it shows** | A water tank filling with hot water from the top port, 0–3,600 s (31 steps). |
| **Colours** | Water temperature. |

**What you should see**

- A hot layer grows downward from the top, with a sharp boundary (thermocline) between hot and cold water.
- The outlet stays cold until about 24 minutes.

This layering is why the Rajasthan model uses a 10-node stratified tank instead of one mixed temperature.

### Case 3: tank draw

```bash
"$PV/paraview.exe" --state="$(wslpath -w "$OF/cases_tank/draw/draw_T.pvsm")" &
```

**What it shows:** hot water being drawn off, i.e. the user's hot-water use.

**What you should see**

- The hot layer shrinks.
- A cold plume rises along the axis from the bottom inlet port. This mixing lowers the delivered temperature.

### Case 4: collector riser

```bash
"$PV/paraview.exe" --state="$(wslpath -w "$OF/cases_collector/test_T30/collector_T.pvsm")" &
```

| | |
|---|---|
| **What it shows** | A strip of the solar collector riser over 5 time steps, with the cross-section stretched 12× so it is visible. |
| **What you should see** | The plate and fin hot, the channel core cooler near the outlet, and the water warming along the length. |
| **Regions** | Separate water and copper regions. When opening the case by hand, tick `/water/internalMesh` and `/copper/internalMesh`. |

## Pictures without the GUI

```bash
cd "$OF/scripts" && python.exe plot_capsule_fields.py ../cases_viz/rt44_d060 --times 0 300 600 900 1200 1800 2400
```

- This writes two PNGs into `cases_viz/rt44_d060/`. That folder already holds them, so **they are overwritten**.
- `python.exe` is Windows Python, which has the packages the README lists.
- To just look at the existing pictures, open `snapshots_liquid_fraction.png` and `snapshots_temperature.png` in
  that folder; no command is needed.

## Making a new animatable case

```bash
cd "$OF/scripts"
python.exe viz_case.py --name om49_d055 --pcm "savE® OM49" --d 0.055 --mdot 0.03 --dT 15 --t-end-h 1.5
"$PV/pvbatch.exe" make_pv_state.py tank "..\\cases_viz\\om49_d055\\om49_d055.foam" "..\\cases_viz\\om49_d055\\om49_d055.pvsm" 300 335
"$PV/paraview.exe" --state="$(wslpath -w "$OF/cases_viz/om49_d055/om49_d055.pvsm")" &
```

- **WSL:** `viz_case.py` runs the solver inside Ubuntu-24.04 with OpenFOAM v2406.
- **Run time:** the case takes a while to run.
- **Backslashes:** the doubled `\\` in the `pvbatch` line is needed in bash.

## Troubleshooting

| Problem | Fix |
|---|---|
| `.exe` not found | Check that `ls "$PV/paraview.exe"` finds the file. |
| ParaView opens blank | Press **Reset Camera**, then **Play**. |
| `python.exe` reports missing packages | Install the packages the README lists: `numpy scipy pandas scikit-learn pyyaml`. |
| Windows line endings in a `.sh` file | Fix with `sed -i 's/\r$//' run_one.sh` (from the README). |
You have 16 cores, so you can run all 9 (regime, PCM) pairs at once. Each script takes `<regime> <pcm_rank>` (regime 0–2, rank 1–3). Run these from the `objective2-rajasthan` folder.

Two warnings first:
- **These re-run the stages that decide the final designs.** They write straight into `results/` and overwrite the current files. The held-out lock only protects you when you go through `pipeline.py`, not when you call a script directly. Back up `results/` before you start, or set `G9_OUTDIR=results_new` for the active-learning step.
- **Don't run `g10_test.py`.** It's the one-shot held-out test, and the lock is already set.

Each of the 9 processes runs on one core, so more than 9 at a time buys nothing.

**Step 1: Taguchi screening (S1), 9 pairs in parallel (PowerShell)**
```powershell
foreach ($r in 0,1,2) { foreach ($p in 1,2,3) { Start-Process python -ArgumentList "scripts/g8_s1_screening.py $r $p" -NoNewWindow -RedirectStandardOutput "results/log_s1_r${r}_p${p}.txt" } }
```

**Step 2: Sobol DOE (S2), 9 pairs in parallel (PowerShell)**
```powershell
foreach ($r in 0,1,2) { foreach ($p in 1,2,3) { Start-Process python -ArgumentList "scripts/g8_s2_doe.py $r $p" -NoNewWindow -RedirectStandardOutput "results/log_s2_r${r}_p${p}.txt" } }
```

**Step 3: surrogate comparison (S3).** It already uses 9 workers, so run it once:
```bash
python scripts/g8_s3_compare.py
```

**Step 4: active learning (S4/S5), 9 pairs in parallel (PowerShell).** This is the 40–80 minute step.
```powershell
foreach ($r in 0,1,2) { foreach ($p in 1,2,3) { Start-Process python -ArgumentList "scripts/g9_s4_s5.py $r $p" -NoNewWindow -RedirectStandardOutput "results/log_g9_r${r}_p${p}.txt" } }
```

**Step 4b: extension with the box-corner step.** The environment variables must be set before launching, and the new `_ext2` files continue from the earlier ones.
```powershell
$env:G9_WARM="1"; $env:G9_VERTICES="1"; $env:G9_MAX_ROUNDS="8"
foreach ($r in 0,1,2) { foreach ($p in 1,2,3) { Start-Process python -ArgumentList "scripts/g9_s4_s5.py $r $p" -NoNewWindow -RedirectStandardOutput "results/log_g9ext_r${r}_p${p}.txt" } }
```
I'm not sure `G9_MAX_ROUNDS=8` is what you used. The script sets the round limit to start + 3, so check the code around `MAX_ROUNDS_EFF` before relying on this.

**Step 5: dense grid (S6), rank-1 PCM only, 3 in parallel (PowerShell)**
```powershell
foreach ($r in 0,1,2) { Start-Process python -ArgumentList "scripts/g9_s6_grid.py $r 1" -NoNewWindow -RedirectStandardOutput "results/log_s6_r${r}.txt" }
```

**Step 6: checks, then selection, 3 regimes in parallel (PowerShell)**
```powershell
python scripts/g9_assess.py
foreach ($r in 0,1,2) { Start-Process python -ArgumentList "scripts/g10_select.py $r" -NoNewWindow -RedirectStandardOutput "results/log_g10_r${r}.txt" }
```

**Waiting for a step to finish before starting the next.** `Start-Process` returns immediately. Check progress with:
```powershell
Get-Process python | Measure-Object | Select-Object Count
```
When the count drops to 0, that step is done. Tail any log with `Get-Content results/log_g9_r0_p1.txt -Tail 5`.

Since the three regimes only differ by an argument, you could run Steps 1 and 2 for all 9 pairs together as 18 processes, but on 16 cores that just slows each one. Keep to 9 at a time.
Writing the two missing study scripts (sizing and extra sensitivities) now; the GP-BO script is already in place. Nothing committed.

Some items already had code and some didn't. I wrote the missing scripts and smoke-tested each one on a reduced setting. I haven't run the full studies, and nothing is committed.

## Why NSGA-II is hand-written
`pymoo` and `DEAP` were not installed here, and the brief said to ask before any `pip install`. The earlier session wrote NSGA-II in numpy instead of asking you. It is tested on a standard benchmark problem (`tests/test_nsga2.py`) and the dense-grid check passes, so I don't see it as a defect. If you want a library cross-check, I can install `pymoo` (needs your OK) and rerun one pair's search on the same surrogate.

## Already had code
**Widened-bound test (boundary-artefact check).** `scripts/g17_issue2_widen.py` exists and reads the current `g10_selection` files. Rerun, it will test the v3 designs, going up to 60 mm radius and 40 % fraction. The plan's rule is that a design on a bound is accepted only if widening that bound moves `g_window` by less than the band.

```bash
python scripts/g17_issue2_widen.py 0
python scripts/g17_issue2_widen.py 1
python scripts/g17_issue2_widen.py 2
```

It overwrites the old `g17_widen_r*.csv`, which `docs/04` section 5e quotes as a v1 diagnostic. After it runs, I need to relabel that section and regenerate the docs.

## New code I wrote
- **`scripts/g20_gp_bo_comparison.py`**: Gaussian-process Bayesian optimisation of `g_window` for the rank-1 PCM on the explore years, compared with the chosen design. The arrangement is one integer dimension, which is a simplification.
- **`scripts/g21_sizing_study.py`**: changes only the tank volume (50, 60, 75, 112.5 and 150 L), in memory, with the collector and demand fixed. It runs two variants, same PCM fraction and same capsule count, each against a water-only tank of the same volume.
- **`scripts/g22_sensitivity_extra.py`**: mains ±2 K, demand ×0.8 and ×1.2, shield off, convection factor 1 and 4, and PCM density and heat capacity ±10 %. It prints each shift next to the regime's band.

All three use the explore years only. The commands (run time estimates are mine, not measured):

```bash
python scripts/g20_gp_bo_comparison.py 0
python scripts/g20_gp_bo_comparison.py 1
python scripts/g20_gp_bo_comparison.py 2
```
About 15–20 min each.

```bash
python scripts/g21_sizing_study.py 0
python scripts/g21_sizing_study.py 1
python scripts/g21_sizing_study.py 2
```
About 6 min each.

```bash
python scripts/g22_sensitivity_extra.py 0
python scripts/g22_sensitivity_extra.py 1
python scripts/g22_sensitivity_extra.py 2
```
About 6 min each.

## Not coded, and why
- **Flow-dependent collector correction:** it needs a cited correction (such as the Hottel–Whillier flow factor) and collector inputs the repository doesn't have. I won't invent one. Give me a source and I'll add it as an off-by-default option.
- **Monthly mains temperature:** there is no data source in the repository.
- **Viscosity and expansion sensitivity:** the simulator has no natural-convection model, so there is nothing to vary beyond the convection factor in g22.
- **Chen retention benchmark:** I need its numbers and conditions from the paper before I can code a comparison.

## Next step
Say go for any of these and I'll run them. A full run would write result files that nothing references yet. I'd then add them to the registry and docs, and rebuild the report.