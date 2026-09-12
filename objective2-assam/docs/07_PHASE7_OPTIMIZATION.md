# 07 — Phase 7 Audit: Optimization Pass + Simulator Confirmation (Assam)

Actual files used: `scripts/run_phase7_optimization.py` (a **bespoke
script written for Assam**, not the ported `src/optimize/search.py` +
`src/optimize/select_deployable.py` used by Rajasthan/Tamil Nadu, though
those ported files also exist unused in this repo's `src/optimize/`).
Output: `results/phase7_top_candidates.csv`,
`results/phase7_optimized_designs.csv`,
`results/phase7_resimulation_results.csv`,
`results/phase7_deployable_design_per_regime.csv`,
`results/phase7_optimization_report.md`.

> Rewritten from the actual report/CSV files. The previous version of
> this doc described Rajasthan's method and result (plain tank wins all
> 3 regimes, 0/45 PCM candidates pass safety) — **Assam's actual process
> and result are different, and the reported verdict contains a bug**;
> see "The safety-verdict bug" below before citing any Phase 7 Assam
> number as validated.

## Method as actually run

1,000 random candidate design vectors per regime×PCM pair, 3 regimes ×
4 pairs (3 shortlisted PCMs + plain-tank baseline) = **12,000
candidates**. Screened through the real geometry/physical constraint
check plus the Phase 6 feasibility classifier (probability ≥ 0.50) →
**7,966 feasible candidates** scored by the Phase 6 regressors.

