# Phase 5 Plots — Design-of-Experiments Dataset

Files: `phase5_doe_coverage.*`, `phase5_outcome_distribution.*`.
Data source: `results/uttarakhand/design_cases.parquet` (all 215 generated cases).

---

## Plot 1 — DOE sample coverage

**What it is**: All 215 DOE cases plotted in the `capsule_diameter_m` vs `flow_rate_kg_s`
plane, colored by validity (green = valid, red = rejected), with markers
distinguishing sampling origin:
- Circles: Latin Hypercube Sampling (LHS) draws
- Diamonds: Boundary extreme cases
- Stars: Baseline reference cases

**What we infer**:
- The red rejected cases cleanly occupy the vertical strip where `capsule_diameter_m < 0.04 m`.
  This accounts for exactly $73 / 215$ cases ($34.0\%$), close to the theoretical
  proportion of the diameter interval below the $0.02\text{ m}$ thickness limit.
- The remaining 142 valid cases achieve balanced, space-filling coverage across the
  entire valid parameter space ($0.04 \le d \le 0.08\text{ m}$ and $0.010 \le \dot{m} \le 0.050\text{ kg/s}$)
  without clustering or voids.
- Boundary points anchor the four corners of the parameter envelope, ensuring the
  surrogate model does not extrapolate near design boundaries.

**How to justify it**: *"This plot visually confirms the fidelity of our sampling
strategy. The rejections are not random sampling failures; they reflect the exact
conduction-thickness physics defined in Phase 2. The remaining 142 points provide
an unbiased, space-filling Latin Hypercube foundation for surrogate training."*

---

## Plot 2 — Outcome distribution across 142 valid DOE cases

**What it is**: Side-by-side histograms of simulation outcomes across all 142 valid
cases:
- Left: Useful annual energy delivered ($E_{\text{useful}} \in [1509, 1627]\text{ kWh}$)
- Right: Annual solar fraction ($\text{SF} \in [0.28, 0.41]$)

**What we infer**:
- Both metrics exhibit multi-modal distributions, reflecting physical differences
  across Uttarakhand's 5 distinct climate clusters (e.g., higher elevation regimes
  with lower ambient mains temperatures vs. lower-elevation valley regimes).
- All outcomes are physically bounded and continuous: no negative energies, no
  unphysical solar fractions ($> 1.0$), and no numerical convergence crashes.
- The spread confirms that the sampled design variations produce meaningful,
  learnable performance differences across the parameter space.

**How to justify it**: *"The smooth outcome histograms confirm the robustness of
the simulator over 142 independent annual simulations. The multi-modal shape reflects
the real geographic diversity of Uttarakhand's mountain climate regimes rather
than numerical artifacts."*
