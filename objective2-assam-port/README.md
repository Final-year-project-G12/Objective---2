# Objective 2 - Assam (port of the Tamil Nadu pipeline)

Created 2026-11-19 by copying the code of `../objective2-tamilnadu` (src/, scripts/, tests/, run_parallel.ps1, configs/design_space.yaml)
and replacing every input with Assam's. The earlier Assam tree (`../objective2-assam`, phase 0-8 pipeline, one 2025 ERA5 year, no held-out
test) is untouched and its contract is superseded by `results/obj3_environment_contract_assam_v3.json` once this run finishes.

## What is Assam-specific
| Item | Value |
|---|---|
| `config.py` STATE | `assam` |
| Regimes | 3 (Assam O1 K=3 GMM): medoids ASP_0012, ASP_0092, ASP_0028 (`configs/states/assam.yaml`) |
| Weather | NASA POWER hourly, UTC, 2011-2025, 45 point-years, all accepted (`data/weather/point_years/assam`, `weather_inventory.csv`) |
| Year roles (unchanged from Tamil Nadu) | test 2011-15, explore 2016-20, select 2021-23, 2024-25 unused |
| System | 50 L tank, 1.5 m2 collector, 100 L/day (33.3 L/m2, below IS 12976:2023 - a stated limitation). Tamil Nadu is 100 L / 2.5 m2 / 300 L/day |
| PCM shortlist | savE OM48, OM50, OM46 - O1's physics-validated order, NOT an MCDM consensus (O1 has none for Assam) |

## Things to know
* `scripts/a1_fetch_assam_power.py` downloaded 25 of the 45 raw JSONs from NASA POWER (ASP_0012/0028 2011-15, ASP_0092 2011-25); the other 20 were copied from `PCM-Selection-ML-model/era5-assam`.
* ASP_0092 is not one of Objective 1's 80 downloaded POWER points, so it has no sunrise/sunset reference; 2011-2015 also lie outside `suntimes.csv`. Those years are checked only by the clear-sky peak hour (05-06 UTC everywhere = no timestamp shift).
* `tn_rebuild_weather_from_raw.py` geometry check was patched for Assam (sunrise before 00:00 UTC). The point-year files themselves are written by `src/weather/inventory.py`, then `scripts/a2_build_regime_weather.py` builds the regime-level files.
* Tests were adapted where they hard-coded Tamil Nadu (demand shape, 100 L geometry rejections, O1 shortlist/ties, LST provenance).
* NOT ported: the Tamil Nadu narrative documents (`g12_results_doc.py`, `g12_verify_docs.py`), ANSYS/Fluent cases, the OpenFOAM/CFD checks, `objective3/`.
* The held-out test (`g10_test.py`) is one-shot: `results/held_out_test.lock` is created when it runs. Do not rerun it.

Run: `powershell -NoProfile -ExecutionPolicy Bypass -File .\run_parallel.ps1` (waves 1-9; edit `max_parallel.txt` to throttle).
