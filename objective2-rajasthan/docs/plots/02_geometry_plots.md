# Phase 2 Plots — Geometry & Constraint Engine (Rajasthan)

Files: `results/plots/{static,interactive}/phase2_validity_map.*`,
`phase2_ergun_hydraulics.*`. Code:
`src/plots/make_plots.py::phase2_validity_map`, `phase2_ergun_hydraulics`.
(Phase 2 is state-agnostic — these figures are identical to Tamil Nadu's
except the state label.)

## Plot 1 — Design-space validity map

**What it is**: every combination of `capsule_diameter_m` (0.02–0.08 m, 61
steps) × `n_capsule` (8–24) at a fixed mid-range flow (0.030 kg/s),
coloured by what `check_design()` returned: green = valid, red =
`bounds_violation`. ~1,000 points, computed directly from the
deterministic Phase 2 gate — no simulation.

**What we infer**: the red/green boundary is a **perfectly vertical line
at diameter = 0.04 m**, independent of capsule count. That is exactly the
math: for a sphere, PCM thickness = diameter/2, and
`design_bounds_shared.yaml` requires thickness ≥ 0.02 m, so diameter must
be ≥ 0.04 m for *any* count. No stray points on the wrong side (which
would indicate a nondeterministic or inconsistent constraint).

**How to justify it (viva/report)**: *"This is every point in the allowed
diameter×count grid, not a hand-picked example. A single straight vertical
split — not a fuzzy or scattered boundary — is direct visual evidence the
geometry engine is deterministic and this rejection reason is a real
geometric fact about spheres. It also explains why Phase 5's DOE rejected
exactly 54/165 cases (≈32.7 %, ≈ the fraction of the diameter range below
0.04 m) — point here when that number comes up."*

## Plot 2 — Ergun-equation pressure drop vs flow rate

**What it is**: pressure drop (Pa) vs flow (0.002–0.10 kg/s) for four
capsule diameters (0.02 / 0.04 / 0.06 / 0.08 m) at a representative void
fraction 0.90 and bed length 0.10 m, from `compute_hydraulics()` — the
same function the simulator calls every timestep. Green band = the
permitted flow range (0.010–0.050 kg/s).

**What we infer**: every curve is monotonically increasing (more flow →
more pressure drop) and smaller capsules give steeper curves (more surface
area / resistance per unit bed length) — both physically required. Within
the permitted band the pressure drop stays sub-Pa to a few Pa, nowhere
near the 3.5 bar (350 kPa) safety limit — which is why
`pressure_drop_limit` never appeared as a rejection reason anywhere in
the Rajasthan DOE.

**How to justify it**: *"This is the Ergun equation (1952), a standard
citable packed-bed correlation. The curves behave exactly as the equation
predicts — monotonic in flow, steeper for smaller particles — and the
permitted flow range sits orders of magnitude below the pressure-drop
safety limit, which is why the optimizer never had to reject a candidate
for pressure drop."*
