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

## Result (Uttarakhand, actual run)

**Final run (2026-09-14)**, against the fully-corrected pipeline (Objective 1
fixes, cluster-ID config fix, Tm-target retargeting, design-bounds
widening). This stage was regenerated from scratch
(`force_lowfid_rerun=True`) rather than reusing any cached low-fidelity
dataset from an earlier config — an earlier attempt at this had silently
reused a stale cache and produced nonsensical negative R² values; that
mistake is not repeated here.

**Speedup: 2.02×** (303.7s high-fidelity vs. 150.1s low-fidelity, 215
both-valid cases, fresh order-randomized same-process timing) — this time
genuinely **larger** than Tamil Nadu's 1.53× and larger than Uttarakhand's
own pre-widening result (1.58×). This is a real, physically-explained
effect: the widened design space (doc 13) now includes designs with up to
16.8% PCM volume fraction (vs. ~12.9% before), and more PCM mass per
design means adaptive sub-stepping triggers more often in high fidelity
— exactly the scenario this multi-fidelity mechanism is designed to
exploit. Unlike the earlier (pre-widening) run, where the speedup ceiling
was capped by how rarely any Uttarakhand design entered the melt band,
the widened space now genuinely exercises the adaptive stepping logic
more, and the speedup reflects that.

**Low-fidelity-only accuracy** (Uttarakhand, final — 215 both-valid cases):

| Target | R² | Mean bias |
|---|---|---|
| useful_energy_kWh | 1.000 | −0.0% |
| solar_fraction | 1.000 | −0.0% |
| unmet_energy_kWh | 1.000 | +0.0% |
| pump_energy_kWh | 1.000 | −0.0% |

The low-fidelity solver tracks the high-fidelity ground truth essentially
exactly on every target, even with the widened, more-actively-cycling
design space.

**Sample-efficiency** (Uttarakhand, final — same ExtraTrees architecture
as Phase 6, 112 candidate train rows, evaluated on Phase 6's fixed 30-row
hold-out set):

| Target | HF fraction | High-fidelity-only R² | Multi-fidelity-augmented R² |
|---|---|---|---|
| useful_energy_kWh | 25% | 0.99915 | 0.99955 |
| useful_energy_kWh | 50% | 0.99934 | 0.99963 |
| useful_energy_kWh | 100% | 0.99979 | 0.99989 |
| solar_fraction | 25% | 0.99993 | 0.99994 |
| solar_fraction | 50% | 0.99976 | 0.99989 |
| solar_fraction | 100% | 0.99996 | 0.99999 |
| pump_energy_kWh | 25% | 0.804 | 0.818 |
| pump_energy_kWh | 100% | 0.929 | 0.919 |

For `useful_energy_kWh` and `solar_fraction`, the multi-fidelity-augmented
model matches or beats high-fidelity-only at **every** training fraction —
a cleaner result than the pre-widening run, and consistent with Tamil
Nadu's own finding. `pump_energy_kWh` is a genuine coin-flip either way
(both models track a near-null target dominated by noise at these PCM
fractions, consistent with Phase 6's own finding that linear regression
already ties or beats ExtraTrees here) — no longer showing the small-sample
negative-R² artifact from the pre-widening 25%-fraction run, since the
widened dataset gives more training rows at every fraction.

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
