# Results — Rajasthan, Phases 0–8 (Objective 2 complete)

> **Update 2026-09-17:** capsule arrangement restored as a searched
> variable (single-layer/staggered/radial); simulator re-tagged
> `sim_v2_rajasthan`. See `docs/00_MASTER_CHANGE_PLAN.md` and
> `docs/09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md` §9 for the full change and
> `docs/0N_PHASEN_*.md` for current per-phase numbers — the narrative below
> predates this change and still describes `sim_v1_rajasthan`.

> **⚠ Update 2026-09-14: PCM now wins outright in ALL 3 regimes (not just
> Regime 0) — `select_deployable.py`'s selection rule was corrected.**
> Two changes now compound:
>
> 1. **2026-09-13 — safety shield as pipeline default.** A rule-based
>    overheat-protection shield (stop pump above 72°C water / block PCM
>    charging above 62°C — IS 12976:2023 §8.2's standard mechanism) is
>    `configs/system_config_shared.yaml`'s `safety_shield.enabled: true`
>    default, so Phases 5 (DOE) through 8 (robustness/handoff) all run WITH
>    the shield active. This alone let 60/60 Phase 7 candidates clear
>    temperature safety (up from 15/60, all plain-tank, unshielded).
> 2. **2026-09-14 — `apply_selection_rule()` re-ported from
>    `objective2-tamilnadu`.** The old rule still let the plain tank win
>    Regimes 1/2 via the pump-energy/PCM-mass tie-break, because PCM's
>    shielded energy edge over plain water is razor-thin (well inside the
>    5% Pareto tolerance) and the old rule tie-broke toward the lowest PCM
>    mass — zero. The corrected rule (Tamil Nadu's own 2026-09-13 scope
>    correction: Objective 2's stated problem presupposes a PCM design, so
>    the plain tank was always an internal diagnostic baseline, not an
>    eligible final answer) excludes the plain tank from the winner pool
>    entirely. Plain-tank rows still appear in `phase7_optimized_designs.csv`
>    as the diagnostic comparison baseline; they just cannot win.
>
> **Result: the deployable design is now a PCM in all 3 regimes** — RT45HC
> (regime 0), Paraffin/HDPE PCM6 (regime 1), Paraffin/HDPE PCM3 (regime 2) —
> each ~0.07–0.14% higher useful energy than the best plain-tank geometry the
> same search found, and **all 3 regimes are ROBUST** (P(temp-safe) = 1.00
> everywhere, up from the pre-shield 0.45–0.57) — see
> `phase7_deployable_design_per_regime.csv` and `phase8_robustness.csv`.
> `phase8_recommendation_cards.md` and `obj3_environment_contract_rajasthan.json`
> reflect this directly (both regenerated 2026-09-14, 00:25).
>
> A separate, still not-yet-adopted finding also exists: the frozen 50 L tank
> / 1.5 m² collector sizing (33.3 L/m²) is itself below IS 12976:2023's cited
> 37.5–100 L/m² range; resizing to the standard's 75 L/m² reference (112.5 L)
> makes every shortlisted PCM pass safety AND raises solar fraction, **with no
> shield needed at all** — see `fix6_standards_compliant_sizing_supplementary.csv/.md`
> and `docs/09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md` §7. Not folded into the
> numbers above (a frozen-shared-config change needs a coordinated 4-state
> re-run) — it is a second, shield-independent route to the same qualitative
> conclusion (PCM beats plain water once given a fair chance at safety), not
> a competing finding.
>
> The Phase-by-Phase sections below were written before this update and
> describe the pre-shield/pre-selection-fix pipeline mechanics (still
> accurate for Phases 0–4, and for Phase 5/6's own mechanics — DOE sampling
> and surrogate training did not change). **Phase 7 and Phase 8's result
> tables and inference prose below have been updated in place** to the
> current 2026-09-14 numbers; where an earlier finding is kept for the
> historical record it is explicitly labeled "superseded."

What every file in this folder contains, how it was produced, and what to
infer from it. Methodology and full background live in `../docs/`
(`00_MASTER_OVERVIEW.md` through `08_PHASE8_ROBUSTNESS_HANDOFF.md`); this
file is the output-and-inference companion, not a repeat of the methodology.

No Tamil Nadu results are checked in here yet — the project owner is
adding those separately. Everything below is Rajasthan-only.

---

## Phase 0 — `phase0_climate_signature_check.txt`

**Produced by:** `python check_climate_signature.py`
**Format:** plain text, one block per Level-A regime (cluster_id 0/1/2) + an overall verdict.

### What it contains

For each of Rajasthan's 3 climate regimes: mean daily GHI and ambient
temperature at the regime's medoid point, the Apr–Jun summer daily-max
temperature, a cross-check that the medoid point id and regime population
size match Objective 1's own `cluster_profiles_rajasthan.csv` /
`medoid_points_rajasthan.csv`, a data-cleanliness check (duplicate rows,
calendar gaps) on the multi-year daily weather file, and the frozen
`Tm_target_C` / `L_required_kJ_per_kg` design targets Objective 1 already
computed for that regime.

### Result

| Cluster | Medoid | Mean GHI (kWh/m²/d) | Mean T_a (°C) | Apr–Jun daily-max T_a (°C) | Duplicates / gaps | Verdict |
|---|---|---|---|---|---|---|
| 0 | RJP_0132 | 5.12 | 25.4 | 39.8 (abs max 47.6) | 0 / 0 | **PASS** |
| 1 | RJP_0202 | 5.40 | 26.2 | 40.3 (abs max 48.3) | 0 / 0 | **PASS** |
| 2 | RJP_0055 | 5.06 | 25.8 | 41.1 (abs max 49.0) | 0 / 0 | **PASS** |

**Overall: PASSED, 3/3 regimes.**

### Inference

The frozen weather under `data/weather/` is genuinely Rajasthan's, not a
mis-copied file from another state. Every GHI value sits inside the
3.0–7.0 kWh/m²/day dry-climate band and every summer daily-max sits
inside the 33–47 °C Rajasthan band; medoid ids and regime sizes match
Objective 1 exactly (no drift between what Objective 1 clustered and what
Objective 2 is simulating); and each daily file spans the full
2016–2025 record (3,653 days) with zero duplicate timestamps and zero
missing calendar days, so nothing downstream (Phase 3's year-long
simulation) can silently run on a truncated or double-counted year. This
clears the gate to proceed to Phase 1/2 configuration and geometry —
**it does not itself validate the simulator**, only the input weather.

---

## Phase 2 — `phase2_geometry_boundary_selftest.txt`

**Produced by:** `python pipeline.py --state rajasthan --stage geometry`
**Format:** plain text, one line per boundary case + a determinism verdict.

### What it contains

8 hand-picked boundary/edge cases run through the geometry+constraint
engine (`src/design/geometry.py` + `constraints.py`) **twice each**, to
check both (a) whether the engine correctly accepts/rejects each case and
(b) whether it is deterministic (same inputs → byte-identical output,
both runs).

### Result

```
min_diameter_min_count       valid=False reason=bounds_violation     deterministic=True
max_diameter_max_count       valid=True  reason=None                 deterministic=True
min_diameter_max_count       valid=False reason=bounds_violation     deterministic=True
max_diameter_min_count       valid=True  reason=None                 deterministic=True
mid_case                     valid=True  reason=None                 deterministic=True
flow_below_min               valid=False reason=flow_out_of_range    deterministic=True
flow_above_max               valid=False reason=flow_out_of_range    deterministic=True
oversized_diameter_for_tank  valid=False reason=bounds_violation     deterministic=True

All boundary cases deterministic: True
```

**Exit code 0 — all 8/8 deterministic.**

### Inference

The two `min_diameter_*` cases are rejected with `bounds_violation` for a
non-obvious reason worth stating explicitly: at the minimum capsule
diameter (0.02 m), the *derived* PCM thickness (`= diameter/2 = 0.01 m`)
falls below the independently-checked 0.02 m thickness floor in
`design_bounds_shared.yaml`. This is a real, designed-in interaction
between two bounds that both look reasonable in isolation — not a bug —
and it means the smallest nominally-in-range capsule diameter is not
actually usable on its own. `max_diameter_min_count` and `mid_case` both
validate, and the flow-rate and oversized-capsule cases reject for their
own distinct reason codes, showing the engine's reason codes correctly
discriminate between failure modes rather than collapsing everything to
one generic "invalid."

The result is **identical, line-for-line, to Tamil Nadu's own Phase 2
self-test** (only the printed state name differs) — direct evidence that
Phase 2 is genuinely state-agnostic, as the framework document requires,
rather than accidentally depending on some Rajasthan-only input. This is
a code/engine result, not a climate result — it says nothing about which
designs will perform well in Rajasthan's climate, only that the
constraint-checking machinery itself is correct and reproducible.

See `../docs/02_PHASE2_GEOMETRY_CONSTRAINTS.md` for the related finding
that the maximum PCM volume fraction reachable within these bounds is
12.9%, not the 15–20% seen in some cited literature baselines.

---

## Phase 3 — one-year simulation smoke runs

**Produced by:** `python pipeline.py --state rajasthan --stage simulate --cluster <N> [--pcm NAME --diameter D --count N --flow F | --no-pcm]`
**Format:** JSON, one file per case — the full metrics dict `run_case()` returns.

Six cases were run, covering all 3 regimes' plain-tank baseline plus three
PCM geometries in the hottest-Objective-1-rank-1 regime (Cluster 0, PCM
`RT50`). These are **smoke-test runs**, not a Phase 4 verification battery
— they confirm the simulator runs a full year without crashing/diverging
and give a first read on plausibility; they are not Gate 1–5 evidence.

### Files and headline numbers

| File | Cluster | PCM | Geometry (d, n, flow) | Solar fraction | Max water/PCM (°C) | Safety violations | Residual (% of E_collector) |
|---|---|---|---|---|---|---|---|
| `phase3_simulate_cluster0_baseline_noPCM.json` | 0 | none | (0.08, 19, 0.030) — default, unused (n_capsule forced to 0) | 0.5497 | 68.6 / 68.6 | 0 | 0.00030% |
| `phase3_simulate_cluster0_RT50_maxload.json` | 0 | RT50 | (0.08, 24, 0.025) — max reachable loading | 0.5507 | 69.1 / 69.0 | **896** | 0.00064% |
| `phase3_simulate_cluster0_RT50_mid_flow010.json` | 0 | RT50 | (0.04, 12, 0.010) | 0.5499 | 68.7 / 68.6 | **2,347** | 0.00036% |
| `phase3_simulate_cluster0_RT50_mid_flow050.json` | 0 | RT50 | (0.04, 12, 0.050) | 0.5499 | 68.7 / 68.7 | **3,142** | 0.00036% |
| `phase3_simulate_cluster1_baseline_noPCM.json` | 1 | none | (0.08, 19, 0.030) — default, unused | 0.5823 | 72.4 / 72.4 | 0 | 0.00045% |
| `phase3_simulate_cluster2_baseline_noPCM.json` | 2 | none | (0.08, 19, 0.030) — default, unused | 0.5388 | 68.7 / 68.7 | 0 | 0.00163% |

(`n_capsule` and diameter/flow are reported but not physically used in the
`--no-pcm` baseline rows — `run_case.py` forces `n_capsule_effective=0`
whenever no PCM is given, so the tank is simulated as plain sensible-water
storage regardless of the geometry flags passed on the command line.)

### Inference

**All six cases complete cleanly.** Every energy-balance residual is
between 0.00030% and 0.00163% of collector energy — one to three orders
of magnitude under the 0.1% Gate-1 pass threshold and far under the 0.5%
hard-stop limit — confirming both Phase-4-discovered bug fixes (the
reverse-collector-flow accounting fix and the adaptive-substepping
stiffness fix, both described in `03_PHASE3_GREYBOX_SIMULATOR.md`) are
intact in this Rajasthan run, not just in the Tamil Nadu run they were
originally found in.

**Solar fraction is climate-driven, not PCM-driven, at this stage.** All
three Cluster-0 RT50 geometries (max-load, and two mid-geometries at
different flow rates) land within 0.001 of the plain-tank baseline's
0.5497 — consistent with Tamil Nadu's own Phase 4 finding that a single
PCM's marginal effect on annual solar fraction is small in this
lumped-tank architecture. This is a **smoke-test observation**, not a
Phase 4 Gate-3 baseline comparison (that requires the full battery of
comparator designs Gate 3 defines) — treat it as a reason Phase 4 is worth
running carefully, not as a substitute for it.

**The safety-violation numbers are the finding worth flagging before
Phase 4.** RT50 (`Tm = 50 °C`) exceeds the frozen 65 °C PCM
material-stability limit in **every** Cluster-0 geometry tested — and the
violation count is *higher*, not lower, at the smaller mid-geometry
(2,347–3,142 sub-hours) than at the maximum loading (896 sub-hours).
Cross-referencing the plain-tank baseline explains why: Cluster 0's own
water temperature reaches **68.6 °C with zero PCM in the tank at all** —
this is a property of Rajasthan Cluster 0's hot-dry, high-clearness solar
input (confirmed genuinely Rajasthan by the Phase 0 check above) hitting
the frozen 50 L tank / 1.5 m² collector sizing, not a capsule-sizing
choice. A smaller PCM mass tracks the (already too-hot) water temperature
more closely and faster than a larger, more thermally-buffered PCM mass
does, which is the mechanism behind the counter-intuitive "more violations
at less PCM" direction — a real, physically-explicable result, not
simulator noise. Clusters 1 and 2's plain-tank baselines reach 72.4 °C and
68.7 °C respectively, so this is not a Cluster-0-only pattern.

**This needs a decision before Phase 4/5 proceeds**, in the same spirit as
Tamil Nadu's own documented findings (the 12.9%-not-20% PCM-loading limit,
and the PCM-vs-plain-tank near-tie): either (a) report that, under the
frozen shared collector/tank config, no PCM in Objective 1's Rajasthan
shortlist can stay under the 65 °C safety limit in Cluster 0 without an
additional bypass/overheat-protection control action (which is out of
Objective 2's scope and belongs to Objective 3's DRL controller), or (b)
flag the frozen collector sizing itself as needing a hot-climate-specific
revisit. Either way, **do not quietly raise the 65 °C limit or drop the
violation count from future reports** — it is real and it is Rajasthan's,
confirmed independently by the Phase 0 climate check.

