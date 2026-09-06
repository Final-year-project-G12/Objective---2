# Phase 2 Plots — Geometry & Constraint Engine

Files: `results/tamilnadu/plots/{static,interactive}/phase2_validity_map.*`,
`phase2_ergun_hydraulics.*`. Code: `src/plots/make_plots.py::phase2_validity_map`,
`phase2_ergun_hydraulics`.

---

## Plot 1 — Design-space validity map

**What it is**: every combination of `capsule_diameter_m` (0.02–0.08 m, 61
steps) and `n_capsule` (8–24) at a fixed mid-range flow rate (0.030 kg/s),
each colored by what `check_design()` returned for it: green = valid, red
= `bounds_violation`. 1,037 points, computed directly — no simulation
involved, just the deterministic Phase 2 geometry gate.

**What we infer**: the boundary between red and green is a **perfectly
vertical line at diameter = 0.04 m**, independent of capsule count. That
is exactly what the math predicts: for a sphere, PCM thickness (max
conduction distance) = diameter/2, and `design_bounds_shared.yaml`
requires thickness ≥ 0.02 m — so diameter must be ≥ 0.04 m, for *any*
capsule count. The plot shows the constraint engine enforcing this rule
consistently across the entire count range, with no stray red points on
the green side or vice versa (which would indicate a bug — e.g., a
constraint evaluated inconsistently, or a random/nondeterministic result).

**How to justify it (viva/report)**: *"This isn't a hand-picked example —
it's every point in the allowed diameter×count grid. The fact that the
red/green split is a single straight vertical line, not a scatter or a
fuzzy boundary, is direct visual evidence that the geometry engine is
deterministic and that this specific rejection reason
(`bounds_violation`, from the derived thickness bound) is a real,
consistent geometric fact about spheres — not a bug that only triggers
for some designs."* This is also the plot that explains why Phase 5's DOE
rejected exactly 70/215 cases (≈32.6%, matching the ≈33% of the diameter
range below 0.04 m) — point to this figure when that number comes up.

---

## Plot 2 — Ergun-equation pressure drop vs flow rate

**What it is**: pressure drop (Pa) vs flow rate (0.002–0.10 kg/s) for four
capsule diameters (0.02, 0.04, 0.06, 0.08 m) at a fixed representative void
fraction (0.90) and bed length (0.10 m), computed directly from
`compute_hydraulics()` — the same function the simulator calls every
timestep. The green shaded band marks the permitted flow range
(0.010–0.050 kg/s).

**What we infer**: every curve is monotonically increasing (more flow →
more pressure drop, always) and smaller capsules produce steeper curves
(smaller diameter → more surface area / more resistance per unit bed
length in the Ergun equation) — both are the physically-required
directions. Within the permitted flow band, pressure drop stays in the
sub-Pa-to-few-Pa range for all four diameters — nowhere near the 3.5 bar
(350,000 Pa) safety limit, which is why "pressure_drop_limit" never showed
up as a rejection reason anywhere in this project's DOE run.

**How to justify it**: *"This is the Ergun equation (1952), a standard,
citable packed-bed correlation — not something derived from scratch. The
curves behave exactly as the textbook equation predicts: monotonic in
flow, and steeper for smaller particles. That the permitted flow range
sits far below the pressure-drop safety limit here also explains, from
first principles, why our optimizer never needed to reject a candidate
for excessive pressure drop — it's a geometric consequence of this tank
size and flow range, not something we assumed away."*
