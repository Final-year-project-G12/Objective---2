# 07 — Phase 7 Audit: Optimization Pass + Simulator Confirmation (Rajasthan)

Files: `src/optimize/search.py`, `src/optimize/select_deployable.py`.
Run: `python pipeline.py --state rajasthan --stage optimize`.
Output: `results/phase7_surrogate_top_candidates.csv`,
`results/phase7_optimized_designs.csv` (PCM-comparison report),
`results/phase7_deployable_design_per_regime.csv` (final selection).

> **Ported from `objective2-tamilnadu/src/optimize/`.** Search logic
> (400 random candidates per pair, real Phase 2 geometry gate before
> scoring, rank by predicted `useful_energy_kWh`), the >15% large-error
> rule, and the pre-declared selection rule are all unchanged. Only the
> model path (`results/phase6_surrogate_models.pkl`), the three output
> paths (flat `results/phase7_*`) and the `__main__` state fallback
> differ.

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
   (`selection.pareto_tolerance_pct = 5%`) is applied per regime: reject
   anything failing the temperature-safety check → keep every
   simulator-confirmed candidate within 5% of the best useful energy for
   that regime → among those, minimise pump energy, then PCM mass, then
   capsule count → prefer the larger constraint margin as the final
   tie-break. "Confirm on an unseen weather year" is deferred (medoid-only,
   per the 40-hr cut list — noted, not hidden).

## Result: surrogate accuracy in practice

**Mean surrogate-vs-simulator error across all 60 confirmed candidates:
0.025% (max 0.100%). 0/60 exceeded the 15% large-error threshold.**
Independent confirmation (beyond Phase 6's hold-out R²) that surrogate,
geometry engine and simulator are self-consistent. Energy-conservation
residual across the same 60 full-year runs stayed tiny (mean 0.00087%,
max 0.0018% of collector energy) — generalising Gate 1's 5-case result to
the whole search.

## Result: deployable design per regime

| Regime | Winning design | Diameter (m) | Count | Flow (kg/s) | Useful energy (kWh) | Solar fraction | Max water T (°C) | Margin to 75 °C |
|---|---|---|---|---|---|---|---|---|
| 0 | **plain tank (no PCM)** | 0.0441 | 23 | 0.0349 | 1585.70 | 54.97% | 68.6 | 6.4 °C |
| 1 | **plain tank (no PCM)** | 0.0407 | 14 | 0.0298 | 1673.36 | 58.23% | 72.4 | 2.6 °C |
| 2 | **plain tank (no PCM)** | 0.0443 | 8 | 0.0127 | 1592.27 | 53.88% | 68.7 | 6.3 °C |

(`n_capsule` / diameter are reported for the plain-tank rows but not
physically used — `run_case.py` forces `n_capsule_effective = 0` whenever
no PCM is given.)

## The headline finding, now with full-search evidence

Best simulator-confirmed design **per PCM** in each regime
(`phase7_optimized_designs.csv`) — every shortlisted PCM's best-found
geometry beats the best plain-tank geometry found by the same
400-candidate search, by a razor-thin margin:

| Regime | Best plain tank (kWh) | Best PCM found (kWh) | PCM's edge | PCM meets safety? |
|---|---|---|---|---|
| 0 | 1585.70 | 1588.14 (RT45HC) | +0.15% | **No** |
| 1 | 1673.36 | 1675.11 (savE® OM50) | +0.10% | **No** |
| 2 | 1592.27 | 1593.44 (Paraffin/HDPE PCM3) | +0.07% | **No** |

Same physical story as Tamil Nadu, and as this project's own Phase 4
Gate 3 / Phase 5 DOE: within the frozen bounds (≤12.9% PCM volume
fraction) and this 50 L direct-encapsulation tank, Objective 1's
climate-ranked PCM shortlist gives at most a **fraction-of-a-percent**
useful-energy improvement over plain water — two orders of magnitude
below the pre-declared 5% Pareto tolerance. The selection rule therefore
treats plain tank and best PCM as equivalent on energy and picks the
lower PCM mass (zero → plain tank), in **every** regime.

## The temperature-safety filter is fully binding for PCM here (stronger than Tamil Nadu)

Of the 60 simulator-confirmed candidates, **only 15 satisfied
`meets_temperature_safety`** (max water ≤ 75 °C, max PCM ≤ 65 °C, zero
per-substep violations over the year) — and **all 15 are plain-tank
candidates** (5 per regime). **0 / 45 PCM candidates passed**, in any
regime, for any of the six shortlisted PCMs. Tamil Nadu had one regime
(its regime 4) where PCM candidates cleared safety; Rajasthan has none —
consistent with the Phase 5 finding that every one of the 111 valid DOE
cases exceeded the 65 °C PCM limit under this collector/tank sizing and
Rajasthan's hot-dry irradiance.

So in Rajasthan the plain tank doesn't just win on the cost/PCM-mass
tie-break — it is the **only** design family that lands inside the safety
envelope at all. This is a real, previously-unexamined consequence of the
frozen 1.5 m² collector / 50 L tank against Rajasthan's solar resource
with no active overheat protection modelled (no relief valve, no forced
high-temperature bypass) — it shows up consistently across
independently-sampled candidates, so it is not a search or simulator
defect.

**Note on regime 1:** the deployable plain-tank design there reaches
72.4 °C max water temperature — only 2.6 °C below the 75 °C scald limit.
It passes, but the margin is thin; an overheat shield/bypass (Objective 3
territory) or a collector-sizing revisit is worth flagging for any
follow-up.

## What this means for the recommendation

Under the frozen shared config and the pre-declared selection rule, the
Rajasthan deployable design for all three climate regimes is a
**plain (sensible-only) 50 L tank** — the Objective 1 PCM shortlist does
not earn its mass here. This is a defensible negative result, not a gap:
it is the same conclusion Phase 4 Gate 3 and Phase 5 reached, now
confirmed by a 400-candidate-per-pair search with full simulator
re-confirmation. If PCM is to be pursued for hot-dry states, the
follow-up is (a) widen the design bounds so > 12.9% PCM fraction becomes
reachable **and** add a high-temperature bypass, or (b) revisit the
frozen collector/tank sizing for hot climates — both out of Objective 2's
40-hr scope, named here rather than silently dropped.

## Deviations from the full framework doc

No NSGA-II / full Pareto front, no active-learning loop (retrain-and-
repeat) — single search pass per the reduced spec. The "confirm on an
unseen weather year" step of the selection rule is deferred (medoid-only,
single 2025 year), stated explicitly.
