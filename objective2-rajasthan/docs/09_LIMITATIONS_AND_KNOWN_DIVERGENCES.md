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

## 1. Objective 1 ↔ Objective 2 delivery-temperature divergence (not resolved, documented instead)

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

**Decision: documented divergence, not silently reconciled.** The two
objectives currently model "the same" domestic hot-water system with a
15 °C disagreement on what temperature it delivers. This affects
`Tm_target_C`, `L_required_kJ_per_kg` (both O1-side) and O2's own
solar-fraction definition (see §3 below) simultaneously. Aligning them
requires a coordinated decision — pick one number and re-run all four
states' Phase 3-8 — that is out of a single-state 40-hr scope. Flagged
here as explicit future work, per the fix doc's own fallback option
("pick one number, or explicitly document why the two objectives
legitimately differ").

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
