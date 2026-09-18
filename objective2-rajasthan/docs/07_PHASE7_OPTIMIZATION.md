# 07 — Phase 7 Audit: Optimization Pass + Simulator Confirmation (Rajasthan)

Files: `src/optimize/search.py`, `src/optimize/select_deployable.py`.
Run: `python pipeline.py --state rajasthan --stage optimize`.
Output: `results/phase7_surrogate_top_candidates.csv`,
`results/phase7_optimized_designs.csv` (PCM-comparison report),
`results/phase7_deployable_design_per_regime.csv` (final selection).

> **Ported from `objective2-tamilnadu/src/optimize/`**, then updated twice
> since:
> - **2026-09-14** — `apply_selection_rule()` re-ported from Tamil Nadu to
>   exclude the plain tank from the winner pool. Objective 2's stated
>   problem — "determine the optimal PCM thickness, capsule arrangement,
>   number of PCM capsules, and flow rate" — presupposes a PCM design; the
>   plain tank was always an internal diagnostic baseline, not an eligible
>   answer. Plain-tank rows stay in `phase7_optimized_designs.csv` (the
>   full comparison report) but are excluded from the pool
>   `apply_selection_rule()` selects the winner from.
> - **2026-09-17** — search spans arrangement, winner gets a rationale
>   (`Objective2 Consolidated plan.md` §6, Phase 7): `search.py` samples
>   arrangement uniformly per candidate, before the real Phase 2 geometry
>   gate; candidate count widened 400→600/pair so each arrangement still
>   gets a comparable surviving pool. `select_deployable.py` adds
>   `arrangement_rationale` to each regime's winner — it compares the
>   winning arrangement's simulator-confirmed useful energy against the
>   best confirmed candidate from each other arrangement in the same
>   regime×PCM pool, using the run's own mean surrogate-vs-simulator error
>   as the noise band.

## Method (D2.6) — one pass, not the full active-learning loop

1. **Search** (`search.py`): 600 random candidate design vectors per
   regime×PCM pair (widened from 400 on 2026-09-17 so each of the 3
   arrangements — now sampled uniformly per candidate — still gets a
   comparable surviving pool after the Phase 2 gate). Rajasthan has **12
   pairs** (3 regimes × 3 shortlisted PCMs + 3 no-PCM baselines) = 7,200
   candidates. Each is first passed through the **real** Phase 2 geometry
   gate (free, deterministic, arrangement-specific — a candidate the
   geometry engine already rejects is never scored by the surrogate),
   then scored by the Phase 6 surrogate. Top 5 per pair by predicted
   `useful_energy_kWh` are kept — **60 candidates total**, spanning
   whichever arrangement(s) the surrogate favored per pair.
2. **Confirm** (`select_deployable.py`): every one of the 60 is **re-run
   in the real simulator** — never a surrogate-only number (framework
   doc: non-negotiable). Surrogate-vs-simulator error logged per
   candidate; the >15% large-error rule (trust the simulator, log it) is
   applied.
3. **Select**: the pre-declared rule from `system_config_shared.yaml`
   (`selection.pareto_tolerance_pct = 5%`) is applied per regime, over the
   **PCM-only candidate pool** (plain tank excluded from winning): keep
   every simulator-confirmed PCM candidate within 5% of the best PCM
   useful energy for that regime → among those, minimise pump energy,
   then PCM mass, then capsule count → prefer the larger constraint
   margin as the final tie-break. Safety is reported
   (`meets_temperature_safety`, `constraint_margin_C`, `deployment_note`)
   rather than pre-filtered. `arrangement_rationale` is then computed for
   the winner (see Method step 3 above). "Confirm on an unseen weather
   year" is deferred (medoid-only, per the 40-hr cut list).

## Result: surrogate accuracy in practice

