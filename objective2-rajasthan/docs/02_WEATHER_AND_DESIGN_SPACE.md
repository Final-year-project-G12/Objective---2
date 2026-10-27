# 02 - Weather, year roles and the design space

## 1. Weather inventory (`src/weather/inventory.py`)

- **Points:** the current Objective 1 medoids only: cluster 0 = RJP_0132, cluster 1 = RJP_0192, cluster 2 = RJP_0083
  (`src/weather/inventory.py: CURRENT_MEDOIDS`). The stale `data/objective1/medoid_points_rajasthan.csv` (RJP_0202 / RJP_0055) is not used.
- **Source:** raw NASA POWER JSON under `PCM-Selection-ML-model/era5-rajasthan/data/raw/nasapower/` in the project root, outside this folder (read-only; the SHA-256 of each file is
  recorded in the inventory).
- **Output:** `data/weather/point_years/weather_inventory.csv` (45 rows = 3 points x 2011-2025; 2011-2015 added 2026-10-27) and 45 cleaned hourly files
  `data/weather/point_years/rajasthan/cluster<c>_<point>_<year>.csv`.
- **Acceptance rule:** at least 98 % valid hours; gaps up to 3 h interpolated and flagged; longer gaps reject the point-year and stay listed.
  Result: all 45 accepted, 100 % valid hours, no gaps; 8760 h after the 29 February drop (`tests/test_weather_roles.py` exercises the
  fill and reject paths on synthetic files).
- **Check of the plan's claim:** 2024 and 2025 are the two lowest-GHI years in all three clusters (progress log section 7).

## 2. Year roles (`src/weather/roles.py`)

| Role | Years | Used for |
|---|---|---|
| explore | 2016-2020 | screening, DOE, surrogates, active learning, dense grid, ablations |
| select | 2021-2023 | choosing the final design |
| test (v3) | 2011-2015 | one-shot held-out evaluation, untouched; downloaded 2026-10-27 (`scripts/g19_fetch_test2_weather.py`, NASA POWER, same request as the 2016-2025 data) |
| used_test_v1 | 2024-2025 | the v1 (20 % cap) held-out test, already used; accepted for no purpose by `src/weather/roles.py` |

`load_point_year(state, cluster, point, year, purpose)` refuses a year whose role differs from the stated purpose. Test years also need
`acquire_test_lock(run_id, fingerprint)`, an atomic single-use file `results/held_out_test.lock`. The v1 lock (run id `heldout_96d878ef8f24`, 2024-2025) is archived in `results/v1_cap20/`; the v3 lock is created by
`scripts/g10_test.py --confirm-run-once` on 2011-2015; a second run raises `HeldOutLockError`. This is a guard rail in
the code, not a security boundary, and the lock file must never be deleted to retry (`tests/test_weather_roles.py` checks it names the
run that wrote `g10_heldout_results.csv`).

## 3. Shortlist

Objective 1's MCDM top-3 per cluster as written (`data/objective1/mcdm_topk_by_cluster.csv`, read by `io_utils.get_regime`):

| Cluster | Rank 1 | Rank 2 | Rank 3 |
|---|---|---|---|
| 0 | savE OM55 | Palmitic-stearic acid / Expanded graphite | Myristic acid / NBR-0.5 |
| 1 | PureTemp 60 | CrodaTherm 60 | n-Heptacosane (C27) |
| 2 | n-Heptacosane (C27) | PureTemp 58 | PlusICE A58 |

Cluster 0's rank 1 is a tie in O1 (Borda 10 each); both are kept in file order. The retargeted lists of `src/design/retarget_tm.py` are
retired and kept only as a labelled comparison (`SHORTLIST_SOURCE = "retargeted"`).

## 4. Design space (approved 2026-10-26, `configs/design_space.yaml`, read by `src/design/space.py`)

| Variable | Range | Notes |
|---|---|---|
| PCM thickness = sphere inner radius | 10-40 mm, continuous | outer diameter D = 2 (R_in + wall) with wall 0.8 mm; vendor availability below 15 mm not checked |
| PCM amount | outer-volume fraction 2-30 % of the tank (v3; v1 was 2-20 %) | capsule count N is derived (`count_for_fraction`); the cap is administrative, the geometry engine accepts 28-48 % (single-layer 44 %, staggered 48 %, radial 28 % at R 40 mm); a diagnostic run shows it is the one bound that limits the result (`04_RESULTS.md` section 5e) |
| Flow | 0.010-0.050 kg/s | **an optimum at the 0.010 floor is a model artefact** (flow-independent collector F_R) |
| Arrangement | single-layer, staggered, radial | exact packing check in `src/design/geometry.py` |

Constraints: PCM peak at most 65 C in **any** simulated year (otherwise infeasible), water peak at most 75 C, exact geometry.
Model settings: multi-node N = 10, stack anchor centre, dt 150 s. Fixed and not optimised: tank volume, collector area, demand profile,
the O1 shortlist. The legacy `configs/design_bounds_shared.yaml` (8-37 capsules, 40-80 mm diameter) is unchanged and describes the old
pipeline.

## 5. Evidence behind the ranges (G7 sensitivity study, explore years 2018-2019)

- PCM amount: every metric rises monotonically with the fraction over the whole range, so the optimum sits at the cap
  (`results/g7_sensitivity_r{0,1,2}.csv`, progress log section 9B).
- Radius at constant PCM mass: the metrics pull in opposite directions (small radius longer hold, large radius more delivered energy),
  with a disclosed confound (outer volume falls with radius at constant mass).
- Flow: the water-only tank itself depends strongly on flow in the multi-node model; the PCM gain at the same flow is nearly flat.
- Arrangement: a null at a single point (R = 20 mm, 5 %), but about 15 % of the gain variance over the whole space in screening.
