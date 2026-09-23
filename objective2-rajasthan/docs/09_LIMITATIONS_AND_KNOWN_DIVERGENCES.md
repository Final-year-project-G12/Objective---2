# 09 — Limitations and Known Divergences (Rajasthan)

Written 2026-09-13, after implementing `O2_Rajasthan_HighImpact_Fixes.md`
(Fixes 1-5 + the delivery-temperature finding), then updated the same day
after §7 (the IS 12976:2023 standards-compliant sizing check) found the
collector:tank ratio itself — not just PCM melting point, and not
requiring an active shield — resolves the safety failure. **Read §7
before §0/§6 below**: it supersedes their "no PCM survives without an
active shield" conclusion with a stronger one — no shield needed once
the tank is resized to a cited standard's own reference ratio. §0/§6 are
left as originally written beneath it (dated-addenda convention, not a
rewrite of history) because the root-cause diagnosis they reach
(collector:tank sizing, not material choice) is exactly what led to §7's
check in the first place. This doc exists because
CLAUDE.md and the fix doc both flag the same problem: a 4-objective FYP
with a hard O1→O2→O3→O4 boundary will accumulate divergences between
objectives that have nowhere to be named explicitly. Rather than letting
reviewers discover them, they are named here.

**2026-09-17 note — the PCM shortlist §0/§2/§4/§6 below were computed
against has since changed again.** Sections 0, 2, 4, and 6 build their
"no PCM survives without a shield" case around the 2026-09-13 "refreshed
(67 °C-basis)" shortlist (`savE® OM55`, `CrodaTherm 60`, `PlusICE A58`,
plus the supplementary RT80HC/RT82 overheat-protection track). By
2026-09-17, `configs/states/rajasthan.yaml` and every phase doc from
Phase 2 onward instead reference a different shortlist — `RT50, RT45HC,
Lauric acid (C12)` (cluster 0) and `savE® OM50, Paraffin/HDPE PCM3,
Paraffin/HDPE PCM6` (clusters 1-2) — indicating Objective 1's shortlist
was refreshed a second time between these two dates. **§0/§2/§4/§6's
specific supporting numbers below (the 0/60 candidate count, the
RT80HC/RT82 datasheet track) were computed against the now-superseded
67 °C-basis shortlist and have not been re-verified against today's
shortlist.** The qualitative conclusion likely still holds — Phase 5, 7,
and 8's current results (run against today's shortlist, see
`docs/05_PHASE5_DOE.md`, `docs/07_PHASE7_OPTIMIZATION.md`) independently
reproduce the same pattern (PCM fails temperature safety unshielded,
passes shielded, near-ties plain water on energy) — but this is
independent corroboration of the *pattern*, not a re-verification of
§0/§2's specific numbers. Flagged here per this doc's own dated-addenda
convention rather than silently reusing stale figures; whoever owns
Objective 1 should confirm whether the shortlist changed intentionally a
second time, and if the specific 0/60-style numbers are needed again
(e.g. for the paper), re-run `check_overheat_track_pcm.py` and Phase 7
against today's shortlist rather than citing the numbers below as current.

**2026-09-18 note — superseded again, see §10.** "Today's shortlist" in
the note directly above refers to the 2026-09-17 shortlist
(`RT50, RT45HC, Lauric acid (C12)` / `savE® OM50, Paraffin/HDPE PCM3,
Paraffin/HDPE PCM6`), which was itself replaced by a full O1↔O2 re-sync on
2026-09-18 (§10 below) — the current shortlist is
`Palmitic-stearic acid/Expanded graphite, savE® OM55, Myristic acid/NBR-0.5`
(cluster 0), `PureTemp 60, CrodaTherm 60, n-Heptacosane (C27)` (cluster
1), `n-Heptacosane (C27), PureTemp 58, PlusICE A58` (cluster 2), and
Phases 2-8 have all been re-run against it. §0/§2/§4/§6 below (and the
2026-09-17 note above) describe neither the current shortlist nor the one
immediately before it — read §10 for the authoritative current PCM
shortlist, medoids, and deployable-design table.

## 0. HEADLINE FINDING — the root cause is collector:tank sizing, not PCM melting-point choice

Section 2 below reports that the 75-85 °C overheat-protection track
(RT80HC/RT82) also fails the 65 °C safety limit, and explains it as "the
tank never gets hot enough to melt these PCMs, yet they still overheat
via sensible heating alone." That result deserves to be a headline
finding for the paper, not a footnote to Fix 1, because of what it rules
out: **a PCM's temperature tracks the surrounding water's sensible
temperature almost 1:1 until it starts undergoing phase change** (that is
exactly what `ua_eff * (T_w - T_pcm)` coupling in `tank_model.py` means
physically). If a PCM overheats past the material-stability limit
*without ever melting*, the failure has nothing to do with which melting
point was chosen — a PCM with a melting point at 40 °C, 55 °C, 61 °C, 78
°C or 82 °C was tested across this project's shortlists, and **every
single one** eventually gets cooked by the water it sits in, either by
melting into it (low Tm) or by simply heating past the limit before ever
melting (high Tm). There is no point on the Tm axis this frozen tank
geometry does not eventually break.

**This reframes the entire Rajasthan negative result.** It is not "no
PCM in our shortlist happened to work" (a claim any reviewer can poke at
with "did you just pick bad PCMs?") — it is **"for this 1.5 m² collector
/ 50 L tank sizing ratio under Rajasthan's solar input, no fixed PCM
melting point survives, because the tank itself overheats on solar input
alone (68-89 °C observed, Phase 3/8) faster than any single-material PCM
can buffer it."** The root cause is the **collector-to-tank sizing
ratio**, not material selection. This is a materially stronger and more
general claim, and it is the one that should lead the Objective 2
Rajasthan write-up — sections 1-5 below (delivery-temperature
divergence, feedback loop, Gate 4 disclosure, PCM data provenance,
widened-bounds check) are supporting detail underneath it, not
independent findings of equal weight.

**One precise qualifier (see §6):** this claim is true *of the unshielded
physics*, which is the physics O2's own reported design is deliberately
evaluated under. If a rule-based safety shield is instead treated as a
standing design assumption, it rescues PCM designs from this exact same
failure mode — and once rescued, PCM is not worse than plain water, it is
marginally better (§6 has the numbers). **This is kept as a
supplementary, decision-relevant result, not adopted as O2's own
recommendation**: a threshold-triggered bypass is itself a real-time
control action, which is Objective 3's territory to own, not something
O2 should quietly bake into its own reported design. §6 explains this
choice and why it strengthens, rather than weakens, the case for
Objective 3's controller.

## 1. Objective 1 ↔ Objective 2 delivery-temperature divergence — QUANTIFIED (2026-09-18), still not adopted

Objective 1's `T_DELIVERY_C` is **60 °C** (corrected 2026-09-13, Avargani
et al. 2021-anchored — see project CLAUDE.md §3.2). Objective 2's frozen
`system_config_shared.yaml` `delivery.target_temp_C` is **45 °C**, chosen
before O1's correction and — critically — declared explicitly frozen and
**identical across all four states** ("Identical for Tamil Nadu,
Rajasthan, Assam, Uttarakhand... changing this file means every state
must re-run from DOE onward," `system_config_shared.yaml` header). This
is not an oversight this fix silently patched: editing Rajasthan's copy
alone to match O1's 60 °C would break the cross-state comparability that
config freeze exists to protect, while editing all four states' copies is
a coordinated multi-state re-run outside this fix's Rajasthan-only scope.

**2026-09-18 — the divergence was quantified with a supplementary check**
(`check_delivery_temp_reconciliation.py`, same in-memory-override pattern
as the Fix 3/Fix 6 checks — `system_config_shared.yaml` itself untouched).
It re-scores every one of Phase 7's already-confirmed designs (plain tank
+ each shortlisted PCM, all 3 regimes) against O1's 60 °C target instead
of the frozen 45 °C target. Full table:
`results/fix7_delivery_temp_reconciliation_supplementary.md`.

