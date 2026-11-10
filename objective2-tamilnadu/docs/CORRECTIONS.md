# CORRECTIONS — Objective 2 (Tamil Nadu)

**Applied 2026-11-09.** Companion to
`../../tamilnadu_pipeline/docs/era5_tamilnadu/CORRECTIONS.md` (Objective 1).
Kept per-tree so each objective stays self-contained.

**One code change, no re-runs.** The only non-documentation edit is a corrected
module docstring in `src/optimize/surrogates_advanced.py` (O2-1). No pipeline
stage was re-run and **no Objective 2 result changed**. 89/89 tests pass.

> **What this pass can and cannot do.** Item O2-1 found a genuinely wrong claim
> in the repository. Fixing it does not change which surrogate the search used —
> it changes what the repository *says* it used, bringing the text in line with
> the results file that was authoritative all along. The designs, the held-out
> numbers and the gates are untouched and remain correct.

---

## Verification first

Each of the eight reviewed items was checked against the results files before
any edit. **Three of the eight were already correct in the repository**, and two
of the review's "blocking" claims were false.

| item | verdict after checking | action |
|---|---|---|
| **1** Conflicting surrogate winner | **Real defect — but the opposite of what the review said.** `stacked won all 9 pairs` is **correct and authoritative**. The *other* claim — "XGBoost won 21 of 27 groups, GP came third" — is the wrong one, and it is not in a report but in a **code docstring**. No current results file supports it. | Corrected the docstring. **O2-1** |
| **2** Held-out test status unclear | **False — the test ran.** `results/held_out_test.lock` records `run_id heldout_2da11230bfb5` at `2026-10-30T09:56:22Z` with a selection fingerprint; `g10_heldout_results.csv` holds the per-year rows for 9 designs × 5 years. **Not a blocker.** | Recorded the evidence. **O2-2** |
| **3** Tank/collector specs wrong | **False for the pipeline.** `configs/system_config_shared.yaml` already reads `volume_L: 100.0` and `area_m2: 2.5`. The only 50 L / 1.5 m² design figures sit in the already-superseded `objective3/` handoff; other mentions are deliberate comparisons to the Rajasthan source study. | Confirmed; see **O2-3** |
| **4** "Global optimum" overclaimed | **True.** The 30 % cap is demonstrably binding and the flow optimum may be a model artefact. | New section. **O2-4** |
| **5** CFD presented as validation | **Partly true.** `docs/CFD_VERIFICATION.md` was already honest ("a sanity check, not a replacement", "not a validated, production-grade CFD study", and it reports 0 % liquid fraction openly). But `OVERVIEW.md` called it an "independent physics check". | Reclassified. **O2-5** |
| **6** Pareto front vs selection not separated | **True** — the data existed but was never presented as front-then-funnel. | New section. **O2-6** |
| **7** "Surrogate-assisted search" may outrun the evidence | **Largely unfounded.** Every stage `g2`…`g24` has result files on disk. Two real scope limits found instead. | Evidence table. **O2-7** |
| **8** "Validation" used for three different things | **True.** | Terminology standard. **O2-8** |

---

## O2-1 — The surrogate winner, settled

**Authoritative file: `results/g8_s3_selection.csv`.** It picks `stacked` in
**all 9 (regime, PCM) pairs**. That is the surrogate the NSGA-II search used, so
*"stacked won all 9 pairs" was right.*

The claim that conflicts with reality is the other one. `surrogates_advanced.py`
asserted in its module docstring: *"on the real DOE, XGBoost won 21 of 27 groups
and the GP came third."* Measured from `results/g8_s3_comparison.csv` (360 rows
= 9 pairs × 4 targets × 5 families × 2 validation schemes), winner = lowest RMSE
per group:

| grouping | result |
|---|---|
| per (pair, target), `designs_5fold`, 36 groups | `stacked` 14, `gp_ard` 13, `rsm_quadratic` 5, **`xgboost` 4** |
| per (pair, target), `leave_one_year_out`, 36 groups | `stacked` 14, `gp_ard` 14, `rsm_quadratic` 4, **`xgboost` 4** |
| base families only (stacked removed), 72 groups pooled | **`gp_ard` 42**, `rsm_quadratic` 18, `xgboost` 12 |

So **XGBoost wins 4 of 36, not 21 of 27**, and the **GP is first among the base
families, not third.** The "27 groups" arithmetic (9 pairs × 3 targets) belongs
to an older 3-target DOE and never applied to this 4-target one.

The docstring now carries the measured table and an explicit instruction not to
quote the old figures. **Nothing downstream changes:** the search consumed
`g8_s3_selection.csv`, not the docstring.

**This error had propagated.** `documentation/OBJECTIVES_AND_ALGORITHMS.md`
repeated the 21-of-27 figure from the docstring; it has been corrected too.

## O2-2 — Held-out test: run, locked, recorded

Not an open question.

