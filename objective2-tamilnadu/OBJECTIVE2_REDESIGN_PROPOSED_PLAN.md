# Objective 2 Redesign — Proposed Plan (planning only, nothing implemented)

**Status:** PROPOSED — for the project guide's review. No source code, configuration, dataset, result, paper or other document was modified to produce this plan. The only file created in the project is this one.
**Prepared:** 2026-10-26. **Scope of evidence:** repository files as they exist on disk on that date; papers as listed in §2.
**Revision 2026-10-26 (second pass):** WP5 now specifies Option B — a neural-network-ensemble surrogate + NSGA-II with active learning — and a new sub-package WP2-C defines how **OpenFOAM and ANSYS Fluent** are used for calibration and checking only. Decisions already taken by the user are in §6 and §6A. New reading is listed in §2.5.

**Evidence labels used throughout**

| Label | Meaning |
|---|---|
| **[V]** Verified | I read the file/line or reproduced the number by running the existing code *read-only* (no repo file written). |
| **[L]** Literature | Stated by a paper I actually read (pages/tables given). |
| **[P]** Proposed | My engineering proposal. Not established by the project or literature. |
| **[O]** Open | Unresolved; needs an experiment or the guide's decision. |
| **[A]** Assumption | Needs confirmation by the guide / student. |

