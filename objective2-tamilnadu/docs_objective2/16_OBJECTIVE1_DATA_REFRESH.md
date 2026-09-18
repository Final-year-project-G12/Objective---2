# 16 — Objective 1 Data Refresh (2026-09-17)

**Status: RESOLVED / APPLIED.** This is a summary/index doc — the detailed
per-phase mechanics and results are in
`docs_objective2/tamilnadu_phase_docs/01_PROMPT_PHASE1_CONFIG_TAMILNADU.md`.
Written in the style of docs 12–15 (a focused, single-topic methodology
record), not a duplicate of the phase docs.

## What happened

`tamilnadu_pipeline` (the sibling Objective 1 project, read-only from
Objective 2) was re-run with updated scripts between the 2026-09-14 run
this project's earlier docs (00–15, `RESULTS.md`, the audit report)
describe and 2026-09-17. Objective 2's frozen `data/objective1/` copy was
stale relative to the new outputs and was rebuilt from scratch — not
patched — via updated `build_input_package.py` (its `SMALL_FILES` list now
matches the refreshed pipeline's renamed/new output files) and
`build_regime_weather.py`.

## What actually changed, old → new

| Field | Old (pre-2026-09-17) | New (2026-09-17) |
|---|---|---|
| GMM regime count (K) | 5 | **3** |
| `Tm_target_C` (Objective 1's raw climate-anchored value, pre-Obj2-retargeting) | 57.0°C (all regimes) | 67.0°C (all regimes) |
| Elevation | flat 150 m placeholder (no dedicated script) | **real**, via new `00c_attach_elevation.py` — varies 44–627 m across the 3 medoids |
| `L_required_kJ_per_kg` | ~301–326 | ~406–438 |
| Feasibility engine | single feasibility file, strict latent-heat floor | split into a plain file **and** a kappa-calibrated (rescue) file — the strict floor now rejects every candidate given the higher `L_required`, so the kappa-calibrated pool is the one that must be used downstream |
| MCDM output files | `mcdm_full_scores_by_cluster.csv` | renamed `mcdm_full_rankings.csv`, plus new `mcdm_method_agreement.csv` |
| Level-B seasonal files | `level_b_seasonal_{topk,summary}.*` | renamed `seasonal_pcm_sensitivity_{topk,summary}.*` (script rewritten), plus new Level-B GMM outputs (`cluster_assignments_tamilnadu_levelB.csv`, `level_b_feature_importance_tamilnadu.csv`, etc.) |
| Top-1 PCM (state-wide) | n-Octacosane (C28), Tm=61.6°C | RT57HC, Tm=56.5°C (pre-retargeting); after Objective 2's retargeting + MCDM re-rank, differs per regime |

## Downstream propagation (each documented in its own phase doc)

1. `configs/states/tamilnadu.yaml` rebuilt from scratch (3 regimes, fresh
   medoid/population/mains-temp/elevation data).
2. `src/design/retarget_tm.py` and `src/design/mcdm_reranking.py` — both
   already-existing, state-agnostic scripts — needed one schema fix each
   (new `c1`-`c8` column names, and switching to the kappa-calibrated
   feasibility pool) before they could be re-run against the fresh data.
   Re-running them (not rewriting their methodology) produced the current
   `Tm_target_C` (53.3/46.5/50.3°C) and PCM shortlist per regime.
3. `src/surrogate/features.py` — `monte_carlo_stability.csv` renamed
   `name`→`pcm_id` and `top3_inclusion_probability`→`mc_top3_inclusion_pct`
   (0–100 scale); the confidence-feature join was updated and renormalized.

## Why this doesn't invalidate the intervening methodology docs (12–15)

Docs 12 (Tm retargeting), 13 (bounds widening), 14 (selection-rule scope
correction), and 15 (MCDM reranking + safety tie-break) describe
**methodology**, not frozen numbers — the methodology itself (simulate a
reference design, take the tank's own charging-hour median as the new
target; widen the count bound to reach the documented PCM-volume levels;
select from the PCM-only pool; break ties on temperature safety first) was
re-applied unchanged against the fresh data. Only the *inputs* to that
methodology changed, which is exactly what those docs' own "re-run
required after any Objective 1 change" language anticipated.
