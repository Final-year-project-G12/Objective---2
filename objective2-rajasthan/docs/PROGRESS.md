# O2 — Rajasthan progress log

Single progress log for the implementation of
`DOCUMENTATION PORTAL/OBJECTIVE2_REDESIGN_PROPOSED_PLAN.md` (read-only; not edited).
Branch: `o2-redesign-rajasthan` (nothing committed). Scope: this folder only.
Frozen `configs/system_config_shared.yaml` is not edited. Every number below
traces to a command output or file named next to it.

## 0. Decisions carried in from the plan (§6, §6A) — not reopened

| # | Decision | Source |
|---|---|---|
| D1 | Demand profile (07:00 / 19:00) is **local time**; the UTC indexing is a confirmed bug, fixed first | §6 item 1 |
| D2 | O2 uses **Objective 1's MCDM top-3** as written; `retarget_tm.py` lists are retired from the main pipeline (labelled comparison only); Phase 4 re-run on O1 PCMs | §6 item 2 |
| D3 | Shape family: spheres, **thickness = inner radius** (diameter derived `D = 2(R_in + t_w)`); tube capsules dropped | §6 item 3 |
| D4 | **1-D stratified multi-node tank** (WP2 Level 2) approved | §6 item 4 |
| D5 | Weather split: 2016–2020 explore, 2021–2023 pick winner, **2024–2025 held-out test** (the two lowest-GHI years; state in paper). One simulation set per O1 cluster, using the cluster's **current** O1 medoid over 10 years | §6 item 8 |
| D6 | Point-year accepted at ≥ 98 % valid hours; gaps ≤ 3 h interpolated and flagged; longer gaps reject the point-year (listed, not dropped silently); gap table per point-year | §6A 1 |
| D7 | Safety shield ON by default (IS 12976:2023 §8.2); shield-off reported as a sensitivity case | §6A 2 |
| D8 | IS 12976 non-compliance (33.3 L/m² < 40–100) disclosed as a "compact tank" case; labelled supplementary sizing-sensitivity study via in-memory overrides only | §6A 3 |
| D9 | "Better than water-only" = paired multi-year gain exceeds the WP6 repeatability band on ≥ 1 primary metric; primary set = WP1 night/morning metrics (E_del,45 in 18:00–09:00, τ_serve, delivery-temperature stability); annual energy secondary | §6A 4 |
| D10 | Tie-breakers: (a) lower overheating/shield hours, (b) higher τ_serve, (c) lower PCM mass, (d) fewer capsules, (e) larger margin to 65 °C. Ties inside the band = "indistinguishable" | §6A 5 |
| D11 | Optimiser: NN-ensemble surrogate + NSGA-II + active learning; DOE screening first; dense-grid check; GP-BO and XGBoost/RSM as comparisons | §6A 8 |
| D12 | CFD (OpenFOAM, Fluent) calibration/cross-check only, never in the loop | §6A 9 |
| D13 | Rule for all work: every run/regime/year/metric reported, including nulls; fixed parameters (tank, collector, demand, O1 shortlist) not tuned | §6A preamble |

## 1. Out of scope for this pass (stated, not faked)

- **WP2-C new CFD runs.** ANSYS Fluent is not installed; no new OpenFOAM runs.
  `configs/cfd_closure_v1.yaml` will be built read-only from the existing CFD φ
  findings and labelled **provisional, not recalibrated**.
- **WP7 porting** to Tamil Nadu, Assam, Uttarakhand. Code stays `--state`-parameterised;
  only Rajasthan is touched. The same UTC-index bug exists in the other three
  states' `tank_model.py` and is **not** fixed here.
- No `pip install` and no PyTorch without asking.

## 2. Pre-flight evidence

- Branch created from `main` (`git checkout -b o2-redesign-rajasthan`); working tree clean at start
  except untracked `../openfoam_cfd/` (outside this folder, not touched).
- Legacy snapshot: SHA-256 of all 77 files under `results/` taken **before any edit** →
  `docs/legacy_result_hashes.sha256`. `git status --short results` is empty after G1, i.e.
  no result file has been changed.

### Baseline reproduction (before any edit)

Scratch script (outside the repo, bytecode writing off) calling `run_case` with the Phase-7
deployable design per regime from `results/phase7_deployable_design_per_regime.csv`;
plain tank = same design vector with `pcm_name=None`. Python 3.10.11.

| Regime | Plain kWh (repro) | PCM kWh (repro) | Plan §3.1/3.3 |
|---|---|---|---|
| 0 | 1584.8187 | 1588.0561 | 1584.8 / 1588.1 ✔ |
| 1 | 1843.3873 | 1845.6208 | 1843.4 / 1845.6 ✔ |
| 2 | 1788.9153 | 1791.2025 | 1788.9 / 1791.2 ✔ |

Timing re-run (`timing_shift_hours`, unfixed code) reproduces the plan §3.3 table: all
kWh and solar-fraction (SF) cells match. **One cell differs in the last digit:** regime 1,
shift 5.0 PCM gain is **0.3331 %** from the same kWh values (1203.3010 / 1199.3066), the plan
prints 0.331 %. The kWh values agree, so this looks like a rounding/transcription slip in the
plan; no effect on conclusions. Gate "baseline matches" → **PASS**.

## 3. G1 — Timing fix

**Change.** `src/simulation/tank_model.py`: new `_demand_hour_of_day(row, i)` replaces the
UTC-hour lookup; it reads the weather file's `local_hour`. A frame with `timestamp_utc` but no
`local_hour` raises `ValueError` (no silent UTC fallback); a frame with neither (synthetic gate
inputs) keeps the legacy row-index fallback.
**Test.** `tests/test_demand_timing.py` (4 tests). The expected clock is computed
independently (`timestamp_utc → Asia/Kolkata`), not from the `local_hour` column the simulator
reads. Checks: `local_hour` equals IST hour for the whole file; the largest draw of every
complete local day is at 19:00 and the morning/evening peaks are at 07:00 / 19:00; UTC-only
frames are refused; `run_case` records `hour_of_day` equal to the IST hour.
`pytest tests` → **6 passed** (4 new + 2 existing reproducibility).
**Negative control.** Re-installing the pre-fix UTC lookup makes the two timing tests fail.

**Post-fix re-run** (same designs as the baseline, `record_hourly=False`):

| Regime | Plain kWh | Plain change vs pre-fix | Plain SF | PCM kWh | PCM SF | PCM gain | Gate-1 residual % |
|---|---|---|---|---|---|---|---|
| 0 | 1098.9371 | −30.66 % | 0.3587 | 1106.3826 | 0.3621 | 0.6775 % | 0.0419 |
| 1 | 1199.3066 | −34.94 % | 0.3951 | 1203.3010 | 0.3956 | 0.3331 % | 0.0649 |
| 2 | 1208.7442 | −32.43 % | 0.3834 | 1213.2942 | 0.3850 | 0.3764 % | 0.0330 |

(residual column = `residual_pct_of_collector` of the PCM run.)

**Reading against the pass condition** ("−31 % energy and 0.34–0.40 SF shift reproduce"):
- The −31 % figure in the plan is the regime-0 value only; regimes 1–2 drop 32–35 %.
- SF after the fix is 0.359–0.395, inside the plan's 0.34–0.40 range; all three are below the
  54–84 % Gate-4 benchmark band (`system_config_shared.yaml`), as the plan anticipated. The
  Phase-4 calibration therefore has to be revisited.
- **Half-hour alignment (new, needs your call).** `local_hour` is the *floor* of IST
  (00:00 UTC = 05:30 IST → 5), which is identical to the plan's `shift = 5.0` row above, not the
  `5.5–6.0` row (which rounds up and gives regime 0: 1085.8 kWh, SF 0.340; regime 1: 1195.9,
  0.376; regime 2: 1185.9, 0.361). The two alignments differ in plain-tank energy by 1.2 % (regime 0),
  0.3 % (regime 1) and 1.9 % (regime 2). An hourly NASA POWER value stamped 00:00 UTC spans 05:30–06:30 IST,
  so neither is exact; the fix follows your instruction to use `local_hour`.

**Not changed in G1 (deliberately):** `run_case.py:103` still sums the draw with `h % 24`; over
whole days this equals the local-hour sum, so annual `e_demand_ideal` is unaffected for 8760 h
and 8784 h years. Leap-year handling is a G2 item.

**Gate G1 verdict: PASS, with the disclosures above.**
Every previously reported Rajasthan number (docs 05–09, results/phase5–8, the Objective 3 contract)
is now stale relative to the fixed simulator; nothing has been regenerated yet. Per your note,
work stops here for your review.

## 4. G2 — WP2 Level 1 repairs (decision: keep `local_hour` floor, continue)

**Changes (all inside this folder; frozen YAML untouched).**

| Item | Change |
|---|---|
| PCM mass / wall mass | New `src/simulation/capsule_mass.py`: PCM mass from the **inner** sphere `D − 2·t_w` (t_w = 0.8 mm from config); wall mass from the shell volume × 2700 kg/m³ (Al density and cp 900 J/kg·K are handbook values, **not** in the frozen config — flagged). Water displacement still uses the outer volume. |
| Wall thermal mass | Carried in the PCM node as `PCMThermalProps.wall_cp_J_kgK` (= m_wall·c_Al / m_pcm); `capsule_enthalpy.py` stays exactly invertible (unit-tested). Stiffness check uses the wall-inclusive heat capacity. |
| Leap year | `io_utils.load_hourly_weather(..., drop_29_feb=True)` removes local 29 Feb → every year 8760 h (clusters 1 and 2 were 8784 h). |
| Per-run outputs | `mean/min/max_f_melt`, `delivery_temp_hours`, masses now computed inside `run_year` for every run (previously only with `record_hourly=True`; `delivery_temp_hours` was NaN in all DOE rows). |
| Pump energy | **Flagged, not dropped:** metric `pump_energy_meaningful = False` (Ergun ΔP across the capsule bed only; real loop not modelled). Must not be used as an objective or tie-breaker. |
| Not changed | `R_pcm = r/(5k)` still uses the outer radius; the PCM conduction path via inner radius belongs with the thickness = inner-radius reparametrisation (D3, G7 onward). |

**Tests.** `tests/test_level1_repairs.py` (9 tests): PCM mass = N·π/6·(D−2t)³·ρ to 1e-6; plan's 11.5 % / 5.9 % overstatement reproduced; enthalpy round-trip and band enthalpy with wall; 8760 h and no 29 Feb in all 3 regimes; `run_case` inner mass and summaries without hourly. `pytest tests` → **15 passed**.

**Time-step convergence** — `scripts/g2_timestep_convergence.py` → `results/g2_timestep_convergence.csv`
(18 runs, regime designs from phase7, plain and PCM, dt = 300/150/75 s via in-memory override):

| Regime | Case | Useful kWh @300 | @150 | @75 | change 300→150 | change 150→75 |
|---|---|---|---|---|---|---|
| 0 | plain | 1098.937 | 1098.131 | 1097.763 | −0.0734 % | −0.0335 % |
| 0 | PCM RT44HC | 1104.421 | 1104.312 | 1104.308 | −0.0099 % | −0.0003 % |
| 1 | plain | 1196.126 | 1195.035 | 1194.493 | −0.0912 % | −0.0453 % |
| 1 | PCM OM49 | 1198.677 | 1198.471 | 1198.478 | −0.0172 % | +0.0006 % |
| 2 | plain | 1205.535 | 1204.529 | 1203.992 | −0.0835 % | −0.0446 % |
| 2 | PCM lauric | 1208.369 | 1208.365 | 1207.950 | −0.0003 % | −0.0344 % |

Gate-1 residual: max **0.068 %** over all 18 runs (≤ 0.1 % ✔). Regimes 1–2 plain-tank energy at 300 s
differs from the G1 table (1199.3 / 1208.7) only because 29 Feb is now dropped (8784 → 8760 h).

**Paired PCM gain depends on dt (this is the material finding):**

| Regime | gain @300 s | @150 s | @75 s |
|---|---|---|---|
| 0 | 0.499 % | 0.563 % | 0.596 % |
| 1 | 0.213 % | 0.288 % | 0.334 % |
| 2 | 0.235 % | 0.319 % | 0.329 % |

The plain tank shows clean first-order behaviour (each halving removes about half the previous
change); the PCM runs, which sub-step more finely around the melt band, are already closer to
converged at 300 s. So the 300 s step under-reports the PCM gain by roughly 0.1 pp — about a third
of the gain itself.

**Gate G2 verdict: FAIL on the stated criterion, residual part PASS.**
"Annual energy changes < 0.05 % when Δt halves": 300→150 s fails for all three plain tanks
(0.073–0.091 %); 150→75 s passes in all six series (max |Δ| 0.0453 %). Per the
gate rule, work stops here; nothing past G2 has been started. Options are in the hand-off message.

### G2 re-check at production dt = 150 s (decision: use 150 s)

`run_case.PRODUCTION_SOLVER_OVERRIDE = {"solver": {"timestep_s": 150}}`, merged in code before any caller
override; `system_config_shared.yaml` untouched. `pytest tests` → 15 passed. Convergence re-run
`python scripts/g2_timestep_convergence.py 150,75,37.5 results/g2_timestep_convergence_150_75_37p5.csv`
(the earlier 300/150/75 s data is kept as `g2_timestep_convergence_300_150_75.csv`).

| Regime | Case | change 150→75 s | change 75→37.5 s |
|---|---|---|---|
| 0 | plain | −0.0335 % | −0.0180 % |
| 0 | PCM RT44HC | −0.0003 % | −0.0193 % |
| 1 | plain | −0.0453 % | −0.0226 % |
| 1 | PCM OM49 | +0.0006 % | −0.0191 % |
| 2 | plain | −0.0446 % | −0.0245 % |
| 2 | PCM lauric | −0.0344 % | −0.0203 % |

Max Gate-1 residual **0.0698 %** (≤ 0.1 % ✔). Largest change on any halving **0.0453 %** (< 0.05 % ✔).
Paired PCM gain (useful energy), 150 s vs 37.5 s: regime 0 0.563 → 0.595 %, regime 1 0.288 → 0.337 %,
regime 2 0.319 → 0.333 %, i.e. the residual dt bias in the gain at 150 s is 0.01–0.05 pp; carry it into the
WP6 repeatability band. Slowest run was the 37.5 s PCM year at 30 s (not a production setting).

**Gate G2 verdict: PASS at dt = 150 s** (the 300 s step failed and is no longer used).
All numbers from here on use 150 s; the earlier G1 numbers (300 s) are superseded.

## 5. G3 — WP1 metrics

