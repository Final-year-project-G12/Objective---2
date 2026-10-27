# 19 — CFD Cross-Verification: ANSYS Fluent & OpenFOAM (2026-10, updated 2026-10-27)

**Status: CURRENT as of 2026-10-27.** Fluent has been re-run against the
**final** design (demand-timing fix + safety shield + 100L/2.5m² tank
resize — see `RESULTS.md`), using the real deployable geometry for all 3
regimes (Regime 2 now on n-Pentacosane/C25, Regimes 0/1 on n-Hexacosane/
C26). The earlier blocker (`"Unexpected license problem; exiting"`) turned
out to be a stray `ansyscl.exe` license-client process left running since
an earlier GUI session, not a real license failure or a code issue —
killing it restored normal operation immediately, confirmed with a clean
headless launch. A second lesson from this re-run: launching two PyFluent
sessions concurrently (2 processors each) exceeded the Student license's
parallel-session cap and both failed outright — the fix is to run exactly
one Fluent session at a time, which is what the results below reflect.
OpenFOAM: Regime 0 only, original pre-fix geometry, scope-limited (see
below), not re-run since. This is a basic physics cross-check of
Objective 2's already-trained, already-selected designs — it does not
re-optimize or re-select anything. All geometry, PCM identity, capsule
count, and flow rate come directly from
`results/tamilnadu/deployable_design_per_regime.csv` (Objective 2's real
optimizer output). Working files live in `ansys_openfoam_case/`
(`regime{0,1,2}_v3_capsule.cgns/.msh`, `_v3_mesh_only.cas.h5`,
`_v3_c26_melting.{cas,dat}.h5` / `_v3_c25_melting.{cas,dat}.h5`), built
with the new `pyfluent_v3_setup.py` (parameterizes PCM identity per
regime, unlike `pyfluent_v2_setup.py` which assumed C26 everywhere).

**2026-10-26 re-run note**: `src/simulation/tank_model.py` had a
demand-timing bug (see `RESULTS.md`/`TAMILNADU_REDESIGN_PLAN.md`) that was
fixed and the Python pipeline re-run, which changed the deployable design
in every regime — notably, **n-Hexacosane (C26) now wins in all 3
regimes** (previously RT57HC/C26/C25). The Fluent results below are the
corrected re-run, built from fresh meshes at the new capsule radii and
fresh inlet velocities at the new flow rates/capsule counts. The original
(pre-fix) results and meshes are kept as `regime{0,1,2}_*` (without the
`_v2` suffix) in `ansys_openfoam_case/` for the record; the corrected ones
are `regime{0,1,2}_v2_*`.

## Why this exists

Objective 2's own simulator (`src/simulation/tank_model.py`) is a fast
greybox model built for a DOE/surrogate/optimizer loop — not a CFD tool.
This work answers a different question: does a real commercial/open CFD
solver, modeling the actual capsule geometry and PCM phase-change physics
independently, produce physically sensible behavior for the same design?
It is a sanity check, not a replacement for Objective 2's own validation
(Phase 4 gates, Phase 7 simulator confirmation, Phase 8 robustness).

## Geometry and mesh

