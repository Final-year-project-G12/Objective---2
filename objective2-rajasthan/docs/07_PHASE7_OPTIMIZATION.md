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
> - **2026-09-18** — the whole Objective 1 -> Objective 2 input chain was
>   resynced (`configs/states/rajasthan.yaml`,
>   `state_config_version: "state_config_rajasthan_v2.0_2026-09-18-resync"`):
>   the O1 PCM shortlist per regime changed (cluster0 -> Palmitic-stearic
>   acid/Expanded graphite / savE(R) OM55 / Myristic acid/NBR-0.5;
>   cluster1 -> PureTemp 60 / CrodaTherm 60 / n-Heptacosane (C27);
>   cluster2 -> n-Heptacosane (C27) / PureTemp 58 / PlusICE A58),
>   superseding the pre-resync RT50/RT45HC/Lauric acid C12 and savE
>   OM50/PCM3/PCM6 shortlists. Phase 7 was re-run against the resynced
>   config today (13:43-13:46); every result below is from that re-run,
>   not the arrangement-restore-only run this section otherwise describes.

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

**Mean surrogate-vs-simulator error across all 60 confirmed candidates
(2026-09-18 resynced run): 0.02% (max 0.064%; 0/60 exceeded the 15%
large-error threshold).** Independent confirmation (beyond Phase 6's
hold-out R²) that surrogate, geometry engine and simulator are
self-consistent under the resynced PCM shortlist too.
Energy-conservation residual across the same 60 full-year runs stayed
tiny (mean 0.00029%, max 0.00037% of collector energy) — generalising
Gate 1's 7-case result to the whole search.

## Result: deployable design per regime (arrangement-restored search)

| Regime | Winning PCM | Arrangement | Diameter (m) | Count | Flow (kg/s) | Useful energy (kWh) | Solar fraction | Max water T (°C) | Max PCM T (°C) | Margin to nearest limit | Arrangement rationale |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | **savE® OM55** | single-layer | 0.04068 | 9 | 0.01648 | 1584.88 | 54.98% | 68.68 | 62.90 | 2.10 °C (to 65 °C PCM) | Tied within noise (margin=-0.06% ≤ 0.02% noise band) against `single-layer` |
| 1 | **PureTemp 60** | staggered | 0.04263 | 10 | 0.01230 | 1844.48 | 61.60% | 72.06 | 63.35 | 1.65 °C (to 65 °C PCM) | Tied within noise (margin=-0.00% ≤ 0.02% noise band) against `single-layer`/`staggered` |
| 2 | **PureTemp 58** | staggered | 0.04524 | 9 | 0.01851 | 1789.95 | 58.21% | 72.02 | 63.17 | 1.83 °C (to 65 °C PCM) | Tied within noise (margin=0.00% ≤ 0.02% noise band) against `radial`/`single-layer`/`staggered` |

All three deployable designs are PCM (plain tank excluded from the
winner pool per the 2026-09-14 selection-rule correction) and all clear
temperature safety under the rule-based safety shield
(`system_config_shared.yaml: safety_shield.enabled`, adopted 2026-09-13
— see `09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md` §6-§8). **These winners
are from today's (2026-09-18) resynced run** — the O1 → O2 input chain
was rebuilt (`configs/states/rajasthan.yaml`
`state_config_rajasthan_v2.0_2026-09-18-resync`), replacing the prior
RT50 / Paraffin-HDPE PCM3 / savE® OM50 (radial) winners (themselves the
arrangement-restore-run winners, which had in turn replaced RT45HC /
Paraffin-HDPE-PCM6 / Paraffin-HDPE-PCM3) with the current
savE® OM55 (single-layer) / PureTemp 60 (staggered) / PureTemp 58
(staggered) set — expected, not a regression: the resync changed which
PCMs are even in each regime's shortlist, on top of the widened count
bound (8–37, was 8–24), the 600-candidate search (was 400), and
arrangement now entering the candidate pool. None of the three current
winners is `radial` — all three are decided within Phase 6's
near-zero-importance noise band, see "Arrangement did or did not decide
the outcome" below.

## Top-5 composition per regime×PCM pair — what the search actually surfaced

| Regime / PCM | single-layer | staggered | radial |
|---|---|---|---|
| 0 / Palmitic-stearic acid/Expanded graphite | 2 | 0 | 3 |
| 0 / savE® OM55 | 2 | 0 | 3 |
| 0 / Myristic acid/NBR-0.5 | 3 | 0 | 2 |
| 0 / NONE_plain_tank | 1 | 1 | 3 |
| 1 / PureTemp 60 | 2 | 3 | 0 |
| 1 / CrodaTherm 60 | 2 | 3 | 0 |
| 1 / n-Heptacosane (C27) | 1 | 2 | 2 |
| 1 / NONE_plain_tank | 2 | 3 | 0 |
| 2 / n-Heptacosane (C27) | 2 | 3 | 0 |
| 2 / PureTemp 58 | 2 | 2 | 1 |
| 2 / PlusICE A58 | 0 | 3 | 2 |
| 2 / NONE_plain_tank | 1 | 2 | 2 |