**Mean surrogate-vs-simulator error across all 60 confirmed candidates:
0.03% (0/60 exceeded the 15% large-error threshold).** Essentially
unchanged from the pre-arrangement-restore baseline (0.023%, max 0.090%)
— the surrogate generalizes across arrangements about as well as it did
within one. Independent confirmation (beyond Phase 6's hold-out R²) that
surrogate, geometry engine and simulator are self-consistent.
Energy-conservation residual across the same 60 full-year runs stayed
tiny (mean 0.00090%, max 0.0019% of collector energy) — generalising
Gate 1's 7-case result to the whole search.

## Result: deployable design per regime (arrangement-restored search)

| Regime | Winning PCM | Arrangement | Diameter (m) | Count | Flow (kg/s) | Useful energy (kWh) | Solar fraction | Max water T (°C) | Max PCM T (°C) | Margin to nearest limit | Arrangement rationale |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | **RT50** | staggered | 0.0409 | 11 | 0.0267 | 1586.89 | 54.99% | 68.7 | 62.1 | 2.90 °C (to 65 °C PCM) | Only arrangement `staggered` was confirmed for this regime/PCM pool |
| 1 | **Paraffin/HDPE PCM3** | staggered | 0.0413 | 8 | 0.0359 | 1674.69 | 58.25% | 72.1 | 62.2 | 2.82 °C (to 65 °C PCM) | Tied within noise (margin ~0.00% ≤ 0.03% noise band) against `radial`/`single-layer` |
| 2 | **savE® OM50** | **radial** | 0.0425 | 31 | 0.0244 | 1593.82 | 54.04% | 68.9 | 62.2 | 2.76 °C (to 65 °C PCM) | Tied within noise (margin ~0.00% ≤ 0.03% noise band) against `staggered`/`single-layer` |

All three deployable designs are PCM (plain tank excluded from the
winner pool per the 2026-09-14 selection-rule correction) and all clear
temperature safety under the rule-based safety shield
(`system_config_shared.yaml: safety_shield.enabled`, adopted 2026-09-13
— see `09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md` §6-§8). **These winners
differ from the pre-arrangement-restore run** (which selected RT45HC /
Paraffin-HDPE-PCM6 / Paraffin-HDPE-PCM3) — expected, not a regression: the
widened count bound (8–37, was 8–24), the 600-candidate search (was 400),
and arrangement now entering the candidate pool all genuinely change
which designs the surrogate proposes and which survive Phase 2's gate, so
a different near-tied winner can emerge from the same underlying PCM
shortlist and safety shield. Regime 2's winner is now **radial**, not
staggered — the first regime where a non-staggered arrangement actually
wins outright (though within Phase 6's near-zero-importance noise band,
see "Arrangement did or did not decide the outcome" below).

## Top-5 composition per regime×PCM pair — what the search actually surfaced

| Regime / PCM | single-layer | staggered | radial |
|---|---|---|---|
| 0 / RT50 | 0 | 5 | 0 |
| 0 / RT45HC | 0 | 5 | 0 |
| 0 / Lauric acid (C12) | 1 | 3 | 1 |
| 0 / NONE_plain_tank | 3 | 0 | 2 |
| 1 / savE® OM50 | 2 | 3 | 0 |
| 1 / Paraffin/HDPE PCM3 | 1 | 3 | 1 |
| 1 / Paraffin/HDPE PCM6 | 0 | 1 | 4 |
| 1 / NONE_plain_tank | 3 | 1 | 1 |
| 2 / savE® OM50 | 1 | 1 | 3 |
| 2 / Paraffin/HDPE PCM3 | 3 | 1 | 1 |
| 2 / Paraffin/HDPE PCM6 | 2 | 1 | 2 |
| 2 / NONE_plain_tank | 3 | 2 | 0 |

Composition varies considerably by pair — some pairs (0/RT50, 0/RT45HC)
came back 5/5 staggered, while others (1/Paraffin-HDPE-PCM6) came back
4/5 radial. Consistent with Phase 6's finding that arrangement has
near-zero effect on predicted useful energy: which arrangement lands in a
given top-5 is close to a coin flip rather than a strong preference, so
this scatter is the expected consequence of that finding, not a
search-quality problem.

## Arrangement did or did not decide the outcome — reported per regime, not forced to a single story

- **Regime 0 (RT50):** decisive by elimination, not by margin — `staggered`
  was the *only* arrangement that survived into this pair's top-5 pool in
  this search (0 single-layer, 0 radial candidates reached the confirmed
  set at all for RT50). No comparison against another arrangement was
  possible for this specific PCM.
- **Regime 1 (Paraffin/HDPE PCM3):** all three arrangements' best
  simulator-confirmed useful energy landed within the run's own 0.03%
  surrogate-vs-simulator noise band of each other — reported honestly as
  "tied within noise," per the consolidated plan's instruction not to
  force a single winner when the margin is inside noise.
- **Regime 2 (savE® OM50):** same as Regime 1 — tied within noise, with
  `radial` winning the tie-break (lower pump energy / larger margin among
  near-identical candidates), not because it produced meaningfully more
  useful energy.

None of this contradicts Phase 6's arrangement-importance finding — if
anything it is exactly what near-zero importance predicts: arrangement
essentially never decides Rajasthan's per-regime winner on energy alone;
where it "wins," it wins the tie-break among candidates the surrogate
already considered equivalent.

## The headline finding, now with full-search evidence

Best simulator-confirmed design **per PCM** in each regime
(`phase7_optimized_designs.csv`, all 60 candidates, not just the winner
after tie-break) — every shortlisted PCM's best-found geometry beats the
best plain-tank geometry found by the same 600-candidate search, and
under the default safety shield every one of the 60 confirmed candidates
**passes** temperature safety:

| Regime | Best plain tank (kWh) | Best PCM found (kWh) | PCM's edge | PCM meets safety? |
|---|---|---|---|---|
| 0 | 1585.70 | 1588.34 (RT45HC, staggered) | +0.17% | **Yes** |
| 1 | 1673.34 | 1675.07 (savE® OM50, staggered) | +0.10% | **Yes** |
| 2 | 1592.27 | 1593.86 (savE® OM50, radial) | +0.10% | **Yes** |

(Note: the single best-simulated PCM candidate per regime above is not
always the same PCM as the deployable winner in the table further up —
several PCM candidates land within the 5% Pareto tolerance of each other,
and the selection rule's tie-break — min pump energy, then PCM mass, then
capsule count, then max margin — picks among that near-tied pool, not
simply the single highest-energy row.)

Same physical story as before arrangement was restored, and as this
project's own Phase 4 Gate 3 / Phase 5 DOE: within these bounds and this
50 L direct-encapsulation tank, Objective 1's climate-ranked PCM shortlist
gives at most a **fraction-of-a-percent** useful-energy improvement over
plain water — two orders of magnitude below the pre-declared 5% Pareto
tolerance. Restoring arrangement as a search variable did not change this
qualitative conclusion; it added a fourth searched dimension without
producing a new, decisive result along it.

## Deviations from the full framework doc

No NSGA-II / full Pareto front, no active-learning loop (retrain-and-
repeat) — single search pass per the reduced spec, now spanning all four
decision variables jointly (diameter, count, arrangement, flow). The
"confirm on an unseen weather year" step of the selection rule is
deferred (medoid-only, single year), stated explicitly.
