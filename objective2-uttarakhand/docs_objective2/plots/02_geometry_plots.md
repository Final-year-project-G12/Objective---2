# Phase 2 Plots — Geometry & Constraint Engine

Files: `results/uttarakhand/plots/{static,interactive}/phase2_validity_map.*`,
`phase2_ergun_hydraulics.*`. Code: `src/plots/make_plots.py::phase2_validity_map`,
`phase2_ergun_hydraulics`.

---

## Plot 1 — Design-space validity map

**What it is**: Every combination of `capsule_diameter_m` (0.02–0.08 m, 61 steps)
and `n_capsule` (8–24) at a fixed mid-range flow rate (0.030 kg/s), each colored
by what `check_design()` returned for it: green = valid, red = `bounds_violation`.
1,037 points computed deterministically via Phase 2 geometry constraint gates.

**What we infer**: The boundary between red and green is a **perfectly vertical
line at diameter = 0.04 m**, completely independent of capsule count.
This confirms the geometric physics of spherical encapsulation:
- Conduction thickness (maximum thermal diffusion distance) = $d / 2$.
- `configs/design_bounds_shared.yaml` mandates thickness $\ge 0.02\text{ m}$.
- Therefore, $d \ge 0.04\text{ m}$ is required for any spherical capsule regardless
  of count.
- The constraint engine enforces this boundary strictly with zero false passes or
  nondeterministic rejections across the entire grid.

**How to justify it (viva/report)**: *"This is comprehensive visual evidence that
the geometry engine is deterministic and consistent. The transition at 0.04 m
directly explains why Phase 5's Latin Hypercube DOE rejected exactly 70 of 215
cases (32.6%) — corresponding directly to the one-third of the diameter interval
between 0.02 m and 0.04 m."*

---

## Plot 2 — Ergun-equation pressure drop vs flow rate

**What it is**: Pressure drop (Pa) vs flow rate (0.002–0.10 kg/s) for four
capsule diameters (0.02, 0.04, 0.06, 0.08 m) at representative bed void fraction
(0.90) and bed length (0.10 m), computed via `compute_hydraulics()` using the
classical Ergun (1952) packed-bed equation. The green shaded band highlights the
permitted flow operating envelope (0.010–0.050 kg/s).

**What we infer**:
1. Every curve is strictly monotonically increasing with flow rate ($\Delta P \propto v + v^2$).
2. Smaller capsule diameters create steeper hydraulic resistance curves due to
   higher specific surface area per unit bed volume.
3. Within the permitted 0.010–0.050 kg/s flow envelope, the maximum pressure drop
   remains below 0.01 Pa. This is negligible compared to the system pressure-drop
   ceiling of 3.5 bar (350,000 Pa).

**How to justify it**: *"The hydraulic model relies on standard, citable packed-bed
formulations (Ergun 1952). The curves behave smoothly and monotonically. The fact
that pressure drop in this 50 L tank remains orders of magnitude below the pump
and tank rating confirms from first principles why hydraulic pressure drop never
acted as an active constraint limit in Uttarakhand's optimization search."*
