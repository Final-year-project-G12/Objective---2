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

**What we infer** (Uttarakhand, final run post-widening — see `11_MULTIFIDELITY_SURROGATE.md`):
- **Execution speedup**: $2.02\times$ ($303.7\text{s} \to 150.1\text{s}$ across
  215 both-valid cases) — genuinely **larger** than Tamil Nadu's $1.53\times$
  and larger than Uttarakhand's own pre-widening result ($1.58\times$). The
  widened design space (doc 13) now includes designs with up to 16.8% PCM
  volume fraction (vs. ~12.9% before), and more PCM mass per design triggers
  adaptive sub-stepping more often in high fidelity — exactly the scenario
  this speedup mechanism is designed to exploit.
- **Sample efficiency**: For `solar_fraction` and `useful_energy_kWh`, the
  multi-fidelity-augmented model matches or beats high-fidelity-only at
  every training fraction (e.g. `useful_energy_kWh` at 25%: $0.99955$ vs.
  $0.99915$; at 100%: $0.99989$ vs. $0.99979$) — a cleaner result than the
  pre-widening run, with more training rows available at every fraction
  thanks to the larger valid DOE set.

**How to justify it (viva/report)**: *"Rather than simply citing multi-fidelity
theory from the literature, our framework implements a concrete two-tier architecture:
an inexpensive single-step simulator feeding a machine learning correction layer.
This demonstrates that high surrogate accuracy can be maintained even when
computational resources allow only a fraction of full-physics simulations to be run."*
