# 08 — Phase 7 Audit: Optimization Pass + Simulator Confirmation

Files: `src/optimize/search.py`, `src/optimize/select_deployable.py`.
Run: `python pipeline.py --state tamilnadu --stage optimize`.
Output: `results/tamilnadu/surrogate_top_candidates.csv`,
`optimized_designs.csv` (full comparison report — plain tank still
included here for diagnostics), `deployable_design_per_regime.csv`
(final PCM-only selection).

**This doc describes the CURRENT (2026-09-13) methodology and results —
after the Tm-target retargeting (doc 12), design-bounds widening (doc 13)
and selection-rule scope correction (doc 14). All three are applied
below; see those docs for why each was made.**

## Method (D2.6) — one pass, not the full active-learning loop

1. **Search** (`search.py`): 400 random candidate design vectors per
   regime×PCM pair (20 pairs = 8,000 candidates total), each first passed
   through the **real** Phase 2 geometry gate (free, deterministic — a
   candidate the geometry engine already rejects is never even scored by
   the surrogate), then scored by the Phase 6 surrogate. Top 20 per pair
   by predicted `useful_energy_kWh` are kept (400 candidates total —
   broadened from an original top-5/pair specifically to check whether a
   safe-but-competitive mid-range PCM design existed anywhere in the space
   for the regimes that initially failed the safety check; see below).
2. **Confirm** (`select_deployable.py`): every one of those 400 candidates
   is **re-run in the real simulator** — never a surrogate-only number
   (framework doc: non-negotiable). Surrogate-vs-simulator error is logged
   per candidate; the framework's "large-error rule" (>15% → trust the
   simulator, log it) is applied.
3. **Select**: the pre-declared rule from `system_config_shared.yaml`
   (`selection.pareto_tolerance_pct = 5%`) is applied per regime, over a
   **PCM-only candidate pool** (see "Selection-rule scope correction"
   below): keep every simulator-confirmed PCM candidate within 5% of the
   best PCM useful energy found for that regime → among those, minimize
   pump energy, then PCM mass, then capsule count → prefer the larger
   constraint margin as a final tie-break. Safety
   (`meets_temperature_safety`, `constraint_margin_C`) is computed and
   reported on the winner, never used to fall back to a non-PCM answer.

## Selection-rule scope correction (2026-09-13)

The actual problem statement (`presentation_review2.pdf`) defines
Objective 2 as determining "the optimal PCM thickness, capsule
arrangement, number of PCM capsules, and flow rate for maximizing thermal
energy storage" — it presupposes a PCM design; it does not ask whether to
use PCM at all. The zero-mass "plain tank" candidate was added to the
search space by this implementation, on its own initiative, as a
diagnostic (it is what let Gate 3 prove the simulator wasn't buggy, and
what let Phase 6's feature-importance analysis show climate dominates the
outcome) — but letting it *win* the final per-regime recommendation
answered a different question than the one actually posed. See
`14_SELECTION_RULE_SCOPE_CORRECTION.md` for the full rationale. Plain-tank
rows remain in `optimized_designs.csv` for comparison
(`pcm_vs_plain_tank_pct` column) but cannot become the deployable pick.

## Result: surrogate accuracy in practice

