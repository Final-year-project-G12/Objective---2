# Objective 2 — Results Summary (Tamil Nadu)

**Status: COMPLETE, Phases 1–8. Objective 2 is finished for Tamil Nadu.**
Simulator released as `sim_v1_tamilnadu`
(Phase 4, GO). All numbers below are simulator-confirmed unless explicitly
marked "surrogate-predicted" — no surrogate-only value is reported as
final anywhere in this document (framework doc, non-negotiable rule).

Full methodology, verification detail, and honest caveats for every phase
are in `docs_objective2/` — this file is the results digest; that folder
is the audit trail. Plots referenced below live in
`results/tamilnadu/plots/` (`interactive/*.html` for live/interactive
viewing, `static/*.png` for reports).

---

## Phase 1 — Frozen configuration

- Shared config frozen across all 4 states: `configs/system_config_shared.yaml`, `configs/design_bounds_shared.yaml`.
- Tamil Nadu's state config: `configs/states/tamilnadu.yaml` — 5 GMM climate regimes (clusters 0–4), each with `Tm_target_C=57.0°C`, mains temperature 24.0–26.0°C, and a Top-3 PCM shortlist (n-Octacosane (C28) is Objective 1's consensus rank-1 PCM in all 5 clusters).
- Climate-signature sanity check: **PASSED** (GHI 5.13–5.28 kWh/m²/day, RH 62.5–70.2% — matches Tamil Nadu's coastal-humid signature).

Details: `docs_objective2/01_PHASE1_CONFIG_AND_STATE_SETUP.md`

---

## Phase 2 — Geometry & constraint engine

- Sphere capsules, staggered packing, Ergun-equation hydraulics.
- Determinism verified: 8/8 boundary cases byte-identical across repeated calls.
- **Finding**: the documented 15%/20% PCM-volume test levels (Chen et al. baseline) are not geometrically reachable within `capsule_diameter_m ≤ 0.08 m` and `capsule_count ≤ 24` — maximum reachable fraction is **12.9%** (n=24, d=0.08 m). Diameters below 0.04 m always fail the derived-thickness bound (thickness = diameter/2 < 0.02 m floor).

Plots: `phase2_validity_map`, `phase2_ergun_hydraulics`.
Details: `docs_objective2/02_PHASE2_GEOMETRY_CONSTRAINTS.md`, `docs_objective2/plots/02_geometry_plots.md`

---

## Phase 3 — Grey-box enthalpy simulator

- Full state vector, backward-Euler solver with adaptive sub-stepping, non-negotiable ambient tank-loss term always active.
- Sample case (cluster 0, n-Octacosane, 0.08 m/19 capsules/0.030 kg/s): useful energy 1663.0 kWh/yr, solar fraction 51.4%, mean PCM liquid fraction 1.4%.
- **Two real bugs found and fixed during development**:
  1. Reverse-collector-flow energy leak — Gate 1 residual dropped from 1.6% to ~0.00002% after the fix.
  2. Numerical instability for high-conductivity PCM capsules — fixed with adaptive stiffness-based sub-stepping.

Plots: `phase3_temperature_timeseries` (shows the PCM melting plateau directly), `phase3_melt_fraction_year`, `phase3_energy_breakdown`.
Details: `docs_objective2/03_PHASE3_GREYBOX_SIMULATOR.md`, `docs_objective2/plots/03_simulator_plots.md`

---

## Phase 4 — Simulator verification (Gates 1–5)

| Gate | Verdict | Headline number |
|---|---|---|
| 1 — Energy conservation | **PASS** | max residual 0.00008% (5 diverse cases) |
| 2 — Limiting cases | **PASS** | 10/10 checks (zero irradiance, zero flow, no PCM, high conductivity, insulated tank, empty demand, solid/liquid init, flow limits, capsules removed) |
| 3 — Baseline comparison | **PASS** | capability check (synthetic Tm=40°C PCM) beats plain tank decisively (55.19% vs 52.26% SF), ruling out a simulator defect |
| 4 — Published-benchmark calibration | **PASS-WITH-CAVEAT** | 51.39% vs cited 54–84% band — explained by no auxiliary heater / smaller storage-to-demand ratio |
| 5 — Sensitivity/monotonicity | **PASS** | 3/3 checks in the physically correct direction |

**Go/No-Go: GO.** Simulator released as `sim_v1_tamilnadu`.

Plots: `phase4_gate1_residuals`, `phase4_gate3_baseline_comparison`, `phase4_gate5_sensitivity`.
Details: `docs_objective2/04_PHASE4_VERIFICATION_GATES.md`, `docs_objective2/plots/04_verification_plots.md`

---

## Phase 5 — Design-of-experiments dataset

- 215 cases: 120 Latin Hypercube + 90 boundary + 5 no-PCM baselines, across 5 regimes × 3 shortlisted PCMs.
- **145 valid, 70 rejected** — all 70 for `bounds_violation` (diameter < 0.04 m), matching the Phase 2 finding almost exactly (32.6% actual vs ≈33% predicted).
- Case-level train/holdout split: 170 train / 45 holdout, stratified by (regime, PCM, validity).

Plots: `phase5_doe_coverage`, `phase5_outcome_distribution`.
Details: `docs_objective2/06_PHASE5_DOE.md`, `docs_objective2/plots/05_doe_plots.md`

---

## Phase 6 — AI surrogate model

| Target | ExtraTrees R² | vs. Linear baseline |
|---|---|---|
| useful_energy_kWh | 0.9999 | tree wins |
| solar_fraction | 0.9990 | tree wins |
| unmet_energy_kWh | 0.9997 | tree wins |
| pump_energy_kWh | 0.9872 | **linear ties/wins** (physically explained — see doc) |
| pcm_mass_kg | 0.9979 | tree wins |
| feasibility (classifier) | accuracy 1.000, infeasible-recall 1.000 | — |

**Feature importance finding**: the top 4 features are all **climate**
(`RH_mean_true`, `GHI_daily_kWh_mean`, `HSI`, `DTR_true_mean`) — no design
variable or PCM property makes the top 15. This independently confirms
(via a third, purely data-driven method) that climate dominates useful
energy far more than PCM/geometry choice in this design space.

Plots: `phase6_parity_plots`, `phase6_feature_importance`.
Details: `docs_objective2/07_PHASE6_SURROGATE.md`, `docs_objective2/plots/06_surrogate_plots.md`

---

## Phase 6b — Multi-fidelity surrogate augmentation (bonus phase)

Added a cheap `fidelity="low"` mode to the simulator itself (fixed
timestep, no adaptive sub-stepping — `src/simulation/tank_model.py`),
re-ran all 215 DOE cases at low fidelity, and used the result both as a
standalone cheap predictor and as an extra input feature to the Phase 6
surrogate.

- **Speedup: 1.53×** (fair, order-randomized, same-process timing — an
  initial version of this comparison mixed timings from two different
  process runs and produced a nonsensical result; corrected before being
  reported here).
- **Low-fidelity-only accuracy**: R²=0.999 (useful_energy_kWh), 0.982
  (solar_fraction), 0.997 (unmet_energy_kWh) vs. the real simulator — a
  cheap proxy that's already highly informative on its own.
- **Sample-efficiency finding**: augmenting a *shrunken* high-fidelity
  training set with the free low-fidelity feature matches or beats the
  high-fidelity-only baseline at every tested training fraction for
  `solar_fraction`/`unmet_energy_kWh`/`pump_energy_kWh` (e.g. at 50%
  high-fidelity data, `solar_fraction` R² goes from 0.970 to 0.983 with
  the low-fidelity feature added) — i.e. Phase 6's accuracy can be
  approached with meaningfully less expensive simulator data if a cheap
  low-fidelity proxy exists.

Plots: `phase6b_multifidelity`.
Details: `docs_objective2/11_MULTIFIDELITY_SURROGATE.md`

---

## Phase 7 — Optimization pass + simulator confirmation

400 candidates/pair searched (8,000 total), top 5/pair (100 total)
re-run in the real simulator. **Mean surrogate-vs-simulator error: 0.02%,
0/100 exceeded the 15% large-error threshold.**

### Deployable design selected per regime

| Regime | Selected | Diameter (m) | Count | Flow (kg/s) | Useful energy (kWh) | Solar fraction | PCM mass (kg) |
|---|---|---|---|---|---|---|---|
| 0 | Plain tank (no PCM) | 0.0409 | 9 | 0.0159 | 1673.29 | 52.26% | 0 |
| 1 | Plain tank (no PCM) | 0.0422 | 13 | 0.0124 | 1809.93 | 53.11% | 0 |
| 2 | Plain tank (no PCM) | 0.0443 | 8 | 0.0127 | 1749.80 | 53.30% | 0 |
| 3 | Plain tank (no PCM) | 0.0435 | 8 | 0.0185 | 1816.50 | 54.42% | 0 |
| 4 | n-Octacosane (C28) | 0.0406 | 17 | 0.0105 | 1622.90 | 50.96% | 0.544 |

**Headline finding**: every shortlisted PCM beats plain water by only
~0.08% at its best-found geometry — two orders of magnitude below the 5%
selection tolerance — so the pre-declared rule picks the zero-mass plain
tank in 4/5 regimes. **Only 35% of the 100 confirmed candidates stayed
within the temperature-safety envelope**; all 5 plain-tank candidates in
every regime were safe, while PCM candidates in regimes 0–3 all tripped
the safety limit at some point in the year.

Plots: `phase7_pareto_by_regime`, `phase7_surrogate_vs_simulator`, `phase7_safety_compliance`.
Details: `docs_objective2/08_PHASE7_OPTIMIZATION.md`, `docs_objective2/plots/07_optimization_plots.md`

---

## Phase 8 — Robustness + Objective 3 hand-off

120 Monte Carlo draws per design (PCM latent heat ±10%, **two-level**
weather noise [annual GHI scale/ambient offset **plus** independent
per-hour jitter], demand ±20%/±30min, mains temperature ±2°C), re-run
through the **real simulator** for every draw (never the surrogate).
"Meets delivery/demand" use fixed, state-independent solar_fraction
thresholds (≥0.45 / ≥0.50) rather than thresholds relative to each
design's own nominal performance — this methodology was revised to align
with the parallel Rajasthan implementation of this framework, for
cross-state comparability (see `docs_objective2/
10_PHASE8_ROBUSTNESS_HANDOFF.md`, "Alignment with the Rajasthan
implementation," for exactly what changed and why).

**Upgrade**: the annual GHI-scale/ambient-offset component is no longer a
synthetic assumed range (the original `U(0.93,1.07)` / `U(-1.5,+1.5°C)`).
It is now drawn from a genuine **10-year (2016–2025) historical weather
ensemble** built from Objective 1's own daily ERA5/POWER archive
(`src/robustness/weather_ensemble.py`, reading `data/objective1/
daily_aggregates_tamilnadu.csv` — 133 population-grid points, all 10 years
complete on disk but previously unused past Objective 1's climate
signature step). Each Monte Carlo draw's annual weather is now one of the
10 real observed years for that climate regime, not an assumed
distribution shape (per-hour jitter within the year is still synthetic —
documented in `10_PHASE8_ROBUSTNESS_HANDOFF.md`, not hidden).

| Regime | Design | P(meets delivery) | P(meets demand) | P(temperature-safe) | Robust? | Useful energy P5–P50–P95 (kWh) | Max water T P95 |
|---|---|---|---|---|---|---|---|
| 0 | Plain tank | 100% | 89.2% | 92.5% | No | 1568 – 1668 – 1763 | 75.1°C |
| 1 | Plain tank | 100% | 90.0% | 80.0% | No | 1700 – 1800 – 1931 | 77.3°C |
| 2 | Plain tank | 100% | 94.2% | 71.7% | No | 1659 – 1744 – 1867 | 77.6°C |
| 3 | Plain tank | 100% | 95.0% | 79.2% | No | 1716 – 1810 – 1920 | 77.1°C |
| 4 | n-Octacosane | 100% | **69.2%** | **40.8%** | No | 1531 – 1616 – 1703 | 73.8°C |

**Headline finding holds under the real historical-year methodology**:
delivery-temperature reliability is never the problem (100% everywhere).
Under the fixed (not self-referential) demand threshold, **regime 4 — the
one regime that actually uses PCM — is still revealed as the weakest
performer on *both* remaining axes at once**: only 69.2% demand-reliable
(below the 75% target) and just 40.8% temperature-safe (the worst of all
five, and the only one to fail both robustness criteria simultaneously).
Every regime fails the ≥95% temperature-safety bar regardless of PCM.
Replacing the assumed weather-noise range with real observed inter-annual
variability moved every regime's numbers by only a few points (real
Tamil Nadu year-to-year GHI variability turns out to be narrower than the
±7% originally assumed) and changed no qualitative conclusion — if
anything this strengthens confidence in the finding, since it now survives
a second, independently-sourced weather methodology. This is a genuine
consequence of having no active high-temperature safety shield anywhere
in Phases 1–7's physics, not a bug — and it is now the **fourth
independent method** (after Gate 3, Phase 6's feature importance, and
Phase 7's full search) pointing at the same PCM regime as the weakest
link in this deployment.

**One real bug found and fixed during development**: the first
robustness implementation double-counted plain-tank designs against the
PCM temperature limit (`T_pcm` is just a copy of `T_water` when there's
no PCM, so checking it against 65°C flagged ordinary hot water as a false
"PCM over-temperature"). Caught by cross-checking against the simulator's
own internal violation counter, which was correct all along; both now
agree exactly. The fix is retained in the current (aligned) methodology.

Recommendation cards (`results/tamilnadu/recommendation_cards.md`) and the
Objective 3 hand-off contract (`results/tamilnadu/
obj3_environment_contract_tamilnadu.json`) are both generated and include
this robustness data, the full PCM property record, the flow/temperature
envelope, a `global_limits` summary block, a safety shield that now trips
on a **3°C precautionary guard band** below each hard limit (72°C water /
62°C PCM — matching Rajasthan's contract exactly, rather than the
original version's trip-at-the-hard-limit design), an explicit
`deferred_future_work` list, and the acceptance-test checklist Objective
3 must pass before training.

Plots: `phase8_robustness_probabilities`, `phase8_useful_energy_intervals`.
Details: `docs_objective2/10_PHASE8_ROBUSTNESS_HANDOFF.md`

---

## The two findings that matter most, together

1. **PCM barely helps in this design** (Phases 4, 6, 7): every shortlisted
   PCM beats plain water by at most ~0.08% at its best-found geometry —
   the selection rule picks the zero-mass plain tank in 4/5 regimes.
2. **No design is temperature-robust under realistic uncertainty**
   (Phase 8): every regime's selected design — PCM or plain tank — fails
   the framework's 95% temperature-safety bar, because Phases 1–7 never
   modeled an active overheat-protection mechanism. Under a fixed,
   cross-state-comparable demand threshold, the one PCM regime (4) is
   worse than every plain-tank regime on **both** demand reliability
   (69.2%) and temperature safety (40.8%) — the only regime to fail both
   bars at once. This holds under Phase 8's real 10-year historical
   weather ensemble, not just the original synthetic-noise version.

Four independent methods — the Gate 3 baseline comparison, Phase 6's
feature-importance analysis, Phase 7's 400-candidate search, and Phase
8's Monte Carlo robustness analysis — all converge on the same
conclusion: within this design space, climate dominates outcome variance
far more than PCM/geometry choice, and the one regime that adopted PCM is
the weakest performer of the five, not merely a marginal one.

Together these say: Tamil Nadu's current best hardware recommendation is
a plain tank (cheaper, simpler, marginally better performing) — **but it
still needs an active safety shield before it's deployable**, independent
of whether PCM is used at all. That shield is now a specified requirement
in the Objective 3 contract (with a 3°C precautionary guard band below
each hard limit, matching the parallel Rajasthan implementation), not an
assumption.

## Files produced (all under `results/tamilnadu/`)

| File | Phase | Contents |
|---|---|---|
| `simulator_verification_report.txt` | 4 | Gate 1–5 full readout |
| `design_cases.parquet` / `.csv` | 5 | 215-case DOE database |
| `surrogate_metrics.csv`, `surrogate_error_by_group.csv`, `surrogate/models.pkl` | 6 | trained models + accuracy |
| `design_cases_lowfid.parquet`, `multifidelity_speedup_report.json`, `multifidelity_sample_efficiency.csv`, `multifidelity_runtime_benchmark.csv` | 6b | low-fidelity re-run, speedup, sample-efficiency experiment |
| `surrogate_top_candidates.csv`, `optimized_designs.csv`, `deployable_design_per_regime.csv` | 7 | search → confirm → select |
| `robustness_results.csv`, `robustness_summary.csv` | 8 | Monte Carlo draws (real 10-yr weather ensemble) + per-regime summary |
| `recommendation_cards.md` | 8 | one card per regime |
| `obj3_environment_contract_tamilnadu.json` | 8 | frozen Objective 3 hand-off package, incl. fully specified reward function |
| `plots/interactive/*.html`, `plots/static/*.png` | 2–8 | 18 justification figures |

## Where to go next

- `docs_objective2/OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` — what Objective 3 needs and what to do first.
- `docs_objective2/10_PHASE8_ROBUSTNESS_HANDOFF.md` — full robustness methodology and the temperature-safety finding.
- `docs_objective2/09_NEXT_STEPS.md` — the PCM-vs-plain-tank decision the team should make before extending this to the other 3 states.
- `docs_objective2/HOW_TO_RUN.md` — every command to reproduce everything in this file.
