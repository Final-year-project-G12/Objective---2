# Seeing the simulations (ParaView and without it)

ParaView 6.2.0 is installed at `D:\Program Files\ParaView 6.2.0\` (`paraview.exe` = window, `pvbatch.exe` =
headless, used by the scripts). Everything below was **run and checked on this machine** unless marked.

## 1. Quickest: ready-made state files (play the simulation)

A `.pvsm` state file contains the full pipeline (reader → mirror → colour by T → camera → time steps).

| State file | Shows |
|---|---|
| `cases_tank\charge\charge_T.pvsm` | tank filling with hot water from the top (time 0–3600 s, 31 steps) |
| `cases_tank\draw\draw_T.pvsm` | hot layer shrinking during a draw, cold plume from the bottom port |
| `cases_collector\test_T30\collector_T.pvsm` | collector riser strip (cross-section stretched 12×), 5 time steps |

**In ParaView:** File → Load State → pick the file → "Use File Paths from State". Press ▶ (green Play). If the
time controls are missing: View → Toolbars → tick *VCR Controls* and *Current Time Controls*. **Reset Camera** if the
view is blank.

**From PowerShell:**
```powershell
& "D:\Program Files\ParaView 6.2.0\bin\paraview.exe" --state="D:\Final Year Project\OBJECTIVE2\Objective---2\openfoam_cfd\cases_tank\charge\charge_T.pvsm"
```
New state file for any case:
```powershell
& "D:\Program Files\ParaView 6.2.0\bin\pvbatch.exe" make_pv_state.py tank "<case>.foam" "<case>_T.pvsm" 298 333
```
(`tank` or `collector`; the last two numbers fix the colour range in kelvin.)

## 2. Opening a `.foam` file by hand (and why it can look empty)

File → Open → `<case>.foam` → **Apply**. Raw readers are easy to mis-set:

* The tank and capsule are **thin 5° axisymmetric slices**: add **Filters → Reflect** (named *Axis Aligned Reflect* in
  ParaView 6), Plane = **Y Min**, tick *Copy Input*, then view along +Z.
* Colour by `T` (or the liquid fraction, listed as `solidificationMeltingSource1:alpha1` — the colon may appear as an
  odd character).
* The collector has several mesh regions: in *Mesh Regions* untick the plain `internalMesh` and tick
  `/water/internalMesh` and `/copper/internalMesh`.
* *Skip Zero Time* is on by default (so the initial state is hidden).
* **Harmless warnings:** "boundaryField defaultFaces not found in object T/U/p/p_rgh at time = 0" — the mesh has an
  empty `defaultFaces` patch with zero faces. Ignore.

## 3. Run a new capsule case so it can be animated

Normal DOE runs keep only the last 3 time steps. Use the viz runner:
```powershell
cd "D:\Final Year Project\OBJECTIVE2\Objective---2\openfoam_cfd\scripts"
python viz_case.py --name om49_d055 --pcm "savE® OM49" --d 0.055 --mdot 0.03 --dT 15 --t-end-h 1.5
python make_pv_state.py tank "..\cases_viz\om49_d055\om49_d055.foam" "..\cases_viz\om49_d055\om49_d055.pvsm" 300 335
```
(The capsule is also axisymmetric, so `tank`-mode state files mirror it correctly; for the liquid fraction instead
of T use `capsule_paraview.py`, below.) Opening `cases_viz\rt44_d060\rt44_d060.foam` shows the example run
(145 time steps, 1.2 h simulated).

## 4. Images without the GUI

| Command | Output |
|---|---|
| `python plot_capsule_fields.py ..\cases_viz\rt44_d060 --times 0 300 600 900 1200 1800 2400` | `snapshots_liquid_fraction.png`, `snapshots_temperature.png` (matplotlib; melt front and temperature, no ParaView needed) |
| `pvbatch.exe capsule_paraview.py <case.foam> <outdir>` | liquid-fraction and T PNGs by ParaView; used for `cases_viz\rt44_d060\paraview\` |
| `pvbatch.exe component_paraview.py tank <case.foam> <outdir>` | tank temperature at six times |
| `pvbatch.exe component_paraview.py collector <case.foam> <outdir>` | collector cross-sections at x = 0.05/0.6/1.19 m and a longitudinal section |
| `python plot_pht_vs_greybox.py` | `results\pht_vs_greybox.png` (PCM temperature and melt fraction vs hour, bed vs grey-box) |
| `python tank_postprocess.py <case>` | `tank_profiles.png` (axial profiles, outlet T, MIX number, thermocline) |

GUI with the pipeline built by script (set the case first):
```powershell
$env:CASE_KIND = "tank"      # or collector
$env:CASE_FOAM = "D:\...\cases_tank\draw\draw.foam"
& "D:\Program Files\ParaView 6.2.0\bin\paraview.exe" --script="D:\...\scripts\component_paraview.py"
```

## 5. What the pictures show

* **Capsule:** melting from the outside inward; the top melts first because liquid wax rises, leaving a solid core
  at the bottom that sinks — fully melted at ≈ 40 min for 60 mm, 15 K drive (RT44HC).
* **Tank charge:** a hot layer growing downward from the top port; outlet stays cold until ≈ 24 min.
* **Tank draw:** shrinking hot layer; a cold plume rises along the axis from the bottom port.
* **Collector:** plate/fin hot, channel core cooler at the outlet; water warming along the length.

## 6. Notes

* ParaView 6 renamed *Reflect* to `AxisAlignedReflect` (property `PlaneMode`); the scripts handle ParaView 5 and 6.
* `capsule_movie.py` (frames + GIF) was written but **not run**; `pvbatch.exe capsule_movie.py <case.foam> <outdir> liquid`.
* A case folder is overwritten when the same case is re-run: results are copied back from WSL only at the end of a run.
