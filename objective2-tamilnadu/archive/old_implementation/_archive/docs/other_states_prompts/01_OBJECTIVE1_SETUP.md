# Prompt 1 — Build Objective 1 for {STATE}

Paste this (with `{STATE}` replaced, e.g. `rajasthan`) to start:

---

I want to build Objective 1 (climate clustering + PCM shortlisting) for
{STATE}, following the same real methodology already implemented and
validated for Tamil Nadu in `new_obj/tamilnadu_pipeline/`. Read that
project's scripts (numbered `00_...` through the clustering/MCDM scripts,
`05_cluster_tamilnadu.py` etc.) to understand the real pipeline structure
before writing anything — don't guess at the methodology from the output
file names alone.

**What Objective 1 must produce** (read
`new_obj/objective2_design_optimization/data/objective1/` for Tamil
Nadu's exact file set as the target — Objective 2 consumes these by
file-name pattern `*_tamilnadu.csv`, so {STATE}'s outputs must follow the
same naming convention with `_{STATE}` instead):
- Real weather data for {STATE} (ERA5 and/or NASA POWER — same sources
  Tamil Nadu used, not synthetic data) — geographic bounds need to be
  {STATE}'s actual extent, not Tamil Nadu's.
- A population grid and representative sample points across {STATE}.
- Daily aggregates, a climate "signature" per point (the same
  temperature/humidity/solar-irradiance feature set Tamil Nadu computed).
- GMM clustering into climate regimes — **do not assume K=3 or K=5**; run
  the same BIC-based model-selection step Tamil Nadu used
  (`bic_selection_tamilnadu.csv` is the reference) and let {STATE}'s own
  data pick its own K.
- A PCM database with real property data (reuse Tamil Nadu's
  `pcm_database_tamilnadu.csv` directly if it's not location-specific —
  check whether PCM physical properties were treated as universal or
  Tamil-Nadu-specific before deciding to copy vs. rebuild).
- MCDM ranking (the real multi-method engine, not a placeholder) producing
  a `mcdm_topk_by_cluster.csv` equivalent — Top-2/Top-3 PCM shortlist per
  regime, which is Objective 1's actual deliverable per the project's own
  objective statement.
- `Tm_target_C` per regime, climate-anchored (the pre-retargeting,
  correct value — see `../history/18_OBJECTIVE1_SHORTLIST_RESTORED.md` for why
  this must NOT be re-derived by Objective 2 later).

**Before writing any code**, tell me: (a) what real weather-data sources
and geographic bounds you'll use for {STATE}, (b) whether you're reusing
or rebuilding the PCM database, (c) your plan for validating the
clustering is sensible for {STATE}'s actual climate (Köppen cross-check
or equivalent, same as Tamil Nadu's `koppen_ari`/`koppen_nmi` columns
attempted, even if that validation came back inconclusive for Tamil
Nadu's own K=3 result — still worth attempting here).

This is real, open-ended data-engineering work — don't fabricate
plausible-looking numbers if real data acquisition fails or is rate-limited;
tell me and we'll figure out a fallback together.
