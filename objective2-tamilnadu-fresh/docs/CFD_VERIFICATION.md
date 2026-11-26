# 19 — CFD Cross-Verification: ANSYS Fluent & OpenFOAM (2026-10, updated 2026-10-29)

## 🔴 2026-10-29 — the v3 cases reported liquid fraction = 0, and the cause was the initial condition

Every v3 case (all three regimes) ended with a volume-averaged capsule liquid
fraction of **exactly 0.000** and a peak capsule temperature of 323.4–324.7 K
(50.3–51.6 °C). A PCM study in which the PCM never melts demonstrates nothing,
so the cases were re-posed.

**It was not an under-run, a bad mesh, or wrong PCM data.** The inlet was
already at 343.15 K (70 °C), comfortably above every candidate's melt point.
The fault was one line:

```python
pyfluent_v3_setup.py:148    init.defaults["temperature"] = 298.15
```

That initialises the **whole domain** to 25 °C — the water included — while the
inlet velocity is 5.6e-5 m/s, which is effectively stagnant. Hot water therefore
had to reach the capsule by advection at ~0.06 mm/s. Over the 2 140–4 530 s
simulated it never arrived, the capsule sat in cold water, and the
enthalpy-porosity model correctly reported no melt. **The answer was right for
the case that was posed; the case was the wrong question.**

A second, compounding defect: v3's `patch liquid fraction` call raised
`invalid command` in all three runs. It was wrapped in a failure-tolerant
`step()` helper, so the message scrolled past in a 120 kB log and the solve
continued from an unverified initial state.

### What v4 does instead (`pyfluent_v4_melt.py`)

| | v3 | v4 |
|---|---|---|
| water initial T | 298.15 K (cold) | **343.15 K** — collector delivery |
| capsule initial T | 298.15 K | **303.15 K**, patched and **read back to confirm** |
| physical time | 2 140–4 530 s | **21 600 s** (6 h charging window) |
| timestep × iters | 10 s × 20 | 20 s × 40 |
| PCMs | one per regime mesh | **all four, on one mesh** |
| initial-condition failure | logged, run continued | **aborts the run** |

The capsule now starts cold and solid inside hot water, which is the state a
mid-tank capsule is actually in once the collector loop is warm.

**Why buoyancy is still off.** It is tempting to blame "momentum frozen" and
switch on gravity + Boussinesq. That is wrong *on this mesh*: `verify_zones.py`
shows the domain is a half-slice with a **symmetry plane at y = 0** (zones
`2_l_5`, `2_l_10`, `2_l_11` all lie on y = 0, and the domain spans y = 0…0.061
only). Gravity perpendicular to a symmetry plane is physically inconsistent —
buoyancy would drive flow through a boundary that exists to forbid it. Melting
here is conduction-limited anyway (PCM k ≈ 0.15–0.24 W/mK dominates the
water-side resistance), and the empirical melt-film enhancement is carried by
the node model's `pcm_integration.liquid_convection_enhancement`. A
`--convection` flag is retained for a future full-domain rebuild where
buoyancy would be admissible.

**Why all four PCMs run on the regime-0 mesh.** v3 ran each PCM on its own
regime mesh, which confounds PCM identity with capsule radius and flow rate —
no PCM-vs-PCM statement could be drawn from it. v4 varies only the material.

**Patch API.** `probe_patch_api.py` tried five call forms against this build;
only the positional TUI form binds (`solver.tui.solve.patch(zone, "()", field,
value)`). The settings API rejects both `cell_zones` and `zones` as invalid
keys. `liquid-fraction` is not patchable at all here — it does not need to be,
since enthalpy-porosity derives it from temperature, and v4 **verifies** it is
0 rather than assuming it.

**Licence note (unchanged, and it binds v4):** the Student licence permits one
Fluent session at a time, so the four PCM runs are strictly sequential.

### v4 results — three of four PCMs melt cleanly

Capsule Ø 42 mm, initially 30 °C solid, immersed in 70 °C water for 6 h:

| PCM | Tm (°C) | k (W/mK) | melt fraction @ 6 h | T_end (°C) | divergences |
|---|---|---|---|---|---|
| n-Hexacosane (C26) | 56.5 | 0.238 | **0.76** | 64.5 | 0 |
| RT57HC | 56.5 | 0.200 | 0.72 | 64.0 | 0 |
| PureTemp 58 | 58.0 | 0.150 | 0.60 | 64.0 | 0 |
| n-Pentacosane (C25) | 54.0 | 0.239 | *diverged* | — | 147 |

The three that ran are physically ordered: C26 and RT57HC share a melt point
and the higher-conductivity one melts more; PureTemp 58 has both the highest
melt point and the lowest conductivity and melts least.

### The C25 divergence — what it is, and what it is not

C25 is the only PCM that diverges, and it does so within its first chunk. Five
hypotheses were tested and **four were disproved**:

| tried | result | what it rules out |
|---|---|---|
| dt 20 s → 5 s | diverged to the 1 K *floor* instead of the 5000 K ceiling | not a timestep problem — a timestep problem improves as dt shrinks |
| melt viscosity 3.5e-3 → 10 Pa·s (immobile melt) | still diverged, at liquid fraction 0.19 | not melt mobility, and not loss of Darcy damping at full melt |
| `delh` under-relaxation 0.9 → 0.2 (+ temperature 0.8, mom 0.5) | still diverged | not the enthalpy-update relaxation |
| mushy band 10 K → 20 K | still diverged | **not overshoot past liquidus** — at 20 K the liquidus (347.15 K) is *above* the 343.15 K water, so no cell can leave the band at all |
| material properties read back from the solver | all seven bind correctly, viscosity included | not a data-entry error |
| aggressive relaxation (`delh` 0.02, temperature 0.3) | divergences fell 147 → 43 but did not stop | not fixable by relaxation alone |
| **mesh refinement 1 105 → 4 378 capsule cells** | **still diverged (158)** | **not melt-front resolution** |

The decisive test was `c26_at_c25_tm`: **C26's own properties carrying C25's
melt point**. It diverges too (146 divergences). Changing one number — the melt
point, by 2.5 K — turns a case with *zero* divergences into an unstable one.

So the trigger is the 54 °C melt point against 70 °C water on this mesh, not
any property of C25. The blow-up is bidirectional (5000 K ceiling at dt = 20 s,
1 K floor at dt = 5 s), which is the signature of a conditioning problem in the
coupled energy/liquid-fraction update rather than a physical instability.

### ✅ RESOLVED 2026-10-30 — it was the pressure–velocity coupling

The seventh hypothesis was the right one. `probe_methods.py` read the real
options off the solver (`SIMPLE | SIMPLEC | PISO | Coupled`), and switching to
**Coupled with first-order upwind** gives **zero divergences** where every
previous C25 attempt gave 43–158.

All four PCMs were then re-run under identical settings — not C25 alone, since
mixing a Coupled/first-order C25 with SIMPLE/second-order results for the
others would put a *numerical* difference into a figure that claims to show a
*material* difference:

| PCM | Tm (°C) | k (W/m·K) | melt fraction @ 6 h | divergences |
|---|---|---|---|---|
| n-Pentacosane (C25) | 54.0 | 0.239 | **0.60** | 0 |
| n-Hexacosane (C26) | 56.5 | 0.238 | 0.50 | 0 |
| RT57HC | 56.5 | 0.200 | 0.47 | 0 |
| PureTemp 58 | 58.0 | 0.150 | 0.38 | 0 |

The ordering is physically consistent three ways: C25 has the lowest melt
point and melts most; C26 and RT57HC share a melt point and the
higher-conductivity one melts more; PureTemp 58 has the highest melt point and
lowest conductivity and melts least.

**Accuracy caveat, stated plainly.** First-order upwind is more numerically
diffusive than second order, so these melt fractions are *conservative*. The
earlier second-order run of the three PCMs that would solve gave 0.76 / 0.72 /
0.60 against 0.50 / 0.47 / 0.38 here — the relative ordering is identical, the
absolute values are lower. First order is used because it is the only setting
under which all four solve, and the comparison requires identical settings.
Read the ordering, not the absolute numbers.

---

**Historical status (superseded by the above): a characterised numerical
limitation, not a result.** C25's melt curve was NOT reported, and the
comparison figure carried three PCMs with the fourth named as unavailable
rather than silently dropped.

A refined mesh was built and tested (`build_mesh_regime.py` now takes a
refinement factor; `regime0_fine_capsule` quadruples the capsule to 4 378
cells) specifically because it was the last remaining lever after the solver
settings were exhausted. **It did not help** — C25 still diverges on the fine
mesh. So melt-front resolution is not the cause either, and the earlier
recommendation to refine the mesh is withdrawn.

What remains untested is the pressure-velocity coupling and the discretisation
scheme, which is where a conditioning problem in the coupled
energy/liquid-fraction update would most plausibly live. That is the next thing
to try, and it is recorded as open rather than guessed at.

Note also that two CGNS imports failed with `Connection reset` before an
identical third attempt succeeded, so Fluent sessions here are occasionally
flaky under rapid launch/exit churn. A single import failure is worth retrying
before being treated as a bad mesh file — a structural diff (CGNS is HDF5, so
`h5py` reads it directly) showed the rejected and accepted files were
identical in zones and names.

---

**Status of the sections below: these describe the v3 runs, whose
liquid-fraction results are superseded by the above.** The mesh, zone
identification, geometry-bug history and licence findings remain valid.

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
`data/legacy/phase7_deployable_design_per_regime.csv` (Objective 2's real
optimizer output). Working files live in `ansys/`
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
`_v2` suffix) in `ansys/` for the record; the corrected ones
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
`data/legacy/phase7_deployable_design_per_regime.csv`).

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
`regime2_v3_c25_melting.{cas,dat}.h5` in `ansys/` (final
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
`archive/openfoam_legacy/openfoam_case/`. **Scope-limited by the solver
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
