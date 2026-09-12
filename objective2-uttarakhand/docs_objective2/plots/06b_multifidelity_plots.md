# Phase 6b Plots — Multi-Fidelity Surrogate Augmentation

Files: `phase6b_multifidelity.*` (generated when `--stage multifidelity` is executed).
Data source: `results/uttarakhand/multifidelity_speedup_report.json` and
`multifidelity_sample_efficiency.csv`.

---

## Plot Structure & Intent

**What it is**: A dual-panel figure illustrating the computational and statistical
gains of multi-fidelity modeling (addressing audit recommendations citing Lee et al.
2026 and related DHW-ANN surrogate literature):
1. **Left panel**: Total simulator execution time across all 215 DOE cases at
   High Fidelity (adaptive sub-stepping up to 60 steps/hour near phase transition)
   versus Low Fidelity (fixed 1 step/hour, no melt-band escalation), with the
   empirical speedup factor annotated.
2. **Right panel**: Hold-out test $R^2$ for useful energy as a function of the
   fraction of high-fidelity training data utilized (100%, 75%, 50%, 25%),
   comparing the baseline high-fidelity-only model against the multi-fidelity
   augmented architecture that includes the cheap low-fidelity prediction as an
   additional feature.

**What we infer**:
- **Execution speedup**: The low-fidelity solver eliminates ODE sub-stepping
  overhead, delivering faster batch simulation while preserving macroscopic energy
  trends.
- **Sample efficiency**: When the high-fidelity training budget is restricted
  (e.g., down to 25% or 50% of cases), augmenting the surrogate with the free
  low-fidelity output recovers a substantial portion of the accuracy gap. This is
  especially pronounced for metrics sensitive to phase timing like `solar_fraction`.
- For `useful_energy_kWh`, the baseline high-fidelity surrogate is already near the
  $R^2 > 0.999$ ceiling with the full dataset, meaning the primary value of
  multi-fidelity modeling is enabling rapid preliminary design sweeps with far
  fewer expensive simulations.

**How to justify it (viva/report)**: *"Rather than simply citing multi-fidelity
theory from the literature, our framework implements a concrete two-tier architecture:
an inexpensive single-step simulator feeding a machine learning correction layer.
This demonstrates that high surrogate accuracy can be maintained even when
computational resources allow only a fraction of full-physics simulations to be run."*