**Code.** `src/metrics/tes_metrics.py` (definitions, open-choice decisions and sign conventions in its
docstring); `run_year` gained per-hour `draw_kg`, `vol_ge_target_kg`, `Edel_target_Wh`, min/max
temperatures, melt-fraction min/max, an optional `initial_state` and `stop_when_Tw_below_C`;
`run_case(..., compute_tes_metrics=True, night_day_stride=k)` returns `tes` (dict) and `night_daily`
(per-day table). `run_case` solar-fraction denominator now uses the solver's actual draws (was an
`h % 24` index; identical for full years).
**Open choices fixed here (change deliberately):** retention start = 18:00 local; night window
18:00–09:00 (plan §6A; the plan's WP1 text says 08:00 and WP2 says 22:00); night scenarios restart from
each design's *own* 18:00 state of that weather day; hold censored at 72 h.
**Tests.** `tests/test_tes_metrics.py` (7) — three hand-calculated synthetic days (60 °C tank: E_rec,45 =
0.8708 kWh; 40 °C tank: 0; window delivery/compliance), PCM recoverable energy by hand (227.8 kJ; Tm < 45 °C
contributes sensible heat only), no double counting, crossing interpolation, annual closure recomputed from
hourly records (equals the solver's own residual to 1e-6), E_del,45 vs solar fraction, and τ_hold,45 vs the
analytic Newton-cooling time (|Δ| ≤ 0.05 h on two days, 0 on the third). `pytest tests` → **22 passed**.
*Note:* closure is an annual criterion — a 30-day January slice reads 0.34 % in both my recomputation and the
solver's own accumulator (only ~90 kWh collected), so the slice was not used for the gate.
*Note:* E_del,45/E_ideal ≥ solar_fraction by the energy drawn while the tank is colder than mains
(solar_fraction counts it negative, E_del,45 clips it at 0); gap < 0.002 on the test run.

**Evidence run** — `scripts/g3_metrics_report.py` → `results/g3_metrics_report.csv`,
`g3_night_daily_r{0,1,2}_{plain,pcm}.csv` (364 night scenarios per case, every day). Designs are the
legacy Phase-7 deployables (retargeted PCMs RT44HC / savE® OM49 / lauric acid), dt = 150 s —
**illustrative, not the O1-top-3 designs (G6)**.

| Metric | R0 plain | R0 PCM | R1 plain | R1 PCM | R2 plain | R2 PCM |
|---|---|---|---|---|---|---|
| Useful energy kWh (old metric) | 1098.1 | 1104.3 | 1195.0 | 1198.5 | 1204.5 | 1208.4 |
| Closure residual % | 0.045 | 0.045 | 0.060 | 0.068 | 0.034 | 0.034 |
| E_rec,45 mean kWh | 0.316 | 0.305 | 0.376 | 0.381 | 0.357 | 0.353 |
| E_rec,45 daily-max mean kWh | 1.381 | 1.339 | 1.541 | 1.551 | 1.492 | 1.476 |
| E_del,45 annual kWh | 904.2 | 914.3 | 952.9 | 956.6 | 987.4 | 993.9 |
| E_del,45 share in 18:00–09:00 | 0.648 | 0.651 | 0.663 | 0.664 | 0.656 | 0.658 |
| Max outlet T °C | 72.65 | 72.34 | 72.69 | 72.23 | 72.69 | 72.35 |
| Max PCM T °C | — | 62.32 | — | 62.21 | — | 62.33 |
| Latent cycles/day | — | 0.98 | — | 1.00 | — | 0.98 |
| τ_hold,45 mean h | 27.8 | 26.1 | 39.8 | 41.4 | 34.1 | 33.6 |
| τ_hold,45 censored (72 h cap) | 1.4 % | 1.1 % | 9.3 % | 12.4 % | 7.7 % | 8.0 % |
| τ_serve mean h (of 15) | 0.46 | 0.44 | 0.60 | 0.60 | 0.50 | 0.49 |
| serve_frac_45 mean | 0.053 | 0.050 | 0.072 | 0.072 | 0.058 | 0.057 |

**What these numbers say (reported as they are):**
1. **No PCM benefit on the night-and-morning metrics at these designs.** τ_hold,45 is 1.7 h *shorter* with PCM in
   regime 0, 0.5 h shorter in regime 2, and 1.6 h (4 %) longer in regime 1; E_rec,45 is slightly *lower* with PCM in
   regimes 0 and 2 (PCM displaces water). Annual E_del,45 is higher with PCM by 1.1 / 0.4 / 0.7 %.
2. **Floor effect on the serve metrics.** serve_frac_45 is only 5–7 % for both tanks: the 46 L evening draw on a 50 L
   tank brings the outlet below 45 °C within ~0.5 h of the 18:00 restart, whatever is inside. With the fixed
   sizing, τ_serve and serve_frac cannot separate designs; this matters for decision D9 (they are the named
   primary metrics) and goes to the guide as an open item, together with the IS 12976 sizing diagnostic (D8).
3. The PCM melts and freezes ~once a day (0.98–1.00 cycles/day) and the safety shield binds at the PCM side
   (max PCM 62.2–62.3 °C vs the 62 °C bypass).
4. RT44HC melts at 42.5 °C (< 45 °C), so its latent heat is excluded from E_rec,45 by definition.
5. Cost: with all-day night scenarios a PCM run takes 27–46 s (plain 6–10 s). The optimiser will use the in-run
   metrics every evaluation and the scenarios on a day stride; G8 must decide the stride.

**Gate G3 verdict: PASS** — closure ≤ 0.1 % (max 0.068 %), three synthetic-day hand checks pass, all metrics
unit-tested.

## 6. G4 — WP2 Level 2: 1-D stratified multi-node tank

**Code.** New `src/simulation/tank_model_multinode.py` (numba-compiled kernel; physics, assumptions and
limits in its docstring); `tank_model.py` (single node) untouched and still the default
(`run_case(..., tank_model="single")`; `tank_model="multinode", n_nodes=10, stack_anchor="center"` selects the new
one). Same `SimulationResult` contract, node-resolved hourly `E_stored_kWh` / `E_rec45_kWh`, node states in
`hourly.attrs` for the night scenarios; `tes_metrics` uses them when present.
Model in one paragraph: N equal nodes; draw = plug flow mains→bottom, outlet = top node; collector loop takes
water from the bottom node at the design flow rate and returns it at the node of equal temperature (so flow sets
loop ΔT and inlet level, not collector Q); upwind advection, axial conduction, per-node ambient loss, pairwise
inversion removal (pool-adjacent-violators, energy-conserving); capsules placed in nodes by layer height
(stack anchored at the tank **centre** by default — a neutral choice, ablate in G11); per-node UA_eff uses the node's
actual through-flow; shield and re-solve as in the single-node model; pump energy not modelled (flagged since G2).
**Not applied here:** the CFD φ closure (`cfd_closure_v1.yaml`, still to be built, provisional); PCM sub-model is
still the lumped r/(5k) one.

**Tests** — `tests/test_multinode_tank.py` (8): numba enthalpy = reference enthalpy (1e-12); **N = 1 reproduces
the single-node plain tank** (energy, unmet, loss to 1e-5); energy closes to < 1e-6 % and a year < 20 s;
inversion removal conserves energy; capsule layout/anchor; CFD draw case; stratification persists 7 h without draw;
node-resolved metrics + night restarts run. Full suite: `pytest tests` → **30 passed**. (Two bugs found and fixed on
the way: the first mixing routine did not fully sort strongly inverted profiles; the hourly closure must use the
unclipped load that the exact balance books — `Q_load_net_Wh`.)

**CFD qualitative reproduction** (`results/g4_cfd_draw_case.csv`; `openfoam_cfd/docs/COMPONENT_CFD_NOTES.md`:
50 L tank, 30 L at 55 °C over 20 L at 25 °C, 0.03 kg/s of 25 °C mains, CFD result 27 L at ≥ 45 °C; a fully mixed
43 °C node gives none). dt = 30 s.

| nodes | stratified: litres ≥ 45 °C | mixed 43 °C |
|---|---|---|
| 5 | 19.8 | 0.0 |
| 10 | 22.5 | 0.0 |
| 20 | 25.2 | 0.0 |
| 40 | 26.1 | 0.0 |

Ideal plug flow would give 30 L; first-order upwind diffusion pulls the 1-D result below it, converging toward the
CFD's 27 L as N grows. The CFD itself is not validated against measurements (its own §4), so this is agreement with
another model, not validation.

**Timed years and the single- vs multi-node comparison** (`scripts/g4_multinode_report.py`,
`results/g4_multinode_report.csv`; legacy Phase-7 designs, illustrative; dt = 150 s; JIT warm-up
excluded):

| Regime / case | useful kWh single | N=10 | N=20 | SF single | SF N=10 | SF N=20 | runtime s single / N=10 / N=20 |
|---|---|---|---|---|---|---|---|
| 0 plain | 1098.1 | 1165.6 | 1174.5 | 0.357 | 0.302 | 0.294 | 2.6 / 1.4 / 2.5 |
| 0 PCM | 1104.3 | 1173.8 | 1185.7 | 0.361 | 0.306 | 0.298 | 10.8 / 3.0 / 5.8 |
| 1 plain | 1195.0 | 1267.5 | 1275.9 | 0.393 | 0.331 | 0.322 | 3.1 / 1.7 / 2.4 |
| 1 PCM | 1198.5 | 1277.9 | 1289.5 | 0.395 | 0.331 | 0.322 | 11.7 / 3.1 / 5.4 |
| 2 plain | 1204.5 | 1286.0 | 1296.4 | 0.382 | 0.327 | 0.320 | 3.3 / 1.8 / 3.2 |
| 2 PCM | 1208.4 | 1293.0 | 1305.4 | 0.384 | 0.329 | 0.321 | 9.8 / 2.3 / 4.0 |

Paired PCM gain in useful energy: single 0.56 / 0.29 / 0.32 %; N=10 0.70 / 0.82 / 0.55 %; N=20 0.95 / 1.07 / 0.70 %
(regimes 0 / 1 / 2). Gate-1-style residual: 0 (to print precision) for all multi-node runs.

**What this means (reported as is):**
1. Stratification changes the annual numbers a lot: +6–7 % useful energy (cooler collector inlet → more collection)
   and solar fraction *down* 0.05–0.06 (hot water is drawn from the top first, so the hottest layer is wasted above
   45 °C while later draws are cold). The single-node results in sections 2–5 are therefore model-form dependent.
2. **The multi-node result is not converged in N**: N = 10 → 20 adds 0.7–1.0 % to useful energy and 0.15–0.25 pp to
   the paired PCM gain. N is a modelling parameter until an N-convergence study (10/20/40) sets it; I have *not*
   changed the default (plan range 8–12) and flag it as an open decision for WP6's repeatability band.
3. Runtime is no obstacle: 1.4–3.1 s per year at N = 10 (≤ 5.8 s at N = 20), so the multi-fidelity plan is not needed.
4. The plain-tank maximum water temperature rises to 73.3 °C (shield acts on the top node, start-of-sub-step);
   still < 75 °C. PCM maximum stays at the 62 °C shield.

**Gate G4 verdict: PASS** — reproduces "27 L vs 0 L" qualitatively (22.5 L at N = 10, 26.1 L at N = 40, vs 0 L mixed);
a year takes ≤ 5.8 s (< 20 s).

## 7. G5 — WP4 weather inventory and year roles

**Code.** `src/weather/inventory.py` (inventory + cleaned hourly files), `src/weather/roles.py` (year roles and the
held-out lock), `run_case(..., weather=<frame>)` for multi-year runs; `io_utils.drop_leap_day` shared.
**Points.** Current Objective 1 medoids only: cluster 0 → RJP_0132, 1 → RJP_0192, 2 → RJP_0083 (each has membership
probability 1.0 in `data/objective1/cluster_assignments_rajasthan.csv`, cluster sizes 109 / 83 / 128; matches
`rajasthan.yaml` and `build_regime_weather.py`). The stale `medoid_points_rajasthan.csv` (RJP_0202 / RJP_0055) is not used.
**Source.** Raw NASA POWER JSON under `PCM-Selection-ML-model/era5-rajasthan/data/raw/nasapower/` (read-only; SHA-256 of each
file in the inventory). **Output:** `data/weather/point_years/weather_inventory.csv` (30 rows: 3 points × 2016–2025) and 30 cleaned
hourly files `data/weather/point_years/rajasthan/cluster{c}_{point}_{year}.csv`.
**Hourly resolution verified** per file: keys form an unbroken hourly UTC sequence 1 Jan 00:00 – 31 Dec 23:00
(8760 or 8784 keys; `hourly_sequence_ok` true for all 30).
**Result.** All 30 point-years accepted: 100 % valid hours, 0 gaps, 0 filled hours, 0 negative GHI, 0 hours with GHI above
1.1 × clear-sky + 5 W/m²; 8760 h after the 29 Feb drop. (The gap-fill and reject paths are exercised on synthetic files in
`tests/test_weather_roles.py`: a 3 h gap is filled and flagged, a 4 h gap and a 97 % valid year are rejected and stay listed.)
**Consistency check.** The new cache reproduces the existing regime weather files exactly (cluster 0 2025, clusters 1–2 2016:
timestamps, GHI, T, local_hour).
**Year roles enforced in code** (`roles.py`): 2016–2020 explore, 2021–2023 select, 2024–2025 test; `load_point_year`
refuses a year whose role differs from the stated purpose; test years additionally need `acquire_test_lock()` (atomic, single
use, writes `results/held_out_test.lock`; absent now — a test fails if it ever exists unexpectedly). This is a guard
rail inside the codebase, not a security boundary.
**Check of the plan's claim** "2024–2025 are the two lowest-GHI years": **true in all three clusters** (annual GHI kWh/m²,
2024 / 2025 vs the next-lowest year: cluster 0: 1785 / 1802 vs 1820; cluster 1: 1883 / 1892 vs 1941; cluster 2: 1791 / 1812 vs
1856) — so the held-out test is harsher than average, as the plan says; state it in the paper.
**Sanity run (non-test years only, plain tank, single-node, legacy design):** annual useful energy 1098–1165 kWh and
solar fraction 0.357–0.375 across the eight explore/select years of cluster 0 (6 % spread) — an early indication of the
year-to-year band WP6 must beat. No test year was loaded.

**Gate G5: PASS** — 100 % valid hours (≥ 98 %), current medoids only, year-role split enforced and tested.
`pytest tests` → 43 passed.

## 8. G6 — O1 PCM top-3 as the shortlist; Phase 4 re-run

**Change.** `io_utils.get_regime()` now returns Objective 1's MCDM top-3 (`data/objective1/mcdm_topk_by_cluster.csv`, consensus-rank
order) as `pcm_shortlist`; the retired `retarget_tm.py` list is kept only as `pcm_shortlist_retargeted` (labelled comparison;
`SHORTLIST_SOURCE = "retargeted"` reproduces the old behaviour). Every consumer (DOE, search, cards, selection, gates) therefore
sees the O1 list. `tests/test_o1_shortlist.py` (5 tests): lists equal O1's file, retired lists only as comparison, all 9 PCMs in the
database, cluster-0 rank-1 tie visible. **O1 rank-1 is tied in cluster 0** (savE® OM55 and Palmitic-stearic acid/Expanded graphite,
Borda 10 each); both stay on the shortlist, in file order.
O1 shortlists: cluster 0 = savE® OM55, Palmitic-stearic acid/Expanded graphite, Myristic acid/NBR-0.5; cluster 1 = PureTemp 60,
CrodaTherm 60, n-Heptacosane (C27); cluster 2 = n-Heptacosane (C27), PureTemp 58, PlusICE A58.
**Phase 4 re-run** (`scripts/g6_phase4_o1.py` → `results/phase4_verification_o1_pcms.txt`; the legacy report is untouched):
repaired simulator, dt = 150 s, single-node tank. Gate 1 PASS; Gate 2 PASS (12/12); Gate 3 PASS; **Gate 4 PASS-WITH-CAVEAT**
(optimised-looking design 36.9 % solar fraction vs the 54–84 % band — a 17.1-point mismatch, reported, not tuned: 50 L tank vs 300 L/day,
no backup heater); Gate 5 PASS (3/3). New O1 roster check: **all nine O1 PCMs verified** (worst Gate-1 residual 0.067 %).
Go/No-Go: **GO**. The report names the O1 PCMs.

