# 04 — Phase 4 Audit: Simulator Verification Gates (Rajasthan)

File: `src/verify/gates.py`. Output: `results/phase4_simulator_verification_report.txt`.

No Phase 5 DOE row may be generated until this passes (framework doc §5).
Reduced 5-gate battery per `O2_Unified_PerState_Execution_Framework.md`.
Run with `python pipeline.py --state rajasthan --stage verify`.

> **Ported from `objective2-tamilnadu/src/verify/gates.py`**, then made
> **arrangement-aware on 2026-09-17** when capsule arrangement was restored
> as a searched variable (`Objective2 Consolidated plan.md` §0.1, §4). Gate
> logic, thresholds, and the verdict rule are unchanged from Tamil Nadu;
> what changed is which *test inputs* each gate exercises:
> - Rajasthan has **3** Level-A clusters (0,1,2), not TN's 5.
> - PCM names, in `src/verify/gates.py`'s `PCM_C0`/`PCM_C1`/`PCM_C2`
>   constants, are Rajasthan's Objective 1 shortlist **as of the
>   2026-09-18 resync**: `Palmitic-stearic acid/Expanded graphite`
>   (cluster 0 rank-1), `PureTemp 60` (cluster 1 rank-1), `n-Heptacosane
>   (C27)` (cluster 2 rank-1) — updated from the pre-resync `RT50`/
>   `savE® OM50` picks (`gates.py`'s own comment flags this: those old
>   names are still present in `pcm_database_rajasthan.csv` but are no
>   longer O1's current rank-1 per cluster). **Caveat:** the individual
>   Gate 1 case *labels* in `gates.py` (e.g. `"A: cluster0 / RT50 / mid
>   design"`) are leftover pre-resync text — the case still actually runs
>   the current `PCM_C0`/`PCM_C1`/`PCM_C2`, only the string label is
>   stale; this doc's Gate 1 table below reproduces those labels verbatim
>   from the live report for traceability.
> - Gate 1 runs **7** cases (was 5): the original 5 (all staggered) plus a
>   cluster1/savE-OM50/single-layer and a cluster2/savE-OM50/radial case.
> - Gate 2's "capsules removed (N=0)" case runs **once per arrangement**
>   (3 checks, was 1). "Oversized diameter for tank" per arrangement is
>   covered by Phase 2's `run_boundary_self_test()` 24-case matrix instead
>   of being duplicated here (same `check_design()` code path).
> - Gate 3's baseline table reports `fixed_PCM_max_feasible` **once per
>   arrangement** at the shared count ceiling (n=37, d=0.08 m) instead of
>   one pooled row.
> - Gate 4 states explicitly which arrangement produced the
>   optimized-looking design used for the benchmark comparison.
> - The simulator is tagged `sim_v2_rajasthan` (bumped from
>   `sim_v1_rajasthan` — physics unchanged, but the geometry module it
>   depends on changed). This tag is hard-coded into `src/doe/run_batch.py`,
>   `src/handoff/build_obj3_contract.py`, and
>   `src/handoff/build_recommendation_cards.py`, so no Phase 5+ code path
>   can default back to `sim_v1_rajasthan`.
> - One **informational, non-gating** Gate 2 line records Cluster 0's
>   plain-tank overheating (see `docs/00_MASTER_OVERVIEW.md`).
> - Report path follows this repo's flat `results/phaseN_*` scheme rather
>   than TN's `results/<state>/` subdirectory.

## Gate 1 — Energy conservation: **PASS**

7 diverse cases (all 3 clusters, 2 PCMs, a no-PCM baseline, a
bounds-extreme design, and one single-layer + one radial case), each a
full simulated year:

| Case | Residual (% of E_collector) |
|---|---|
| A: cluster0 / RT50 / mid design (staggered) | 0.000324% |
| B: cluster1 / savE® OM50 / small-capsule design (staggered) | 0.000283% |
| C: cluster2 / savE® OM50 / large-capsule design (staggered) | 0.000287% |
| D: cluster2 / no-PCM plain-tank baseline (staggered) | 0.000204% |
| E: cluster0 / RT50 / bounds-extreme design (staggered) | 0.000362% |
| F: cluster1 / savE® OM50 / single-layer | 0.000283% |
| G: cluster2 / savE® OM50 / radial | 0.000287% |

(Case labels are the literal, pre-resync text `gates.py` still prints —
see the module-note caveat above; the PCM actually simulated in every
case is the current `PCM_C0`/`PCM_C1`/`PCM_C2`.)

Mean 0.000290%, max 0.000362% — both far inside the 0.1% pass threshold
(and ~1,300× inside the 0.5% hard-stop). Cases F and G match their
staggered counterparts (B and C) exactly — expected, since arrangement
only affects hydraulics/pump-power, never energy accounting (see
`03_PHASE3_GREYBOX_SIMULATOR.md`). Both Phase-3-documented bug fixes
(reverse-collector-flow accounting, adaptive-substepping stiffness) are
intact in this Rajasthan run.

## Gate 2 — Limiting cases: **PASS (12/12)**

| Case | Result |
|---|---|
| Zero irradiance | E_collector = 0 exactly |
| Zero flow | Completes, residual ≈ 0.0003%, no crash |
| No PCM | E_charge = E_discharge = 0 |
| Zero latent heat | Completes; f_melt degenerates to a step function (expected — L=0 makes the melt band a point) |
| Very high PCM conductivity (×200) | Mean \|T_w−T_pcm\| gap SMALLER than nominal (0.147 °C vs 0.605 °C) — correct direction, no divergence after the stiffness fix |
| Perfectly insulated tank | E_loss = 0 exactly |
| Empty demand | E_load = E_unmet = 0 |
| Fully solid initial PCM | f₀ = 0.000 → f₂₄ = 0.000 (stays solid; no sun yet at hour 0 in this weather trace) |
| Fully liquid initial PCM | f₀ = 1.000 → f₂₄ = 0.000 (fully discharges within the first day — small PCM mass, plausible) |
| Flow below/above [0.010, 0.050] permitted range | Completes at 0.002 and 0.20 kg/s; higher flow narrows the T_w−T_pcm gap (0.833 °C → 0.548 °C) — correct direction |
| Capsules removed (N=0), single-layer | E_charge = 0 |
| Capsules removed (N=0), staggered | E_charge = 0 |
| Capsules removed (N=0), radial | E_charge = 0 |

All 12/12 gating checks pass. Every expected direction was written into
the test code *before* running it (see `gate2_limiting_cases`).

**Informational, non-gating:**
- `rajasthan_cluster0_plain_tank_overheat` — Cluster 0's **plain-tank**
  (no PCM at all) water temperature reaches **68.6 °C**, above the frozen
  65 °C PCM material-stability limit, on solar input alone. This is
  recorded so the safety-limit violations seen in the Phase 3 smoke runs
  are unambiguously attributed to Rajasthan Cluster 0's hot-dry /
  high-clearness collector input against the frozen 50 L tank / 1.5 m²
  collector sizing — **not** a capsule-sizing or arrangement choice.
- `oversized_diameter_for_tank` per arrangement — covered by
  `run_boundary_self_test()`'s 24-case matrix (`02_PHASE2_GEOMETRY_CONSTRAINTS.md`),
  not re-run here to avoid asserting the same code path twice.

Neither line changes a gate verdict.

## Gate 3 — Baseline comparison: **PASS**

| Design | Useful energy | Solar fraction | Unmet energy | Pump energy |
|---|---|---|---|---|
| Plain tank (no PCM) | 1584.8 kWh | 55.00% | 1138.4 kWh | 0.0001 Wh |
| Fixed PCM, Palmitic-stearic acid/Expanded graphite, max feasible fraction (n=37, d=0.08 m), single-layer | 1575.0 kWh | 54.67% | 1146.8 kWh | 0.0006 Wh |
| Fixed PCM, Palmitic-stearic acid/Expanded graphite, max feasible fraction (n=37, d=0.08 m), staggered | 1575.0 kWh | 54.67% | 1146.8 kWh | 0.0013 Wh |
| Fixed PCM, Palmitic-stearic acid/Expanded graphite, max feasible fraction (n=37, d=0.08 m), radial | 1575.0 kWh | 54.67% | 1146.8 kWh | 0.0003 Wh |
| "Optimized-looking" (n=19, d=0.08 m, flow=0.040 kg/s, staggered) | 1579.9 kWh | 54.85% | 1142.2 kWh | 0.0007 Wh |

**`PCM_C0` = Palmitic-stearic acid/Expanded graphite (Objective 1's
current rank-1 pick for Cluster 0, `Tm = 55.2 °C`) does NOT beat the
plain tank** at this 50 L / max-feasible-fraction design — solar fraction
54.67% vs the plain tank's 55.00%, unmet energy 1146.8 kWh vs 1138.4 kWh,
for all three arrangements. This is the live, current report's own
"HONEST FINDING": at this tank size and PCM fraction the PCM's mean
liquid fraction stays low (rarely reaches its 55.2 °C melting point for
long), so it mostly displaces sensible-storage water without activating
as latent storage — motivating Phase 5–7's search for a larger PCM
fraction, better-matched melting point, or larger tank/collector, rather
than assuming the O1 climate-ranked PCM is automatically effective in
hardware. **This supersedes an earlier version of this doc**, which
(pre-resync, using the old rank-1 pick `RT50`, `Tm = 48 °C`) reported
this PCM beating the plain tank; the current O1 rank-1 PCM's higher
`Tm` (55.2 °C vs 48 °C) sits further from this tank's actual operating
range, which is exactly why the result flipped. Whether Tamil Nadu's own
rank-1 PCM still fails the same check is **UNVERIFIED** here — not
re-checked as part of this audit (out of scope: this file covers
Rajasthan only).

All three arrangements land at the same useful energy/solar fraction
(54.67%) to the precision reported — consistent with Phase 6's later
finding that arrangement's effect on performance is near-zero; only
`pump_energy_kWh` differs measurably between them (0.0003–0.0013 Wh),
consistent with arrangement only touching hydraulics.

**Capability check** (synthetic PCM, same geometry/fraction, `Tm = 40 °C`
matched to the tank's operating range): solar fraction 55.72%, mean liquid
fraction 0.416 — a decisive, well-cycling improvement over plain tank,
confirming the simulator rewards a well-matched PCM.

**Ambient-loss diagnostic (Bug-Fix 1, confirms the loss term is active):**
removing `U_tank` entirely raises solar fraction from 54.67% to 56.78% —
i.e. *no-loss ≥ with-loss*, confirming `Q_loss = U_tank·A_tank·(T_w−T_amb)`
is genuinely active in every case.

Gate 3's pass/fail is gated on the capability check **and** the active
loss term, not on whether today's shortlisted PCM happens to win — both
pass (the shortlisted PCM losing to plain tank does not fail Gate 3).

## Gate 4 — Published-benchmark calibration: **PASS**

Cited benchmark band (Singh et al. 2025): 54.0–84.0% solar fraction. The
live report also notes a second calibration reference (Chen et al. 2025:
94.2% storage efficiency / 31.7 h retention on a comparable
configuration) as a calibration reference, not a universal constant.
This simulator's optimized-looking design (**arrangement=staggered**,
d=0.08 m, n=19, flow=0.040 kg/s — see Gate 3): **54.85%** — **inside the
band**.

Unlike Tamil Nadu (51.39%, 2.6 points below the band and reported as a
PASS-WITH-CAVEAT — **UNVERIFIED here**, not re-checked as part of this
audit), Rajasthan's stronger solar resource lands the same 50 L-tank /
300 L-day / no-backup-heater configuration inside the cited range without
any tuning.

## Gate 5 — Sensitivity & monotonicity: **PASS (3/3)**

| Check | Result |
|---|---|
| Latent heat +10% vs −10% | More PCM energy cycled with more latent heat (14.63 vs 13.84 kWh) — correct direction |
| Flow +50% vs −50% | Pump energy higher with higher flow (0.0003 vs 0.0000 Wh) — correct direction |
| Reduced effective tank-loss coefficient (ambient-warming proxy) | Lower E_loss (70.36 vs 77.85 kWh baseline) — correct direction |

**Caveat on the flow check** (inherited from TN, unaffected by
arrangement): at the PCM fractions reachable here, the packed-capsule bed
is sparse enough that Ergun pressure drop — and therefore pump energy —
is numerically tiny at *any* permitted flow rate, so this check is
directionally correct but a weak discriminator.

## Informational — safety-shield confirmation against today's actual Phase 7 winners

Added after `docs/OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` flagged that this
Gate battery had only ever exercised generic baseline/boundary designs,
never the *specific* designs Phase 7 actually selected. Non-gating (same
convention as Gate 2's Cluster-0 line): `gate_shield_confirmation_for_winners()`
reads `results/phase7_deployable_design_per_regime.csv` and re-runs each
of the three current winners through the full shield-enabled physics:

| Winning design | Shield active? | Max water T | Max PCM T | Shield water activations | Shield PCM activations | Safety violations |
|---|---|---|---|---|---|---|
| Regime 0 — RT50 / staggered | Yes | 68.72 °C | 62.10 °C | 0 | 12,201 | 0 |
| Regime 1 — Paraffin/HDPE PCM3 / staggered | Yes | 72.13 °C | 62.27 °C | 214 | 23,085 | 0 |
| Regime 2 — savE® OM50 / radial | Yes | 72.01 °C | 62.58 °C | 1 | 9,401 | 0 |

**3/3 pass, shield genuinely engaging** (thousands of PCM-charge-block
activations per design, plus water-bypass activations in Regimes 1 and 2)
— not merely never needed.

**STALE relative to today's actual Phase 7 winners — flagged, not
silently corrected here.** The PCM names in this table (`RT50`,
`Paraffin/HDPE PCM3`, `savE® OM50`) are exactly what
`results/phase4_simulator_verification_report.txt` prints (re-read
2026-09-18 as part of this audit), but `results/phase7_deployable_
design_per_regime.csv` was regenerated at **13:46:24** — *after* this
Phase 4 report was written at **13:32:00** — and now lists different
PCMs per regime: `savE® OM55` (regime 0), `PureTemp 60` (regime 1),
`PureTemp 58` (regime 2). Since `gate_shield_confirmation_for_winners()`
reads that CSV directly (`src/verify/gates.py`, no hardcoded PCM names in
this function), this is not a code bug — it means the CSV changed after
the last Phase 4 run, not that the gate logic is broken. **Action
needed, not taken as part of this doc-only audit:** re-run `python
pipeline.py --state rajasthan --stage verify` so this informational table
reflects the current Phase 7 winners; until then this table (and its
"today's Phase 7 winners" framing) is out of sync with
`phase7_deployable_design_per_regime.csv`. This does not affect the 5/5
gate verdicts or the Go/No-Go call, since this check is explicitly
non-gating.

## Go/No-Go

Framework rule: residual < 0.5% **and** ≥ 3/5 gates clean.
Result: max residual 0.000362%, **5/5 gates clean** → **GO**.

**Simulator released as `sim_v2_rajasthan`** (bumped from
`sim_v1_rajasthan` on 2026-09-17 when arrangement was restored as a
searched variable — see the module note above). Tagged at commit time so
Phase 5's DOE cases record which simulator version produced them
(framework doc: never mix outputs from two simulator versions in one
training dataset without a version feature).
