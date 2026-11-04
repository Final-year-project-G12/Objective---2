# Porting Rajasthan's (Manvitha's) Objective 2 methodology to Tamil Nadu — progress tracker

## 🔴 2026-10-29 — CRITICAL: the weather cache carried a +5 h solar shift; all O2 results were voided and re-run

**What was wrong.** Every one of the 45 files under
`data/weather/point_years/tamilnadu/` had its solar columns shifted **+5
hours** against its own `timestamp_utc`. They were sliced out of
`weather_regime_tamilnadu_cluster{0,1,2}_hourly_multiyear.csv`, which
carried the shift. `src/optimize/baseline.py` and `src/optimize/evaluate.py`
both read that cache through `roles.load_point_year`, so **every gate that
evaluates a design** inherited it — the Sobol DOE, the surrogate bake-off,
NSGA-II, and all downstream gates.

**How it was caught.** A ported test,
`test_new_cache_matches_existing_regime_weather_file`, failed on row counts.
Chasing that produced a 5-hour lag at correlation 0.99887 between the cache
and the legacy single-year regime file, with annual clearsky sums matching to
0.03 % — the signature of a pure time shift, not different data.

**Three independent confirmations**, for TNP_0001 on 2016-06-15 (true
sunrise 00:13 UTC, from `data/objective1/suntimes.csv`):

| source | clearsky > 0 | peak | verdict |
|---|---|---|---|
| raw NASA POWER JSON (`header.time_standard == "UTC"`) | 00:00–12:00 UTC | 06:00 UTC | ✅ ground truth |
| `weather_regime_..._cluster2_hourly.csv` (legacy single-year) | 00:00–12:00 UTC | 06:00 UTC | ✅ correct |
| `point_years/.../cluster2_TNP_0001_2016.csv` | 05:00–17:00 UTC | 11:00 UTC | ❌ **+5 h** |

+5 h is IST (+05:30) truncated to whole hours: the series was written against
local-clock stamps while labelled UTC. The cache put sunrise at 10:00 IST and
sunset at 22:30 IST.

**Why it mattered, and why it could not be corrected after the fact.** The
study's primary objective is the evening delivery window against a demand
profile peaking at 19:00 IST. The shift moved collector gain from ~11:30 to
~16:30 local — four to five hours *closer* to the evening peak than reality,
systematically flattering PCM on the one objective the whole study turns on.

**The fix.** `scripts/tn_rebuild_weather_from_raw.py` rebuilds the multiyear
files and the per-point-year caches **directly from the raw POWER JSONs**,
applying no offset, and **refuses to write** unless clearsky daylight
brackets independently computed sunrise/sunset on every day (±90 min). All 30
rebuilt point-years pass: 3,653 days per cluster. Solar noon now lands at
local hour 11 in all 30 files (was 16 in all 45).

**Held-out test years quarantined.** Raw JSONs cover 2016–2025 only
(explore 2016–2020, select 2021–2023, used_test_v1 2024–2025). 2011–2015
existed *only* in the shifted multiyear CSV and cannot be verified, so those
15 files were moved to
`data/weather/_shifted_backup_2026-10-29/quarantined_test_years/`.
`roles.load_point_year` now raises `FileNotFoundError` for them, so
**`g10_test` is blocked by construction** until raw 2011–2015 is fetched and
passes the same ephemeris check. A one-shot held-out run must not be spent on
weather we cannot verify.

**Blast radius.** All 125 entries of `results/` moved to
`results_STALE_shifted_weather_2026-10-29/` (nothing deleted). Only
`g4_multinode_report` survived — it reads the legacy correct file via
`load_hourly_weather` — and was copied back. The full pipeline was restarted
from `g2` on corrected weather. The results voided include the completed
128-point × 9-pair DOE and the 93.9-minute surrogate bake-off.

**Lesson for the pipeline.** The original builder recorded
`"time_standard": "UTC"` into its inventory as metadata but never *checked*
it against solar geometry. Clearsky irradiance is pure astronomy, so the
check costs nothing and is now mandatory in the rebuild path. Provenance
metadata is not verification.


This is the single, persistent source of truth for this build (mirrors
Manvitha's own `docs/PROGRESS.md` practice on the Rajasthan side, for the
same reason: this is multi-session work and nothing here should need to be
re-derived from scratch if a session boundary cuts it off mid-way).