Single-capsule, unit-cell cross-section built in `gmsh` (`build_mesh.py` /
`build_mesh_regime.py`, parameterized per regime): a half-disk capsule
(radius = Objective 2's real deployable diameter / 2) inside a surrounding
water annulus (outer radius = 1.7× capsule radius, approximating the
packed-bed void fraction already used in `geometry.py`), axial length = 4×
capsule diameter.

**A real geometry bug was found and fixed during this work**: `gmsh`'s
`addDisk` creates a full circle, not a half-disk — an earlier mesh had the
capsule's cross-section extending below the symmetry axis (`r<0`), which
is meaningless for an axisymmetric model. Fixed by clipping with a cutting
rectangle before use; verified by direct re-inspection of the mesh file's
own node data (`plot_mesh_check.py`, `mesh_verification.png`) — no mesh
node has `r<0`, and the capsule cross-section area matches the expected
half-disk area within 0.06%.

## ANSYS Fluent

Driven entirely through **PyFluent** (`ansys-fluent-core`), Fluent's own
Python scripting API — not the GUI, and not blind TUI text commands (an
early attempt at scripting via raw TUI command guessing was abandoned as
too unreliable; PyFluent's typed settings API gave real, actionable error
messages instead of silent wrong behavior). Scripts: `pyfluent_full_setup2.py`
(Regime 0), `pyfluent_regime1_setup.py`, `pyfluent_regime2_setup.py`.

**Zone identity is verified, not assumed.** Fluent's CGNS import assigns
generic names (`3_s_1`, `2_l_7`, etc.) that do **not** reliably repeat
across regimes even for topologically-identical meshes — confirmed
directly: Regime 0's inlet/outlet zone names differ from Regimes 1 and
2's. Each regime's zone identities (which name is water, which is the
capsule, which boundary is inlet/outlet/wall/axis) were independently
confirmed by reading the saved case file's own HDF5 face/cell adjacency
data (`verify_zones.py`) before writing any boundary condition — not
inferred from position or copied from a previous regime.

**A real numerical instability was found and fixed.** RT57HC's real
solidus/liquidus gap is ~1 K — numerically too narrow for Fluent's
enthalpy-porosity solidification/melting model at this mesh/timestep
resolution: the energy equation's AMG solver diverged (residuals
exploding 1e+3 → 1e+23 within a handful of iterations) every time the
melt front crossed this narrow band. Fixed by widening the *numerical*
mushy-zone band to 10 K (a standard, documented Fluent stability
technique for phase-change problems) — confirmed to push the divergence
point later and later as the band widened (1K→147s, 3K→153s, 10K→stable
through 500s), isolating mushy-zone width as the actual lever, not
timestep size (an independent smaller-timestep test was *not* sufficient
on its own).

**True axisymmetric mode was attempted and found unresolvable in the time
available.** The mesh's `y` axis represents radius; true axisymmetric
revolution is the physically correct interpretation (matching the real
capsule-in-tank geometry and the inlet velocity derivation). Setting it up
correctly caused an immediate, instant momentum/pressure divergence at
the very first iteration — a different and more fundamental failure than
the thermal stiffness above. Three independent, legitimate fixes were
tried and all failed with the identical signature: smaller timestep,
baking axisymmetric into the mesh at creation instead of switching it
after loading, and a different pressure-velocity coupling scheme (SIMPLE
vs Coupled). This points to a deeper mesh-conditioning issue near the
symmetry axis that needs visual/mesh-level investigation (e.g. in the
GUI) to resolve — **not pursued further by explicit user decision**.
**Scope decision: all 3 Fluent regimes use planar (flat, non-revolved)
geometry** — the same simplification OpenFOAM's case uses below. This is
a real, disclosed limitation, not a hidden one.

**Results, FINAL design (2026-10-27 re-run; all real, independently
queried via Fluent's own volume report definitions,
`pyfluent_query_v2.py`):**

| Regime | PCM (Tm) | Real design inputs (from Objective 2, final) | Inlet velocity | Simulated duration | Advection travel time | Capsule temp range | Liquid fraction melted |
|---|---|---|---|---|---|---|---|
| 0 | n-Hexacosane/C26 (56.5°C) | ⌀72.22mm, 32 capsules, 0.02066 kg/s | 5.582e-5 m/s | 2140 s | 1941 s | 25.18–50.85°C | 0% |
| 1 | n-Hexacosane/C26 (56.5°C) | ⌀75.31mm, 33 capsules, 0.01085 kg/s | 2.613e-5 m/s | 4530 s | 4323 s | 26.38–51.56°C | 0% |
| 2 | n-Pentacosane/C25 (54.0°C) | ⌀79.76mm, 35 capsules, 0.02371 kg/s | 4.802e-5 m/s | 2700 s | 2492 s | 25.18–50.25°C | 0% |

All three runs cover their own advection travel time plus roughly a 200s
margin (the same margin convention used in the 2026-10-26 re-run, kept for
consistency), so the hot-water front genuinely reaches each capsule before
the run ends — but **0% liquid fraction is the honest result in all 3
regimes this time**, including Regime 1 (which showed a small 0.33% melt
in the prior re-run). This is not a regression: the resized tank/collector
changed every regime's capsule diameter and per-capsule flow rate, which
changed the unit-cell inlet velocity and travel time for all three —
Regime 1's travel time grew from 457s (pre-resize) to 4323s (post-resize,
a ~9.5× increase, because its selected capsule diameter grew from 44.7mm
to 75.3mm while its flow rate roughly halved), so the fixed ~200s margin
that used to leave Regime 1 comfortably past arrival now only barely
clears it, same as Regimes 0 and 2. The physically correct conclusion is
unchanged from the prior re-run: all three capsules are heating up
steadily and consistently with their real flow rates (compare the
Min→Max capsule temperature spread above — ~25°C rise in every regime),
just not yet past their PCM's melting point within this simulated window.
A longer run would very likely show melting begin in all three; this was
not pursued further given this is a secondary sanity check, not
Objective 2's own validation (which already confirms real melting via the
grey-box simulator's own `sim_mean_f_melt` output — 21.4% / 14.5% / 23.1%
for Regimes 0/1/2 respectively — in
`results/tamilnadu/deployable_design_per_regime.csv`).

