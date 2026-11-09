# What we simulate with, and why

**The question Objective 2 answers:** for each of Tamil Nadu's three climate
regimes, what capsule size, how many capsules, which PCM and what flow rate
make a 100 L solar water tank deliver the most useful hot water in the
evening — and does that beat an identical tank with no PCM in it at all?

Answering that needs two very different simulators. This note says which,
why each is needed, and why the CFD tool changed when the study moved from
Rajasthan to Tamil Nadu.

---

## The two simulators

| | **Tank model** | **ANSYS Fluent** |
|---|---|---|
| what it is | 1-D stratified tank, 10 nodes, enthalpy method for the capsules | commercial finite-volume CFD |
| scope | the whole tank, a whole year | one capsule, six hours |
| runtime | seconds per simulated year | about 30 minutes per PCM |
| role | **the optimiser's evaluator** | independent physics check |
| decides the design | **yes** | no |
| resolves the melt front | no | **yes** |

They are not alternatives. One searches, the other verifies.

### Why the optimiser cannot use CFD

The search does not evaluate a moment, it evaluates a *design*: every
candidate is run over a full year of hourly weather, several years over,
against a plain-water tank on the same weather and the same demand. The
pipeline did that for a 128-point Sobol design of experiments per regime and
PCM, NSGA-II with active learning on top, a 720-design dense grid, a
60-evaluation Bayesian search, and repeat runs at halved timestep and doubled
node count to measure its own repeatability — **over 1,100 design evaluations
before any design was chosen.**

At CFD speed that is years of compute. At tank-model speed it is hours. The
reduced model is not a compromise for convenience; it is what makes an
optimisation study possible at all.

### Why the study still needs CFD

The tank model earns its speed by assuming things: that a capsule is radially
lumped, and that the convective enhancement of a molten PCM can be carried as
an empirical factor rather than resolved. Those assumptions are reasonable,
and they are still assumptions. CFD is how we find out whether a real solver,
given the actual geometry and the real phase-change physics, agrees.

No design is selected or rejected on a CFD result. Its job is to say whether
the physics the fast model assumes is the physics that actually happens.

---

## Why ANSYS Fluent here, and OpenFOAM there

The Rajasthan study used **OpenFOAM**; this one uses **ANSYS Fluent**. That is
not a preference or a licence convenience. It is a capability difference that
decides whether the question can be answered at all:

> **OpenFOAM's standard solvers have no native solidification/melting model.**

Its `chtMultiRegionFoam` resolves conjugate heat transfer beautifully — hot
water conducting into a solid capsule — but with **sensible heating only**.
No latent heat. No phase change. For a study whose entire premise is that a
phase-change material stores heat *in its phase change*, a solver that cannot
melt the material can only ever show the uninteresting half of the physics.

The Rajasthan OpenFOAM case is honest about this, and its own documentation
records the limit: Regime 0 only, no phase change modelled, retained here at
`archive/openfoam_legacy/` for the record.

ANSYS Fluent has the **enthalpy-porosity** solidification/melting model built
in. That is the model this study needs, and it is why the Tamil Nadu port
changed CFD tools.

| | Rajasthan (Manvitha) | Tamil Nadu (this study) |
|---|---|---|
| CFD solver | OpenFOAM `chtMultiRegionFoam` | ANSYS Fluent 2026 R1 Student |
| phase change in CFD | **not modelled** — sensible heating only | **enthalpy-porosity**, melt front resolved |
| CFD coverage | Regime 0 only | all 3 regimes, all 4 shortlisted PCMs |
| tank volume | 50 L | **100 L** (project instruction; collector scaled to keep 40 L/m², the low end of IS 12976:2023) |
| surrogate | XGBoost | **stacked ensemble**, selected over 5 families in all 9 pairs |
| tank model | hers | **hers, adopted unchanged** |

The last row matters. The tank model is Manvitha's own code, taken as it is
rather than reimplemented, so a difference in results is a difference in
*inputs*, not in method. Absolute kWh figures are not comparable between the
two states — the tanks are different sizes — but the algorithms, gates and
pass/fail criteria are.

---

## What we actually do in Fluent

A single-capsule unit cell: a half-disk capsule inside a water annulus,
meshed in gmsh, solved 2-D planar. The capsule starts **solid at 30 °C** and
sits in water held at **70 °C**, the collector delivery temperature, for a
six-hour charging window. Geometry, PCM identity and flow rate are read from
the optimiser's own output — nothing is typed in by hand.

Three things come out of it:

1. **Melt curves for all four PCMs** on one mesh under one duty, so the only
   difference between the curves is the material. C25 melts most, C26 and
   RT57HC share a melt point and the higher-conductivity one melts more,
   PureTemp 58 melts least. The ordering follows melt point and conductivity
   exactly as the physics predicts.
2. **A flow-rate sweep** across the design space (0.010 / 0.030 / 0.050 kg/s)
   showing the benefit saturating: tripling flow adds 0.097 to the melt
   fraction, raising it a further 1.7× adds only 0.021. The optimiser settled
   between 0.027 and 0.039 kg/s — in the bend of that curve, not at its top.
   The CFD never saw the tank model, the weather or the demand profile, so
   that agreement is an independent check.
3. **The whole-system geometry** — tank, capsules and collector panel in one
   case — confirming the heat path end to end.

### Stated limits

- The mesh is a **half-slice with a symmetry plane**, so buoyancy-driven
  convection in the melt is excluded. That is precisely the enhancement the
  tank model carries empirically, which is the division of labour, not an
  oversight.
- The solver runs **first-order upwind**, more diffusive than second order, so
  melt fractions are conservative. It is the only setting under which all four
  PCMs solve, and a comparison needs identical settings. **Read the ordering,
  not the absolute values.**
- The **Student licence allows one session at a time**, so the PCM runs are
  strictly sequential.
- The whole-system case runs **energy-only with momentum frozen**, so it shows
  the heat path, not melting. Melting evidence is the capsule cases.

---

## In one line

The tank model decides the design because it is the only thing fast enough to
search; Fluent checks the physics the tank model assumes, and it is Fluent
rather than OpenFOAM because OpenFOAM cannot melt the PCM.

---

*Code: `src/simulation/` (tank model), `ansys/` (Fluent cases),
`ansys/HOW_TO_RUN_ANSYS.md` (how to run, including the manual GUI route).
Full CFD history — including a defect that made an earlier set of runs report
no melting at all, and the seven hypotheses it took to make C25 converge — is
in `docs/CFD_VERIFICATION.md`.*