| evidence | value |
|---|---|
| `results/held_out_test.lock` | `run_id heldout_2da11230bfb5`, `utc 2026-10-30T09:56:22.980791+00:00`, selection fingerprint `2da11230…1f6e298` |
| `results/g10_heldout_results.csv` | 9 designs × 5 years (2011–2015), per-year paired rows |
| coverage | the chosen design **plus the best design of every other shortlisted PCM** — 9, not 3, so it cannot be a cherry-pick |
| outcome | 9/9 beat the water-only twin; PCM peak 63.4–64.0 °C (limit 65); water peak 72.2–72.9 °C (limit 75) |

The "not yet performed" wording the review cites is from a progress document
written *before* 2026-10-30. It was true when written and is now stale.

## O2-3 — Tank and collector specs: already correct

`configs/system_config_shared.yaml` → `tank.volume_L: 100.0`,
`collector.area_m2: 2.5`. Every result in `results/` was produced against this.

The 50 L / 1.5 m² figures appear in three distinct ways, and only one is wrong:

1. **Wrong, already flagged:** `objective3/obj3_environment_contract_tamilnadu.json`
   and `objective3/OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` (both 2026-10-27)
   describe the superseded 50 L design. These must be regenerated before
   Objective 3 starts — see `../../documentation/README.md` → "Known gaps".
2. **Legitimate:** `system_config_shared.yaml`'s own comment
   *"TAMIL NADU: project instruction (hers is 50 L)"* — a deliberate note that
   the Rajasthan source study used 50 L.
3. **Legitimate:** historical entries in `RESULTS.md` and
   `RAJASTHAN_METHOD_PORT_PROGRESS.md` below their superseded banners, which
   record the 2026-10-27 resize as history.

## O2-4 — Not a global optimum

Added to `OVERVIEW.md`. The selected designs are **the best found within the
declared search bounds**, and two bounds matter:

- **The 30 % PCM-fraction cap is binding.** The `g17` widened-bound diagnostic
  shows 40 % raises window gain by more than the repeatability band in **every**
  regime, with both peaks still inside 65 °C and 75 °C. The cap is
  administrative — the packing engine accepts 28–48 % at R 40 mm, and the only
  literature in the files read (Chen 2025) covers 10–20 %. A 40 % run is
  planned, not done.
- **The flow optimum may be a model artefact**, because the collector's F_R is
  flow-independent in this model. `g17` does establish that the *upper* flow
  bound is not limiting (0.080 kg/s moves `g_window` by less than the band).

Required wording: **"best design within the declared 2–30 % PCM-fraction and
0.010–0.050 kg/s search bounds"**, never "optimal design".

**Consequence for Objective 3:** it inherits a design that is *good and
verified*, not one proven optimal. It must not treat the inherited flow value as
a physical optimum to defend.

## O2-5 — CFD reclassified

`OVERVIEW.md`'s two-simulator table called Fluent an "independent physics
check"; it now reads **"model consistency cross-check (NOT experimental
validation)"**.

The substance was already documented honestly in `docs/CFD_VERIFICATION.md` —
only the framing needed fixing. The limits, restated: one capsule, six hours;
three v3 cases returned **0 % liquid fraction**, which that document records as
the honest result rather than suppressing; melt fractions elsewhere are
conservative because first-order upwind is the only scheme under which all four
PCMs converge; the mesh is a symmetry half-slice, excluding buoyancy-driven melt
convection.

Required wording: **"CFD cross-check of selected modelling assumptions"**, never
"CFD-validated design".

## O2-6 — Pareto front and selected design, reported separately

Added to `OVERVIEW.md`. NSGA-II returns a *set*; the front and the pick are now
separate tables.

Front quality (`g9_grid_check.csv`): **all 9 (regime, rank) pairs** are now
cross-checked against a 720-point dense grid (was rank-1 only; see O2-14).
Final fronts hold 50–65 designs against the grid's 8–13; hypervolume ratios run
1.014–1.148, so the search front dominates the grid in every pair; and every
ε-indicator value on every objective sits inside the repeatability band
(27.99 / 27.99 / 107.98 kWh).

Funnel (`g10_selection_r{0,1,2}.json`): 90 candidates per regime → S0 (within
band on `g_window`) 14 / 10 / 12 → S1 5 / 3 / 5 → S2 3 / 3 / 2 → chosen.

**The tie-breaks were declared before results were seen** (plan WP6, decisions
D9/D10). Regime 0 shows the rule doing real work: RT57HC scores *higher* on
window energy than the chosen PureTemp 58 (297.1 vs 283.4 kWh/yr), but the gap
is inside the band, so S0 treats them as tied and overheating decides — 856 vs
1059 shield-hours, favouring PureTemp 58. The higher-energy design was **not**
chosen, and the documented rule is why.

## O2-7 — Stage evidence audit

Every stage has results on disk, so "surrogate-assisted constrained
multi-objective search" is a supportable description of what ran:

