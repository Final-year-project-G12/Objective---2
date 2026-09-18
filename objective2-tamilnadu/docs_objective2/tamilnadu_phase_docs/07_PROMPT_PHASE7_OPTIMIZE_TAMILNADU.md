# 07 — Phase 7 (Tamil Nadu): Search Spans Arrangement, Winner Gets a Rationale

**Files touched:** `src/optimize/search.py`, `src/optimize/select_deployable.py`.
**Not touched:** the safety-shield default, the >15% surrogate-error rule,
the PCM-only selection pool (both 2026-09-13/14 corrections stay exactly as
they were). Adapted from
`a Rajasthan-pilot change plan (source removed from this project after adaptation, see docs_objective2/tamilnadu_phase_docs/)`.

## What was actually run (Tamil Nadu)

1. **`search.py`**: candidate generator now samples arrangement uniformly
   from `{single-layer, staggered, radial}` alongside diameter/count/flow,
   before the real Phase 2 geometry gate. Candidate count raised
   **400→600** per pair (documented reasoning: candidates now split ~3 ways
   by arrangement before the gate, so 600 keeps each arrangement's
   post-gate pool close to the old per-arrangement-equivalent budget).
   Logs which arrangement(s) appear in each pair's top 5(→20).
2. **`select_deployable.py`**: after the unchanged simulator-confirmation
   step (every top candidate re-run for real, >15% large-error rule,
   PCM-only pool, safety shield active), added `arrangement_rationale`:
   compares the winning arrangement's simulator-confirmed useful energy
   against the best confirmed candidate of the SAME PCM under each OTHER
   arrangement in the same regime. A margin inside the observed mean
   surrogate-vs-simulator error is reported as "tied within noise," not a
   real difference.

```
python pipeline.py --state tamilnadu --stage optimize
```
(`--top-n-per-pair 20`, unchanged default — 12 regime×PCM(+no-PCM) groups
× 20 = 240 candidates simulator-confirmed.)

## Results

*(Updated 2026-09-18 for the Objective-1-shortlist restoration — see
[docs_objective2/18_OBJECTIVE1_SHORTLIST_RESTORED.md](../18_OBJECTIVE1_SHORTLIST_RESTORED.md).
The PCM pool searched per regime is now Objective 1's actual Top-3
consensus shortlist, not a Tm-retargeted substitute list — every winner
below is genuinely one of Objective 1's candidates.)*

**Surrogate-vs-simulator mean error: 0.03%** across all 240 confirmed
candidates (0/240 exceeded the 15% large-error threshold). Surrogate
proposal step: 389-411/600 candidates survived the geometry gate per
regime×PCM pair (12 pairs = 3 regimes × [3 shortlisted PCMs + no-PCM
baseline]).

**Deployable design per regime:**

| Regime | PCM | Arrangement | d (m) | N | Flow (kg/s) | Useful energy | Solar fraction | Constraint margin |
|---|---|---|---|---|---|---|---|---|
| 0 | RT57HC | radial | 0.0420 | 20 | 0.0274 | 1756.33 kWh | 56.09% | -6.86°C |
| 1 | n-Hexacosane (C26) | single-layer | 0.0440 | 26 | 0.0219 | 1623.22 kWh | 50.86% | +0.12°C |
| 2 | n-Pentacosane (C25) | single-layer | 0.0459 | 10 | 0.0119 | 1633.98 kWh | 53.41% | -6.29°C |

**Arrangement rationale, reported honestly rather than overclaiming a
decisive win:**
- Regime 0: arrangements tied within noise (margin ~0.00%, inside the
  0.03% surrogate-vs-sim noise band) — arrangement not decisive; next-best
  was single-layer.
- Regime 1: **only arrangement=single-layer was simulator-confirmed** for
  this regime/PCM pool — no other arrangement had a confirmed candidate to
  compare against.
- Regime 2: arrangements tied within noise (margin ~0.00%) — arrangement
  not decisive; next-best was radial.

Unlike the previous (Tm-retargeted) run, radial does **not** sweep all
three regimes this time — it wins regime 0, but regime 1 and 2 land on
single-layer. This is expected: the restored shortlist changes which PCMs
are searched per regime, and arrangement's effect was already shown
(Phase 6) to be minimal on the continuous targets — so which arrangement
wins is sensitive to exactly which few tied-within-noise candidates the
simulator confirms, not a strong physical preference for one arrangement.

**Regime-1 caveat, flagged for a decision**: the selected design's useful
energy (1623.22 kWh) is ~0.05% *below* plain tank's (1623.96 kWh) in this
run. The selection rule (reject infeasible -> within 5% tolerance of best
-> safety -> minimize pump energy -> minimize PCM mass -> minimize capsule
count -> constraint margin) is working exactly as documented, but many
regime-1 candidates are statistically tied on useful energy, and the
pump-energy tie-break is deciding among differences of order 1e-7 kWh —
simulator noise, not a real physical distinction. Whether the tie-break
order should be revisited (e.g., break on useful-energy margin before pump
energy) is an open question for the next iteration.

**Safety, reported not hidden**: 2 of 3 regimes (0 and 2) have negative
constraint margin under nominal operation — these are still the best PCM
designs found within the energy tolerance, but require Objective 3's
active bypass/discharge control before hardware deployment (existing
`deployment_note` convention, unchanged by this work). Phase 8's Monte
Carlo results (below) confirm this is a real, robust-negative finding, not
a one-off.

## Exit check before moving to Phase 8

Every selected row has a simulator result, not a surrogate-only value
(confirmed: `sim_*` columns populated for all 3 winners). No plain-tank
diagnostic entered the PCM-only final pool, and every winning PCM is
confirmed present in Objective 1's actual Top-3 consensus shortlist for
its regime (`configs/states/tamilnadu.yaml`'s `pcm_shortlist`). Safety
evaluated using the correct water/PCM limits per design. The regime-1
tie-break finding above should be surfaced to the user/next iteration, not
smoothed over in Phase 8's cards.