---

## Phase 4 — `phase4_simulator_verification_report.txt`

**Produced by:** `python pipeline.py --state rajasthan --stage verify`
**Format:** plain text, one section per gate (1–5) + a SUMMARY / Go-No-Go block.

### What it contains

The reduced 5-gate verification battery from the framework doc, run
end-to-end (~2–3 min; ~40 full-year simulations total). `src/verify/gates.py`
is ported from `objective2-tamilnadu/src/verify/gates.py` — same gate
logic, thresholds and verdict rules — with only the state-specific test
inputs changed (3 clusters not 5; PCMs `RT50` / `savE® OM50` not
`n-Octacosane`), plus one **informational, non-gating** Gate 2 line that
records Cluster 0's plain-tank overheating.

### Result

| Gate | Verdict | Headline number |
|---|---|---|
| 1 — Energy conservation (5 cases) | **PASS** | max residual 0.0016% of E_collector (pass < 0.1%) |
| 2 — Limiting cases | **PASS** | 10/10 gating checks; +1 informational Cluster-0 overheat record |
| 3 — Baseline comparison | **PASS** | RT50 beats plain tank (SF 55.08% vs 54.97%); capability check + active loss term both confirmed |
| 4 — Published-benchmark calibration | **PASS** | 55.07% solar fraction — **inside** the cited 54–84% band (Singh et al. 2025) |
| 5 — Sensitivity / monotonicity | **PASS** | 3/3 spot checks in the physically-correct direction |