| stage | evidence |
|---|---|
| `g2` timestep convergence | 2 CSVs (300/150/75 and 150/75/37.5 ladders) |
| `g3` metrics, `g4` multinode | `g3_metrics_report.csv`, night-daily CSVs, `g4_multinode_report.csv` |
| `g6` O1 PCM ingest | `results/phase4_verification_o1_pcms.txt` — Go/No-Go: **GO** |
| `g7` sensitivity, packing, baseline | 6 CSVs |
| `g8_s1` Taguchi L9 + ANOVA | 18 CSVs (9 pairs × design + ANOVA) |
| `g8_s2` Sobol DOE | 9 CSVs (one per pair, 128 points each) |
| `g8_s3` surrogate bake-off | `g8_s3_comparison.csv` (360 rows), `g8_s3_selection.csv` |
| `g9_s4/s5` NSGA-II + active learning | 10 seed-front CSVs |
| `g9_s6` dense grid | 3 CSVs |
| `g9_band` repeatability | 3 CSVs + `wp6_band.csv` |
| `g10` selection + held-out | 6 selection files, `g10_heldout_results.csv`, lock |
| `g11`, `g13`–`g18`, `g20`–`g24` | 3 CSVs each (per regime), `g18` 1 |

**Two real scope limits, stated rather than implied:**

1. ~~**The dense grid covers rank-1 PCM pairs only**~~ — **CLOSED 2026-11-09
   (O2-14).** All 9 (regime, rank) pairs now have a dense-grid cross-check, so
   the "search missed no region" claim holds for every pair, not just rank 1.
2. **`g18`'s with/without comparison is incomplete.** Its CSV holds only the
   `base` state; `novert` and `vert` never ran. The generated results document
   now prints an explicit *"This comparison is INCOMPLETE"* note instead of the
   previously hardcoded reading, which quoted numbers absent from the data.

## O2-8 — Three kinds of checking, three names

Added to `OVERVIEW.md`:

| what it is | call it | status |
|---|---|---|
| energy-balance and unit tests in code (89 tests, Gate-1 residual) | **simulator verification** | done |
| ANSYS Fluent against the fast model's assumptions | **model consistency cross-check** | done, with O2-5 caveats |
| physical measurement on hardware | **experimental validation** | **NOT DONE** — Objective 4 |

---

## O2-9 — The Objective 3 contract, built (2026-11-09, second pass)

**This was the single blocker on starting Objective 3, and it is now closed.**

The problem: no Objective 3 contract existed for the current results. The only
Tamil Nadu contract (2026-10-27) described a superseded run, and the newer
generator `build_obj3_contract_v2.py` is **hardcoded for Rajasthan** — it reads
`obj3_environment_contract_rajasthan.json`, which is absent from this tree, and
writes `..._rajasthan_v2.json`.

**What was built:**

| artefact | what |
|---|---|
| `src/handoff/build_obj3_contract_tamilnadu.py` | new generator. Reuses the unchanged generic blocks (action space, reset scenarios, acceptance tests, state schema) from the 2026-10-27 contract; rebuilds everything design- and result-specific from live files |
| `scripts/g25_obj3_contract.py` | pipeline-convention wrapper, with an input-presence check that fails with a readable message rather than a traceback |
| `tn_run_all.py` stage 31 | `g25_obj3_contract`, registered after `g10_test` since it reads the held-out outputs |
| `results/obj3_environment_contract_tamilnadu_v3.json` | the contract, 35.8 kB, also copied to `objective3/` |

**Everything in it is read from a file** — `g10_selection_r{0,1,2}.json`,
`g10_heldout_results.csv`, `held_out_test.lock`, `wp6_band.csv`,
`system_config_shared.yaml`, `states/tamilnadu.yaml` — and each is SHA-256
recorded in the contract's `provenance` block.

**The corrections from this pass are carried into the contract itself**, so
Objective 3 cannot inherit a claim this audit has already retired:

- `design_space_caveats` — `NOT_A_GLOBAL_OPTIMUM: true`, the binding 30 % cap,
  and an explicit instruction not to treat the nominal flow as a physical
  optimum (O2-4).
- `temperature_specification` — the master table, and the finding that
  67 °C vs 65 °C is **not** a safety problem, plus the open 60 °C/45 °C
  service mismatch.
- `verification_status` — simulator verification / model consistency
  cross-check / experimental validation kept separate, with Objective 1's weak
  non-significant physics agreement stated plainly (O2-5, O2-8).
- `held_out_test` — status, lock id, timestamp and fingerprint, closing the
  "was it run?" question inside the machine-readable artefact.

**A chain-integrity assertion is built in**: the generator asserts every
selected PCM is in that regime's Objective 1 shortlist, so a substituted
material cannot reach Objective 3 silently.

**Unit confusion removed.** The docs quote 81.6 mm; the selection files store
`R_in_m = 0.04`, i.e. 80.0 mm inner. These differ by the 0.8 mm aluminium wall
on each side. The contract now emits **both** `capsule_inner_diameter_mm` and
`capsule_outer_diameter_mm`.

**Retired:** the 2026-10-27 contract and `OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md`
moved to `archive/superseded_obj3_contract_2026-10-27/`. The handoff document
was rewritten against real output; its old headline claims — "PCM loses to a
plain tank in every regime (−12.5 % to −14.8 %)" and "P(meets demand) = 0–4 %" —
are **false for the current designs**, which beat the water-only twin 9 of 9.

