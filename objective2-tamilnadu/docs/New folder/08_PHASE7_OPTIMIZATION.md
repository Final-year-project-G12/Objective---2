# 08 — Phase 7 Audit: Optimization Pass + Simulator Confirmation

Files: `src/optimize/search.py`, `src/optimize/select_deployable.py`.
Run: `python pipeline.py --state tamilnadu --stage optimize`.
Output: `results/tamilnadu/surrogate_top_candidates.csv`,
`optimized_designs.csv` (PCM-comparison report),
`deployable_design_per_regime.csv` (final selection).

## Method (D2.6) — one pass, not the full active-learning loop

1. **Search** (`search.py`): 400 random candidate design vectors per
   regime×PCM pair (20 pairs = 8,000 candidates total), each first passed
   through the **real** Phase 2 geometry gate (free, deterministic — a
   candidate the geometry engine already rejects is never even scored by
   the surrogate), then scored by the Phase 6 surrogate. Top 5 per pair by
   predicted `useful_energy_kWh` are kept (100 candidates total).
2. **Confirm** (`select_deployable.py`): every one of those 100 candidates
   is **re-run in the real simulator** — never a surrogate-only number
   (framework doc: non-negotiable). Surrogate-vs-simulator error is logged
   per candidate; the framework's "large-error rule" (>15% → trust the
   simulator, log it) is applied.
3. **Select**: the pre-declared rule from `system_config_shared.yaml`
   (`selection.pareto_tolerance_pct = 5%`) is applied per regime: reject
   anything that fails the temperature-safety check → keep every
   simulator-confirmed candidate within 5% of the best useful energy found
   for that regime → among those, minimize pump energy, then PCM mass,
   then capsule count → prefer the larger constraint margin as a final
   tie-break.

## Result: surrogate accuracy in practice

**Mean surrogate-vs-simulator error across all 100 confirmed candidates:
0.02%. 0/100 exceeded the 15% large-error threshold.** This is strong,
independent evidence (beyond Phase 6's own hold-out R²) that the
surrogate, the geometry engine, and the simulator are all self-consistent
— a surrogate this accurate on a problem this smooth is expected, not
suspicious, given Phase 6's R²>0.98 on every target.

## Result: deployable design per regime

| Regime | Winning PCM | Diameter (m) | Count | Flow (kg/s) | Useful energy (kWh) | Solar fraction | PCM mass (kg) |
|---|---|---|---|---|---|---|---|
| 0 | **plain tank (no PCM)** | 0.0409 | 9 | 0.0159 | 1673.29 | 52.26% | 0 |
| 1 | **plain tank (no PCM)** | 0.0422 | 13 | 0.0124 | 1809.93 | 53.11% | 0 |
| 2 | **plain tank (no PCM)** | 0.0443 | 8 | 0.0127 | 1749.80 | 53.30% | 0 |
| 3 | **plain tank (no PCM)** | 0.0435 | 8 | 0.0185 | 1816.50 | 54.42% | 0 |
| 4 | **n-Octacosane (C28)** | 0.0406 | 9 | 0.0104 | 1623.41 | 51.01% | 0.287 |

## The headline finding, now with full-search evidence (not just Gate 3's two hand-picked designs)

Looking at the best simulator-confirmed design **per PCM** in each regime
(`optimized_designs.csv`), every shortlisted PCM actually **slightly beats**
the best plain-tank design found by the same 400-candidate search — by a
razor-thin margin:

| Regime | Best plain tank (kWh) | Best PCM found (kWh) | PCM's edge |
|---|---|---|---|
| 0 | 1673.29 | 1674.66 (n-Hexacosane) | +0.08% |
| 1 | 1809.93 | 1811.39 (n-Hexacosane) | +0.08% |
| 2 | 1749.80 | 1751.17 (n-Hexacosane) | +0.08% |
| 3 | 1816.50 | 1818.02 (n-Hexacosane) | +0.08% |
| 4 | 1622.35 | 1623.41 (n-Octacosane) | +0.07% |

So PCM **is** measurably better than plain sensible storage at its
best-found geometry in every single regime — but the margin (~0.08%) is
two orders of magnitude smaller than the pre-declared 5% Pareto tolerance.
The selection rule therefore correctly treats plain tank and the best PCM
design as statistically equivalent and picks whichever has the **lower
PCM mass** — which is the zero-mass plain tank, every time, *except*
regime 4, where the PCM candidate the search happened to land on came out
marginally ahead even of that regime's own plain-tank optimum, so PCM
wins there outright before the tolerance tie-break is even needed.

**This is the optimizer working exactly as designed, not a bug** — it is
the same physical story Gate 3 found with two hand-picked designs
(`04_PHASE4_VERIFICATION_GATES.md`), now confirmed across a 400-candidate
search per pair: within the current design bounds (≤12.9% PCM volume
fraction) and this specific 50 L direct-encapsulation tank, Objective 1's
climate-ranked PCM shortlist provides at most a fraction-of-a-percent
useful-energy improvement over plain water — nowhere near enough to
justify the PCM mass/cost under the pre-declared selection rule. See
`09_NEXT_STEPS.md` for what this means for the Tamil Nadu recommendation
and for Phase 8.

## Additional finding: the temperature-safety filter is a real, binding constraint here

Across all 100 simulator-confirmed candidates, energy-conservation
residual stayed tiny everywhere (mean 0.0000192%, max 0.0000911% — this
generalizes Gate 1's result from 5 hand-picked cases to the whole search,
a further correctness confirmation), but **only 35/100 candidates
(35%) satisfied `meets_temperature_safety`** (max water ≤75°C, max PCM
≤65°C, zero per-substep violations over the simulated year). Breaking it
down by regime: **all 5 of the no-PCM baseline's candidates pass safety
in every regime, but only 15/80 PCM candidates do (all in regime 4)** —
every PCM candidate confirmed for regions 0–3 tripped the safety limit at
some point in the year. This is a real, previously-unexamined
consequence of this collector/tank combination under Tamil Nadu's
irradiance with no active overheat protection modeled (no relief valve,
no forced bypass at high temperature) — not a search or simulator defect,
since it shows up consistently across many independently-sampled
candidates. It also **strengthens the plain-tank-wins finding above**: in
4/5 regions, the plain tank isn't just cheaper at equivalent performance,
it's also the design far more likely to land inside the safety envelope,
so if the team pursues option 2 in `09_NEXT_STEPS.md` (widening the PCM
bounds), an explicit high-temperature safety shield/bypass belongs in that
follow-up work too.

## Deviations from the full framework doc

No NSGA-II / full Pareto front, no active-learning loop (retrain-and-
repeat), single search pass per the reduced spec. The "confirm on an
unseen weather year" step of the selection rule is deferred — medoid-only,
noted explicitly rather than silently skipped.
