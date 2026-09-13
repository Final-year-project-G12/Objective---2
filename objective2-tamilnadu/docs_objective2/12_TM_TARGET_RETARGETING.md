# 12 — Tm_target_C Retargeting (Objective 2 methodology revision, 2026-09-12)

**Status: APPLIED to `configs/states/tamilnadu.yaml`. Phases 5–8 fully re-run against it, together with the design-bounds widening (doc 13) and the selection-rule scope correction (doc 14) — see `RESULTS.md` for final, current numbers. The "What has and hasn't been re-run" and "Headline finding" sections below are kept as a historical record of the intermediate (retargeted-only, pre-widening, pre-scope-correction) state; they are superseded by docs 13 and 14.**

This is a deliberate, documented methodology revision — not a silent edit. It changes *which PCM melting point Objective 2 selects for*, replacing Objective 1's climate/delivery-anchored `Tm_target_C` with a value derived from this tank's own simulated behavior.

## Why

Objective 1 set `Tm_target_C = 57.0°C` for every regime, from `04b_climate_signature.py`'s climate/delivery formula (`SHARE_PCM=0.5` of a 300 L draw heated from mains to 50°C). That number was never checked against what temperature the *tank in this specific Objective 2 design* actually reaches on a normal day.

Two independent pieces of evidence, both already on record before this change, showed the mismatch:

1. **Phase 4, Gate 3** (`docs_objective2/04_PHASE4_VERIFICATION_GATES.md`) — a synthetic diagnostic PCM with `Tm=40°C` beat the plain tank decisively (55.19% vs 52.26% solar fraction), proving the simulator *can* show a PCM benefit when the melting point is right. But the real shortlisted PCM (n-Octacosane, `Tm=61.6°C`, from the old 57°C-anchored formula) did *not* beat plain tank (51.16% vs 52.26%).
2. **Phase 7's full 400-candidate search** (pre-retargeting; see `RESULTS.md`'s original Phase 7 table) confirmed this generalizes: every regime's original shortlist — all PCMs in the 56.5–64°C range — lost to plain tank by at most ~0.08%, in 4 of 5 regimes outright.

Both point at the same root cause: this tank's real charging-hour water temperature sits well below the old 57°C target in every regime, so a PCM tuned to 57°C almost never actually melts and freezes — it just sits there as dead mass.

## Method (`src/design/retarget_tm.py`)

For each regime, one **reference plain-tank design** is run through the full-year simulator — `capsule_diameter_m=0.05, n_capsule=16, flow_rate_kg_s=0.030`, the exact midpoint of `design_bounds_shared.yaml`'s bounds, chosen once and identically for all 5 regimes so no regime's target is cherry-picked toward any particular PCM. The new `Tm_target_C` is the **median water temperature during hours the collector is actually delivering heat** (`Q_collector_Wh > 0`) — the temperature a PCM must melt at on a *typical* charging day, not just the sunniest ones, to actually cycle every year. This is the physical requirement the old climate/delivery formula never checked directly.

PCM re-selection reuses Objective 1's own `feasibility_survivors_by_cluster.csv` (latent heat / cycling / supercooling / corrosion / safety pass flags are unchanged — they don't depend on `Tm_target`), recomputes each candidate's melting-window pass/fail against the new target using the *same* `[target-5, target+8] °C` window Objective 1's file itself uses, and ranks window survivors by `|Tm_C - new_target|` (closest first) — a simpler, explicitly-documented substitute for Objective 1's full 4-method MCDM consensus, not a re-implementation of it. Top 3 per regime become the new `pcm_shortlist`.

An additional check not present in Objective 1's feasibility flags: candidates must also have all five properties the simulator itself needs (`TC_W_mK`, `density_liquid_kg_m3`, `density_solid_kg_m3`, `Cp_liquid_kJ_kgK`, `Cp_solid_kJ_kgK`) non-null in the full PCM database. A handful of literature-only entries (e.g. "C22H46 (docosane-class paraffin)") pass every feasibility flag on Tm/latent-heat alone but were never simulatable — previously irrelevant because their Tm sat outside the old 52–65°C window, but retargeting to a lower window can bring them into range on melting point alone, so this must be checked explicitly here.

## Result: before → after

