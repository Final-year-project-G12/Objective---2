# 08 — Phase 8 (Tamil Nadu): Robustness, Recommendation Cards, Objective 3 Hand-off

**Files touched:** `src/handoff/build_recommendation_cards.py`,
`src/handoff/build_obj3_contract.py`, `src/robustness/monte_carlo.py`
(one-line `DesignVector` fix). **Not touched:** robustness methodology
(draw count, uncertainty sources, thresholds), the safety-shield guard-band
logic, `src/robustness/weather_ensemble.py` (arrangement-agnostic — purely
about weather years). Adapted from
`a Rajasthan-pilot change plan (source removed from this project after adaptation, see docs_objective2/tamilnadu_phase_docs/)`.

## What was actually run (Tamil Nadu)

1. **Robustness rerun**: the existing 120-draw-per-design Monte Carlo (PCM
   latent heat ±10%, two-level weather noise drawn from a real 10-year
   historical ensemble, demand volume/timing, mains temperature) re-run
   against Phase 7's new arrangement-searched winners — not reused from any
   prior run. Only code change needed: `DesignVector` construction now
   passes `capsule_arrangement=row["arrangement"]`.
2. **Recommendation cards**: added "Selected arrangement" and "Arrangement
   rationale" lines beneath "Selected design" in every card. Fixed three
   pieces of stale hardcoded text discovered while doing this: the flat
   150 m elevation note (now real per-regime elevation), the "sim_v1"
   simulator tag (now sim_v2), and the "sphere, staggered (frozen)"
   capsule line (now dynamic per regime).
3. **Objective 3 contract**: added `capsule_arrangement` (now the real
   per-regime winning arrangement, not a hardcoded "staggered") and
   `arrangement_rationale` to each regime's design block; K=5→K=3 fixed in
   `regime_membership_rule`; `validated_simulator_version` → `sim_v2_tamilnadu`;
   added an explicit `supersession_note` (every contract from before
   2026-09-17 is now a stale working draft — two changes landed together:
   arrangement search and the Objective 1 data refresh); removed the
   stale "PCM-volume capped at ~12.9%" deferred-work item (resolved by the
   earlier count-widening to 37, already reaching 19.8%).

```
python pipeline.py --state tamilnadu --stage robustness
python pipeline.py --state tamilnadu --stage handoff
```

## Results

*(Updated 2026-09-18 for the Objective-1-shortlist restoration — see
[docs_objective2/18_OBJECTIVE1_SHORTLIST_RESTORED.md](../18_OBJECTIVE1_SHORTLIST_RESTORED.md).)*

**Robustness (120 draws × 3 regimes = 360 total simulator re-runs):**

| Regime | PCM | Arrangement | P(meets delivery) | P(meets demand) | P(temp-safe) | Robust? |
|---|---|---|---|---|---|---|
| 0 | RT57HC | radial | 100% | 100% | **0%** | NOT ROBUST |
| 1 | n-Hexacosane (C26) | single-layer | 99% | 72% | **19%** | NOT ROBUST |
| 2 | n-Pentacosane (C25) | single-layer | 100% | 95% | **0%** | NOT ROBUST |

Consistent with Phase 7's nominal constraint margins (regimes 0 and 2 were
already negative/unsafe under nominal operation; regime 1 was barely
positive at +0.12°C). Under weather/demand/property uncertainty, every
regime falls well short of the framework's P(temp-safe)≥95% bar — reported
plainly as a caveat, per this project's own convention, not hidden or
averaged away. This is the direct evidence for why Objective 3's active
bypass shield is a hard requirement, not an optional safety feature, for
all three of this state's regimes. This is also the expected consequence
doc 18 flagged in advance: Objective 1's actual shortlist PCMs melt at
54-58°C, a range Phase 4's own capability check already showed running
close to this tank's real charging-hour temperatures.

**A card-generation bug found and fixed while updating the cards for this
run**: `build_recommendation_cards.py` previously asserted every non-plain
winner "reached the regime's own best useful-energy value... winning
outright" unconditionally. Checking the actual numbers showed this was
never literally true (every regime's winner is a few hundredths of a
percent below the true pool maximum, picked via the tolerance+tie-break
rule, not by being the single best candidate) — and for **regime 1** the
gap is real enough to matter: the selected n-Hexacosane/single-layer
design (1623.22 kWh) is ~0.06% below a *safety-compliant* RT57HC
candidate also within tolerance (1624.22 kWh, `meets_temperature_safety
=True`), which itself is only marginally above plain tank (1623.96 kWh).
The safety-first tie-break step is working correctly (it does exclude the
single highest-energy candidate in the pool, n-Pentacosane at 1625.23 kWh,
because that one fails nominal temperature safety) — but the *next*
tie-break criterion, pump energy, is then deciding among the remaining
safety-compliant candidates on differences of order 1e-7 kWh, which is
simulator noise, not physics, and in this instance it did not pick the
safety-compliant candidate with the most energy. The card text now reports
the actual gap and its cause instead of overclaiming; the selection rule's
tie-break order itself was left unchanged pending a decision (see doc 07's
regime-1 caveat).

**Recommendation cards**: all 3 regimes have a complete card with
arrangement + rationale, real elevation, K=3-consistent language, and
`sim_v2_tamilnadu` tagged throughout. The "PCM shortlist" and "Tm_target_C"
lines were also updated to stop describing the superseded Tm-retargeting
methodology (doc 12) and correctly point to doc 18.

**Objective 3 contract**: schema-consistent, `contract_version:
"obj3_contract_v2.0_2026-09-17"`, all 3 regimes carry `capsule_arrangement`
("radial"/"single-layer"/"single-layer") and `arrangement_rationale`
verbatim from Phase 7, supersession note present, and every regime's
`pcm_id` is confirmed to be one of Objective 1's actual Top-3 consensus
candidates.

## Exit check — this closes the Tamil Nadu arrangement-restoration +
data-refresh batch, but not the project

- All draws are simulator-based (confirmed — `run_case` called per draw,
  never the surrogate). Draw counts/seeds match the documented 120/`MC_SEED`.
- Every regime has one card and one contract entry (3/3).
- Percentile calculations spot-checked against `robustness_results.csv`
  (360 rows = 120 draws × 3 regimes, matches).
- Safety shield (guard-band trigger, `max_limit - 3°C`) remains stricter
  than the hard simulator limits — unchanged by this work.
- **Do not rebuild the four-state comparative table yet** — Rajasthan,
  Assam, and Uttarakhand each need this identical Phase 1-8 change (Objective
  1 refresh where applicable + arrangement restoration) before that
  comparison is valid again, per `obj2_revised`'s cross-state validity
  checks (identical shared-config hash, identical simulator version,
  identical selection rule).
- Objective 3 must re-pull `obj3_environment_contract_tamilnadu.json`
  rather than use any cached copy from before 2026-09-17 — a design
  selected under the old K=5/staggered-only run does not correspond to any
  regime in this version.
