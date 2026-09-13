# 14 — Selection Rule Scope Correction: PCM-Only Final Selection (2026-09-13)

**Status: APPLIED to `src/optimize/select_deployable.py`. Phase 7 re-selected (no new simulation needed — re-applied to the already-confirmed candidate pool from the widened-bounds run). Phase 8 (robustness + hand-off) re-run against the new selection. All current.**

This is a deliberate, documented scope correction — not a tuning of results.

## Why

The actual problem statement (`presentation_review2.pdf`) defines Objective 2 as:

> "Develop an AI-driven design optimization model to determine the **optimal PCM thickness, capsule arrangement, number of PCM capsules, and flow rate** for maximizing thermal energy storage under location-specific climatic conditions."

This objective **presupposes a PCM-based design** — it asks for the optimal values of PCM-specific parameters (thickness, capsule arrangement, capsule count, flow rate), not whether to include PCM at all. Nowhere does it ask for a plain-water-tank alternative to be evaluated as a competing, potentially-winning option.

The zero-PCM "plain tank" candidate was added to Phase 5/7's search space by this implementation, on its own initiative, as a valuable *diagnostic* — it is what let Gate 3 (`04_PHASE4_VERIFICATION_GATES.md`) prove the simulator wasn't buggy, and what let Phase 6's feature-importance analysis show climate dominates the outcome. That diagnostic value is real and is kept (see "What is kept" below). But letting the plain-tank candidate *win* the final per-regime recommendation was answering a different question — "should this regime use PCM at all?" — than the one Objective 2 was actually asked to answer — "what is the optimal PCM design for this regime?". Once `Tm_target_C` was corrected (doc 12) and the design bounds were widened (doc 13), every regime's best PCM candidate already had *higher* useful energy than plain tank; the only thing still handing the result to plain tank in 4 of 5 regimes was a **hard safety pre-filter** this project had layered on top of the assignment's own criteria (see `10_PHASE8_ROBUSTNESS_HANDOFF.md` for why that filter existed and what it was catching).

## What changed (`apply_selection_rule`, `src/optimize/select_deployable.py`)

- The candidate pool the winner is chosen from is now **PCM candidates only** (`pcm_id != "NONE_plain_tank"`) — plain-tank rows remain in `optimized_designs.csv` (the full comparison report) for diagnostic/justification purposes, but cannot become `deployable_design_per_regime.csv`'s pick.
- The winner is the PCM design with the highest simulator-confirmed `useful_energy_kWh` (the objective's literal "maximizing thermal energy storage"), with the same existing tie-break order (minimize pump energy, then PCM mass, then capsule count, then maximize constraint margin) among anything within the pre-declared 5% tolerance of the best.
- **Safety is never hidden.** `meets_temperature_safety`, `constraint_margin_C`, and `n_safety_violations` are computed and reported for every selected design exactly as before. A new `deployment_note` field states plainly whether the pick meets this project's precautionary margin as-is, or requires Objective 3's active bypass before hardware deployment — a reported precondition, not a disqualification back to a non-PCM answer the assignment never asked for.
- A new `pcm_vs_plain_tank_pct` field keeps the plain-tank comparison visible on every row, so "how much better is this than plain water" remains an honest, checkable number, not something the correction erases.

## What is kept, unchanged

- Gate 3's plain-tank baseline capability check (Phase 4) — still the diagnostic proof the simulator isn't buggy.
- Phase 6's feature-importance analysis and its plain-tank rows in the DOE — still the third independent line of evidence that climate dominates the outcome.
- Phase 7's full `optimized_designs.csv` comparison report — still contains every candidate, plain tank included, for anyone who wants to see the full picture.
- Every other selection-rule mechanic (tolerance band, tie-break order) — unchanged, just applied to a PCM-only pool now.

## Result: before → after

| Regime | Before (plain-tank-eligible) | After (PCM-only pool) | vs. plain tank | Meets safety margin? |
|---|---|---|---|---|
| 0 | Plain tank | **n-Tetracosane (C24)**, 0.373 kg | +0.11% | No |
| 1 | Plain tank | **n-Tetracosane (C24)**, 0.457 kg | +0.08% | No |
| 2 | Plain tank | **PlusICE A52**, 0.414 kg | +0.08% | No |
| 3 | Plain tank | **PureTemp 53**, 1.375 kg | +0.12% | No |
| 4 | n-Tricosane (C23) (already PCM before this correction) | **n-Tricosane (C23)**, 1.404 kg | +0.12% | Yes (nominal only — see Phase 8 below) |

Every regime now has a genuine, simulator-confirmed PCM design as Objective 2's answer, matching what the assignment actually asks for.

## Phase 8 robustness on the corrected selection (real numbers, re-run)

| Regime | PCM | P(meets demand) | P(temp-safe) | Max water T P95 |
|---|---|---|---|---|
| 0 | n-Tetracosane (C24) | 80.8% | **0%** | 75.0°C |
| 1 | n-Tetracosane (C24) | 91.7% | **0%** | 78.4°C |
| 2 | PlusICE A52 | 95.0% | **0%** | 78.1°C |
| 3 | PureTemp 53 | 98.3% | **0%** | 78.0°C |
| 4 | n-Tricosane (C23) | 73.3% | **25%** | 74.3°C |

Regime 4's nominal design was only safe by a razor-thin 0.0088°C margin (see doc 13's follow-up search) — under Monte Carlo weather/demand/property uncertainty, it drops to 25% safe, not 100%. Regimes 0–3, whose nominal margins were already several degrees negative, are 0% safe under uncertainty exactly as their nominal numbers implied.

**This is the honest, load-bearing consequence of the scope correction**: Objective 2 now delivers what Objective 3 (a Deep-RL adaptive controller for "PCM charging, discharging, and bypass operations") is *actually* designed to consume — a real PCM design in every regime that is optimal by energy but is not yet safe standing on its own. That is precisely the gap Objective 3 exists to close. This is stated as a hand-off requirement, not walked back into a non-PCM design, in `OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md`.

## What this does NOT change

- The physics simulator, verification gates, `Tm_target_C` retargeting (doc 12), and design-bounds widening (doc 13) — all unchanged; this is a selection-rule change only.
- The safety limits themselves (`max_water_temp_C=75°C`, `max_pcm_temp_C=65°C`) — unchanged, still the real manufacturer/scald-based values. This correction does not relax them; it changes what happens when a design doesn't meet them (reported and handed to Objective 3, not silently swapped for a non-PCM answer).
- The underlying physical finding from Phase 8 (no design is temperature-robust without an active bypass) — unchanged and, if anything, now stated more sharply, since it applies to the actual PCM recommendation in every regime rather than only the one regime that happened to use PCM before.

## Literature

This is a scope-correction decision (re-reading the assignment, not a
physics or methodology change), so it does not itself rest on a specific
citation the way docs 12/13 do. The literature that remains relevant is
the same base already cited for the phases whose *conclusions* this
correction now surfaces without a plain-tank fallback:
- **[Rubitherm2024]** — the real datasheet limit behind every regime's
  P(temp-safe) result in the table above.
- **[Sivaraj2023]**, **[Emami2026]** — why Objective 3's active bypass
  controller is the correct place to close the safety gap this doc makes
  explicit, rather than reopening Objective 2's design or safety limits.