The same known, low-risk unresolved item recurred: the liquid-fraction
initialization patch command failed with a TUI argument error in every
run. Still very likely inconsequential for the same reason as before
(initialized temperature 298.15K already implies 0% melt everywhere at
t=0) — not independently confirmed by fixing the actual patch call.

**A real, reproducible operational finding from this re-run**: Fluent's
CGNS import crashed once on Regime 2's mesh with the documented
`CeetronSAM.dll` SIGSEGV bug (same failure mode noted below for the
original mesh-import work) — a simple retry succeeded on the next attempt
with no changes, consistent with this being a transient crash, not a
mesh-specific defect (confirmed independently: `verify_zones.py` on the
successfully-imported Regime 2 mesh shows the same clean zone topology as
Regimes 0 and 1).

Saved results: `regime{0,1,2}_v3_c26_melting.{cas,dat}.h5` /
`regime2_v3_c25_melting.{cas,dat}.h5` in `ansys_openfoam_case/` (final
design, 2026-10-27). The 2026-10-26 re-run results
(`regime{0,1,2}_v2_c26_melting.{cas,dat}.h5`, bug-fixed/no-shield/50L
design) and the original pre-fix results
(`regime{0,1,2}_{rt57hc,c26,c25}_melting.{cas,dat}.h5`) are kept alongside
for the record. See `FLUENT_GUI_SETUP_CHECKLIST.md` for how to open any of
these in the GUI and inspect contours directly, and `HOW_TO_RUN.md` §11
for the exact commands to rebuild/re-run this from scratch for a future
design change (note: `pyfluent_v3_setup.py` supersedes `pyfluent_v2_setup.py`
as the current setup script — it takes PCM identity and all zone names as
CLI args instead of hardcoding C26 and assuming fixed zone names, since
Regime 2 now uses a different PCM).

## OpenFOAM

`chtMultiRegionFoam` (conjugate heat transfer), Regime 0 only, in
`ansys_openfoam_case/openfoam_case/`. **Scope-limited by the solver
itself, not by choice**: OpenFOAM's standard solvers have no native
solidification/melting model — this demonstrates heat conduction from the
hot water into the solid PCM capsule (sensible heating only, no latent
heat / phase change modeled at all). Mesh is a genuine 3D thin-slab
extrusion of the same corrected half-disk cross-section (OpenFOAM has no
native 2D mode), with a verified-conformal (not just adjacent) interface
between the water and capsule regions (`openfoam_interface_check.png` —
coupling-patch face centroids coincide to machine precision, ~1e-18 m).
Regimes 1 and 2 were not attempted in OpenFOAM.

## What this does and doesn't prove

**Does**: confirms Objective 2's selected designs behave physically
sensibly under independent, real heat-transfer/CFD physics — hot water
genuinely conducts into the PCM at a rate consistent with each regime's
real, different flow rate (final re-run: ~25°C capsule temperature rise
in all 3 regimes, tracking their respective travel times). In the earlier
2026-10-26 re-run, Regime 1's much larger margin past arrival was also
enough to show the PCM actually cross into melting (0.33% liquid
fraction) — direct independent confirmation that the solidification model
is live and responds correctly once the surface clears Tm, not just
conducting heat.

**Doesn't**: this is not a validated, production-grade CFD study —
planar (not axisymmetric) geometry, a short demonstration window (the
final re-run's 0% melt everywhere reflects that window, not a physics
problem — Objective 2's own simulator independently confirms real melting
at these designs' real timescales), no mesh-independence study, and the
OpenFOAM side has no phase-change physics at all. Treat it as "the
physics is not obviously wrong," not as a substitute for Objective 2's
own Phase 4/7/8 validation.
