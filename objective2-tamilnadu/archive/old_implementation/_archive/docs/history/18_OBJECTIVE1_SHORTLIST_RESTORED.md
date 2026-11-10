# 18 — Objective 1's PCM Shortlist Restored as the Search Space (2026-09-18)

**Status: RESOLVED / APPLIED.** Supersedes the 2026-09-17 "Tm-retargeting"
revision (doc 12) as the mechanism for choosing which PCMs Objective 2
searches. Files touched: `configs/states/tamilnadu.yaml` only — no code
changes were needed (`src/design/retarget_tm.py` and
`src/design/mcdm_reranking.py` still exist and still work correctly; they
are simply no longer invoked as part of the standard Phase 1-8 run).

## What was wrong

Re-reading the project's own formal objective statements exposed a real
scope violation:

> **Objective 1**: "...identifies the **Top-2/Top-3 suitable PCM
> candidates** for different climatic conditions using multi-criteria
> decision-making."
>
> **Objective 2**: "...determine the optimal **PCM thickness, capsule
> arrangement, number of PCM capsules, and flow rate** for maximizing
> thermal energy storage under location-specific climatic conditions."

Objective 1's deliverable is explicitly a *shortlist of candidates* for
Objective 2 to design around. Objective 2's deliverable is explicitly the
four *geometric/flow* variables — nowhere does it say Objective 2 also
re-derives *which material* to use. The 2026-09-17 Tm-retargeting
revision had Objective 2 recompute its own melting-point target from tank
simulation and re-run the MCDM ranking from scratch against that new
target — which is defensible physics (documented in doc 12), but its
practical effect was that **the PCM actually deployed in every regime was
never one of Objective 1's Top-3 candidates**:

