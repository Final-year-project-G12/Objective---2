# Fluent GUI Setup Checklist — Regime 0 / RT57HC Single-Capsule Melting

Mesh import is already verified and scripted (`import_mesh.jou`). Everything
below is the remaining setup, done by hand in the GUI because Fluent's
legacy TUI command syntax for these panels (argument count/order) could not
be reliably verified without the risk of silently-wrong settings (see
`setup_and_run.jou` for the abandoned TUI attempt). All numbers below are
real, taken from Objective 2's Regime-0 deployable design and the RT57HC
entry in `pcm_database_tamilnadu.csv` — nothing is invented.

## 0. Open the mesh

File > Read > Case... is not used for a fresh mesh. Instead:
File > Read > Journal... → pick `import_mesh.jou`, OR start Fluent normally
(2D, Double Precision) and run File > Import > CGNS... → Mesh →
`regime0_capsule.cgns`.

After import, General panel: confirm 2D **Axisymmetric** (not planar) —
y is radius here, matching the original (x, r) mesh the Fluent-side
geometry was built for (unlike the OpenFOAM case, which uses a planar
pseudo-2D reinterpretation of the same cross-section).

## 1. Models

- Energy: **On**.
- Viscous: **Laminar**. (Real check: Re = U·D/ν ≈ 3.49e-4 × 0.042044 /
  3.5e-7 ≈ 42 — comfortably laminar at this flow rate.)
- Solidification & Melting: **On**. Leave default under-relaxation/mushy-zone
  parameter (mushy zone constant 1e5) unless you want to tune melt-front
  sharpness later.

## 2. Materials

Create a new fluid/solid material `rt57hc` (Materials > Create/Edit...):

| Property | Value | Source |
|---|---|---|
| Density | 900 (solid) / 800 (liquid) kg/m³ | pcm_database_tamilnadu.csv |
| Cp | 2000 J/kg·K (both phases) | pcm_database_tamilnadu.csv |
| Thermal conductivity | 0.239 W/m·K | pcm_database_tamilnadu.csv |
| Melting heat (latent heat) | 240000 J/kg | pcm_database_tamilnadu.csv |
| Solidus temperature | 329.65 K (56.5 °C) | Tm, no supercooling (0 K) |
| Liquidus temperature | 330.65 K (57.5 °C, +1 K mushy window) | assumed 1 K mushy band for solver stability — real Tm is 56.5 °C; narrowing this band is a legitimate "minor modification" if you want a sharper melt front |

Water: use Fluent's built-in `water-liquid` (998.2 kg/m³, Cp 4182 J/kg·K,
k 0.6 W/m·K, μ 0.001003 Pa·s — room-temperature defaults). For a closer match
to the real ~70 °C operating temperature, edit it to: ρ=977, Cp=4190,
k=0.668, μ=4.04e-4 (same values used in the OpenFOAM case's
`thermophysicalProperties`).

## 3. Cell Zone Conditions

From the import log, zones are named generically (Fluent doesn't carry
gmsh's physical-group names through CGNS). Cross-referenced by cell count
against the known mesh (capsule zone has ~1105–1585 triangles depending on
mesh version; water is the larger zone):

- Smaller-count zone (`3_s_1` in the original unclipped mesh, or whichever
  zone pairs with ~half the expected capsule triangle count after the
  half-disk fix) → **Solid**, material `rt57hc`.
- Larger zone → **Fluid**, material `water-liquid` (edited properties above).

**Verify before trusting the auto-names**: Display > Mesh... and colour by
cell zone, or just click on the capsule region in the graphics window and
read its zone ID from the status bar — this is more reliable than the
face-count guess above now that the geometry was corrected (half-disk
clip changed the triangle counts from the originally-logged ones).

## 4. Boundary Conditions

Real inlet velocity (recomputed, replacing an earlier unverified 0.05 m/s
placeholder — see note below):

```
total regime-0 flow        0.02736 kg/s   (deployable_design_per_regime.csv)
÷ 20 capsules               -> 0.001368 kg/s per unit cell
water density at ~70°C      977 kg/m3
volumetric flow Q           1.400e-6 m^3/s
unit-cell inlet area        pi * R_OUTER^2 = pi*(1.7*0.021022)^2 = 4.012e-3 m^2
inlet velocity U            Q / area = 3.49e-4 m/s
```

- **inlet** (velocity-inlet): axial velocity magnitude **3.49e-4 m/s**,
  temperature **343.15 K** (70 °C, the real tank/collector peak temp).
- **outlet** (pressure-outlet): gauge pressure 0, backflow temperature
  343.15 K.
- **wall_outer**: adiabatic (zero heat flux) — represents the insulated
  tank wall.
- **axis**: Fluent sets this automatically for the 2D-axisymmetric
  centerline; no action needed (it should already show type `axis`, not
  `wall`, since gmsh tagged it and CGNS import should have preserved the
  face-zone's boundary-condition hint — if it imported as `wall` instead,
  change it to `axis` in Boundary Conditions).
- **capsule/water interface** (the coupled wall pair Fluent created on
  import): leave as default coupled wall (no manual BC needed — heat
  transfers directly cell-to-cell across it).

## 5. Initialization

Solution > Initialization > Standard Initialization:
- Temperature: **298.15 K** (25 °C ambient start, PCM fully solid).
- Velocity: 0 (or compute from inlet).

Patch the capsule zone's liquid fraction to 0 explicitly if Fluent doesn't
infer it from the initial temperature being below solidus (Solution >
Initialization > Patch... → Melt/Solidification liquid fraction → 0 →
register/select the solid cell zone).

## 6. Run Calculation

- Time stepping: Transient, fixed or adaptive time step. Start with
  **0.5 s** fixed (matches the original plan in `setup_and_run.jou`), 20
  iterations/timestep, 400 timesteps (200 s physical time — enough to see
  the melt front start moving at this real, fairly low flow rate; extend
  if you want to watch it reach full melt).
- Add a report definition: Surface/Volume report of liquid-fraction volume
  average over the solid (PCM) zone, written to a file, so you get a
  liquid-fraction-vs-time curve without manually re-reading the solution.

## 7. Save

File > Write > Case & Data... Save as
`regime0_rt57hc_melting.cas.h5` / `.dat.h5`.

---

**Note on the corrected geometry**: the capsule cross-section in this mesh
was originally built from gmsh's `addDisk`, which creates a *full* circle,
not a half-disk — meaning an earlier version of this mesh had the PCM
capsule's cross-section extending below the symmetry axis (r<0), which is
meaningless for an axisymmetric solver. This has been fixed (the capsule is
now correctly clipped to r≥0) and `regime0_capsule.cgns` was regenerated
and re-verified against Fluent (clean import, 0 errors) as of this pass.
If you have an older case file lying around from before this fix, discard
it and re-import from the current `regime0_capsule.cgns`.