**Explicit scope decision (2026-10-28, confirmed by the user)**: implement
the full set of algorithms/methodology described in
`O2_Rajasthan_Pipeline_Report.docx` (multi-node tank, Taguchi screening,
Sobol DOE, 3-way surrogate comparison, NSGA-II + active learning with the
box-vertex fix, dense-grid cross-check, repeatability band, held-out-lock
test, 6 diagnostic/ablation studies, results registry, test suite) —
**but keep Tamil Nadu's own existing file/folder structure** (no `g1`...`g19`
script renaming, no copying Rajasthan's folder layout). CFD stays ANSYS
Fluent (not OpenFOAM). Tank stays 100 L / 2.5 m² (not Rajasthan's 50 L).
Final output format/deliverables (`deployable_design_per_regime.csv`,
robustness P(delivery)/P(demand)/P(temp-safe) framework) stays as Tamil
Nadu's current shape — the algorithms underneath change, not the contract.
Cleanup: archive unneeded files (don't delete), separate Objective-3-related
files into their own folder out of `results/`.

**Important, disclosed gap**: the actual Rajasthan `o2-redesign-rajasthan`
branch code (its `nsga2.py`, `g7`...`g18` scripts, `design_space.yaml`,
`tests/`) is NOT present in this workspace — only a pre-rebuild snapshot of
`objective2-rajasthan/` (same simple structure Tamil Nadu currently has)
and the narrative report. Everything below is being built from the
report's description, validated independently on Tamil Nadu's own data —
it will not numerically match Manvitha's results, only the methodology.

## 2026-10-29: her ACTUAL source was located — the hand-port is superseded

Everything above this section was written while porting from her `.docx`
report's prose, which was all that was available. Her real implementation
turned out to be in the workspace at
`Github/Objective---2/objective2-rajasthan` (4,247 lines of `src/` +
3,056 lines of `scripts/`, gates g2–g24 — five gates beyond the report's
G19).

A file-by-file comparison against the hand-port found **ten material
physics divergences**. The decisive one:

> **Her collector is a MASS-FLOW loop; the hand-port modelled it as a pure
> heat source.** Hers moves water out of node 0 and back in at the
> stratified return node (`ext_out[0] += mdot_c; ext_in[k_ret] += mdot_c`),
> derives interface flows from mass conservation, and applies first-order
> upwind advection — so the flow rate sets the loop delta-T and the return
> node. As her own docstring puts it, flow "acts on stratification, not on
> Q". The hand-port's `rhs[j_charge] += q_collector_trial` has no mass
> transport at all, so flow barely affected stratification.

A flow-rate optimisation built on the wrong one of those is not worth
running, and flow rate is one of the four things Objective 2 exists to
determine. The other nine divergences were the return-node rule
(highest node with `T[j] <= t_out`, not nearest-temperature), a 5× axial
conduction enhancement the hand-port invented, end-cap vs. even ambient
loss split, per-node vs. constant water-side velocity, the wall-capacity
enthalpy span (`L + x*(Tl-Ts)`, not `L`), real packing-layer capsule
placement, count CLIPPING vs. rejection, residual on net vs. clipped load,
and a Gate-1 threshold of 0.1 % rather than 0.5 %.

**Decision: adopt her code rather than keep patching the port.** Her tree
is copied to `.` (project root) and pointed at Tamil Nadu's frozen inputs. This
removes all ten divergences at once and makes any remaining difference in
results a difference in *inputs*, not in method — which is the only way
the comparison is worth anything.

### What is deliberately different in `.` (project root)
| | hers | Tamil Nadu |
|---|---|---|
| state | rajasthan | tamilnadu (her state-config format, filled from TN's Objective 1 output) |
| tank | 50 L | **100 L** (project instruction) |
| collector | 1.5 m² (33.3 L/m²) | 2.5 m² — scaled to hold 40 L/m², the low end of IS 12976:2023 §4.2. Her 33.3 L/m² sits *below* that band, which her own report flags (decision D8). |

Her absolute kWh figures are therefore **not** directly comparable to
ours; the algorithms, gates and pass/fail criteria are.

### Adaptation needed to run her code on Tamil Nadu
* `local_hour` / `local_date` columns added to TN's weather
  (`scripts/tn0_add_local_hour.py`). Her `_demand_hour_of_day()` *refuses*
  a frame with `timestamp_utc` but no `local_hour` rather than falling
  back to UTC — the G1 fix made structural. Floor, not round.
* TN's 15 years laid out as her per-point-year files plus
  `weather_inventory.csv` (`scripts/tn1_build_point_years.py`), so the
  year-role enforcement and the held-out lock are inherited rather than
  reimplemented. 45/45 point-years accepted.
* Medoids set to TNP_0006 / TNP_0007 / TNP_0001; the 29 hardcoded
  `"rajasthan"` string literals parameterized to `config.STATE`.

### Verified running on Tamil Nadu
Her multinode tank, regime 0, RT57HC, R_in 20 mm / fraction 0.15 /
0.030 kg/s / staggered (398 capsules): **energy residual 3.4e-12 %** —
far cleaner than the hand-port's 0.0204 %, and inside her own 0.1 % Gate-1
threshold by nine orders of magnitude. Warm runtime 4.3 s/simulated-year
at dt=150 s, N=10.

### Speed: ours stays faster
Our numba kernel does the same dt=150 s / N=10 year in **1.0–1.9 s**
against her implementation's **4.3 s**, measured on this machine. The
parallel layer (11 workers, persistent pool, worker-side input caching)
sits on top of either. Her gates are run through it rather than through
her serial `for` loops, which is the one place her code is wrapped rather
than used as-is.

### Correction to the earlier surrogate claim
The "GP beats XGBoost by 11.2×" figure recorded below was measured on a
**synthetic smooth** 3-input function and **did not transfer to real
data**. On the actual 11,070-row DOE the ranking inverts:

| model | mean RMSE / sd(y) | groups won (g_window) |
|---|---|---|
| quadratic_rsm | 0.846 | 6 / 27 |
| xgboost_baseline | 0.858 | **21 / 27** |
| kriging_gp | 0.945 | 0 / 27 |
| nn_ensemble | 1.066 | 0 / 27 |

Every model sits at RMSE/sd ≈ 0.85–1.07, i.e. barely better than
predicting the mean — and the likely cause is visible in the setup: the
hand-port split groups by arrangement, leaving only 76–85 points each.
Hers uses **one multi-output model per (regime, PCM) pair with arrangement
as a one-hot feature** — 128 points per group and the arrangement effect
learned rather than partitioned away. Her layout is adopted with her code,
and the bake-off will be re-run on it before any surrogate claim is made.

## Does PCM beat the water-only tank in Tamil Nadu? Yes — measured (2026-10-29)

Run with HER simulator and HER paired water-only baseline, on explore year
2016. `g_window` is the primary objective: extra energy delivered at 45 C
in the 18:00–09:00 window, PCM tank minus the water-only tank at the same
flow, weather and demand.

### One design point is not the answer
At an arbitrary mid design (R_in 20 mm, fraction 0.15, 0.030 kg/s,
staggered, rank-1 PCM) the gain is marginal: **+18.2 / −8.7 / +12.6 kWh**
for regimes 0/1/2. That is roughly her repeatability band, i.e.
indistinguishable from the water-only tank. Reporting that as "PCM does
not work" would be a statement about one untuned point, not about the
design space.

### Lever sweep: what actually moves it (`results/tn_lever_sweep.csv`)
| lever | effect on g_window |
|---|---|
| capsule inner radius 10 → 40 mm | regime 0 **+0.4 → +41.4**, regime 2 **−4.3 → +34.6**. Bigger capsules win. |
| PCM fraction 0.02 → 0.30 | helps regimes 0 and 2 (to +32 / +19), **hurts** regime 1 (to −26) |
| flow 0.010 → 0.050 kg/s | 0.010 is actively harmful (**−29 to −37**); flat above ~0.020 |
| PCM melting point | **dominant** — see below |

The flow result matters for interpretation: her report flags that "flow
optima are not physical" because collector F_R is flow-independent in the
model, so low flow always helps a stratified tank. Here low flow *hurts*,
because at 0.010 kg/s the collector loop cannot move heat into the stack
fast enough to charge the capsules at all.

### Combined levers — the shortlist DOES win, in every regime
(`results/tn_corner_check.csv`, 162 combinations)

| regime | PCM (Objective 1 shortlist) | R_in | fraction | arrangement | N | **g_window** | g_annual | PCM peak |
|---|---|---|---|---|---|---|---|---|
| 0 | RT57HC (rank 1) | 34 mm | 0.30 | radial | 169 | **+37.1** | +28.2 | 62.38 C |
| 1 | n-Pentacosane C25 (rank 3) | 34 mm | 0.20 | radial | 113 | **+28.8** | +14.6 | 62.33 C |
| 2 | n-Pentacosane C25 (rank 2) | 40 mm | 0.30 | staggered | 105 | **+63.1** | +61.5 | 62.31 C |

All three positive, all inside the 65 C PCM limit and the 75 C water
limit. **No change to Objective 1's shortlist was needed.**

What rescues regime 1 is PCM *selection within* the shortlist: its rank-1
PCM (RT57HC, 56.5 C) reaches only +1.0 kWh there, while its rank-3 PCM
(C25, 54.0 C) reaches +28.8. That is exactly the division of labour
docs/18_OBJECTIVE1_SHORTLIST_RESTORED.md prescribes —
Objective 2 "must search geometry/flow for Objective 1's ACTUAL
shortlisted PCMs and select among THEM by simulated performance". Picking
the lower-melting shortlisted PCM is selection, not substitution.

These are coarse single-year grid points; the DOE + NSGA-II search should
improve on them, and every number that gets reported is re-simulated on
the select years before selection.

### The off-list sweep — RETRACTED, 2026-10-29

An earlier revision of this document reported an off-shortlist PCM sweep
(RT45HC and five others, +116…+145 kWh) and concluded from it that
**Objective 1's `Tm_target_C: 67.0` was an error**, on the grounds that
67 C sits above the 65 C PCM safety limit so "a PCM at that target could
never melt."

**That conclusion was wrong, and both the sweep and the recommendation are
withdrawn.** Two things were confused:

1. **`Tm_target_C` is a ranking criterion, not a material requirement.**
   It enters Objective 1's MCDM as `crit_Tm_fitness` / `f_Tm` — a fitness
   score measuring how close each candidate's melting point sits to the
   target. Nothing in the method requires a PCM to melt *at* 67 C, and the
   PCMs Objective 1 actually selected melt at **54.0–58.0 C**, comfortably
   under the 65 C cap. There was never a conflict with the safety limit.

2. **`Tm_target_C: 67.0` is already the corrected value.** It is
   `T_DELIVERY_C (60.0) + DT_APPROACH_C (7.0)` from the canonical
   `PCM-Selection-ML-model/pcm_shared_config.py`, physics-corrected on
   2026-09-13 against Avargani et al. 2021. The *pre*-correction value was
   57.0 C (delivery 50 C), which still survives in a stale copy under
   `All_objective_all/`. The doc-12 "retargeting" lineage (46.5–53.3 C)
   descends from that superseded 57 C basis — so the off-list sweep was
   re-deriving a number Objective 1 had already deliberately moved away
   from, in the opposite direction.

The off-list arm has been deleted from `scripts/tn_lever_sweep.py` and its
output CSV removed. A number that exists invites being quoted, and quoting
it would be Objective 2 re-deriving Objective 1's deliverable.

### Objective 1 hand-off, verified verbatim (2026-10-29)

`configs/states/tamilnadu.yaml` was checked field-by-field against
Objective 1's own `data/processed/pcm/mcdm_topk_by_cluster.csv`
(consensus-rank order). **Zero drift:**

| regime | Objective 1 consensus ranks 1,2,3 | Tm (C) | in O2 config |
|---|---|---|---|
| 0 | RT57HC · n-Hexacosane (C26) · PureTemp 58 | 56.5 · 56.5 · 58.0 | exact |
| 1 | RT57HC · n-Hexacosane (C26) · n-Pentacosane (C25) | 56.5 · 56.5 · 54.0 | exact |
| 2 | RT57HC · n-Pentacosane (C25) · n-Hexacosane (C26) | 56.5 · 54.0 · 56.5 | exact (genuine rank-2 tie, both kept) |

`Tm_target_C: 67.0` in all three regimes, matching Objective 1. Objective 2
simulates these nine regime×PCM pairs and nothing else.

## Scope reductions, declared (2026-10-29)

Two gates were reduced to fit the hardware. Both are recorded here and in the
scripts themselves, because a gate that was narrowed without saying so is
worse than a gate that was never run.

**The machine.** Everything runs on an i7-1255U: **2 performance cores + 8
efficient cores** (12 logical), 15.7 GB RAM with ~1.4 GB free. Measured
throughput, same work, same code:

| concurrent jobs | per-job rate | aggregate | wall time for the remaining work |
|---|---|---|---|
| 1 | 4.0 s/sim-year | 0.25 yr/s | 5.8 h |
| **4** | 7.0 s/sim-year | **0.57 yr/s** | **2.5 h** |
| 9 | 35.0 s/sim-year | 0.26 yr/s | 5.7 h |

Nine concurrent jobs ran no faster in aggregate than **one** — most land on
E-cores and the box is near its memory limit. `tn_run_all.py` defaulted to
`cpu_count() - 1 = 11`, which was the worst of both worlds. Default is now 4.

**G9/S6 grid cross-check, cut 15x.** Full scope is 9 (regime, PCM-rank) pairs
x 720 designs x 5 explore years = **32,400 simulated years, ~42 CPU-hours**,
about 17 h wall here -- longer than every other gate combined. Reduced to
**3 regimes x rank-1 PCM x 720 designs x 1 explore year = 2,160 simulated
years**.

What was kept and what was given up, and why:
* **Kept: the full 720-point resolution** in all four design variables
  (6 radii x 8 fractions x 5 flows x 3 arrangements). This is the part that
  decides whether the brute-force front is actually found, which is the whole
  point of the gate.
* **Given up: 5 years -> 1** (2018, mid-explore). The gate compares the
  *shape and position* of the NSGA-II front against the brute-force front;
  the weather year sets the absolute kWh level, not which designs are
  non-dominated. Per-year spread on the designs that matter is measured
  properly by `g9_band`, on the selected designs, at the confirmation step.
* **Given up: 3 PCM ranks -> 1.** Ranks 2 and 3 differ only in material
  properties, not in the geometry of the design space, so the
  front-finding check does not need repeating per material.

`python scripts/g9_s6_grid.py <cid> --full` restores her original scope.

**Resume added** to `g8_s2_doe.py` and `g9_s6_grid.py` (ours). Both iterate
deterministic sequences -- a fixed-seed scrambled Sobol set and an
`itertools.product` grid -- so a row already on disk is byte-for-byte the row
a rerun would recompute, and skipping it changes no result. Delete the CSV to
force a clean rerun. Without this, any interruption to a 5-year-per-design
stage threw away hours.

## Gate-by-gate status

Legend: **DONE** = built and verified · **BUILT** = code written, not yet
run on real data · **RUNNING** · **TODO**

| Rajasthan gate | Status | Where |
|---|---|---|
| G1 demand timing (local-hour FLOOR) | **DONE** — the pre-existing fix had the right offset but rounded it, collapsing 24 local hours onto 12 buckets; now floored | `src/simulation/demand_profile.local_hour_index` |
| G2 model repairs (inner-sphere PCM mass, shell heat capacity, leap day) | **DONE** — outer-volume mass overstated PCM by 6–28 % | `src/simulation/capsule_mass.py` |
| G2 dt convergence | **DONE, and it corrects an earlier claim** — her own gate is met only at **dt = 37.5 s**, not 150 s. Two-tier step adopted: 150 s to search, 37.5 s to report. See below. | `scripts/g2_timestep_convergence.py`, `results/g2_richardson_summary.csv` |
| D3 conduction on inner radius/area | **DONE** | `capsule_mass.pcm_side_resistance`, `heat_transfer.ua_eff_total_w_k(pcm_r_coeff=...)` |
| G3 TES metrics (E_del,45, g_window, g_annual, d_overheat, tau_hold/serve) | **DONE** — in use by the DOE | `src/metrics/tes_metrics.py` |
| G4 multi-node stratified tank (N=10) | **DONE** — numba kernel, **844× faster**, equivalence-validated to machine precision (24/24) against the pure-Python reference in both shield modes | `src/simulation/tank_model_multinode_fast.py` (reference: `tank_model_multinode.py`) |
| **Safety shield (her §3.4, Table 9)** | **DONE** — the big fix: water-side bypass and PCM-side charge block are **two** mechanisms, not one. See the dedicated section below. | both tank models |
| G4 CFD draw-case cross-check | **TODO** — ANSYS Fluent (not OpenFOAM); scale her 30 L@55 °C over 20 L@25 °C case to 100 L | `docs/CFD_VERIFICATION.md` |
| G5 weather inventory + year roles | **DONE** — 15 years × 3 medoids = 45 point-years, 100 % QC pass; explore/select/test/extra assigned | `src/weather/fetch_multiyear_weather.py` |
| G6 O1 shortlist + Phase 4 gates | **DONE** (reused unchanged) | `pipeline.py --stage verify` |
| G7 design-variable ranges | **DONE** — reparameterized to v3.0: volume fraction 0.02–0.30 searched, count derived, bound now enforced | `configs/design_bounds_shared.yaml`, `src/design/volume_fraction.py` |
| G8 S1 Taguchi L9 + ANOVA | **BUILT** | `src/doe/taguchi_screening.py` |
| G8 S2 Sobol DOE | **RUNNING** — 3,456 cases × 5 explore years, paired | `src/doe/sobol_doe.py`, `src/doe/run_sobol_doe.py` |
| G8 S3 surrogate comparison | **DONE (code) / pending real data** — XGBoost **demoted to baseline**, Gaussian-process/Kriging promoted; measured 11.2× less error than XGBoost, posterior sd calibrated 0.969 | `src/surrogate/model_zoo.py`, `src/surrogate/fit_per_pair.py` |
| G8 paired water-only baseline | **DONE** — run in the same worker as its PCM twin (`paired_plain=True`), so gains are differences under identical conditions | `src/parallel/runner.simulate_one` |
| G8 active learning + box-vertex step | **BUILT** — acquisition uses the **GP posterior sd**, not NN committee spread, because the committee was measured to be ~3× overconfident (0.328 coverage vs 0.95) | `src/optimize/active_learning.py` |
| G9 S4/S5 NSGA-II | **DONE** — SBX, polynomial mutation, constrained domination, crowding, exact hypervolume; ZDT1 front RMSE 0.00312. A real hypervolume bug was found and fixed here. | `src/optimize/nsga2.py`, `src/optimize/nsga2_search.py` |
| G9 band (repeatability tolerance) | **BUILT** — year + dt + node + property terms, combined in quadrature, all measured | `src/verify/repeatability.py` |
| G9 S6 dense-grid cross-check, seed stability | **TODO** | — |
| G10 S7 selection funnel S0→S1→S2 + tie-break | **BUILT** — her rule verbatim: lowest PCM mass, then fewest capsules, then largest margin to 65 °C | `src/optimize/selection_funnel.py` |
| G10 S8 held-out lock test | **BUILT** — atomic `O_EXCL` single-use lock, SHA-256 fingerprint of designs + config | `src/verify/held_out_lock.py` |
| G11 + G13–G18 diagnostics | **BUILT** (G13 shield split, G14/G16 stack position, G15 serve decomposition, G17 widened bounds, G11 one-at-a-time); G18 box-vertex ablation **TODO** | `src/verify/diagnostics.py` |
| G12 results registry | **DONE** — every citable number with its source file + content hash; un-run stages report `NOT RUN` rather than stale values | `src/verify/results_registry.py` |
| Parallelization | **DONE** — process pool + worker-side input caching + persistent pool. Two real bugs fixed: `sklearn.isotonic` was costing every worker 10.6 s for a helper the kernel never uses (worker import 12.0 s → 3.0 s), and the pool was being rebuilt per stage. | `src/parallel/runner.py`, `src/simulation/node_layout.py` |
| Test suite | **DONE** — 15 physics invariants, all passing, including regression guards for the shield bug and the demand-hour collapse | `tests/test_physics_invariants.py` |
| New Tamil Nadu pipeline report (.docx) | **TODO** — after the chain completes | deliverable |
| File cleanup / Objective-3 split | **DONE** — 62 docs → 6 live; `archive/old_implementation/_archive/` + `objective3/`, nothing deleted | `scripts/organize_repo.py` |

## Multi-node tank validation log (2026-10-28)

Test case: Regime 0, n-Hexacosane (C26), radial, 72.22mm/32 capsules/0.02066 kg/s
(the current real deployable design), full year, 2016 weather.

| Run | Residual % | Useful energy (kWh) | Max water (C) | Max PCM (C) | Mean f_melt | Wall time |
|---|---|---|---|---|---|---|
| Single-node (existing, reference) | 0.00000 | 1668.7 | 62.42 | 62.30 | 0.2139 | 3.5 s |
| Multi-node, N=1 | 0.00000 | 1669.2 (+0.03%) | 63.16 | 62.75 | 0.2180 | 11.9 s |
| Multi-node, N=10 | 0.08577 | 1751.8 (+4.95% vs N=1) | 71.34 | 57.46 | 0.0788 | 123.3 s |

**Two real bugs found and fixed during this validation** (not a clean first
try -- logged honestly, same as every other fix in this project):
1. First attempt: residual 2580% (N=1) / 1171% (N=10). Cause: the
   collector-charge term was injecting `mdot*cp*T_return` (a mass-flow
   enthalpy) at the matching-temperature node with no corresponding
   removal anywhere in the matrix -- manufactured energy from nothing.
   Fixed: inject the actual heat RATE (`q_collector_trial`, Watts) as a
   pure local source, the same way ambient loss and PCM coupling are
   already rate terms, not flow terms.
2. Second attempt: residual dropped to ~1% but not fully clean. Cause: the
   inversion-removal (PAV) step was applied BEFORE computing that
   sub-step's q_load/q_loss/q_pcm accounting, so the reported flows didn't
   match what the matrix equations actually solved for. Fixed: compute all
   energy accounting from the raw (pre-PAV) solve, apply PAV only to the
   state carried forward into the next sub-step.

N=10 shows real, physically-sensible stratification behavior relative to
N=1: more useful energy (hot water reaches the top/delivery node without
being diluted by the whole tank volume), hotter top node, but a COOLER
PCM (since in the default "center" stack anchor the PCM isn't sitting in
the hottest layer) -- qualitatively the same pattern Rajasthan's own
report describes for multi-node vs single-node.

Validation script: `validate_multinode.py` (repo root) -- not yet folded
into the pytest suite (that happens in the "test suite" step).

## NSGA-II validation log (2026-10-28)

Benchmark: ZDT1 (10 vars, 2 objectives), pop=60, 80 generations, seed=42 --
independent of the real (slow) PCM simulator, to validate the algorithm
itself before wiring it to anything physical.

**One real bug found and fixed**: the first `hypervolume()` implementation
produced NEGATIVE values (impossible by definition) and caused 33/80
generations to show large HV "decreases". Root cause: the 2-D sweep
processed points in the wrong order and used a "skip if not improving"
rule that undercounts -- verified by hand on a 2-point example (points
(0,1) and (1,0) against ref (2,2): true hypervolume is 3, the buggy
version returned 2). Fixed to the standard prefix-minimum staircase
algorithm (ascending x, running minimum y). After the fix: no negative
values, hypervolume rises smoothly from 0 to 1.095.

**Remaining small fluctuations are expected, not a bug**: 9/80 generations
still show a hypervolume dip, but tiny (largest = 0.09% of current HV) and
only once the front has already converged close to the true Pareto front
(RMSE 0.003). This is textbook behavior for crowding-distance NSGA-II
(unlike hypervolume-indicator algorithms such as SMS-EMOA, standard
NSGA-II truncates for diversity, not hypervolume, once the front already
exceeds the population size) -- not something to "fix".

Validation script: `validate_nsga2.py` (repo root).

## Compute budget: the 547-hour problem, and its removal (2026-10-28)

### The problem, as first found
Rajasthan's full plan (3456 Sobol cases x up to 5 explore years = 17,280
simulator runs) assumes her numba-jitted multi-node kernel (1.4-3.1s/year).
At Tamil Nadu's first pure-numpy multi-node speed (~114-194s/year at N=10),
the same budget would have taken **~547 hours**. The fallback plan was to
run the DOE/screening/surrogate/search phases on the fast single-node model
and reserve the multi-node model for final confirmation only -- a real loss
of fidelity in the search phase, accepted only because of the runtime.

### The fix: compile the kernel instead of lowering the fidelity
`src/simulation/tank_model_multinode_fast.py` -- the same equations,
compiled with numba. **Measured: 194.1 s/year -> 0.230 s/year, an 844x
speedup** (`validate_multinode_fast.py`, logged below). The interpreted
version was never arithmetic-bound; it paid per-call overhead 105,120
times per simulated year on three things that are cheap in principle:

| per-substep cost | interpreted version | compiled version |
|---|---|---|
| tridiagonal solve | dense `np.linalg.solve` (LAPACK call, O(N^3)) | inlined Thomas algorithm, O(N) |
| inversion removal | `sklearn.IsotonicRegression()` built + fitted from scratch | PAV written out directly (same algorithm, same result) |
| capsule conductance | full Wakao-Kaguei Re/Pr correlation per PCM node | water-side + wall resistance hoisted to once per YEAR (they are constant); only the f_melt-dependent term stays in the loop |

The third item was a genuine waste present in the interpreted version too:
`h_w`, `r_conv` and `r_wall` depend only on superficial velocity and
capsule diameter, both fixed for an entire run, yet were recomputed ~1M
times per year.

### Measured throughput (`benchmark_parallel.py`, 240 cases, 11 workers)

| configuration | s/sim-year, 1 process | sim-years/hour pooled |
|---|---|---|
| 10-node compiled kernel | **0.381** | **14,300** |
| 10-node, paired with water-only twin | **0.456** | **24,002** |
| single-node (`tank_model.py`, interpreted) | 18.303 | 1,262 |
| *Rajasthan's quoted 10-node kernel, 1 process* | *1.4 - 3.1* | *1,160 - 2,570* |

(0.23 s/year is the Regime-0 validation design; 0.38 is the mean across
randomly sampled designs from the whole box, which reach higher capsule
counts and therefore more PCM nodes. 64% of random box samples -- 154/240
-- are geometrically valid, which is the number to size DOE batches
against.)

**Tamil Nadu is now 3-8x faster than Rajasthan per process, and 6-20x
faster in aggregate once pooled.**

### The surprise: single-node is now the SLOW model
The compiled 10-node kernel is **48x faster than the single-node model**
it was supposed to be the expensive alternative to. `tank_model.py`'s
`run_year` is interpreted and does adaptive stiffness sub-stepping (up to
60 inner substeps per base substep) plus a `hydraulic_model` call every
substep, so it costs 18.3 s/year on box-sampled designs -- far more than
the original ~3.5-6.5 s/year estimate, which came from one favourable
design.

**Therefore the single-node-for-search compromise is withdrawn outright,
and not as a close call.** The 10-node model is simultaneously the
higher-fidelity *and* the faster option, so every stage -- Sobol DOE,
Taguchi screening, surrogate training, NSGA-II search, active learning,
dense grid, diagnostics, robustness -- runs on it. The single-node model
reverts to being purely a regression reference. `SimTask(model="single")`
is kept for deliberate single-vs-multi-node comparison (the G17-style
node-count ablation needs it), never as a speed measure.

### Consequence for the budget
| budget | sim-years | pooled, 11 workers |
|---|---|---|
| 3456 Sobol cases x 5 explore years | 17,280 | ~73 min |
| the same, paired with water-only twins (needed for g_window / d_overheat) | 34,560 | ~86 min |

Rajasthan's own kernel would need 13.4-29.8 h serial for the paired
budget. Hours of compute remain in the plan, but they are now spent on
*more* of the method (full fidelity everywhere, more active-learning
rounds, all 7 diagnostics) rather than on waiting.

### Parallel layer
`src/parallel/runner.py` stacks three separate speedups:
1. the compiled kernel (above);
2. **worker-side input caching** -- the serial path re-parsed an 8760-row
   weather CSV, the demand profile, the PCM database and two YAMLs *per
   case*; now each worker process parses each input at most once
   (`lru_cache` at module level == one cache per process);
3. **process fan-out across cores** -- cases are embarrassingly parallel
   (the year loop itself is strictly sequential, so there is no inner loop
   to parallelize; the parallelism available is across cases, which is
   where it is taken). Threads would not work: the GIL is held through the
   numpy/pandas setup around each run.

Also fixed while building it: `e_del_target()` was making 8760 Python
calls per metric evaluation (`hour_of_day.map(draw_mass_kg_for_hour)`),
which mattered not at all at 194 s/year but cost more than the physics at
0.23 s/year. Replaced with a 24-entry table lookup -- same values, same
rounding rule (both numpy and Python round half-to-even, confirmed by the
equivalence test passing exactly on Q_load).

**Windows note:** workers are *spawned*, so every script that calls
`run_tasks_parallel()` must put its body behind
`if __name__ == "__main__":`, or each worker re-runs the script and builds
its own pool. `run_tasks_parallel()` now detects this and raises a message
saying so, rather than dying with a bare `BrokenProcessPool`.

## Environment confirmed available (checked 2026-10-28)

xgboost 3.3.0, numba 0.68.0, scipy 1.17.1, sklearn 1.8.0 — all present.
`pymoo` (would've given a ready-made NSGA-II) is **not installed** — NSGA-II
is being hand-written (SBX crossover, polynomial mutation, fast
non-dominated sort, crowding distance — standard textbook NSGA-II, not a
simplified stand-in).

## Numba kernel equivalence log (2026-10-28)

`validate_multinode_fast.py` runs the compiled kernel and the pure-Python
reference on the same Regime-0 design and compares everything the
selection funnel and robustness gates read. **All 24 checks passed, to
machine precision** (relative differences 0 to 1.7e-13, against a 1e-6
tolerance), including the integer counters (`n_shield_activations` =
18,839 in both) and all nine whole-year hourly series. Residual identical
at 0.08577%.

That is the expected outcome and the reason the tolerance was set loose
rather than tight: a Thomas factorization and a dense LU factorization of
the same tridiagonal system are mathematically identical and differ only
in rounding accumulation. `tank_model_multinode.py` is kept unmodified as
the reference so this comparison can be re-run any time the kernel is
touched.

## Production timestep: her gate is met at 37.5 s, not 150 s (2026-10-29)

Run on **her** simulator with **her** gate, via her own
`scripts/g2_timestep_convergence.py`, twice as her report does it
(300/150/75, then 150/75/37.5). Merged into
`results/g2_richardson_summary.csv`.

Her acceptance criterion: Gate-1 residual <= 0.1 % in every run, and annual
useful energy changing < 0.05 % each time dt is halved.

| halving onto | max abs change | passes < 0.05 %? |
|---|---|---|
| 150 s | 0.0540 % | **no** |
| 75 s | 0.0713 % | **no** |
| 37.5 s | 0.0410 % | **yes** |

Residual passes everywhere by a wide margin (worst 1.6e-11 %), so this is
purely a time-discretization result. Richardson extrapolation over
150/75/37.5 gives the observed order and the error against the
extrapolated exact value:

| regime / case | observed p | err @150 s | err @75 s | err @37.5 s |
|---|---|---|---|---|
| r0 pcm | 0.80 | 0.168 % | 0.097 % | 0.055 % |
| r1 pcm | 0.82 | 0.083 % | 0.047 % | 0.027 % |
| r2 pcm | 0.99 | 0.141 % | 0.071 % | 0.036 % |
| r0 plain | 0.96 | 0.042 % | 0.021 % | 0.011 % |
| r1 plain | 2.38 | 0.018 % | 0.003 % | 0.001 % |
| r2 plain | 1.44 | 0.019 % | 0.007 % | 0.003 % |

The plain-tank cases converge fast; **the PCM cases are the binding ones,
at p = 0.80-0.99.** That is first order, and it is the melt band that
makes it so -- the enthalpy inversion is only piecewise-smooth, so halving
dt buys about half the error instead of a quarter. Her 50 L Rajasthan tank
passed at 150 s; our 100 L tank does not. That is a property of the tank
being simulated, not a defect in the port, and it is why the value had to
be re-derived rather than inherited.

**What was adopted — a two-tier step**, in `configs/system_config_shared.yaml`:
* `timestep_s: 150` for the DOE, surrogate fitting and NSGA-II. Worst-case
  discretization error 0.17 %, far inside the repeatability band, so the
  *ranking* of designs is unaffected — and it keeps a 128-point Sobol DOE
  across 9 regime-PCM groups affordable.
* `timestep_confirm_s: 37.5` for everything reported: confirmation runs,
  the S0/S1/S2 funnel, the held-out test. No number leaves this project at
  a step that fails her gate.

Searching coarse and confirming fine is standard practice, but it is only
honest if stated, so it is stated here and in the config itself.

**This supersedes an earlier claim in this document** that the study gave
"dt = 150 s, matching her 150 s independently." That earlier study used a
<1 %-per-halving criterion on `max_water_temp_C`; her actual gate is
<0.05 % on annual useful energy, which is roughly twenty times tighter.
150 s passes the loose criterion and fails the real one.

## Earlier dt study, and the safety-shield bug it exposed (2026-10-28)

`src/verify/dt_convergence.py` -- 7-rung ladder (600 s down to 9.375 s),
3 regimes, box-midpoint design, 21 runs in 0.85 min pooled. Criterion
fixed before looking at results: Gate-1 residual < 0.5% AND every decision
metric moving < 1% when dt is halved.

### The numerics are sound
Observed order of convergence for `max_water_temp_C`, fitted from the
three finest rungs: **p = 0.980 / 1.007 / 1.021** across the three
regimes. Backward Euler is formally first-order in time, so p ~= 1 is
exactly right and confirms the ladder is in the asymptotic range (which
is what licenses the Richardson extrapolation below).

### The finding: dt=300 s was manufacturing safety violations
Richardson-extrapolated dt->0 limits, all three regimes:

| quantity | regime 0 | regime 1 | regime 2 |
|---|---|---|---|
| max water temp limit | 61.99 C | 62.01 C | 62.01 C |
| max PCM temp limit | 62.00 C | 62.02 C | 62.01 C |

All six land on **62.0 C, which is exactly the shield trip point**
(65 C PCM limit minus the 3 C guard band). That is the physically correct
answer: a correctly-resolved shield pins both water and PCM AT the trip
temperature. But the model as run reported:

| dt | reported max PCM temp (regime 0) | error vs. 62.0 C |
|---|---|---|
| 600 s | 101.9 C | 64% |
| **300 s (production!)** | **71.8 C** | **15% (9.3 C)** |
| 150 s | 64.8 C | 4.6% |
| 75 s | 62.7 C | 1.1% |
| 9.375 s | 62.02 C | 0.03% |

So at the production timestep the model claimed the PCM reached 71.8 C,
**above its hard 65 C limit**, when the true value is 62.0 C -- comfortably
inside it. Shield activations scaled the same way (10,855 -> 19,303 ->
35,764 -> 65,813), i.e. the shield fired in a roughly constant FRACTION of
substeps, but each coarse-step firing happened after a far larger
excursion.

> **Read the next section before acting on the 62 C figures above.** The
> 62 C Richardson limit is real, but it is a consequence of a SECOND and
> deeper defect -- Tamil Nadu was stopping the collector to protect the
> PCM, which pinned the water at 62 C. Once that is fixed the water runs
> to its own 72 C bypass and these numbers change. The dt findings and the
> order-of-convergence result stand; the specific 62 C value was measuring
> a bug.

### Root cause, and why the fix is not "use a smaller dt"
The shield decided whether to cut the collector using **start-of-substep**
temperatures, so it kept charging for the whole substep after the
threshold was already crossed. The overshoot is therefore proportional to
dt -- a pure artifact of the decision lag, not of the physics.

Brute-forcing to the converged dt=18.75 s costs 16x more compute (~6
s/year), which would have made Tamil Nadu SLOWER than Rajasthan again --
the wrong trade for an artifact.

**Fix: a predictive shield.** Solve the substep assuming the collector
runs; if that solve lands at or past a trip threshold, remove the
collector source and re-solve the same substep. The matrix does not depend
on whether the collector circulates (only `rhs[j_charge]` does), so it
costs one extra Thomas sweep on affected substeps only. The PCM-side check
uses the *projected* end-of-substep PCM temperature, so a PCM node that
would cross its own limit also trips the shield, not just water.

This is the same pattern `tank_model.py` already uses, and has used since
before this port, for its differential-controller reverse-flow check
("solve once assuming circulation, re-solve with the collector off if that
would imply reverse flow") -- applied to the safety shield, where it was
missing. It also models a real controller better: a working sensor cuts
the pump before a 9 C excursion.

Implemented in BOTH the fast kernel and the pure-Python reference, behind
`safety.shield_predictive` (default **true**). Set it false to reproduce
pre-2026-10-28 numbers. Default is true because PCM peak <= 65 C is an
NSGA-II *constraint*, not just a reported metric: searching with the
lagged shield would reject feasible designs and accept infeasible ones.

## THE BIG ONE: the shield was one mechanism, not two (2026-10-28)

This is the defect that made PCM look useless in Tamil Nadu, and it was
found by going back to Manvitha's report and reading what her shield
actually does, rather than reasoning forward from ours.

### Her report, section 3.4 (Table 9), defines TWO mechanisms
| mechanism | her wording | effect |
|---|---|---|
| water-side bypass | "Collector stops while top-node water is at or above 72 C" | stops the collector, at WATER's own limit |
| PCM-side charge block | "Capsule UA set to zero while PCM at or above 62 C **and water hotter than PCM**; discharge never blocked" | decouples the capsules only; collector keeps running |

### What Tamil Nadu was doing instead
It collapsed both into one trip:
`water_trip_C = min(75-3, 65-3) = 62` and then **stopped the collector**
whenever the PCM got hot. So the PCM's 65 C material limit was throttling
the ENTIRE system: water was pinned at 62 C, PCMs melting at 54-58 C had
only ~4.5 C of charging window, barely melted, and acted as dead mass
displacing water.

That last part is quantitative: non-melting paraffin has a volumetric
sensible heat capacity of ~1,556 kJ/m3K (2.0 kJ/kgK x 778 kg/m3) against
water's 4,180 -- about **37%**. PCM that does not melt is strictly worse
than the water it replaced, which is why g_window got monotonically worse
with more PCM (correlation -0.96 to -0.99; -39 kWh at 10% fraction
falling to -267 kWh at 30%).

### Investigation trail (what was ruled out, in order)
1. *"Not enough PCM"* -- the design bounds could only reach 9.9% volume
   fraction at 100 L (see below). **Refuted**: reparameterizing to reach
   10-30% made g_window WORSE, monotonically.
2. *"The tank never gets hot enough to melt PCM"* -- **Refuted** by the
   plain tank's own temperature duration curve: it is above 57 C for
   2,380-2,714 h/yr and reaches 72 C.
3. *"Wrong PCM melting band"* -- a sweep over 11 PCMs from 45 to 58 C
   showed g_window correlating **-0.98** with melting temperature. This
   line of inquiry is **retracted** (see "The off-list sweep — RETRACTED"
   above): it ran against the pre-shield-fix simulator, it required PCMs
   Objective 1 did not shortlist, and its premise -- that `Tm_target_C:
   67.0` was an Objective 1 defect -- was mistaken. The sweep and its
   numbers have been deleted rather than kept as a "comparison".
4. *"Raise the 65 C PCM cap to 75 C"* -- tested, and it did work (9/9
   shortlisted combos positive). **Not applied**: it changes a safety
   limit, and Rajasthan achieves the same thing at 65 C. Keeping a
   defensible safety limit and fixing the mechanism is strictly better
   than relaxing the limit to accommodate a bug.

An apparent internal contradiction was also recorded here -- that
Objective 1's `Tm_target_C: 67.0` exceeds Objective 2's 65 C PCM cap
(62 C after the guard band), so "the targeted PCM could never melt."
**There is no contradiction.** `Tm_target_C` is a ranking criterion
(`crit_Tm_fitness` / `f_Tm`) inside Objective 1's MCDM, not a melting
point any material must have; the PCMs it selected melt at 54.0-58.0 C,
well inside the cap. The real defect was entirely on Objective 2's side --
the single-trip shield -- and is fixed below.

### The fix
Implemented in BOTH the fast kernel and the pure-Python reference:
* water-side bypass at `max_water_temp_C - guard` = 72 C, tested over
  **every** node (not just the outlet: the collector injects into whichever
  node matches its return temperature, and the inversion-removal step then
  lifts the nodes above it -- testing only the top node let interior
  heating slip past and showed up as a measured 64.88 C peak against a
  62 C trip);
* PCM-side charge block zeroing `ua_per_node[k]` while that capsule group
  is at/above 62 C and the water is hotter, charging direction only,
  discharge never blocked;
* both decided on the PROJECTED end-of-substep state, with a re-solve.
  The PCM side needs this as much as the water side: with the lagged
  decision a capsule group crossed from under 62 C to a measured
  **73.9 C in a single 300 s substep** -- past its 65 C hard limit --
  because at 15% volume fraction the group's UA is large and the PCM
  node's time constant is far shorter than the substep. Blocking a node
  changes `diag`/`rhs`, so the matrix is rebuilt (up to two assemble/solve
  passes), unlike the water-side re-solve which only touches `rhs`.
* shield counters are now SPLIT (`n_shield_water_activations`,
  `n_shield_pcm_activations`, and matching hourly columns), because
  `d_overheat` is defined on the split (her section 7.5).

### Result: 12/12 regime x PCM combinations positive, all limits respected
At 15% volume fraction, 0.05 m capsules, 0.03 kg/s, staggered:

| | g_window | f_melt | max PCM | max water | residual |
|---|---|---|---|---|---|
| ours, 12/12 combos | **+48.9 to +112.6 kWh** | 0.17-0.26 | 62.3-63.1 C | 71.98-72.00 C | 0.007-0.055% |
| limit | -- | -- | <=65 C | <=75 C | <0.5% |
| *her report, for comparison* | *all positive, min 95.7* | *--* | *64.1 C* | *73.3 C* | *<=0.0698%* |

Water now runs to its own 72 C bypass while the PCM sits at ~62 C, which
is exactly what the two-mechanism design is for. **No safety limit was
changed and Objective 1's shortlist is untouched.**

## Model repairs ported: G1, G2, D3 (2026-10-28)

Three repairs her report lists that Tamil Nadu did not have. All three are
in BOTH tank models and the numba kernel ("mechanisms kept in both tank
models", her Table 9).

### G1 -- demand hour is the FLOOR of local (IST) time
Her `_demand_hour_of_day` uses "local_hour, floor of IST". Tamil Nadu had
the right offset (+5:30) but rounded the result. India's half-hour offset
means every UTC hour maps to an X.5 local value, and both numpy and Python
round halves to even, so:

```
UTC 00 -> IST 05:30 -> floor 5 | round 6
UTC 01 -> IST 06:30 -> floor 6 | round 6   <- collision
UTC 02 -> IST 07:30 -> floor 7 | round 8
UTC 03 -> IST 08:30 -> floor 8 | round 8   <- collision
```

**Measured: the rounding collapsed 24 local hours onto only 12 distinct
buckets** -- half the 24-point demand curve was never read at all, and
each surviving bucket was used twice. 50.0% of the year's hours (4,392 of
8,784) mapped to the wrong local hour.

Now derived once, in one place, by
`src/simulation/demand_profile.local_hour_index()`, shared by all three
models so the convention cannot drift between them. (For scale, her report
measures the related UTC-vs-local error at 30.7 / 34.9 / 32.4 % of
plain-tank annual useful energy.)

### G2 -- PCM mass from the INNER sphere, shell capacity in the PCM node
Her wording: "PCM mass from inner sphere (D - 2 t_wall); wall heat
capacity carried in the PCM node ... Older outer-volume mass overstated
PCM by 11.5 / 5.9 %."

A capsule with an 0.8 mm aluminium wall does not hold D-worth of PCM.
Measured overstatement from using the outer volume, at 770 kg/m3:

| capsule D | m_pcm (inner) | m_pcm (outer) | overstated | shell mass | cp augment |
|---|---|---|---|---|---|
| 20 mm | 0.251 kg | 0.323 kg | **+28.4%** | 0.250 kg | 897 J/kgK |
| 30 mm | 0.924 | 1.089 | +17.9% | 0.579 | 564 |
| 50 mm | 4.571 | 5.040 | +10.2% | 1.643 | 323 |
| 80 mm | 19.428 | 20.642 | +6.2% | 4.257 | 197 |

(consistent with her 11.5 / 5.9 % at her design sizes). The error inflates
both sensible and LATENT capacity, and latent capacity is the entire point
of the store, so it fed straight into g_window.

The shell is also not thermally inert. Instead of a third node, its heat
capacity is folded into the PCM node as an augmented specific heat,
`cp_aug = cp_pcm + m_wall*cp_wall/m_pcm`, applied to the solid and liquid
branches with latent heat untouched (aluminium does not melt). Because
`capsule_enthalpy`'s h(T) is built from those cp values, h_s, the melt
band and the h -> (T, f_melt) inversion all stay consistent automatically,
and `m_pcm * h` totals PCM *and* shell energy so Gate 1 still closes
without a separate wall term. At 20 mm capsules the shell nearly doubles
the effective cp -- a term the model previously ignored completely.

Aluminium rho 2700 kg/m3 and cp 900 J/kgK are handbook values, read from
config if present and otherwise defaulted; her report notes the same
("not in the frozen config").

### D3 -- PCM conduction path on the inner radius and inner area
"PCM conduction path uses inner radius and inner area (thickness = inner
radius)." Heat entering a capsule travels inward from the inner wall
surface. The lumped r/(5 k A) sphere approximation is unchanged; only the
geometry it is evaluated on moves from outer to inner.
`ua_eff_total_w_k()` takes an explicit `pcm_r_coeff` for this rather than
changing its default silently; water-side convection and the thin wall
still act on the OUTER surface, which is correct.

All implemented in `src/simulation/capsule_mass.py` (same module name her
report uses).

### Result after G1 + G2 + D3, rank-1 PCM, 15% fraction
| regime | g_window | PCM mass | f_melt | max PCM | max water | residual |
|---|---|---|---|---|---|---|
| 0 | +148.17 kWh | 13.49 kg | 0.252 | 62.58 C | 71.85 C | 0.0292% |
| 1 | +107.34 | 13.49 | 0.211 | 62.80 | 71.92 | 0.0070% |
| 2 | +131.59 | 13.49 | 0.237 | 62.82 | 70.61 | 0.0087% |

Every gate passes (PCM <=65, water <=75, residual <0.5%).

## The PCM charge block has to iterate to a fixed point (2026-10-28)

Caught by the first full Sobol DOE, which is exactly what a 17,280-case
sweep is for: it reaches corners a spot check does not.

**Symptom.** 120 of 11,070 geometrically-valid designs reported a PCM peak
above the 65 C hard limit, up to **68.51 C**. Every one of them sat in the
same corner of the design space:

| | breaching designs (median) | the rest (median) |
|---|---|---|
| pcm_volume_fraction | 0.279 | 0.151 |
| capsule_diameter_m | 0.041 | 0.060 |
| n_capsule | 757 | 120 |
| flow_rate_kg_s | 0.0113 | 0.0304 |

Evenly split across all three arrangements (40/40/40), so not an
arrangement bug -- a UA-magnitude bug.

**Cause.** The predictive PCM-side block was implemented as TWO passes:
solve, block any capsule group whose projected end-of-substep temperature
would reach the 62 C trip, re-solve. That is not enough. Blocking a group
removes a heat SINK, so the water left in the tank runs hotter, and that
can push a *different* group -- one that was comfortably fine in the first
solve -- over its own trip. With 757 small capsules the per-group UA is
large enough for this to happen in a single 150 s substep, and nothing
re-checked after the second solve.

**Fix.** Iterate block-and-resolve until no new group needs blocking. The
iteration is monotone (a group blocked within a substep is never
unblocked), so it terminates in at most `n_pcm_nodes` passes; the cap is
`n_pcm_nodes + 2` for the final no-change confirmation. Applied to both
the numba kernel and the pure-Python reference.

**Verified** on the exact breaching corner: 776 capsules at 41 mm and
0.0113 kg/s now peaks at **62.00 C** -- pinned at the trip, as it should
be -- with the energy residual still at 0.080 %. Three such corners are
now parametrized regression tests
(`test_high_ua_corner_respects_pcm_limit`), so a future two-pass
regression fails loudly.

The pre-fix DOE output is kept at
`archive/old_implementation/_archive/results_pre_shield_fix/sobol_doe_results_pre_fixedpoint.csv`
for comparison; the DOE was re-run, because constraint data from a shield
that breaches its own limit cannot be used to handle that constraint.

## Design space reparameterized: volume fraction searched, count derived (2026-10-28)

Found while investigating the above, and a real defect regardless.
`design_bounds_shared.yaml` v2.0 declared
`pcm_volume_fraction: {min: 0.10, max: 0.20}` and justified its
`capsule_count.max = 37` with "count=37 reaches
pcm_volume_fraction=0.198". That arithmetic was correct **for a 50 L
tank**. The tank was later specified at 100 L and the ceiling was never
rescaled:

| tank | max reachable pcm_volume_fraction under v2.0 bounds |
|---|---|
| 50 L | 0.1984 (matches the config's own claim) |
| 100 L (actual) | **0.0992** |

So the entire declared band was unreachable -- the achievable maximum sat
just BELOW the declared minimum. Nothing caught it because
`pcm_volume_fraction` was declared in the config but **never enforced** in
`src/design/constraints.py`.

v3.0 (`config_v3.0_2026-10-28`):
* `pcm_volume_fraction` is now the SEARCHED variable, range 0.02-0.30 --
  matching the Rajasthan study's own searched band ("2 to 30 % of tank
  volume", her Table 2) and her parameterization ("PCM outer-volume
  fraction of the tank; capsule count N is derived");
* `capsule_count` is DERIVED (`src/design/volume_fraction.py`) and keeps
  only a loose sanity ceiling; the real limits remain the unchanged
  geometric overlap/passage/pressure checks;
* the fraction bound is now actually enforced in `constraints.py`;
* the ACHIEVED fraction (integer count, so the request is not hit exactly)
  is what gets recorded and fed to surrogates, never the requested value.

Only the SEARCH SPACE is reparameterized: `DesignVector`,
`check_design()` and `compute_geometry()` are untouched and still take an
integer count, so all validated geometry logic is unchanged.

Per the v2.0 note's own instruction, this shared-config change invalidates
the other three states' Phase 2-8 results. Only Tamil Nadu is being
re-run; the other three are flagged here, not silently left stale.

## Surrogate: XGBoost demoted to baseline, Gaussian process promoted (2026-10-28)

The review comment that XGBoost is "too easy" is correct, and the
structural reason is stronger than novelty. `src/surrogate/model_zoo.py`
holds four candidates behind one interface; all four are still scored on
every pair, so the demotion is a measurement, not an assertion.

Boosted trees are a bad structural match for THIS job (rank designs on a
smooth 3-input surface from ~128 points, and tell the optimizer where it
is unsure): they are piecewise-constant, so the fitted surface is a
staircase with no usable gradient; they cannot extrapolate past the
training hull at all (which is exactly what the box-vertex and
widened-bounds diagnostics probe); and they have no principled predictive
variance.

Gaussian-process (Kriging) regression with an anisotropic Matern-5/2
kernel is both the more advanced instrument and the right one: smooth and
differentiable, exact closed-form posterior sd, and length scales learned
per input dimension by marginal-likelihood maximization (which doubles as
a sensitivity readout cross-checkable against the Taguchi ANOVA).

### Measured on a synthetic smooth 3-input response at n=128
(`validate_surrogates.py`, with one deliberately irrelevant input)

| model | Spearman | RMSE/sd(y) | +/-2sd coverage |
|---|---|---|---|
| kriging_gp | 0.99930 | **0.01338** | **0.969** |
| nn_ensemble | 0.99931 | 0.01602 | 0.328 |
| quadratic_rsm | 0.98473 | 0.10112 | 0.945 |
| xgboost_baseline | 0.99194 | 0.15040 | n/a |

* **XGBoost carries 11.2x the GP's error.**
* The GP's posterior sd is calibrated (0.969 vs. a 0.95 target).
* **The NN ensemble's uncertainty is NOT** -- 0.328 coverage, i.e.
  overconfident by roughly 3x. This matters beyond model choice:
  Rajasthan's active-learning loop drives on NN *committee disagreement*,
  and this says that signal is badly scaled. Tamil Nadu's active learning
  will use the GP posterior sd instead, which is measured to be
  calibrated.
* The GP recovered the planted irrelevant input (length scales
  [8.3, 21.2, 1e4-ceiling]); a length scale at the ceiling is the
  "this input does not matter" readout.
* The quadratic RSM stays in the bake-off as a real contender, not a straw
  man -- on a near-quadratic response it scores 0.985.

## Next steps (in order, updated 2026-10-28 session 2)

Done: weather fetch, multi-node tank (validated), **numba kernel (844x,
equivalence-validated)**, **parallel execution layer**, NSGA-II core
(validated), Sobol DOE generator, Taguchi screening generator, TES metrics
module. The single-node-for-search compromise is **withdrawn** -- see the
compute-budget section; everything now runs at full 10-node fidelity.

1. dt convergence study (G2) -> pick production timestep. Script written
   (`src/verify/dt_convergence.py`, 12 runs, parallel) -- not yet run
2. Three-way surrogate comparison module (XGBoost / quadratic RSM / NN
   ensemble, per regime x PCM pair) -- not yet written
3. Wire NSGA-II's evaluate_fn to the real 10-node simulator + the trained
   per-pair surrogate, batched through `run_tasks_parallel`
4. Actually RUN the Sobol DOE at 10-node fidelity (~12 min pooled, paired)
5. Active learning loop (committee disagreement among the 3 surrogates) +
   box-vertex fix
6. Dense-grid cross-check, seed stability, boundary detector
7. Repeatability band -> selection funnel (S0/S1/S2) -> tie-break (reuses
   existing rule) -> RE-CONFIRM every finalist on the multi-node model ->
   re-verify all 3 regimes still cross every robustness threshold
8. Held-out lock test (one-shot, multi-year weather now available)
9. 7 diagnostic/ablation studies
10. Results registry + regenerated RESULTS.md + new .docx report
11. Test suite
12. File archive/cleanup pass
