# 07 — Phase 7 Audit: Optimization Pass + Simulator Confirmation (Rajasthan)

Files: `src/optimize/search.py`, `src/optimize/select_deployable.py`.
Run: `python pipeline.py --state rajasthan --stage optimize`.
Output: `results/phase7_surrogate_top_candidates.csv`,
`results/phase7_optimized_designs.csv` (PCM-comparison report),
`results/phase7_deployable_design_per_regime.csv` (final selection).

> **Ported from `objective2-tamilnadu/src/optimize/`.** Search logic
> (400 random candidates per pair, real Phase 2 geometry gate before
> scoring, rank by predicted `useful_energy_kWh`) and the >15% large-error
> rule are unchanged. The model path (`results/phase6_surrogate_models.pkl`),
> the three output paths (flat `results/phase7_*`) and the `__main__` state
> fallback differ from Tamil Nadu's version, as before.
>
> **Updated 2026-09-14 — `apply_selection_rule()` re-ported from Tamil
> Nadu.** The original pre-declared rule (below) let the zero-mass
> "plain tank" row compete for the per-regime win on an equal footing
> with PCM candidates; Tamil Nadu's own implementation was corrected
> (2026-09-13, scope correction in its own `select_deployable.py`
> docstring) to recognise that Objective 2's stated problem — "an
> AI-driven design optimization model to determine the optimal PCM
> thickness, capsule arrangement, number of PCM capsules, and flow rate"
> — presupposes a PCM design; the plain tank was always an internal
> diagnostic baseline, not an eligible answer. That correction is now
> ported into this file too: plain-tank rows stay in
> `phase7_optimized_designs.csv` (the full comparison report) but are
> excluded from the pool `apply_selection_rule()` selects the winner
> from. See "Result: deployable design per regime" below for what this
> changes for Rajasthan on top of the safety-shield update from the same
> week.

## Method (D2.6) — one pass, not the full active-learning loop

1. **Search** (`search.py`): 400 random candidate design vectors per
   regime×PCM pair. Rajasthan has **12 pairs** (3 regimes × 3 shortlisted
   PCMs + 3 no-PCM baselines) = 4,800 candidates. Each is first passed
   through the **real** Phase 2 geometry gate (free, deterministic — a
   candidate the geometry engine already rejects is never scored by the
   surrogate), then scored by the Phase 6 surrogate. Top 5 per pair by
   predicted `useful_energy_kWh` are kept — **60 candidates total**.
2. **Confirm** (`select_deployable.py`): every one of the 60 is **re-run
   in the real simulator** — never a surrogate-only number (framework
   doc: non-negotiable). Surrogate-vs-simulator error logged per
   candidate; the >15% large-error rule (trust the simulator, log it) is
   applied.
3. **Select**: the pre-declared rule from `system_config_shared.yaml`
   (`selection.pareto_tolerance_pct = 5%`) is applied per regime, over the
   **PCM-only candidate pool** (plain tank excluded from winning, see the
   2026-09-14 note above): keep every simulator-confirmed PCM candidate
   within 5% of the best PCM useful energy for that regime → among those,
   minimise pump energy, then PCM mass, then capsule count → prefer the
   larger constraint margin as the final tie-break. Safety is reported
   (`meets_temperature_safety`, `constraint_margin_C`, `deployment_note`)
   rather than pre-filtered — a design with a negative margin would be
   flagged as needing Objective 3's active bypass before deployment
   rather than silently disqualified back to the plain tank; in
   Rajasthan's current run (safety shield active by default since
   2026-09-13) every winner already clears safety outright, so no design
   currently carries that flag. "Confirm on an unseen weather year" is
   deferred (medoid-only, per the 40-hr cut list — noted, not hidden).

## Result: surrogate accuracy in practice

