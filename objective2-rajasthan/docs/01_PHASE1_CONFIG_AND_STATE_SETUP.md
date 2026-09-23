# 01 — Phase 1 Audit: Frozen Configuration & State Setup (Rajasthan)

Files: `configs/system_config_shared.yaml`, `configs/design_bounds_shared.yaml`,
`configs/states/rajasthan.yaml`. Loader: `src/io_utils.py`. Phase 0 sanity
check: `check_climate_signature.py`.

> `system_config_shared.yaml` and `src/io_utils.py` are **byte-identical**
> to `objective2-tamilnadu/`'s copies (verified). `design_bounds_shared.yaml`
> **diverges from Tamil Nadu/Assam/Uttarakhand's copies as of 2026-09-17**
> (see below) — Rajasthan was run as the pilot state for
> `Objective2 Consolidated plan.md`'s corrected 4-variable design vector
> (arrangement restored); the other three states have not received the
> identical edit yet, per the consolidated plan's shared-config rule (§5,
> §7). `configs/states/rajasthan.yaml` is state-specific as always — this
> audit otherwise mirrors the Tamil Nadu reference audit's structure, with
> Rajasthan's own numbers.
>
> **RE-SYNCED 2026-09-18** (separate from the 2026-09-17 arrangement change
> above): `configs/states/rajasthan.yaml` was rebuilt against a corrected
> Objective 1 run (`state_config_version:
> "state_config_rajasthan_v2.0_2026-09-18-resync"`) — `Tm_target_C` moved
> 57.0→67.0 °C, `L_required_kJ_per_kg` moved ~285–344→~427–443 kJ/kg, the
> per-cluster PCM shortlist changed entirely, and clusters 1–2's medoid
> points changed (`RJP_0202`→`RJP_0192`, `RJP_0055`→`RJP_0083`; cluster 0's
> `RJP_0132` is unchanged). `system_config_shared.yaml` and
> `design_bounds_shared.yaml` were not touched by this resync. See
> `docs/09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md` §10 for the full record.

## Purpose

Freeze everything Phase 2–4 needs, once, so the simulator can never be
compared against a moving target. Per
`O2_Unified_PerState_Execution_Framework.md`, Phase 0: the two
`*_shared.yaml` files are identical for all four states (Tamil Nadu,
Rajasthan, Assam, Uttarakhand); only `configs/states/<state>.yaml` varies.

## `system_config_shared.yaml` — what's frozen and why

| Category | Value | Source |
|---|---|---|
| Collector | 1.5 m², F_R(τα)=0.75, F_R·U_L=4.5 W/m²K | Domestic FPC baseline [Singh 2025] |
| Tank | 50 L, height:diameter=2:1, U_tank=0.8 W/m²K | Chen et al. 2025 Table 1 |
| PCM integration | Direct encapsulation, Al capsule wall (0.8mm, 205 W/mK) | Framework doc §3.1 |
| Pump | 0.010–0.050 kg/s, η=0.60 | Framework doc §3.1 |
| Safety | max water 75°C, max PCM 65°C, max pressure 3.5 bar | Framework doc §3.1 |
| Delivery | target 45°C | Framework doc §3.1 |
| Solver | backward-Euler (linear-implicit water node, lagged PCM), dt=300s, adaptive sub-stepping | Barqawi 2025 §4c |
| Selection | Pareto tolerance = 5% | Framework doc §9.5 (pre-declared, Bug-Fix 7) |
| Verification | Gate 1 pass <0.1%, warn <0.5%; Gate 4 benchmark band 54-84% | Framework doc §5, Singh 2025 |

Same two config-only additions as Tamil Nadu (not per-state, both live in
the shared file): `melting_half_width_K` (the PCM database reports a
single `Tm_C`, not a measured solidus/liquidus interval) and
`initial_water_temp_C` / `initial_pcm_state` (Gate 2's initial-condition
tests need these overridable).

**This is the config that produces the Cluster-0 safety finding in the
master overview.** `safety.max_pcm_temp_C = 65.0` and `tank.volume_L = 50.0`
are both frozen here, identical to Tamil Nadu — the finding is not a
Rajasthan-specific config choice, it is what this shared config does when
fed Rajasthan's much hotter collector input (see Phase 0 section below).