---

## O2-10 — The generated results document (applied earlier the same day)

**Recorded here 2026-11-09 after an audit found it missing from this file.** It
was applied earlier in the day and written up only in
`../../documentation/README.md`, which is not where an Objective 2 correction
belongs.

`scripts/g12_results_doc.py` **crashed every time it ran**:
`IndexError: single positional indexer is out-of-bounds` at line 270, on
`w1[(w1.pair == tag) & (w1.state == st)].iloc[0]` — an empty selection indexed
without a guard. Cause: `g18_issue1_with_without.csv` holds only the `base`
state, but the generator assumed `base`, `novert` and `vert` all existed.

Three things were wrong, all fixed:

1. **Its output had never existed.** It writes `docs/04_RESULTS.md` — *not*
   `docs/RESULTS.md`, which is a separate hand-maintained file. Because the
   script had never once succeeded, the auto-generated results document — the
   one in which no number is typed by hand — was simply **absent from the
   repository**. It now exists and regenerates cleanly.
2. **The narrative asserted numbers its own table could not show.** The
   hardcoded reading quoted `novert`/`vert` figures ("23.5 kWh against 13.8",
   "3.1", "r1 5.0 without, 1.8 with") that are not in the results at all. It now
   prints an explicit *"This comparison is INCOMPLETE"* note naming the missing
   states, and the full reading only when all three are present.
3. **The document was titled "Objective 2, Rajasthan"** inside the Tamil Nadu
   tree — a leftover from the method port. Now "Tamil Nadu".

## O2-11 — The stale-path-reference count, and a correction to my own figure

**Also applied earlier the same day and missing from this file until now.**

`OVERVIEW.md` said: *"`g12_verify_docs` reports ~68 stale path references,
almost all inside the historical progress log, which legitimately describes
paths as they were."*

**The count was right; my first correction of it was wrong.** I initially
reported the real figure as **236** and called the claim understated. That 236
came from the stale snapshot `results/_log_g12_verify_docs_all.log`
(2026-10-31 16:46) — and the docs were repaired three minutes later at 16:49. A
live run on 2026-11-09 gives **68**. The original "~68" was correct all along,
and the 236 figure has been reverted everywhere it appeared.

**The second half of the original claim is still wrong**, and that part stands
corrected. Only 15 of the 68 are in the progress log:

| doc | missing refs |
|---|---|
| `docs/DATA_REFERENCE.md` | 31 |
| `docs/RAJASTHAN_METHOD_PORT_PROGRESS.md` | 15 |
| `docs/HOW_TO_RUN.md` | 15 |
| `README.md` | 3 |
| `docs/CFD_VERIFICATION.md` | 3 |
| `docs/RESULTS.md` | 1 |

So "almost all in the progress log" covers 22 %, not almost all. `OVERVIEW.md`
now carries 68 with this breakdown. **The 68 references themselves are not
repaired** — only the claim about them is honest.

## O2-12 — Optimisation method references added

**This was review item 2.8 and had not been done.** An audit on 2026-11-09
found `docs/REFERENCES.md` contained **no citation for NSGA-II at all**, though
it is the core search algorithm of this objective. Six method sources added:

| key | covers |
|---|---|
| `Deb2002` | NSGA-II itself — non-dominated sorting, crowding distance, elitism, constrained domination, SBX and polynomial mutation (`src/optimize/nsga2.py`) |
| `Bhattacharjee2016` | multi-surrogate competition rather than one chosen model (`g8_s3_compare.py`) |
| `Bradford2018` | GP surrogates for expensive black-box MOO (`gp_ard`, `g20_gp_bo_comparison.py`) |
| `Kumar2024` | the Taguchi → surrogate → NSGA-II *combination* |
| `Gadhave2020` | MCDM-based PCM selection for domestic water heating (the O1 application) |
| `Sobol1967` / `Owen1998` | the scrambled-Sobol DOE in `g8_s2_doe.py` |

Each entry states what it does **and does not** support — they are method
precedents, not evidence that this project's bounds, DOE size or results are
correct.

---

## O2-13 — Stale path references: 68 -> 0, and the run guide was unusable

`g12_verify_docs` now **passes** (`checked 310 references; 0 missing`, exit 0).
It had never passed before.

The 68 split three ways, and only the third group were real stale paths:

**1. Checker bugs (~25, every one a false positive).** `DATA_REFERENCE.md`
writes template placeholders like `climate_signature_{state}.csv`. The checker
understood brace *alternation* `{a,b}` but not a single-token placeholder, so it
substituted the placeholder's NAME literally and looked for a file called
`climate_signature_state.csv`. Fixed: a brace containing no comma is now a
wildcard, as `<c>` already was. Also fixed — `...` elisions in prose paths; the
project's own folder name used as a prefix (`objective2_design_optimization/…`),
which never matched because every base resolves *inside* the project; sibling
repos under the outer tree (`Github/PCM-Selection-ML-model/pcm_shared_config.py`
is real and was reported missing); and `x.cgns/.msh` prose for "both forms".

