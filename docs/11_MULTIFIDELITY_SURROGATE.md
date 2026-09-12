# 11 — Phase 6b Audit: Multi-Fidelity Surrogate Augmentation (All Four States)

Files: `src/simulation/tank_model.py` (`fidelity` parameter),
`src/surrogate/multifidelity.py`. This is a **bonus phase**, not one of
the framework's 8 numbered phases — it exists to close an external
audit's "multi-fidelity surrogate not explored" gap (citing a
multi-fidelity thermal-battery design-optimization approach and a
related DHW-ANN surrogate paper).

## Status side by side

| State | Run? | Speedup | Notes |
|---|---|---|---|
| Tamil Nadu | **Yes — the only state this was actually executed for** | **1.53×** | Modest, because the shortlisted PCMs spend nearly the entire year outside the melt band |
| Rajasthan | No | — | Not run |
| Assam | No | — | Not run |
| Uttarakhand | Doc written; **stage not actually run** | Projected, not measured | `results/uttarakhand/` has no `multifidelity_*` output files; `11_…` explicitly says "reference: Tamil Nadu run" and projects a possibly-larger speedup for regime 2 (its actively-cycling PCM), pending someone actually running `--stage multifidelity` |

**Only Tamil Nadu has a real, executed multi-fidelity result.** The
other three states' equivalent docs (where they exist) are honest about
this — Uttarakhand's own `11_…` says "run this stage and check
`multifidelity_speedup_report.json` to confirm" rather than presenting
the projected number as measured.

## What "low fidelity" means (shared mechanism)

`tank_model.py`'s adaptive sub-stepping (near the PCM melt band, or
whenever a stiffness check finds the PCM's thermal time constant short
relative to the timestep) is disabled entirely when `fidelity="low"`:
exactly one fixed-size sub-step per hour regardless of PCM state. Every
Phase 4/5/7/8 result in every state uses `fidelity="high"` (unchanged);
`fidelity="low"` is used only by this Phase 6b module.

## Tamil Nadu's measured result (the only real data point)

| Target | R² (low-fidelity-only) | Mean bias |
|---|---|---|
| useful_energy_kWh | 0.999 | −0.03% |
| solar_fraction | 0.982 | +0.04% |
| unmet_energy_kWh | 0.997 | −0.05% |
| pump_energy_kWh | 0.689 | +594% (near-null-signal noise, not a real failure — pump energy is ~1e-11 kWh/year) |

Sample-efficiency: for `solar_fraction`, multi-fidelity-augmented
training matches or beats high-fidelity-only training at every
training-fraction below 100%; for `useful_energy_kWh`, no gap (already
at the R² ceiling).

## Literature review — why multi-fidelity modeling at all

- **Multi-fidelity surrogate modeling** — training a surrogate with both
  a cheap, approximate ("low-fidelity") data source and a smaller number
  of expensive, accurate ("high-fidelity") points — is a well-established
  technique for reducing the total simulation budget needed to reach a
  target surrogate accuracy in engineering design optimization,
  originally motivated by thermal-battery and related design-optimization
  work an external audit specifically flagged as a gap in this project's
  original Phase 6 (single-fidelity ExtraTrees only).
- **Reporting this as "a demonstration, not a production speedup claim"**
  (Tamil Nadu's own framing) is a deliberate, honest scoping choice: the
  experiment reuses Phase 5's already-completed high-fidelity DOE, so it
  did not actually reduce this project's own DOE runtime — the payoff
  (a genuine low-fidelity pre-filter cutting DOE runtime before Phase 5
  runs) is named as future work for a full four-state rollout, not
  claimed as already achieved.
- **Only Tamil Nadu having a real measured result** is itself worth
  stating plainly in any methods section — a projected number ("may
  produce a larger speedup") should never be presented with the same
  confidence as a measured one, and none of this project's docs blur
  that line for Rajasthan, Assam, or Uttarakhand.