## `design_bounds_shared.yaml` — what's frozen and why

Sphere shape stays frozen (`[sphere]`) — never named in the objective
statement, so this remains a documented, undisputed scope cut. **Capsule
arrangement is a searched categorical variable** (`[single-layer,
staggered, radial]`) as of 2026-09-17, per the Objective 2 statement's own
four named parameters (diameter, arrangement, count, flow) — previously
frozen to `[staggered]` only, which was a real scope gap, not a
justified simplification (see `09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md`
§9). Capsule diameter 0.02–0.08 m, capsule count 8–37 (integer, widened
from 8–24 to give the volume-fraction target more headroom — re-verified
per arrangement in Phase 2, see `02_PHASE2_GEOMETRY_CONSTRAINTS.md`), PCM
volume fraction 0.10–0.20 of tank volume, flow 0.010–0.050 kg/s.
`src/design/schema.py`'s `DesignVector` requires `capsule_arrangement`
explicitly (no default), so no call site can silently assume staggered.

## `configs/states/rajasthan.yaml` — Phase 1's actual output

Every field was read directly off the frozen Objective 1 files already
sitting in `data/objective1/` — nothing in this file is invented:

- **3 Level-A GMM regimes** (`cluster_id` 0–2) — Rajasthan's Objective 1
  clustering chose `K_FINAL=3` (Tamil Nadu chose 5; this is Objective 1's
  own model-selection result, not an Objective 2 choice). Each regime
  carries its population count, `Tm_target_C` (**67.0 °C for all 3
  Rajasthan clusters** as of the 2026-09-18 resync — was 57.0 °C under
  the pre-resync `state_config_rajasthan_v1.0` read, now stale; see
  `state_config_version` at the top of `rajasthan.yaml` and
  CLAUDE.md §3.2), `T_mains_est_C`
  (24.7–26.0 °C across clusters — noticeably lower spread than Tamil
  Nadu's, but read directly off `climate_signature_rajasthan.csv`, not
  estimated), `L_required_kJ_per_kg`, and paths to that cluster's medoid
  hourly/daily weather files — read from `cluster_profiles_rajasthan.csv`.
- **PCM shortlist per regime** — the Top-3 names per cluster from
  `mcdm_topk_by_cluster.csv`, **re-synced 2026-09-18** (the pre-resync
  shortlist — Cluster 0 `RT50, RT45HC, Lauric acid (C12)`; Clusters 1/2
  both `savE® OM50, Paraffin/HDPE PCM3, Paraffin/HDPE PCM6` — is stale,
  read off a pre-T_DELIVERY-correction Objective 1 run). Current
  shortlists, now genuinely distinct per cluster: Cluster 0 gets
  `Palmitic-stearic acid/Expanded graphite, savE® OM55, Myristic
  acid/NBR-0.5` (medoid RJP_0132, unchanged); Cluster 1 gets `PureTemp
  60, CrodaTherm 60, n-Heptacosane (C27)` (medoid now RJP_0192/Nagaur,
  was RJP_0202); Cluster 2 gets `n-Heptacosane (C27), PureTemp 58,
  PlusICE A58` (medoid now RJP_0083/Jaipur, was RJP_0055). See
  `rajasthan.yaml`'s `regimes[].pcm_shortlist_detail` for the consensus
  rank/Borda score behind each.
- **Demand profile**: 300 L/day, `data/demand/demand_profile_rajasthan.csv`
  — matches `04_climate_signature_rajasthan.py`'s `NIGHT_DRAW_TOTAL_L=300`
  assumption (Avargani et al. 2021), and deliberately kept identical to
  Tamil Nadu's total so the four-state comparison stays fair (per
  `build_demand_profile.py`'s own docstring).
- **Mains temperature**: 18–30 °C range from the framework doc's Rajasthan
  state-input row; the per-regime point estimate the simulator actually
  uses (`T_mains_est_C`, 24.7–26.0 °C) is the population-weighted mean of
  the point-level column in `climate_signature_rajasthan.csv`, already
  inside that range.