**2. Genuine renames (20 replacements).** `g2_richardson_summary.csv` →
`g2_timestep_convergence_*.csv`; `docs/PROGRESS.md` →
`RAJASTHAN_METHOD_PORT_PROGRESS.md`; the O3 handoff doc → `objective3/`; three
numbered docs → their archive paths; `deployable_design_per_regime.csv` →
`data/legacy/phase7_…`; `mcdm_full_scores_by_cluster.csv` →
`mcdm_full_rankings.csv`.

**3. Genuinely gone (16).** Rather than repoint these at something that exists —
which would be a lie — the checker now accepts a path **only if the document
says on that line that it is gone** (`GONE` regex: deleted / removed / retired /
renamed / superseded / no longer produced / not present). So "genuinely missing"
and "deliberately recorded as deleted" stay distinguishable, and a path can only
be excused by a sentence a reader also sees. All 16 annotated accordingly.

### The serious finding underneath: `HOW_TO_RUN.md` was 100 % unusable

Not a path problem. The run guide carried a banner claiming the current pipeline
was `run_rajasthan_pipeline.py --stage all` plus `src.doe.run_sobol_doe`, and the
legacy one `pipeline.py --stage ...`. **Checked 2026-11-09: none of those entry
points exists**, and neither do `src/doe/`, `src/surrogate/` or `src/robustness/`.
Someone following this guide could not have run a single command in it.

Worse, its legacy sections report results that the current run **contradicts**:

| the guide said | current result |
|---|---|
| "radial arrangement won in all 3 regimes" | **staggered** in all three |
| "P(temperature-safe) = 0 %/18 %/0 % — every regime fails the 95 % safety bar" | **9 of 9** designs inside both the 65 °C and 75 °C limits |
| "ExtraTreesRegressor + LinearRegression baseline" | retired; five-family bake-off, `stacked` wins 9/9 |

The banner was replaced with the real pipeline (`scripts/tn_run_all.py`, 31
stages `g2`…`g25`), a task→command table, a map from the old Phase names to the
current stages, and an explicit list of which legacy claims are wrong. Rewriting
the whole guide is still open; the top of it is now correct and the rest is
marked history-only.

---

---

## O2-14 — Dense-grid cross-check extended to all 9 pairs (2026-11-09)

**The gap.** The "the search missed no region of the design space" claim rested
on `g9_s6_grid`, a 720-point full-factorial sweep run at reduced fidelity
(1 weather year) and compared against the NSGA-II/active-learning front. Only
the **rank-1** PCM of each regime had been swept — 3 of 9 (regime, rank) pairs.
Worse, `scripts/g9_assess.py` line 112 globbed `g9_s6_grid_r*_p1.csv`, so even
if the rank-2/3 grids had existed the assessment would have ignored them.

**What was done.** The 6 missing grids were computed at the *same* reduced
fidelity rank 1 used, so all 9 stay comparable, then the glob was widened to
`g9_s6_grid_r*_p*.csv`. The 6 jobs ran concurrently via
`scripts/tn_parallel_backfill.py` (see O2-15).

**Result — all 9 pairs pass.**

| pair | grid feasible | grid front | search front | HV ratio | ε (window / annual / overheat) | within band |
|---|---|---|---|---|---|---|
| `r0_p1` | 603 | 11 | 65 | 1.103 | +0.62 / +0.62 / +1.25 | yes |
| `r0_p2` | 631 | 9 | 52 | 1.107 | -0.67 / -0.26 / +23.65 | yes |
| `r0_p3` | 651 | 10 | 62 | 1.098 | +4.56 / +5.19 / -0.16 | yes |
| `r1_p1` | 603 | 10 | 50 | 1.095 | +3.06 / +3.63 / -3.98 | yes |
| `r1_p2` | 636 | 9 | 50 | 1.107 | -0.66 / +0.30 / +6.81 | yes |
| `r1_p3` | 665 | 13 | 54 | 1.148 | -2.24 / +0.22 / -6.85 | yes |
| `r2_p1` | 608 | 11 | 53 | 1.016 | +11.97 / +13.23 / -3.37 | yes |
| `r2_p2` | 665 | 8 | 65 | 1.086 | +8.37 / +8.31 / -4.93 | yes |
| `r2_p3` | 637 | 10 | 53 | 1.014 | +10.71 / +11.18 / +5.53 | yes |

Two things to read off this table:

* **HV ratio > 1 in all 9** (1.014–1.148). The search front dominates the dense
  grid's front everywhere — the optimiser never did worse than brute force.
* **Every ε value is inside the repeatability band** (27.99 kWh on `g_window`
  and `g_annual`, 107.98 °Ch on `d_overheat`). Several ε values are negative,
  meaning the search front strictly covers the grid front on that objective.
  The largest positive gap, +13.23 kWh (`r2_p1`, `g_annual`), is still under
  half the band.

**Scope, stated plainly.** This shows the search front is at least as good as a
720-point sweep *at reduced fidelity* — it is a search-adequacy check, not a
proof of global optimality. O2-4's `NOT_A_GLOBAL_OPTIMUM` flag stands.