**Gates passing cleanly: 5/5. Go/No-Go: GO.** Simulator to be tagged
`sim_v1_rajasthan` at the next commit.

### Inference

**The simulator is verified for Rajasthan** — no DOE row is blocked now.
Every energy-balance residual is under 0.0016% (≈300× inside the 0.5%
hard-stop), so both Phase-3 bug fixes hold on Rajasthan's weather, not
just Tamil Nadu's. All ten limiting cases degrade in the physically
sensible direction.

**Rajasthan verifies one gate cleaner than Tamil Nadu** (5/5 vs TN's
4/5), on identical code. Two Rajasthan-specific reasons, both real, not
tuning:
1. **Gate 3** — `RT50` (`Tm = 48 °C`) actually beats the plain tank here,
   whereas TN's rank-1 PCM (`n-Octacosane`, `Tm = 61.6 °C`) did not. RT50's
   melting point sits inside this tank's operating range, so it cycles as
   latent storage (mean liquid fraction rises) instead of just displacing
   sensible water. The margin is small (0.11 pp) because the reachable PCM
   fraction is still capped at ~12.9%, but the sign is correct with no
   caveat.
2. **Gate 4** — the same 50 L-tank / 300 L-day / no-backup-heater config
   lands at 55.07% solar fraction, **inside** the cited 54–84% band;
   TN's was 51.39%, just below. Rajasthan's stronger solar resource is
   the whole difference.

