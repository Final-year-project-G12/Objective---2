# 08 — Phase 7 Audit: Optimization Pass + Simulator Confirmation

Files: `src/optimize/search.py`, `src/optimize/select_deployable.py`.
Run: `python pipeline.py --state uttarakhand --stage optimize`.
Output: `results/uttarakhand/surrogate_top_candidates.csv`,
`optimized_designs.csv` (PCM-comparison report, includes plain tank for
reference), `deployable_design_per_regime.csv` (final selection, PCM-only).

**This is the final version of this doc (2026-09-14)**, after the Tm-target
retargeting (doc 12), design-bounds widening (doc 13), and the
selection-rule scope correction described below were all applied together.

## Method (D2.6) — one pass, not the full active-learning loop

1. **Search** (`search.py`): 400 random candidate design vectors per
   regime×PCM pair (20 pairs = 8,000 candidates total, now sampling the
   widened design space — `capsule_count` up to 37), each first passed
   through the **real** Phase 2 geometry gate, then scored by the Phase 6
   surrogate. Top **20** per pair by predicted `useful_energy_kWh` are kept
   (400 candidates total confirmed in the simulator — widened from 5/pair
   to 20/pair to match Tamil Nadu's more thorough search now that the
   selection actually matters).
2. **Confirm** (`select_deployable.py`): every one of those 400 candidates
   is **re-run in the real simulator**. Surrogate-vs-simulator error is
   logged per candidate; the framework's "large-error rule" (>15% → trust
   the simulator) is applied.
3. **Select — SCOPE CORRECTED (2026-09-14, ported from Tamil Nadu)**:
   Objective 2's assignment is "an AI-driven design optimization model to
   determine the optimal PCM thickness, capsule arrangement, number of PCM
   capsules, and flow rate for maximizing thermal energy storage" — it
   presupposes a PCM design and asks for its optimal parameters, it does
   not ask whether to use PCM at all. The zero-mass "plain tank" option
   was an internal diagnostic baseline this implementation added on its
   own initiative; it is **kept in `optimized_designs.csv` for reference**
   but **excluded from winning** the final per-regime recommendation.
   Among PCM candidates only, the winner is the one with the highest
   simulator-confirmed useful energy, tie-broken by the existing
   pump-energy/PCM-mass/count/margin order. Temperature safety is **never
   hidden** — `meets_temperature_safety`, `constraint_margin_C` and
   `n_safety_violations` are computed and reported for every row, and a
   negative-margin winner gets an explicit `deployment_note` flagging that
   Objective 3's active bypass/discharge control is a precondition for
   deployment, not a disqualification of the design.

## Result: surrogate accuracy in practice

**Mean surrogate-vs-simulator error across all 400 confirmed candidates:
~0.03%. 0/400 exceeded the 15% large-error threshold.** Strong,
independent evidence (beyond Phase 6's own hold-out R²) that the
surrogate, the geometry engine, and the simulator are all self-consistent
even after the design-space widening.

## Result: deployable design per regime

| Regime | Winning PCM | Diameter (m) | Count | Flow (kg/s) | Useful energy (kWh) | Solar fraction | PCM mass (kg) | Margin (°C) | Safe? |
|---|---|---|---|---|---|---|---|---|---|
| 0 | **RT42** | 0.0448 | 12 | 0.0337 | 1539.0 | 39.06% | 0.496 | **−6.48** | No |
| 1 | **Myristic acid (C14)** | 0.0452 | 9 | 0.0109 | 1525.9 | 28.05% | 0.431 | **+11.88** | Yes |
| 2 | **RT42** | 0.0432 | 13 | 0.0105 | 1626.4 | 37.42% | 0.482 | **−5.12** | No |
| 3 | **RT42** | 0.0491 | 31 | 0.0143 | 1565.5 | 40.91% | 1.689 | **−7.79** | No |
| 4 | **savE® OM42** | 0.0445 | 11 | 0.0107 | 1625.9 | 37.00% | 0.458 | **−4.21** | No |

Regime 3's winner uses `n_capsule=31` — only reachable after the
design-bounds widening (doc 13); it would not have been searchable before
that change.

## The headline finding: retargeting gives every regime a genuine (if narrow) PCM win — but exposes a sharper safety problem

| Regime | Best plain-tank useful energy (kWh) | Best PCM useful energy (kWh) | PCM vs. plain tank |
|---|---|---|---|
| 0 | 1537.37 | 1539.01 (RT42) | **+0.106%** |
| 1 | 1525.58 | 1525.92 (Myristic acid) | +0.023% |
| 2 | 1625.09 | 1626.45 (RT42) | **+0.083%** |
| 3 | 1563.33 | 1565.48 (RT42) | **+0.138%** |
| 4 | 1625.64 | 1625.87 (savE® OM42) | +0.014% |

Every regime's best PCM candidate now beats its own best plain-tank
candidate — a real change from the pre-retargeting picture, where the two
were statistically indistinguishable and the pick was effectively a
tie-break coin flip. The margins are still small in absolute terms
(0.01–0.14%), but they are **consistently positive**, which they were not
before retargeting.

**The safety picture is now the sharper, more important finding.** Because
plain tank can no longer win, and because temperature safety is no longer
a selection filter (only a reported precondition), the winning PCM design
in **4 of 5 regimes exceeds its own 65°C body-temperature limit** at
nominal (un-perturbed) conditions:

| Regime | Max water temp (°C) | Max PCM temp (°C) | Margin (°C) | `n_safety_violations` (hours/year) |
|---|---|---|---|---|
| 0 | 71.62 | 71.48 | −6.48 | 1456 |
| 1 | 58.06 | 53.12 | +11.88 | 0 |
| 2 | 70.30 | 70.12 | −5.12 | 697 |
| 3 | 72.97 | 72.79 | −7.79 | 1030 |
| 4 | 69.55 | 69.21 | −4.21 | 320 |

**Why this happens even after retargeting**: `Tm_target_C` was set to each
regime's *median* charging-hour water temperature (doc 12) — by
construction, roughly half of all charging hours run *above* that
median, and on the sunniest days the tank can run well past both the PCM's
melting point and the 65°C safety ceiling. A PCM tuned to typical
conditions is not the same as a PCM (or a system) that never overheats on
atypical ones — nothing in this design has active overheat protection.

**Regime 1 is the outlier, and not for a reassuring reason.** It is the
only region where the selected PCM (Myristic acid (C14), Tm=53°C) stays
under both limits — but this is not because retargeting worked there.
Doc 12 explains: regime 1's own retargeted `Tm_target_C` is 27.8°C, and
**no PCM in the database** survives a melting window centered there, so
regime 1 keeps its **old**, climate-anchored (and equally mismatched)
shortlist. Its selected PCM is mismatched to the tank's real (cold)
operating range in the *same* way every other regime's *pre-retargeting*
PCM was — which is exactly why it barely melts, behaves mostly as inert
sensible mass, and therefore never gets hot enough to threaten the 65°C
limit. This is a coincidental safety benefit of a still-unsolved
mismatch, not a validated design choice.

## Deviations from the full framework doc

No NSGA-II / full Pareto front, no active-learning loop (retrain-and-
repeat), single search pass per the reduced spec. The "confirm on an
unseen weather year" step of the selection rule is deferred — medoid-only,
noted explicitly rather than silently skipped.