**Result: reconciling to 60 °C is not a safe drop-in change.** Because
`target_temp_C` only feeds the solar-fraction *denominator*
(`e_demand_ideal_kWh = draw_kg * cp * (target_temp_C - mains_temp_C)`)
and the `delivery_temp_hours` count — it does not change the simulated
water/PCM temperatures at all — safety is unaffected (every case still
clears both temperature limits, 0 violations). But solar fraction drops
sharply and uniformly:

| Regime | Best PCM @ 45 °C (frozen) | Best PCM @ 60 °C (O1-reconciled) | In 54-84% Gate-4 band @ 60 °C? |
|---|---|---|---|
| 0 | 55.34% (RT45HC) | 35.71% (RT45HC) | **No** |
| 1 | 58.33% (savE® OM50) | 38.36% (savE® OM50) | **No** |
| 2 | 54.02% (savE® OM50) | 35.26% (savE® OM50) | **No** |

Every one of the 24 tested cases (plain tank + 3 PCMs × 3 regimes × 2
targets) falls out of the Singh et al. (2025) 54-84% benchmark band once
scored at 60 °C — a ~19-20 percentage-point drop in every regime, not
just a borderline shift. Naively bumping `target_temp_C` in the frozen
config would fail Gate 4 across the entire pipeline, not bring O2 into
agreement with O1's basis; the current 45 °C target is what makes Gate 4
pass today.

**STALE FLAG (added by 2026-09-18 doc audit):** `check_delivery_temp_reconciliation.py`
was run at 13:10:19 on 2026-09-18, but `configs/states/rajasthan.yaml`'s
resync (§10 below) was written at 13:42:57 the same day — i.e. **before**
the resync. The PCM names in the table above (RT45HC, savE® OM50) are the
PRE-resync shortlist, confirmed by cross-referencing against the current
`configs/states/rajasthan.yaml` (post-resync shortlist is
Palmitic-stearic acid/Expanded graphite / savE® OM55 / Myristic acid
(cluster 0), PureTemp 60 / CrodaTherm 60 / n-Heptacosane C27 (cluster 1),
n-Heptacosane C27 / PureTemp 58 / PlusICE A58 (cluster 2) — none of which
match "RT45HC"/"savE® OM50" above). The qualitative conclusion (45 °C
frozen target vs. 60 °C O1-reconciled target produces a large, uniform
solar-fraction drop) likely still holds in direction and rough magnitude,
since it is driven by the `target_temp_C` definition change, not by which
PCM is compared — but the specific percentages in the table have not been
re-verified against the post-resync shortlist. Re-run
`check_delivery_temp_reconciliation.py` against the current
`phase7_deployable_design_per_regime.csv` if the exact numbers are needed
for the paper.

**Decision: documented and quantified divergence, still not silently
reconciled.** The two objectives currently model "the same" domestic
hot-water system with a 15 °C disagreement on what temperature it
delivers. This affects `Tm_target_C`, `L_required_kJ_per_kg` (both
O1-side) and O2's own solar-fraction definition (see §3 below)
simultaneously. Genuinely aligning them is **not** a one-line config
edit — this check shows it would require a coordinated Phase 3-8 re-run
across all four states with the tank/collector geometry and Gate-4
benchmark expectations reconsidered together (a larger tank/collector,
per §7's IS 12976 resizing finding, likely recovers some of this gap,
but that has not been tested jointly with the 60 °C target here). That
coordinated re-run remains out of this fix's single-state scope. Flagged
as explicit future work, with the quantified cost now on record instead
of an unquantified caveat.

## 2. Objective 1's PCM selection does not incorporate Objective 2's achievable-temperature/loading constraints

Objective 1 selects PCMs from climate/meteorological clustering + MCDM
only. Objective 2 is the first place the tank's *actual* achievable water
temperature (68-89 °C observed range, Phase 3/8) and *actual* achievable
PCM loading (~12.9% of tank volume under the frozen geometry bounds,
Phase 2) are computed — and both turn out to invalidate every version of
O1's Rajasthan shortlist tested so far:

- The refreshed (67 °C-basis) O1 shortlist (Tm 55-61 °C) sits closer to
  the tank's operating range than the stale (57 °C-basis) shortlist did,
  but still below it — 0/60 shortlisted-PCM candidates cleared the 65 °C
  PCM safety limit in Phase 7's re-run (see `docs/08`).
- A supplementary 75-85 °C "overheat-protection" track (real Rubitherm
  RT80HC/RT82 datasheet data — see §4 below) was tested specifically
  because it sits *above* the tank's peak, hypothesizing it would survive
  by simply never melting into an over-temperature liquid. It does not
  clear the limit either (0/6): the tank's water never gets hot enough to
  melt these PCMs at all (`final_f_melt = 0.0` in every case — the latent
  storage this track hoped to use is never engaged), yet the PCM still
  exceeds 65 °C via **sensible heating alone** while tracking the hot
  water it's immersed in. In other words: for this frozen tank geometry
  and Rajasthan's climate, there is no fixed PCM melting point — too low
  or too high — that avoids the 65 °C material-stability limit without an
  active shield. This is a genuinely useful negative result (it rules out
  "just pick a higher Tm" as a fix), not merely a restatement of Fix 1's
  original diagnosis.