**The Cluster-0 65 °C finding is now on the record inside the gate
report** (Gate 2, informational line): the plain tank alone reaches
68.6 °C, so the Phase 3 smoke-run safety violations are a
climate-plus-sizing property, confirmed here, not a capsule-sizing bug.
It does not fail any gate — but it is the specific thing Phase 6/7 must
carry forward (either as a reported hot-climate constraint under the
frozen collector/tank sizing, or a trigger to revisit that sizing for
hot-dry states — **not** something to silently drop). Phase 5 below
quantifies it across the whole design space.

---

## Phase 5 — `phase5_design_cases.parquet` (+ `.csv`)

**Produced by:** `python pipeline.py --state rajasthan --stage doe`
**Format:** one row per simulation case — 165 rows × 42 columns. Columns:
`case_id`, `regime_id`, `pcm_id`, the design vector (`capsule_diameter_m`,
`n_capsule`, `flow_rate_kg_s`), `sampling_method`/`seed`,
`simulator_version`, `valid`/`reason`, geometry outputs (`geom_*`),
performance outputs (`useful_energy_kWh`, `solar_fraction`,
`unmet_energy_kWh`, `pump_energy_kWh`, `max_water_temp_C`,
`max_pcm_temp_C`, `n_safety_violations`, `residual_pct_of_collector`, …),
and `split ∈ {train, holdout}`.

### What it contains

The reduced DOE: 9 regime×PCM pairs (3 clusters × 3 shortlisted PCMs) ×
(12 Latin-Hypercube + 6 boundary cases) + 3 no-PCM baselines = **165
cases**, each run through the Phase 2 geometry gate and (if valid) a full
Phase 3 simulated year with `sim_v1_rajasthan`. Sampling: LHS over
(diameter, flow, count) with fixed seed base `20260905`; boundary corners
= `dmin/dmax × fmin/fmax`, `nmin`, `nmax`. `src/doe/generate_cases.py` is
byte-identical to Tamil Nadu's; `run_batch.py` uses `n_lhs_per_pair=12`
(TN uses 8) so a 3-regime state still lands in the framework's 150–300
target. See `../docs/05_PHASE5_DOE.md`.

### Result

| | Count | Note |
|---|---|---|
| Total cases | 165 | 108 LHS + 54 boundary + 3 baseline |
| Valid / simulated | **111** | — |
| Rejected at Phase 2 geometry gate | **54** | all `reason=bounds_violation`; 36 LHS + 18 boundary, 18 per cluster |
| Train / holdout split | **138 / 27** | stratified by `(regime_id, pcm_id, valid)`; all 9 regime×PCM pairs have ≥1 holdout |
| DOE runtime | 809 s | ~4.9 s/valid case |

Across the 111 valid rows: `solar_fraction` 0.538–0.587 (mean 0.559),
`geom_pcm_volume_fraction` 0.0064–0.1138, `max_pcm_temp_C` 68.2–72.7 °C.

### Inference

**The 54 rejections are the Phase 2 finding at scale, not a new bug.**
Any `capsule_diameter_m` in `[0.02, 0.04)` gives a derived
`pcm_thickness_m = diameter/2 < 0.02`, below the frozen thickness floor.
That is `(0.04−0.02)/(0.08−0.02) = 33.3%` of the diameter range; the LHS
draws rejected at 36/108 = 33.3% and the boundary cases at exactly the 2
`dmin_*` corners × 9 pairs = 18 — so 54/165 = **32.7%**, matching Tamil
Nadu's 32.6% almost exactly. Nothing else is silently dropping cases. All
54 are **kept** in the parquet with `valid=False` and the reason code, per
the framework doc — they are the feasibility boundary Phase 6's classifier
will learn.

**The split is leakage-free by construction** — every row is one complete
independent simulation, so a random row-level 80/20 split cannot leak a
shared trajectory. Stratifying on `valid` too means the holdout contains 9
infeasible rows, so Phase 6's feasibility-classifier recall can actually
be measured. No unseen-weather-year holdout (medoid-only, single 2025
year) — named future work, same cut as Tamil Nadu.

