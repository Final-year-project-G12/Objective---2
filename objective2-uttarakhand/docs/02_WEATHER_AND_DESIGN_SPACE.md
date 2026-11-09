# 02 - Weather, year roles and the design space

## 1. Regimes: Objective 1 now has K = 4

Objective 1 reduced Uttarakhand from 5 to 4 regimes (O1 commit 6be0dcd). The frozen O1 copies in `data/objective1/` were refreshed for K = 4
(manifest `data/objective1/manifest.json`; since the cleanup only the five files the pipeline reads are kept there), and
`configs/states/uttarakhand.yaml` was regenerated for 4 regimes. The K = 5 files were removed in the cleanup (git history only).

| Regime | Medoid point (O1 recommendation card) | Points in the regime | Estimated mains C | Tm target C |
|---|---|---|---|---|
| 0 | UKP_0014 | 10 | 21.8 | 57.0 |
| 1 | UKP_0029 | 23 | 18.6 | 57.0 |
| 2 | UKP_0025 | 9 | 17.0 | 56.5 |
| 3 | UKP_0041 | 3 | 7.4 | 55.2 |

The medoid is the card medoid of the O1 script 09_recommendation_cards.py (the member closest to the cluster mean), not the point with the highest
membership probability; the single list is `src/weather/inventory.py: CURRENT_MEDOIDS`.
Regime 3 (the cold, high-altitude regime) has only 3 points, so its weather basis is narrow.

## 2. Weather inventory (`src/weather/inventory.py`)

- **Source:** raw NASA POWER JSON in the Objective 1 folder (`config.py: OBJ1_RAW_POWER_DIR`, read-only; SHA-256 of each file in the inventory).
- **Output:** `data/weather/point_years/weather_inventory.csv` (40 rows = 4 points x 2016-2025) and 40 cleaned hourly files
  `data/weather/point_years/uttarakhand/cluster<c>_<point>_<year>.csv`.
- **Acceptance rule:** at least 98 % valid hours; gaps up to 3 h interpolated and flagged; longer gaps reject the point-year.
  Result: all 40 accepted, 100 % valid hours, no gaps, 8760 h after the 29 February drop.

Annual GHI (kWh/m2) from the inventory:

| Year | Regime 0 | Regime 1 | Regime 2 | Regime 3 |
|---|---|---|---|---|
| 2016-2020 mean (explore) | 1796 | 1767 | 1809 | 1697 |
| 2021-2023 mean (select) | 1785 | 1753 | 1787 | 1651 |
| 2024 (test) | 1763 | 1742 | 1789 | 1652 |
| 2025 (test) | 1729 | 1686 | 1691 | 1608 |

Rajasthan's claim that the two test years are the two lowest-GHI years does **not** hold in Uttarakhand: 2025 is the lowest in regimes 0-2,
but 2023 is the lowest in regime 3, and 2023 is below 2024 in regime 0. What does hold: the mean of the two test years is below the mean of
the other eight years in every regime (`tests/test_weather_roles.py: test_test_years_are_below_average_ghi_in_every_cluster`).

## 3. Year roles (`src/weather/roles.py`)

| Role | Years | Used for |
|---|---|---|
| explore | 2016-2020 | screening, DOE, surrogates, active learning, dense grid, ablations |
| select | 2021-2023 | choosing the final design |
| test | 2024-2025 | one-shot held-out evaluation |

Rajasthan's v3 used 2011-2015 as its test years because its 2024-2025 test was spent in v1. Uttarakhand had no earlier test on the current
chain, so the user chose 2024-2025 (2026-10-28) and no 2011-2015 weather is downloaded. `load_point_year(state, cluster, point, year, purpose)`
refuses a year whose role differs from the stated purpose; test years also need `acquire_test_lock(run_id, fingerprint)`, the single-use file
`results/held_out_test.lock`, created by `scripts/g10_test.py --confirm-run-once` (run id in the lock). The lock file must never be deleted to retry.

## 4. Shortlist

Objective 1's MCDM top-3 per regime as written (`data/objective1/mcdm_topk_by_cluster.csv`, read by `src/io_utils.py: o1_top3`; the
Uttarakhand file names its PCM column `name`, not `pcm_id`):

| Regime | Rank 1 | Rank 2 | Rank 3 |
|---|---|---|---|
| 0 | PureTemp 58 | n-Octacosane (C28) | PlusICE A58 |
| 1 | PureTemp 58 | n-Octacosane (C28) | PlusICE A58 |
| 2 | PureTemp 58 | savE OM55 | n-Hexacosane (C26) |
| 3 | PureTemp 53 | n-Hexacosane (C26) | Myristic acid (C14) |

No rank-1 ties (`tests/test_o1_shortlist.py`).

## 5. Design space (`configs/design_space.yaml`, ported unchanged from Rajasthan v3)

| Variable | Range | Notes |
|---|---|---|
| PCM thickness = sphere inner radius | 10-40 mm | wall 0.8 mm |
| PCM amount | outer-volume fraction 2-30 % of the tank | capsule count N is derived (`count_for_fraction`) |
| Flow | 0.010-0.050 kg/s | **an optimum at the 0.010 floor is a model artefact** (flow-independent collector F_R) |
| Arrangement | single-layer, staggered, radial | exact packing check in `src/design/geometry.py` |

Constraints: PCM peak at most 65 C in **any** simulated year, water peak at most 75 C, exact geometry. Model settings: multi-node N = 10,
stack anchor centre, dt 150 s. Fixed and not optimised: 50 L tank, collector area, demand profile, the O1 shortlist.

## 6. G7 sensitivity (explore years, `results/g7_sensitivity_r{0,1,2,3}.csv`, paired file `results/g7_sensitivity_paired.csv`)

- PCM amount: in regimes 0-2 the window gain rises with the fraction over the range checked; in regime 3 it is flat (PureTemp 53) or falls
  (n-Hexacosane, Myristic acid). Regime 3 has the coldest mains (7.4 C) and the lowest sun of the four regimes.
- Flow: the water-only tank itself depends strongly on flow in the multi-node model; the paired gain is nearly flat.
- PCM peaks at the sensitivity designs were 62.0-67.1 C: 48 of the 568 paired rows exceed the 65 C limit (39 in the thickness block at R 20-30 mm, 9 in the count block).
  G7 only maps responses; the 65 C limit is applied as a feasibility constraint from G8 on.