| Regime | Objective 1's actual consensus Top-3 | What was deployed under Tm-retargeting |
|---|---|---|
| 0 | RT57HC, n-Hexacosane (C26), PureTemp 58 | n-Hexacosane (C26) *(only this one overlapped)* |
| 1 | RT57HC, n-Hexacosane (C26), n-Pentacosane (C25) | n-Tricosane (C23) *(not in Obj1's Top-3 at all)* |
| 2 | RT57HC, n-Pentacosane (C25), n-Hexacosane (C26) | n-Tetracosane (C24) *(not in Obj1's Top-3 at all)* |

Two of three regimes deployed a PCM Objective 1 never shortlisted. That
is not "Objective 2 optimizing geometry for Objective 1's candidates" —
it is Objective 2 quietly re-doing Objective 1's job with a different
target and a simplified nearest-Tm heuristic for two of the three
regimes' final picks (only regime 0's winner came from the real MCDM
re-rank; the underlying `retarget_tm.py` shortlist that fed the DOE was
itself the simpler nearest-distance substitute — see doc 12's own
disclosure of this).

## What changed

`configs/states/tamilnadu.yaml`'s `Tm_target_C` and `pcm_shortlist` per
regime were restored to Objective 1's actual, unedited output — copied
directly from `cluster_profiles_tamilnadu.csv` (`Tm_target_C = 67.0`, all
regimes) and `mcdm_topk_by_cluster.csv` (consensus-rank order; regime 2
has a genuine tie at rank 2, both candidates kept, giving that regime 3
distinct PCMs same as the others). The pre-restoration file is preserved
at `configs/states/tamilnadu.yaml.bak_pre_obj1_shortlist_restore`.

**Phases 5-8 were re-run** against this restored config (framework doc's
Phase 0 gate: a `pcm_shortlist`/`Tm_target_C` change requires re-running
from Phase 5 onward). **Phases 2-4 were NOT re-run** — they verify the
geometry engine and simulator physics, which are PCM-identity-agnostic;
re-running them would not test anything the restored shortlist affects.

## What this means for the retargeting scripts

`src/design/retarget_tm.py` and `src/design/mcdm_reranking.py` are **not
deleted** — they remain valid, documented tools for a genuinely useful
diagnostic question: *"if Objective 2's own simulator disagrees with
Objective 1's climate-signature-derived melting-point target, what would
a re-optimized target suggest?"* That is legitimate, citable research
insight (Objective 1's target formula is a simplification that has no way
to validate itself against real tank physics). But it is a **diagnostic
finding to report**, not a mechanism for silently substituting Objective
2's own PCM choice for Objective 1's. The evidence these scripts produced
(`results/tamilnadu/tm_retargeting_report.csv`,
`mcdm_reranked_shortlist_report.csv`) is kept and is exactly the kind of
honest, documented finding this project's whole methodology is built
around surfacing — it now lives as a **reported observation about
Objective 1's target formula**, not as Objective 2's actual search space.

## Expected consequence, stated in advance (not hidden after the fact)

Objective 1's actual shortlist PCMs melt at 54-58°C. Objective 2's own
Phase 4 Gate 3 capability check already showed that a PCM in this
temperature range, in this specific 50 L tank, may not clearly beat plain
tank — the tank's real median charging-hour temperature runs well below
this range in every regime (46-53°C, per the retargeting report). **This
re-run may therefore show a weaker headline result than the retargeted
version did** (lower solar fraction improvement, or even a regime where
no Objective-1-shortlisted PCM beats plain tank). That is not a failure of
this change — it is the honest answer to the actual research question the
objective statements pose: *does the climate/MCDM-optimal PCM, once you
optimize its physical design, actually perform best?* If it doesn't, that
is itself a real, reportable finding about the limits of climate-signature-
only PCM screening — precisely the kind of result a four-objective,
physics-validated pipeline is supposed to be able to surface, per Gate 3's
own precedent (doc 04's capability-check framing).

## Results

Phases 5-8 were re-run end-to-end against the restored shortlist
(2026-09-18). Headline: **every regime's deployed PCM is now genuinely one
of Objective 1's actual Top-3 candidates** — including regime 0 getting
Objective 1's literal #1 pick, RT57HC.

**Phase 5 (DOE):** 219 cases run, 107 valid / 112 rejected at the Phase 2
geometry gate (bounds_violation and passage_blocked, same causes as
before — PCM identity doesn't change the geometry feasibility physics).
Train/holdout split: 165/54, 27/30 regime x PCM x arrangement combos with
>=1 holdout case.

**Phase 7 (optimize + confirm):** surrogate proposed 240 top candidates
across 12 regime x PCM pairs (392-411/600 candidates survived the
geometry gate per pair); surrogate-vs-simulator mean error on useful
energy was 0.03% (0/240 candidates over the 15% large-error threshold).
Deployable design per regime:

| Regime | PCM | Arrangement | Useful energy (kWh) | Solar fraction | PCM mass (kg) | vs. plain tank |
|---|---|---|---|---|---|---|
| 0 | RT57HC | radial | 1756.33 | 0.561 | 0.700 | tied within noise (arrangement not decisive; next-best single-layer) |
| 1 | n-Hexacosane (C26) | single-layer | 1623.22 | 0.509 | 0.895 | only arrangement simulator-confirmed for this regime/PCM pool |
| 2 | n-Pentacosane (C25) | single-layer | 1633.98 | 0.534 | 0.406 | tied within noise (arrangement not decisive; next-best radial) |

**Regime 1 caveat:** the selected design (1623.22 kWh) is ~0.05% *below*
plain tank's useful energy (1623.96 kWh) in this run. This is not a bug —
the pre-declared selection rule (reject infeasible -> within 5% tolerance
of best -> safety -> minimize pump energy -> minimize PCM mass -> minimize
capsule count -> constraint margin) is working as documented — but at this
design scale the pump-energy tie-break is deciding between candidates on
differences of order 1e-7 kWh, which is simulator noise, not a real
physical distinction. Many regime-1 candidates are statistically tied on
useful energy, so the tie-break effectively picks among them close to
arbitrarily. Flagged for a decision on whether the tie-break order should
be revisited (e.g. break on useful energy margin before pump energy).

**Phase 8 (Monte Carlo robustness, 120 draws/design):**

| Regime | PCM | P(meets delivery) | P(meets demand) | P(temperature-safe) | Robust? |
|---|---|---|---|---|---|
| 0 | RT57HC | 1.00 | 1.00 | 0.00 | No |
| 1 | n-Hexacosane (C26) | 0.99 | 0.72 | 0.19 | No |
| 2 | n-Pentacosane (C25) | 1.00 | 0.95 | 0.00 | No |

None of the three regimes is robust by the pre-declared robustness
criterion, driven almost entirely by P(temperature-safe): these PCMs melt
at 54-58°C, and under latent-heat/weather/demand uncertainty the tank
frequently exceeds the safety-relevant delivery temperature band. This is
the honest consequence flagged in advance in this doc's "Expected
consequence" section above — it is a real finding about the limits of
climate-signature-only PCM screening when validated against full-system
physics and uncertainty, not a defect in this restoration.

**Bottom line vs. the previous (Tm-retargeted) run:** this run is more
modest — all three regimes beat plain tank only marginally (+0.1%, and
regime 1 actually slightly *below* it before rounding), versus the
previous run's inflated ~59% solar-fraction claims built on PCMs
Objective 1 never shortlisted. That is the expected, correct trade:
Objective 2 is now answering the actual research question ("does the
climate/MCDM-optimal PCM, once optimized physically, perform best?") and
the honest answer this run gives is "only marginally, and not robustly
temperature-safe" — which is itself the reportable finding.