**What the roster shows (reported as is; mid design = 14 × 50 mm, 0.03 kg/s, staggered; useful-energy change vs plain tank):**
cluster 0: OM55 +0.38 %, Palmitic-stearic/EG +0.29 %, Myristic/NBR +0.11 %; cluster 1: PureTemp 60 +0.55 %, CrodaTherm 60 +0.38 %,
n-Heptacosane +0.34 %; cluster 2: n-Heptacosane +0.29 %, PureTemp 58 +0.48 %, PlusICE A58 +0.41 %.
1. All nine melt completely (max melt fraction 1.0, 326–354 melt/freeze cycles a year) although mean melt fraction is only 0.21–0.23:
   the O1 PCMs (Tm 54.6–61 °C) only melt on the hottest afternoons — far above the 45 °C delivery target.
2. **Safety:** at this mid design the PCM peak exceeds the 65 °C limit for **Palmitic-stearic/EG (65.6 °C)** and **PureTemp 58 (66.5 °C)**,
   although the PCM-side shield (bypass 62 °C) engages tens of thousands of sub-steps a year. The shield stops *charging* only at 62 °C,
   which is not enough for a PCM that is already above its melt band. This must become a feasibility constraint in the optimisation
   (and is a point for O3's shield design) — it is not hidden by the roster's PASS, which gates on energy closure only.
3. O1's ranking table and the PCM database disagree on thermal conductivity (e.g. savE® OM55: 0.429 vs 0.13 W/m·K; Palmitic-stearic/EG
   0.452 vs 0.16; PureTemp 60 0.208 vs 0.20; n-Heptacosane 0.210 vs 0.2415). The simulator reads the database; the discrepancy is an O1
   data issue to raise, not resolved here.
**Gate G6: PASS** — verification report names the O1 PCMs; retargeted list retired from the main pipeline.
Superseded-evidence note: after this point `heat_transfer.py` / the numba kernel use the **inner** radius and inner area for the PCM
conduction resistance (decision D3; was the outer radius). The G3/G4 evidence tables above predate that change by a few tenths of a
percent on PCM runs and are illustrative only; the unit tests now compare the numba and Python UA directly.
`pytest tests` → 49 passed.

## 9. G7 — WP3 sensitivity study and PROPOSED design ranges (**stopped here for your approval**)

**Study.** `scripts/g7_sensitivity.py` (+ `scripts/g7_flow_baseline_and_packing.py`), explore years 2018 and 2019 only
(through `roles.py`; no select/test year loaded), O1 top-3 PCMs for each regime, 438 runs, **all geometrically valid** under
permissive bounds. Files: `results/g7_sensitivity_r{0,1,2}.csv`, `g7_sensitivity_paired.csv` (paired deltas vs the
water-only tank of the same year/model), `g7_plain_flow_baseline.csv`, `g7_flow_same_flow_gain.csv`, `g7_max_packing_fraction.csv`.
Gains are paired differences vs the plain tank (same weather, demand, shield, tank model); tau_hold in hours; night scenarios use
every 30th day (12 days), so tau metrics are noisier than the annual ones. Multi-node tank, N = 10, unless stated.

**Repeatability band measured here** (identical design, 2018 vs 2019 paired gain, n = 213): useful energy sd **0.10 pp**
(max 0.48), E_del,45 sd **0.16 pp** (max 0.98), tau_hold sd **0.52 h** (max 2.3 h). Model-form difference single vs multi-node on the same
designs: useful gain +0.09 ± 0.27 pp, tau_hold −1.35 ± 0.83 h. Not yet in the band: the node-count effect (G4: 0.15–0.25 pp on
the gain from N = 10 to 20) and the dt effect (0.01–0.05 pp).

### A. Thickness (inner radius) at constant PCM mass (inner PCM volume = 5 % of tank; staggered, 0.03 kg/s)
Mean over 3 regimes x 3 O1 PCMs x 2 years (18 runs per row):

| R_in mm | N | outer vol % | useful gain % | E_del,45 gain % | tau_hold gain h | runs > 65 C |
|---|---|---|---|---|---|---|
| 10 | 597 | 6.30 | 1.08 | -0.25 | 1.83 | 0 |
| 15 | 177 | 5.85 | 1.15 | 0.59 | 1.73 | 0 |
| 20 | 75 | 5.65 | 1.11 | 1.22 | 1.34 | 2 |
| 25 | 38 | 5.47 | 1.08 | 1.61 | 1.05 | 4 |
| 30 | 22 | 5.39 | 0.97 | 1.82 | 0.68 | 1 |
| 40 | 9 | 5.12 | 0.56 | 2.31 | 1.12 | 0 |

Across radii the spread is 0.4–0.9 pp (useful), 2.1–2.9 pp (E_del,45) and 1.0–1.3 h (tau_hold) per regime, above the measured band.
The metrics pull in opposite directions (small radius: longer hold; large radius: more delivered energy), a real trade-off for the
optimiser. **Confound, disclosed:** at constant PCM mass the capsules' outer volume falls from 6.3 % to 5.1 % of the tank as the radius
grows, so part of the E_del,45 trend is simply more water. In the single-node tank the radius spread is smaller (useful 0.2–0.25 pp,
tau_hold 0.4–0.7 h): the thickness effect is **model-form dependent**.

### B. Count, expressed as PCM volume fraction (R_in = 20 mm, staggered, 0.03 kg/s, multi-node)

| outer vol % | N | useful gain % | E_del,45 gain % | tau_hold gain h | runs > 65 C (of 18) |
|---|---|---|---|---|---|
| 0.5 | 7 | 0.31 | -0.53 | 0.57 | 5 |
| 1 | 13 | 0.38 | -0.35 | 0.67 | 5 |
| 2 | 27 | 0.55 | 0.06 | 0.87 | 2 |
| 3.5 | 46 | 0.77 | 0.39 | 0.78 | 2 |
| 5 | 66 | 1.00 | 0.97 | 1.18 | 2 |
| 7.5 | 99 | 1.38 | 1.85 | 1.93 | 2 |
| 10 | 133 | 1.78 | 2.72 | 2.90 | 2 |
| 15 | 199 | 2.54 | 4.10 | 4.12 | 2 |
| 20 | 265 | 3.31 | 5.64 | 5.89 | 2 |

Every metric rises monotonically across the whole range, so the best design will sit **at the 20 % cap**. The cap is administrative, not
geometric: the packing engine accepts 30–48 % (staggered: 39.6 % at R = 10 mm, 47–48 % at R = 20–40 mm; `g7_max_packing_fraction.csv`).
The sign differs from the old single-node finding (Phase 3.5 loading sweep: gain turned negative above ~2.5–3 % loading); that sweep was
not re-run here. The runs over 65 C are **PCM-specific, not fraction-specific**: Palmitic-stearic/EG (cluster 0) exceeds 65 C at every
fraction (peaks 65.3–65.8 C); savE OM55 and Myristic/NBR exceed it only at 0.5–1 % (too little PCM to absorb the charge).

### C. Flow (R_in = 20 mm, 5 %, staggered, multi-node)
In the multi-node tank the **water-only** tank itself depends strongly on flow (loop delta-T and return level set stratification and
collector inlet temperature; the collector F_R is flow-independent in the project model): regime 0, 0.05 to 0.01 kg/s raises useful
energy 1187.5 to 1275.7 kWh (+7.4 %) and E_del,45 785.5 to 882.6 kWh (+12.4 %). The **PCM gain at the same flow** is nearly flat:

| kg/s | useful gain % | E_del,45 gain % | tau_hold gain h | max PCM C |
|---|---|---|---|---|
| 0.010 | 0.85 | 0.98 | 1.42 | 63.7 |
| 0.020 | 1.28 | 1.32 | 1.49 | 64.5 |
| 0.030 | 1.28 | 1.38 | 1.55 | 64.8 |
| 0.040 | 1.26 | 1.39 | 1.47 | 65.1 |
| 0.050 | 1.31 | 1.41 | 1.49 | 65.5 |

Flow matters for the system, little for the PCM's added value, and PCM peak temperature rises with flow.

### D. Arrangement (R_in = 20 mm, 5 %, 0.03 kg/s, stack centred)
single-layer / staggered / radial: useful gain 1.274 / 1.275 / 1.276 %, E_del,45 1.399 / 1.376 / 1.407 %, tau_hold 1.62 / 1.55 / 1.65 h.
Spread <= 0.002 pp, 0.03 pp, 0.1 h: **inside the band, a null at this stack position**. Arrangement can only act through the vertical
spread of the capsules; the stack-anchor ablation is in G11.

### PROPOSED exploration ranges (each is a proposal for you to approve or change)

