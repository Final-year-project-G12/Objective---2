# 01 — Phase 1 (Tamil Nadu): Objective 1 Data Refresh + Restore Arrangement in Shared Config

> **2026-09-18 update — Section 2 below (Tm-retargeting + MCDM
> re-ranking) is superseded.** Re-reading the project's objective
> statements showed this step caused Objective 2 to deploy PCMs
> Objective 1 never shortlisted (2 of 3 regimes) — a scope violation, not
> a defensible physics improvement. `configs/states/tamilnadu.yaml` was
> restored to Objective 1's own raw `Tm_target_C=67.0` and consensus
> `pcm_shortlist` for **all three regimes** (not the per-regime
> 53.3/46.5/50.3°C retargeted values and re-ranked PCMs shown below).
> `retarget_tm.py`/`mcdm_reranking.py` still exist and still run
> correctly, but are no longer part of the standard Phase 1 pipeline —
> they're kept only as an optional diagnostic. See
> `../18_OBJECTIVE1_SHORTLIST_RESTORED.md` for the full correction, the
> current config values, and why. Section 1 (Objective 1 data refresh)
> and Section 3 (arrangement restoration) below are unaffected.

**Files touched:** `build_input_package.py`, `configs/states/tamilnadu.yaml`,
`configs/design_bounds_shared.yaml`, `src/design/schema.py`,
`src/design/retarget_tm.py`, `src/design/mcdm_reranking.py`.
**Not touched:** `configs/system_config_shared.yaml`, `src/io_utils.py`.
Adapted from `a Rajasthan-pilot change plan (source removed from this project after adaptation, see docs_objective2/tamilnadu_phase_docs/)`.

## Why

Two independent changes land in this phase:

1. **`tamilnadu_pipeline` (Objective 1) was re-run** with updated scripts
   (`04b_climate_signature.py`, `05_cluster_tamilnadu.py`,
   `06_build_pcm_database.py`, `07_feasibility_filter.py`,
   `08_mcdm_ranking.py` all have 2026-09-12–17 timestamps). Its outputs
   moved: K=5→**K=3** regimes, `Tm_target_C` 57.0→**67.0°C**, a real
   elevation field via the new `00c_attach_elevation.py` (was a flat 150 m
   placeholder), and a rewritten feasibility/MCDM pipeline that separates a
   strict feasibility file from a **kappa-calibrated** (rescued) one.
   Objective 2's frozen `data/objective1/` copy was stale relative to this
   and had to be rebuilt, not patched.
2. `design_bounds_shared.yaml` currently freezes shape=sphere **and**
   arrangement=staggered as one combined "40-hr scope cut." Shape freezing
   is correct (never named in the objective statement). Arrangement
   freezing is not — the objective statement names "capsule arrangement" as
   one of the four things the model must determine. This edit un-freezes
   only arrangement.

## What was actually run (Tamil Nadu)

### 1. Objective 1 data refresh

```
# build_input_package.py's SMALL_FILES list was updated first to match the
# refreshed tamilnadu_pipeline output structure (new/renamed files:
# mcdm_full_rankings.csv, mcdm_method_agreement.csv,
# feasibility_survivors_by_cluster_kappa_calibrated.csv,
# cluster_*_levelB.csv, level_b_feature_importance_tamilnadu.csv,
# seasonal_pcm_sensitivity_{topk,summary}.* replacing the old
# level_b_seasonal_{topk,summary}.*) -- see build_input_package.py's own
# SMALL_FILES comment for the full list.
python build_input_package.py      # -> 59 files copied, 0 missing, medoids:
                                     #    cluster0=TNP_0006, cluster1=TNP_0007, cluster2=TNP_0001
python build_regime_weather.py     # -> rebuilt for K=3 (deleted the stale K=5
                                     #    weather_regime_tamilnadu_cluster{0..4}_*.csv first)
```