> **Read this first — three findings that change the plan's starting point**
>
> 1. **[V] Probable demand-timing bug (highest priority).** The demand profile is defined in local clock hours (07:00 / 19:00 peaks — `build_demand_profile.py` docstring), but `src/simulation/tank_model.py:202` indexes it with the **UTC** hour of the weather timestamp. Rajasthan is UTC+5:30, so the "evening" 46 L draw is applied at ~00:30 local, when the tank is coldest (mean 27.9 °C at UTC 19), and the "morning" draw at ~12:30 local. Re-running the existing code with the demand shifted to local time (using the code's own `timing_shift_hours`) changes annual useful energy by about **−31 %**, solar fraction from 0.55–0.62 to **0.34–0.40**, and PCM-vs-plain-tank gain from 0.12–0.20 % to **0.33–0.81 %** (table in §3.3). Every Rajasthan result — and, by identical code, every other state's — is conditional on this. It must be confirmed by the student/guide before anything else is rerun. The same line exists in all four state folders.
> 2. **[V] PCM benefit is small mostly because of scale and model structure, not only because of the metric.** At the selected designs the PCM can store 0.9–2.0 % of annual useful energy even if it completed one full melt/freeze cycle every day (arithmetic in §3.4); the simulator realises ~10–13 % of that. A 50 L tank with 300 L/day demand (6 turnovers/day) leaves almost no room for latent storage to matter. A new metric alone will not fix this.
> 3. **[V] Objective 2 is not currently working on Objective 1's PCM shortlist.** `retarget_tm.py` replaced O1's MCDM top-3 with a different top-3 chosen by proximity to a Tm derived from O2's own plain-tank simulation (`results/tm_retargeting_report.csv`); the "O1 rank-1" used in O2's divergence check is the first entry of that *retargeted* list (`select_deployable.py:213`). The brief says the O1 shortlist stays fixed, so this needs a guide decision (§5, WP3 and WP6).
>
> Also: the pasted brief ended mid-sentence inside Work Package 8, and **Work Package 9 was not in the text I received**. I have proposed a WP9 (reporting/reproducibility/O3 hand-off) and marked it **[A]**; please send the original WP9 text if it differs.

---

## 1. Authoritative Objective 2 (verbatim, unchanged)

> **Objective 2 (O2):** Develop an AI-driven design optimization model to determine the optimal PCM thickness, capsule arrangement, number of PCM capsules, and flow rate for maximizing thermal energy storage under location-specific climatic conditions, using the research directions represented by Chen2025TaguchiGRAPCM, Barqawi2025MLPCMSWH, and Kou2025BIHPPCM.

**Fixed (never optimised):** tank volume; solar collector area; hot-water demand profile; PCM shortlist selected by Objective 1.
**Design variables (exactly four):** (1) PCM thickness, (2) capsule arrangement, (3) number of PCM capsules, (4) flow rate.

Current fixed values **[V]** (`configs/system_config_shared.yaml`): collector 1.5 m² (line 24), tank 50 L (line 30), demand 300 L/day (`configs/states/rajasthan.yaml:38`), delivery target 45 °C (line 76).

**Verified identity of the three cited references** (details in §2): `Chen2025TaguchiGRAPCM` = Chen et al., *Energy Conversion and Management: X* 26 (2025) 100910 — Taguchi + GRA on a TRNSYS model; `Barqawi2025MLPCMSWH` = Barqawi, *Muthanna J. Eng. Technol.* 13(3) (2025) 1–14, DOI 10.52113/3/eng/mjet/2025-13-03/-1-14 — **a neural-network pump-flow *controller*, not a design optimiser**; `Kou2025BIHPPCM` = Kou et al., *Building and Environment* 285 (2025) 113674 — PSO over PCM *material properties* for a heat-pipe-coupled building wall, **not a water-heater or capsule-geometry study**. So the three papers support the *method families* (designed experiments + multi-objective ranking; learning-based control of flow; metaheuristic optimisation of PCM parameters) but none optimises capsule thickness/arrangement/count in a solar-water-heater tank. This should be said plainly in the paper.

---

## 2. Phase 0 — Source inventory and reading status

### 2.1 What `Sources.zip` is **[V]**

- `D:\Final Year Project\Sources.zip`, 263 MB, 97 entries (93 files + directories), CRC test passed.
- Extracted into an empty scratch directory (not into the repo); no script/macro from the archive was executed; PDFs were only opened as data.
- **SHA-256 comparison: all 93 files in the zip are byte-identical to the 93 files in `.claude/Sources/`.** `PCM-Selection-ML-model/Sources/` holds 83 of the same files (it lacks: `Fetsov2023_OpenFOAM_GranularPCM_summary.md`, the Fetsov PDF, and 8 `_extra_text/` items). Nothing in the zip is new, different, missing or duplicated-with-different-content.
- **Consequence:** no new `_summary.md` files were needed, and nothing was written into the repo (which also respects the "only create this document" rule). If the guide adds *new* papers, they should be extracted once to `.claude/Sources/<Name>_summary.md` per `CLAUDE.md` §5.

### 2.2 Extraction failures / limitations **[V]**

| Item | Problem | What I did |
|---|---|---|
| `A review of artificial intelligence to thermal energy storage.pdf` (Nems) | pdf parser error ("Invalid object in /Pages"); `_extracted_nems_ai_tes.txt` is 0 bytes | Left **unread**; not citable as evidence. |
| `Muthanna energy pcm conversion.pdf` (= Barqawi 2025) | Image-only "Print to PDF" (0 text chars); project OCR failed (`tesseract` not installed → `_extracted_barqawi_ocr.txt` is 14 error lines) | Rendered pages 1, 6, 9 to images and read them directly (§2.3). |
| `IS12976_2023.pdf` | Text layer present but with font warnings; no project extract existed | Extracted with `pdftotext`; read scope, §4.2, §7.1, §8.2. |
| Legacy "Barqawi 2025 — …", "Chen et al. 2025 — …", "Kou(2025)…" `.md` files | Stubs pointing to the `_summary.md` files | Ignored. |

### 2.3 Reading status of the key papers **[V]**

| Paper | Status | Examined | Identity check |
|---|---|---|---|
| **Chen 2025** (PDF → project text extract) | **Read (selectively, ~85 %)** | Abstract; §1 end; §2 (system, Table 1); §3.1–3.4 (Taguchi, S/N, ANOVA, GRA, Eqs. 1–17); §3.5 collector model (skimmed); §4 opening (metric definitions Eqs. 53–56, heat-retention definition), factor/level Table 7, §4.1 validation (Table 10), Tables 11–13, 16–17 (ANOVA), 21–25 (GRA, confirmation), Conclusions. Pages 18–19 and the comparison Table 26 only skimmed. | Matches the cited key. 36-run L36 Taguchi on a TRNSYS model; 9 factors. |
| **Barqawi 2025** (image-only PDF) | **Partly read** | Pages 1 (abstract/intro), 6 (NN architecture, Eqs. 17–19), 9 (results §4.1–4.2, Fig. 7) viewed as images. Pages 2–5, 7–8, 10–14 **not viewed by me**; for those I only have the project's `_summary.md`, which agrees with every number I could check on pp. 1/6/9. | Matches DOI/authors/journal. Paper = flow-multiplier NN controller, simulation only, trained on **synthetic rule-based labels**. |
| **Kou 2025** (PDF → project text extract) | **Partly read (~45 %)** | Abstract; §1.2 (PCM optimisation background), §1.4 (aim), §2.2.1 (indices, Eqs. 12–18), §2.2.2 (PSO method), Conclusions + Table 3. Model description and validation (§2.1), results (§3) **not read by me**. | Matches. Building wall + heat pipes; variables are ρH, Tm, λ; **thickness and transition range held fixed**. |
| **Avargani 2021** (`_extra_text`) | Partly read | Abstract, Table-2 parameter excerpt, Conclusions. | Packed-bed PCM in a solar-water-heater tank (CFD, COMSOL). |
| **Li 2020** (`_extra_text`) | Partly read | Abstract + notation/method excerpts. | RSM + NSGA-II + LINMAP/TOPSIS for PCM tank design (swimming-pool heating). |
| **IS 12976:2023** | Partly read | Scope/foreword; §4.2; §7.1; §8.2. | BIS, First Revision, Nov 2023. |
| **Eldokaishi 2022** | **Summary only** (project `_summary.md`; not re-read) | — | — |

### 2.4 All other papers **[V for status]**

I did **not** read these; each has a project-written `_summary.md` (and usually a text extract). They are listed so no one mistakes them for read-and-verified: Abdellatif 2025; Al-Mamun 2023; Assareh 2023; Barghi 2026; Chopra 2023; Duraivel 2025; Emami 2026; Fetsov 2023; Ghodusinejad 2026; Hamzat 2025; Liu 2025; Mansouri 2025; Martinez 2025; Mohammed 2025; Odoi-Yorke 2025; Singh 2025; Terfai 2025; Yan 2025. Unread and not relevant to O2: Magnus saturation-vapour-pressure note; solar position algorithm; occupant-behaviour paper; MCDA domestic-PCM selection (`mcda_pcm_domestic.txt`, relevant to O1 not O2). **Nems 2025: unread (extraction failed).**
**Rule for this plan:** a claim attributed to an "other paper" below is marked *(summary-only)* and must be re-verified against the PDF before it appears in the manuscript (per `CLAUDE.md` §0, item 4).

---

### 2.5 Additional reading for the algorithm-B / CFD update (2026-10-26) **[V]**

| Paper | Status | Examined |
|---|---|---|
| Yan et al. 2025, Applied Energy 390:125863 (extract: `_extracted_yan_ml.txt`) | **Partly read** | Abstract/highlights; §2.2 simulation method (ANSYS Fluent, enthalpy-porosity, mushy-zone constant, grid/time-step independence); §3 ML section skimmed. Results tables not read. |
| Liu et al. 2025, Renewable Energy 238:121973 (extract: `_extracted_liu_ai_pcm.txt`) | **Partly read** | Abstract; passage on NSGA-II/MOPSO/DDQN (pp. 12–14, Figs. 12–13). Rest unread. |
| Li et al. 2020 | **Partly read (more)** | Abstract; §2.3 NSGA-II; §2.4 decision methods; RSM R² passage; nomenclature. |
| Abdellatif et al. 2025 | **Snippet only** | Passages mentioning ANSYS Fluent (found by keyword search); not read in full. Do not cite beyond "Fluent is widely used for enthalpy-method PCM simulation". |

## 3. Phase 1 — Verification of the existing audit against the repository

All paths below are relative to `OBJECTIVE2/Objective---2/` (abbreviated `RJ/` = `objective2-rajasthan/`).

### 3.1 The twelve claims

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| 1 | Rajasthan is the only state with the complete four-variable pipeline; TN/Assam/UK retain older design spaces | **Partly confirmed** | Bounds files: Rajasthan `configs/design_bounds_shared.yaml` v1.2 (d 0.04–0.08, count 8–37, **three** arrangements, fraction floor 0.003, shield on). **Tamil Nadu** v2.0 also lists three arrangements (`allowed: [single-layer, staggered, radial]`, line 51–53) and has `pack_radial` (`geometry.py:146`) and 600 candidates, **but** still d 0.02–0.08 and fraction floor 0.10 (the dead zone Rajasthan removed). **Assam** v1.0: count 8–24, d 0.02–0.08, `[staggered]` only, 400 candidates, no `pack_radial`. **Uttarakhand** v1.1: count 8–37, `[staggered]` only, 400 candidates, no `pack_radial`. So "older design spaces" is true for Assam/UK; TN is intermediate. |
| 2 | PCM thickness is derived from diameter, not optimised | **Confirmed** | `RJ/src/design/geometry.py:260` `thickness_m = d / 2.0`; `constraints.py:47–49` re-derives and bound-checks it; `schema.py:12–13` states it is "DERIVED, not independently sampled"; `design_bounds_shared.yaml:19–26`. The thickness bound `{0.02, 0.10}` can never bind above 0.04 m given d ≤ 0.08 (derived thickness ∈ [0.02, 0.04]). |
| 3 | 600 random candidates/PCM; Extra Trees on 219 cases; only 126 valid | **Partly confirmed; the 219/126 numbers are stale** | 600 ✔ (`src/optimize/search.py:41`; drawn *before* the geometry gate, surviving count not logged). Extra Trees ✔ (`src/surrogate/train.py:87`, 300 trees). **But the saved DOE is 327 cases, all valid** (216 LHS + 108 boundary + 3 baseline; 273 train / 54 holdout; `results/phase5_design_cases.csv` and its manifest: `n_lhs_per_pair 24, n_boundary_per_pair 12, n_total_cases 327`). "219 cases, 126 valid, 93 rejected" appears in `docs/05_PHASE5_DOE.md:31,55` and the `generate_cases.py:141` docstring, i.e. the pre-diameter-floor DOE. (The number 126 also coincides with the 126-row loading sweep.) |
| 4 | Selected designs sit near d = 0.04 m and/or count = 37 | **Partly confirmed** | `results/phase7_deployable_design_per_regime.csv`: d = 0.0429 / 0.0410 / 0.0403 m (all within 0.003 m = 7.3 % of the 0.04 floor); count = 37 / 25 / 37 (two of three at the ceiling). Regime 1's count (25) is interior. Note the 0.04 floor itself is an artefact of the derived-thickness bound (§3.2 item 2). |
| 5 | PCM adds only ≈0.12–0.20 % annual useful energy vs plain tank | **Confirmed** | Same CSV, `pcm_vs_plain_tank_pct` = 0.204 / 0.121 / 0.128 %. In kWh: 1588.06 vs 1584.82 (+3.24), 1845.62 vs 1843.39 (+2.23), 1791.20 vs 1788.92 (+2.29). I re-ran those designs: plain 1584.8, PCM 1588.1 (regime 0) — reproduced exactly. |
| 6 | Arrangement and flow have negligible effect; arrangement mostly changes pump power | **Confirmed for arrangement; flow only partly** | `arrangement_rationale` column: tied "within noise band = 0.04 %". DOE (324 PCM cases) mean gain by arrangement: radial 0.0463 %, single-layer 0.0473 %, staggered 0.0485 % (σ ≈ 0.12 %). Pump energy is ~1e-7 kWh/year (DOE max 2.5e-6): Ergun ΔP is 1.5e-5–8e-3 Pa, pump power 3e-10–7e-7 W — *physically meaningless*, so "arrangement changes pump power" is true but irrelevant. Flow: collector output is independent of flow (`collector_model.py:37–60`); flow enters only via packed-bed h_w and pump power. No flow-ablation exists; the DOE correlation (0.18) is confounded. |
| 7 | Bounds / fraction limits were changed in response to results | **Confirmed (with nuance)** | `git log` on `design_bounds_shared.yaml`: initial 2026-09-06 (d 0.02–0.08, count 8–24, fraction ≥0.10); count 24→37 on 2026-09-17 (commit 0f05aed); **d_min 0.02→0.04 and fraction floor 0.10→0.003 on 2026-09-23 (commit 505c715)**. File comments (lines 29–68) state the 0.003 floor was set *because* `scripts/sweep_pcm_loading.py` showed gain turns negative above ≈2.5–3 % loading. I re-binned `results/phase3_5_pcm_loading_sweep.csv`: mean gain +0.069 % (<1 % loading), +0.029 % (1–2.5 %), −0.065 % (2.5–5 %), −0.209 % (5–10 %), −0.430 % (10–15 %), −0.702 % (15–20 %). So bounds followed results. Nuance: the sweep itself comes from the simulator whose limits §3.3 describes, so it shows the *simulator* penalises loading, not that real PCM does. |
| 8 | O2's selected PCM sometimes differs from O1's top-ranked | **Confirmed — and stronger: 3 of 3 regimes differ** | Winners RT44HC / savE® OM49 / Lauric acid vs "rank-1" OM42 / n-Tricosane / RT45HC. **But** `select_deployable.py:213` sets `o1_rank1_pcm = o1_shortlist[0]` where the list is O2's *retargeted* `pcm_shortlist`. O1's own rank-1 (in `rajasthan.yaml` `pcm_shortlist_detail`) is Palmitic-stearic acid/EG & savE® OM55 (regime 0), PureTemp 60 (regime 1), …, none of which are in O2's list. The true divergence from O1 is therefore larger than reported. |
| 9 | Single 8760-h medoid year despite a ten-year record | **Confirmed, with corrections** | Each regime uses one calendar year at one point (`data/weather/*_hourly.csv`): cluster 0 = 2025 (8760 h), clusters 1 & 2 = **2016 (8784 h, leap year)**. `build_regime_weather.py:74` picks the year `max(frames, key=len)`, i.e. *the year with the most hours*, which is a leap year; this is not a climatological choice. In Objective 1's `historical_annual_ensemble_rajasthan.csv`, 2016 is the **sunniest** year in all three clusters (GHI scale 1.041/1.042/1.044), 2025 is third-lowest (0.966/0.970/0.970): regime comparisons are confounded with year differences of ~8 %. The ten-year record exists: daily aggregates for all 320 points; NASA POWER JSON for 320 points × 2016–2025 (3,200 files in `PCM-Selection-ML-model/era5-rajasthan/data/raw/nasapower`; hourly resolution to be re-verified in WP4). `monte_carlo.py`/`weather_ensemble.py` reuse annual scale factors from the 10 years but keep one year's hourly shape. |
| 10 | No explicit heat-retention time / night-hold scenario | **Confirmed** | `grep -ri "retention\|overnight\|night\|standby" RJ/src` → no matches. `delivery_temp_hours` (`run_case.py:109`) counts hours with bulk tank ≥45 °C; it is `NaN` in all DOE rows (`record_hourly=False`) and present only for the 3 deployable confirmation runs. It is not a retention time. |
| 11 | Docs and results disagree on winning PCMs, shortlists, results | **Confirmed** | At least four mutually inconsistent descriptions: (a) `rajasthan.yaml` `pcm_shortlist_detail` (O1: Palmitic-stearic/EG, savE® OM55, Myristic/NBR…) vs `pcm_shortlist` (O2-retargeted: OM42, RT44HC, RT47 …); (b) `results/phase4_simulator_verification_report.txt` verifies Palmitic-stearic/PureTemp 60/n-Heptacosane — i.e. the **pre-retarget** shortlist — so Phase 4 was not rerun on the PCMs Phases 5–7 use; (c) `docs/05_PHASE5_DOE.md` (219 cases); (d) Assam `README.md` says Phase 8 "NOT RUN" while `results/phase8_*` and `obj3_environment_contract_assam.json` exist. |
| 12 | The comprehensive audit report describes results/settings that differ from the current implementation | **Confirmed** | `O2_O3_COMPREHENSIVE_AUDIT_REPORT.md`: 165 cases, 138/27 split, 54 infeasible, 400 candidates/pair, PCMs RT35…OM42, "plain tank wins all 3 regimes, 0/45 PCM pass T_PCM ≤ 65 °C", R² = 0.9998, rated "9.2/10". Current: 327 cases, 273/54, 600 candidates, safety shield on, PCM +0.12–0.20 %. It also cites "Consensus" database papers I did not read. Do not cite it as evidence. |

### 3.2 Additional discrepancies found (not in the brief's list) **[V]**

1. **Demand timing — see headline #1.** `tank_model.py:202` (`hour_of_day = int(row["timestamp_utc"].hour)`); weather rows are true UTC (e.g. `2025-01-01 02:00 UTC, GHI 61.8` = 07:30 IST) and carry a separate `local_hour` column that the simulator never reads.
2. **0.04 m diameter floor and 0.003 fraction floor are artefacts of redundant bounds** (`design_bounds_shared.yaml:29–68`): the thickness bound (min 0.02) forces d ≥ 0.04.
3. **PCM mass uses the *outer* sphere volume.** `geometry.py:258` `v_capsule = sphere_volume_m3(d)`; `tank_model.py:158` `m_pcm = N · V_capsule · ρ`. The 0.8 mm aluminium wall (`system_config_shared.yaml:41`) is ignored in volume and thermal mass, overstating PCM mass by ≈(1 − ((d−1.6 mm)/d)³) = 11.5 % at d = 40 mm, 5.9 % at 80 mm (my arithmetic).
4. **Delivery target is inconsistent across objectives.** O1 anchors on 60 °C delivery (`CLAUDE.md` §3.2: `T_DELIVERY_C = 60`, Tm_target = 67 °C); O2 uses 45 °C (`system_config_shared.yaml:76`). O2's retargeting then moves Tm_target to 43.5/47.9/45.7 °C.
5. **The "Tm target retarget" is real but circular.** I independently reproduced the reported values by running the plain reference tank (d 0.05, N 16, 0.030 kg/s): median tank temperature during collector-charging hours = **43.45 / 47.89 / 45.69 °C** → 43.5 / 47.9 / 45.7 (`retarget_tm.py:67–71, 101–104`). The source is the simulator's own median charging-hour water temperature, which itself depends on the fixed sizing and on the demand-timing issue in item 1. It is not a delivery-temperature argument: with Tm ≤ 45 °C, a PCM cannot hold water *above* 45 °C while discharging.
6. **"Frozen shared config" is not identical across states.** Rajasthan `system_config_shared.yaml` is v1.1 (safety shield on, lines 70–73); Tamil Nadu, Assam, Uttarakhand are v1.0 with no shield (diff confirmed). Results across states are therefore not comparable as they stand.
7. **Weather years differ by state/regime:** Rajasthan 2025/2016/2016; Tamil Nadu all 2016; Uttarakhand all 2016 (5 regimes, not 3); Assam all 2025. `objective2-assam/data/weather/` also contains stray copies of Rajasthan weather files (cluster 1/2 with the *old* medoid IDs RJP_0202/RJP_0055).
8. **Stale Objective-1 artefacts inside the O2 repo.** `data/objective1/medoid_points_rajasthan.csv` still lists medoids RJP_0132/0202/0055 and sizes 114/103/103, while the live assignments and `rajasthan.yaml` use RJP_0132/0192/0083 and 109/83/128. The cached 10-year JSON in `RJ/data/objective1/raw_weather/` is only for the old medoids. (`docs/01_PHASE1…` acknowledges this at lines ~24 and 136–139.)
9. **Metric mismatch inside the optimiser.** `search.py:109` ranks by predicted `useful_energy_kWh`, which is `E_load` = ∫ ṁ·cp·max(T_w − T_mains, 0) (`tank_model.py:292`, `run_case.py:115`): *any* heat above mains counts, including water drawn at 60–72 °C that would be mixed down in a real system, and including water below the 45 °C target. This metric rewards overheating. The solar-fraction metric (`run_case.py:104–107`) is better aligned (unmet energy is measured against 45 °C).
10. **Surrogate R² is inflated by between-regime variance.** Hold-out R² ≈ 0.99999 for useful energy (`phase6_surrogate_metrics.csv`), but within a regime all 109 cases span only ~5 kWh (σ ≈ 1.7–2.3 kWh), RMSE = 0.37 kWh, max error 1.70 kWh — the same order as the 2.2–3.2 kWh PCM gain being optimised. Good R² here says the surrogate recovers regime offsets, not that it ranks designs.
11. **`useful_energy` vs year length.** `run_case.py:103` sums demand over `len(weather)` hours, so regimes using a 8784-h year draw ~0.27 % more water than 8760-h years.

### 3.3 Why does adding PCM barely help? — causal analysis

Each row separates what I *demonstrated* from what remains a hypothesis. "Demonstrated" = read in code and/or reproduced by running the repo's own functions without modifying them.

| Candidate cause | Category | Status | Evidence / reasoning |
|---|---|---|---|
| **Energy-capacity ceiling vs demand** | System sizing | **Demonstrated (arithmetic)** | Demand 300 L/day through a 50 L tank = 6.0 turnovers/day; the largest hourly draw is 46.3 L (≈93 % of the tank volume) (`data/demand/demand_profile_rajasthan.csv`, hour 19). Selected PCM masses are 1.2/0.74/1.2 kg. Latent ceiling per day = m·L: regime 0: 1.224 kg × 250 kJ/kg = 306 kJ = 0.085 kWh/day → 31 kWh/yr = **1.96 %** of 1585 kWh; regime 1: 0.738 kg × 224 = 165 kJ → 16.7 kWh/yr = **0.91 %** of 1843; regime 2: 1.217 kg × 184 = 224 kJ → 22.7 kWh/yr = **1.27 %** of 1789. Realised gains (3.24/2.23/2.29 kWh) are **10.4 / 13.3 / 10.1 %** of that ceiling. Even at the 20 % loading cap (10 L, 8 kg, 250 kJ/kg, one cycle/day) the ceiling is ~203 kWh/yr = 12.8 % *before* subtracting displaced-water sensible capacity. *(Assumes one complete melt-freeze cycle per day; PCM properties from `data/objective1/pcm_database_rajasthan.csv`.)* |
| **Water displacement penalises loading** | System sizing / fairness | **Demonstrated** | `tank_model.py:161` `m_w = (V_tank − V_pcm)·ρ`. Gain falls monotonically with loading (§3.1 claim 7), DOE correlation of gain with fraction = −0.74. The comparison is *fair in accounting* (baseline has full water mass; PCM tank loses water volume, as it physically would) but it means high loading is penalised by construction in a well-mixed tank. |
| **Hot tank, PCM mostly liquid** | Operating conditions | **Demonstrated** | Plain tank reaches 68.6/72.3/71.9 °C (`phase4` report and DOE baselines); simulated mean melt fraction of the chosen designs is 0.33–0.39, and PCM temperature at maximum is 62.08–62.12 °C — i.e. the **safety-shield bypass (62 °C) is binding** for all three. The shield (pump off) caps every design's collection, flattening differences. |
| **Tm ≤ delivery temperature** | Operating conditions / metric | **Reasoned (physics), not yet simulated** | PCM latent release holds water near Tm. With Tm 42.5–49 °C vs a 45 °C threshold, RT44HC (Tm = 42.5 °C in the project DB), OM42 (44 °C), lauric acid (44.8 °C) cannot maintain ≥45 °C by themselves. The metric `E_load` nevertheless credits heat released at 43–44 °C as "useful". |
| **Collector output independent of flow** | Model limitation | **Demonstrated** | `collector_model.py:37–60`: `a = A·(FRτα·I + FRUL·T_amb)`, `b = A·FRUL` with constant `FR`; no flow dependence. Flow therefore can only act through h_w (Wakao–Kaguei, `heat_transfer.py:97–111`) and pump power. |
| **PCM-side resistance dominates h_w, so flow barely matters** | Model limitation | **Demonstrated (calc.) + CFD-supported** | Per capsule, R_pcm = r/(5k) (`heat_transfer.py:139`) with k = 0.14–0.30 W/m·K gives an equivalent coefficient of ~50 W/m²K at r = 20 mm vs h_w ≈ 130–290 W/m²K over the allowed flow range → total UA changes only ~15–20 % across 0.01–0.05 kg/s (my hand calculation, superficial velocity ≈ 1e-4–6e-4 m/s). The project's own CFD (`openfoam_cfd/docs/CFD_FINDINGS.md` §3) finds the lumped r/(5k) is ~2× too pessimistic (φ median 0.47) — but recalibrating changed annual energy by only 0.06–0.16 % (§4), so heat transfer is *not* the limiting factor. |
| **Single lumped water node + single lumped PCM node** | Model limitation | **Demonstrated (code); consequence per project CFD** | `tank_model.py:264–266` (one water temperature) and one PCM temperature for all capsules (one `h_pcm`). No stratification, no melt front. `openfoam_cfd/docs/00_INDEX.md` §3: "A stratified tank delivers 27 L at ≥ 45 °C from a state where a fully mixed single node (43 °C) delivers none; energy totals are unaffected, temperature-threshold metrics are." So threshold-based metrics (retention, delivery compliance) are the ones a mixed-node model cannot represent. Arrangement cannot matter thermally in a mixed tank by construction (every capsule sees the same water). |
| **Ergun pump model is physically empty** | Numerical / implementation | **Demonstrated** | ΔP across the capsule bed ≈ 1e-5–1e-2 Pa; pump energy ≈ 1e-7 kWh/yr. The real hydraulic loop (collector, piping, fittings) is not modelled, so "pressure_drop_limit" never binds and pump energy cannot discriminate designs. |
| **Demand time misalignment** | Numerical / implementation | **Demonstrated (re-run), needs confirmation** | See headline #1 and the table below. |
| **Metric `E_load` rewards overheating, ignores 45 °C threshold, ignores night delivery** | Metric mismatch | **Demonstrated (code)** | §3.2 item 9. |
| **Energy balance, units, time step** | Numerical | **Partly verified** | Gate-1 residuals ≤ 0.0004 % (`phase4` report) — but run on the pre-retarget PCMs. Time-step convergence (5 min, sub-stepping) has **not** been tested [O]. Units in the files I read are consistent (J, W, kg). |
| **Capsule wall / PCM volume consistency** | Implementation | **Demonstrated** | §3.2 item 3 (5.9–11.5 % PCM-mass overstatement; wall thermal mass omitted). |
| **Water-only baseline vs PCM equivalence** | Fairness | **Verified** | `run_case.py:78,92–97`: baseline = `pcm_name=None`, `n_capsule=0`, full water mass, same weather/demand/shield/mains; PCM case = same, minus displaced water. |

**Re-run of the existing code with the demand applied in local time [V — my scratch script, repo untouched]**
`timing_shift_hours` is the code's own parameter; shift 5.0 ≈ UTC+5, 5.5/6.0 ≈ UTC+5:30 (nearest-hour lookup makes them identical). PCM designs are the *already-selected* ones (not re-optimised).

| Regime | Shift | Plain useful kWh | Plain SF | PCM useful kWh | PCM SF | PCM gain |
|---|---|---|---|---|---|---|
| 0 | 0 (as is) | 1584.8 | 0.550 | 1588.1 | 0.554 | 0.204 % |
| 0 | 5.0 | 1098.9 | 0.359 | 1106.4 | 0.362 | 0.677 % |
| 0 | 5.5–6.0 | 1085.8 | 0.340 | 1094.6 | 0.343 | 0.811 % |
| 1 | 0 | 1843.4 | 0.617 | 1845.6 | 0.618 | 0.121 % |
| 1 | 5.0 | 1199.3 | 0.395 | 1203.3 | 0.396 | 0.331 % |
| 1 | 5.5–6.0 | 1195.9 | 0.376 | 1201.6 | 0.377 | 0.477 % |
| 2 | 0 | 1788.9 | 0.582 | 1791.2 | 0.585 | 0.128 % |
| 2 | 5.0 | 1208.7 | 0.383 | 1213.3 | 0.385 | 0.376 % |
| 2 | 5.5–6.0 | 1185.9 | 0.361 | 1191.6 | 0.363 | 0.476 % |

Implications **[O]**: (i) the correction roughly triples the PCM margin but it stays <1 %, so the sizing/capacity argument above still holds; (ii) solar fractions of 0.34–0.40 fall *below* the Gate-4 benchmark band 54–84 % (`system_config_shared.yaml:104–105`), so the Phase-4 calibration would have to be revisited; (iii) the `Tm_target` retargeting (which uses the same simulation) must be redone after the fix.

**What cannot yet be concluded:** whether PCM *can* deliver a meaningful benefit under standards-compliant sizing (IS 12976, §5 WP3) — the project's own earlier test (CLAUDE.md §3.5, `objective2-rajasthan/docs/09…` §7, Case A: 112.5 L tank) showed larger solar fractions and "best PCM marginally beating the plain tank" but did not quantify retention or night delivery. That must be run as a *diagnostic* (in-memory override, frozen files untouched), never as an optimisation variable.

### 3.4 Do the fixed parameters fundamentally constrain the benefit? **[V arithmetic / O decision]**

- Yes for *annual energy*: the ceiling in §3.3 (≤ ~2 % at current loadings, ≤ ~13 % at the 20 % cap before displacement) bounds any design. The honest statement is "within the fixed sizing, PCM can add at most a low-single-digit percentage to annual energy".
- The place where PCM can matter is **timing and temperature** (night/morning delivery above 45 °C), which a mixed single-node model cannot show and the current metric does not measure.
- **Quantify without changing fixed parameters:** (a) report the analytical capacity ceiling (m·L per cycle, cycles/day actually achieved) next to every result; (b) a supplementary "sizing diagnostic" table using IS 12976-compliant values *as in-memory overrides*, clearly labelled non-authoritative, repeating the project's earlier Case A approach; (c) a "headroom" metric = achieved gain / theoretical ceiling.

---

## 4. Phase 2 — Literature evidence map

### 4.1 Matrix (one row per paper/configuration; only papers I read or whose summary I name)

| Paper (verified cite) · status | System / question | Variables varied | PCM & geometry | Conditions | TES metrics (exact definition) | Methods | Reported findings (location) | Limits / applicability | Reusable | Var. relevance (T/A/N/F) | Supports / contradicts / silent on current impl. |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Chen 2025**, ECM:X 26, 100910 · *read* | Flat-plate collector + 40 L tank + RT35HC in PCM tubes; TRNSYS; optimise storage efficiency & retention (p.1, Table 1) | 9 factors (Table 7): PCM yes/no; PCM volume 10/15/20 %; PCM tubes 12/14/16; fluid (water/Al₂O₃/CuO); **mass flow 0.02/0.025/0.03 kg/s**; collector tubes 9–11; plate material; tilt 20.4–24.4°; azimuth −45/0/45° | RT35HC paraffin; pipe height 450 mm, 12 pipes, 0.0037 m³ (Table 1); **tube diameter/thickness not varied** | Taiwan; collector 0.505×0.32 m (0.16 m²), tank 0.04 m³ | **η = (Q_store+Q_latent)/(A·E)** (Eqs. 53–56); **retention time = time after sunset until tank water < 30 °C, no solar** (p.12–13) | L36 Taguchi, S/N (LTB), ANOVA, GRA (ζ = 0.5), confirmation runs | Optimum η 94.2 %, retention 31.7 h (+28 %, +14.6 h) (Tables 24–25; conclusions). **ANOVA contribution to η: PCM tubes 0.29 % (p = 0.109), flow 0.36 % (p = 0.068), PCM vol. 1.18 %; to retention: PCM vol. 0.31 % (p = 0.751), PCM tubes 0.57 % (p = 0.598), flow 0.45 % (p = 0.666)** (Tables 13, 17). Collector plate material dominates (44.7 % / 60.0 %). Validation within 5 % (Table 10): w/o PCM η 66.16 vs 63.41 %, retention 17.13 vs 16.59 h; with PCM the experiment could only measure *sensible* storage. | Collector area 0.16 m² & tank 40 L ⇒ 250 L/m² (≫ IS 12976 100 L/m²); efficiency > 90 % is unusually high for a collector-driven system (definition divides stored energy by incident energy over a window — treat with caution); 5 "repeat" columns differ by ≤0.2 % (pseudo-replicates, so ANOVA error df is optimistic); threshold 30 °C ≠ 45 °C; PCM presence shifts retention by only ≈ 1.2 h (18.33 vs 17.13 h) in validation. | L36 design recipe; S/N & GRA formulas; retention definition (adapt threshold); factor-significance logic | T: partly (volume %); N: yes (tubes); F: yes; A: no | **Supports** the finding that capsule count and flow have small effects; **does not support** a claim that thickness/arrangement matter (not tested). |
| **Barqawi 2025**, Muthanna JET 13(3):1–14 · *partly read (pp. 1, 6, 9)* | Tank + coil + PCM containers; 3-phase lumped ODEs; **NN predicts pump flow multiplier** | PCM container volume V_p 0.025–0.05 m³ & area A_p 2.5–5.0 m² (P01–P05); five synthetic climates; control (fixed vs NN) | Generic organic PCM, Tm = 44 °C, L = 165 kJ/kg, ρ 850, cp 2.1/2.3 kJ/kgK; k not reported | 33°N, 44°E; 14 h runs; no draw-off; no ambient loss | Stored energy via Eqs. 11–16 (sensible + latent), reported in MJ/kg | RK45; NN 8→64→32→16→1, Adam, 100 epochs, **trained on synthetic rule-based labels**, "90 % validation accuracy" (p. 6) | +2.5–4.1 % energy, 12–18 % lower pumping (summary; Table 3); no-PCM baseline 12.3 MJ/kg vs +26 % with P01 (p. 9); P03 and P04 behave identically (same V_p, A_p) (p. 9) | **Not a design-optimisation paper.** Simulation-only; no draw; no losses; target labels synthetic; energy unit "MJ/kg" for a system-level quantity is ambiguous | Three-phase ODE structure; event detection; flow-multiplier idea (belongs to O3) | T: no; A: no; N: no; F: yes (control) | **Silent** on design variables; relevant as an O3 precedent. Do not cite as "ML-driven design optimisation". |
| **Kou 2025**, Build. Environ. 285:113674 · *partly read* | Heat-pipe + PCM building wall, 61 Chinese cities | **ρH, Tm, λ** of PCM (3 continuous variables); *thickness and transition range fixed* (§2.2.2) | Material properties only | Heating season; with/without HVAC | **ESR = (Q_RB − Q_HP)/Q_RB**, **IDTD = (IDDC_RB − IDDC_HP)/IDDC_RB** — both *relative to a no-PCM reference building*; climate index RRTD_HS (Eqs. 12–18) | **Particle swarm optimisation, population 20, 30 iterations** (≈ 600 simulator calls per city) | Optimal PCM: highest λ and enthalpy within ranges; Tm ≈ T_L + 2 °C with HVAC; ESR/IDTD 30–100 %, linear in RRTD (Conclusions) | Building envelope, not a water tank; no capsule geometry | PSO set-up; **reference-relative metrics**; climate-indexed reporting | T/A/N/F: no | **Silent** on geometry; supports reporting gain *relative to a reference* and a climate index. |
| **Avargani 2021**, SETA 47:101350 · *partly read* | Encapsulated paraffin bed in SWH tank; CFD (COMSOL) | Bed porosity 0.2–0.5; bed length/diameter (0.6×0.3 m); collectors in series; flow | **Capsule diameter 55 mm**; porosity 0.2–0.5 | Circular-trough (concentrating) collector | Hot-water volume at 60 ± 2 °C and duration (abstract; conclusions) | Experimentally validated CFD | 300 L at 60 ± 2 °C for 7 h (one collector, bed Ø0.3 m × 0.6 m); up to 1200 L/8 h with two collectors; high flow → outlet never reaches Tm | Concentrating collector ≠ flat plate; PCM *is* the storage bed in the flow path; PCM fraction ≈ 50–80 % (1 − ε_b) | Only literature datum for capsule **diameter (55 mm)** and **bed porosity** | T: 1 point; A: packed bed; N: via bed volume; F: qualitative | **Contradicts the structure** of the O2 model (PCM immersed in a mixed tank vs bed in the flow path). Demand-scale reference only (`CLAUDE.md` §3.3). |
| **Li 2020**, J. Energy Storage (2020), doi:10.1016/j.est.2020.101371 *(volume/pages not verified)* · *partly read* | PCM tank design for pool heating | PCM volume, heat-pump capacity (design variables); RSM surrogate | — | — | Energy-saving and cost ratios | RSM + NSGA-II + LINMAP/TOPSIS (double/triple objective) | — | Different application | Multi-objective workflow & decision rules | Method only | Supports surrogate + Pareto + decision rule pattern. |
| **IS 12976:2023** (BIS, First Revision, Nov 2023) · *partly read* | Code of practice for SWH systems | — | — | — | f-chart solar fraction (§7.1) | — | §4.2: tank stores "1.5 to 2 times the average daily hot water usage"; "tank capacities are generally chosen between 40 l/m² to 100 l/m² of collector area"; §7.1 correction C3 relative to **75 l/m²**, valid 37.5–300 l/m²; §8.2 overheating protection by stopping circulation | Code of *practice* (guidance); does not cover PCM | Sizing check; shield justification | — | See §5 WP3. |
| Eldokaishi 2022 · *summary only* | Water–PCM SDHW, ANN surrogate | A_c 1–8 m², V_st 50–240 L, Tl, Tp, V_f | capric-acid-like, 182 kJ/kg | 189 L/day, 8 L/min draw | Solar fraction | ANN trained on 250–10,000 LHS/Sobol samples | R² up to 0.9999 | Different PCM class, climate | LHS/Sobol sample-size study | — | *(re-verify from PDF before citing)* |

### 4.2 Synthesis by topic (what the evidence does and does not say)

1. **Energy balances / TES capacity.** Chen defines η with sensible + latent terms (Eqs. 53–55); Barqawi tracks sensible/latent separately (Eqs. 11–16). Neither defines "useful recoverable energy above a delivery threshold". **[P]** Use a threshold-based definition (§WP1).
2. **Heat retention and discharge.** Only Chen defines retention (time after sunset until tank < 30 °C, no draw). It is a no-draw metric dominated by tank insulation. Chen's data: PCM raises validated retention from 17.1 to 18.3 h (+7 %). No source I read defines retention under draw-off.
3. **Capsule thickness/diameter.** **[O] unresolved.** Chen did not vary tube dimensions; Barqawi varies volume/area only; Avargani uses one diameter (55 mm); Kou holds thickness fixed. The CFD folder explored d = 40–80 mm only within the already-assumed range.
4. **Arrangements/packing.** No read paper varies arrangement. Chen cites Park et al. (tube number ↑ → faster melting) via its reference list [50] *(not read)*. **[O] unresolved.**
5. **Melting/latent utilisation.** Project CFD (`CFD_FINDINGS.md` §3): natural convection shortens 90 % melt by a median 2.35×; the lumped model is ~2× too slow; μ and β are *assumed*, shifting melt time ±10–12 %. Not experimentally validated (`00_INDEX.md` §4).
6. **Flow rate.** Chen 0.02–0.03 kg/s (citing literature that performance declines above 0.03 to 0.05 kg/s) — on a 0.16 m² collector, i.e. ≈0.125–0.19 kg/s per m², **4–6× above** the project's 0.01–0.05 kg/s on 1.5 m²; so the range is *not directly transferable*. Barqawi: velocities 0.02–0.05 m/s, multipliers 0.3–0.6.
7. **Standby losses / overnight.** Config: U_tank = 0.8 W/m²K, tank area 0.789 m² (my calc. from `tank_dimensions_m`) ⇒ UA = 0.63 W/K, C = 209 kJ/K, τ ≈ 92 h. With no draw, an 8 h night loses only ~3 K from 60 °C (my arithmetic, ambient 25 °C) — so a *no-draw* retention metric is dominated by insulation; PCM at 1.2 kg × 250 kJ/kg offsets ≈ 300 kJ ≈ 4.4 h of standby loss at ~19 W, **if** Tm exceeds the threshold.
8. **Weather-driven evaluation.** Kou uses 61 cities and a climate index; Barqawi uses five synthetic days. Objective 1 provides ten years.
9. **Surrogates, DOE, optimisers.** Chen: L36 + S/N + ANOVA + GRA (no surrogate). Kou: PSO (600 sims/city). Li: RSM + NSGA-II. Eldokaishi *(summary-only)*: ANN on LHS/Sobol. **Neither Chen nor Kou uses a surrogate.** The project's grey-box runs a full year in **≈0.8 s** (I timed a plain-tank year), so direct simulation of ~10⁴–10⁵ year-runs is feasible on a laptop (§WP5).
10. **Validation/uncertainty.** Chen validates TRNSYS against its own rig (≤ 5 %, Table 10). Barqawi: simulation-only. The project has *no* experimental comparison (`openfoam_cfd/docs/00_INDEX.md` §4 item 1).
11. **Standards.** IS 12976:2023 (see WP3).

### 4.3 Literature-supported ranges per design variable

| Variable | Project range now | What the literature gives (source) | Verdict |
|---|---|---|---|
| Thickness (PCM conduction distance) | radius 0.02–0.04 m (via d 0.04–0.08) | Only datum: capsule Ø 55 mm → radius 27.5 mm (Avargani 2021, Table-2 excerpt). Chen: PCM volume share 10/15/20 % (Table 7). None varies thickness. | **Unresolved.** Propose a bounded sensitivity study (§WP3), not a literature-backed interval. Check commercial capsule availability with a vendor **[O]**. |
| Capsule count | 8–37 | Chen: 12/14/16 *tubes* (Table 7), found insignificant (Tables 13, 17). No count range for spherical capsules. 37 is arithmetic (20 % × d_max), not geometric: hex packing of Ø 80 mm in this tank fits ≈ 91 spheres (13/layer × 7 layers; my calculation from `pack_staggered`). | **Unresolved.** Define by PCM mass/fraction and packing feasibility. |
| Flow rate | 0.010–0.050 kg/s | Chen 0.02–0.03 kg/s (not transferable per unit area, §4.2 item 6); Avargani: high flow prevents reaching Tm. | **Partly supported** only as an order of magnitude; re-derive per m² collector. |
| Arrangement | single-layer / staggered / radial | None. | **Unresolved**; project-defined categories. Needs a stratified model to matter (WP2). |

---

## 5. Phase 3 — Redesign plan: nine work packages

Conventions: **Effort** = student weeks, an *estimate* [P], single person, not including waiting for the guide. **Thresholds** marked [P] are proposals, not project or literature facts.

### WP1 — Define thermal-energy-storage metrics

**Purpose.** Replace "annual `E_load`" (§3.2 item 9) with a physically meaningful, threshold-aware metric set.
**Inputs.** Simulator state variables (T_w, T_pcm, f_melt, Q-terms), demand profile, 45 °C target, IS 12976 context. Chen Eqs. 53–56 and retention definition (§4.1).
**Method [P] with evidence.** Define (all per regime, per weather year, then aggregate):
- **A. Stored energy** E_stored(t) = m_w·cp·(T_w − T_ref) + m_pcm·[h(T_pcm) − h(T_ref)] (+ wall: m_wall·c_wall·(T_pcm − T_ref)), with T_ref = T_mains. `h` is the existing enthalpy function (`capsule_enthalpy.py:80–88`), so latent + sensible are counted once. Report *total stored* and **E_rec,45 = recoverable above 45 °C** = water above 45 °C plus PCM energy releasable at T ≥ 45 °C (zero if Tm < 45 °C). Primary measure: **E_rec,45** (answers "useful above the delivery threshold"); total stored is secondary.
- **B. Retention.** (i) **τ_hold,45** (no draw): from end of charging (daily maximum E_rec,45 or local sunset 18:00 — choose one and fix it [A]) until the *delivery* temperature < 45 °C. (ii) **τ_serve**: for the project's demand profile, volume (or % of the evening/morning demand) delivered at ≥ 45 °C between 18:00 and 08:00 local with no solar input. Report separately; they are not equivalent. Chen's 30 °C threshold is *not* used (project threshold is 45 °C).
- **C. Peak temperature.** T_deliv,max = max outlet (top-node) temperature; T_pcm,max = max over PCM nodes (safety, ≤ 65 °C); T_w,max (scald, ≤ 75 °C). Interval: daily maxima and annual maximum. Never mix these.
- **D. Latent-heat utilisation.** LU = (1/N_days)·Σ_day [(f_melt,max − f_melt,min)] and `full_cycles`; or ∫|dh_latent|/(m·L) per year. Computable from existing `f_melt`; `complete_melt_cycles` already exists (`tank_model.py:336–341`).
- **E. Supporting.** Delivered energy at target (E_del,45 = Σ ṁ·cp·(min(T_out, 45) − T_m); this is what `solar_fraction` already approximates), SF, compliance hours (draw-weighted, not clock hours), unmet energy, standby/ambient loss, ΔP and pump energy (only after hydraulics are made meaningful), shield-activation hours.
**Primary objective [P]:** maximise **E_del,45 over the night-and-morning window plus daytime** (i.e. annual E_del,45), with **retention τ_serve** and **T_pcm,max ≤ 65 °C** as constraints/secondary objectives; use **ε-constraint or Pareto**, not a weighted sum. If the guide wants a single score, use GRA as Chen does — but only with a documented weight rationale and a weight-sensitivity analysis (Chen's own GRA weights are equal, Eq. 17).
**Why annual `E_load` is inadequate:** counts above-target and below-target heat equally, does not distinguish night from day, and (§3.3) is insensitive to the timing at which PCM acts.
**Artifacts.** `metrics_definition.md`, unit-tested metric functions, a table mapping each metric to simulator variables.
**Acceptance [P].** (1) Closure: E_stored(t₁) − E_stored(t₀) equals ΣQ terms within the project's existing 0.1 % Gate-1 limit; (2) metric of the plain tank equals hand-calculated value on 3 synthetic days (pass/fail); (3) no double counting: sensible+latent PCM terms sum to `h(T_pcm)·m` exactly.
**Verification.** Analytical test days (constant draw, constant irradiance); compare E_del,45 with the existing `solar_fraction` (should agree where T_w ≤ 45).
**Risks / fallback.** Threshold metrics are noisy near 45 °C → use smoothed (e.g. ±0.5 K) variants as sensitivity. Fallback: keep SF as the primary.
**Effort.** 1.5 weeks.
**Guide decisions.** Primary objective; start of the retention window; whether mixing-valve tempering is modelled.

### WP2 — Repair physical model / simulator requirements

**Purpose.** Minimum changes for the four variables to affect results *when physically they should*.
**Inputs.** `src/simulation/*`, `src/design/geometry.py`, `openfoam_cfd/` (inventory below), IS 12976 §8.2.
**Recommended method.** Two levels, both proposals **[P]**:
- **Level 1 — defect repair (targeted, required).** (a) Apply demand in local time (confirm with guide first) and add a unit test that the peak draw falls at local 07:00/19:00; (b) use inner volume (d − 2·t_wall) for PCM mass and add wall thermal mass; (c) fix leap-year handling (drop 29 Feb or normalise per day); (d) make `E_del,45`, retention and latent-utilisation outputs available in every run (`record_hourly` summaries); (e) add a conservative real loop-pressure model for pump energy or **drop pump energy as an objective** until one exists; (f) time-step and sub-step convergence test (Δt = 300/150/75 s).
- **Level 2 — structural upgrade (needed for arrangement and thresholds to matter).** Replace the single water node by a **1-D multi-node stratified tank** (e.g. 8–12 nodes; plug-flow draw, buoyancy mixing, inter-node conduction) with PCM capsules assigned to nodes according to *arrangement* (vertical distribution), each PCM sub-model keeping the CFD-calibrated closure φ (median 0.47) instead of ×2-after-50 %-melt. Evidence for need: project CFD tank result (27 L vs 0 L delivered at ≥ 45 °C), and arrangement cannot otherwise act. A full CFD/porous-media model is **not** needed for the optimisation loop (cost) — use it only for calibration.
- **Not recommended:** per-capsule 3-D CFD inside the optimiser.
**Capsule geometry & independence of thickness.** For a solid-filled sphere of outer diameter D and wall t_w, the PCM conduction distance is R_in = D/2 − t_w; **thickness and diameter are the same degree of freedom**, so the current code samples diameter and derives thickness (§3.1 claim 2). Physically consistent options **[P]**:
  1. *Reparametrise (recommended default):* sample **PCM thickness (inner radius)** as the variable, derive D = 2(R_in + t_w); drop the redundant diameter bound (this removes the dead zone and the 0.04 m floor artefact). Four variables remain: thickness, arrangement, count, flow.
  2. *Cylindrical tube capsules (Chen uses PCM tubes):* radius (= thickness) and fill length are then independent; count and arrangement (in-line/staggered/radial) map naturally; requires changing "capsule shape = sphere only" (`design_bounds_shared.yaml:73`, a 40-hour scope cut) — guide approval needed.
  3. *Hollow-core spherical shell or flat slab capsules:* thickness independent of overall size, but needs a manufacturing check.
  Thickness and count interact through PCM mass (m ∝ N·R_in³). **Any thickness ablation must hold PCM mass fixed** (vary N ∝ R_in⁻³) to separate the heat-transfer effect from the mass effect.
**Water displacement / fixed tank volume.** Keep the current treatment (water volume = tank − PCM volume − wall volume). Add a check that packing fits the *fixed* tank (`geometry.py` already does) and report PCM fraction alongside every result.
**Night-hold and draw-off scenario [P], defined from the project's own demand profile.** Use the existing 24-h profile (two peaks: 07:00 ≈ 11 % and 19:00 ≈ 15 % of 300 L, `demand_profile_rajasthan.csv`) in local time. Window: from the last draw of the evening peak (~22:00) to the end of the morning peak (~09:00); no solar input. Initial state: the plain-tank's *own* end-of-day state on the same day (not a hand-picked sunny state); the PCM tank starts from the same weather day. Metrics: delivered volume ≥ 45 °C and energy, minimum delivery temperature, τ_serve. Evaluate over all days and report the distribution (not just a favourable day). This avoids designing a scenario that favours PCM.
**`openfoam_cfd/` inventory [V]** (`OBJECTIVE2/Objective---2/openfoam_cfd/`): (i) single-capsule axisymmetric 5° wedge, `buoyantPimpleFoam` + enthalpy-porosity, 48-case DOE (d 40–80 mm, 0.010–0.050 kg/s, 3 PCMs), 48 conduction twins, mesh study (256–2500 cells; t90 changes 9 % between production and finest mesh), sensitivity to assumed μ, β (±10–12 %); (ii) packed-bed `porousHeatTransferFoam` cases driven by hourly grey-box temperatures — agrees with the grey-box to 0.2–0.8 K RMSE over 48 h; (iii) water-only tank charge/draw (laminar); (iv) one-riser collector strip (reproduces F_R·U_L = 4.5 and F_R·τα = 0.75 given τα = 0.84). **Not validated against any measurement** (`00_INDEX.md` §4).
**What can be validated against it:** the lumped R_pcm closure (via φ), the stratified-tank delivery volume, collector F_R·U_L. **What cannot:** arrangement (single capsule has no neighbours), real PCM supercooling/volume change, any experimental quantity.
**Staged verification [P].** (1) Analytical energy balance and limiting cases (existing Gate 1/2 style, rerun after repairs); (2) a lumped sphere vs analytical Stefan/conduction solution; (3) multi-node tank vs the CFD tank draw case *only after* matching boundary conditions (the CFD tank is water-only, laminar, ports on axis); (4) capsule closure vs the CFD wedge cases at matching Biot/driving ΔT; (5) literature benchmarks (Chen Table 10 retention without/with PCM; Avargani 300 L/7 h *as a demand-scale reference only*). **Do not claim CFD validation until the reference cases are shown comparable.**
**Outputs.** Repaired simulator behind a version tag; model-change log; verification report.
**Acceptance [P].** Gate 1 residual ≤ 0.1 % (existing); annual energy changes < 0.05 % when Δt halves (proposed); PCM mass volume-consistent to 1e-6; demand peak lands at local 07:00/19:00; the stratified model reproduces the project CFD's "mixed 43 °C delivers 0 L vs stratified 27 L" qualitatively.
**Risks / fallback.** Level 2 may take longer than planned; fallback = Level 1 only plus an explicit statement that arrangement/threshold effects cannot be resolved by the model (an honest negative result).
**Effort.** Level 1: 2 weeks; Level 2: 3 weeks (**5 weeks total**, estimate).
**Decisions already made (user, 2026-10-26):** local-time demand fix confirmed; multi-node tank approved. **Still open:** shape family; whether to keep the shield as default.

#### WP2-C — CFD tier: OpenFOAM and ANSYS Fluent for **checking and calibration only** (user decision 2026-10-26)

**Principle.** CFD is far too slow to sit inside the optimisation loop (a capsule case takes minutes to hours; the optimiser needs 10⁴–10⁵ evaluations). So CFD has three jobs: **(1) calibrate** the closures the fast simulator uses, **(2) cross-verify** the numerics (two independent codes), **(3) spot-check** the final designs. Neither code is allowed to change the four fixed parameters. **Neither provides validation against measurements**; validation needs experiments or compatible published data (§WP8).

**Tools and roles.**

| Tool | Role | Why | State today |
|---|---|---|---|
| **OpenFOAM v2406** (WSL2, existing `openfoam_cfd/`) | Primary calibration engine; batch DOE; packed-bed (`porousHeatTransferFoam`) and tank cases | Free, scriptable, **already built and QC'd** (48 capsule cases + 48 conduction twins + 6 sensitivity + mesh studies; energy balance < 3 % on 48/48) | Exists; melting only; PCMs are the *retargeted* RT44HC / OM49 / lauric acid, **not the O1 top-3** |
| **ANSYS Fluent** (enthalpy-porosity melting/solidification, 2-D axisymmetric) | **Independent cross-check** of OpenFOAM on a subset; GUI-based mesh/time-step studies; optional packed-bed (porous-zone, non-equilibrium) check | Precedent in the sources: Yan et al. 2025 ran an enthalpy-porosity melting model in ANSYS Fluent with three grids (16,117 / 49,908 / 80,258 cells) and a 0.3 s time-step check; the Abdellatif 2025 review *(summary-level; Fluent passages only skimmed)* lists Fluent as a widely used enthalpy-method solver for solar PCM systems | **Not yet set up** in the repo. Licence terms, version and mesh/cell limits must be checked with the department **[A/O]** |

**Do not run both codes on the whole DOE.** OpenFOAM does the full calibration DOE; Fluent repeats a **small subset (8–12 cases, chosen to span diameter, driving ΔT and PCM)** to quantify code-to-code difference. This difference is a measured "numerical/model-form uncertainty" that goes into WP6.

**C1 — Capsule melting and, new, freezing (discharge) calibration (OpenFOAM, subset in Fluent).**
- Geometry: one PCM-filled aluminium sphere, 5° axisymmetric wedge (existing), wall 0.8 mm (frozen value).
- Cases: the **O1 top-3 PCM per regime** [decision 2026-10-26; the existing 48 cases used different PCMs and must be redone], radii spanning the WP3 sensitivity range, water-side coefficient from the same Wakao–Kaguei correlation the simulator uses at the 0.010–0.050 kg/s flows, driving ΔT spanning the simulator's range (existing cases: 5.2–24.3 K).
- **Freezing runs are new and essential:** overnight retention is a *solidification/discharge* process; the existing CFD only melts. Supercooling and volume change are not modelled today (`00_INDEX.md` §4 item 4) and stay as listed limitations unless data allow adding them.
- Output: a **closure function** φ (ratio of true to lumped internal resistance) as a function of Biot, Stefan and Rayleigh-type numbers (or a small lookup table), separately for melting and freezing. Existing evidence to beat: φ median 0.47 (range 0.30–0.73), natural convection speeds 90 % melt 1.8–3.3×; mesh effect ≈ 9 % on t90 at the production mesh (`CFD_FINDINGS.md` §1, §3).
- Missing inputs: liquid viscosity and thermal expansion are **assumed** in the existing cases (±10–12 % effect on melt time); replace with datasheet values from the O1 PCM database or manufacturer sheets and cite them **[O, action]**.
- Mushy-zone constant: Yan 2025 quotes recommended values of 10⁴–10⁷ for most calculations (§2.2); the existing OpenFOAM sensitivity found the Darcy constant immaterial (± < 8 %). Run it as a sensitivity in both codes.
- Where it enters: a **new versioned closure file** read by the repaired simulator (e.g. `configs/cfd_closure_v1.yaml`); the frozen `system_config_shared.yaml` keys (`liquid_convection_enhancement: 2.0`) are **not edited**. If the guide later wants it folded into the shared config, the WP7 rerun list applies.

**C2 — Code-to-code verification (OpenFOAM vs Fluent).** Same geometry, mesh density class, boundary condition, properties, mushy constant, initial state and stop criterion; compare t50, t90, liquid-fraction curve, wall heat flux and total stored energy. Mesh and time-step independence in both codes (Yan 2025's three-grid / time-step protocol is the template); report **Richardson/GCI** instead of the current informal "9 % below the finest mesh" note. **Proposed acceptance [P, not a literature value]:** t90 agreement within 5 %, energy balance < 3 % (the project's existing QC level). A larger gap is reported as uncertainty, not hidden.

**C3 — Tank stratification check.** Compare the new multi-node tank (WP2 Level 2) against the existing **OpenFOAM water-only tank charge/draw cases** (`cases_tank/`, laminar, ports on axis) *for the draw-off thermocline only*; the CFD tank has no capsules, so it can confirm the stratification/mixing behaviour (the "27 L at ≥ 45 °C vs 0 L for a mixed node" finding) but **cannot** validate PCM–tank interaction. If the department's Fluent licence allows, a Fluent tank case with the same conditions is an independent second reference.

**C4 — Packed-bed / arrangement check (optional, bounded).** Use OpenFOAM `porousHeatTransferFoam` (existing; paper case reproduced from Fetsov & Lutsenko 2023 — *summary-only*) and, optionally, a Fluent porous-zone model, driven by the **hourly water temperatures from the simulator** for the chosen designs (existing practice: 3 Rajasthan beds, 48 h, agreement 0.2–0.8 K RMSE). Purpose: confirm that arrangement-dependent axial behaviour in the multi-node model has the right sign and rough size. Existing note predicts < 0.02 % arrangement effect on energy from a G0 analysis; the new check should say whether threshold/night metrics differ. **A single-capsule CFD cannot resolve arrangement; only this bed-level check can, and only approximately.**

**C5 — Design-point spot-checks (after S8).** For 1–3 final designs per regime: run capsule-level CFD at the design's operating window (radius, flow-derived h_w, PCM) and compare the PCM melt-fraction timeline with the simulator's over a representative 48 h; the gap enters WP6 as closure uncertainty (simulator rerun at closure low/high).

**C6 — Collector (optional).** The existing collector-strip CFD reproduces F_R·U_L = 4.5 (CFD 4.45) and F_R·τα = 0.75 given τα = 0.84 (assumed). It can be used to add a flow-dependent F_R correction **only if the guide wants flow to act on collection**; otherwise state that flow acts only through the PCM film coefficient.

**Data flow.** CFD runs → `closure_v1` (function + uncertainty band) → simulator (version-tagged) → training data (regenerated; old surrogate data become stale) → surrogate → NSGA-II. Any change to the closure triggers the rerun list in WP7.

**What each tool can and cannot support (for the paper).** *Can:* internal consistency of the lumped PCM model, size of natural-convection effect, melt/freeze time scaling, thermocline shape, code-to-code numerical uncertainty. *Cannot:* agreement with real capsules (no measurement exists in the repo), supercooling, volume change, real tank plumbing losses. Candidate **compatible published data** to check geometry/condition match before use: Al-Abidi's melting data used by Yan 2025 (triplex-tube, different geometry — likely *not* compatible), Avargani 2021's packed-bed experiments (concentrating collector, 55 mm capsules — packed-bed only). Declare "validated" only after a compatible case is confirmed; otherwise use "verified/cross-checked".
**Acceptance [P].** Closure function fitted with a stated residual; Fluent–OpenFOAM difference reported with mesh/time-step independence in both; every CFD number traceable to a case folder and log; no CFD-derived value enters the simulator without version stamp.
**Risks / fallback.** Fluent licence/limits unavailable → use OpenFOAM alone with a second mesh/solver-setting study and say "single-code"; freezing runs unstable → start with conduction-dominated cases and the existing early-stop logic; CFD cost → keep the wedge 2-D axisymmetric (250–2500 cells in existing work; far below typical student-licence cell limits, to be confirmed).
**Effort.** +1.5 weeks on top of WP2's 5 weeks (estimate [P]); Fluent setup is the main uncertainty.
**Guide decisions.** Which Fluent licence/version is available; whether a bench experiment (O4 hardware) will be used for true validation.

### WP3 — Redefine the physically feasible design space

**Purpose.** State each variable, its bounds, and which require approval, with the four fixed items untouched.

| Variable | Meaning / unit | Existing bounds & source | Literature support | Constraints / dependencies | Proposed exploration range [P] | Approval |
|---|---|---|---|---|---|---|
| PCM thickness (inner radius) | m | `pcm_thickness_m` 0.02–0.10 (derived); `capsule_diameter_m` 0.04–0.08 (`design_bounds_shared.yaml:70–71`) | 55 mm Ø single datum (Avargani) | Packing in fixed tank (Ø0.317 m × 0.634 m); PCM fraction cap; CFD Biot range; wall 0.8 mm | Sensitivity study first: radii 10–40 mm in ≥ 5 levels at **constant PCM mass**; then fix range | Yes |
| Count | – | 8–37 (derived from 20 % × d_max) | 12–16 tubes (Chen, different geometry) | N·V ≤ cap, hex fit ≈ 91 at Ø 80 mm | Define via **PCM fraction 0.5–20 %** and packing feasibility instead of a raw count | Yes |
| Flow | kg/s | 0.010–0.050 (`:80`) | 0.02–0.03 (Chen; not per-area transferable) | Pump/loop ΔP; collector F_R(flow) not modelled | Keep 0.010–0.050 provisional; add a collector F_R(flow) correction **or** state that flow only acts through the PCM film coefficient | Yes |
| Arrangement | categorical | single-layer / staggered / radial (`:74`) | none | Packing void fraction; stratification position | Keep three levels; evaluate only after WP2 Level 2 | Yes |

- **Fraction floor 10 % → 0.3 %.** Verified history in §3.1 claim 7. The 0.3 % floor is "just below the smallest reachable fraction (~0.54 %)" (comment lines 62–66), so it is non-binding by design. **[O]** I recommend defining the fraction range as a *consequence* of thickness × count (not as an independent bound) and keeping a physically motivated floor (e.g. PCM energy ≥ x % of daily load) instead.
- **Consistency with the fixed tank.** The geometry engine checks fit, stack height and passage fraction (`geometry.py:288–327`); capsule count ceiling 37 is *not* a geometric limit (≈ 91 fit at Ø 80 mm).
- **IS 12976 sizing question [V].** *Document:* IS 12976:2023 "Solar Water Heating Systems — Code of Practice" (First Revision, BIS, November 2023). *Clauses:* §4.2 — storage "should be … sized as to store 1.5 to 2 times the average daily hot water usage"; "tank capacities are generally chosen between 40 l/m² to 100 l/m² of collector area"; §7.1 — f-chart correction C3 relative to a **75 l/m²** reference ratio, defined between 37.5 and 300 l/m²; §8.2 — overheating protection by stopping circulation. *Units:* litres per square metre of collector area; litres of storage per litre/day of use.
  *Compliance of the fixed system:* 50 L / 1.5 m² = **33.3 L/m²**, below the 40 L/m² guidance and below the f-chart validity floor (37.5). Against the daily-usage criterion, 300 L/day ⇒ 450–600 L, so 50 L is **0.08–0.11× the recommended size** (and 112.5 L at 75 L/m² is still only 0.19–0.25×). The two criteria are mutually inconsistent for this combination: 300 L/day with 75 L/m² ⇒ ~6 m² collector. *Applicability:* it is a code of practice (guidance, not a mandatory limit) for general SWH systems and says nothing about PCM tanks. *Implication for O2:* (i) the project's earlier finding (CLAUDE.md §3.5) that undersized tankage forces overheating is consistent with these numbers; (ii) the result "PCM ≈ plain tank" is conditional on non-standard sizing; (iii) **do not change the fixed parameters** — flag to the guide and quantify with the diagnostics in §3.4.
- **Does the fixed sizing leave a meaningful feasible region?** For annual energy, no (§3.4 ceiling ≤ ~2 % at current loadings). For night/morning delivery above 45 °C it is **unknown** until WP1+WP2 are done. Plan: run the *capacity-ceiling* and *in-memory sizing diagnostic*; declare the region "meaningful" only if the best design beats the plain tank by more than the repeatability threshold (WP6) on at least one primary/secondary metric.
**Acceptance [P].** Every bound has a source or an explicit "engineering assumption" tag; no bound is derived from another bound; a boundary-artefact detector (WP6) reports 0 designs at an unjustified bound.
**Risks / fallback.** Guide may prefer to keep spheres; fallback = Option 1 reparametrisation.
**Effort.** 1.5 weeks. **Guide decisions.** All "Approval = Yes" rows; how to disclose the IS 12976 non-compliance in the paper.

### WP4 — Climate-representative evaluation strategy

**Purpose.** Replace single-medoid-year optimisation with multi-year evaluation without leakage.
**Inputs.** `daily_aggregates_<state>.csv` (320 points × 10 years), NASA POWER JSON (3,200 files for Rajasthan; **hourly resolution and variable list to be re-verified**), `cluster_assignments`, Objective 1 manifest.
**Verify first [O]:** temporal resolution/columns of each JSON, missing-data handling in `build_regime_weather.py`, whether *all four states* have hourly data for all member points, and the Uttarakhand 5-regime layout.
**Method [P].**
- **Representation.** Per regime: medoid plus *k* additional member points chosen by climate-feature quantiles (e.g. k = 2 [A]) × 10 years. Report per point-year, then aggregate population-weighted.
- **Years: roles.** Option A (recommended): *screening/DOE* on 2016–2020 (5 yr); *optimiser selection + surrogate hyper-parameters* on 2021–2023 (3 yr); **held-out test 2024–2025** — but these are the two lowest-GHI years (scale 0.957–0.970), so the test is *adverse*; Option B: blocked leave-one-year-out cross-validation (10 folds) plus a final untouched test of two years spanning the range (e.g. 2018, 2022); Option C: no split, report all 10 years with the design chosen by median — simplest but leaks. Trade-offs: A is clean but biased to a low-GHI test; B uses all data but multiplies cost; C is not defensible for a "held-out" claim.
- **Never use a favourable year.** The existing rule `max(frames, key=len)` (`build_regime_weather.py:74`) picks 2016, the sunniest year; retire it.
- **Statistics reported.** 10-year mean, median, minimum (worst year), range; with n = 10 a "5th percentile" is just an interpolation near the minimum, so report *worst year* and *P10-of-point-years* when member points are added; state that percentile estimates from 10 annual values are very uncertain.
- **Missing/incomplete data.** Record a gap table per point-year; reject a point-year if > x % hours missing [A, x = 2 %]; fill short gaps by linear interpolation with a flag; never impute whole days silently.
- **Fair baseline.** Plain-tank (water-only) run on exactly the same weather-year, demand, mains temperature and shield state for every PCM design; compare **paired differences per weather year**.
- **Mains temperature.** Currently one scalar per regime (e.g. 25.13 °C); consider a monthly series if the data exist **[O]**.
- **Leap years.** Normalise by number of days or drop 29 Feb.
**Artifacts.** `weather_inventory.csv` (point, year, hours, gaps, GHI mean), split manifest, per-regime weather-year panels.
**Acceptance [P].** Zero hours of leakage between roles (checked by year IDs); every weather-year has ≥ 98 % valid hours; paired baseline for every design-year.
**Risks / fallback.** If hourly data exist only for medoid points, use medoids × 10 years; if hourly data are missing for some years, fall back to the daily-aggregate scaling already used in `weather_ensemble.py` and state the limitation.
**Effort.** 2 weeks. **Decided (user, 2026-10-26):** split Option A. **Decided (user, 2026-10-26):** one representative point per cluster (see §6 item 8). **Still open:** data-quality threshold.

### WP5 — AI-driven optimisation: neural-network-ensemble surrogate + NSGA-II with active learning (**Option B, chosen by the user 2026-10-26**)

**Purpose.** Find, for every (state, regime, Objective-1 PCM), the Pareto-optimal combinations of the four O2 variables — **PCM thickness (sphere inner radius), capsule arrangement, number of capsules, flow rate** — under the fixed tank, collector, demand and O1 shortlist, and then choose one design per regime by the WP6 rule. This is what the authoritative Objective 2 asks for ("AI-driven design optimization model … optimal thickness, arrangement, number, flow … location-specific").

**Inputs / prerequisites.** WP1 metrics; WP2 Level 1 + Level 2 simulator and the CFD closure (WP2-C); WP3 design space; WP4 year roles (2016–2020 explore, 2021–2023 select, 2024–2025 test) and one representative point per cluster; O1 top-3 PCM per regime.

#### 5.1 Why B, and what the literature does and does not say

| Evidence | Status | What it supports | What it does not support |
|---|---|---|---|
| **Li et al. 2020** (J. Energy Storage, doi:10.1016/j.est.2020.101371) — abstract, §2.3–2.4 and nomenclature read | partly read | Same pipeline shape as B: simulated experiments (central composite design) → surrogate (RSM; quadratic model predicted R² 0.98–0.99 for the objectives that were fitted well, **0.52–0.57 for linear/2FI on one objective**) → **NSGA-II** double/triple-objective Pareto set → final decision by **LINMAP and TOPSIS** | Uses RSM, not a neural network; different application (pool heating). It shows low-order models can fail on nonlinear objectives, which is a reason to compare surrogates. |
| **Yan et al. 2025** (Applied Energy 390:125863) — abstract, §2.2 (ANSYS Fluent enthalpy-porosity, mesh and time-step independence), §3 (ML) skimmed | partly read | A **CFD-generated dataset of only 60 cases** was enough to train ML models (polynomial regression, SVR, random forest, **XGBoost best, 92 % accuracy**, Bayesian hyper-parameter tuning). Shows small simulator datasets can train useful surrogates and that a tree/boosting model must be one of the comparison models. | Predicts melting time of one geometry; no design optimisation loop. |
| **Liu et al. 2025** (Renewable Energy 238:121973) — review; Fig. 12 and the NSGA-II/MOPSO/DRL passage (pp. 12–14) read | partly read | NSGA-II and MOPSO are the standard multi-objective optimisers for PCM geometry problems; a DDQN agent scored 4.3 % and 1.6 % above them in one cited study. | The DRL result is a review citation (not verified at source); DRL is O3's tool, not O2's. |
| **Barqawi 2025** (pp. 1, 6 read) | partly read | A small feed-forward NN (8→64→32→16→1, ReLU, Adam, MSE, 100 epochs) is a plausible architecture size for this kind of data. | It controls pump flow; labels were synthetic; it is not a design optimiser. |
| **Chen 2025** (read) | read | Screening by designed experiment + ANOVA before optimising; multi-objective ranking by GRA. | No surrogate, no NSGA-II. |
| **Kou 2025** (partly read) | partly read | Metaheuristic (PSO, 20 × 30) over PCM parameters with **reference-relative metrics**. | Not geometry. |
| Eldokaishi 2022 | **summary only** | Feed-forward ANN surrogate with LHS/Sobol samples (R² up to 0.9999); re-verify before citing. | — |

So **no paper I read combines an NN-ensemble surrogate with NSGA-II for capsule geometry in a water heater.** The combination is a proposal assembled from verified parts (surrogate-assisted NSGA-II: Li 2020; CFD-seeded ML: Yan 2025; screening: Chen 2025). Say this in the paper.

#### 5.2 What learns, what it learns, how it guides decisions

- **What learns:** an **ensemble of 5 small feed-forward neural networks** (the "surrogate"). *Why an ensemble:* a single NN gives no uncertainty; the spread across members is a usable (if optimistic) uncertainty signal.
- **What it learns:** the mapping from the four design variables (+ one-hot arrangement) to the WP1 metrics, *as paired differences against the water-only tank on the same weather-year*, for one (regime, PCM) pair.
- **How predictions guide decisions:** NSGA-II evaluates ~10⁴–10⁵ candidate designs on the surrogate (microseconds each) to propose a Pareto front; the most promising and most uncertain candidates are **re-run in the real simulator**, added to the training set, and the ensemble is retrained (active learning). **The surrogate never produces a final result** — every reported number comes from the simulator (existing project rule, Bug-Fix 5). If the dense-grid check (5.6) shows the simulator is cheap enough to do the whole job, say so openly in the paper: the contribution then lies in the metrics, the physics and the uncertainty handling, not in the surrogate.

#### 5.3 Problem definition (all items [P] unless stated)

- **Decision variables:** thickness R_in (continuous, sphere inner radius; WP3 range), count N (integer), flow ṁ (continuous), arrangement (categorical: single-layer / staggered / radial). Geometry feasibility (packing in the fixed 0.317 m × 0.634 m tank, passage fraction ≥ 0.05, PCM fraction cap) is checked **exactly by the geometry function, not learned**.
- **Objectives (minimise the negatives), all paired against water-only:** f1 = night-and-morning delivered energy at 45 °C (WP1 B/E), f2 = annual delivered energy at 45 °C, f3 = overheating (shield-activation hours). PCM mass is carried as a **cost proxy** (tie-breaker), not an objective. This matches the primary/secondary split of §6A items 4–5.
- **Constraints:** T_pcm,max ≤ 65 °C with a 3 K guard (use the ensemble mean + 2σ so uncertain designs are penalised), T_water,max ≤ 75 °C, geometry feasibility, hydraulic feasibility once a loop model exists.
- **Per-pair models:** one ensemble per (state, regime, O1 PCM). With 3 PCMs per regime there are too few PCM "points" for a model to learn PCM properties, so PCM identity is *not* a learned input; PCMs are compared by their Pareto fronts.
- **Climate:** each regime is its own model, trained only on that cluster's representative-point years; the earlier practice of feeding 29–39 climate descriptors to a global model (which with 3 regimes only encodes regime ID) is dropped.

#### 5.4 Staged plan with gates (small experiment first)

| Stage | Action | Size (estimate [P]) | Gate to proceed |
|---|---|---|---|
| S0 | WP2 repairs, CFD closure v1, WP1 metric tests pass; **time one simulated year** with the new multi-node model | — | Runtime known. Current single-node year ≈ 0.8 s (measured); multi-node assumed 10–20× slower **[A, to measure]** |
| S1 | **Screening:** Taguchi L9 (3⁴) or 3-level factorial (Chen's tool) on the four variables, replicated over the 5 exploration years | 9–81 designs × 5 yr per pair | ANOVA says which variables matter; variables with no effect are fixed at a justified value and the search shrinks |
| S2 | **Initial DOE:** Sobol/LHS (Li 2020 uses central composite; Eldokaishi *(summary-only)* used LHS/Sobol) | ~100–150 designs per pair | ≥ 95 % of runs complete; no geometry failures slip past the exact gate |
| S3 | **Surrogate selection:** train the NN ensemble, **XGBoost** (Yan 2025's best), and a quadratic RSM (Li 2020); compare on held-out *designs* and held-out *years* | 5-fold + leave-one-year-out | Choose by **within-regime** RMSE and Spearman rank correlation, not global R² (§3.2 item 10). If XGBoost or RSM beats the NN ensemble, report it and say why B was kept or switched. |
| S4 | **NSGA-II** (pymoo or DEAP, both named in `CLAUDE.md` §3): population 100, 100–200 generations, mixed-variable operators (categorical handled by arrangement as an integer gene or an outer loop), 3 random seeds | 10⁴–10⁵ surrogate calls | Front stable across seeds (hypervolume spread inside the WP6 band) |
| S5 | **Active-learning rounds:** pick ~10 Pareto/uncertain candidates per round (largest ensemble disagreement or hypervolume gain), simulate on 2016–2020, add, retrain | 3–5 rounds | Hypervolume change < ε for 2 rounds, or budget used |
| S6 | **Dense-grid check:** simulate a regular grid (e.g. 6 radii × 6 counts × 3 arrangements × 5 flows = 540 designs) for one pair per state; compute how close the NSGA-II front is to the grid's true front | 540 × 5 yr per checked pair | NSGA-II front within the repeatability band of the grid front |
| S7 | **Selection years:** re-simulate the final Pareto set on 2021–2023; apply WP6 selection | ~20–50 designs × 3 yr | One design + alternatives per regime |
| S8 | **Held-out test:** run the chosen design and its plain-tank twin on 2024–2025 **once**; no tuning afterwards | 2 yr | Results reported as they are (note: these are the two lowest-sunshine years) |
| S9 | **CFD/Fluent spot-checks** of the chosen designs (WP2-C, C4) | 1–3 designs per regime | Closure-uncertainty band added to WP6 |

**Compute budget [P, estimate].** With 14 (regime, PCM-pair) groups per state set (3 + 3 + 3 + 5 regimes × 3 PCMs = 42 pairs across four states), 150 designs × 5 years × ~12 s ≈ 2.5 h per pair on one core, ≈ 105 h total, ≈ 13 h on 8 cores. Active learning and the grid add roughly 50 %. If the measured multi-node runtime is much higher, use **multi-fidelity**: 1 weather-year and a coarser time step for early rounds, 5 years only for the final rounds (the Uttarakhand folder already contains a multi-fidelity benchmark: `results/uttarakhand/multifidelity_*.csv`, not re-checked here).

#### 5.5 Surrogate and optimiser specification (starting values [P]; tuned on validation folds, not on the test years)

- **Network:** inputs 4 numeric + 3 one-hot (standardised); two hidden layers (32, 32), ReLU or tanh; outputs = the 3 objectives plus T_pcm,max and PCM mass; Adam, MSE, early stopping; **5 members** trained on bootstrap resamples with different seeds. Implementation on a laptop with scikit-learn `MLPRegressor` or PyTorch (CLAUDE.md names scikit-learn/XGBoost; PyTorch would be an addition [A]).
- **Targets:** mean over exploration years of the paired gain per metric, plus its year-to-year standard deviation as a second output if useful.
- **Uncertainty:** ensemble standard deviation. **Known weakness:** it understates uncertainty away from training data — hence mandatory re-simulation and the grid check.
- **Hyper-parameters:** tuned by validation folds; Yan 2025 used Bayesian tuning for its models, which is an option.
- **NSGA-II:** simulated-binary crossover and polynomial mutation for real genes, integer rounding for N, population 100, 100–200 generations, 3 seeds; constraint handling by feasibility-first.
- **Final choice from the Pareto front:** follow §6A (tie-breaker order) and WP6; **TOPSIS/LINMAP as in Li 2020 may be shown as a comparison, with a weight-sensitivity table** (Li uses these decision methods; arbitrary weights are not accepted without sensitivity analysis — brief rule).

#### 5.6 Why the old method is not repeated (kept for the paper's argument)

Random 600 candidates + Extra Trees ranking failed to give a reliable optimum because: the response was nearly flat (within-regime σ ≈ 2 kWh) while surrogate error (RMSE 0.37, max 1.70 kWh) was comparable; R² (0.99999) reflected regime offsets; Extra Trees gives no uncertainty and extrapolates as steps, so top picks sat at bounds (d ≈ 0.04 m, N = 37); and the objective itself rewarded heat above mains. B fixes these by (i) a better-posed metric, (ii) per-regime models judged on within-regime accuracy, (iii) uncertainty-aware active learning, (iv) a multi-objective front instead of one ranked score, (v) a grid check.

**Comparison with the other options (retained for the record).**

| Criterion | A: designed experiment only | **B: NN ensemble + NSGA-II (chosen)** | C: Gaussian-process Bayesian optimisation (kept as comparison) |
|---|---|---|---|
| Mixed categorical + continuous | natural (levels) | handled by encoding / outer loop | needs encoding |
| Evaluations | 9–81 | ~150–300 per pair incl. active learning | ~30–100 |
| Several objectives at once | via GRA | **native (Pareto)** | single objective (or scalarised) |
| Uncertainty | none needed | ensemble spread (optimistic) | **built-in** |
| Explainability | highest | medium | medium |
| Fallback | dense grid | A / C | A |

**Outputs / artifacts.** Per pair: DOE table, trained ensemble files with seeds, surrogate-comparison table (NN vs XGBoost vs RSM), Pareto fronts (3 seeds), active-learning log, grid-check report, selection-year and test-year result tables.
**Acceptance [P].** (i) Surrogate within-regime RMSE below the WP6 repeatability band, or the surrogate is declared unfit and the grid is used; (ii) NSGA-II front within the band of the grid front on every checked pair; (iii) ≥ 3 seeds agree on the selected design's metrics within the band; (iv) no selected design sits on an unjustified bound (WP6 test); (v) the test years are touched exactly once.
**Validation.** Hold-out designs, leave-one-year-out, grid comparison, repeated seeds, CFD spot-checks.
**Risks / fallback.** Flat response → many designs tie (reported as ties, §6A item 5); surrogate fails → dense grid (affordable if the multi-node runtime is ≤ ~20 s/year); NN not better than XGBoost/RSM → report and switch with justification; active learning chases noise → use paired objectives and a noise floor in the acquisition.
**Effort.** 4.0 weeks (estimate [P]).
**Guide decisions.** Whether comparison surrogates (XGBoost, RSM) are acceptable alongside the NN; whether PyTorch is allowed in addition to the project's listed stack.

### WP6 — Final design selection and uncertainty handling

**Purpose.** A reproducible, non-arbitrary selection rule.
**Procedure [P].**
1. Candidate set per regime = feasible designs for **each of the O1 shortlisted PCMs**.
2. Hard constraints: geometry/packing, T_pcm,max ≤ 65 °C, T_w,max ≤ 75 °C, hydraulic feasibility (when modelled), 45 °C target.
3. Objective: WP1 primary; secondary via ε-constraint/Pareto.
4. **Boundary-artefact test.** A selected design on a bound is accepted only if (a) widening that bound in a diagnostic run changes the primary metric by less than the repeatability band, or (b) the bound has an independent physical justification. Otherwise it is reported as "boundary-limited".
5. **Lower-ranked PCM selection.** Allowed only if its *paired multi-year* gain over the O1-rank-1 PCM exceeds the equivalence band **and** it satisfies all hard constraints with margin; the O1 ranking and the simulator-based ranking are both reported. (Rationale: O1 ranks climate fit; O2 ranks design performance; today's rule does not weight O1 at all — `select_deployable.py`.)
6. **Uncertainty sources:** weather year (paired differences), surrogate/GP posterior, numerical (time-step), stochastic optimiser (≥ 3 seeds), material-property uncertainty (k, ρ, L ±10 %, μ/β from CFD sensitivity).
7. **"Meaningful improvement" is not a universal percent.** It is defined as: gain over the water-only baseline > max(2·σ_repeat across weather years [paired], discretisation error from the Δt test, 2× the sensitivity to the largest uncertain property) **and** > the smallest practically relevant benefit set by the guide [A]. The current "0.04 % noise band" has no documented derivation [O] and should be re-derived.
8. **Ties.** If |Δ| < band, report designs as statistically indistinguishable and pick by a pre-declared tie-breaker order (lower PCM mass → lower cost proxy → fewer capsules → larger safety margin) — keeping the current spirit, but made explicit.
9. **Trade-offs** between stored energy, overnight delivery, pump energy: show the Pareto set; do not collapse.
**Deliverables per regime:** selected design; ≥ 2 feasible alternatives; metric table (mean, worst year, uncertainty); paired baseline comparison; reasons; boundary/tie flags.
**Acceptance [P].** A written selection log per regime that another person can reproduce from seeds and files.
**Effort.** 1.5 weeks. **Guide decisions.** Tie-breaker order; practical-relevance threshold; policy on lower-ranked PCMs.

### WP7 — Consolidate implementation across the four states

**Purpose.** One parameterised code path: `python pipeline.py --state {rajasthan|tamilnadu|assam|uttarakhand}`.
**Current status, verified directly [V].**

| State | Bounds / arrangement | Shield | Retarget | Weather yrs | Results state | Blockers |
|---|---|---|---|---|---|---|
| Rajasthan | v1.2, 3 arrangements, d ≥ 0.04 | on (v1.1 config) | Yes, O1 list replaced | 2025/2016/2016 | Phases 1–8 + CFD + supplementary fixes | Demand-timing; stale Phase-4; shortlist override |
| Tamil Nadu | v2.0, 3 arrangements, d ≥ 0.02, fraction ≥ 0.10 | none | Yes (`tm_retargeting_report.csv`) | 2016 ×3 | Phases run (results/tamilnadu) | Dead zone persists; Objective-1 TN `10_physics_validation.py` still hard-codes `T_DELIVERY_C=50` (`CLAUDE.md` §3.2, not re-checked by me) |
| Assam | v1.0, staggered only, count ≤ 24 | none | **No** (Tm 44 °C; O1 shortlist OM48/50/46) | 2025 ×3 + stray Rajasthan files | Phases through 8 present; **all 3 deployable PCM designs fail the 65 °C limit** (max PCM 66.1/67.7/70.0 °C, `meets_temperature_safety=False`) | README says Phase 8 not run (stale); Phase-7 "safety-verdict bug" documented in `docs/07…`; no radial packing; no shield |
| Uttarakhand | v1.1, staggered only, count ≤ 37 | none | Yes | 2016 ×5 (5 regimes) | Phases + multifidelity benchmarks | Different regime count; no radial; no shield |

**Shared vs state-specific [P].**
- *Shared:* simulator, geometry, metrics, optimiser, evaluation, plots; `system_config_shared.yaml` and `design_bounds_shared.yaml` (truly shared, one version).
- *State-specific:* weather (points/years), regimes/clusters, mains temperature, PCM shortlist **taken from O1** + property records, demand file (currently state-invariant), validation cases, logs/provenance.
**Dependency-aware rerun order [P].** (0) fix and confirm UTC/local timing; (1) verify data and configs (hashes, versions) per state; (2) repaired simulator + unit tests; (3) simulator verification gates on the *actual* shortlists; (4) water-only baselines (paired, multi-year); (5) metric implementation tests; (6) screening DOE; (7) BO/grid optimisation; (8) multi-year evaluation; (9) held-out validation + ablations; (10) robustness; (11) final tables/plots/handoff.
**Added by the algorithm-B / CFD update:** the CFD closure file (`closure_v1`), all trained surrogate ensembles, NSGA-II Pareto fronts, active-learning logs and the CFD case folders (OpenFOAM and Fluent) are stale whenever the simulator physics, metric definitions, O1 PCM properties or design bounds change; surrogates also go stale when the closure changes.
**Artifacts that would become stale if shared logic, bounds, metrics, materials or state config change [V list].** All of: `phase4_simulator_verification_report*`, `phase5_design_cases.*`, `phase6_surrogate_*` (including `.pkl`), `phase7_*`, `phase8_*`, `obj3_environment_contract_*.json`, `tm_retargeting_report.csv`, `fix1..7_*supplementary*`, `phase3_5_pcm_loading_sweep.csv`, all `final_plots/*`, per-state `recommendation_cards.md`, and the numeric claims in docs 05–09 and `O2_O3_COMPREHENSIVE_AUDIT_REPORT.md`. Specifically for a future approved change to `system_config_shared.yaml` (**I do not edit it**): tank/collector/pump/safety/shield/solver values invalidate everything from Phase 3 downward for all four states; `delivery.target_temp_C` additionally invalidates `retarget_tm` and the shortlist; `pcm_integration` invalidates Phase-3 onward; `design_bounds_shared.yaml` invalidates Phases 5–8; `states/<state>.yaml` invalidates only that state from the phase it affects.
**Acceptance [P].** A one-command, per-state run reproduces a stored hash-stamped result; state differences confined to files under `configs/states/` and `data/`.
**Risks.** Merging four diverged code bases; fallback = migrate Rajasthan first, then diff-based port.
**Effort.** 3 weeks. **Guide decisions.** Scope of each state in the paper; whether Uttarakhand's 5 regimes are in scope; whether to unify the shield/config versions across states.

### WP8 — Validation, baselines and ablation

**Validation plan [P].**
1. *Analytical energy-balance and numerical checks:* Gate-1 style residual on repaired model; Δt halving; mesh-free.
2. *PCM vs water-only baseline under equal conditions:* paired by weather year.
3. *Comparison with existing O2 designs:* re-evaluate the current deployable designs under the repaired model/metrics.
4. *Literature benchmarks:* Chen Table 10 retention (17.13 vs 18.33 h simulated) as a trend check; Avargani 300 L @ 60 ± 2 °C/7 h only as a demand-scale reference (concentrating collector).
5. *CFD comparison:* only for capsule closure and the tank draw case, after boundary-condition matching.
6. *Held-out weather years and regimes* (WP4).
7. *Repeated optimisation runs* (≥ 3 seeds).
8. *Sensitivity:* k, L, ρ ±10 %, μ/β from CFD sensitivity (±12 %), liquid-convection factor, mains temperature ±2 K, demand ±20 %, shield on/off.
9. *Boundary checks:* geometry, packing, flow, safety.
10. *Runtime:* record seconds per year-run and total laptop hours.
11. *Surrogate/optimiser checks (WP5):* held-out designs, leave-one-year-out, within-regime RMSE and Spearman rank, NN vs XGBoost vs quadratic RSM, NSGA-II front vs dense-grid front, 3 seeds.
12. *CFD tier (WP2-C):* OpenFOAM vs ANSYS Fluent code-to-code check on 8–12 capsule cases with mesh/time-step independence and GCI; closure-uncertainty runs of the simulator (closure low/high); design-point spot-checks; stratified-tank draw-off check against the OpenFOAM tank case. These are *verification* unless a compatible experiment is found.
**Ablation experiments [P]** — each uses the same baseline design, fixed weather-years and PCM; report paired differences with uncertainty:

| Variable | Baseline design | Change | Held fixed | Conditions | Expected evidence | Interpretation if no effect |
|---|---|---|---|---|---|---|
| Thickness | mid-range design | inner radius 10–40 mm in ≥ 5 steps with **N ∝ R⁻³ so PCM mass is constant** | arrangement, flow, PCM, mass, weather | all weather-years, night-hold scenario | change in τ_serve/E_del,45 and latent utilisation (LU rises as R falls if conduction-limited) | The sphere closure is not limiting (consistent with CFD φ result) → thickness is a mass/packing choice, not a heat-transfer one |
| Count | mid-range design | N 8…max fit at **fixed radius** (PCM mass varies) | others | same | gain vs PCM fraction (expect the sweep's rise then decline); compare with mass-matched run | Mass-driven effect only; report PCM fraction as the real variable |
| Flow | mid-range design | 0.010, 0.020, 0.030, 0.050 kg/s | others; collector model on/off F_R(flow) | same | change in UA, f_melt cycling, T_pcm,max | Model-structural: flow acts only through h_w (§3.3) → say so; do not call it optimised |
| Arrangement | mid-range design | the three arrangements, *after* WP2 Level 2 (vertical distribution) | N, radius, flow | night-hold scenario | change in delivery temperature profile and E_del,45 | In the current mixed-node model the result is *zero by construction*; in the stratified model any effect is physical — report both |

Each ablation also reports a **negative control** (N = 0 baseline) and a **positive control** (a deliberately extreme design, e.g. 20 % loading) to demonstrate the harness can detect an effect.
**Acceptance [P].** For every variable, either a detected effect larger than the WP6 equivalence band, or a documented null with the structural reason; no ablation changes more than one factor.
**Effort.** 2.5 weeks. **Guide decisions.** Which benchmarks count as "compatible"; sensitivity ranges.

### WP9 — Reporting, reproducibility and Objective-3 hand-off **[A: WP9 text missing from the brief; this is my proposal]**

**Purpose.** Produce the paper-ready outputs and keep downstream work consistent.
**Method.** (i) Single results registry (hash-stamped CSVs, config versions, seeds); (ii) rewrite the stale docs (05–09, audit report) from the new results or mark them superseded; (iii) restate the O3 motivation — O1's material choice is seasonally robust (CLAUDE.md §3.4), O3 addresses hour-by-hour operation — and regenerate the O3 environment contract (`obj3_environment_contract_*.json`) after the model changes; (iv) honest-limitation section: no experimental validation; fixed non-standard sizing; CFD uncalibrated against measurements; (v) paper tables: per regime baseline vs design, mean/worst-year, uncertainty, ablation outcomes.
**Title used (inferred, needs your confirmation):** "Reporting, reproducibility and guide hand-off".
**Risk register [P].** (R1) Timing fix changes all baselines → rerun everything (mitigation: fix first, WP7 order). (R2) Fixed sizing caps benefit → report capacity ceiling and a labelled diagnostic, not a hidden retune. (R3) Stratified model slips → fallback Level 1 plus honest null result. (R4) Hourly data missing for some points/years → medoid × 10 years. (R5) Shortlist decision delayed → run both lists, label clearly. (R6) Another fabricated-number incident → every number in the paper must cite a file path and a script run ID. (R7) Four diverged code bases → port Rajasthan first.
**Schedule roll-up [P].** Effort table above (21 student-weeks, about 14–15 calendar weeks with overlap); critical path as stated. These are estimates, not commitments.
**Hand-off package for Dr. T. Deepika.** The consolidated questions in §6, the label legend, the list of unread papers (§2.4), and the stale-artifact list (WP7).
**Acceptance [P].** Every number in the paper traces to a file and commit; contradictions between docs eliminated.
**Effort.** 1.5 weeks.

### Effort summary (estimates [P])

| WP | Weeks | WP | Weeks |
|---|---|---|---|
| 1 | 1.5 | 6 | 1.5 |
| 2 | 6.5 (5.0 + 1.5 CFD tier) | 7 | 3.0 |
| 3 | 1.5 | 8 | 2.5 |
| 4 | 2.0 | 9 | 1.5 |
| 5 | 4.0 | **Total** | **24.0 (≈ 16–17 calendar weeks with overlap; WP1/3/4 and the CFD tier partly parallel)** |

Critical path: confirm timing fix → WP2 Level 1 → WP1 → WP4 → WP5 → WP6 → WP8 → WP9; WP7 starts once WP2 Level 1 lands.

---

## 6. Questions requiring the guide's decision (consolidated)

> Update 2026-10-26: items 1, 2 and 4 were answered by the user (below). Consequences: the Tm retargeting must be redone/retired, the shortlist-override finding (headline #3) is now a fix, and WP2 Level 2 is in scope (adds to the 5-week WP2 estimate; no re-estimate yet).

1. **Demand timing — DECIDED (user, 2026-10-26): the 07:00/19:00 profile is local time.** The UTC indexing is therefore a confirmed bug; fix it first (affects every reported number in every state).
2. **PCM shortlist — DECIDED (user, 2026-10-26): O2 uses Objective 1's MCDM top-3 as written.** The retargeted lists from `retarget_tm.py` are retired from the main pipeline (kept only as a labelled comparison); Phase 4 verification must be rerun on the O1 PCMs.
3. **Shape family — DECIDED (user, 2026-10-26): PCM capsules, taken as spheres with thickness = inner radius** (WP2 option 1). Tube capsules are dropped.
4. **Model fidelity — DECIDED (user, 2026-10-26): the 1-D stratified multi-node tank (WP2 Level 2) is approved.**
5. **Primary objective and retention definition** (WP1).
6. **Sizing:** the fixed 50 L / 1.5 m² / 300 L/day violates IS 12976:2023 guidance; how to present this; permission to run *labelled non-authoritative* sizing diagnostics.
7. **Shared-config unification:** Rajasthan v1.1 has the safety shield; the other three states do not.
8. **Weather split — DECIDED (user, 2026-10-26): Option A.** 2016–2020 explore designs, 2021–2023 pick the winner, 2024–2025 are the held-out test (the two lowest-GHI years, so the test is harsher than average; state this in the paper). **Member points — DECIDED (user, 2026-10-26, as I read it): one simulation set per Objective 1 cluster (regime), using that cluster's Objective 1 representative point over the 10 years; extra member points are not simulated.** Assumption to confirm: 'representative point' = the Objective 1 medoid, taken from the *current* assignments, not the stale `medoid_points_rajasthan.csv`. **Still open:** missing-data threshold.
9. **Practical-relevance threshold** for "meaningful improvement" and tie-breaker order.
10. **Scope of states** in the paper (Uttarakhand's 5 regimes; Assam currently failing the 65 °C limit).
11. **Original text of WP9.**

## 6A. Decision log — remaining open items settled (user, 2026-10-26)

Direction given: this is a research project; show the possibility and positive side of the PCM design. I have made each decision below to do that **without hiding results**: favourable framing comes from choosing metrics and conditions where a PCM is meant to help, and from reporting honestly where it does not. All of these are **proposed engineering decisions [P]**, adopted at the user's instruction; the guide may still revise them.

**Rule that applies to every decision (non-negotiable):** every run, regime, state, weather-year and metric is reported, including the ones where PCM gives no benefit. No run is dropped, no year or regime is cherry-picked, and the fixed parameters (tank, collector, demand, O1 shortlist) are not tuned to favour PCM. "Positive" means leading with the metrics and windows where PCM acts (night/morning delivery above 45 °C, temperature stability, overheat damping, worst-year behaviour) and stating plainly that annual energy gain is small within the fixed sizing.

1. **Missing-data threshold.** A point-year is accepted if at least 98 % of its hours are valid. Gaps of up to 3 consecutive hours are filled by linear interpolation and flagged; longer gaps reject that point-year (it is listed, not silently dropped). A gap table per point-year is an artifact (WP4).
2. **Safety shield.** Kept **ON as the default for all four states** (it is in Rajasthan's v1.1 config only today; Tamil Nadu, Assam and Uttarakhand must adopt it so results are comparable). Basis: IS 12976:2023 §8.2 (stop circulation to prevent overheating). Shield-off runs are reported as a sensitivity case. This also addresses Assam's current failure (all three deployable PCM designs exceed the 65 °C limit without a shield).
3. **IS 12976 disclosure.** Stated openly in the limitations: the fixed 50 L / 1.5 m² (33.3 L/m²) is below the standard's 40–100 L/m² and its 1.5–2× daily-use guidance. It is presented as a **deliberately small-tank, conservative case**; the paper's claim is "PCM benefit under a compact tank". In addition, a clearly labelled **supplementary sizing-sensitivity study** (in-memory overrides, frozen files untouched, never an optimisation variable) tests whether the PCM benefit grows toward the standard's range. This is a hypothesis to be tested, not an assumed result; whatever it shows is reported.
4. **Practical-relevance threshold.** Not a fixed percent. A design counts as better than water-only when its paired multi-year gain exceeds the repeatability band derived in WP6 (weather-year spread, time-step error, property sensitivity) on **at least one primary metric**. The primary metric set is the WP1 night-and-morning delivery metrics (E_del,45 in the 18:00–09:00 window, τ_serve, delivery-temperature stability), with annual energy as a secondary metric. Reason: these are the functions a PCM store is for; annual energy is reported but not used as the only judge.
5. **Tie-breaker order.** (a) lower overheating/shield-activation hours, (b) higher night delivery (τ_serve), (c) lower PCM mass, (d) fewer capsules, (e) larger safety margin to 65 °C. Ties inside the band are reported as "indistinguishable", not as a win.
6. **States in scope: all four** — Rajasthan (3 regimes), Tamil Nadu (3), Assam (3), Uttarakhand (5 regimes). WP7's per-state port order: Rajasthan first, then Tamil Nadu, Assam, Uttarakhand.
7. **WP9 original text.** Not supplied in the brief, so WP9 stays as the inferred "Reporting, reproducibility and guide hand-off" (§5). It is still marked inferred; replace it if you paste the original.

8. **Optimisation algorithm — Option B (user, 2026-10-26):** neural-network-ensemble surrogate + NSGA-II with active learning; designed-experiment screening first; dense-grid check; GP Bayesian optimisation and XGBoost/RSM kept as comparisons (WP5).
9. **CFD tools (user, 2026-10-26):** OpenFOAM and ANSYS Fluent are used **only for calibration, cross-checking and spot-checks**, never inside the optimisation loop (WP2-C). OpenFOAM is the primary engine (already built); Fluent repeats a subset. Both are *verification* tools until compared with compatible measurements.

**Effect on earlier sections:** §6 items 5, 6, 7, 9 and 10 are now answered by this log; WP3's "how to disclose the IS 12976 non-compliance" and WP6 items 5–8 follow items 3–5 here; WP7's "scope" and "unify shield" questions are answered by items 2 and 6.

## 7. Assumptions I made that you should confirm **[A]**

- Hot-water draw hours in `demand_profile_*.csv` are local clock hours (from `build_demand_profile.py` docstring).
- Local time = UTC + 5 to + 5.5 h for all four states (NASA POWER timestamps are UTC; `local_hour` uses Asia/Kolkata).
- The brief's list of 12 claims is exhaustive for the "existing audit".
- Hourly NASA POWER resolution for all 320 points; I counted files (3,200) but did not open them.

## 8. What I did not do

- I did not change any repo file, rerun any pipeline stage that writes results, install anything, or open OpenFOAM.
- All of my "re-runs" used the repo's functions read-only from a scratch script (outside the repo) with bytecode writing disabled.
- I did not run, install or license-check ANSYS Fluent; everything said about Fluent in this plan comes from Yan 2025 (read in part) and a keyword scan of Abdellatif 2025. Student-licence cell limits are **not** taken from any source I opened and must be checked.
- I did not train any neural network or run NSGA-II; every size, budget and setting in WP5 is a proposal, and the multi-node simulator runtime is unmeasured.
- I did not read the 18 summary-only papers, Nems 2025, the full Kou or Barqawi papers, or Eldokaishi's PDF.
- I did not test time-step sensitivity, the real PCM supercooling/volume-change effect, or any CFD case.
- I did not verify Tamil Nadu, Assam or Uttarakhand code beyond the files named above (bounds, geometry arrangements, config diff, weather years, one results table).