(Rebuilt from today's, 2026-09-18, resynced `phase7_surrogate_top_candidates.csv`
— the old table's RT50/RT45HC/Lauric acid C12 and savE OM50/Paraffin-HDPE
PCM3/PCM6 rows no longer exist; the current shortlist is per
`configs/states/rajasthan.yaml`.) Composition still varies considerably
by pair — some pairs (0/Palmitic-stearic, 0/savE OM55) lean radial
(3/5), while regime 1's pairs lean staggered (3/5 in all three). No pair
is unanimous (5/5) this run, but the spread is still consistent with
Phase 6's finding that arrangement has near-zero effect on predicted
useful energy: which arrangement lands in a given top-5 is close to a
coin flip rather than a strong preference, so this scatter is the
expected consequence of that finding, not a search-quality problem.

## Arrangement did or did not decide the outcome — reported per regime, not forced to a single story

- **Regime 0 (savE® OM55):** reported as tied within noise by
  `select_deployable.py`'s own rationale text (margin=-0.06% vs. a 0.02%
  noise band, tied arrangements list = `['single-layer']`) — both
  `single-layer` and `radial` savE® OM55 candidates were confirmed for
  this regime/PCM pool (no `staggered` one was), but the code's own tie
  classification only names `single-layer` as tied; treated here as a
  UNVERIFIED — could not confirm whether this is a deliberate "only
  within-noise-band alternatives count as tied" rule or a reporting quirk,
  since `radial`'s own best confirmed energy (1585.80 kWh) is actually
  higher than the `single-layer` winner's (1584.88 kWh) but is not listed
  as tied.
- **Regime 1 (PureTemp 60):** all confirmed arrangements' best
  simulator-confirmed useful energy landed within the run's own 0.02%
  surrogate-vs-simulator noise band of each other — reported as "tied
  within noise."
- **Regime 2 (PureTemp 58):** same as Regimes 0/1 — tied within noise
  across `radial`/`single-layer`/`staggered`, with `staggered` winning
  the tie-break (lower pump energy / larger margin among near-identical
  candidates), not because it produced meaningfully more useful energy.

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
| 0 | 1584.82 | 1585.93 (Palmitic-stearic acid/Expanded graphite, radial) | +0.07% | **Yes** |
| 1 | 1843.39 | 1844.91 (n-Heptacosane (C27), staggered) | +0.08% | **Yes** |
| 2 | 1788.92 | 1790.22 (n-Heptacosane (C27), staggered) | +0.07% | **Yes** |

(Note: the single best-simulated PCM candidate per regime above is not
always the same PCM as the deployable winner in the table further up —
several PCM candidates land within the 5% Pareto tolerance of each other,
and the selection rule's tie-break — min pump energy, then PCM mass, then
capsule count, then max margin — picks among that near-tied pool, not
simply the single highest-energy row. E.g. regime 0's best-found PCM
above is `Palmitic-stearic acid/Expanded graphite`, but the deployable
winner is `savE® OM55`; regimes 1/2's best-found PCM above is
`n-Heptacosane (C27)`, but the deployable winners are `PureTemp 60` /
`PureTemp 58` respectively — all within Pareto tolerance of the
best-found row.)

Same physical story as before arrangement was restored, and as this
project's own Phase 4 Gate 3 / Phase 5 DOE: within these bounds and this
50 L direct-encapsulation tank, Objective 1's climate-ranked PCM shortlist
gives at most a **fraction-of-a-percent** useful-energy improvement over
plain water — two orders of magnitude below the pre-declared 5% Pareto
tolerance. Restoring arrangement as a search variable did not change this
qualitative conclusion; it added a fourth searched dimension without
producing a new, decisive result along it.

**Note on why this thin margin is the reported result, not the resized
alternative:** `09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md` §7 already shows
a strictly better result is available — resizing the frozen 50 L tank to
IS 12976:2023's 75 L/m² reference ratio (112.5 L) makes every shortlisted
PCM beat plain water more decisively **without** the safety shield at
all. It was deliberately not adopted here because it requires changing a
shared, frozen, hashed config file that all four states re-run from, out
of this 40-hr pass's scope — not because it was unknown.

## Deviations from the full framework doc

No NSGA-II / full Pareto front, no active-learning loop (retrain-and-
repeat) — single search pass per the reduced spec, now spanning all four
decision variables jointly (diameter, count, arrangement, flow). The
"confirm on an unseen weather year" step of the selection rule is
deferred (medoid-only, single year), stated explicitly.
