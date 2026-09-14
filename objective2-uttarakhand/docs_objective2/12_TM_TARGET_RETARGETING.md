# 12 — Tm_target_C Retargeting (Objective 2 methodology revision, 2026-09-14)

**Status: APPLIED to `configs/states/uttarakhand.yaml`. Phases 2–8 fully re-run against it, together with the design-bounds widening (doc 13) and the selection-rule scope correction — see `08_PHASE7_OPTIMIZATION.md` and `10_PHASE8_ROBUSTNESS_HANDOFF.md` for final, current numbers.**

Ported from `objective2-tamilnadu/src/design/retarget_tm.py` (2026-09-12), which found and fixed the same mismatch there. This is a deliberate, documented methodology revision — not a silent edit. It changes *which PCM melting point Objective 2 selects for*, replacing Objective 1's climate/delivery-anchored `Tm_target_C` with a value derived from this tank's own simulated behavior.

## Why

Objective 1 set `Tm_target_C = 57.0°C` for every regime, from `04b_climate_signature.py`'s climate/delivery formula (`SHARE_PCM=0.5` of a 300 L draw heated from mains to 50°C). That number was never checked against what temperature the *tank in this specific Objective 2 design* actually reaches on a normal day.

Two independent pieces of evidence, both already on record before this change, showed the mismatch:

1. **Phase 4, Gate 3** (`04_PHASE4_VERIFICATION_GATES.md`) — a synthetic diagnostic PCM with `Tm=40°C` beat the plain tank (39.25% vs 39.01% solar fraction), proving the simulator *can* show a PCM benefit when the melting point is right. But the real shortlisted PCM (PureTemp 58 / n-Octacosane, `Tm≈58°C`, from the old 57°C-anchored formula) did *not* clearly beat plain tank.
2. **Phase 7's first 400-candidate search** (pre-retargeting, post scope-correction only) confirmed the real shortlisted PCMs' own body temperature exceeded the 65°C PCM safety limit in 4 of 5 regimes at nominal conditions — the tank's real charging-hour water temperature sits well below the old 57°C target, so a PCM tuned to 57°C rarely melted at the right time and, when it did track water temperature, tracked it right past the safety limit on hot days.

## Method (`src/design/retarget_tm.py`)

For each regime, one **reference plain-tank design** is run through the full-year simulator — `capsule_diameter_m=0.05, n_capsule=16, flow_rate_kg_s=0.030`, the exact midpoint of `design_bounds_shared.yaml`'s (pre-widening) bounds, chosen once and identically for all 5 regimes so no regime's target is cherry-picked toward any particular PCM. The new `Tm_target_C` is the **median water temperature during hours the collector is actually delivering heat** (`Q_collector_Wh > 0`) — the temperature a PCM must melt at on a *typical* charging day, not just the sunniest ones, to actually cycle every year.

PCM re-selection reuses Objective 1's own `feasibility_survivors_by_cluster.csv` (latent heat / cycling / supercooling / corrosion pass flags — unchanged, these don't depend on `Tm_target`), recomputes each candidate's melting-window pass/fail against the new target using the *same* `[target-5, target+8] °C` window Objective 1's file itself uses, and ranks window survivors by `|Tm_C - new_target|` (closest first) — a simpler, explicitly-documented substitute for Objective 1's full MCDM consensus, not a re-implementation of it. Top 3 per regime become the new `pcm_shortlist`.

**Schema adaptation for Uttarakhand**: Tamil Nadu's Objective 1 pipeline exposes a `pass_safety` column that Uttarakhand's `feasibility_survivors_by_cluster.csv` does not have (a later Tamil-Nadu-only Objective 1 refinement). The ported script was adjusted to use whichever of `pass_latent_heat`/`pass_cycling`/`pass_supercooling`/`pass_corrosion`/`pass_safety` actually exist in the state's own feasibility file, so it works correctly against Uttarakhand's real schema rather than assuming Tamil Nadu's.