**No design changed.** This stage only scores fronts that already existed; no
selection, no contract field, and no Objective 3 input is touched.

---

## O2-15 — Parallel backfill driver (2026-11-09)

The two outstanding verification backfills were running **sequentially**, which
used 2 of this machine's 12 logical cores: neither `g9_s6_grid` nor `g9_s4_s5`
parallelises internally. `scripts/tn_parallel_backfill.py` was added to drive
all of them through a `ProcessPoolExecutor`.

Three details that make it safe to re-run:

* **BLAS threads are pinned to 1** (`OMP_NUM_THREADS` and the OpenBLAS / MKL /
  NumExpr equivalents). Without this, ten jobs each try to seize every core and
  the machine thrashes instead of computing.
* **Idempotent.** A job whose output file is already complete is skipped, so an
  interrupted run can simply be restarted.
* **No double writers.** A job whose log file has been touched within
  `STALE_S` (150 s) is assumed to be in flight elsewhere, deferred to the end
  and waited for, rather than started a second time on top of its own output.

**Scope guarantee.** Explore years only. Nothing in this driver touches the
held-out years or `held_out_test.lock`.

It delivered the 6 rank-2/3 dense grids of O2-14. The `g18` `novert` / `vert`
re-runs are the remaining jobs.

**Measured throughput, for anyone repeating this.** 12 logical cores returned
only about 4.3 cores of useful work: each `g9_s4_s5` warm run needs roughly 115
CPU-minutes but took 276-333 wall-minutes with ten of them resident. The
Gaussian-process hyperparameter fits are memory-bandwidth bound, so adding
workers past that point lengthens individual jobs without raising throughput.

---

## O2-16 — Document path checking extended to the docs that matter (2026-11-09)

O2-13 took `g12_verify_docs` from 68 missing references to 0. But the stage was
only reading **six** documents, and `OVERVIEW.md` was not one of them — the very
file that `documentation/README.md` now tells readers to open *first*, because
`docs/RESULTS.md` carries its own superseded banner. The primary current
account of Objective 2 was the one top-level document whose paths nothing
verified.

Added to the checked set: `OVERVIEW.md`, `docs/SIMULATOR_AND_CFD.md`,
`docs/REFERENCES.md`. Coverage went from 310 references over 6 documents to
**370 over 8, still 0 missing**.

One genuine provenance defect surfaced by the wider net, in
`docs/REFERENCES.md`: it claimed its citations were *"carried over verbatim
from `vertopal.com_references.txt`"*, a filename that exists nowhere — not in
this tree, not in the sibling `Github/` trees.

My first fix simply marked the file gone. That was wrong, and the project owner
corrected it: the bibliography itself was never lost, only the filename. It is
in the repository as `tamilnadu_pipeline/sources/references.txt`, which is
**byte-identical** to `tamilnadu_pipeline/sources/references.bib` — both are
BibTeX despite the `.txt` extension, which is a format-converter download name
(vertopal.com is a file converter, hence the old filename).

Verified rather than assumed: the BibTeX file holds 33 entries,
`REFERENCES.md` holds 33 citation keys, and **19 are common to both**. The 14
that are not in the BibTeX are exactly the entries added to this document
later — five data-source citations (`rubitherm2024`, `pluss2024`,
`globalsolaratlas2024`, `renewablesninja2024`, `isrosolarcalc2024`), the six
optimisation-method citations added under O2-12 (`deb2002`, `sobol1967`,
`bhattacharjee2016`, `bradford2018`, `kumar2024`, `gadhave2020`), and
`barghijahromi2026`, `nemes2025`, `iced2026`.

So the document now points at a file a reader can actually open and check
every verbatim entry against, and states which 19 of its 33 keys that covers
— a stronger claim than the original vague one, and far better than the
"it is gone" note I first wrote.

A second, smaller fix in the checker itself: a backticked token that is *only*
an extension (`` `.txt` ``, `` `.csv` ``) is prose about a file format, not a
path. `SKIP` had one hardcoded entry for `.csv`; it is now a pattern.

`docs/CORRECTIONS.md` is deliberately **excluded** from the checked set. Its
job is to name files that were deleted, renamed or never written, and most of
its remaining path-like tokens are prose rather than references — `g9_s4/s5`,
`x.cgns/.msh`, the elided `..._rajasthan_v2.json`, and
`climate_signature_state.csv`, which appears only because O2-10 quotes the
placeholder bug verbatim. Forcing those to resolve would mean rewriting true
sentences to satisfy a checker.

---

## O2-17 — The doc check passed locally but would fail on a clone (2026-11-10)

`scripts/g12_verify_docs.py` resolves path references against the **working
tree**, not against the git index. Nothing had ever compared the two. When
measured, **79 of its 373 references resolved only inside `archive/`** — a
directory `.gitignore` excluded wholesale. So O2-13's "0 missing" was true on
the author's machine and would have been "79 missing" for anyone who cloned
the repository. A green check that is green only locally is worse than a red
one, because nobody looks again.

