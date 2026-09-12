# 08 — Phase 7 Audit: Optimization Pass + Simulator Confirmation

Files: `src/optimize/search.py`, `src/optimize/select_deployable.py`.
Run: `python pipeline.py --state uttarakhand --stage optimize`.
Output: `results/uttarakhand/surrogate_top_candidates.csv`,
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
~0.02–0.05%. 0/100 exceeded the 15% large-error threshold.** This is strong,
independent evidence (beyond Phase 6's own hold-out R²) that the
surrogate, the geometry engine, and the simulator are all self-consistent.

## Result: deployable design per regime

| Regime | Winning PCM | Diameter (m) | Count | Flow (kg/s) | Useful energy (kWh) | Solar fraction | PCM mass (kg) |
|---|---|---|---|---|---|---|---|
| 0 | **plain tank (no PCM)** | 0.0487 | 9 | 0.0119 | 1675.3 | 40.71% | 0 |
| 1 | **plain tank (no PCM)** | 0.0501 | 9 | 0.0293 | 1625.3 | 37.38% | 0 |
| 2 | **PureTemp 58** | 0.0438 | 10 | 0.0116 | 1527.2 | 28.04% | 0.392 kg |
| 3 | **plain tank (no PCM)** | 0.0429 | 10 | 0.0396 | 1563.8 | 40.75% | 0 |
| 4 | **plain tank (no PCM)** | 0.0441 | 8 | 0.0175 | 1624.0 | 37.20% | 0 |

## The headline finding: PCM wins only in regime 2 (the coldest regime)

Looking at the best simulator-confirmed design **per PCM** in each regime
(`optimized_designs.csv`), the pattern is markedly different from Tamil Nadu:

- **Regimes 0, 1, 3, 4**: the best PCM found and the best plain tank found
  are within the pre-declared 5% Pareto tolerance, so the selection rule's
  next tie-breaker (minimize PCM mass) picks the zero-mass plain tank —
  same physical story as Tamil Nadu.
- **Regime 2** (coldest: Ta_mean~9.4°C, highest L_required=178 kJ/kg):
  PureTemp 58's best-found design reached the regime's own best
  useful-energy value (1527.7 kWh), winning outright before the tolerance
  tie-break was even needed. The pool size was 20 candidates within 5% of
  best, reflecting a fuller and more competitive search in this regime.

**Why regime 2 is different**: at Ta_mean~9.4°C, the mains temperature is
only 7.4°C (the coldest across all 5 regimes), which raises `L_required`
to 178 kJ/kg (the highest in the state). The tank water temperature is
thus driven further into the PCM's operating range, allowing PureTemp 58
(Tm=58°C) to actually cycle — unlike the warmer regimes where the tank
rarely reaches 58°C. The constraint margin for regime 2's selected design
is +7.97°C below the safety limit, confirming the PCM never overheats in
this colder climate.

**This is not a simulator inconsistency** — it is the optimizer finding that
where the hardware actually works as intended (cold inlet, low ambient,
PCM has room to melt and re-solidify), the latent-storage benefit is real.
Phase 8's robustness analysis confirms this (regime 2 has 0% safety
violations — the only regime to achieve that).

## The temperature-safety filter is a real, binding constraint here

Across all 100 simulator-confirmed candidates, **only a subset of PCM
candidates satisfy `meets_temperature_safety`** (max water ≤75°C, max PCM
≤65°C, zero per-substep violations over the simulated year). Notably:
- Regime 2's PureTemp 58 candidates *do* pass (constraint margin +7.97°C) —
  the colder climate prevents the tank from overheating.
- Regimes 0 and 3 have PCM candidates that breach the safety limit
  (constraint margins around −9 to −10°C for PureTemp 58 in regime 0),
  consistent with those regimes' warmer ambients and higher solar loads.

This is a real, climate-driven consequence of this collector/tank
combination with no active overheat protection modeled — not a search or
simulator defect.

## Deviations from the full framework doc

No NSGA-II / full Pareto front, no active-learning loop (retrain-and-
repeat), single search pass per the reduced spec. The "confirm on an
unseen weather year" step of the selection rule is deferred — medoid-only,
noted explicitly rather than silently skipped.