- **Elevation**: unlike Tamil Nadu (which has no dedicated elevation
  script), Rajasthan's Objective 1 has `00c_attach_elevation.py` — a real
  per-point elevation attach, not a flat approximation. This is carried
  through unchanged into Objective 2 (nothing in Phase 1–3 reads elevation
  directly, but it is part of the frozen climate signature record).

## Phase 0 — climate-signature sanity check (Bug-Fix 8): PASSED, 3/3 regimes

`check_climate_signature.py` confirms the frozen weather under
`data/weather/` is genuinely Rajasthan's (hot, dry, high-clearness), not
another state's, and that each daily file is internally clean. Full
output: `results/phase0_climate_signature_check.txt` — see
`results/README.md` for what each line means and the inference drawn.

> **STALE — pre-resync, not yet re-run.** `results/phase0_climate_signature_check.txt`
> is dated 2026-09-17 22:28, i.e. written *before* the 2026-09-18 resync
> (`rajasthan.yaml`'s `state_config_version` timestamp). Its printed medoid
> ids for clusters 1–2 (`RJP_0202`, `RJP_0055`), regime sizes (114/103/103),
> and `Tm_target`/`L_required` figures (57.0 °C / 312.8, 304.1, 319.9 kJ/kg)
> all reflect the pre-resync inputs and are superseded by `rajasthan.yaml`'s
> current values (medoids RJP_0132/RJP_0192/RJP_0083, sizes 109/83/128,
> Tm_target 67.0 °C, L_required 437.90/427.18/443.35 kJ/kg). The table below
> is left as the last actually-produced output of this script; UNVERIFIED —
> could not confirm what a fresh run against the resynced config would
> print for GHI/T_a/CDD24 (cluster 0's medoid is unchanged so its row is
> likely still valid, but clusters 1–2's medoid points changed, so their
> GHI/T_a/CDD24 numbers below cannot be assumed to carry over). This script
> should be re-run before this section is cited again.

Summary of what the last (pre-resync) run reported, per regime:

| Cluster | Medoid (pre-resync) | Mean GHI (kWh/m²/d) | Apr–Jun mean daily-max T_a (°C) | CDD24 | Verdict |
|---|---|---|---|---|---|
| 0 | RJP_0132 | 5.12 | 39.8 | 12,348 | PASS |
| 1 | RJP_0202 (now RJP_0192) | 5.40 | 40.3 | 15,837 | PASS |
| 2 | RJP_0055 (now RJP_0083) | 5.06 | 41.1 | 14,789 | PASS |

All three sat inside the expected 3.0–7.0 kWh/m²/day dry-climate GHI band
and the 33–47 °C Rajasthan summer daily-max band at the time of that run;
medoid ids and regime sizes matched Objective 1's own
`cluster_profiles_rajasthan.csv` and `medoid_points_rajasthan.csv` at that
time; zero duplicate (point_id, date) rows and zero calendar gaps across
all 3,653 days (2016–2025) in every regime's weather file. The hot-dry
signature (high CDD24, large DTR, high daytime clearness, low cloud
fraction) was confirmed independently of the GHI/temperature bands, and
was visibly different from Tamil Nadu's coastal-humid or Assam's
humid-cloudy signatures — this was the evidence that the weather actually
simulated was Rajasthan's, not a mis-copied file from another state's
`data/weather/` folder. `rajasthan.yaml`'s own
`climate_signature_sanity_check` block (status: PASSED) reflects the
current, resynced numbers for the cluster-aggregate CDD24/DTR/Ta_p95/
cloud-fraction/kt figures, and should be treated as more current than
this stale results file for anything other than the pre-resync medoid
point-level GHI/T_a numbers above.

## How Phase 1 was verified

`load_state_config("rajasthan")` in `src/io_utils.py` is exercised every
time any Phase 2/3 function runs (every one of them resolves its weather/
PCM/demand paths through it) — so every successful Phase 2/3 run in this
project is itself an implicit Phase 1 integration test, same as Tamil
Nadu. There is no separate Phase 1 script beyond the Phase 0 sanity check;
see `HOW_TO_RUN`-equivalent commands in `../README.md`.