**Mean surrogate-vs-simulator error across all 60 confirmed candidates:
0.023% (max 0.090%). 0/60 exceeded the 15% large-error threshold.**
Independent confirmation (beyond Phase 6's hold-out R²) that surrogate,
geometry engine and simulator are self-consistent. Energy-conservation
residual across the same 60 full-year runs stayed tiny (mean 0.00088%,
max 0.0018% of collector energy) — generalising Gate 1's 5-case result to
the whole search.

## Result: deployable design per regime (re-run 2026-09-14, safety shield + PCM-only selection rule)

| Regime | Winning design | Diameter (m) | Count | Flow (kg/s) | Useful energy (kWh) | Solar fraction | Max water T (°C) | Max PCM T (°C) | Margin to nearest limit |
|---|---|---|---|---|---|---|---|---|---|
| 0 | **RT45HC** | 0.0500 | 24 | 0.0175 | 1587.88 | 55.33% | 68.8 | 62.1 | 2.9 °C (to 65 °C PCM) |
| 1 | **Paraffin/HDPE PCM6** | 0.0414 | 15 | 0.0302 | 1674.69 | 58.28% | 72.0 | 62.2 | 2.8 °C (to 65 °C PCM) |
| 2 | **Paraffin/HDPE PCM3** | 0.0416 | 8 | 0.0181 | 1593.46 | 53.90% | 68.8 | 62.1 | 2.9 °C (to 65 °C PCM) |

All three deployable designs are now PCM, not plain tank. This is the
result of two changes that both landed the same week, on top of each
other:

1. **The rule-based safety shield became the pipeline default on
   2026-09-13** (`system_config_shared.yaml: safety_shield.enabled:
   true`, bypass at 72 °C water / 62 °C PCM) — this alone rescues PCM
   candidates from the overheat failure mode described below, so
   **60/60** simulator-confirmed candidates now pass
   `meets_temperature_safety` (up from 15/60 unshielded).
2. **`apply_selection_rule()` was re-ported from Tamil Nadu on
   2026-09-14** to exclude the plain tank from the winner pool (see the
   note at the top of this doc). Before this second change, the shielded
   re-run still let the plain tank win two of three regimes via the
   pump-energy/PCM-mass tie-break, because PCM's shielded energy edge
   over plain water is razor-thin (see below) and the old rule let
   "lowest PCM mass" mean "zero" whenever candidates tied within 5%. With
   the plain tank excluded from the pool, the winner is now the
   best-tie-broken PCM candidate in every regime.

(`n_capsule` / diameter for a plain-tank row are reported but not
physically used, for reference — `run_case.py` forces
`n_capsule_effective = 0` whenever no PCM is given; the plain-tank rows
themselves still appear in `phase7_optimized_designs.csv` as the
diagnostic comparison baseline.)

## The headline finding, now with full-search evidence

Best simulator-confirmed design **per PCM** in each regime
(`phase7_optimized_designs.csv`, all 60 candidates, not just the winner
after tie-break) — every shortlisted PCM's best-found geometry beats the
best plain-tank geometry found by the same 400-candidate search, and
under the now-default safety shield every one of them also **passes**
temperature safety:

| Regime | Best plain tank (kWh) | Best PCM found (kWh) | PCM's edge | PCM meets safety? |
|---|---|---|---|---|
| 0 | 1585.70 | 1587.95 (RT45HC) | +0.14% | **Yes** |
| 1 | 1673.34 | 1674.76 (Paraffin/HDPE PCM3) | +0.08% | **Yes** |
| 2 | 1592.27 | 1593.71 (savE® OM50) | +0.09% | **Yes** |

(Note: the single best-simulated PCM candidate per regime above is not
always the same PCM as the deployable winner in the table further up —
e.g. regime 1's absolute best-found candidate is a Paraffin/HDPE PCM3
geometry, but the deployable winner is Paraffin/HDPE PCM6, because
several PCM candidates land within the 5% Pareto tolerance of each other
and the selection rule's tie-break — min pump energy, then PCM mass,
then capsule count, then max margin — picks among that near-tied pool,
not simply the single highest-energy row.)

Same physical story as Tamil Nadu, and as this project's own Phase 4
Gate 3 / Phase 5 DOE: within the frozen bounds (≤12.9% PCM volume
fraction) and this 50 L direct-encapsulation tank, Objective 1's
climate-ranked PCM shortlist gives at most a **fraction-of-a-percent**
useful-energy improvement over plain water — two orders of magnitude
below the pre-declared 5% Pareto tolerance. What changed between the
unshielded and shielded/PCM-only-selection runs is not the size of that
margin (it stays a fraction of a percent throughout) but **which design
family is even eligible to win**: unshielded, none of the PCM candidates
clear the safety limit at all, so the plain tank wins by elimination;
shielded, the margin becomes real (and positive for PCM) precisely
because the shield clips the same high-temperature tail for both design
families roughly equally, and the PCM-only selection rule now lets that
razor-thin PCM edge actually decide the winner instead of being
tie-broken away in favour of zero PCM mass.

## The temperature-safety filter is no longer binding against PCM here (reversed from the unshielded run)

Of the 60 simulator-confirmed candidates, **all 60 now satisfy
`meets_temperature_safety`** (max water ≤ 75 °C, max PCM ≤ 65 °C, zero
per-substep violations over the year) — 15 plain-tank and 45 PCM
candidates alike. This reverses the earlier unshielded finding (only
15/60 passed, all plain-tank, 0/45 PCM) described in
`docs/09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md` §0/§2/§6: that finding was
always scoped to "true of the unshielded physics" (§6's own qualifier),
and now that the shield is the pipeline default, the safety filter no
longer favours the plain tank at all — it simply confirms every
candidate the search proposed is deployable, PCM included.

**Note on regime 1:** the deployable design there reaches 72.0 °C max
water / 62.2 °C max PCM temperature — 2.8 °C below the tighter PCM limit,
the thinnest margin of the three regimes. It passes cleanly under the
shield, but the margin is still worth flagging for anyone revisiting the
collector/tank sizing.

## What this means for the recommendation

Under the pipeline's current default configuration (safety shield active,
PCM-only selection pool), **the Rajasthan deployable design for all three
climate regimes is a shortlisted PCM** — RT45HC (regime 0), Paraffin/HDPE
PCM6 (regime 1), Paraffin/HDPE PCM3 (regime 2) — each beating the best
plain-tank geometry found by the same search by a fraction of a percent
in useful energy, and each clearing temperature safety with a ~2.8–2.9 °C
margin under the shield. This reverses the earlier "plain tank wins
everywhere" conclusion, which was a consequence of (a) unshielded physics
letting no PCM candidate clear the safety filter and (b) a selection rule
that let the plain tank win the near-tied tie-break by virtue of zero PCM
mass. Neither condition holds in the current default run. A separate,
still-not-yet-adopted finding remains relevant context: resizing the
frozen 50 L tank to IS 12976:2023's 75 L/m² reference ratio (112.5 L)
independently makes every PCM candidate pass safety **and** beat plain
water **without** needing the shield at all (see
`docs/09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md` §7) — the shield and the
resize are two different, non-exclusive routes to the same qualitative
conclusion.

## Deviations from the full framework doc

No NSGA-II / full Pareto front, no active-learning loop (retrain-and-
repeat) — single search pass per the reduced spec. The "confirm on an
unseen weather year" step of the selection rule is deferred (medoid-only,
single 2025 year), stated explicitly.