| Cluster | Label | Old Tm_target | New Tm_target | Old shortlist | New shortlist |
|---|---|---|---|---|---|
| 0 | coastal/high-humidity (8 pts) | 57.0°C | **48.9°C** | n-Octacosane (C28); n-Hexacosane (C26); PureTemp 58 | savE® OM49; n-Tricosane (C23); n-Tetracosane (C24) |
| 1 | interior plains (42 pts) | 57.0°C | **49.5°C** | n-Octacosane (C28); RT64HC; n-Hexacosane (C26) | n-Tricosane (C23); n-Tetracosane (C24); n-Pentacosane (C25) |
| 2 | coastal belt (39 pts) | 57.0°C | **50.4°C** | n-Octacosane (C28); PureTemp 58; n-Hexacosane (C26) | savE® OM49; PlusICE A52; n-Tetracosane (C24) |
| 3 | semi-arid interior (22 pts) | 57.0°C | **51.5°C** | n-Octacosane (C28); PureTemp 58; n-Hexacosane (C26) | n-Tetracosane (C24); PlusICE A52; PureTemp 53 |
| 4 | high-humidity / highest HSI (22 pts) | 57.0°C | **46.5°C** | n-Octacosane (C28); RT64HC; n-Hexacosane (C26) | n-Tricosane (C23); RT45HC; n-Docosane (C22) |

Full before/after evidence table (including new shortlist Tm and latent heat per candidate): `results/tamilnadu/tm_retargeting_report.csv`.

Every new target is 6.5–10.5°C below the old 57°C, and the new shortlists shift entirely into the C22–C25 paraffin / OM49 / PlusICE A52 / PureTemp 53 range — a materially different candidate pool from Objective 1's own MCDM consensus (which was n-Octacosane/RT64HC/PureTemp 58/n-Hexacosane-dominated, all in the 56.5–64°C band). **This is the headline consequence of the revision**: Objective 1's Top-3 PCM per regime, reported throughout the Objective 1 documentation and the original (pre-retargeting) `RESULTS.md`, is no longer what Objective 2 is evaluating for Tamil Nadu.

## What has and hasn't been re-run (as of 2026-09-12)

Per the framework's Phase 0 gate (`O2_Unified_PerState_Execution_Framework.md`), changing `Tm_target_C`/`pcm_shortlist` requires re-running Phases 3–8. Status:

| Phase | Re-run against new targets? | Notes |
|---|---|---|
| 5 — DOE | ✓ Yes | `results/tamilnadu/design_cases.csv` regenerated after this change |
| 6 — Surrogate | ✓ Yes | `results/tamilnadu/surrogate_metrics.csv`, `surrogate/models.pkl` regenerated after this change |
| 7 — Optimize | ✓ Yes | `results/tamilnadu/optimized_designs.csv`, `deployable_design_per_regime.csv` regenerated after this change — **but see below, this run used the OLD (pre-widening) `capsule_count` bound** |
| 8 — Robustness + hand-off | ✗ **No** | `results/tamilnadu/robustness_results.csv`, `recommendation_cards.md`, `obj3_environment_contract_tamilnadu.json` and the Phase 8 plots still reflect the **pre-retargeting** (`Tm_target=57`, n-Octacosane-era) run. Do not quote Phase 8 numbers from the current `RESULTS.md` as current until this is re-run. |

Additionally, **`configs/design_bounds_shared.yaml` was widened (`capsule_count.max` 24→37) after Phase 7's re-run above** — see `docs_objective2/13_DESIGN_BOUNDS_WIDENING.md`. That means even the Phase 5–7 numbers currently on disk do not yet reflect the widened design space. **Phases 5–8 all need one more full re-run** before any number downstream of this revision (including a corrected Phase 7/8 section of `RESULTS.md`) can be called final.

## Literature

- **[Rathore2024]** and **[AlMamun2023]** corroborate the general
  principle behind this revision: PCM benefit in a solar-thermal tank
  depends on the melting point actually matching the tank's realized
  operating-temperature distribution, not merely on a climate/delivery
  sizing calculation.
- **[Yan2025]** independently supports using melt/liquid-fraction
  behavior (this doc's "median water temperature during charging hours"
  criterion) as the physically meaningful quantity to target, rather
  than an indirect proxy.
- **[Rubitherm2024]** / **[PLUSS2024]** are the datasheet sources for the
  new shortlist candidates' `Tm_C` values (n-Tetracosane, n-Tricosane,
  PlusICE A52, PureTemp 53, etc.) in `pcm_database_tamilnadu.csv`.

## Headline finding from the retargeted Phase 7 run (already on disk)

Even with melting points now matched to the tank's real operating range, **every regime's deployable design selection still picked the plain tank (`NONE_plain_tank`)** in the post-retargeting, pre-widening `deployable_design_per_regime.csv` — regime 4 (previously the one regime where n-Octacosane won) now has a 15-candidate pool and still selects plain tank. This needs re-confirming after the design-bounds-widening re-run before being reported as a stable conclusion, but on the evidence currently on disk, retargeting alone did **not** flip the "PCM barely helps" finding from the original `RESULTS.md` — it may instead be reinforcing it. Do not present this as final until the Phase 5–8 re-run against the widened bounds (see doc 13) completes.