| Variable | Proposed range | Basis (source / evidence) | Tag |
|---|---|---|---|
| PCM thickness = sphere inner radius | **10–40 mm**, continuous | Plan WP3 sensitivity range; only literature datum is a 55 mm diameter capsule (R_in 26.7 mm, Avargani 2021, summary-level); effect above the band with a metric trade-off. R_in < 15 mm means at least 177 shells (597 at 10 mm): vendor availability **not checked**. The 10 mm end is the best end for tau_hold, so a result there would be boundary-constrained. | engineering assumption + study |
| Capsule count | **not a free integer**: set through PCM outer volume fraction **2–20 %** of the tank, N = round(f * V_tank / V_capsule(R)) | Floor 2 %: E_del,45 gain <= 0 below about 2 % and cluster-0 PCMs overheat at 0.5–1 %. Cap 20 %: the existing bound (`design_bounds_shared.yaml`, also Chen 2025's highest PCM-volume level), not geometric (packing allows 30–48 %). | study + existing bound |
| Flow | **0.010–0.050 kg/s kept, provisional** | Existing range. Without a flow-dependent collector F_R the optimum will sit at the 0.010 floor for a model reason, not a physical one (decision 3). | existing bound |
| Arrangement | single-layer / staggered / radial kept as three levels | Project-defined categories (no literature). Expect a null; kept so the null is documented. | project-defined |

### Decisions needed from you / Dr. Deepika
1. **Radius range:** accept 10–40 mm, or change the ends (extend below 10 mm? raise the floor to 15 mm for availability)?
2. **Count/fraction:** accept 2–20 %, or lift the 20 % cap (say to 30 %) since every optimum will sit on it? (Chen-comparability argues for 20 %.)
3. **Flow:** (a) add a flow-dependent F_R(m_dot) correction (e.g. the Hottel-Whillier flow factor; needs a cited F-prime, not in the project),
   (b) keep as is and report any flow optimum at 0.010 as a model artefact, or (c) fix flow and drop it as a variable. The objective names flow as a variable.
4. **Baseline convention:** paired gain vs a water-only tank at the *same* flow (what I used), or vs water-only at its own best flow (stricter)?
5. **Tank-model default:** multi-node N = 10 (plan range) vs N = 20 (closer to the CFD's 27 L; 0.15–0.25 pp different gain). Not covered by this study.
6. **65 C safety:** treat peak PCM temperature > 65 C as an infeasible design (Palmitic-stearic/EG would then be infeasible in cluster 0 at every fraction
   tested), or change the shield rule? Today's shield only blocks charging at 62 C.
7. **Arrangement:** keep as a variable although it is a null here, or fold it into the anchor ablation only?
8. **PCM conductivity discrepancy** between O1's ranking table and the PCM database (G6 finding 3): the O1 owner needs to confirm which is right.

**Gate G7:** ranges proposed with their sources; **awaiting your approval. Nothing past G7 (no optimisation, DOE, surrogate) has been run.**

## 10. G7 approval and G8 (WP5 S1-S3) - screening, initial DOE, surrogate selection

**G7 approved by the user (2026-10-26)**, recorded in `configs/design_space.yaml` (a new file; the legacy
bounds and the frozen system config are unchanged): inner radius **10-40 mm**, PCM outer-volume fraction **2-20 %** (count
derived by `src/design/space.py`), flow **0.010-0.050 kg/s**, arrangements **single-layer / staggered / radial**. Decisions that
came with it: flow option (b) - any optimum at the 0.010 floor is reported as a **model artefact** (the collector F_R is flow
independent); baseline = **water-only at the same flow**; multi-node **N = 10**; a design whose PCM peak exceeds **65 C** in any
simulated year is **infeasible**. Not answered by the user, so unchanged: the O1 conductivity discrepancy (G6 finding 3; the
simulator keeps reading the PCM database) and the 20 % cap (kept as approved).

**Infrastructure added for G8:** `src/optimize/baseline.py` (plain-tank flow grid, 17 flows per regime and year for the explore and
select roles only, PCHIP; error vs exact plain runs < 0.01 %), `src/optimize/evaluate.py` (one design -> paired objectives from the real
simulator), solver-measured `shield_water_h`, `shield_pcm_h`, `hours_over_limit`, `run_case(night_day_stride=0)` skips the night
scenarios. Tests: `tests/test_design_space.py` (23) and `tests/test_anova.py` (3).

### S1 - Taguchi L9 screening (`scripts/g8_s1_screening.py`, 9 (regime, O1 PCM) pairs x 9 runs x 5 explore years, 0 invalid runs)
Mean contribution of each variable to the total sum of squares (%, average over the 9 pairs; the error term is the year-to-year
spread, so p-values are optimistic - a screening aid only, as with Chen 2025):

| Response | inner radius | PCM fraction | flow | arrangement |
|---|---|---|---|---|
| g_window (night+morning E_del,45 gain) | 34.1 | 45.4 | 5.0 | 14.8 |
| g_annual (annual E_del,45 gain) | 31.6 | 48.2 | 4.8 | 14.7 |
| d_overheat (shield hours vs plain) | 84.8 | 0.7 | 11.0 | 1.5 |
| t_pcm_max | 79.3 | 5.8 | 12.0 | 2.6 |

**No variable can be fixed:** each explains at least ~5 % of one response, and radius governs overheating and PCM peak temperature
(the 65 C rule). **Arrangement is not a null over the whole space** (about 15 % of the gain variance; pairs in regime 1 reach 24-28 %),
unlike the single-point test in G7 (R = 20 mm, 5 %). L9 aliases interactions with the main effects, so this is a screening result; the
arrangement ablation (G11) tests it properly. Files: `g8_s1_r*_p*.csv`, `g8_s1_anova_r*_p*.csv`.

### S2 - scrambled-Sobol DOE (`scripts/g8_s2_doe.py`, 128 points, seed 20261026, same points for every pair, 5 explore years each)
1,152 designs (9 pairs): **1,143 simulated, 9 geometry-rejected by the exact engine, 0 errors -> 100 % complete** (gate >= 95 %).
The nine rejections are the same single radial design (R = 31.5 mm, 18.4 %, `passage_blocked`). Four designs first failed with
`MemoryError` (nine parallel jobs plus a large git command); they were re-run with the same Sobol points
(`scripts/g8_s2_repair.py`). Largest energy-balance residual 0.0000 %. Share of simulated designs within the 65 C limit
(rest are infeasible): r0: 119 / 119 / 125 of 127; r1: 127 / 126 / 124; r2: 127 / 111 / 101 (per PCM rank 1 / 2 / 3).
Files: `g8_s2_r*_p*.csv` (means, per-year sd, and per-year columns).

### S3 - surrogate comparison (`scripts/g8_s3_compare.py`, `src/optimize/surrogates.py`; `g8_s3_comparison.csv`, `g8_s3_selection.csv`)
Three families per pair: NN ensemble (5 x (32,32) tanh, bootstrap, scikit-learn), XGBoost, full quadratic RSM (ridge). Validation
inside each pair only: 5-fold over designs and leave-one-year-out x design folds. Mean over the 9 pairs:

| Target | Spearman NN / RSM / XGB (designs) | RMSE / year-sd NN / RSM / XGB | global R2 NN / RSM / XGB |
|---|---|---|---|
| g_window | 0.987 / 0.993 / 0.989 | 1.70 / 1.38 / 1.80 | 0.979 / 0.984 / 0.977 |
| g_annual | 0.988 / 0.993 / 0.989 | 1.76 / 1.40 / 1.87 | 0.979 / 0.985 / 0.977 |
| d_overheat | 0.946 / 0.970 / 0.967 | 1.82 / 1.26 / 1.47 | 0.884 / 0.946 / 0.923 |
| t_pcm_max | 0.844 / 0.886 / 0.928 | 7.48 / 7.19 / 5.47 | 0.681 / 0.720 / 0.862 |

Leave-one-year-out gives the same order (RMSE/year-sd 1.9-2.2 for the gains). Best Spearman per pair x target x validation:
RSM 26 + 27, XGBoost 10 + 9, **NN ensemble 0 + 0**. Per-pair choice (highest mean Spearman, ties within 0.02 broken by relative RMSE):
XGBoost for r0_p1, r0_p2, r0_p3, r1_p1, r2_p2, r2_p3; quadratic RSM for r1_p2, r1_p3, r2_p1.

**Reading (reported as is):**
1. The surrogates **rank** designs very well for the gain objectives (Spearman ~0.99), less well for overheating (0.95-0.97) and worst for the
   PCM peak temperature (0.84-0.93), which is the 65 C feasibility constraint; XGBoost is best on that one.
2. **Their absolute error is larger than the weather-year scale:** RMSE is 1.4-1.9 x the year-to-year sd for the gains (and 5-7 x for
   t_pcm_max, i.e. about 1 C). Plan acceptance (i) ("within-regime RMSE below the repeatability band, or the surrogate is declared unfit and
   the grid is used") is **not met** for absolute values. Surrogates are therefore used only to rank and propose candidates; every
   reported number is a simulator run, and the dense-grid check (S6) carries more weight.
3. **The NN ensemble did not win anywhere** (option B as specified). By the plan's own rule this is reported, and for G9 it stays only as a
   committee member (its spread is the uncertainty signal for active learning) alongside XGBoost and RSM; ranking and the PCM-peak
   constraint use the per-pair winner. Global R2 (0.96-0.98 for gains) looks good and is not what decides this.

**Gate G8: PASS** - surrogate chosen on within-pair RMSE and Spearman rank, not global R2; with finding 2 carried into G9.
`pytest tests` was last run before the S1-S3 scripts (56 passed); these scripts have no unit tests beyond the ANOVA ones.
Git: nothing committed by me; the user's commit `10bd4bc` (26 Oct 23:14) already contains my work up to that time plus `openfoam_cfd/`.

## 11. G9 - S4/S5 active learning + S6 dense grid (2026-10-27)

Files: `results/g9_al_summary.csv`, `g9_seed_stability.csv`, `g9_grid_check.csv`, `g9_boundary_check.csv`,
`g9_al_log_r*_p*.csv`, `g9_seed_front_r*_p*.csv`, `g9_s6_grid_r*_p1.csv`, `g9_band_r*.csv`. Produced by `scripts/g9_s4_s5.py`,
`scripts/g9_s6_grid.py`, `scripts/g9_assess.py`. All 9 (regime, PCM) pairs ran 5 AL rounds without crashes; the grid has 540 designs per
regime for the rank-1 PCM (0 rejected).

| Criterion | Result |
|---|---|
| Seed stability (3 seeds, hypervolume spread inside the WP6 band) | PASS, 9/9 pairs (`g9_seed_stability.csv`) |
| Grid vs final front, additive epsilon inside the WP6 band | PASS for r1_p1 and r2_p1; **FAIL for r0_p1**: eps 24.9 (g_window), 25.6 (g_annual) vs band 13.8 / 13.3 (`g9_grid_check.csv`) |
| Boundary detector | R_in at the 40 mm end and PCM fraction at the 20 % cap on 73-100 % of every front (all 9 pairs). Flow at the 0.010 floor on 0-44 % (r0 pairs 31-44 %): flagged as a MODEL ARTEFACT, as agreed. |

What the r0_p1 failure is (from the saved grid and seed-front files): the grid front point at 73.7 kWh g_window / d_overheat +26.2
(staggered, fraction 0.199, flow 0.010) is covered by no optimiser point within the band; the optimiser's nearest points differ by 24.9 kWh
in g_window. The optimiser also has no front point with d_overheat below +5.2 (grid has -2.6, single-layer, fraction 0.125, flow 0.010).
So the NSGA-II + AL front under-covers the **low-flow, low-overheating** corner for regime 0. The high-performance end (>99 kWh) is matched
within about 1-4 kWh. The final front is larger than the grid front in hypervolume (ratio 1.010 in r0, 0.945 in r1, 1.072 in r2).

Reading: the optimum is on the box boundary (large capsules, maximum PCM fraction), so the result says "more PCM is better inside the
approved ranges"; it does not locate an interior optimum. This is reported as found, not tuned away.

**Gate G9: NOT fully passed (1 criterion failed, r0_p1). Stopped here for a decision.** Options:
(a) add the dense-grid designs (real simulator runs) to the r0 candidate pool and report that origin separately;
(b) rerun r0_p1 AL with more rounds / a seed that seeds the low-flow corner;
(c) accept and carry the failure into the selection as a stated limitation for regime 0.
Recommendation: (a), because the grid points are simulator evaluations and cost nothing extra, and (b) afterwards only if the criterion is wanted to pass in its own right.

### 11.1 G9 follow-up: r0_p1 re-run with more AL rounds (option b, chosen by the user)

`G9_WARM=1 G9_MAX_ROUNDS=10 python scripts/g9_s4_s5.py 0 1` continued from the saved state (DOE + rounds 1-5, 170 designs); outputs
`results/g9_*_r0_p1_ext.csv` (originals kept). It stopped by the script's own convergence rule after round 8 (190 designs,
simulated-front hypervolume 1.969e7 -> 1.982e7, +0.7 % over three rounds). `scripts/g9_assess.py` now prefers `_ext` files when they exist.

Re-assessed (`g9_grid_check.csv`): seed spread still inside the band (288,577 vs band 6.29e6), but the grid-vs-front epsilon for r0_p1 is
**still outside the band**: g_window 23.5 vs 13.8, g_annual 24.1 vs 13.3, d_overheat 55.1 vs 166.9 (was 24.9 / 25.6 / 7.8). More rounds
did not close the gap, so it is not a budget problem; the surrogate-driven search does not reach the low-flow, low-overheating
corner of regime 0 (the corner where PCM adds heat only gently, see section 11).

**G9 remains NOT fully passed (r0_p1 only).** Options now: (a) add the 540 grid designs (real simulator runs, already saved) to the
regime 0 candidate pool for G10, reported with origin "grid"; (c) accept and state it as a limitation. Waiting for the choice.

### 11.2 G9 follow-up 2: box-vertex augmentation (method change, user asked to tune regime 0 until it passes)

**What the diagnosis found** (from `results/g9_s6_grid_r0_p1.csv`, no new runs): the uncovered grid-front point is a corner of
the design box (R_in 40 mm, PCM fraction about 20 %, flow 0.010 kg/s, staggered: g_window 73.67, d_overheat +26.2). In the same slice the
radial layout gives d_overheat +389.8 for g_window 74.4, so d_overheating is a cliff in the design variables; the surrogate smooths it
and NSGA-II populations rarely land exactly on a vertex. More AL rounds alone (section 11.1) did not help: eps 23.5 / 24.1 vs band 13.8 / 13.3.

**What was changed** (method only; band, criterion, simulator, design box and fixed parameters untouched):
`scripts/g9_s4_s5.py` gained `G9_VERTICES=1` (with `G9_WARM`, `G9_FROM_SUFFIX`): before more AL rounds it simulates all 2^3 box vertices
(R_in, fraction, flow) x 3 arrangements = 24 designs (origin "vertex"), adds them to the training set, then runs 3 more rounds.
The vertices are fixed by the approved box and are therefore chosen independently of the grid. Justification: the G9 boundary detector
had already shown the optima sit on the box edges. **Disclosure:** the grid also contains the vertices by construction, so the check
is not fully independent of this fix; the genuinely independent evidence is the seed spread and the interior of the front.
Outputs: `results/g9_*_r0_p1_ext2.csv` (the `_ext` and original files are kept; `scripts/g9_assess.py` prefers `_ext2`, then `_ext`).

**Result for r0_p1** (`g9_grid_check.csv`): eps_g_window 3.12, eps_g_annual 3.47, eps_d_overheat 15.8 vs band 13.8 / 13.3 / 166.9 -> **within band**;
final front 52 points, hypervolume ratio final/grid 1.046; seed spread 318,699 vs band 6.44e6 (pass); 243 simulated designs; 24/24 vertices valid.

**Consistency:** to keep PCM comparisons inside a regime fair, the same vertex step is being applied to the other 8 pairs
(same 3 extra rounds). Results of that run are recorded in 11.3 below.

### 11.3 G9 final state after the vertex step on all 9 pairs

All 8 other pairs ran the same warm start + 24 vertices + 3 rounds (`G9_WARM=1 G9_VERTICES=1`, ~20-25 min each, no errors; files
`g9_*_r*_p*_ext2.csv`). Re-assessed with `scripts/g9_assess.py` (`g9_grid_check.csv`, `g9_seed_stability.csv`, `g9_al_summary.csv`, `g9_boundary_check.csv`):

| Criterion | Result |
|---|---|
| Seed spread inside the WP6 band | 9/9 pass |
| Grid vs front epsilon inside the band (rank-1 PCM per regime) | r0_p1 3.12/3.47/15.8, r1_p1 1.75/1.84/1.85, r2_p1 0.20/0.05/0.00 (g_window / g_annual / d_overheat) vs band 13.8 / 13.3 / 166.9: **3/3 pass**. Grid hypervolume ratio final/grid 1.05, 1.01, 1.07. |
| Boundary detector | Unchanged qualitative result: R_in at the 40 mm end and PCM fraction at the 20 % cap on most fronts; flow at the 0.010 floor is flagged as a model artefact. |

Caveats: the grid check exists for the rank-1 PCM of each regime only (p2, p3 have no dense-grid check); the vertices are on the grid by
construction (see 11.2). **Gate G9: PASSED after the method change in 11.2.** The original (pre-vertex) files are kept for the record.

## 12. G10 - selection on the select years 2021-2023 (2026-10-27)

Produced by `scripts/g10_select.py <c>` from the latest G9 points per pair (`_ext2`). Files: `results/g10_selection_r{0,1,2}.json`,
`g10_selection_candidates_r{0,1,2}.csv` (90 candidates per regime, all feasible on the select years; the JSON carries a SHA-256 fingerprint).
A bug was found and fixed during this step (the tau_serve columns were joined after the feasible table had been copied, so the first
run crashed with a KeyError after simulating); the rerun is what is reported. Rule: plan 6A / decisions D9-D10 (see the script docstring).

| Regime | Chosen PCM | R_in mm | fraction | N | flow kg/s | arrangement | g_window kWh | g_annual kWh | d_overheat h | PCM peak C | PCM kg | tau_serve gain h | WP6 band g_window | S0/S1/S2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | savE® OM55 | 40 | 0.200 | 36 | 0.022 | staggered | 99.4 | 103.8 | 425 | 62.9 | 8.81 | -0.081 | 15.1 | 25/11/1 |
| 1 | PureTemp 60 | 40 | 0.199 | 35 | 0.048 | staggered | 94.3 | 99.3 | 193 | 62.3 | 9.01 | -0.012 | 10.0 | 15/8/2 |
| 2 | PureTemp 58 | 40 | 0.199 | 35 | 0.021 | staggered | 94.9 | 99.2 | 361 | 63.3 | 8.35 | -0.034 | 15.7 | 24/8/3 |

Reading (all from the files above): every chosen design sits at the box edge (R_in 40 mm, fraction ~0.20), i.e. 'maximum PCM'.
The benefit on the primary metric g_window is far above its band in every regime, but the night-serve duration gain (tau_serve) is
about zero or slightly negative (-0.01 to -0.08 h): PCM raises delivered energy, it does not extend how long 45 C water is served.
d_overheat is positive: the PCM designs spend more shield hours than the water-only twin. These are findings, not defects hidden.
The S0 sets (15-25 designs) are indistinguishable on g_window by the band; the pick is by the tie-break order, so the exact flow/
capsule count should not be over-interpreted. The best design of each other O1 PCM is carried into the held-out test.

### 12.1 G10 - one-shot held-out test (2024-2025), run 2026-10-27

`python scripts/g10_test.py --confirm-run-once` ran **once** (run id `heldout_96d878ef8f24`, selection fingerprints verified; lock file
`results/held_out_test.lock` now exists and is never to be deleted). 18 rows = 3 regimes x (chosen + best of each other O1 PCM)
x 2 years, each against its same-flow water-only twin: `results/g10_heldout_results.csv`. Nothing dropped.

| Regime | Design | g_window 2024 / 2025 (kWh) | Select-year value | d_overheat 2024 / 2025 (h) | PCM peak C | tau_serve gain h |
|---|---|---|---|---|---|---|
| 0 | savE OM55 (chosen) | 97.1 / 95.8 | 99.4 | 407.8 / 394.9 | 62.9 | -0.08 |
| 0 | Palmitic-stearic/EG | 85.9 / 84.8 | - | 797.2 / 774.4 | 63.3 | -0.06 |
| 0 | Myristic/NBR-0.5 | 61.3 / 60.6 | - | 1032.0 / 997.9 | 63.3 | -0.06 / -0.07 |
| 1 | PureTemp 60 (chosen) | 89.9 / 89.1 | 94.3 | 175.8 / 163.9 | 62.3 | -0.01 / -0.02 |
| 1 | CrodaTherm 60 | 75.8 / 74.6 | - | 671.8 / 649.2 | 62.4 | +0.02 |
| 1 | n-Heptacosane | 74.7 / 73.8 | - | 795.2 / 776.4 | 62.4 | +0.01 |
| 2 | PureTemp 58 (chosen) | 90.7 / 91.2 | 94.9 | 338.8 / 335.0 | 63.3 | -0.04 / -0.03 |
| 2 | n-Heptacosane | 64.8 / 64.5 | - | 804.0 / 822.4 | 62.4 | 0.00 |
| 2 | PlusICE A58 | 87.2 / 87.1 | - | 723.5 / 739.9 | 64.2 | -0.01 / 0.00 |

Reading: the chosen designs hold up on unseen years (3-5 kWh below their select-year g_window, i.e. well inside the bands of 10-16 kWh);
the ranking of PCMs within each regime is the same as on the select years; no PCM peak exceeded 65 C and water peaks stayed below 75 C
(72-73 C). 2024-2025 are the two lowest-GHI years, so these are harsher than average. **Null/negative findings, stated plainly:**
night-serve duration (tau_serve) is not improved by PCM in any regime (gain within about +-0.08 h), and every PCM design spends more
shield-hours than its water-only twin (d_overheat > 0).

## 13. G11 - ablations with controls (2026-10-27)

`python scripts/g11_ablation.py <c>` for c = 0, 1, 2 around each chosen design, explore years 2016-2020 (held-out years untouched); 35 rows per
regime in `results/g11_ablation_r{0,1,2}.csv`. Bands from `g10_selection_r<c>.json` (g_window: 15.1 / 10.0 / 15.7 kWh).

**Controls**
| Control | Expected | Observed (all three regimes) |
|---|---|---|
| N1 design variables on the water-only tank | identical | max abs diff 0.0 (3 variants) - PASS |
| N2 chosen design run twice | identical | diff 0.0 - PASS |
| N3 capsule-wall conductivity x10 | inside band | change 0.00 kWh (r0), -0.00 (r1, r2) - PASS |
| P1 latent heat = 0 | g_window falls by more than the band | 101.1 -> -28.0 (r0), 95.3 -> -37.9 (r1), 98.9 -> -36.5 (r2) - PASS (sensible-only PCM is worse than water) |
| P2 PCM fraction x2 | gain changes by more than the band | **NOT INFORMATIVE**: the chosen designs are already at the 20 % cap, so x2 is capped back to the same design (identical value). The count ablation below is the real test. |
| P3 synthetic Tm = 45 C PCM (diagnostic, not an O1 PCM) | night window responds | g_window 114.4 / 142.5 / 131.3 vs chosen 101.1 / 95.3 / 98.9 - the metric can see a PCM matched to the delivery target; r1 gains most (+47 kWh) |

**Effects vs the band (chosen -> varied)**
- **PCM amount (count via fraction 2 -> 20 %)**: g_window rises almost linearly, 5.9 -> 101.1 (r0), 5.9 -> 95.3 (r1), 5.8 -> 98.9 (r2): the dominant factor, far above the band. This is why every optimum is at the cap.
- **Capsule thickness at constant PCM mass**: only R_in = 40 mm is a valid geometry (R_in 10-30 mm at the same mass need 83-2248 capsules and fail the geometry check), so there is no thickness comparison inside the feasible set. State this rather than claim a thickness effect.
- **Flow**: r0 flow 0.010 gives 75.2 (-26 vs 101.1, outside the band) with d_overheat 22.7 vs 439; 0.02-0.05 is flat (100.4-103.7, inside the band). r1 is steeper (18.3 at 0.010, 66.2 at 0.020, 95.7 at 0.050). r2: 57.9 at 0.010, then flat 97-103. The low-flow differences come from stratification in a model with flow-independent collector F_R, i.e. the flow-floor **model artefact** already flagged.
- **Arrangement at the centre anchor**: r0 97.9 / 101.1 / 96.8 (single / staggered / radial), inside the band; r1 88.7 / 95.3 / 97.6 (largest gap 8.9 vs band 10.0, inside); r2 92.3 / 98.9 / 100.4 (largest gap 8.1 vs band 15.7, inside). So arrangement is a null on g_window in all three regimes at the centre anchor. Overheating differs more: r0 518 / 439 / 759 h (band 153), r1 429 / 198 / 336 (band 196), r2 612 / 373 / 529 (band 148), i.e. outside the band for some pairs of arrangements. (Correction 2026-10-27: an earlier version of this paragraph wrongly called the r1 and r2 single-layer gaps outside the band.)
- **Stack anchor (tank-model assumption)**: staggered g_window bottom / centre / top = 74.2 / 101.1 / 120.2 (r0), 58.8 / 95.3 / 114.9 (r1), 63.4 / 98.9 / 120.5 (r2). **This assumption moves the result by -27 to -37 and +19 to +22 kWh, larger than the band in every regime.** The absolute kWh values should be quoted only together with the anchor assumption (centre, an unvalidated modelling choice); the ranking of designs is less affected than the level.

None of this was used to retune anything. Note for the write-up: the tank-position sensitivity and the amount of PCM dominate; thickness, count at a fixed amount and arrangement are second-order or untestable inside the feasible box.

## 14. G12 - results registry, Objective 3 contract v2, documentation (2026-10-27)

- **Registry:** `python scripts/g12_registry.py` -> `results/results_registry.csv` (276 rows: bands, selection, held-out test, G9 checks,
  G11 controls and main effects, G4 CFD draw case; each row names its source file and filter). `scripts/g12_results_doc.py` generates
  `docs/04_RESULTS.md` from the same files, so its tables are not typed by hand.
- **Objective 3:** `PYTHONPATH=. python -m src.handoff.build_obj3_contract_v2` -> `results/obj3_environment_contract_rajasthan_v2.json`.
  The builder keeps the generic parts of the old contract and replaces simulator version, state vector, weather roles, per-regime designs
  and results, config hashes, the reward block (stale Phase-7 normalisation constants, default weights and the pump-energy term removed) and the shield text.
  The old contract file is untouched.
- **Documentation updated to match the code (standing instruction):** new set `docs/` (README, 01 model and metrics, 02 weather and design
  space, 03 optimisation pipeline, 04 results, 05 limitations and open items, 06 Objective 3 hand-off). `docs/00_*`-`09_*`,
  `docs/OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` and `results/README.md` got a "superseded" banner (bodies unchanged); `README.md` got a
  "current state" box at the top. `scripts/g12_verify_docs.py` checks that every file and function named in `docs/` exists:
  **111 references checked, 0 missing**.
- **Corrections made while documenting:** the G11 text in section 13 wrongly called the r1 and r2 single-layer arrangement gaps outside the
  band (8.9 and 8.1 kWh against 10.0 and 15.7); corrected in place with a dated note. The test `test_real_lock_file_not_present_yet`
  became `test_real_lock_records_the_single_held_out_run` (the lock now legitimately exists). The progress log had one Windows-1252 byte
  (the registered-trademark sign in a PCM name written by a script) that was converted to UTF-8.
- **Tests:** `python -m pytest tests` -> 79 passed.
- **Not done / not verified:** `docs/CLEANUP_PROPOSAL.md` is still a proposal (nothing archived or deleted); `pipeline.py` and `run_all_rajasthan.py`
  still run the old chain; `src/plots/make_plots.py` is not adapted to the current outputs (no new figures); the other three states, new CFD
  runs and any hardware validation are out of scope; no number in `docs/` is from outside `results/` except the
  early-gate numbers quoted from this log (sections 3-9), which come from `results/g2_*`, `g3_*`, `g4_*`, `g7_*`.
- **Git:** nothing committed by me; the working tree holds all changes.

## 15. Gate summary

| Gate | Result |
|---|---|
| G1 timing fix | PASS (with the half-hour alignment disclosed; user chose the `local_hour` floor) |
| G2 Level-1 repairs | FAIL at 300 s, PASS at 150 s (user chose 150 s) |
| G3 metrics | PASS |
| G4 multi-node tank | PASS (not converged in N, disclosed) |
| G5 weather and roles | PASS |
| G6 O1 top-3 and Phase 4 | PASS (Gate 4 with the solar-fraction caveat) |
| G7 sensitivity | stopped for approval, approved 2026-10-26 |
| G8 S1-S3 | PASS (the NN ensemble won nowhere; surrogates only rank) |
| G9 S4-S6 | PASS after a method change (box vertices); regime 0 failed twice before it |
| G10 selection and held-out test | PASS; test run once, `heldout_96d878ef8f24` |
| G11 ablations | done; controls pass except "fraction x2" which is uninformative (at the cap) |
| G12 registry, contract, docs | done |

## 16. Cleanup applied (2026-10-27, user-approved sections A and B of docs/CLEANUP_PROPOSAL.md)

- Moved to an archive folder (deleted on 2026-10-28 at the user's request): 40 stale files from `results/` (fix1-3/6/7, phase3.5-8, tm_retargeting_report.csv, results/README.md), the `results/plots/` directory (about 82 MB), and the logs `robustness_rerun.log` and `run_all_output.log` (to the legacy archive (deleted 2026-10-28)logs/`).
- Hash check against `docs/legacy_result_hashes.sha256`: 76 files match; the only difference is `results/README.md`, which has the "superseded" banner added earlier.
- Left in place: `results/`, `results/obj3_environment_contract_rajasthan.json` (kept until contract v2 is accepted), `results/phase0_*.txt`, `results/phase2_*.txt`, all code, all `docs/`, all `__pycache__/` (gitignored, regenerated by any run; moving them has no value).
- Three rework scripts read the old design table (`g2_timestep_convergence.py`, `g3_metrics_report.py`, `g4_multinode_report.py`); their path now points to `data/legacy/phase7_deployable_design_per_regime.csv` so they still run.
- 79 tests pass; `scripts/g12_verify_docs.py` reports 0 missing. Nothing committed.

## 17. Plots and entry points adapted to the current outputs (2026-10-27, user request)

- **Plots:** new `src/plots/make_plots_results.py` writes nine PNG figures to `results/plots/` (list in `docs/README.md`). It
  only reads saved files under `results/` (grid, optimiser points, selection logs, held-out results, ablations, band, G7/G8 tables); nothing is
  re-simulated and the held-out loader is not called. Inspected figures 1, 3 and 6 by eye. First draft errors fixed before keeping them: figure 1 compared the
  rank-2 selected design (regime 2) with the rank-1 optimiser points, now the points of the selected PCM's rank are shown and the grid only where it exists
  (rank 1); figure 3 legend overlapped bars; figure 6 labels were truncated and duplicated. The old `src/plots/make_plots.py` and `docs/plots/` still
  describe the old results.
- **`pipeline.py`:** rewritten. Stages verify, sensitivity, baseline, screening, doe, surrogate, band, optimize, select, heldout, ablation, report, handoff,
  plots, plus simulate, status and all. Each stage runs the same script and arguments that produced the saved results; `optimize` = 5-round run, then
  `G9_WARM=1 G9_VERTICES=1`, then the dense grid and `g9_assess.py`. The old copy is the deleted legacy copy.
- **`run_all_rajasthan.py`:** rewritten. Default = tests + report + handoff + plots + status (about 1.3 min, run once: tests passed, all stages finished);
  `--full` = the whole chain.
- **Guards:** stages that decide the frozen designs refuse while `held_out_test.lock` exists unless `--allow-invalidate` (checked: `--full` was refused);
  `--stage heldout` was called once to check the guard and was refused by the lock itself (`HeldOutLockError`), with `g10_heldout_results.csv` untouched.
- **Not executed:** `--stage all` end to end (hours, and it would overwrite the frozen results); only `--dry-run` listings (65 commands with the held-out stage).
  Re-deriving regime 0 pair 1 from scratch uses 5 rounds then vertices; the saved files had an extra intermediate `_ext` run (section 11.2).
- **Not tested end to end after the wrapper change:** `simulate` was run (regime 0, select years, chosen-like design: g_window 99.6 kWh, within the chosen design's range; not stored as a result).

## 18. Six-issue investigation (opened 2026-10-27): baseline, evidence and PROPOSED classification (no code changed yet; awaiting approval)

### 18.0 Rules in force for this section
Fixed parameters (tank, collector, demand, O1 shortlist) and model physics are not tuned toward PCM. A change is legitimate only if it corrects a defect, closes a method gap
or improves a measurement; an unfavourable result that survives a legitimate change stays a finding. The request also says issues 3 and 4 should be pursued "until they
disappear". Read together with the rule: I will keep testing legitimate variants of the measurement until the cause is understood, and I will record where a difference
vanishes and why; I will not alter physics, limits, demand or the shield to make it vanish. If a difference survives every legitimate variant it stays reported.

### 18.1 Baseline (reproduced)
Re-simulated the three chosen designs from `results/g10_selection_r{0,1,2}.json` with `src.optimize.evaluate.evaluate_design` (explore and select years). Differences from the
saved values: at most 1.0e-11 kWh (explore) and exactly 0 (select), all three regimes (g_window 101.1429 / 95.2857 / 98.8596 explore; 99.4345 / 94.3202 / 94.9431 select).
`g9_grid_check.csv` `within_band` is True for r0_p1, r1_p1, r2_p1, and `g9_seed_stability.csv` `spread_within_band` is True for all nine pairs. The baseline reproduces; work may proceed.

### 18.2 Evidence and proposed classification

| # | Issue | Proposed class | Core evidence (saved file / code) |
|---|---|---|---|
| 1 | Corner seeding added after r0_p1 failed | **Method gap** (undeclared post-hoc step) | not in the plan (no "vertex" or "corner" text in `DOCUMENTATION PORTAL/OBJECTIVE2_REDESIGN_PROPOSED_PLAN.md`); disclosed in this log sections 11.1-11.3; afterwards applied to all nine pairs and all three seeds (`g9_s4_s5.py`, env `G9_VERTICES`), so uniform in scope but not pre-declared. The grid check without the step exists for r0_p1 only as log text; base point files exist for all nine pairs (`g9_points_r*_p*.csv`), so the "without" side can be recomputed from saved files with no new simulation |
| 2 | Chosen designs on the box edge | **Finding + method gap** (the WP6 widening test was never run) | `g9_boundary_check.csv`: R_in at 40 mm on 83-99 % of the final fronts and fraction at the 20 % cap on 88-99 % (r0_p1 0.85 / 0.875; r1_p2 0.987 / 0.987; r2_p2 0.831 / 0.983). The packing engine accepts 30-48 % at R 40 mm (`g7_max_packing_fraction.csv`: 0.438 single-layer, 0.478 staggered, 0.279 radial), so the 20 % cap is administrative (the plan gave Chen 2025 10/15/20 % as the only source); R 40 mm comes from the legacy 40-80 mm diameter range. Neither bound has a physical or vendor justification in the files read |
| 3 | tau_serve gain about zero | **Finding, with a measurement gap** | held-out chosen designs: serve fraction 0.078-0.103 with PCM vs 0.092-0.108 plain (`g10_heldout_results.csv`); `g3_night_daily_r0_plain.csv`: mean tau_serve 0.46 h and mean minimum outlet temperature 25.2 C, i.e. the evening draw empties the tank either way (floor effect confirmed). The PCM gain is slightly negative (-0.08 h regime 0, SE 0.003 h, `g10_selection_r0.json`) and the metric does separate designs, so it is not blind. Working explanation, to be tested not assumed: the capsules take 20 % of the tank volume, so less water is available to a draw that already nearly empties the tank. `g11_ablation_r*.csv` P1 (latent heat 0) gives g_window -28.0 / -37.9 / -36.5 kWh, consistent with displacement on the primary metric. tau_hold (no draw) is positive: 49.5 vs 43.3 h held-out regime 0 |
| 4 | More shield hours than water-only | **Defect in the metric definition** (accounting mix) | `src/optimize/evaluate.py:61` and `:106`: d_overheat = (shield_water_h + shield_pcm_h) - plain shield_water_h. The PCM-side term is a per-node throttle at 62 C (`src/simulation/tank_model_multinode.py:323-328`) with no counterpart in a water-only tank, so the difference is positive by construction. Like for like (re-simulated, select years 2021/22/23, chosen designs): water-side shield hours PCM vs plain 481/516/452 vs 641/694/608 (r0), 603/576/536 vs 831/806/756 (r1), 492/503/451 vs 677/684/625 (r2), i.e. FEWER with PCM; PCM-side throttle hours 574/635/562, 432/412/409, 549/543/529. Peak water 72.2-72.5 C with PCM vs 72.9-73.4 C plain (the plain tank overshoots the 72 C guard more). Thresholds and logic (72 C water at the top node, 62 C PCM) are as frozen in `configs/system_config_shared.yaml` lines 70-73 and `tank_model_multinode.py:301`. No bug found in the shield logic itself |
| 5 | Thickness and "fraction x2" controls uninformative | **Method gap** (control design) | `g11_ablation_r*.csv`: thickness at constant mass is invalid for R 10-30 mm in all regimes (anchored at the 20 % design, R 10 mm needs 2248 capsules); R 40 mm gives 100.45 / 95.29 / 98.86 against base 101.14 / 95.29 / 98.86. "fraction x2" returns exactly the base value (101.14 / 95.29 / 98.86) because the cap clips it back. G7 (`g7_sensitivity_r*.csv`) shows a 5 % inner-volume mass IS valid from R 10 to 40 mm (R 10 mm: 597 capsules, valid), so the controls can be run from an interior anchor |
| 6 | Result depends on stack position | **Method gap + finding** (undeclared design-like assumption; the dependence is a finding) | set at `configs/design_space.yaml:23` (`stack_anchor: center`), passed at `src/optimize/evaluate.py:53,94` and `src/simulation/run_case.py:45,122`, applied in `src/simulation/tank_model_multinode.py:80` (`z0` for bottom / top / center). The chosen stack is 3 layers, 0.252 m of the 0.634 m tank height (40 %), so position is not neutral. `g11_ablation_r*.csv`, staggered, change in g_window against the centre: bottom -26.9 / -36.5 / -35.5, top +19.0 / +19.7 / +21.7 kWh (bands 15.1 / 10.0 / 15.7); single-layer top +12.2 / +12.5 / +12.8; radial -13.2 to +14.0. The gain stays positive at every position (lowest 58.8 kWh, staggered bottom, regime 1), so the sign is robust and the level is not |

### 18.3 Proposed actions, one issue at a time (each with a regression check against 18.1; nothing batched)
- **Issue 4 first** (cheapest; it feeds the objective and the tie-break): keep `d_overheat` as stored, add two separate paired quantities, `d_shield_water_h` (PCM minus plain, like for like) and `shield_pcm_h` (reported alone), and re-simulate the thinned candidate sets and the chosen/alternative designs. Decision for you: should the optimisation objective f3 and the S1 tie-break (`scripts/g10_select.py:93`) use the like-for-like term? Option A: yes (consistent with the corrected definition; G9 fronts and G10 selection are re-run, designs may change, a new untouched test is needed). Option B: keep f3 as is and report the corrected quantities beside it (nothing goes stale, but the headline changes from "more shield hours" to "fewer water-side, more PCM-side"). I recommend testing first on the saved points whether the corrected objective changes the front, then choosing.
- **Issue 5:** run the controls from an interior anchor (about 5-10 % fraction, where every radius is valid at constant mass; "x2" from 10 % to 20 %); replaces P2 and the thickness block in G11; chosen designs unchanged.
- **Issue 6:** report the chosen designs at bottom / centre / top for all regimes and arrangements (G11 has the explore years; extend to the select years and to the other O1 PCMs to check the PCM ranking does not depend on position) and add the anchor spread to the uncertainty budget next to the WP6 band. No position is chosen for being best. Decision for you: centre as nominal with the spread, or the range only.
- **Issue 3:** add paired delivered-energy and delivered-volume-at-45 C metrics for the evening scenario (the fields `serve_E_del45_kWh` and `vol_ge_target_kg` already exist in `src/metrics/tes_metrics.py`) and a volume-normalised comparison to test the displacement explanation. tau_serve stays in the report as measured.
- **Issue 1:** declare the corner step as a documented method step in `docs/03_OPTIMISATION_PIPELINE.md`; recompute the G9 grid check with and without it for all nine pairs from saved files; report both.
- **Issue 2:** diagnostic widened runs (fraction cap 30 %; R_in above 40 mm only if a capsule-size source is found), then label designs "boundary-limited" or re-search. Widening is reported, not adopted silently.

### 18.4 Downstream results that become stale if a fix changes a design (nothing changed yet)
Issue 4 option A and issue 2 with a re-search: `g9_points_*`, `g9_grid_check.csv`, `g9_seed_stability.csv`, `g9_boundary_check.csv`, `g10_selection_r*.json`, `g10_selection_candidates_r*.csv`, `g11_ablation_r*.csv`, `results_registry.csv`, `docs/04_RESULTS.md`, `obj3_environment_contract_rajasthan_v2.json`, the plots; `g10_heldout_results.csv` is not re-run and stays as the used pre-fix test. Issues 1, 3, 5, 6 (reporting and diagnostics): only the registry, `04_RESULTS.md`, plots and docs.

### 18.5 Held-out policy (confirmed by the user)
`g10_heldout_results.csv` (run `heldout_96d878ef8f24`, years 2024-2025) stays on record as "pre-fix test, used". If any fix changes a selected design: re-select on 2021-2023, then test on data not yet used (other member points of the same clusters, or a leave-one-year-out check on years not used to decide the new design), labelled as such. 2024-2025 will not be presented as untouched again. The lock file is not touched.

### 18.6 Sources, verification level and search record
**Local, opened (PDF text extracted with `pypdf` into the scratchpad):**
- Eldokaishi et al. 2022, Applied Thermal Engineering 204:118009 (`.claude/Sources/pdfs/Modeling of water-PCM solar thermal storage system.pdf`): abstract and introduction read (**partly read**). Its introduction reports, as secondary citations of Mazman, Mehling, Najafian, Cabeza, Abdelsalam, Suresh and Saini, that PCM modules at the top of a stratified tank were studied, that Mehling et al. found a 20-40 % storage-density increase with PCM at the top, that Najafian et al. found the best module location near the top, and that larger PCM fractions improved stratification. These are second-hand statements; the primary papers were not opened.
- Avargani et al. 2021, Sustainable Energy Technologies and Assessments 47:101350 (`Integrating paraffin phase change material in the storage tank...pdf`): abstract, introduction and set-up lines read (**partly read**). The PCM is a flow-through packed bed (bed length 0.6 m, radius 0.15 m, porosity 0.49) filling the tank, a different geometry from a 3-layer stack in a hot-water tank; it does not settle where a stack should sit.
- `.claude/Sources/*_summary.md` and extracts: keyword searches (stratification and position; overheating and stagnation; retention and draw-off). Matches in the AlMamun 2023, Abdellatif 2025, Eldokaishi 2022, Odoi-Yorke 2025, Chen 2025 and Singh 2025 summaries were read only at the matching lines (**snippet level**); they give stratification and PCM-in-tank context but no quantitative position result. I did not open all 93 papers; the searches covered the 66 top-level files plus `extracted_papers/` and `_extra_text/` text, and PDFs without an extract (for example the mantle-tank and shallow-PCM papers) were not searched.
- IS 12976:2023 and Chen 2025 were read earlier in this project; not re-read here.

**Web (WebSearch only; no page opened, so every item is snippet level).** Terms: "PCM module position stratified solar water heater storage tank top location capsules thermal performance 2022..2025"; "overheating stagnation phase change material solar water heater tank temperature limit 2023 2024"; "optimum on the boundary of design space surrogate-assisted optimisation bound handling expand search space Bayesian optimization"; "held-out test set reuse after model change adaptive data analysis overfitting test set holdout reuse"; "hot water draw-off test PCM storage tank delivered energy above 45 C metric stratification evaluation EN 12977 draw-off energy". Results: a 2022 Journal of Energy Storage CFD study of PCM in a mantle tank (position, amount and melting temperature varied; the snippet says stratification and outlet temperature improve, not which position); a 2019 Renewable Energy study of PCM-ball position against flow rate; Dwork et al. 2015 and Feldman, Frostig and Hardt 2019 on reusing a holdout set (standard remedy: a fresh holdout); BE-CBO (ICML 2024) and boundary-update surrogate methods on optima at constraint boundaries (none confirmed to extend variable bounds); Ranilovic and Grozdek 2020 on PCM overheating protection of collectors; a Cyprus University of Technology draw-off study of 50 l PCM tanks (1-6 l/min). No source was found that defines a "delivered energy above 45 C" metric under EN 12977. Nothing from the web is cited as a result in this project until a page is opened.

### 18.7 Papers and data needed (not guessed)
1. Mazman et al. 2009, Mehling et al. 2003, Najafian et al. 2015 (primary papers on PCM position in a stratified tank), to turn the second-hand "near the top" statement into a checked one.
2. The 2022 Journal of Energy Storage mantle-tank PCM position paper, for the direction and size of the position effect.
3. EN 12977-3 or ISO 9459 draw-off test definitions (or the SPF stratification-efficiency papers) for an accepted delivered-energy or retention metric.
4. A vendor catalogue of spherical PCM capsules (outer diameters above 82 mm, fill fraction) to justify or move the 40 mm inner-radius bound.
5. A source for PCM volume fractions above 20 % in domestic tanks (Suresh and Saini 20-80 % is named in Eldokaishi's introduction; primary paper not opened) and for how capsule baskets are mounted in commercial tanks.
6. Anything in `openfoam_cfd/` (read-only; not opened in this pass) that fixes where a capsule bed sits.

### 18.8 Status table (to be updated as each issue is closed)
| Issue | Proposed class | Status | Evidence file |
|---|---|---|---|
| 1 corner seeding | method gap | not started | `g9_points_r*_p*.csv`, `g9_grid_check.csv`, this section |
| 2 box-edge optima | finding + method gap | not started | `g9_boundary_check.csv`, `g7_max_packing_fraction.csv` |
| 3 tau_serve | finding + measurement gap | not started | `g3_night_daily_r*_plain.csv`, `g10_heldout_results.csv`, `g11_ablation_r*.csv` |
| 4 overheating hours | defect (metric definition) | not started | `src/optimize/evaluate.py:61,106`; re-simulation in 18.2 |
| 5 controls | method gap | not started | `g11_ablation_r*.csv`, `g7_sensitivity_r*.csv` |
| 6 stack position | method gap + finding | not started | `g11_ablation_r*.csv`, `tank_model_multinode.py:80` |

Note: the water-side and PCM-side shield-hour figures in 18.2 row 4 come from an interactive re-simulation that was not saved to a file. A saved script will regenerate them before any is quoted in a report.

## 19. Issue 4 - shield hours (closed 2026-10-27, option B approved by the user)

**Classification:** defect in the metric definition (accounting), not a shield bug. **Status:** fixed as a measurement; f3 and all G9-G11 results unchanged.
- **Mechanism:** `src/optimize/evaluate.py:61,106` defines `d_overheat = (shield_water_h + shield_pcm_h) - plain shield_water_h`. `shield_pcm_h` counts hours in which any PCM node is at or above 62 C with hotter water around it and its heat exchange is switched off (`src/simulation/tank_model_multinode.py:323-328`); a water-only tank has no such term, so the sum is positive by construction.
- **What changed:** new `scripts/g13_issue4_shield_split.py` (run per regime, three runs, about 2 min) writes `results/g13_shield_split_r{0,1,2}.csv` (96 rows: chosen design and the best design of each other O1 PCM, explore 2016-2020 and select 2021-2023). Regression: the chosen designs' select-year mean of the stored `d_overheat` is reproduced exactly (424.694777 / 193.184794 / 360.717731 against `g10_selection_r*.json`). `scripts/g12_registry.py` and `scripts/g12_results_doc.py` now carry the split (registry rows `shield.*`; section 1b of `docs/04_RESULTS.md`); `docs/01, 05, 06, README` reworded. No limit, shield threshold, physics or objective was touched.
- **Result (select-year mean, chosen designs):** water-side shield hours PCM vs water-only 482.9 vs 648.1 (r0), 571.7 vs 796.2 (r1), 482.2 vs 662.0 (r2): d_shield_water -165.3 / -224.5 / -179.8 h/yr. PCM-side throttle 590.0 / 417.7 / 540.5 h/yr. Peak water 72.4 / 72.2 / 72.2 C with PCM vs 73.1 / 73.4 / 73.0 C water-only. In 96 of 96 design-years the water-side hours are lower with PCM (including all non-chosen PCMs, whose PCM-side throttle is larger: up to 1,139 h/yr mean).
- **Where "more overheating hours" disappears and why:** it disappears when only the water side is compared like for like; the cause was summing a PCM-only throttle into the PCM tank's count. What remains as a reported finding: PCM-side throttle hours of 418-1,139 h/yr (means) with the PCM peak below 65 C, i.e. the capsules are full for hundreds of hours and charging is held back (a design-capacity statement, not an exceedance).
- **Not done / limits:** the held-out file (`g10_heldout_results.csv`) has no split and was not re-run (those years are used and locked). The water-side comparison depends on the 72 C top-node guard in the frozen `system_config_shared.yaml`; it was not varied. Option A (re-defining f3) was not taken, so fronts and selections are not stale.
- **Stale downstream results:** none. Sources: code and saved files only (no paper needed).

## 20. Issue 5 - controls that can see an effect (closed 2026-10-27)

**Classification:** method gap in the control design (G11 ran both controls from the capped, chosen design). **Status:** fixed as a method step; chosen designs and G9-G11 results unchanged.
- **Anchor declared before running:** the middle levels of the S1 screening grid, R_in 25 mm, outer PCM fraction 10 % (70 capsules), flow 0.030 kg/s, staggered, stack centre, the regime's chosen PCM, explore years 2016-2020 only (no select or test year).
- **What changed:** new `scripts/g14_issue5_controls.py` (runs `run` and `design_from` from `scripts/g11_ablation.py`; output `results/g14_controls_r{0,1,2}.csv`, about 3 min for three regimes in parallel). Thickness at constant INNER PCM volume (count scales with (25/R)^3) for R 10-40 mm; fraction x0.5, x1, x2. Registry rows `ctrl.*` and section 5b of `docs/04_RESULTS.md` are generated from the files; `05` and `README` of `docs` reworded. G11 files are kept as they were.
- **First attempt, recorded:** x2 with N = 2 x 70 = 140 gave an outer fraction of 20.1 %, which the 20 % cap rejects (valid = False, all regimes). The control was then defined as min(2 N, largest count inside the cap) = 139 capsules (20.0 %), declared in the script docstring, and the whole script re-run (same numbers for the other rows; deterministic).
- **Results (change in g_window against the anchor, kWh; band in brackets):**
  - fraction x2: +43.8 (15.1) / +30.8 (10.0) / +36.3 (15.7): positive control passes in every regime; x0.5: -24.8 / -19.7 / -22.2.
  - thickness at constant mass, R 10 / 15 / 20 / 30 / 40 mm: r0 -28.1 / -16.2 / -8.5 / +4.0 / +3.8; r1 -31.0 / -21.3 / -11.4 / +6.4 / +8.1; r2 -29.6 / -19.4 / -10.6 / +5.8 / +9.1. So R 10 and 15 mm are clearly worse in every regime (R 20 mm only in regime 1); R 30 and 40 mm are inside the band of R 25 mm in every regime.
  - anchor g_window: 41.5 / 33.1 / 36.6 kWh (about 40-45 % of the chosen 20 % designs' 95-101 kWh, consistent with the fraction response).
- **Consequence for issue 2:** at constant mass the gain is flat from R 25 to 40 mm, so the R_in = 40 mm edge optimum is a plateau (the optimiser went to the edge because nothing penalises it), not a sharp peak that a wider box would move. This is to be tested directly in issue 2, not assumed.
- **Limits:** one anchor per regime, one PCM, explore years only; outer volume (and displaced water) varies from 0.097 to 0.115 of the tank across radii, a confound that is shown in the CSV (`outer_fraction`) and not removed; the sign of the radius effect at other anchors is untested.
- **Stale downstream results:** none. Sources: code and saved files only.

## 21. Issue 6 - stack-position dependence (closed as a reported finding plus uncertainty entry, 2026-10-27)

**Classification:** method gap (the position is an undeclared mounting assumption) plus a finding (the level of the gain depends on it). **Status:** quantified and added to the uncertainty budget; no position chosen; the model default (centre) is kept only as the nominal case.
- **Where it is set:** `configs/design_space.yaml:23` (`stack_anchor: center`) -> `src/optimize/evaluate.py:53,94` -> `src/simulation/run_case.py:45,122` -> `src/simulation/tank_model_multinode.py:70-88` (`z0` for bottom / top / center). The chosen stacks are 3 layers of 12 capsules, 0.252-0.254 m of the 0.634 m tank height (40 %).
- **What changed:** new `scripts/g15_issue6_anchor.py` (three runs in parallel, about 15 min) writes `results/g15_anchor_r{0,1,2}.csv` (288 rows: 4 frozen designs x 3 positions x explore and select years, per regime; nothing re-optimised). Regression: the centre rows reproduce the saved explore and select g_window of the chosen designs to 1e-11 kWh. Registry rows `anchor.*` and section 5c of `docs/04_RESULTS.md` are generated from the files; `docs/05` and `README` reworded.
- **Results (chosen design, select years, g_window kWh, bottom / centre / top):** r0 72.6 / 99.4 / 118.3; r1 58.0 / 94.3 / 114.1; r2 60.9 / 94.9 / 116.0. Range 45.7 / 56.1 / 55.0 against bands 15.1 / 10.0 / 15.7. Smallest gain of any kept design at any position: 41.6 kWh. Best PCM per regime identical at all positions; its margin over the runner-up (bottom / centre / top): r0 11.6 / 14.7 / 16.1 (band 15.1), r1 15.2 / 18.2 / 21.7 (band 10.0), r2 9.0 / 9.2 / 16.4 (band 15.7), i.e. inside the band in regime 0 at the bottom and centre and in regime 2 at the bottom and centre. Regret of the chosen design against the best of the four saved designs: r1 22.2 and r2 22.0 kWh at the bottom (same PCM, different flow and count), 0-4.5 kWh elsewhere. So the SIGN of the gain and the best PCM are robust, the LEVEL is not, and the chosen designs are not anchor-robust at the bottom position.
- **Uncertainty budget:** the stack position is treated as a model-form range (not a random error, so not added in quadrature): the headline reads "g_window 94-99 kWh at the centre (band 10-16 kWh) and 58-73 / 114-118 kWh at the bottom / top".
- **Sources (verification level):** Eldokaishi et al. 2022 introduction (partly read; second-hand statements that PCM near the top is best, Mehling +20-40 % storage density, Najafian best location near the top). Izgi and Arslan 2022, Journal of Energy Storage 52 (abstract only, read through the publisher-repository page https://avesis.bozok.edu.tr/yayin/af9f8d8b-a2f9-4838-9109-e7bda7a2de51/effect-of-phase-change-material-on-thermal-stratification-of-solar-hot-water-tank-with-a-mantle-a-numerical-analysis): 3D CFD of PCM tubes in a mantle tank during discharge; PCM at the top gave the largest benefit (outlet +4.98 C, 19.6 %) and the best stratification (Case 7, 56 tubes at the top). Direction agrees with this model's top > centre > bottom order; it comes from a different tank (mantle, tubes) and a discharge-only test, so it supports the existence and direction of the effect, not the size. Not used to pick the top position.
- **Not resolved / papers still needed:** the real mounting position of a capsule bed in a commercial tank (basket location) and a source that settles it (section 18.7 items 1, 2, 5, 6). A full-height packed-bed layout (as in Avargani 2021, bed filling the tank) is not representable in the current packing engine and was not tried.
- **Stale downstream results:** none (reporting only).

## 22. Issue 3 - night-serve duration (closed 2026-10-27: explained and re-measured; part remains a finding)

**Classification:** finding with a measurement gap. **Status:** decomposed with saved diagnostics; no metric was redefined and tau_serve is still reported as measured.
- **Floor effect (confirmed):** the evening scenario draws far more than the 50 L tank holds, so the mean minimum outlet temperature is about 25 C and tau_serve about 0.5-0.8 h for every tank (`g3_night_daily_r0_plain.csv`; `g16_serve_r*.csv`).
- **What changed:** new `scripts/g16_issue3_serve.py` (per regime, night scenarios every 15th day, select years 2021-2023; about 40 min for the three regimes in parallel, plus a short re-run of the diagnostic case) writes `results/g16_serve_r{0,1,2}.csv` and `g16_serve_plain_40L_r{0,1,2}.csv`. Four cases per regime: `pcm` (the frozen chosen design), `plain` (official baseline), `pcm_L0` (latent heat set to 0) and `plain_40L` (diagnostic: water-only tank with the water volume cut by the capsule volume). First attempt: `plain_40L` was invalid because the real capsule layout does not fit a 40 L tank; the case was re-run with a small placeholder layout (the plain tank ignores capsules, G11 control N1) via `G16_ONLY=plain_40L`. Registry rows `serve.*`, section 5d of `04_RESULTS.md`, `docs/05, 06, README` updated; no other result changed.
- **Results (select-year means; plain / 40 L water / L=0 / PCM):**
  - tau_serve h: r0 0.719 / 0.558 / 0.602 / 0.638; r1 0.777 / 0.598 / 0.655 / 0.765; r2 0.692 / 0.537 / 0.584 / 0.658. PCM minus plain: -0.081 / -0.012 / -0.034 h; PCM minus the 40 L tank: +0.080 / +0.167 / +0.121 h.
  - E_del45 (energy delivered up to 45 C, kWh per scenario night): r0 0.986 / 0.708 / 0.894 / 1.247; r1 0.995 / 0.721 / 0.871 / 1.249; r2 0.998 / 0.717 / 0.884 / 1.246. PCM minus plain: +0.261 / +0.254 / +0.248; positive in all nine regime-years (+0.24 to +0.28).
  - tau_hold h (no draw): r0 44.0 / 31.8 / 35.0 / 51.4; PCM minus plain +7.4 (r0), +6.9 (r1), +7.1 (r2).
- **Where the "no benefit" disappears and why:** it disappears on energy (E_del45 +25 %) and on hold time (+7 h); the latent heat is the source (L=0 is below the water-only tank on E_del45 in every regime). It is the net of water displacement (-0.16 to -0.18 h) and a PCM benefit (+0.08 to +0.17 h) on tau_serve.
- **What remains as a finding:** against the same fixed 50 L tank the serve fraction (volume at 45 C or above) is lower with PCM (r0 0.081 vs 0.102, r1 0.105 vs 0.110, r2 0.087 vs 0.098) and tau_serve is not longer, because the capsules take water volume. This depends on the fixed-tank decision (tank volume is not tuned) and on the evening draw far exceeding the tank (IS 12976 sizing open item, section 18.7/05 item 2).
- **Limits:** one design per regime, select years, every 15th day; `plain_40L` has a different tank geometry (height and loss area scale with volume) and is a diagnostic, not a baseline; E_del45 counts energy up to the 45 C cap, so it measures delivery toward the target, not threshold compliance. The sources searched (section 18.6) define no accepted "energy above 45 C" metric; EN 12977-3 / ISO 9459 are still on the papers-needed list.
- **Stale downstream results:** none.


## 22. Legacy phase figures rebuilt for the current chain (2026-10-27)

**What was asked:** the 17 phase figures of the legacy set (the legacy plots folder (deleted), Phases 2-8) in `results/plots/`, same names and format.
**Status:** done, 17 of 17. Code: `src/plots/make_plots_phases.py` (new; `src/plots/make_plots_results.py` and its 9 `fig1..fig9` PNGs are unchanged). `python pipeline.py --state rajasthan --stage plots` now runs both modules.
- **Output:** `results/plots/static/<name>.png` (4.6 MB, tracked) and `results/plots/interactive/<name>.html` (80 MB, git-ignored through `.gitignore`; regenerate on demand). Figure guide with the data behind each one: `docs/plots/10_PLOTS.md`.
- **Data rules kept:** 11 figures only read saved files under `results/`. Six need simulation or a refit and cache it in `results/plots_data/` (rebuild with `--refresh`): the three Phase 3 figures and Gate 5 (explore year 2018, regime-0 chosen design and its water-only twin, 7 runs of about 20 s), the Phase 6 parity plot (5-fold out-of-fold predictions of each pair's selected surrogate, same split as `scripts/g8_s3_compare.py`), and the two Phase 8 figures (chosen design of each regime on the 5 explore + 3 select years, 24 runs, about 8 min on 3 cores). Held-out numbers come only from `g10_heldout_results.csv`; the module never calls the held-out loader and `_weather()` refuses any purpose other than explore or select.
- **Substitutions, because the old figure has no honest equivalent:** (1) Phase 8 Monte Carlo probabilities are replaced by shares of the 10 real weather years (steps of 0.1), and the P5-P95 interval figure by min-max and mean over the same years (10 values do not support percentiles, WP4). (2) Phase 6 feature importance is the ANOVA contribution of the screening runs (`g8_s1_anova_*`), not a surrogate importance. (3) Gate 5's second panel shows window delivered energy against flow, because pump energy is 0.0 kWh/yr (`pump_energy_meaningful = False`). (4) Gate 3 uses the G4 report designs (RT44HC, savE OM49, lauric acid), which were run before G6 restored the O1 shortlist; the figure says so and does not show the final chosen designs. (5) Phase 5 and 7 figures use the Sobol DOE, the active-learning logs and the dense grid instead of the 219-case DOE and the 60 surrogate candidates.
- **Defects found and fixed while building:** the `_ext` and `_ext2` active-learning logs repeat every earlier round, so concatenating them doubled the curves in the Phase 7 surrogate-error figure (the longest file per pair is used now, with training-set size on the x-axis); the Gate 1 log axis was unreadable (decade ticks now); a hourly f_melt series over 8760 points aliased into a solid block (folded to daily min / max / mean); two titles ran past the figure edge.
- **What the figures show (read from the saved numbers, not a new result):** chosen regime-0 design on 2018: delivered at 45 C in the 18:00-09:00 window 575 kWh against 475 kWh for the water-only twin; 295 of 365 days melt and refreeze completely; PCM peak 62.9 C against the 62 C shield bypass. Gate 5: latent heat -10 / +10 % changes charge energy 221.6 / 235.1 / 248.1 kWh (monotonic); flow -50 % raises window energy to 603.6 from 575.3 kWh and +50 % lowers it to 567.5, the flow-independent collector artefact already flagged. Robustness: over the 10 years the chosen design clears the repeatability band, has positive window gain and stays at or below 65 C in every year, but it has extra overheating hours against the water-only tank in every year (share of years without extra overheating = 0.00 in all three regimes), the same finding as issue 4. Gate 3 (G4 test designs, 2018): the multi-node tank gives a lower solar fraction than the single-node tank in every case (30.2-33.1 % against 35.7-39.5 %), and PCM adds 0.0-0.4 percentage points.
- **Not done / limits:** the figures are Rajasthan only (`make_plots_phases.main` is not state-parameterised); the Phase 3 time series is one explore year of one regime; no figure uses the held-out years except through `g10_heldout_results.csv`. The old `src/plots/make_plots.py` is left in place but cannot run (it needs the retired `phase5_design_cases.parquet` and `phase6_surrogate_models.pkl`).

## 23. Issue 2 - box-edge optima (diagnostic closed 2026-10-27; reported as "boundary-limited on the PCM fraction", no bound changed)

**Classification:** finding plus method gap (the WP6 widening test had not been run). **Status:** test run; the approved box (`configs/design_space.yaml`) and every G9-G11 result are unchanged; no bound was widened in the pipeline.
- **What changed:** new `scripts/g17_issue2_widen.py` (about 20 min for three regimes, run serially while other jobs ran) writes `results/g17_widen_r{0,1,2}.csv`: frozen chosen design of each regime, explore years, stack centre, geometry still checked exactly, paired against exact water-only runs at the same flow (so flows above 0.050 kg/s are possible). Blocks: radius 20-60 mm at the chosen fraction; fraction 10-40 % at the chosen radius; joint R 40/50 mm x fraction 25/30/40 %; flow 0.050-0.080 kg/s. Wider geometry bounds exist only inside the script. Registry rows `widen.*`, section 5e of `docs/04_RESULTS.md`, `docs/02, 05, README` updated.
- **Regression:** the chosen-design rows reproduce the saved explore g_window to within the count-rounding differences (R 40 mm at the chosen fraction: 100.46 / 95.26 / 98.86 vs saved 101.14 / 95.29 / 98.86; fraction 20 % at the chosen radius: 101.16 / 95.25 / 98.86).
- **Results (change in g_window vs the chosen design, kWh; bands 15.1 / 10.0 / 15.7):**
  - radius at the chosen fraction: R 30 mm -6.3 / -16.1 / -13.6; R 45 mm -7.4 / -11.2 / -6.7; R 50 mm -27.7 / -36.3 / -26.7. The 40 mm edge is at or near an interior optimum (coarse sampling at 30, 40, 45 mm), so the radius bound is not limiting.
  - flow upper bound: 0.080 kg/s gives +3.3 / +3.9 / +4.2, inside the band, so not limiting.
  - PCM fraction at the chosen radius: 25 % +24.0 / +21.3 / +21.7; 30 % +49.5 / +43.5 / +44.9; 40 % +100.6 / +84.3 / +87.9: beyond the band in every regime and still rising; PCM peak 62.3-63.7 C and water peak 72.2-72.6 C (all feasible against 65 / 75 C). Joint widening with R 50 mm is worse than R 40 mm at the same fraction.
  - lower bounds (R 10 mm, fraction 2 %): 0 % of every final front (`g9_boundary_check.csv`), not binding.
- **Verdict:** the designs are boundary-limited on the 20 % fraction cap. WP6 acceptance item (iv) ("no selected design sits on an unjustified bound") is therefore NOT met for that bound: its only source in the files read is the 10-20 % range of Chen 2025, and the packing engine accepts 28-48 % at R 40 mm. The remaining optimum edges (radius, flow) are not boundary artefacts by this test.
- **Options (no choice made, no bound changed):** (a) keep 20 % and state the result as "best within a 20 % cap" (sourced, comparable with Chen 2025); (b) raise the cap to 30 % (inside the packing limits and near the 28-48 % range) and re-run G9-G11, then re-select on 2021-2023 and test on data not yet used (the 2024-2025 years stay labelled used); (c) report the cap-sensitivity (about +4 to +5 kWh per percentage point of PCM fraction) as is. Raising the cap would also lower the water volume further, and the displacement penalty seen in issue 3 grows with it.
- **Limits:** diagnostic at one frozen design per regime, explore years, centre anchor; radii above 40 mm have no capsule-size source (vendor catalogue is on the papers-needed list, section 18.7); the radius sampling is coarse; no re-search was run, so a joint optimum elsewhere in a widened box is untested.
- **Stale downstream results:** none (no pipeline change).

## 24. Issue 1 - the box-vertex step (closed 2026-10-27: declared as a method step; both variants reported)

**Classification:** method gap (the step was added post hoc, after regime 0 PCM 1 failed twice; not in the plan, no "vertex" or "corner" text in `DOCUMENTATION PORTAL/OBJECTIVE2_REDESIGN_PROPOSED_PLAN.md`). **Status:** declared; with/without comparison for all nine pairs saved; G9 criterion and band unchanged.
- **What changed:** `scripts/g9_s4_s5.py` gained `G9_OUTDIR` (output directory; default unchanged). New `scripts/g18_issue1_compare.py` writes `results/g18_issue1_with_without.csv`. Eight pairs were re-run without the step (`G9_WARM=1 G9_MAX_ROUNDS=8`, outputs in `results/issue1_novert/`, about 3 h of wall time for eight runs three at a time); regime 0 PCM 1 reuses its historical 8-round no-vertex run. First attempt, recorded: without `G9_MAX_ROUNDS` the warm start added no rounds (outputs identical to base); those files are kept in `issue1_novert/_invalid_run1_rounds_not_extended/` and were not used. The earlier session's background job was stopped when it ended; the eight corrected runs all finished (log lines for all eight).
- **Results (dense-grid epsilon gap on g_window, band 13.8 kWh; base / without step / with step):** r0_p1 24.9 FAIL / 23.5 FAIL / 3.1 pass; r1_p1 5.9 / 5.0 / 1.8 (all pass); r2_p1 0.4 / 0.2 / 0.2 (all pass). Hypervolume against the best state per pair: higher with the step in six of nine pairs (+0.5 % to +4.7 %), 0.1-0.2 % lower in three (r1_p2, r1_p3, r2_p1).
- **Uniformity:** the step is applied to every pair, regime and seed by the same code, before any refit, from the approved box only. It was not applied selectively; its effect is measured for all pairs.
- **Caveats:** regime 0 PCM 1 has 8 rounds without the step and 11 with it (its vertex run continued from the no-step state); the vertices are part of the dense grid, so the grid check is not fully independent of the step; only rank-1 pairs have a grid, so pairs 2 and 3 are compared by hypervolume only.
- **Stale downstream results:** none (the selection already used the vertex runs).

## 25. Six-issue summary (2026-10-27)

| Issue | Class | Outcome | Evidence file | What remains |
|---|---|---|---|---|
| 1 corner seeding | method gap | declared; with/without run for all 9 pairs; only regime 0 PCM 1 needs it | `g18_issue1_with_without.csv`, section 24 | grid check partly dependent on vertices; r0_p1 round counts differ |
| 2 box-edge optima | finding + method gap | tested: fraction cap limits (+21 to +101 kWh at 25-40 %), radius and upper flow edges do not; designs labelled boundary-limited, no bound changed | `g17_widen_r*.csv`, section 23 | decision on the 20 % cap (guide); vendor source for R above 40 mm |
| 3 tau_serve | finding + measurement gap | explained (displacement vs PCM benefit); evening energy gain +0.25 kWh/night, hold +7 h; volume and time at 45 C not better than the fixed 50 L tank | `g16_serve_*.csv`, section 22 | serve fraction/time remain a finding |
| 4 overheating hours | defect (metric definition) | fixed as a measurement: water-side hours lower with PCM in 96/96 design-years; PCM-side throttle reported separately; f3 unchanged (option B) | `g13_shield_split_r*.csv`, section 19 | held-out file has no split |
| 5 controls | method gap | re-run from an interior anchor: fraction x2 passes (+31 to +44 kWh), thickness informative below 25 mm and flat above | `g14_controls_r*.csv`, section 20 | one anchor, outer-volume confound |
| 6 stack position | method gap + finding | quantified: range 46/56/55 kWh vs bands 15/10/16; sign and best PCM robust; chosen designs not robust at the bottom position (regret 22 kWh in r1, r2) | `g15_anchor_r*.csv`, section 21 | actual mounting position needs a source |

Held-out years: no design changed, so no re-selection and no new test were needed; 2024-2025 stay labelled "pre-fix test, used" (the lock is untouched). Option decisions left for the user: the 20 % cap (issue 2) and whether f3 should use the like-for-like water term (issue 4 option A, not taken).

## 26. DECLARED CHANGE v3: PCM fraction cap 20 % -> 30 % (started 2026-10-27)

**Decision (user, 2026-10-27):** raise the cap to 30 %, re-run G8-G11 for all regimes, re-select on 2021-2023, test once on untouched data; 2024-2025 stay labelled used.
**Why:** issue 2 (section 23): the 20 % cap was the only bound that limited the result (gain +43 to +49 kWh at 30 % in the widened-bound diagnostic).

What changed (and only this): `configs/design_space.yaml` fraction max 0.20 -> 0.30 (version string `design_space_o2_v3_cap30_2026-10-27`); the scripts that hardcoded the 20 % end
(`g8_s1_screening` levels 2/16/30 %, `g8_s2_doe` and `g9_s4_s5` Sobol/decoder mapping 2-30 %, `g9_s6_grid` 8 fraction levels 2-30 % = 720 designs, `g9_assess` boundary test at 30 %, `g11_ablation` fraction list and cap).
Not changed: tank, collector, demand, O1 shortlist, model physics, shield limits, PCM 65 C and water 75 C limits, radius and flow ranges, the metrics.
G8 (screening, DOE, surrogate) must be re-run as well as G9-G11, because the surrogate has to cover the new box (the user asked for G9-G11; the surrogate input data is a necessary consequence, not an extra choice).
Baseline (water-only flow grids) and the G7 sensitivity are unaffected by the cap and are not re-run.

**Archive (nothing deleted):** `results/v1_cap20/` = copy of all v1 results, plus `docs_snapshot/` (docs, this log, the config, pipeline.py). Tests: 83 pass with the new cap (4 tests updated for 30 %).

**Untouched test data.** All of 2016-2025 was already assigned, so the new one-shot test uses 2011-2015 at the same three medoid points (NASA POWER hourly, same request as the original download,
`scripts/g19_fetch_test2_weather.py`, 15 files, approved by the user in chat: "Earlier years"). Roles are now: 2011-2015 `test` (one shot, untouched), 2016-2020 explore, 2021-2023 select, 2024-2025 `used_test_v1`
(accepted for no purpose by `src/weather/roles.py`). QC of the new years only (inventory, no simulation): 15/15 accepted, 100 % valid, no gaps, 0 filled hours. The v1 lock and `g10_heldout_results.csv` are moved into
`results/v1_cap20/` immediately before the new test (copies already there); the new test writes `results/g10_heldout_results.csv` and a new lock.

Chain launched in the background: `pipeline.py --stage {screening,doe,surrogate,band,optimize,select} --allow-invalidate --jobs 4` (log in the session scratchpad; outputs overwrite results/g8_*, g9_*, g10_selection_*).

### 26.1 Chain result and start of the v3 one-shot test (2026-10-28)
Chain (screening, doe, surrogate, band, optimize, select) finished 03:37 without failure. G9 grid check: within band in all three regimes (epsilon g_window 0.71 / 11.27 / 0.23 kWh vs band 19.4).
Boundary check on the final fronts (rank-1 PCM): inner radius at 40 mm 100 / 0 / 97 %, fraction at the 30 % cap 56 / 0 / 83 % (r0, r1, r2 of p1) - the designs are STILL boundary-limited at the new cap in regimes 0 and 2 (details in 04_RESULTS after regeneration).
Selected (select years 2021-2023): r0 savE OM55 R 39.5 mm f 28.4 % flow 0.0155 staggered; r1 PureTemp 60 R 40 mm f 29.6 % flow 0.049 single-layer; r2 PureTemp 58 R 40 mm f 29.6 % flow 0.0236 single-layer.
Before the test: the v1 lock and the v1 `g10_heldout_results.csv` were MOVED into `results/v1_cap20/` (sha256 of the archived copies verified identical first; the lock is never deleted to retry, this is the visible, logged act the `roles.py` docstring asks for). The v3 test is then run once on 2011-2015.

### 26.2 v3 results (2026-10-28)
Gates (all from saved files; full tables in `docs/04_RESULTS.md`):
- **G8/G9:** screening, DOE (1,152 designs), surrogate comparison, band and active learning (7-8 rounds, vertices included from the start) all ran without failure. G9 dense-grid check (720 designs per regime, rank-1 PCM): within band in all three regimes at the first attempt (epsilon g_window 0.71 / 11.27 / 0.23 kWh vs band 19.4); seed spread inside the band for all 9 pairs; the grid contains the vertices, so this is not fully independent evidence. Boundary check: still boundary-limited (radius 100 / 0 / 97 % of the fronts at 40 mm, fraction at the 30 % cap 56 / 0 / 83 %).
- **G10 selection (2021-2023):** same PCM in every regime as in v1. r0 savE OM55 R 39.5 mm f 28.4 % flow 0.0155 staggered, 130.4 kWh/yr; r1 PureTemp 60 R 40 mm f 29.6 % flow 0.049 single-layer, 137.4; r2 PureTemp 58 R 40 mm f 29.6 % flow 0.0236 single-layer, 140.6 (v1: 99.4 / 94.3 / 94.9).
- **One-shot test, untouched 2011-2015 (run `heldout_3242a7f4fd8a`, 9 designs x 5 years):** chosen 137.5 / 145.7 / 149.3 kWh/yr (v1 test on 2024-2025: 96.4 / 89.5 / 91.0), every design-year gain positive (minimum 95.7), PCM peak at most 64.1 C, water peak at most 73.3 C. Regime 0: the runner-up Palmitic-stearic acid/Expanded graphite is tied with the chosen design (138.0 vs 137.5, band 21). Regimes 1 and 2: chosen ahead by +26.8 and +11.5 kWh over the best other PCM (the latter inside the band of 21.9). Like-for-like water-side shield hours are lower with PCM in all three regimes (543 vs 715, 541 vs 858, 473 vs 733 h/yr); PCM-side throttle 376-740 h/yr. tau_serve gain -0.12 / +0.03 / -0.01 h (still about zero), tau_hold +8 to +10 h.
- **G11 ablations:** negative controls zero, latent-heat = 0 control gives -40 to -57 kWh, count sweep still rising at the cap (+16.5 / +19.6 / +21.1 kWh from 25 to 30 %).
Not re-run on v3: the six-issue diagnostics (g13-g18); they stay labelled v1 in `04_RESULTS.md`. Not claimed: the true optimal PCM amount, anything above 30 %. 2024-2025 stay labelled used (role `used_test_v1`). Tests, report, handoff and plots re-run; see the last entry below.
Caveat: the test years 2011-2015 are different (higher-GHI) years from 2024-2025, so v1 and v3 held-out levels are not like for like; v1 vs v3 select-year numbers are on the same years 2021-2023.

## 27. FUTURE PLAN (not started, decision 2026-10-28): test a higher PCM fraction cap (proposed 40 %)

**Status: planned only. Nothing was run and nothing in the code or configs was changed for it.** The current result is v3 (cap 30 %, section 26).
**Why:** the v3 designs are still at the cap (chosen fraction 28.4-29.6 %; 56 / 0 / 83 % of the rank-1 fronts at the cap in regimes 0 / 1 / 2; the count sweep still rises +16.5 / +19.6 / +21.1 kWh from 25 % to 30 %). The earlier widened-bound diagnostic (section 23) had also shown gains up to 40 % with PCM and water peaks still inside 65 / 75 C.
**What it would be:** a new declared change, same procedure as section 26.
1. Snapshot v3 into `results_v3_cap30/` (copy, delete nothing).
2. Change `pcm_volume_fraction.max` in `configs/design_space.yaml` and the scripts that hardcode the cap (same list as section 26: `g8_s1_screening`, `g8_s2_doe`, `g9_s4_s5`, `g9_s6_grid`, `g9_assess`, `g11_ablation`, `tests/test_design_space.py`). Nothing else changes (tank, collector, demand, shortlist, physics, shield limits, radius and flow ranges).
3. Re-run screening, DOE, surrogate, band, optimise (with the box-vertex step), selection on 2021-2023, then the ablations.
4. New one-shot test on years never used before. All of 2011-2025 is now assigned (2011-2015 used by v3, 2024-2025 used by v1), so new data are needed: proposed 2006-2010 at the same three medoid points from NASA POWER with the same request (`scripts/g19_fetch_test2_weather.py` is the template). The download needs the user's approval at that time. Give the new years their own role in `src/weather/roles.py` and mark 2011-2015 `used_test_v3`, accepted for no purpose.
5. Regenerate registry, results document, plots and the Objective 3 handoff; archive the v3 lock and held-out file before the new test, as in section 26.1.
**Estimated time (from the v3 run):** about 11-12 h of computing (screening 13 min, DOE 1.6 h, surrogate and band 8 min, active learning plus dense grid 8-10 h, selection 15 min, test under 10 min, ablations 7 min) plus about 1 h of documentation work.
**Risks to state beforehand:** packing accepts only 28-48 % at R 40 mm (radial fewest), so some designs near the new cap will be geometry-rejected; the displaced water volume reduces the tank's water further, which the tau_serve finding already shows; no source read covers fractions above 20 % (Chen 2025 gives 10-20 %), so the cap beyond that is a modelling choice, not a literature value. If the optimum stays at the new cap again, the result is reported as boundary-limited and the search is stopped there rather than continued.
**Not done in this plan:** the six-issue diagnostics (g13-g18) on the v3 designs; they could be re-run on the final version only.

## 28. Cleanup and renaming (2026-10-28, user request)
- Deleted `archive_pre_redesign/` (78 files, 121 MB: old results, logs, old entry points, old plots). Kept only `data/legacy/phase7_deployable_design_per_regime.csv` (byte-identical copy), the one table that `scripts/g2_timestep_convergence.py`, `g3_metrics_report.py` and `g4_multinode_report.py` still read.
- Dropped the word "redesign" from folders, files and text: `results/redesign/` -> `results/`, `results/redesign_v1_cap20/` -> `results/v1_cap20/`, `docs/redesign/` -> `docs/`, `docs/REDESIGN_PROGRESS.md` -> `docs/PROGRESS.md`, `docs/plots/10_REDESIGN_PLOTS.md` -> `10_PLOTS.md`, `docs/pre_redesign_result_hashes.sha256` -> `docs/legacy_result_hashes.sha256`, `configs/design_space_redesign_v2.yaml` -> `configs/design_space.yaml`, `data/weather_redesign/` -> `data/weather/point_years/`, `data/weather_redesign_raw_test2/` -> `data/weather/raw_test_2011_2015/`, `src/plots/make_plots_redesign.py` -> `make_plots_results.py`, `make_plots_redesign_phases.py` -> `make_plots_phases.py`. "pre-redesign" wording became "legacy".
- Left as they were: the external plan file name `OBJECTIVE2_REDESIGN_PROPOSED_PLAN.md` and the branch name `o2-redesign-rajasthan` (names outside this folder / the intended git branch), and the archived v1 snapshot contents in `results/v1_cap20/` (historical copies, their inner text still uses the old paths).
- Earlier entries of this log mention the old paths as they were at the time.

## 29. Legacy documents removed (2026-10-28, user request)
- Deleted the 20 documents that described the legacy pipeline: `docs/00_MASTER_CHANGE_PLAN.md`, `00_MASTER_OVERVIEW.md`, `01_PHASE1_*` ... `08_PHASE8_*`, `09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md`, `OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md`, and `docs/plots/00_INDEX.md`, `02..08_*_plots.md`. All were tracked, so their text is in git history.
- Content still true for the current code, checked against it before moving: solver safeguards (differential-controller re-solve, stiffness sub-stepping, the two shield levels) and the further simplifications -> `01_MODEL_AND_METRICS.md` sections 3b, 4 (solar-fraction definition) and 6; geometry engine and rejection codes (including `below_min_pcm_fraction`) -> `02_WEATHER_AND_DESIGN_SPACE.md` section 4b; IS 12976:2023 quotes and the legacy resizing result, the 45 C vs 60 C delivery-temperature gap, the missing O2->O1 feedback and the RT80HC/RT82 track -> `05_LIMITATIONS_AND_OPEN_ITEMS.md` items for Dr. Deepika 2, 8 and 9. Legacy numbers are labelled as such.
- Not carried over: phase-by-phase results of the old chain (DOE, surrogate, Phase 7/8 selections, robustness), the stale Phase 0 climate-signature table, and the change plans; all describe outputs that no longer exist.
- The project `README.md` was rewritten as a short pointer to `docs/README.md`; its old body described the legacy pipeline.