**Fix.** The 79 point at retired *documents and scripts*, not at the heavy
data, and those two things differ in size by a factor of 600: archive's text
content is 157 files totalling **1.2 MB**, while its bulk is **713 MB** (a
223 MB OpenFOAM `run.log`, 185 MB of CSVs, 117 MB of interactive HTML, 85 MB
of JSON, the 63/81 MB Objective-1 aggregates). The rule was narrowed to ship
the text and keep out the data:

```gitignore
archive/**            # not archive/ -- git does not descend into an excluded
!archive/**/          # DIRECTORY, so the negations below would never be read
!archive/**/*.md
!archive/**/*.py
...
archive/**/*.log      # except the logs: bulk, and regenerable
```

That subtlety is the whole fix: `archive/` and `archive/**` behave identically
until you try to negate something underneath them.

**Result: 79 unresolvable on a clone → 23**, for +1.2 MB.

**The 23 that remain are correct to omit**, and `docs/DATA_REFERENCE.md` now
carries a "What is deliberately NOT in a git clone" section naming each
category: the two large Objective-1 aggregates (63 MB and 81 MB, regenerable
by re-running Objective 1), the 2.9 GB of raw ERA5/POWER downloads, archive's
data artefacts, and the two **sibling git repositories** `Github/Objective---2/`
and `Github/PCM-Selection-ML-model/`, which are referenced as external
provenance and must not be nested inside this repository.

One consequence is worth stating because it is easy to miss:
`data/objective1/manifest.json` records a SHA-256 for every frozen
Objective-1 file, and two of those files are not in a clone — so 30 of the 32
hashes are checkable there, not all 32.

**Scope.** This changed only `.gitignore` and documentation. No result, no
design, no contract field.

---

## O2-18 — The box-vertex diagnostic, completed (2026-11-10)

Closes the last compute item. All 18 `g9_s4_s5` warm re-runs finished
(0 failures, 658 min wall for the whole 24-job backfill), so
`g18_issue1_with_without.csv` now holds **27 rows** — 9 pairs x 3 states —
instead of the 9 `base` rows it had before.

### The finding

| state | what it is | points | best HV in |
|---|---|---|---|
| `base` | the original 5 active-learning rounds | 251 | **no pair** |
| `novert` | base + 3 more rounds, no vertex step | 281 | 3 pairs |
| `vert` | base + the 24 box corners + 3 more rounds | 297 | 6 pairs |

**The step makes no difference the acceptance criterion can see.** All 27 rows
are inside the repeatability band on every objective. Hypervolume spans
0.983 to 1.000 of each pair's best — a total spread of **1.7 %**.

Two conclusions, one of them uncomfortable:

* The extra rounds are worth running: `base` is best in no pair.
* **The step is not what fixed regime 0 PCM 1.** That pair was the whole
  reason the step was invented, after it failed the dense-grid check twice. It
  now passes in **all three** states — worst epsilon 0.6 against a 28.0 band —
  including `base`, the state that originally failed. The failure does not
  reproduce once the pair is checked against the full nine-pair dense grid of
  O2-14. An unplanned, reactively-added step turns out to be harmless but not
  load-bearing, and that is now what the documents say.

### Three defects found while completing it

**1. One pair was silently reported with 2 states instead of 3.**
`scripts/g18_issue1_compare.py` special-cased `r0_p1` to read its `novert`
state from `results/g9_points_r0_p1_ext.csv`, a historical no-vertex run. That
file does not exist any more, so the lookup failed `main()`'s `.exists()`
guard and the row was dropped — no warning, just 26 rows where 27 were
expected. The backfill produced a standard `novert` run for `r0_p1` at the
standard path with 281 points, identical to the other eight pairs, so the
special case was removed and all nine pairs are now built the same way. The
docstring claim that `r0_p1` had "11 rounds in total, unlike the other pairs"
was also false once that run existed, and is corrected.

**2. The results-document reading had never executed.** `g12_results_doc.py`'s
`else` branch — the one that prints the full reading when all three states are
present — could not run while the CSV held only `base`. It therefore still
carried the narrative written for an earlier partial run, and **every figure in
it contradicted the completed data**: it stated that without the step regime 0
PCM 1 *"still fails the grid check (23.5 kWh against 13.8)"*, where the
measured value is 0.6 against a band of 28.0, and described an 8-vs-11-round
asymmetry that no longer exists. The reading is now computed from the
dataframe; nothing in section 5f is typed by hand.

This is the same class of bug as O2-10 and worth naming: a branch guarded by a
condition that has never been true is not tested code, and a hardcoded
narrative inside one will state yesterday's result with today's authority.

**3. The epsilon column header hardcoded the wrong band.** It read
`eps g_window (band 13.8)` while the repeatability band is **28.0** — so a
reader checking those epsilon values against the stated threshold would have
used a figure wrong by a factor of two, and could have judged a passing run as
borderline. Now read from `g9_grid_check.csv`.

### Scope

No design, no selection, no contract field changed. `g18` is a diagnostic: it
scores fronts that already existed and feeds nothing downstream. Objective 3's
inputs are untouched.

---

## O2-19 — The frozen config moved, and the contract's provenance went stale with it (2026-11-10)