`configs/states/tamilnadu.yaml` was then **rewritten from scratch** (not
patched) with the fresh 3-regime data: population, medoid point IDs and
elevation, `T_mains_est_C` per medoid (23.97-28.46°C, replacing the old
hand-set 22-30°C state-level guess), `L_required_kJ_per_kg` (406-438 kJ/kg,
up from ~301-326), and `Tm_target_C=67.0` (Objective 1's raw climate-anchored
value, pending Objective 2's own retargeting below).

### 2. Re-run Objective 2's Tm-retargeting + MCDM re-ranking against fresh data

These two scripts (`src/design/retarget_tm.py`, `src/design/mcdm_reranking.py`)
already existed from the pre-refresh methodology revision and are fully
state-agnostic — they needed a schema fix, not a rewrite, because the
refreshed `feasibility_survivors_by_cluster.csv` renamed its per-filter
columns to a `c1`-`c8` string scheme (`"pass"`/`"fail"`/...) and — critically
— **the plain (uncalibrated) feasibility file's strict 0.7x latent-heat
floor now rejects every candidate in every regime**, because
`L_required_kJ_per_kg` rose sharply in the refresh. Both scripts were
switched to read `feasibility_survivors_by_cluster_kappa_calibrated.csv`
instead — the same pool `mcdm_topk_by_cluster.csv` itself is now built from.

```
python -m src.design.retarget_tm tamilnadu
#   regime 0: charging-hour T_water median = 53.3 C
#   regime 1: charging-hour T_water median = 46.5 C
#   regime 2: charging-hour T_water median = 50.3 C
#   -> Tm_target_C rewritten to 53.3 / 46.5 / 50.3 per regime

python -m src.design.mcdm_reranking tamilnadu --apply
#   regime 0: MCDM top-3 = n-Tetracosane (C24), n-Hexacosane (C26), RT57HC
#   regime 1: MCDM top-3 = n-Docosane (C22), RT45HC, n-Tricosane (C23)
#   regime 2: MCDM top-3 = n-Tetracosane (C24), PureTemp 53, n-Hexacosane (C26)
```

### 3. Restore arrangement in the shared design-bounds file

```
In configs/design_bounds_shared.yaml, capsule_arrangement changed from a
plain frozen list ([staggered]) to a categorical bound:

  capsule_arrangement:
    type: categorical
    allowed: [single-layer, staggered, radial]
    default: staggered   # legacy-caller default only

capsule_count.max stays 37 (already widened in an earlier revision, doc 13).
capsule_diameter_m and flow_rate_kg_s unchanged.

In src/design/schema.py, DesignVector's capsule_arrangement field lost its
"staggered" default and became a required, explicitly-passed field (no
default value baked into the dataclass) -- every caller (Phase 2 self-test,
Phase 4 gates, retarget_tm.py's reference design, pipeline.py's CLI) had to
be updated to pass it explicitly. A call site that doesn't pass it is a bug
to fix at that call site, not something to paper over with a default.
```

## What "done" looks like

- `data/objective1/` fully refreshed (59 files), manifest.json regenerated.
- `configs/states/tamilnadu.yaml` reflects K=3 regimes and, **as of
  2026-09-18** (see update note at top), Objective 1's own unedited
  `Tm_target_C=67.0` for all three regimes and its actual consensus
  `pcm_shortlist` per regime — not the retargeted 53.3/46.5/50.3°C values
  or re-ranked PCMs this section originally produced (backups of both
  intermediate states are kept: `.bak_pre_mcdm_rerank` for this step,
  `.bak_pre_obj1_shortlist_restore` for the 2026-09-18 correction).
- `design_bounds_shared.yaml` has a 3-way categorical `arrangement` bound.
- `schema.py`'s `DesignVector` requires `arrangement` with no default.
- `retarget_tm.py`'s module-level `REFERENCE_DESIGN` constant updated to
  pass `capsule_arrangement="staggered"` explicitly (it would otherwise
  crash at import time under the new required-field schema) — the script
  itself still runs correctly, it's just no longer invoked by the standard
  pipeline.

## Exit check before moving to Phase 2

`python -c "from src.io_utils import load_state_config; load_state_config('tamilnadu')"`
runs cleanly. `configs/states/tamilnadu.yaml` shows 3 regimes with
`Tm_target_C`/`pcm_shortlist` values matching Objective 1's own
`cluster_profiles_tamilnadu.csv`/`mcdm_topk_by_cluster.csv` output (not the
old K=5 5-regime file, and not a retargeted/re-ranked substitute).
