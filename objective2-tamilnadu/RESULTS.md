# Objective 2 — Results Summary (Tamil Nadu)

**Status: COMPLETE, Phases 1–8, AS OF THE 2026-09-13 RUN DESCRIBED BELOW.**
Simulator released as `sim_v1_tamilnadu` (Phase 4, GO). All numbers below
are simulator-confirmed unless explicitly marked "surrogate-predicted" —
no surrogate-only value is reported as final anywhere in this document
(framework doc, non-negotiable rule).

> ### 2026-09-12 → 2026-09-13 methodology revisions applied, in order
> Four deliberate, documented revisions were made to Objective 2 after it
> was first completed, and **everything below reflects all four, fully
> re-run end to end**:
> 1. **`Tm_target_C` retargeting** — Objective 1's climate-anchored
>    `Tm_target_C=57.0°C` (n-Octacosane-led shortlist) replaced per-regime
>    with a value derived from this tank's own simulated charging-hour
>    water temperature. **`docs_objective2/12_TM_TARGET_RETARGETING.md`.**
> 2. **`capsule_count` bound widened 24→37** (shared config, all 4
>    states) — the old bound capped reachable PCM-volume-fraction at
>    12.9%, short of the 15–20% literature levels this project cites.
>    **`docs_objective2/13_DESIGN_BOUNDS_WIDENING.md`.**
> 3. **Selection-rule scope correction** — Objective 2's actual problem
>    statement asks for the *optimal PCM design* (thickness, capsule
>    arrangement, count, flow rate), not whether to use PCM at all. The
>    zero-mass "plain tank" candidate — added by this implementation as a
>    diagnostic, never requested by the assignment — is no longer eligible
>    to win the final per-regime recommendation; it remains in
>    `optimized_designs.csv` for comparison only. Safety is reported on
>    every pick, never hidden, never used to silently fall back to a
>    non-PCM answer. **`docs_objective2/14_SELECTION_RULE_SCOPE_CORRECTION.md`.**
> 4. **Phase 8 historical weather ensemble** (independent of the above
>    three — see its own section below) — real 10-year observed annual
>    weather instead of an assumed noise range.
>
> Net effect: **every regime's Objective 2 recommendation is now a real,
> simulator-confirmed PCM design** — a first for this project. Phase 6b
> (multi-fidelity) still reflects the *original* pre-retargeting DOE and
> is flagged stale in its own section below; re-running it is optional
> future work, not required for Objective 2's core deliverable.

Full methodology, verification detail, and honest caveats for every phase
are in `docs_objective2/` — this file is the results digest; that folder
is the audit trail. Plots referenced below live in
`results/tamilnadu/plots/` (`interactive/*.html` for live/interactive
viewing, `static/*.png` for reports).

---

## Phase 1 — Frozen configuration

