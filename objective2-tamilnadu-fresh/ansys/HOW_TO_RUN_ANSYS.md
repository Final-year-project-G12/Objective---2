# How to run the Tamil Nadu PCM case in ANSYS Student Fluent

Everything here is verified against ANSYS Fluent 2026 R1 Student on this
machine. Where a step is known to be flaky, that is stated rather than
glossed over.

---

## 0. Before you start — the one-session rule

**The Student licence allows ONE Fluent session at a time.** Close any open
Fluent window first. If a launch fails with

> Unexpected license problem; exiting

that is usually *not* a real licence failure. It is a stray `ansyscl.exe`
licence-client process left behind by an earlier session. Kill it and relaunch:

```powershell
Get-Process ansyscl -ErrorAction SilentlyContinue | Stop-Process -Force
```

Launching two PyFluent sessions at once exceeds the cap and **both** fail.

---

## 1. The live demo (easiest — one command)

From `ansys_openfoam_case/`:

```bash
python fluent_live_demo.py
```

This opens the Fluent graphics window and runs the optimal Regime-0 design,
re-rendering a liquid-fraction contour each chunk so you watch the melt front
advance. It prints a table as it goes:

```
 time (h)  liquid frac  T_mean (C)
     0.20       0.0239       46.17
     0.30       0.0394       48.81
```

### Options

| flag | meaning |
|---|---|
| `--regime 0\|1\|2` | which climate regime's optimal design (default 0) |
| `--hours 6` | physical duration (default 6 h — a full charging window) |
| `--dt 20` | timestep in seconds (default 20) |
| `--headless` | no window; use to check the setup runs |
| `--rebuild-mesh` | build a mesh at the optimal radius instead of reusing the v3 mesh |

A quick look: `python fluent_live_demo.py --hours 1`
The full result: `python fluent_live_demo.py --hours 6` (~30 min wall clock)

### Where the numbers come from

Nothing in the demo is typed by hand:

- **PCM identity, capsule radius, fraction, capsule count** — read from
  `results/tn_optimal_designs.csv`, the optimiser's own output.
- **PCM thermal properties** — read from
  `data/objective1/pcm_database_tamilnadu.csv` (densities and specific heats
  averaged over solid and liquid, this project's existing convention).

If `tn_optimal_designs.csv` does not exist yet, the demo says so and falls back
to the v3 deployable design, so it still runs mid-pipeline:

```
  design source: FALLBACK (v3 deployable) -- tn_optimal_designs.csv not written yet
```

---

## 2. The four-PCM comparison (batch, no window)

```bash
bash run_v4_pcm_comparison.sh          # ~2 h, sequential (licence cap)
python plot_v4_pcm_comparison.py       # writes v4_pcm_comparison.png
```

Each run writes `v4_<pcm>_melt_melt_history.csv` incrementally, so a partial
run still leaves a usable curve.

**Known limitation:** n-Pentacosane (C25) diverges and is reported as
unavailable rather than plotted. See `docs_objective2/CFD_VERIFICATION.md` for
the six hypotheses tested and disproved.

---

## 3. By hand in the GUI

If you would rather drive it yourself:

1. Launch Fluent: **2D**, **Double Precision**, 2 processes.
2. `File > Read > Case...` → `C:\fluent_work\regime0_v3_mesh_only.cas.h5`
3. **General** → 2D Space: **Planar** (not axisymmetric — the melting cases are
   planar; the old checklist saying axisymmetric is superseded).
4. **Models**: Energy **On**; Viscous **Laminar**; Solidification & Melting
   **On**.
5. **Materials** → Create `c26` (values from the PCM database):

   | property | value |
   |---|---|
   | Density | 770 kg/m³ |
   | Cp | 2290 J/kg·K |
   | Thermal conductivity | 0.238 W/m·K |
   | Viscosity | **3.5e-3 Pa·s** |
   | Pure solvent melting heat | 256000 J/kg |
   | Solidus temperature | 329.65 K |
   | Liquidus temperature | 339.65 K (10 K mushy band) |

   > Do **not** raise the viscosity to make the melt "immobile". It was tried:
   > C26 diverges to 4714 °C at 10 Pa·s with everything else identical, and
   > runs clean at 3.5e-3.

   Copy `water-liquid` from the database and set ρ 977, Cp 4190, k 0.668,
   μ 4.04e-4.

6. **Cell Zone Conditions**: `3_s_1` → water-liquid, `3_s_2` → c26.
7. **Boundary Conditions**:
   - `2_l_7` → velocity-inlet, 5.5815e-5 m/s, **343.15 K**
   - `2_l_9` → pressure-outlet, backflow 343.15 K, *Prevent Reverse Flow* on
   - `2_l_8` → wall, Heat Flux **0**
   - `2_l_5`, `2_l_10`, `2_l_11` → axis
8. **Initialization**: Standard, temperature **343.15 K**, Initialize.
   Then **Patch** the capsule cold:
   *Solution Initialization > Patch...* → zone `3_s_2`, Temperature,
   **303.15 K**.

   > **Check the patch took.** Make a volume-average report of temperature on
   > `3_s_2` and confirm it reads 303.15 K. The v3 runs failed here silently —
   > the patch errored, the message scrolled past, and the solve produced a
   > confident liquid-fraction of 0 from a capsule that was never cold.

9. **Run Calculation**: transient, 1st order; Δt **20 s**; 40 iterations/step;
   1080 steps for 6 h.
10. For the live view: *Results > Graphics > Contours* → `Liquid Fraction`,
    then *Calculation Activities > Solution Animations* to refresh it every
    few timesteps.

---

## 4. Verifying zone names on a new mesh

Zone names are **not** guaranteed to repeat between separately imported
meshes, even when the geometry is identical. Before using any mesh:

```bash
python verify_zones.py "C:\fluent_work\regime0_v3_mesh_only.cas.h5"
```

It reads the HDF5 structure directly — no Fluent launch — and prints cell and
face zones with their geometry, so you can tell inlet from outlet by
`x_mean` rather than by assuming.

---

## 5. Troubleshooting

| symptom | cause and fix |
|---|---|
| `Unexpected license problem` | stray `ansyscl.exe`, or a second session. See §0. |
| `SIGSEGV` / `Connection reset` on CGNS import | Fluent is flaky importing gmsh CGNS. **Retry in a fresh process** — one file needed three separate launches. A retry *inside* the same session can never work: the solver process is already dead. |
| liquid fraction stays exactly 0 | the capsule is not actually cold, or the water is not actually hot. Check the patch read-back (§3.8). This was the v3 bug. |
| temperature → 5000 K or → 1 K | enthalpy-porosity divergence. Check viscosity is 3.5e-3, not a large "immobile" value. |
| `invalid command` from a TUI call | the TUI argument form differs between builds. Patch is positional: `solve/patch zone "()" field value`. `liquid-fraction` is **not** patchable here — it follows from temperature. |

---

## 6. What each file is for

| file | purpose |
|---|---|
| `fluent_live_demo.py` | **the live demo** — optimal design, GUI, animated melt front |
| `pyfluent_v4_melt.py` | batch melting run for one PCM |
| `run_v4_pcm_comparison.sh` | all four PCMs, sequential |
| `plot_v4_pcm_comparison.py` | the comparison figure |
| `build_mesh_regime.py` | gmsh mesh for a given capsule radius (`[refine]` factor optional) |
| `verify_zones.py` | zone ground truth straight from the case HDF5 |
| `pyfluent_v3_setup.py` | superseded — kept for provenance; its runs showed no melt |
