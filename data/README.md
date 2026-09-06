# Objective 2 — Input Data Reference

Data for all four states lives under `data/objective1/<state>/`. Each state has its own
README describing exactly what that folder contains, how it was built, and what's still
missing:

- [`objective1/rajasthan/README.md`](objective1/rajasthan/README.md) — **complete.**
  Full Objective-1 freeze, 10-year hourly weather, demand profile, MCDM rankings.
- [`objective1/tamil_nadu/README.md`](objective1/tamil_nadu/README.md) — **mostly
  complete.** Climate signature, clustering, feasibility, per-regime weather and demand
  are all present; the wide MCDM-rankings table (`mcdm_rankings_tamilnadu.csv`) is still
  owed upstream, though the Top-3 tables already exist.
- [`objective1/assam/README.md`](objective1/assam/README.md) — **not started.** Only the
  shared PCM property sheet is frozen so far.
- [`objective1/uttarakhand/README.md`](objective1/uttarakhand/README.md) — **not
  started.** Only the shared PCM property sheet is frozen so far.

## Shared conventions across all four states

- All three build scripts (`build_input_package.py`, `build_regime_weather.py`,
  `build_demand_profile.py`) read their paths from [config.py](../config.py). To build a
  different state, edit only the `EDIT FOR YOUR STATE` block there (`STATE`,
  `OBJ1_FOLDER_NAME`, `POINT_ID_PREFIX`) — every filename follows automatically.
- Nothing under `data/objective1/` is edited by hand. Re-run the scripts and diff each
  state's `manifest.json` / `MANIFEST.json` instead.
- Naming follows the team convention: `{content}_{state}.csv`, lowercase, no spaces;
  per-cluster files add `_cluster{k}`.
- `pcm_properties.csv` is the one file byte-identical across all four state folders —
  it's the raw manufacturer sheet, present even in the two not-yet-started states.

See each state's own README for its file-by-file table, folder layout, weather/demand
details, and caveats.