**The safety-limit finding is now design-space-wide, not a Cluster-0
special case.** Every one of the 111 valid cases has `max_pcm_temp_C`
above the frozen 65 °C limit (68.2–72.7 °C), and 108/111 log
`n_safety_violations > 0` — all three regimes, all six shortlisted PCMs,
across the full sampled range of diameter / count / flow. Under the frozen
1.5 m² collector / 50 L tank, Rajasthan's solar input overheats the store
before any control action. **Phase 7 must treat the 65 °C limit as a
hard selection constraint** (or the frozen collector sizing needs a
hot-dry-state revisit). This is a real, reportable result — in the same
spirit as Tamil Nadu's 12.9%-not-20% PCM-loading finding — not something
to tune away.

---

## Phase 6 — `phase6_surrogate_*`

**Produced by:** `python pipeline.py --state rajasthan --stage surrogate`
**Files:** `phase6_surrogate_metrics.csv` (hold-out MAE/RMSE/R² per target,
Extra Trees vs LinearRegression), `phase6_surrogate_error_by_group.csv`
(hold-out MAE by regime and by PCM), `phase6_surrogate_models.pkl` (the
trained models + `feature_cols`, git-ignored), `phase6_surrogate_feature_cols.json`.

### What it contains

One tree-based surrogate family (`ExtraTreesRegressor`, 300 trees, seed
`20260905`) per performance target, trained on the **93 valid `train`
rows** of `phase5_design_cases.parquet` and scored on the **18 valid
`holdout` rows**, each with a `LinearRegression` baseline on the identical
split. Plus one `ExtraTreesClassifier` for feasibility, trained on all
138 non-holdout rows (valid + invalid) and scored on the 27-row holdout
(9 infeasible). 39 input features: 9 design/geometry + 17 climate (from
`cluster_profiles_rajasthan.csv` + `T_mains_est_C` from the state yaml) +
11 PCM property + `is_no_pcm` + `top3_inclusion_probability`. The
surrogate *code* is ported from Tamil Nadu unchanged; only the Objective 1
column names are remapped (RJ's Obj1 pipeline uses different headers) —
see `../docs/06_PHASE6_SURROGATE.md` for the mapping table.

### Result

| Target | Extra Trees R² (hold-out) | Linear R² | Tree vs linear |
|---|---|---|---|
| `useful_energy_kWh` | **0.99983** | 0.99988 | tie (linear marginally ahead) |
| `solar_fraction` | 0.99965 | 0.99901 | tree wins |
| `unmet_energy_kWh` | 0.99986 | 0.99962 | tree wins |
| `pump_energy_kWh` | 0.326 | 0.99983 | linear wins (target ≈ 1e-9 kWh, near noise) |
| `pcm_mass_kg` | 0.99725 | 0.99795 | tie (linear marginally ahead) |
| feasibility classifier | accuracy 1.000, infeasible-class recall 1.000 (n=9) | — | — |

### Inference

**Exit check passed with a wide margin.** The framework doc's bar is
useful-energy hold-out R² > 0.80 (< 0.75 → add DOE cases). Rajasthan's is
**0.9998** — no extra DOE needed. The three "key outputs" named in D2.5
(useful energy, solar fraction, unmet energy) are all R² ≥ 0.9996, so the
surrogate can be trusted to *rank* candidate designs in Phase 7. It is
**not** the oracle: Phase 7 re-runs every design it favours in the real
simulator (Bug-Fix 5).

**Honest linear-vs-tree finding (the framework doc requires this
comparison be reported as-is):** linear regression ties or slightly beats
the tree on `useful_energy_kWh`, `pump_energy_kWh` and `pcm_mass_kg`. At
the ≤12.9% PCM fractions reachable within the frozen bounds the physics in
this region is close to linear in the sampled variables — `pcm_mass_kg` is
exactly linear in `n·d³·ρ`; `pump_energy_kWh` is Ergun-viscous-dominated
(linear in flow) and only ~1e-9 kWh anyway, so the tree's R²=0.33 there is
fitting numerical noise, not a real defect; annual `useful_energy` is
carried mostly by the regime-level climate features plus a near-linear
PCM-mass term. Tamil Nadu saw the same for `pump_energy_kWh`; Rajasthan's
smaller/sparser dataset makes it surface for two more low-variance
targets. The tree still wins where the relationship is genuinely
non-linear (`solar_fraction`, `unmet_energy_kWh`), so it stays the ranking
model and the linear baseline is kept in the metrics CSV as the comparator.

**Feasibility classifier 100%/100%** is expected, not suspicious: the
feasibility boundary is one sharp deterministic rule
(`capsule_diameter_m < 0.04 m`, Phase 5) — trivially learnable. The
stratified split (Phase 5) is what gives it 9 infeasible hold-out
examples to be scored on at all.

**Per-group error** (`phase6_surrogate_error_by_group.csv`):
`useful_energy_kWh` MAE 0.23–0.49 kWh across the 3 regimes, 0.05–0.91 kWh
across the 6 PCM groups (worst for `RT45HC`, which has only 2 hold-out
rows). No regime is a systematic weak spot; per-PCM spread is hold-out
count noise (2–4 rows/group), not a badly modelled PCM.

**Caveat:** an 18-row valid hold-out means these R² values say "ranking is
reliable", not "generalisation error is precisely X". Phase 7's simulator
re-confirmation is what produces defensible final numbers.

---

## Phase 7 — `phase7_*`

**Produced by:** `python pipeline.py --state rajasthan --stage optimize`
**Files:** `phase7_surrogate_top_candidates.csv` (60 surrogate-ranked
candidates — proposal only, never final), `phase7_optimized_designs.csv`
(all 60 re-run in the real simulator — the PCM-comparison report),
`phase7_deployable_design_per_regime.csv` (the final selection, 1 row per
regime).

### What it contains

One optimization pass (not the full active-learning loop): 400 random
design vectors per regime×PCM pair (12 pairs), each filtered by the real
Phase 2 geometry gate then scored by the Phase 6 surrogate; top 5 per
pair by predicted useful energy (**60 candidates**) re-run in the real
simulator; then the pre-declared selection rule from
`system_config_shared.yaml` (`pareto_tolerance_pct = 5%`): reject
temperature-unsafe → within 5% of best useful energy → min pump energy →
min PCM mass → min capsule count → max constraint margin. Ported from
`objective2-tamilnadu/src/optimize/` unchanged except the flat
`results/phase7_*` paths.

### Result (current, 2026-09-14 — safety shield default + PCM-only selection)

**Deployable design per regime — a shortlisted PCM in all three:**

| Regime | Design | d (m) | n | flow (kg/s) | Useful energy (kWh) | Solar fraction | Max water T (°C) | Max PCM T (°C) | Margin to 65 °C PCM |
|---|---|---|---|---|---|---|---|---|---|
| 0 | RT45HC | 0.0500 | 24 | 0.0175 | 1587.88 | 55.33% | 68.8 | 62.1 | 2.9 °C |
| 1 | Paraffin/HDPE PCM6 | 0.0414 | 15 | 0.0302 | 1674.69 | 58.28% | 72.0 | 62.2 | **2.8 °C** |
| 2 | Paraffin/HDPE PCM3 | 0.0416 | 8 | 0.0181 | 1593.46 | 53.90% | 68.8 | 62.1 | 2.9 °C |

- **Surrogate accuracy in practice:** mean surrogate-vs-simulator error
  0.023% across all 60 confirmed candidates (max 0.090%); **0/60**
  exceeded the 15% large-error threshold. Energy-conservation residual
  over the same 60 full-year runs: mean 0.00088%, max 0.0018% —
  generalises Gate 1 from 5 cases to 60.
- **Temperature safety is no longer binding against PCM:** **all 60/60**
  candidates now pass `meets_temperature_safety` (max water ≤ 75 °C, max
  PCM ≤ 65 °C, zero year-round violations) — 15 plain-tank and 45 PCM
  alike, a direct consequence of the safety shield becoming the pipeline
  default on 2026-09-13.
- **Best PCM vs best plain tank** (per regime, from
  `phase7_optimized_designs.csv`, all 60 candidates): PCM's best-found
  geometry beats the best plain-tank geometry by +0.14% (regime 0,
  RT45HC) / +0.08% (regime 1, Paraffin/HDPE PCM3) / +0.09% (regime 2,
  savE® OM50) useful energy, and every one of those PCM designs now
  **passes** temperature safety. (The single best-found PCM candidate per
  regime is not always the same PCM as the deployable winner in the table
  above — several PCMs land within the 5% Pareto tolerance, and the
  winner is chosen by the tie-break, not simply the highest-energy row.)

### Inference

**Under the pipeline's current default configuration, the Rajasthan
deployable design for every climate regime is a shortlisted PCM.** This
reverses the original all-plain-tank finding (kept below as
"superseded"), for two compounding reasons:
1. The safety shield (pipeline default since 2026-09-13) rescues PCM
   candidates from the overheat failure mode exactly as it rescues plain
   water — so the 65 °C PCM limit is no longer a filter that only the
   plain tank clears.
2. `apply_selection_rule()` (re-ported from Tamil Nadu, 2026-09-14)
   excludes the plain tank from the winner pool, so the fraction-of-a-
   percent useful-energy edge PCM already had over plain water — present
   even in the original unshielded run, just previously discarded by the
   safety filter or the mass tie-break — now decides the winner.

This is the same magnitude of PCM-vs-water margin Phase 4 Gate 3 and
Phase 5 always found (a fraction of a percent, nothing changed physically
about how much better PCM is) — what changed is which design family gets
to act on that margin. **Flag, unchanged:** regime 1's deployable design
runs at 72.0 °C max water / 62.2 °C max PCM, the thinnest margin of the
three regimes (2.8 °C to the PCM limit) — still passes cleanly, still
worth watching if the collector/tank sizing is ever revisited.

---

### Superseded result (unshielded physics / pre-2026-09-14 selection rule — kept for the record)

**Deployable design per regime — plain (sensible-only) tank in all three:**

| Regime | Design | d (m) | n | flow (kg/s) | Useful energy (kWh) | Solar fraction | Max water T (°C) | Margin to 75 °C |
|---|---|---|---|---|---|---|---|---|
| 0 | plain tank | 0.0488 | 23 | 0.0315 | 1585.70 | 54.97% | 68.6 | 6.4 °C |
| 1 | plain tank | 0.0400 | 8 | 0.0183 | 1673.36 | 58.23% | 72.4 | 2.6 °C |
| 2 | plain tank | 0.0413 | 14 | 0.0310 | 1592.27 | 53.88% | 68.7 | 6.3 °C |

Temperature safety was fully binding against PCM: only 15/60 candidates
passed `meets_temperature_safety`, all 15 plain-tank (5/regime); 0/45 PCM
candidates passed, any regime, any of the six shortlisted PCMs — because
no active overheat protection was modelled at all in this earlier run.
This was the same negative result Phase 4 Gate 3 and Phase 5 first
reached, confirmed by a 400-candidate-per-pair search with full simulator
re-confirmation. It motivated building the safety shield described above.

---

## Phase 8 — `phase8_*`, `obj3_environment_contract_rajasthan.json`

**Produced by:**
```
python pipeline.py --state rajasthan --stage robustness --mc-draws 120
python pipeline.py --state rajasthan --stage handoff
```
(two separate stages, matching `objective2-tamilnadu/pipeline.py`'s
split — this project originally combined both into one `handoff` stage.)
**Files:** `phase8_robustness.csv` (per-regime summary), `phase8_robustness_draws.csv`
(all 360 draws, for audit), `phase8_recommendation_cards.md` (D2.8 — one
card per regime), `obj3_environment_contract_rajasthan.json` (D2.9).

### D2.7 — Robustness (`phase8_robustness.csv` / `_draws.csv`)

**120 Monte Carlo draws per regime** (360 total; framework band 100–200,
never < 50). Each draw re-runs the Phase 7 deployable design for a full
year with independent perturbations: weather (annual GHI scale
U(0.93,1.07) × per-hour N(1,0.04); T_amb annual offset U(±1.5 °C) +
per-hour N(0,0.4 °C)); demand volume U(±20 %); demand timing U(±30 min);
mains temp U(±2 °C). PCM latent-heat ±10 % is **not applicable** — all
deployable designs are the plain tank — stated, not dropped. Weather is
injected via `run_case`'s `weather_perturbation` keyword (per-hour arrays)
so `run_case` needs no Phase-8-specific code path and every metric matches
the Phase 7 `sim_*` definitions exactly.

**Current (2026-09-14, shielded PCM designs):**

| Regime | PCM | P(meet delivery temp) | P(meet annual demand) | **P(temp-safe)** | P(exceeds max safe temp) | Useful energy P5–P50–P95 (kWh) | Max water P95 | Robust? |
|---|---|---|---|---|---|---|---|---|
| 0 | RT45HC | 1.00 | 0.933 | **1.00** | 0.00 | 1451 – 1556 – 1714 | 72.3 °C | **Yes** |
| 1 | Paraffin/HDPE PCM6 | 1.00 | 0.983 | **1.00** | 0.00 | 1506 – 1650 – 1797 | 72.3 °C | **Yes** |
| 2 | Paraffin/HDPE PCM3 | 0.992 | 0.833 | **1.00** | 0.00 | 1461 – 1575 – 1713 | 72.2 °C | **Yes** |

Column names match `objective2-tamilnadu`'s aligned Phase 8 schema
(`p_meets_delivery_temp`, `p_meets_annual_demand`,
`p_temperature_violation`, `p_exceeds_max_safe_temp`,
`useful_energy_p05/p50/p95_kWh`, `max_water_temp_p95_C`,
`robust_per_framework_rule`) — see `../docs/08_…`, "Alignment with the
Tamil Nadu implementation." `pump_energy_p05/p95_kWh` is also in the CSV
(~1e-9 kWh, negligible); unlike the earlier all-plain-tank run,
`pcm_mass_p05/p95_kg` is now non-zero in every regime (fixed per design —
geometry doesn't vary across MC draws — so p05 = p95 = the design's PCM
mass).

Thresholds (project assumptions, stated in `../docs/08_…`):
`meet_delivery_temp` = `solar_fraction ≥ 0.45`, `meet_annual_demand` =
`solar_fraction ≥ 0.50` (`solar_fraction` is already the delivery-temp-
weighted demand-met fraction — Phase 3 doc). Robust if
`P(meet annual demand) ≥ ~0.75` **and** `P(temp-safe) ≥ ~0.95`.

**Inference — ROBUST in all 3 regimes, on both axes.** The demand bar is
cleared everywhere (0.833–0.983) and, unlike the earlier unshielded
result, temperature safety is now perfect: **not one of the 360 Monte
Carlo draws across all three regimes breaches either the 75 °C water or
65 °C PCM limit** — P(temp-safe) = 1.00 everywhere. The safety shield
(pipeline default since 2026-09-13) converges every regime's P95 max
water temperature to 72.2–72.3 °C, just above its own 72 °C trigger — the
mechanism working exactly as designed, not a coincidence of sampling. No
draw produced a NaN/inf or failed year; useful-energy spread is ≈ ±8–9 %
around the median. Regime 1 still has the highest median useful energy
(1650 kWh) of the three, but — unlike before — that no longer trades off
against worse safety (see `../docs/plots/08_robustness_plots.md`, Plot 2).

**Superseded (pre-shield / pre-2026-09-14 selection rule, plain-tank-only
designs, kept for the record):**

| Regime | P(meet delivery temp) | P(meet annual demand) | **P(temp-safe)** | P(exceeds max safe temp) | Useful energy P5–P50–P95 (kWh) | Max water P95 | Robust? |
|---|---|---|---|---|---|---|---|
| 0 | 1.00 | 0.875 | **0.567** | 0.433 | 1454 – 1572 – 1673 | 84.6 °C | **No** |
| 1 | 1.00 | 0.992 | **0.450** | 0.550 | 1523 – 1664 – 1781 | 88.2 °C | **No** |
| 2 | 1.00 | 0.800 | **0.533** | 0.467 | 1447 – 1566 – 1692 | 84.6 °C | **No** |

Every design here was the plain (sensible-only) tank. The demand bar was
still cleared everywhere, but temperature safety failed badly — roughly
half of draws breached the 75 °C water scald limit, worst in regime 1
(nominal Phase 7 margin only 2.6 °C; P95 max water 88.2 °C). This was the
finding that motivated building the safety shield.

### D2.8 — Recommendation cards (`phase8_recommendation_cards.md`)

One card per regime, regenerated 2026-09-14 against the current
shielded/PCM-only pipeline. Each carries: regime/climate summary
(`cluster_profiles_rajasthan.csv`), the Objective 1 PCM shortlist + MCDM
rank + MC top-3 inclusion, the selected PCM geometry + flow, the
`sim_v1_rajasthan`-confirmed full-year performance, the Phase 8
robustness probabilities (now 100% temperature-safe in every regime), the
surrogate-vs-simulator delta (~0.002 %), the decision rationale (why that
PCM — safety shield active throughout search/confirmation/selection, 45/45
PCM candidates now clear the 65 °C limit), and a caveats block (imputed
PCM properties, single-pass optimization, reduced Monte Carlo, single-state
scope, lumped-model ±15 %, plus two shield-specific caveats: every number
is computed WITH the shield active as the pipeline default, and the
IS 12976:2023 tank-resize finding is a further not-yet-adopted mitigation
not folded into these numbers). The file recomputes nothing — every number
is a lookup.

### D2.9 — Objective 3 environment contract (`obj3_environment_contract_rajasthan.json`)

`schema: obj3_environment_contract/v1`. Shared blocks: `global_limits`
(45 °C delivery, 75 °C water, 65 °C PCM, 3.5 bar, 10 W/m² cutoff,
0.010–0.050 kg/s pump); `control_skeleton` with `actions:
[charge, discharge, bypass]`, the recommended continuous-flow hybrid
action space, a 10-element `state_vector`, and a `safety_shield` that
forces `bypass` at `T_water ≥ 72 °C` (3 °C guard band), clamps flow to
the pump envelope, cuts the pump below the irradiance cutoff, and states
the dry-run/sensor-failure fallback rules — its rationale cites the
Phase 8 P(temp-safe) result. `dynamic_state_schema` (10 fields, each with
unit / `measurable` flag / source — ported from Tamil Nadu this pass),
`reset_scenarios` (fully solid / partially charged / fully liquid),
`reward_components_suggested` (formula stated, weights explicitly
"not yet chosen"), `acceptance_test_before_drl_training` (6-item
checklist), `weather_sequences` (states plainly that no train/val/test
weather split exists yet). Per regime: `regime_id`, label,
`regime_membership_rule`, medoid weather path, `T_mains_est_C`,
`Tm_target_C`, `selected_design` (pcm_id `null` for the plain tank,
optional `pcm_properties`, full geometry, `flow_envelope_kg_s` =
{nominal, min, max}), `sim_confirmed_performance`, `robustness` (both
temperature-safety metrics), `sim_v1_rajasthan` tag. A
`deferred_future_work` list names the four-state comparison,
active-learning / NSGA-II, full-draw robustness, widened design bounds,
and hardware validation.

### Exit check

**Met.** All 3 Level-A regimes have a recommendation card and appear in
the contract. This is the Objective 2 "done" line for the ~40-hour
version. Deferred and named as future work (not silently dropped): the
four-state comparison, the active-learning loop, and full-draw robustness
with a real alternate weather series.

---

## Plots — `plots/static/*.png` (17), `plots/interactive/*.html` (17)

**Produced by:** `python pipeline.py --state rajasthan --stage plots`
**Format:** one Plotly figure per Phase 2–8 justification point, saved as
a flat PNG (committed) and a self-contained interactive HTML (git-ignored,
regenerate locally).

`phase2_validity_map`, `phase2_ergun_hydraulics`,
`phase3_temperature_timeseries`, `phase3_melt_fraction_year`,
`phase3_energy_breakdown`, `phase4_gate1_residuals`,
`phase4_gate3_baseline_comparison`, `phase4_gate5_sensitivity`,
`phase5_doe_coverage`, `phase5_outcome_distribution`,
`phase6_parity_plots`, `phase6_feature_importance`,
`phase7_pareto_by_regime`, `phase7_surrogate_vs_simulator`,
`phase7_safety_compliance`, `phase8_robustness_probabilities`,
`phase8_useful_energy_intervals`.

`src/plots/make_plots.py` re-derives nothing — each figure reads a
Phase 5–8 output file or re-runs one already-verified case for a time
series. See `../docs/plots/00_INDEX.md` for what each figure shows, what
to infer, and its viva/report caption. **Regenerated 2026-09-14** against
the current shielded/PCM-only-selection pipeline (the `phase7_safety_
compliance` bar-chart crash from `counts.get(False, 0)` returning a
scalar once every candidate passed safety was also fixed in the same
pass, `src/plots/make_plots.py::phase7_safety_compliance`). Two
standouts, both flipped from their earlier all-plain-tank/unshielded
versions: `phase7_safety_compliance` — all 60/60 candidates (15
plain-tank + 45 PCM) now pass temperature safety, in one picture — and
`phase8_robustness_probabilities` — every regime's green
(temperature-safe) bar now sits at a flat 100 %, at the 95 % reference
line, for the now-PCM deployable designs.

---

## What's not here yet

Nothing from the Tamil Nadu tree — `src/plots/` is ported and wired.
Phases 0–8, the full Objective 2 ~40-hour deliverable set, are complete
and every output is in this folder. Remaining items are the named future
work in `obj3_environment_contract_rajasthan.json` (`deferred_future_work`).
