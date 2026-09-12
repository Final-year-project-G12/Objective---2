# 11 — Phase 6b Audit: Multi-Fidelity Surrogate Augmentation

Files: `src/simulation/tank_model.py` (`fidelity` parameter),
`src/surrogate/multifidelity.py`. Run:
```
python pipeline.py --state uttarakhand --stage multifidelity
```
Output: `results/uttarakhand/design_cases_lowfid.parquet` (+ `.csv`),
`multifidelity_runtime_benchmark.csv`, `multifidelity_speedup_report.json`,
`multifidelity_sample_efficiency.csv`.

This is a bonus phase, not one of the framework doc's 8 numbered phases —
it exists specifically to close an external audit's gap: "Multi-fidelity
surrogate not explored" (citing Lee et al., "Efficient design optimization
using multi-fidelity surrogate modeling for a thermal battery," arXiv
2026, and a related DHW-ANN surrogate paper, both describing a cheap
low-fidelity model feeding a high-fidelity correction layer).

---

## What "low fidelity" means here

`src/simulation/tank_model.py`'s `run_year()` already had an *adaptive*
sub-stepping scheme (Phase 3): near the PCM melt band, or whenever a
stiffness check says the PCM's thermal time constant is short relative to
the timestep, it silently increases the number of sub-steps per hour (up
to 60) to stay numerically stable. A new `fidelity` parameter
(`"high"` = this existing behaviour, unchanged; `"low"` = new) disables
both mechanisms entirely when set to `"low"`: exactly one fixed-size
sub-step per hour, regardless of PCM state.

`fidelity` is threaded through `run_case()` unchanged everywhere else;
every Phase 4/5/7/8 result in this project uses the default
`fidelity="high"`. `fidelity="low"` is used *only* by this Phase 6b
module.

---

## Methodology

1. **Low-fidelity re-run**: every one of Phase 5's 215 DOE case specs
   (same deterministic generation, so `case_id`s match exactly) is re-run
   at `fidelity="low"`, `record_hourly=False`.
2. **Low-fidelity-only accuracy**: for valid cases at both fidelities,
   low-fidelity output is compared directly against the already-recorded
   Phase 5 high-fidelity ground truth (R², MAE, mean bias %) — is the
   cheap version informative on its own?
3. **Fair runtime benchmark**: a fresh, order-randomized, same-process
   re-timing of both fidelities for every case. Randomizing which fidelity
   runs first per case, in the same process, removes timing bias.
4. **Sample-efficiency experiment**: the same ExtraTrees architecture
   Phase 6 uses is trained at shrinking high-fidelity training fractions
   (100/75/50/25% of Phase 5's usable training rows), with and without the
   free low-fidelity prediction as an extra input feature, always evaluated
   on Phase 6's *original, fixed* hold-out set.

---

## Expected results (reference: Tamil Nadu Phase 6b run)

The Tamil Nadu Phase 6b run (the only fully-executed Phase 6b to date)
produced these benchmark numbers for comparison:

**Speedup: 1.53×.** Modest — because this project's actual shortlisted PCMs
(PureTemp 58, Tm=58°C) spend nearly the entire simulated year outside the
melt band (mean liquid fraction ≈ 0–2% annually in the warmer regimes, and
only regime 2's PureTemp 58 cycles meaningfully). A design space with more
actively-cycling PCM would likely show a larger speedup.

**Low-fidelity-only accuracy** (Tamil Nadu reference):

| Target | R² | Mean bias |
|---|---|---|
| useful_energy_kWh | 0.999 | −0.03% |
| solar_fraction | 0.982 | +0.04% |
| unmet_energy_kWh | 0.997 | −0.05% |
| pump_energy_kWh | 0.689 | +594% (near-null signal — see note below) |

The `pump_energy_kWh` row looks alarming in isolation but isn't: pump energy
at this project's reachable design bounds is ~1e-11 kWh/year (functionally
zero). A "594% mean bias" on a near-null quantity is low-fidelity noise
on a near-null signal, not a real surrogate failure.

**Sample-efficiency** (Tamil Nadu reference, same architecture as Phase 6):
- For `solar_fraction`, multi-fidelity-augmented training matches or beats
  high-fidelity-only at every fraction below 100%.
- For `useful_energy_kWh`, no gap (already at the R² ceiling).

For Uttarakhand, regime 2's PCM design actually cycles meaningfully
(mean f_melt ≈ 34.4% in the Gate 3 capability check, and the selected
PureTemp 58 design has a non-negligible cycle fraction). This may produce
a *larger* speedup than Tamil Nadu's 1.53× for regime 2's cases, since
adaptive sub-stepping would trigger more frequently for an actively-cycling
PCM. Run this stage and check `multifidelity_speedup_report.json` to
confirm.

---

## Honest framing: this is a demonstration, not a production speedup claim

This experiment uses Phase 5's existing DOE cases — it demonstrates that
the multi-fidelity mechanism works and quantifies it, but it did not reduce
this project's own DOE runtime (Phase 5 already ran once at high fidelity
before this experiment existed). The practical payoff — actually cutting DOE
runtime via a low-fidelity pre-filter — is future work for the full
four-state rollout.

---

## Deferred / not attempted

- Gaussian-process uncertainty quantification — not part of this phase.
- Cross-state comparison of sample-efficiency gains: once Tamil Nadu,
  Rajasthan, Assam, and Uttarakhand all have Phase 5 data, this experiment
  can be run identically across all four states to report the
  sample-efficiency finding as a general result rather than a
  single-state demonstration.