## Result: before → after

| Cluster | Label | Old Tm_target | New Tm_target | Old shortlist | New shortlist |
|---|---|---|---|---|---|
| 0 | 7 pts, Ta_mean~22.6°C | 57.0°C | **40.8°C** | PureTemp 58; n-Octacosane (C28); PlusICE A58 | RT42; RT44HC; savE® OM42 |
| 1 | 3 pts — small sample, Ta_mean~9.4°C | 57.0°C | **27.8°C** | PureTemp 53; n-Hexacosane (C26); Myristic acid (C14) | **NONE survived the new window — old shortlist retained as fallback** |
| 2 | 9 pts, Ta_mean~19.0°C | 57.0°C | **38.7°C** | PureTemp 58; savE® OM55; n-Hexacosane (C26) | RT42; RT44HC; savE® OM42 |
| 3 | 10 pts, Ta_mean~23.8°C | 57.0°C | **42.1°C** | PureTemp 58; savE® OM55; Palmitic-stearic/graphite | RT44HC; RT42; savE® OM42 |
| 4 | 16 pts, Ta_mean~18.5°C | 57.0°C | **38.4°C** | PureTemp 58; n-Octacosane (C28); PlusICE A58 | RT42; RT44HC; savE® OM42 |

Full before/after evidence table (including new shortlist Tm and latent heat per candidate): `results/uttarakhand/tm_retargeting_report.csv`.

Every new target is 14.9–29.2°C below the old 57°C, and 4 of 5 new shortlists shift entirely into the RT42/RT44HC/savE® OM42 range (Tm 40.5–44.0°C) — a materially different, and much better-matched, candidate pool than Objective 1's own MCDM consensus.

## The regime 1 exception: no PCM in the database matches the coldest regime's real operating range

Regime 1 is genuinely coldest (median charging-hour water temperature only **27.8°C**), and after recomputing the melting window (`[22.8, 35.8]°C`) against every other feasibility criterion, **zero PCM candidates in `pcm_database_uttarakhand.csv` survive** — the database's coverage simply has a gap between the low-temperature end (nothing below ~40°C passes every other feasibility flag) and this regime's actual target. Per the ported script's documented fallback behavior, regime 1's **old** shortlist (PureTemp 53, n-Hexacosane (C26), Myristic acid (C14) — all Tm 53–58°C) is retained rather than leaving the regime with no PCM at all. This is reported explicitly here, not hidden: regime 1's selected PCM (Myristic acid (C14), Tm=53°C) is therefore mismatched to its own regime's real ~28°C operating temperature in the same way the *other* regimes' *old* shortlists were — the retargeting fix could not be applied to regime 1 for lack of a suitable candidate in the current PCM database.

Despite this mismatch, regime 1's selected design still passes temperature safety with the *largest* margin of any regime (+11.9°C) — precisely *because* it's so badly undersized for the tank's cold operating range that it rarely reaches its own high melting point in the first place, so it behaves closer to inert sensible mass than an actively-cycling (and therefore potentially overheating) PCM. See `08_PHASE7_OPTIMIZATION.md`.

## What re-ran after this change

Per the framework's Phase 0 gate, changing `Tm_target_C`/`pcm_shortlist` requires re-running Phases 2–8. All of the following were re-run together with the design-bounds widening (doc 13) and the selection-rule scope correction:

| Phase | Re-run? |
|---|---|
| 2 — Geometry self-test | ✓ |
| 4 — Verification gates | ✓ (Gate 3 now shows a clean, real PCM win — see `04_PHASE4_VERIFICATION_GATES.md`) |
| 5 — DOE | ✓ 142 valid / 73 rejected (see `06_PHASE5_DOE.md`) |
| 6 — Surrogate | ✓ |
| 7 — Optimize | ✓ |
| 8 — Robustness + hand-off | ✓ |
| Plots | ✓ |

Nothing on disk describes the pre-retargeting state anymore; every results file reflects this revision.
