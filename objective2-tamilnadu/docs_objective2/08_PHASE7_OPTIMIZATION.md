# 08 — Phase 7 Audit: Optimization Pass + Simulator Confirmation

> **SUPERSEDED 2026-09-17.** Describes the pre-refresh, pre-arrangement
> winners (all staggered by assumption). The current search spans
> arrangement (600 candidates/pair, `arrangement_rationale` field) and
> selected **radial in all 3 regimes** — see
> `docs_objective2/tamilnadu_phase_docs/07_PROMPT_PHASE7_OPTIMIZE_TAMILNADU.md`
> for the full result and honesty-checked rationale.

Files: `src/optimize/search.py`, `src/optimize/select_deployable.py`.
Run: `python pipeline.py --state tamilnadu --stage optimize`.
Output: `results/tamilnadu/surrogate_top_candidates.csv`,
`optimized_designs.csv` (full comparison report — plain tank still
included here for diagnostics), `deployable_design_per_regime.csv`
(final PCM-only selection).

**This doc describes the CURRENT (2026-09-14) methodology and results —
after the Tm-target retargeting (doc 12), design-bounds widening (doc 13),
selection-rule scope correction (doc 14), and the full-MCDM shortlist
adoption + safety-first tie-break (doc 15). All four are applied below;
see those docs for why each was made.**

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
   best PCM useful energy found for that regime → among those, **prefer
   `meets_temperature_safety=True` first** (added 2026-09-14, doc 15) →
   then minimize pump energy, then PCM mass, then capsule count → prefer
   the larger constraint margin as a final tie-break. Safety is always
   computed and reported, never used to fall back to a non-PCM answer —
   it is now also used, where a safe option exists within tolerance, to
   choose *which* PCM design wins among near-equal-energy candidates.

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

## Result: deployable design per regime (PCM-only pool, safety-first tie-break)

| Regime | Selected PCM | Diameter (m) | Count | Flow (kg/s) | Useful energy (kWh) | Solar fraction | PCM mass (kg) | vs. plain tank | Meets safety margin (nominal)? |
|---|---|---|---|---|---|---|---|---|---|
| 0 | n-Tetracosane (C24) | 0.0419 | 14 | 0.0113 | 1675.06 | 52.34% | 0.432 | +0.11% | No |
| 1 | n-Tetracosane (C24) | 0.0406 | 14 | 0.0405 | 1811.71 | 53.17% | 0.393 | +0.10% | No |
| 2 | n-Hexacosane (C26) | 0.0432 | 10 | 0.0141 | 1750.76 | 53.27% | 0.325 | +0.05% | No |
| 3 | n-Hexacosane (C26) | 0.0423 | 16 | 0.0100 | 1817.25 | 54.39% | 0.487 | +0.04% | No |
| 4 | **RT45HC** | 0.0549 | 30 | 0.0334 | 1627.20 | 52.00% | 2.288 | **+0.30%** | **Yes** (margin +0.39°C — see Phase 8 for uncertainty) |

Every regime now has a genuine, simulator-confirmed optimal PCM design —
the actual Objective 2 deliverable.

## The headline finding, now with four fixes plus a 400-candidate search

Four real, documented changes moved PCM from "loses in 4/5 regimes" to
"wins in 5/5 regimes, one of them genuinely safe":

1. **`Tm_target_C` retargeting** (doc 12) — Objective 1's climate-anchored
   57°C target sat well above this tank's real charging-hour water
   temperature (medians 46.5–51.5°C across regimes); PCMs tuned to it
   barely melted (mean liquid fraction ≈1–2% annually). Retargeting to
   the tank's own operating range roughly doubled to quadrupled PCM's
   nominal energy margin (from ~0.08% to ~0.13–0.33% at the old,
   still-narrow design bounds).
2. **Design-bounds widening** (doc 13) — `capsule_count.max` 24→37 let
   designs reach ~19.8% PCM volume fraction (vs. 12.9% before), giving PCM
   enough mass to matter.
3. **Full-MCDM shortlist adoption** (doc 15, Part 1) — replaced a
   simplified nearest-Tm shortlist substitute with Objective 1's actual
   4-method MCDM engine, which changed every regime's shortlist and
   surfaced n-Tetracosane (C24)/n-Hexacosane (C26)/RT45HC as the
   candidates actually searched.
4. **Safety-first tie-break** (doc 15, Part 2) — among candidates already
   within the energy tolerance, prefer `meets_temperature_safety=True`
   before minimizing mass. This is what turned regime 4's pick from a
   razor-thin-unsafe design into RT45HC: genuinely safe (+0.39°C margin)
   *and* higher useful energy (+0.30% vs. plain tank, the best of any
   regime).

Combined, every regime's best PCM candidate now beats plain tank by
+0.04% to +0.30%.

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
clear the nominal safety check with a real margin (+0.39°C with RT45HC,
after the safety-first tie-break fix in doc 15 — the search itself always
had 40 of 60 confirmed regime-4 candidates clear this margin; the earlier,
now-superseded 0.009°C figure was an artifact of the old tie-break order
picking a different, lower-mass candidate that happened to sit right at
the edge). This is not fixable in regimes 0–3 by retargeting, widening
bounds further, or searching more candidates — it is a property of this
collector/tank's peak operating temperature relative to a fixed material
limit, and the reason Objective 3's active bypass is a universal
requirement (see `10_PHASE8_ROBUSTNESS_HANDOFF.md` and
`OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md`).

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
- See `docs_objective2/15_MCDM_RERANKING_AND_SAFETY_TIEBREAK.md` for the
  MCDM methodology grounding the current shortlist (traced to Objective
  1's own `tamilnadu_pipeline/08_mcdm_ranking.py`, not a new citation).