- Shared config frozen across all 4 states: `configs/system_config_shared.yaml`, `configs/design_bounds_shared.yaml` (`capsule_count.max` widened 24→37, see doc 13).
- Tamil Nadu's state config: `configs/states/tamilnadu.yaml` — 5 GMM climate regimes (clusters 0–4), each now with a **retargeted** `Tm_target_C` (48.9°C, 49.5°C, 50.4°C, 51.5°C, 46.5°C for regimes 0–4 respectively — see doc 12), mains temperature 24.0–26.0°C, and a re-selected Top-3 PCM shortlist per regime drawn from Objective 1's own PCM database (no longer Objective 1's original n-Octacosane-led consensus list — see doc 12 for the full before/after).
- Climate-signature sanity check: **PASSED** (GHI 5.13–5.28 kWh/m²/day, RH 62.5–70.2% — matches Tamil Nadu's coastal-humid signature). Unaffected by the revisions above.

Details: `docs_objective2/01_PHASE1_CONFIG_AND_STATE_SETUP.md`, `docs_objective2/12_TM_TARGET_RETARGETING.md`

---

## Phase 2 — Geometry & constraint engine

- Sphere capsules, staggered packing, Ergun-equation hydraulics — code unchanged throughout all revisions.
- Determinism verified: 8/8 boundary cases byte-identical across repeated calls, re-confirmed after the bounds widening.
- **Finding (updated)**: with `capsule_count.max` widened 24→37 (doc 13), the documented 15–20% PCM-volume test levels (Chen et al. baseline) are now reachable — maximum verified-valid fraction is **19.8%** (n=37, d=0.08 m), landing right at `design_bounds_shared.yaml`'s own existing 0.20 ceiling. Diameters below 0.04 m still always fail the derived-thickness bound (thickness = diameter/2 < 0.02 m floor) — that constraint is unchanged.

Plots: `phase2_validity_map`, `phase2_ergun_hydraulics`.
Details: `docs_objective2/02_PHASE2_GEOMETRY_CONSTRAINTS.md`, `docs_objective2/13_DESIGN_BOUNDS_WIDENING.md`, `docs_objective2/plots/02_geometry_plots.md`

---

## Phase 3 — Grey-box enthalpy simulator

- Full state vector, backward-Euler solver with adaptive sub-stepping, non-negotiable ambient tank-loss term always active. Code unchanged by any of today's revisions (only a `fidelity` parameter was added, defaulting to the same behavior — see Phase 6b).
- Sample case (cluster 0, n-Octacosane, 0.08 m/19 capsules/0.030 kg/s — this specific PCM predates the Tm retargeting and is kept here only as the original illustrative example; the physics and bug-fixes below apply identically regardless of which PCM is used): useful energy 1663.0 kWh/yr, solar fraction 51.4%, mean PCM liquid fraction 1.4%.
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
| 3 — Baseline comparison | **PASS** | capability check (synthetic Tm=40°C PCM) beats plain tank decisively (55.19% vs 52.26% SF), ruling out a simulator defect — **this diagnostic is exactly what later motivated the Tm-target retargeting below** |
| 4 — Published-benchmark calibration | **PASS-WITH-CAVEAT** | 51.39% vs cited 54–84% band — explained by no auxiliary heater / smaller storage-to-demand ratio |
| 5 — Sensitivity/monotonicity | **PASS** | 3/3 checks in the physically correct direction |

**Go/No-Go: GO.** Simulator released as `sim_v1_tamilnadu`. The Gate 3 *verification run* above (`simulator_verification_report.txt`, the pass/fail table) is a hardcoded, one-time diagnostic (n-Octacosane at a fixed test design) independent of whichever PCM shortlist is currently configured, by design — unaffected by any of today's revisions, and it is exactly the diagnostic that motivated them. The Gate 3 **plot** (`phase4_gate3_baseline_comparison`), however, was regenerated 2026-09-13 to use the *current* shortlist PCM (n-Tetracosane, C24) at its actual Phase 7 deployable geometry instead of the original diagnostic design — every PCM bar in that figure now beats plain tank (52.32–56.00% vs. 52.26%), visually showing the post-fix state rather than the pre-fix one. See `docs_objective2/plots/04_verification_plots.md`.

Plots: `phase4_gate1_residuals`, `phase4_gate3_baseline_comparison` (current-state version, see above), `phase4_gate5_sensitivity`.
Details: `docs_objective2/04_PHASE4_VERIFICATION_GATES.md`, `docs_objective2/plots/04_verification_plots.md`

---

## Phase 5 — Design-of-experiments dataset

- 215 cases: Latin Hypercube + boundary + no-PCM baselines, across 5 regimes × 3 **retargeted** shortlisted PCMs, sampled over the **widened** design bounds.
- **144 valid, 71 rejected** — all 71 for `bounds_violation` (diameter < 0.04 m thickness floor — unaffected by the count-bound widening, since that constraint is about diameter, not count).
- Case-level train/holdout split: 170 train / 45 holdout, stratified by (regime, PCM, validity).

Plots: `phase5_doe_coverage`, `phase5_outcome_distribution`.
Details: `docs_objective2/06_PHASE5_DOE.md`, `docs_objective2/plots/05_doe_plots.md`

---

## Phase 6 — AI surrogate model

| Target | ExtraTrees R² | vs. Linear baseline |
|---|---|---|
| useful_energy_kWh | 0.9999 | tree wins |
| solar_fraction | 0.9717 | linear ties/slightly wins (0.9732) |
| unmet_energy_kWh | 0.9950 | linear ties/slightly wins (0.9953) |
| pump_energy_kWh | 0.9891 | linear wins (0.9999) — physically explained, see doc |
| pcm_mass_kg | 0.9898 | linear wins (0.9965) |
| feasibility (classifier) | accuracy 1.000, infeasible-recall 1.000 | — |

Retrained on the retargeted-PCM, widened-bounds DOE set (114 train / 30 evaluated in this printout, 45 in the on-disk holdout). Every target still clears R²>0.97; three of five targets now show the linear baseline tying or slightly beating the tree model (previously only pump energy did) — consistent with the design space being more thoroughly sampled near its true (now wider) volume-fraction ceiling, where several targets behave close to linearly in the sampled range.

Plots: `phase6_parity_plots`, `phase6_feature_importance`.
Details: `docs_objective2/07_PHASE6_SURROGATE.md`, `docs_objective2/plots/06_surrogate_plots.md`

---

## Phase 6b — Multi-fidelity surrogate augmentation (bonus phase) — ⚠ STALE, pre-dates today's revisions

The numbers below (1.53× speedup, sample-efficiency tables) were generated against the **original, pre-retargeting, pre-widening** DOE set. They still stand as a valid demonstration that the multi-fidelity mechanism works, but do not reflect the current PCM shortlist or design bounds. Re-running `python pipeline.py --state tamilnadu --stage multifidelity` against the current DOE set is optional future work — Phase 6b is a bonus phase, not part of Objective 2's core 8-phase deliverable, so this was not re-run today given the volume of re-computation already required for Phases 5–8.

Added a cheap `fidelity="low"` mode to the simulator itself (fixed
timestep, no adaptive sub-stepping — `src/simulation/tank_model.py`),
re-ran all 215 (original) DOE cases at low fidelity, and used the result
both as a standalone cheap predictor and as an extra input feature to the
Phase 6 surrogate.

- **Speedup: 1.53×** (fair, order-randomized, same-process timing).
- **Low-fidelity-only accuracy**: R²=0.999 (useful_energy_kWh), 0.982
  (solar_fraction), 0.997 (unmet_energy_kWh) vs. the real simulator.
- **Sample-efficiency finding**: augmenting a shrunken high-fidelity
  training set with the free low-fidelity feature matched or beat the
  high-fidelity-only baseline at every tested training fraction for
  `solar_fraction`/`unmet_energy_kWh`/`pump_energy_kWh`.

Plots: `phase6b_multifidelity` (stale — from the original DOE set).
Details: `docs_objective2/11_MULTIFIDELITY_SURROGATE.md`

---

## Phase 7 — Optimization pass + simulator confirmation

400 candidates/pair searched (8,000 total), top 20/pair (400 total)
re-run in the real simulator (broadened from the original top-5/pair
specifically to check whether a safe-but-competitive mid-range PCM design
existed anywhere in the space for regimes 0–3 — see below). **Mean
surrogate-vs-simulator error: 0.04%, 0/400 exceeded the 15% large-error
threshold.**

### Deployable design selected per regime (PCM-only pool — see scope correction below)

| Regime | Selected PCM | Diameter (m) | Count | Flow (kg/s) | Useful energy (kWh) | Solar fraction | PCM mass (kg) | vs. plain tank | Meets safety margin (nominal)? |
|---|---|---|---|---|---|---|---|---|---|
| 0 | n-Tetracosane (C24) | 0.0433 | 11 | 0.0235 | 1675.06 | 52.32% | 0.373 | +0.11% | No |
| 1 | n-Tetracosane (C24) | 0.0495 | 9 | 0.0160 | 1811.31 | 53.18% | 0.457 | +0.08% | No |
| 2 | PlusICE A52 | 0.0496 | 8 | 0.0227 | 1751.28 | 53.36% | 0.414 | +0.08% | No |
| 3 | PureTemp 53 | 0.0430 | 36 | 0.0109 | 1818.75 | 54.75% | 1.375 | +0.12% | No |
| 4 | n-Tricosane (C23) | 0.0454 | 36 | 0.0223 | 1624.28 | 51.45% | 1.404 | +0.12% | **Yes** (nominal only — fails under uncertainty, see Phase 8) |

**Selection-rule scope correction (2026-09-13, `docs_objective2/
14_SELECTION_RULE_SCOPE_CORRECTION.md`)**: Objective 2's actual problem
statement asks for the *optimal PCM design* (thickness, capsule
arrangement, count, flow rate) — it presupposes PCM, it does not ask
whether to use it. The zero-mass "plain tank" candidate, added by this
implementation as a diagnostic (valuable for Gate 3 and Phase 6's
feature-importance analysis, both unaffected), is no longer eligible to
win the final per-regime recommendation — it remains visible in
`optimized_designs.csv` for comparison (`pcm_vs_plain_tank_pct` column)
but `deployable_design_per_regime.csv` is now always a genuine PCM
design. Safety (`meets_temperature_safety`, `constraint_margin_C`) is
still computed and reported on every row, never hidden — a design that
doesn't meet it gets a `deployment_note` flagging that Objective 3's
active bypass is required before hardware deployment, not a silent
fallback to a non-PCM answer.

**Headline finding, updated**: after Tm-target retargeting and bounds
widening, every regime's best PCM candidate genuinely beats plain tank on
useful energy (+0.08% to +0.12%) — up from ~0.08% at best, and from a
*loss* in 4/5 regimes, in the original pre-revision run. A **400-candidate
broadened search** (up from the original 100) confirmed regimes 0–3 have
**zero** PCM candidates, at any mass from the smallest (8 capsules) to the
largest (37 capsules) tested, that meet the temperature-safety envelope —
even the minimal PCM dose reaches 70–72°C, ~5–7°C above PCM's 65°C
material-stability limit, because the water itself already runs that hot
in these climates regardless of PCM. Only regime 4's climate stays cool
enough for PCM to nominally clear 65°C (by a margin of 0.009°C — see
Phase 8, this does not survive real-world uncertainty).

Plots: `phase7_pareto_by_regime`, `phase7_surrogate_vs_simulator`, `phase7_safety_compliance`.
Details: `docs_objective2/08_PHASE7_OPTIMIZATION.md`, `docs_objective2/14_SELECTION_RULE_SCOPE_CORRECTION.md`, `docs_objective2/plots/07_optimization_plots.md`

---

## Phase 8 — Robustness + Objective 3 hand-off

120 Monte Carlo draws per design (PCM latent heat ±10%, **two-level**
weather noise [annual GHI scale/ambient offset **plus** independent
per-hour jitter, the annual component drawn from a real 10-year
2016–2025 historical weather ensemble — see below], demand ±20%/±30min,
mains temperature ±2°C), re-run through the **real simulator** for every
draw (never the surrogate), against the **5 PCM designs above**.

| Regime | Design | P(meets delivery) | P(meets demand) | P(temperature-safe) | Robust? | Useful energy P5–P50–P95 (kWh) | Max water T P95 |
|---|---|---|---|---|---|---|---|
| 0 | n-Tetracosane (C24) | 100% | 80.8% | **0%** | No | 1592 – 1682 – 1783 | 75.0°C |
| 1 | n-Tetracosane (C24) | 100% | 91.7% | **0%** | No | 1706 – 1825 – 1939 | 78.4°C |
| 2 | PlusICE A52 | 100% | 95.0% | **0%** | No | 1632 – 1743 – 1844 | 78.1°C |
| 3 | PureTemp 53 | 100% | 98.3% | **0%** | No | 1712 – 1807 – 1900 | 78.0°C |
| 4 | n-Tricosane (C23) | 100% | 73.3% | **25%** | No | 1533 – 1617 – 1703 | 74.3°C |

**Headline finding**: delivery-temperature reliability is never the
problem (100% everywhere). Demand reliability is generally strong (81–98%
in regimes 0–3; 73% in regime 4). **Temperature safety is the real story
now that every regime runs PCM**: regimes 0–3, whose nominal designs
already ran several degrees over the 65°C PCM limit, are **0% safe**
under realistic uncertainty — never safe, in any of the 120 draws.
Regime 4's design, whose nominal margin was a razor-thin 0.009°C, drops
to just **25% safe** once weather/demand/PCM-property uncertainty is
applied — nominal-only safety was never a reliable indicator on its own.

**This is the honest, load-bearing consequence of correctly answering
Objective 2's actual problem statement**: Objective 2 now delivers what
Objective 3 (explicitly "a Deep Reinforcement Learning-based adaptive
controller to optimize PCM charging, discharging, and bypass operations")
is designed to consume — a real, optimal PCM design in every regime that
is not yet safe standing on its own. That is precisely the gap Objective
3 exists to close, and it is now a stated, quantified, non-optional
requirement for every regime (not only one), not an assumption.

**Historical weather ensemble upgrade** (independent of the scope
correction above): the annual GHI-scale/ambient-offset component is no
longer a synthetic assumed range. It is drawn from a genuine **10-year
(2016–2025) historical weather ensemble** built from Objective 1's own
daily ERA5/POWER archive (`src/robustness/weather_ensemble.py`, reading
`data/objective1/daily_aggregates_tamilnadu.csv` — 133 population-grid
points, all 10 years complete on disk but previously unused past
Objective 1's climate signature step). Each Monte Carlo draw's annual
weather is one of the 10 real observed years for that climate regime, not
an assumed distribution shape (per-hour jitter within the year is still
synthetic — documented, not hidden).

**One real bug found and fixed during development** (retained from the
original run): the first robustness implementation double-counted
plain-tank designs against the PCM temperature limit (`T_pcm` is just a
copy of `T_water` when there's no PCM). Now moot for the final result
(every design uses PCM), but the fix — gating the PCM-temperature check on
`has_pcm` — remains in the code.

Recommendation cards (`results/tamilnadu/recommendation_cards.md`) and the
Objective 3 hand-off contract (`results/tamilnadu/
obj3_environment_contract_tamilnadu.json`) are both regenerated against
the 5 PCM designs above, and include this robustness data, the full PCM
property record, the flow/temperature envelope, a `global_limits` summary
block, a safety shield that trips on a **3°C precautionary guard band**
below each hard limit (72°C water / 62°C PCM), a fully specified default
`reward_function` (formula, normalized weights with rationale, penalty
definitions), an explicit `deferred_future_work` list, and the
acceptance-test checklist Objective 3 must pass before training.

Plots: `phase8_robustness_probabilities` (delivery/demand bars only — the
P(temperature-safe) bar was removed from this figure 2026-09-13 at the
user's request; the number itself is unaffected and still reported in
the table above, `robustness_summary.csv`, and the contract),
`phase8_useful_energy_intervals`.
Details: `docs_objective2/10_PHASE8_ROBUSTNESS_HANDOFF.md`, `docs_objective2/14_SELECTION_RULE_SCOPE_CORRECTION.md`

---

## The headline finding, together

1. **Every regime's Objective 2 recommendation is now a genuine, optimal
   PCM design** (thickness/capsule arrangement/count/flow rate, per the
   actual problem statement) — beating plain tank on useful energy
   everywhere (+0.08% to +0.12%), the result of two real, documented
   fixes: retargeting `Tm_target_C` to this tank's own operating range
   (doc 12) and widening the PCM-volume design bounds (doc 13).
2. **No PCM design is temperature-robust without an active bypass**
   (Phase 8): regimes 0–3 are 0% temperature-safe under realistic
   uncertainty — not a rare edge case, never safe in 120 draws — because
   these climates push tank water to 70–72°C on sunny days, ~5–7°C above
   PCM's fixed 65°C material-stability ceiling, regardless of PCM
   mass or melting point. Regime 4, the one climate mild enough for PCM
   to be nominally safe, still drops to only 25% safe once real-world
   variability is applied.

Together these say: Tamil Nadu's Objective 2 recommendation is a specific,
optimal PCM design in every regime — **but every single one of them
requires Objective 3's active charge/discharge/bypass controller before
real deployment.** That is not a weakness of this result; it is exactly
the dependency structure the four objectives were designed to have, now
stated with a precise, quantified, per-regime safety gap for Objective 3
to close, instead of an assumption.

## Files produced (all under `results/tamilnadu/`)

| File | Phase | Contents |
|---|---|---|
| `simulator_verification_report.txt` | 4 | Gate 1–5 full readout |
| `design_cases.parquet` / `.csv` | 5 | 215-case DOE database (retargeted PCMs, widened bounds) |
| `surrogate_metrics.csv`, `surrogate_error_by_group.csv`, `surrogate/models.pkl` | 6 | trained models + accuracy |
| `design_cases_lowfid.parquet`, `multifidelity_speedup_report.json`, `multifidelity_sample_efficiency.csv`, `multifidelity_runtime_benchmark.csv` | 6b | ⚠ stale — from the original pre-revision DOE |
| `surrogate_top_candidates.csv`, `optimized_designs.csv` (full comparison, plain tank included for diagnostics), `deployable_design_per_regime.csv` (PCM-only final pick) | 7 | search → confirm → select |
| `tm_retargeting_report.csv` | — | doc 12's full before/after Tm-target/shortlist evidence |
| `robustness_results.csv`, `robustness_summary.csv` | 8 | Monte Carlo draws (real 10-yr weather ensemble, 5 PCM designs) + per-regime summary |
| `recommendation_cards.md` | 8 | one card per regime (all PCM) |
| `obj3_environment_contract_tamilnadu.json` | 8 | frozen Objective 3 hand-off package, incl. fully specified reward function |
| `plots/interactive/*.html`, `plots/static/*.png` | 2–8 | 18 justification figures |

## Literature

Every phase section above traces to specific citations in
`docs_objective2/REFERENCES.md` (master list, sourced verbatim from
`vertopal.com_references.txt` at the project root) — most load-bearing:
Chen et al. (2025) for the tank baseline and the 15–20% PCM-volume levels
that motivated bounds widening; Singh et al. (2025) for the Gate 4
benchmark band; Rubitherm/PLUSS (2024) data sheets for every PCM property
and the 65°C safety limit; Chopra et al. (2023) for the Monte Carlo
robustness methodology; Assareh et al. (2023) and Barghi Jahromi et al.
(2026) for the surrogate-then-search optimization pattern; Sivaraj et al.
(2023) and Emami et al. (2026) for the Objective 3 DRL hand-off design.

## Where to go next

- **`docs_objective2/14_SELECTION_RULE_SCOPE_CORRECTION.md`** — read this first; it explains the most consequential change (PCM now wins every regime) and why.
- `docs_objective2/12_TM_TARGET_RETARGETING.md` and `docs_objective2/13_DESIGN_BOUNDS_WIDENING.md` — the two design-space revisions that made a genuine PCM win possible.
- `docs_objective2/OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` — what Objective 3 needs and what to do first (now a universal, not regime-4-only, requirement).
- `docs_objective2/10_PHASE8_ROBUSTNESS_HANDOFF.md` — full robustness methodology.
- `docs_objective2/REFERENCES.md` — full literature base, mapped per phase.
- `docs_objective2/HOW_TO_RUN.md` — every command to reproduce everything in this file.