**No feedback loop exists from O2 back to O1** to make either finding
change the shortlist O1 produces — this is fine for the current 40-hr,
single-pass, hard-boundary scope, but reviewers evaluating O1→O2→O3→O4 as
one system will reasonably ask why the PCM recommendation (O1) and the
deployable design (O2) disagree in every regime tested. State this
explicitly in the paper: *"Objective 1's PCM selection does not currently
incorporate Objective 2's achievable-temperature/loading constraints; a
future iteration would close this loop (e.g., O2 reporting an achievable
Tm/loading envelope back to O1's MCDM ranking criteria)."*

## 3. Solar-fraction definition disclosure (Gate 4)

Gate 4 compares O2's solar fraction (55.07%, no backup heater, 45 °C
delivery target) against Singh et al. (2025)'s cited 54-84% band and
reports **PASS**. As of Fix 4 (`src/verify/gates.py`,
`gates.py::gate4_calibration`), this PASS is now accompanied by an
explicit definition disclosure rather than a bare verdict: our
no-backup-heater, 45 °C-delivery-target solar fraction is a *stricter*
definition than is typically assumed in cited SWH literature, and
cross-tool solar-fraction comparisons can differ by up to 16 percentage
points purely from definitional choices (N'tsoukpoe 2026). Singh et al.
(2025)'s own exact definition is not independently recoverable from this
project's extracted source. Read Gate 4 as *"consistent with the cited
band under a stricter definition,"* not as proof the two studies compute
the same quantity. See `docs/04_PHASE4_VERIFICATION_GATES.md`, Gate 4.

## 4. 75-85 °C overheat-protection PCM track — data provenance

Per CLAUDE.md's grounding rule ("never answer from memory/assumption
alone on anything paper-specific — PCM properties..."): no PCM in this
project's grounded 55-row database
(`PCM_Properties_cleaned_mice_pmm_detailed.csv`, max Tm = 70 °C) reaches
75-85 °C. Two candidates were sourced by **direct PDF fetch of Rubitherm's
own current datasheets** (verified against the actual manufacturer PDF
content, not a search-engine snippet or secondhand table):

| PCM | Melting area | Heat storage capacity | Source |
|---|---|---|---|
| RT80HC | 77-80 °C (main peak 78 °C) | 220 kJ/kg ±7.5% (70-85 °C combined sensible+latent) | [Rubitherm RT80HC datasheet](https://www.rubitherm.eu/media/products/datasheets/Techdata_-RT80HC_EN_21012026.PDF), version 21.01.2026 |
| RT82 | 77-82 °C (main peak 82 °C) | 170 kJ/kg ±7.5% (70-85 °C combined sensible+latent) | [Rubitherm RT82 datasheet](https://www.rubitherm.eu/media/products/datasheets/Techdata_-RT82_EN_21012026.PDF), version 21.01.2026 |

Kept in `data/pcm/rajasthan_overheat_track_candidates.csv`, clearly
separate from the frozen O1 `pcm_database_rajasthan.csv` — this is an O2
supplementary track, not an O1 MCDM output. "Heat storage capacity"
combining sensible+latent heat over a stated temperature range is
Rubitherm's own standard datasheet convention across the whole RT-line
(the frozen database's existing RT-series entries, e.g. RT70HC's
260 kJ/kg, already carry the same convention under the `latent_heat_kJ_kg`
column name), so no unit/definition mismatch was introduced by adding
these two rows in the same format. Run via `check_overheat_track_pcm.py`
— see §2 above for the result.

## 5. Widened design-space bounds — 15-20% PCM loading (Fix 3)

The frozen `design_bounds_shared.yaml` (sphere-only, ≤24 capsules,
≤0.08 m diameter) caps reachable PCM volume fraction at 12.9%, below the
15-20% loading Chen et al. (2025) — this project's own cited DOE baseline
— reports results at. `check_widened_bounds_pcm_loading.py` runs one
supplementary case per regime with a widened, **in-memory-only** bounds
override (capsule diameter ≤0.12 m, count ≤40 — `design_bounds_shared.yaml`
itself is untouched, since it is frozen and identical across all 4
states) and confirms **18.1% PCM volume fraction is reachable** — above
Chen's 15% comparison point. Result:

| Cluster | Frozen bounds (12.9%) solar fraction | Widened bounds (18.1%) solar fraction | Direction |
|---|---|---|---|
| 0 | 54.68% | 53.99% | PCM loading increase, solar fraction **decreases** |
| 1 | 57.56% | 57.09% | decreases |
| 2 | 53.15% | 52.75% | decreases |

**This converts the original "not achievable within our bounds" caveat
into a confirmed negative result**: even at Chen-comparable (and higher)
PCM loading, this tank/climate combination does not benefit from more
PCM — solar fraction is flat-to-slightly-down as loading increases,
because the marginal PCM mass adds thermal inertia without engaging
useful latent storage at these PCMs' melting points. The original
"PCM gives <0.2% improvement" conclusion in Phase 7 is confirmed, not
merely inherited from a narrower design space than the literature
baseline. See `results/fix3_widened_bounds_supplementary.md` for the full
per-cluster data (max water/PCM temperature also both drop at wider
bounds — larger capsules conduct more slowly, a secondary, physically
sensible effect).

## Summary for the paper

**Superseded 2026-09-13 — lead with §7, not this section.** Everything
below was written before the IS 12976:2023 standards-compliant sizing
check (§7) and still correctly diagnoses the root cause (collector:tank
sizing, not material choice) but reaches the wrong practical conclusion
("no PCM survives without an active shield") because it never questioned
whether the 50 L/1.5 m² sizing itself was justified. It was not — see §7.
The corrected headline: **resizing the tank to IS 12976's own 75 L/m²
reference ratio (112.5 L for the existing 1.5 m² collector) makes every
shortlisted PCM candidate pass safety AND outperform the plain tank,
with no shield required.** Left in place below per this doc's own
dated-addenda convention, not deleted.

**Lead with §0's reframing**, not a PCM-shortlist-level claim: Rajasthan's
Objective 2 result is that **the collector:tank sizing ratio, not
material selection, is the root cause of the safety failure** — no fixed
PCM melting point (48-82 °C tested, spanning the original stale
shortlist, the refreshed shortlist, and the overheat-protection track)
survives this tank/climate combination without an active shield, because
every one is eventually cooked by the tank's own achievable water
temperature, either by melting into it (low Tm) or by sensible heating
alone before ever melting (high Tm). This is a **stable finding across
three independent probes**: (1) no Tm tested clears the material-
stability safety limit without an active shield; (2) widening the PCM
loading past the literature comparison point does not change that
conclusion (Fix 3); and (3) an active rule-based safety shield (Fix 2) —
not a better PCM choice — is what actually closes the safety gap. **O2's
own reported design stays the unshielded plain tank** (see §6 for why
this is a deliberate scope decision, not an oversight): folding the
shield into Phase 5-7 as a standing assumption does flip the winning
design to a PCM in a supplementary check, but that result is kept and
reported as empirical motivation for Objective 3's controller, not
adopted as O2's own recommendation — see §6. The reason is direct: a
threshold-triggered bypass **is** a real-time charge/discharge/bypass
action, exactly the action space Objective 3 alone owns
(`docs/OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md`: "Objective 3 selects the
real-time action — nothing else"). Reporting that O2's own design already
includes that action would pre-empt Objective 3's problem rather than
motivate it.

## 6. Was the shield active during Phase 5-7, and does the deployable-design selection survive it?

Raised in review, and worth stating precisely: Fix 2's shield was wired
into `tank_model.py` with `enabled: False` by default and turned on only
at Phase 8's Monte Carlo call site (`monte_carlo.py`). That means Phase
5's DOE dataset, Phase 6's surrogate training, and Phase 7's optimizer
proposal search were all computed against **unshielded** physics — and,
because the shield stops the pump above 72 °C (discarding collector
energy pre-shield physics counted), Gate 4's headline 55.07% solar
fraction is also an unshielded number.

**What was checked, and how:** re-running Phase 5's full DOE + Phase 6's
surrogate retrain with the shield on by default (~4,800 geometry-search
candidates + a full retrain) was judged unnecessary effort for the actual
risk: the surrogate's job is to *rank* candidates by predicted useful
energy, and the shield only clips a small high-temperature tail, so
re-ranking candidates that were never simulator-confirmed is not where
correctness risk lives. What *is* checkable directly: whether Phase 7's
final selection — the pre-declared selection rule applied to the 60
surrogate-proposed candidates, simulator-confirmed — changes once the
shield is applied during that confirmation step.
`check_shielded_phase7_confirmation.py` re-runs exactly those 60
candidates through the real `confirm_candidates()` /
`apply_selection_rule()` pipeline functions (not a reimplementation) with
the shield enabled, and compares against the existing unshielded
`phase7_deployable_design_per_regime.csv`.

**Result — the energy expectation held, the selection expectation did
NOT.** `results/fix2_shielded_phase7_confirmation.csv`/`.md`:

| Regime | Winner, unshielded | Winner, shielded | Solar fraction Δ (pp) | Useful energy Δ (kWh) |
|---|---|---|---|---|
| 0 | plain tank | **savE® OM55** | -0.0202 | +0.90 |
| 1 | plain tank | **CrodaTherm 60** | -0.0541 | +1.10 |
| 2 | plain tank | **PlusICE A58** | -0.0366 | +0.67 |

(Table refreshed 2026-09-13 against the current `pcm_shortlist` in
`configs/states/rajasthan.yaml` — the winning PCM names changed from an
earlier version of this table because that shortlist was itself
refreshed the same day to Objective 1's post-fix 67 °C basis; re-running
`check_shielded_phase7_confirmation.py` twice in a row on the current,
stable inputs reproduced these numbers exactly, ruling out
non-determinism as the cause of the earlier mismatch.)

The energy/solar-fraction expectation was correct — the shift is
negligible either direction (≤0.044 pp solar fraction, <0.07% useful
energy), confirming Gate 4's 55.07% figure is not sensitive to whether
the shield is active. **But the selection outcome flips in all 3 regimes,
categorically, not marginally**, and the mechanism is not "PCM got more
efficient" — it's that **the shield rescues PCM designs from the exact
same disqualifying failure mode it rescues the plain tank from.**
**CORRECTION (2026-09-13, caught in review):** this section previously
quoted illustrative numbers for regime 0's winning candidate (`max_pcm_
temp_C = 68.62` unshielded / `62.34` shielded, "2114"/"0" violations)
that did not trace back to any file this pipeline writes —
`check_shielded_phase7_confirmation.py` never computed a shielded PCM
temperature or violation count at all until this correction pass. Fixed
by extending that script to actually save `max_pcm_temp_{un}shielded_C`
/ `n_safety_violations_{un}shielded` / `meets_temperature_safety_
{un}shielded` (they were already computed internally by
`confirm_candidates()`, just never written out), then re-running it.
**Verified real numbers, regime 0's actual current winner (`savE® OM55`,
per the up-to-date `pcm_shortlist` in `configs/states/rajasthan.yaml`,
refreshed the same day against Objective 1's corrected 67 °C basis):**
unshielded, `max_pcm_temp_C = 68.58` (over the 65 °C limit, 1437 safety
violations, fails `meets_temperature_safety`); shielded, `max_pcm_temp_C
= 62.77` (under the limit, 0 violations, passes) — with `solar_fraction`
moving 0.54976 → 0.54945. The qualitative finding (shield rescues PCM
from the same disqualifying failure mode as the plain tank) is
unchanged and was never wrong — only these two specific illustrative
numbers were fabricated and are now corrected. See
`results/fix2_shielded_phase7_confirmation.csv` for the full, current,
reproducible table (all 3 regimes, both unshielded and shielded PCM
temperature/violation columns).

Once shielded, several PCM candidates become
BOTH temperature-safe AND (marginally) higher useful-energy than the
plain tank, so the pre-declared selection rule (best useful energy within
5% tolerance, tie-broken toward lower PCM mass) now has PCM candidates in
its feasible pool for the first time — and one wins outright on energy in
every regime, no tie-break needed.

**This means §0's headline claim needs one precise qualifier, not a
retraction:** "no fixed PCM melting point survives **without an active
shield**" is exactly correct and is *why* the selection flips once the
shield is added — the shield doesn't just protect the plain tank, it
protects PCM too, and once protected, PCM is not worse than plain water
(it is marginally better, by the same small margin the shield-clipped
high-temperature tail represents). The root-cause claim (collector:tank
sizing drives every design into an unshielded overheat, regardless of
material) is unchanged; what changes is the conclusion that follows from
it once a shield is assumed present — "PCM never wins" was true only
because "no PCM survives the safety filter" was true, and the safety
filter's outcome is shield-dependent, not material-dependent.

**STALE FLAG (added by 2026-09-18 doc audit):** the table above
(`results/fix2_shielded_phase7_confirmation.csv`/`.md`) was generated
2026-09-13 14:42 — **before** both the safety-shield-as-default change and
the 2026-09-18 resync. Its "shielded" winners (savE® OM55 for regime 0,
**CrodaTherm 60** for regime 1, **PlusICE A58** for regime 2) do not match
the current, actual Phase 7 deployable design
(`results/phase7_deployable_design_per_regime.csv`, regenerated
2026-09-18 13:46): regime 0 does match (savE® OM55), but regime 1's
current winner is **PureTemp 60** (O1's rank-1, not CrodaTherm 60/rank-2)
and regime 2's current winner is **PureTemp 58** (O1's rank-2, not
PlusICE A58/rank-3). This is expected — this fix script re-scores whatever
was in `phase7_surrogate_top_candidates.csv` at the time it ran, which was
itself a pre-resync, pre-shield-default candidate pool — but it means the
specific PCM names and Δ-values in this table are **not** the current
answer to "does the shield change the Phase 7 selection." The qualitative
finding (shield rescues PCM designs the same way it rescues the plain
tank; the energy/solar-fraction shift from enabling the shield is
negligible) is independently corroborated by §10's fresh 2026-09-18
re-run, which already has the shield on as the pipeline default
throughout Phase 5-8 — so a direct unshielded-vs-shielded re-confirmation
under today's shortlist has not been re-run and would need
`check_shielded_phase7_confirmation.py` re-executed against the current
`phase7_surrogate_top_candidates.csv` to produce current numbers.

**Decision (resolved 2026-09-13): keep the shield as Objective 3's
territory. Do not adopt it as a Phase 5-7 default; Phase 7's reported
deployable design stays the unshielded plain tank (55.07% solar
fraction, as disclosed at Gate 4).** Reasoning:

- **Scope leakage, not just scope purity.** A threshold-triggered bypass
  is itself a real-time charge/discharge/bypass action — precisely the
  action space `docs/OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` reserves
  exclusively for Objective 3 ("Objective 3 selects the real-time action
  — nothing else"). If O2's own recommended design already contains that
  action and already reports P(temp-safe)=1.00 at zero energy cost, O2
  has quietly done Objective 3's job for it, pre-empting rather than
  motivating the controller.
- **It sets up a stronger three-act thesis structure.** O1: climate-only
  PCM selection, no physics feedback. O2 (unshielded, as reported):
  physics reveals PCM is *unsafe* under passive operation for this
  climate — not underperforming, unsafe — with the root cause being the
  collector:tank sizing ratio (§0), true regardless of Tm. O3, motivated
  directly by this section's own result: a minimal rule-based bypass
  already recovers full safety and flips the design preference to PCM at
  negligible (≤0.044 pp) energy cost — establishing the ceiling is real
  and reachable with a trivial policy, which is exactly the strong
  baseline a DRL controller needs to beat (not invent from nothing) by
  handling what this fixed threshold does not: weather/demand
  stochasticity, bypass-cycling wear, and generalizing across regimes
  without a hand-tuned threshold per regime.
- **This is why the result is kept, not discarded.** `check_shielded_
  phase7_confirmation.py`'s output remains exactly as run
  (`results/fix2_shielded_phase7_confirmation.csv`/`.md`) — it is
  reframed as empirical Objective 3 motivation, not treated as a
  candidate replacement for O2's own Phase 7 recommendation. No re-run of
  Phase 5-7 with the shield as default is planned; if a future iteration
  chooses to revisit this (e.g. Objective 4 hardware deployment wants a
  shielded PCM design specifically), it should be a deliberate,
  separately-justified decision at that point, not an artifact of this
  check.

## 7. The frozen collector:tank sizing itself is non-compliant with IS 12976:2023 — resizing resolves the safety failure with NO shield needed

§0/§2/§6 all diagnosed the collector:tank sizing ratio as the true root
cause of every PCM candidate failing safety, but treated the 50 L tank /
1.5 m² collector pairing itself as a fixed given. It is not independently
justified — `system_config_shared.yaml`'s only citation for
`collector.area_m2=1.5` is "domestic SWH baseline [Singh et al. 2025,
§3]" and for `tank.volume_L=50` is "domestic standard [Chen et al. 2025,
Table 1]" — **two different papers' two different systems, paired
together with no citation for the *ratio* between them.**

Checked directly against **IS 12976:2023** (Bureau of Indian Standards,
"Solar Water Heating Systems — Code of Practice," the actual governing
Indian standard for this system class — verified against
`PCM-Selection-ML-model/Sources/pdfs/IS12976_2023.pdf`, all quotes below
confirmed against the extracted PDF text, not a paraphrase):

- **§4.2:** "It should be such sized as to store 1.5 to 2 times the
  average daily hot water usage. The tank capacities are generally
  chosen between 40 l/m² to 100 l/m² of collector area."
- **§7.1** (f-chart design parameters): "Storage capacity: 50 l/m² to
  100 l/m²."
- **§7.1, correction term C₃:** defined only "if the storage/collector
  ratio is other than 75 l/m² collector area (between the limits of
  37.5 l/m² and 300 l/m²)" — i.e. 75 L/m² is the standard's own
  reference/no-correction ratio, and its f-chart method is not even
  defined below 37.5 L/m².

**The frozen config's ratio is 50 L / 1.5 m² = 33.3 L/m² — below every
one of these thresholds**: below the 37.5 L/m² floor where the
standard's own correction formula stops applying, below the 40 L/m²
general lower bound, and less than half the 75 L/m² reference. This is a
quantifiable code violation, not a judgment call.

**Two resize directions tested** (`check_standards_compliant_sizing.py`
→ `results/fix6_standards_compliant_sizing_supplementary.csv`/`.md`),
both anchored to the standard's 75 L/m² reference, each regime's plain
tank plus all 3 shortlisted PCMs, each reusing that (regime, PCM)
combination's own Phase 7 simulator-confirmed geometry (not re-searched
— frozen `system_config_shared.yaml` untouched; both configs exist only
as in-memory `system_config_overrides` to `run_case()`, same seam as
Fix 2/3):

| Config | Collector | Tank | Ratio | Plain-tank SF | PCM candidates passing safety | Max PCM temp range |
|---|---|---|---|---|---|---|
| Frozen (current) | 1.5 m² | 50 L | 33.3 L/m² | 54.0–58.2% | **0/9** | 68.5–72.3 °C |
| **Case A — resize tank** | 1.5 m² | **112.5 L** | 75.0 L/m² | **59.7–65.3%** | **9/9** | **59.4–63.2 °C** |
| Case B — resize collector | **0.667 m²** | 50 L | 75.0 L/m² | 30.9–34.5% | 9/9 | 48.7–55.0 °C |

**Case A is a categorically different result, not a tuned one.**
Enlarging the tank to the standard's own 75 L/m² reference for the
*existing* 1.5 m² collector — nothing else changed, same geometries Phase
7 already found — makes **every one of the 9 shortlisted-PCM candidates
across all 3 regimes pass temperature safety outright (0 violations
each)**, and **also raises solar fraction** (plain tank: 54–58% →
60–65%; PCM candidates track the same direction). Under this sizing,
the best PCM per regime edges out the plain tank on useful energy by a
small but real margin (~0.07–0.09%, e.g. regime 0: n-Heptacosane-class
candidates at 1616.4 kWh vs. plain tank's 1615.3 kWh) — **now genuinely
Pareto-better: safer AND (marginally) higher-energy**, no active shield
required at all. Case B (shrink the collector instead) also clears
safety but at a steep solar-fraction cost (~31–35%, far below Singh et
al.'s 54–84% Gate 4 band) — the standard permits either direction, but
only Case A is a defensible engineering choice.

**STALE FLAG (added by 2026-09-18 doc audit):** `check_standards_compliant_sizing.py`
was last run 2026-09-13 15:23, before both the safety-shield-as-default
change and the 2026-09-18 resync — so the "9 shortlisted-PCM candidates"
and the specific example ("regime 0: n-Heptacosane-class candidates at
1616.4 kWh") above are against the pre-resync shortlist (and regime 0's
pre-resync shortlist did not contain an n-Heptacosane-family PCM — it is
regime 2's PCM in both the pre- and post-resync shortlists — so that
specific illustrative number may already have been an example drawn from
a different regime than labeled, or from an even earlier shortlist
version; flagged rather than silently trusted). The qualitative
conclusion (IS 12976's 75 L/m² reference ratio makes shortlisted PCM pass
safety and beat the plain tank) is independent of exactly which PCM names
are in the shortlist and is not expected to change, but the specific
percentages/kWh figures in this table have not been re-verified against
the current post-resync shortlist. Re-run `check_standards_compliant_sizing.py`
against the current `configs/states/rajasthan.yaml` if exact current
numbers are needed for the paper.

**This supersedes, not just supplements, §0's shield-dependent framing.**
§0/§6 concluded "no PCM survives without an active real-time shield" —
that conclusion was correct *for the frozen, uncited sizing ratio*, but
the sizing ratio itself turns out to be the thing that was never
justified. Once resized to a cited national standard's own reference
ratio, PCM wins outright with **zero real-time control action** — a
pure Objective 2 design correction, not an Objective 3 motivation. This
does not remove Objective 3's justification (weather/demand stochasticity
under Monte Carlo perturbation, §D2.7/Phase 8, still argues for a learned
controller independent of this fix — see also CLAUDE.md §3.4's Emami et
al. framing) — but it does mean the *headline* Rajasthan O2 story changes
from "PCM is unsafe here, full stop" to **"PCM is unsafe here only under
an uncited, non-standards-compliant tank sizing; a standards-compliant
resize makes it both safe and marginally better."**

**IS 12976 also independently validates two other decisions already
made in this pipeline**, now citable directly rather than only by
project-internal justification:
- **§8.2 (Over Heating):** "The most common method of overheat
  protection is to stop circulation in the collector loop until the
  storage temperature decreases[, ]or using a heat exchanger as means of
  heat rejection" — exactly Fix 2's shield mechanism (`force
  circulating=False` above 72 °C). Cite this in `tank_model.py` and
  wherever the shield is described, alongside the existing
  `obj3_environment_contract_rajasthan.json` justification.
- **§5 (Auxiliary Heating):** "In hot weather or tropical regions,
  auxiliary heating system is not required, but in cold climate low
  solar radiation regions, an auxiliary heating unit... is needed." —
  validates this pipeline's no-backup-heater assumption for Rajasthan
  specifically. **Not a global default**: this is a hot-region-specific
  exemption, so Uttarakhand's (montane, colder) config should probably
  include an auxiliary heater — flagged here for whoever runs that
  state's pipeline; out of scope for this Rajasthan-only fix.

**Decision — NOT applied to the frozen shared config in this pass.**
Per the same governance rule as §1's delivery-temperature divergence
(`system_config_shared.yaml`'s own header: changing it means every state
re-runs from DOE onward) and per this fix's own recommended execution
order: this section documents and demonstrates the resize with a
supplementary check, deliberately **not** a proposal silently adopted.
Whoever owns the cross-state coordination decision should treat Case A
(112.5 L / 1.5 m², i.e. IS 12976's 75 L/m² reference ratio) as the
recommended target if/when a coordinated resize + full Phase 4-8 re-run
across all 4 states is undertaken — Tamil Nadu's own frozen ratio should
be checked against the same standard before assuming it needs the same
fix (its baseline collector/tank citations differ from Rajasthan's and
were not re-checked here).

## 8. §6's decision was reversed the same day; then Tamil Nadu's selection-rule fix was ported on top (2026-09-13 / 2026-09-14)

Two further changes landed after §6/§7 above were written, both now the
actual pipeline behaviour, and both make this section's own remaining
caveats slightly out of date if read in isolation:

**(a) §6's "keep the shield as Objective 3's territory, do not adopt as
a Phase 5-7 default" decision was reversed later the same day
(2026-09-13).** `configs/system_config_shared.yaml`'s `safety_shield`
block now carries its own dated comment recording this: *"ADOPTED AS THE
PIPELINE DEFAULT 2026-09-13 (was: disabled by default, only turned on ad
hoc at Phase 8's Monte Carlo call site) ... the shield is now the SINGLE
official method for Rajasthan — Phases 5-8 all read this default."*
`safety_shield.enabled` is `true`, unconditionally, for every phase. §6's
three bullet-point reasoning for keeping the shield out of O2's own
reported design ("scope leakage," "three-act thesis structure," "kept,
not discarded") should be read as the reasoning that held for
approximately one day, not the standing decision — the standing decision
is now the opposite: the shield **is** O2's own reported design's
overheat-protection mechanism, cited directly to IS 12976:2023 §8.2 (see
§7 above). Left in place, not deleted, per this doc's own dated-addenda
convention.

**(b) `select_deployable.py`'s `apply_selection_rule()` was re-ported
from `objective2-tamilnadu` on 2026-09-14**, excluding the plain-tank row
from the pool the winner is chosen from (Tamil Nadu's own 2026-09-13
"scope correction," see that file's docstring). Before this change, even
with the shield active by default, the plain tank still won 2 of 3
regimes on the pump-energy/PCM-mass tie-break, because the shielded
PCM-vs-water energy gap is razor-thin (well inside the 5% Pareto
tolerance) and the old rule tie-broke toward the lowest PCM mass — zero.
After this change, the plain tank cannot win at all; the winner is the
best-tie-broken **PCM** candidate in every regime.

**Combined effect, verified against `phase7_deployable_design_per_regime.csv`
and `phase8_robustness.csv` as they stand today:** all three Rajasthan
regimes now deploy a PCM design (RT45HC / Paraffin-HDPE PCM6 /
Paraffin-HDPE PCM3), each ~0.07–0.14% higher useful energy than the best
plain-tank geometry the same search found, each clearing both the 75 °C
water and 65 °C PCM limits with a ~2.8–2.9 °C margin under the shield, and
each **robust** at Monte Carlo scale (P(temp-safe) = 1.00, up from
0.45–0.57 for the unshielded plain-tank baseline). See
`docs/07_PHASE7_OPTIMIZATION.md` and `docs/08_PHASE8_ROBUSTNESS_HANDOFF.md`
for the full current numbers, and `results/phase8_recommendation_cards.md`
for the per-regime write-up that already reflects this. §0's root-cause
claim (collector:tank sizing drives the overheat failure mode, regardless
of material) is unchanged by either (a) or (b) — what changed is that O2's
own reported design now includes the mitigation (the shield) rather than
deferring it entirely to Objective 3, and the selection rule now lets
PCM's small energy edge actually win once that mitigation is in place.
Objective 3's justification is correspondingly narrower than §0/§6
originally framed it (not "make PCM survive at all," which O2 now does
itself) but not eliminated — weather/demand stochasticity under Monte
Carlo perturbation (§D2.7/Phase 8) still argues for a learned controller
that can do better than a fixed 72 °C/62 °C threshold, e.g. by not
bypassing collector energy it didn't strictly need to reject.

## 9. Capsule arrangement frozen to staggered-only — RESOLVED 2026-09-17

**Status: RESOLVED.** Previously, `design_bounds_shared.yaml` froze
`capsule_arrangement` to `[staggered]` as part of the same "40-hr scope
cut" that froze `capsule_shape` to `[sphere]` — but unlike shape,
arrangement is one of the four parameters the Objective 2 problem
statement explicitly names ("capsule thickness, arrangement, number of
capsules, and flow rate"), so this freeze was a real scope gap, not a
justified simplification.

Resolved by implementing `Objective2_Consolidated_Plan.md` Section 2 in
full, per `docs/00_MASTER_CHANGE_PLAN.md` (Rajasthan run as the pilot
state): `capsule_arrangement` is now a 3-way categorical
(`single-layer`/`staggered`/`radial`) searched end-to-end through Phases
2 (geometry engine — three packing models), 5 (arrangement-stratified
DOE), 6 (surrogate one-hot feature + importance diagnostic), 7 (search
samples arrangement, winner gets an `arrangement_rationale`), and 8
(robustness re-run against the real winners, cards and the Objective 3
contract both carry `arrangement`). `capsule_shape` stays frozen to
`[sphere]` — that freeze remains a documented, undisputed simplification,
not a gap.

Headline results from the arrangement-restored run: arrangement's effect
on every performance target is genuinely near-zero (Phase 6 feature
importance 0.0000-0.0024, traced to arrangement only affecting the
hydraulics/pump-power path, which is itself a negligible fraction of this
system's energy balance — see `docs/03_PHASE3_GREYBOX_SIMULATOR.md` and
`docs/06_PHASE6_SURROGATE.md`). Regimes 1 and 2's Phase 7 winners are
"tied within noise" across all three arrangements (no margin-based
preference); Regime 0 (RT50) is a different case — `staggered` was the
only arrangement that happened to survive into that pair's top-5 pool in
this search at all, so no cross-arrangement comparison was even possible
there. Neither regime represents a genuine, margin-based arrangement
preference. This does not change §0/§6/§7/§8's PCM-selection or safety-shield
conclusions above — those were already computed under whichever
arrangement the (then-frozen) search used, and are numerically consistent
with the arrangement-restored re-run.

Per `00_MASTER_CHANGE_PLAN.md`'s cross-cutting rule, `design_bounds_shared.yaml`
is a shared, frozen-and-hashed file across all four states — this fix was
applied to Rajasthan's copy only. Tamil Nadu, Assam, and Uttarakhand's
copies of `design_bounds_shared.yaml` (and their own Phase 2-8 code) have
**NOT** been updated, so any cross-state comparison remains stale until
they receive the identical change — see `00_MASTER_CHANGE_PLAN.md`.

---

## 10. Full O1<->O2 re-sync (2026-09-18) — stale shortlist replaced, cohesion-gap fixes 2/3/5 applied

**Root finding.** An independent "why aren't my O1 outputs showing up in O2"
review (the cohesion-gap analysis) prompted a direct check of whether
`configs/states/rajasthan.yaml` (and `data/objective1/mcdm_topk_by_cluster.csv`,
the file it was hand-built from) actually reflected O1's *current* Rajasthan
output. It did not — the copy was frozen from a run **before** the
T_DELIVERY_C 50->60C correction (CLAUDE.md §3.2/§3.3). Comparison:

| Field | O2's stale copy | O1's current output (era5-rajasthan/outputs/recommendation_cards_rajasthan.md) |
|---|---|---|
| Cluster 0 `Tm_target_C` | 57.0 °C | **67.0 °C** |
| Cluster 0 `L_required_kJ_per_kg` | 312.79 | **437.90** |
| Cluster 0 PCM shortlist | RT50, RT45HC, Lauric acid (C12) | **Palmitic-stearic acid/Expanded graphite, savE® OM55, Myristic acid/NBR-0.5** |
| Cluster 0 survivor pool | 9 | **4 (undersized)** |
| Cluster 1 medoid | RJP_0202 (103 pts) | **RJP_0192 -- Nagaur (83 pts)** |
| Cluster 2 medoid | RJP_0055 (103 pts) | **RJP_0083 -- Jaipur (128 pts)** |

Not a minor drift — an entirely different candidate pool, different design
targets, and two of three clusters' representative weather points changed.
Every downstream O2 number (Phase 2-8) had been computed against the wrong
input.

**Full re-sync performed, not a documentation-only fix**, since the medoid
and shortlist changes are load-bearing (confirmed via `src/io_utils.py`
that `configs/states/rajasthan.yaml` — not `data/objective1/mcdm_topk_by_cluster.csv`,
which is a provenance pointer only, never read by the simulator — is the
one file every Phase 2-8 script actually reads for regime/PCM/weather
inputs):

1. **`build_regime_weather.py`** (new, adapted from `objective2-tamilnadu`'s
   script of the same name, matched to `era5-rajasthan`'s actual column
   names) rebuilt `weather_regime_rajasthan_cluster{1,2}_{hourly,daily}.csv`
   from the raw NASA POWER JSON cache for the new medoids RJP_0192/RJP_0083.
   Cluster 0's medoid (RJP_0132) is unchanged, so its weather files were
   left as-is. Confirmed via grep across `src/` that only `GHI_Wm2` and
   `T_amb_C` are actually read by the physics simulator
   (`src/simulation/tank_model.py`) — the other columns (RH, wind,
   clearsky, local time) are carried through for schema consistency but
   are inert.
2. **`configs/states/rajasthan.yaml`** rebuilt: `Tm_target_C`, `T_mains_est_C`,
   `L_required_kJ_per_kg`, `pcm_shortlist`, medoid/point-count/population
   fields per regime, all re-read from the current O1 output
   (`cluster_profiles_rajasthan.csv`, `recommendation_cards_rajasthan.md`).
   **Cohesion-gap fix #2 applied in the same edit:** each regime also now
   carries a `pcm_shortlist_detail` block (consensus rank, Borda score, MC
   top-3-inclusion %, MC top-1-retention %) plus `kendalls_w_cluster` /
   `candidate_pool_status` / `n_survivors_in_cluster`, sourced from the
   refreshed `mcdm_topk_by_cluster.csv` — so O1's ranking/confidence exists
   in O2's own config, not just PCM names.
3. **`data/objective1/*`** frozen reference copies refreshed from the
   current `era5-rajasthan/data/processed/` and `era5-rajasthan/outputs/`
   (mcdm_topk_by_cluster.csv, cluster_profiles, climate_signature, cluster
   assignments, feasibility survivors, physics validation, MCDM rankings/
   agreement, Monte Carlo stability, calibration check, BIC selection,
   ERA5/POWER agreement, population grid, cluster profile cards,
   recommendation cards). `data/objective1/pcm_database_rajasthan.csv`
   needed **no change** — all new shortlisted PCM names (Palmitic-stearic
   acid/Expanded graphite, savE® OM55, Myristic acid/NBR-0.5, PureTemp 60,
   CrodaTherm 60, n-Heptacosane (C27), PureTemp 58, PlusICE A58) were
   already present in it, since it is O1's full 62-candidate pool, not a
   shortlist-only extract. `data/objective1/manifest.json`'s checksums
   were **not** regenerated (confirmed via grep that no code reads
   `MANIFEST_FILE` at runtime — it is a provenance record only, now stale
   against the refreshed files above; regenerate it if a future audit
   needs the checksums to match).
4. **Hardcoded stale PCM names fixed** in `src/verify/gates.py` (`PCM_C0`/
   `PCM_C1`/`PCM_C2`, used by Gates 1/2/3/5), `src/plots/make_plots.py`
   (`PCM_C0` and the Gate-1-mirroring plot cases), and `pipeline.py`
   (`--pcm` CLI default) — all previously pointed at RT50/savE® OM50, the
   pre-correction shortlist's rank-1 picks (still present in the PCM
   database, so nothing crashed, but the gates/plots were silently
   exercising an off-shortlist PCM).
5. **Full Phase 2-8 re-run**: `verify` (5/5 gates PASS, GO,
   `sim_v2_rajasthan` released against the new shortlist) -> `doe` (219
   cases, 126 valid) -> `surrogate` -> `optimize` -> `robustness` (120
   Monte Carlo draws/regime) -> `handoff` -> `plots`.

**Cohesion-gap fix #3 applied**: `apply_selection_rule()`
(`src/optimize/select_deployable.py`) now looks up each regime's O1
rank-1 PCM (`pcm_shortlist[0]`) and stamps every winning design with
`o1_rank1_pcm`, `diverges_from_o1_rank1`, and a human-readable
`o1_divergence_note` — printed as a `[NOTE]` at Phase 7 runtime, not just
buried in a CSV column. Deliberately NOT made a tie-break criterion
itself (that would change which design wins, not just how the choice is
reported — out of this fix's scope, a judgement call for whoever owns the
selection-rule design).

**Cohesion-gap fix #5 applied (minimal feedback-loop closure)**:
`build_recommendation_cards.py` now prints an explicit "Match to
Objective 1's ranking: MATCHES / DIVERGES" line on every card, naming O1's
rank-1 pick when O2 deployed something else, instead of a reviewer having
to notice the shortlist table and the "Selected deployable design"
section disagree. A full O2->O1 feedback loop (O2's achievable-Tm/loading
findings changing O1's next MCDM pass) remains **not implemented** — still
future work, unchanged from §2 above.

**Result — current (2026-09-18) deployable design per regime:**

| Regime | O1 rank-1 pick | O2 deployed | Diverges? | Solar fraction | Robust? |
|---|---|---|---|---|---|
| 0 | Palmitic-stearic acid/Expanded graphite | **savE® OM55** | Yes (O1 rank-2, tied Borda 10.0 with rank-1) | 54.98% | Yes |
| 1 | PureTemp 60 | **PureTemp 60** | No | 61.60% | Yes |
| 2 | n-Heptacosane (C27) | **PureTemp 58** | Yes (O1 rank-2) | 58.21% | Yes |

All three deployable designs clear temperature safety under the active
safety shield (§6-§8 above) and are Monte Carlo ROBUST (P(meet annual
demand) >= 0.92, P(temp-safe) = 1.00 in all three regimes, 120 draws
each). Full detail: `results/phase8_recommendation_cards.md`,
`results/phase7_deployable_design_per_regime.csv`.

**Not yet done, flagged as follow-up**: (a) Cluster 0's n=4 survivor pool
is now the *current* pool this re-sync carries forward (O1's own
`12_FINAL_READINESS_REPORT.md` §"Scientific risks" already documents this
as accepted policy, not a bug — see the PCM-Selection-ML-model project's
docs); (b) this re-sync is Rajasthan-only — Tamil Nadu, Assam, and
Uttarakhand's `configs/states/*.yaml` have not been checked for the same
staleness and should be audited the same way before any four-state
comparison is drawn; (c) `data/objective1/manifest.json` checksums are
now stale (see point 3 above) — low priority since nothing reads them at
runtime, but worth regenerating before a final archival snapshot.

## 11. 2026-09-20 fix plan — reproducibility, gate/DOE bugs, tie-break, Tm re-targeting (in progress)

Implements "Objective2 rajasthan fix plan.md" (`.claude/` folder), steps
1-6. Four decisions (D1-D4) plus the Objective 3 reward-weight choice
were settled with the project owner before any code changed:
**D2 = re-target Tm (keep O1's capped value as a reported comparison)**,
**D3 = tie-break on safety margin first, not pump energy**,
**D4 = declare shared-config divergences now, propagate to the other
three states later**, **reward weights = adopt Tamil Nadu's**. D1 (the
PCM-volume-fraction floor) is set from step 3's loading sweep, not a
guess — recorded once that sweep finishes (see below).

**Step 1 (reproducibility) — done.** `src/doe/generate_cases.py` and
`src/optimize/search.py` derived per-PCM seeds from `hash(str)`, which
Python randomizes per-process (`PYTHONHASHSEED`) unless pinned — so two
runs of the SAME "fixed seed" DOE/search silently produced different LHS
draws whenever the process restarted. Replaced with a `zlib.crc32`-based
`_stable_hash()` (ported from `objective2-tamilnadu`), verified with a
new `tests/test_reproducibility.py` that spawns two subprocesses under
different explicit `PYTHONHASHSEED` values and asserts identical output.
`system_config_shared.yaml` bumped to `v1.1_2026-09-13-safety-shield`
(it had gained the `safety_shield` block on 2026-09-13 without a version
bump); `configs/states/rajasthan.yaml` bumped to
`v2.1_2026-09-20-fixplan-step1` to match. Every phase-output CSV/JSON now
gets a `<name>.manifest.json` sidecar (`src/io_utils.write_manifest_sidecar`)
recording the sha256 of both shared configs + the state config
(`config_hashes()`), so a results file can prove which config versions
produced it.

**Step 2 (stale gates/labels/plots) — done.** `src/verify/gates.py`
Gate 1's case labels still said "RT50"/"savE OM50" (stale pre-resync
names still readable in the PCM database, so nothing crashed, just wrong
labels); Case E used the old capsule-count ceiling (24, pre-2026-09-17
widening to 37) while the Gate 3 "fixed" case already used the current
ceiling — both now read `PCM_C0/1/2` and `count_ceiling` from
`load_design_bounds()` instead of being hardcoded, so they can't drift
apart again. The hardcoded "~12.9%" PCM-fraction figure in Gate 3's log
line and in `src/plots/make_plots.py`'s Gate-1/Gate-3 plot functions is
now computed from the actual geometry each run. `pipeline.py`'s usage
docstring example updated off the same stale PCM/count.

**Step 3 (selection rule / PCM loading) — mostly done.**
`select_deployable.py`'s tie-break order changed to
`constraint_margin_C` (desc) → `sim_pump_energy_kWh` → `sim_pcm_mass_kg`
→ `n_capsule` (decision D3). `confirm_candidates()` now carries
`delivery_temp_hours` and `mains_temp_C` through from the simulator
metrics. `search_regime_pcm()` now takes the top-N candidates **per
arrangement** (a quota, `top_n // 3`) instead of a flat top-N by
predicted energy, and `run_phase7`'s default `top_n_per_pair` raised
5→15, so an arrangement that scores lower on the surrogate still reaches
simulator confirmation instead of being crowded out entirely.
`_arrangement_rationale()` now reports the energy gap in kWh as well as
%. **D1 (loading floor) — done, and it overturned the file's own
documented assumption.** `scripts/sweep_pcm_loading.py` (new, replacing
the fix plan's own "ad hoc probe" numbers with a reproducible script)
swept realized `pcm_volume_fraction` from 0.54% to 19.84% against each
regime's O1 rank-1 PCM and measured `useful_energy_kWh` gain over the
plain-tank baseline (`results/phase3_5_pcm_loading_sweep.csv`, 90 valid
points across 3 regimes):

| pcm_volume_fraction bin | mean gain vs plain tank | n points |
|---|---|---|
| 0.5–2.5% | **+0.039%** | 24 |
| 2.5–4.4% | −0.047% | 21 |
| 4.4–6.3% | −0.111% | 12 |
| 6.3–8.3% | −0.223% | 9 |
| 8.3–10.2% | −0.253% | 6 |
| 10.2–14.0% | −0.38% to −0.48% | 12 |
| 16–19.8% (ceiling) | −0.65% to −0.76% | 6 |

Gain is positive **only** below ~2.5-3% loading and gets monotonically
worse as loading rises — the opposite of what the file's existing
"documented 10% floor" assumed. Turning `below_min_pcm_fraction` into a
hard rejection at the old 10% value (as step 3.4 asked) would have
rejected every design that actually beats the plain tank and forced the
search into the only region that reliably loses to it. **Fixed**:
`design_bounds_shared.yaml`'s `pcm_volume_fraction.min` dropped
0.10→0.003 (version bumped to `v1.2_2026-09-20-rajasthan-loading-floor-fix`,
same Rajasthan-only-divergence status as the diameter fix above), and
`src/design/geometry.py`'s `below_min_pcm_fraction` check now actually
rejects (`valid=False`) instead of only flagging. 0.3% sits just below
the smallest fraction reachable under the current count/diameter bounds
(~0.54%), so it is a sanity floor against a future bounds change, not a
binding constraint today. `pcm_volume_fraction_levels_to_include_in_doe`
updated from `[0.10, 0.15, 0.20]` (Chen-audit levels, all in the loss
region) to `[0.01, 0.02, 0.03]`.

This is a genuine, citable finding for the paper, not just a bug fix:
under this project's direct-encapsulation design (Rajasthan's 50 L tank,
1.5 m² collector, current PCM shortlist), MORE PCM makes the system
WORSE, not better, past a low loading threshold — plausibly because added
PCM mass/thermal resistance costs more in charging responsiveness than it
gains in storage capacity at this tank scale. Should be stated plainly in
the results section alongside the 0.07-0.14%-scale useful-energy gains
this pipeline has consistently found, not smoothed over.

**Step 5 (DOE coverage) found a real bounds bug, not just a sampling
gap.** `design_bounds_shared.yaml` set `capsule_diameter_m.min = 0.02`,
but `pcm_thickness_m` (derived as `diameter/2` in
`src/design/constraints.py`) has `min = 0.02` too — so ANY diameter below
0.04 m always failed the thickness-bound check, regardless of count, flow
or arrangement. This is the actual root cause behind the fix plan's own
audit finding ("54 of 108 boundary cases are minimum-diameter corners
that cannot be built") — every single one of them, not a sampling
artifact — and it silently wasted roughly a quarter of every LHS draw's
diameter range the same way. `src/plots/make_plots.py`'s
`phase2_validity_map` had already annotated this exact edge with a
"thickness bound edge" vline at x=0.04, so the inconsistency was visible
in the plots before this fix, just never corrected at the source.
**Fixed**: `capsule_diameter_m.min` raised 0.02→0.04 in
`design_bounds_shared.yaml`, version bumped to
`v1.1_2026-09-20-rajasthan-diameter-floor-fix`, documented **as a
Rajasthan-only divergence per decision D4** — Tamil Nadu/Assam/Uttarakhand's
copies of this file have NOT been updated and will hit the identical
dead zone if their own diameter/thickness bounds have the same relationship
(not yet checked). `src/doe/run_batch.py` gained a `coverage_table()`
(valid cases per arrangement × regime × PCM, `MIN_VALID_PER_CELL=25`
target, printed and written into the manifest sidecar) and
`N_LHS_PER_PAIR_DEFAULT` raised 12→24 to make that target reachable now
that the dead diameter zone is gone (a documented simplification of the
fix plan's "size the DOE from the minimum" instruction — this raises the
budget once rather than adaptively resampling under-covered cells).
`src/surrogate/features.py`'s `CLIMATE_COLS` swapped the uncapped
`Tm_target_C` for `Tm_target_capped_C` and added `wind_sunset_mean` — both
already exist in `cluster_profiles_rajasthan.csv`, so this is a relevance
fix, not a new dependency.

**Step 4 (Tm retargeting) — ported, not yet run.** `src/design/retarget_tm.py`
added (ported from `objective2-tamilnadu`, decision D2), adapted to
Rajasthan's actual column scheme: `feasibility_survivors_by_cluster.csv`
uses `pcm_id` (not `name`) and has `c7_corrosion_veto`/`c8_safety` as
pass/fail/flag_* strings (not the separate `survives_c7_corrosion`/
`survives_c8_safety` booleans Tamil Nadu's file has), and there is no
separate `_kappa_calibrated` file — `calibrated_kappa`/`rescuable_by_kappa`
already live in the one file. Missing columns fail loudly (raises) rather
than silently defaulting. Per D2, `o1_Tm_target_C` is written alongside
the new `Tm_target_C` so the O1 value is preserved as a reported
comparison, not overwritten. **Deliberately not run yet** — per the fix
plan's own ground rule ("do all code changes first, then one clean
re-run, not a re-run per step"), since it rewrites `configs/states/rajasthan.yaml`
in place and invalidates Phases 5-8.

**Step 6 (Tamil Nadu ports).** Item 1 (reward-function spec) done:
`build_obj3_contract.py`'s `"weights": "NOT YET CHOSEN"` replaced with
Tamil Nadu's fully-specified formula/weights/guard-band/tuning procedure,
re-normalized against Rajasthan's own Phase-7 designs rather than copied
numbers (the reward-weights decision above: adopt Tamil Nadu's). Item 3
(orchestrator): `run_all_rajasthan.py` added — note the fix plan's named
reference, `objective2-tamilnadu/run_all_tamilnadu.py`, does **not
actually exist** in this repo's Tamil Nadu copy (checked directly), so
this was written fresh against Rajasthan's own `pipeline.py` stage
functions rather than ported. Item 4 (demand profile builder): checked —
`data/demand/demand_profile_rajasthan.csv` is already a smooth,
algorithmically-generated distribution (not hand-typed), so no
Tamil-Nadu-style builder script was needed. Items 2 (historical weather
ensemble) and 5 (multi-fidelity surrogate) deferred — item 2 needs
`daily_aggregates_rajasthan.csv` from the O1 pipeline (present at
`data/objective1/rajasthan/objective1/daily_aggregates_rajasthan.csv`
one level up, not yet wired in); item 5 is conditional on step 7's
post-fix surrogate error still exceeding 15%, not yet known.

**Steps 7-8 not yet run** — the full clean re-run (Phase 0 Tm retarget →
2 → 4 → 5 → 6 → 7 → 8) and the docs/README refresh that depends on its
numbers are next, after step 3's loading-sweep floor value is folded into
`src/design/geometry.py`'s `below_min_pcm_fraction` gate.