**Mean surrogate-vs-simulator error across all 400 confirmed candidates:
0.04%. 0/400 exceeded the 15% large-error threshold.** Still strong,
independent evidence (beyond Phase 6's own hold-out R²) that the
surrogate, the geometry engine, and the simulator are all self-consistent
— slightly higher than the original 100-candidate pass's 0.02%, as
expected when confirming 4× more candidates including some further from
the surrogate's training distribution, but still two orders of magnitude
below the 15% large-error threshold.

## Result: deployable design per regime (PCM-only pool)

| Regime | Selected PCM | Diameter (m) | Count | Flow (kg/s) | Useful energy (kWh) | Solar fraction | PCM mass (kg) | vs. plain tank | Meets safety margin (nominal)? |
|---|---|---|---|---|---|---|---|---|---|
| 0 | n-Tetracosane (C24) | 0.0433 | 11 | 0.0235 | 1675.06 | 52.32% | 0.373 | +0.11% | No |
| 1 | n-Tetracosane (C24) | 0.0495 | 9 | 0.0160 | 1811.31 | 53.18% | 0.457 | +0.08% | No |
| 2 | PlusICE A52 | 0.0496 | 8 | 0.0227 | 1751.28 | 53.36% | 0.414 | +0.08% | No |
| 3 | PureTemp 53 | 0.0430 | 36 | 0.0109 | 1818.75 | 54.75% | 1.375 | +0.12% | No |
| 4 | n-Tricosane (C23) | 0.0454 | 36 | 0.0223 | 1624.28 | 51.45% | 1.404 | +0.12% | **Yes** (nominal only — see Phase 8) |

Every regime now has a genuine, simulator-confirmed optimal PCM design —
the actual Objective 2 deliverable.

## The headline finding, now with two design-space fixes plus a 400-candidate search

Two real, documented changes moved PCM from "loses in 4/5 regimes" to
"wins in 5/5 regimes on useful energy":

1. **`Tm_target_C` retargeting** (doc 12) — Objective 1's climate-anchored
   57°C target sat well above this tank's real charging-hour water
   temperature (medians 46.5–51.5°C across regimes); PCMs tuned to it
   barely melted (mean liquid fraction ≈1–2% annually). Retargeting to
   the tank's own operating range roughly doubled to quadrupled PCM's
   nominal energy margin (from ~0.08% to ~0.13–0.33% at the old,
   still-narrow design bounds).
2. **Design-bounds widening** (doc 13) — `capsule_count.max` 24→37 let
   designs reach ~19.8% PCM volume fraction (vs. 12.9% before), giving PCM
   enough mass to matter. Combined with retargeting, every regime's best
   PCM candidate now beats plain tank by +0.08% to +0.12%.

## Additional finding: the temperature-safety limit is a real, binding, climate-driven constraint — not a search-coverage gap

The original top-5/pair search found zero safe PCM candidates in regimes
0–3. Before concluding this was a coverage limitation, the search was
**broadened to top-20/pair (400 candidates total, 60 PCM candidates per
regime spanning the full 8–37 capsule / 0.02–0.08 m diameter range)** —
still zero safe PCM candidates in regimes 0–3. A follow-up direct test
confirmed why: even the **smallest possible PCM dose** (8 capsules,
minimum diameter, ~0.2 kg PCM) in these regimes reaches 70.3–72.1°C water
temperature, with **4,164–7,226 hours/year of safety violations** —
because PCM's 65°C material-stability limit (Rubitherm datasheets) is
~10°C tighter than water's own 75°C scald limit, and these climates
already push tank water into the 70–72°C range on sunny days regardless
of whether PCM is present. Only regime 4's cooler climate keeps water
(and therefore PCM) generally under 65°C, letting its selected design
clear the nominal safety check by a margin of just 0.009°C. This is not
fixable by retargeting, widening bounds further, or searching more
candidates — it is a property of this collector/tank's peak operating
temperature relative to a fixed material limit, and the reason Objective
3's active bypass is a universal requirement (see `10_PHASE8_
ROBUSTNESS_HANDOFF.md` and `OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md`).

## Deviations from the full framework doc

No NSGA-II / full Pareto front, no active-learning loop (retrain-and-
repeat), single (now-broadened) search pass per the reduced spec. The
"confirm on an unseen weather year" step of the selection rule is
deferred for the within-year hourly shape — medoid-only — though the
*annual* weather magnitude used in Phase 8's robustness pass is now a real
10-year historical ensemble (doc 12/Phase 8), noted explicitly rather than
silently skipped.

## Literature

- **[Assareh2023]** and **[Chen2025]** (Taguchi/GRA) are direct precedent
  for this phase's LHS-search-then-multi-criteria-selection pipeline
  shape for a PCM-augmented solar-thermal collector.
- **[BarghiJahromi2026]** supports surrogate-guided candidate ranking
  before a physics re-confirmation pass, the same two-step search→confirm
  structure used here.
- **[Rubitherm2024]** is the manufacturer-datasheet source of the
  `max_pcm_temp_C=65°C` limit identified in this doc as the real, binding
  constraint behind the temperature-safety finding above — not a tunable
  design parameter, a real material property.