Re-running `src/handoff/build_obj3_contract_tamilnadu.py` as a reproducibility
check produced a contract whose hash differed from the committed one. Two
fields, and only two:

| field | committed | regenerated |
|---|---|---|
| `generated_utc` | 2026-11-09T09:54:13Z | 2026-11-09T21:49:03Z |
| `provenance.configs/system_config_shared.yaml` | `cb2901f9...` | `a787796f...` |

**Every design value, selection, bound, scenario and acceptance field was
byte-identical.** Only the recorded hash of a config file had moved.

`configs/system_config_shared.yaml` declares itself FROZEN and warns that
"changing this file after Phase 4 verification means every state must re-run
from DOE onward". So the change had to be identified, not assumed benign. No
git history exists yet, but the pre-change copy survives in the sibling
Rajasthan-era tree, and the diff is one line — **inside a comment**:

```diff
-  # results/g2_richardson_summary.csv) shows the PCM cases converge at observed
+  # results/g2_timestep_convergence_{300_150_75,150_75_37p5}.csv) shows the PCM
```

That is one of O2-13's stale-path corrections: the comment named a results file
that does not exist. **No value the solver reads changed**, so the re-run-from-
DOE clause does not apply and no result is invalidated.

**But the contract's provenance block was now wrong**, which matters more than
it looks: the whole point of recording SHA-256 for every input is that a reader
can verify it, and a provenance hash that does not match the file on disk is
worse than no hash — it reads as tampering. The contract was regenerated and
the canonical copy at `objective3/contracts/` refreshed.

**Verified after the refresh:** all 6 file-backed provenance entries now match
the bytes on disk — `g10_heldout_results.csv`, `held_out_test.lock`,
`wp6_band.csv`, `configs/system_config_shared.yaml`,
`configs/states/tamilnadu.yaml`, `configs/design_space.yaml`. The two
non-file keys (`selection`, `generic_blocks_reused_from`) and the derived
`generic_blocks_reused_sha256` are descriptive, not paths.

**The general lesson**, worth keeping: a provenance block is only as good as
the habit of regenerating it. A comment-only edit to a frozen config is exactly
the change most likely to be made without thinking about downstream hashes, and
exactly the one that makes a verification block silently false.

### Also noted, not changed

`objective2_design_optimization/objective3/` exists — a three-file directory
holding a contract copy and two handoff documents. It is **not** a clean
duplicate of the real `objective3/`: both documents differ from their
counterparts there, and `objective3/docs/README_DOCS.md` and
`objective3/docs/from_before/OBJECTIVES_AND_ALGORITHMS.md` both reference it by
that nested path (under the pre-v3 filename, which is not what the directory
actually contains). It is 45 KB and harmless, but it is a second place where
Objective 3's handoff lives. Left in place deliberately: Objective 3 is being
built in parallel and this is its author's territory, not something to tidy
unilaterally mid-flight.

## Still open in Objective 2 (not fixed here)

Renumbered 2026-11-10: the list previously ran 1, 2, 4, 5, 6, 7 with no item 3
after an earlier deletion.

### Genuinely open

1. **The 40 % PCM-fraction run** that `g17` indicates would do better (O2-4).
   Deferred by an explicit decision, not an oversight: it changes designs and
   would invalidate the Objective 3 contract, which is frozen while Objective 3
   is being built in parallel. `g17` puts the gain at +76.7 / +64.6 / +66.0 kWh
   against bands of 28.4 / 26.0 / 29.5, i.e. 2.2-2.7x the noise floor and all
   thermally feasible — so it is a real opportunity, quantified and recorded
   rather than taken.
2. **The Objective 1 re-size at 45 °C.** Objective 1 sized latent heat for a
   60 °C delivery service; Objective 2 scores delivered energy at 45 °C. The
   paired comparison in Objective 2 is unaffected, but whether Objective 1
   would have shortlisted *different* PCMs at 45 °C is unquantified. Also
   design-changing, also deferred for the same reason.
3. **Physics limits, unchanged and disclosed** — flow-independent collector
   F_R, symmetry-slice CFD mesh, wind and humidity reaching no equation,
   plane-of-array irradiance with no tilt model. Listed under `OVERVIEW.md`
   → "Honest limits".
4. **No experimental validation of any kind** (O2-8). Objective 4 scope.
5. **`docs/HOW_TO_RUN.md`'s body** is still a history document. Its top is
   correct and its stale claims are flagged, but the full rewrite is unfinished
   (O2-13).

### Closed since this file was written

| item | closed | entry |
|---|---|---|
| `g18` `novert`/`vert` runs | 2026-11-10 | O2-18 |
| Dense-grid cross-check for rank-2/3 pairs | 2026-11-09 | O2-14 |
| 68 stale path references | 2026-11-09 | O2-13 |
| Doc check passing only on the author's machine | 2026-11-10 | O2-17 |

`g12_verify_docs` now reports **391 references over 8 documents, 0 missing**,
exit 0 — and 23 rather than 79 of those references are unresolvable on a fresh
clone, the remainder being material deliberately excluded (O2-17).