**Selection rule used: the "5% Near-Best Rule"** (different from
Rajasthan/Tamil Nadu's simple `pareto_tolerance_pct` rule): per regime,
keep every candidate with predicted useful energy ≥ 95% of that regime's
best, then rank the survivors by a 6-tier hierarchy — (1) minimize
unmet energy, (2) maximize solar fraction, (3) minimize pump energy,
(4) minimize PCM mass, (5) prefer fewer/standard capsules, (6) maximize
temperature safety margin. This produced **21 top candidates**
(`phase7_top_candidates.csv`). The top 5 across regimes were re-run in
the real `sim_v1_assam` simulator for full 8,760-hour annual
confirmation (`phase7_resimulation_results.csv`).

## Surrogate-vs-simulator accuracy

Across the 5 re-simulated candidates, useful-energy error ranged
0.00–0.51% (worst case: the regime-0 plain-tank baseline). Solar
fraction error ≤0.32%, unmet energy ≤0.53%. Pump-energy *percentage*
errors look large (9–361%) but are on ~1e-9 Wh absolute values — noise
at that scale, consistent with the surrogate's weak `pump_energy_kWh`
fit noted in `06_…`. Energy-conservation residual ≈0.0000% on every
re-run. This part of Phase 7 is solid: the surrogate ranks designs
reliably and the simulator confirms it.

## Result: deployable design per regime (as selected)

| Regime | PCM selected | Diameter (mm) | Count | Flow (kg/s) | Useful energy (kWh) | Solar fraction | Unmet energy (kWh) |
|---|---|---|---|---|---|---|---|
| 0 — Lower Brahmaputra Valley | savE® OM46 | 40.3 | 24 | 0.0463 | 685.18 | 62.78% | 396.68 |
| 1 — Upper Assam Tea Belt | savE® OM48 | 43.0 | 18 | 0.0323 | 709.41 | 62.75% | 409.48 |
| 2 — Barak Valley & Southern Hills | savE® OM48 | 40.0 | 21 | 0.0278 | 656.11 | 53.55% | 560.08 |

Unlike Rajasthan and 4/5 of Tamil Nadu's regimes, **every one of
Assam's 3 regimes selected a PCM design**, not a plain tank.

## The safety-verdict bug — the critical caveat for this phase

`system_config_shared.yaml` (frozen, shared by all 4 states) sets
`max_water_temp_C: 75.0` and `max_pcm_temp_C: 65.0`. Reading the actual
margin columns computed in `phase7_deployable_design_per_regime.csv`
(`scripts/run_phase7_optimization.py` computes these correctly against
the real config, lines ~349–352):

| Regime | Max PCM temp (°C) | PCM margin to 65 °C | Max water temp (°C) | Water margin to 75 °C | `n_safety_violations` (sub-hours/year) |
|---|---|---|---|---|---|
| 0 | 66.21 | **−1.21** | 66.51 | +9.01 | 13 |
| 1 | 67.95 | **−2.95** | 68.60 | +6.40 | 313 |
| 2 | 70.09 | **−5.09** | 70.71 | +4.29 | 215 |

**All 3 selected PCM designs exceed the 65 °C PCM material-stability
limit** — the exact failure mode Rajasthan/Tamil Nadu's Phase 7 filtered
out entirely (their `meets_temperature_safety` check rejects any
candidate with `max_pcm_temp_C > 65` or any logged safety violation).

Yet `results/phase7_optimization_report.md` §5 states:

```
Max PCM Temp   Acceptance Standard <= 90.0°C   ...   PASSED
Safety Violations   Exactly 0 hours   ...   PASSED
```

Both lines are wrong for this run: `n_safety_violations` is 13/313/215,
not 0, and the "≤90 °C" standard does not exist in this project's frozen
config anywhere — `scripts/run_phase7_optimization.py` computes the
correct negative margin against the real 65 °C limit two sections
earlier in the same script, then the report-generation code prints a
**hardcoded "PASSED"** against an unrelated, undocumented 90 °C/95 °C
threshold instead of checking the sign of the margin it just computed.
This is a bug in the report template, not a deliberate, justified
relaxation of the safety limit.

**This is consistent with, not contrary to, Gate 3's finding**
(`04_PHASE4_VERIFICATION_GATES.md`): Gate 3 already showed Assam's
shortlisted PCM (and even a *matched-Tm synthetic* PCM) losing to plain
water on energy. At DOE scale, **79 / 111 valid Phase 5 cases (71%) log
`max_pcm_temp_C > 65 °C`** (0/111 exceed the 75 °C water limit) —
narrower than Rajasthan's near-universal 108/111, but confirming the
overheating is a real, common failure mode across the design space, not
an artifact of the 3 designs Phase 7 happened to select (`05_…`).

## What this means for the recommendation

**As reported, Assam's Phase 7 "PASS" is not trustworthy** — under this
project's own pre-declared 65 °C/75 °C safety rule, 0/3 of the selected
designs actually clear it. The honest path forward, in order of
preference:

1. **Re-run the selection with the correct filter applied** — reject any
   candidate with `max_pcm_temp_C > 65` or `n_safety_violations > 0`
   before ranking by the 5%-near-best rule, the same way
   `src/optimize/select_deployable.py`'s `meets_temperature_safety`
   already does (that ported code exists in this repo, unused for the
   actual Assam run — it could be pointed at the same 12,000-candidate
   pool). Given Gate 3's finding, this will likely force the plain tank
   in some or all 3 regimes, matching Rajasthan's outcome.
2. If a genuinely wider PCM operating ceiling is intended for Assam
   (e.g. because 44–51 °C-Tm PCMs behave differently against a 100 L/day
   demand and 16–20 °C mains than the 300 L/day cases elsewhere), that
   must become an explicit, cited, per-state config decision — not a
   silent mismatch between a correctly-computed margin and a
   hardcoded report line.

Until one of those happens, treat Assam's `phase7_deployable_design_per_regime.csv`
as **unvalidated candidates**, not a deployable recommendation, in any
paper section or Objective 3 hand-off.

## Deviations from the framework doc / from the other two states

- Uses a 1,000-candidate-per-pair random search + 5%-near-best rule
  with a 6-tier tie-break, not Rajasthan/Tamil Nadu's 400-candidate
  search + simple `pareto_tolerance_pct` rule. Both are within the
  reduced 40-hr spec's discretion, but the two are not directly
  comparable methodologically in a cross-state chapter without saying so.
- Only 5 of the 21 top candidates were re-simulated (Rajasthan
  re-simulated all 60 of its top-5-per-pair set) — a narrower
  simulator-confirmation footprint.
- No NSGA-II / full active-learning loop, same as the other states.
