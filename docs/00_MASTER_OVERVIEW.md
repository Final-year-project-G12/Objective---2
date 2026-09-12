# 00 — Objective 2 Master Overview (All Four States: Tamil Nadu, Rajasthan, Assam, Uttarakhand)

## What this covers

This is the **cross-state companion** to each state's own
`objective2-<state>/docs*/00_MASTER_OVERVIEW.md`. It does not replace
those — it exists so a reader (or the guide, or Objective 3) can see, in
one place, what Phase 1–8 actually produced in every state, without
opening four separate repos. Every number below is read from that
state's own audited docs/results, not re-derived here. Naming mirrors
the per-state `docs_objective2/` convention (`00`…`11` + `OBJECTIVE3_…`)
so the two trees stay easy to cross-reference.

Objective 2 turns Objective 1's output — climate regimes + a shortlisted
PCM per regime — into a **physical PCM-storage design and a validated
simulator** that Objective 3 builds a controller against, following one
shared ~40-hour per-state execution plan
(`O2_Unified_PerState_Execution_Framework.md`) applied to four Indian
climates.

## Phase completion matrix

| Phase | Tamil Nadu | Rajasthan | Assam | Uttarakhand |
|---|---|---|---|---|
| 0 — Objective 1 freeze + climate-signature check | COMPLETE | COMPLETE (PASSED 3/3) | Embedded in `assam.yaml`, PASSED (no standalone report file) | NOT independently verified (config self-flags this — RH_mean was never captured at config-write time) |
| 1 — Frozen state config | COMPLETE | COMPLETE | COMPLETE | COMPLETE |
| 2 — Geometry & constraint engine | COMPLETE (state-agnostic) | COMPLETE (state-agnostic) | COMPLETE (state-agnostic) | COMPLETE (state-agnostic) |
| 3 — Grey-box enthalpy simulator | COMPLETE | COMPLETE | COMPLETE (no standalone smoke-run JSON saved) | COMPLETE |
| 4 — Verification Gates 1–5 | GO, 4/5 clean (Gate 4 caveat) | GO, **5/5 clean** | GO, **4/5 clean (Gate 3 fails)** | GO, 4/5 clean (Gate 4 caveat) |
| 5 — DOE | COMPLETE — 215 cases, 145 valid | COMPLETE — 165 cases, 111 valid | COMPLETE — 165 cases, 111 valid | COMPLETE — 215 cases, 145 valid |
| 6 — Surrogate | COMPLETE, R² ≥ 0.98 | COMPLETE, R² = 0.9998 (useful energy) | COMPLETE, R² = 0.9977 (useful energy) | COMPLETE, R² > 0.9998 |
| 6b — Multi-fidelity augmentation | COMPLETE (1.53× speedup) | not run | not run | doc written, **not actually run** (numbers are TN's, projected) |
| 7 — Optimization + simulator confirmation | COMPLETE — plain tank in 4/5 regimes | COMPLETE — plain tank in **3/3** regimes | Run via a **bespoke script**, reported "PASS" — **verdict is wrong**, see caveat below | COMPLETE — plain tank in 4/5 regimes |
| 8 — Robustness + handoff | COMPLETE — 120 draws/design, real 10-yr weather ensemble | COMPLETE — 120 draws/design, synthetic weather noise | **NOT RUN** — no results files, no contract | COMPLETE — 120 draws/design, real 10-yr weather ensemble |

**Read before citing any Assam Phase 7 number**: `scripts/run_phase7_optimization.py`
computes the correct margin against the frozen 65 °C PCM / 75 °C water
limits, then the report template prints a hardcoded "PASSED" against an
unrelated 90 °C/95 °C threshold instead of checking that margin. All 3
of Assam's selected designs actually exceed 65 °C (margins −1.2 to
−5.1 °C). See `objective2-assam/docs/07_PHASE7_OPTIMIZATION.md`, "The
safety-verdict bug." Assam's Phase 8 was never run partly because of
this open issue.

## Regimes, PCM shortlists, and demand per state

| State | K (regimes) | Demand (L/day) | Mains temp range (°C) | PCM shortlist provenance |
|---|---|---|---|---|
| Tamil Nadu | 5 | 300 | 24.0–26.0 | Objective 1 MCDM Top-3; `n-Octacosane (C28)` consensus rank-1 in every cluster |
| Rajasthan | 3 | 300 | 18–30 (24.5–25.8 point est.) | Objective 1 MCDM Top-3; `RT50`/`RT45HC`/Lauric acid (C0), `savE® OM50`/Paraffin-HDPE PCM3/PCM6 (C1–2) |
| Assam | 3 | **100** (50 morning + 50 evening) | 15–28 (16.6–19.9 point est.) | **Not** a standard MCDM Top-3 — Objective 1's confirmed-feasible K=3 MCDM ranking returned zero candidates; shortlist is Objective 1's Phase 9/10 physics-validated substitute (`savE® OM48/OM50/OM46` in every regime) |
| Uttarakhand | 5 | 300 | 7.4–21.8 | Objective 1 MCDM Top-3; `PureTemp 58` rank-1 in every cluster |

Tamil Nadu, Rajasthan, and Uttarakhand's demand and mains-temperature
inputs make their absolute energy numbers roughly comparable to each
other; **Assam's 100 L/day demand is 1/3 of the other three states'**,
so its ~650–710 kWh/year useful-energy figures are not directly
comparable without rescaling — a fact any four-state comparison chapter
must state.

## Cross-state headline: does the shortlisted PCM ever beat plain water?

| State | Regimes where PCM was selected | Regimes where plain tank was selected | Best PCM's nominal edge over best plain tank |
|---|---|---|---|
| Tamil Nadu | 1 / 5 (regime 4, `n-Octacosane`) | 4 / 5 | +0.07–0.08% (all regimes, PCM measurably better but inside the 5% tolerance) |
| Rajasthan | 0 / 3 | 3 / 3 | +0.07–0.15%, but **0/45 PCM candidates pass the 65 °C safety filter** — plain tank wins on safety, not just tolerance |
| Assam | **3 / 3** (reported) — but **unvalidated**, see caveat above | 0 / 3 (as reported; likely different once the safety filter is corrected) | Not meaningfully comparable — Assam's "wins" all breach the PCM temperature limit |
| Uttarakhand | 1 / 5 (regime 2, `PureTemp 58`, the coldest/highest-`L_required` regime) | 4 / 5 | Regime 2's PCM wins outright (exceeds the regime's own plain-tank optimum) |

**The consistent finding across the three properly-validated states
(Tamil Nadu, Rajasthan, Uttarakhand)**: within the frozen 50 L /
1.5 m²-collector / ≤12.9%-PCM-volume-fraction design space, Objective
1's climate-ranked PCM shortlist earns its mass in **at most 1 regime
per state**, and only where the climate is cold enough (or, in
Rajasthan's case, never) to keep the tank inside the PCM's actual
operating range without overheating. This is not a simulator defect —
Gate 3's synthetic matched-Tm-PCM capability check independently confirms
the physics rewards a well-matched PCM in Tamil Nadu and Uttarakhand
(it does *not* in Assam, a further warning sign for that state's Phase 7
result). See `08_PHASE7_OPTIMIZATION.md` for the full method and
`09_NEXT_STEPS.md` for the design decision this raises for every state.

## Cross-state headline: robustness (Phase 8)

| State | P(meets demand) range | P(temp-safe) range | Any regime "robust" (both ≥ target)? |
|---|---|---|---|
| Tamil Nadu | 69.2–95.0% | 40.8–92.5% | No — PCM regime (4) fails both bars at once |
| Rajasthan | 80.0–99.2% | 45.0–56.7% | No — every regime fails temperature safety by a wide margin |
| Assam | Not run | Not run | N/A — Phase 8 never executed |
| Uttarakhand | **0.0%, every regime** | 44.2–100.0% | No — demand bar structurally unreachable at this climate/hardware combination; regime 2 (PCM) is the *only* one that is temperature-safe |

**No state, in any regime, has a design that clears both the 75%
demand-reliability bar and the 95% temperature-safety bar** under the
framework's fixed, cross-state-comparable thresholds. Every state's
Phase 8 independently concludes that an active high-temperature bypass
is a first-class Objective 3 requirement, not an optimization nicety —
see `10_PHASE8_ROBUSTNESS_HANDOFF.md`.

## What differs state-to-state at the code level (and what doesn't)

`src/design/`, `src/simulation/`, and `src/doe/generate_cases.py` are
**byte-identical across Tamil Nadu, Rajasthan, and Uttarakhand** (Assam
was not diffed directly in this pass, but its Phase 4 Gate reports show
the same submodels and bug-fix behavior). Only `configs/states/<state>.yaml`,
the weather/demand/PCM data under `data/`, and a few output-path/tag
constants vary. The one genuine methodological divergence is **Phase 7
for Assam**, which used a bespoke `scripts/run_phase7_optimization.py`
(1,000 candidates/pair, a "5% Near-Best Rule" + 6-tier tie-break) instead
of the shared `src/optimize/search.py` + `select_deployable.py` (400
candidates/pair, a simpler `pareto_tolerance_pct` rule) the other three
states used — this is also where the safety-verdict bug was introduced.

## Literature review — why this overall design

The shared execution framework (collector/tank sizing, safety limits,
solver family, Pareto-tolerance selection rule) is grounded in the
project's PCM-SWH literature base, not invented per state:

- **Collector and tank sizing** (1.5 m² FPC, 50 L tank, H:D = 2:1,
  direct-encapsulation PCM) follows the domestic flat-plate-collector
  baseline in Singh et al. (2025) and the tank proportions in Chen et al.
  (2025, Table 1) — both comprehensive, recent (2025) reviews/experiments
  specifically on PCM-SWH systems (`Singh2025PCMSWH`,
  `Chen2025TaguchiGRAPCM`).
- **The 300 L/day (100 L/day for Assam) night-draw demand convention**
  follows Madadi Avargani et al. (2021)'s PCM-tank hot-water-output study
  (`MADADIAVARGANI2021101350`), the paper this project's demand-volume
  assumption is explicitly built on (see `03_PHASE3_GREYBOX_SIMULATOR.md`).
- **Reporting a Gate-4 published-benchmark mismatch honestly, rather than
  tuning the model to match it**, follows the same Singh et al. (2025)
  solar-fraction band as the calibration reference, cross-checked against
  Chen et al. (2025)'s reported 94.2% storage efficiency / 31.7 h
  retention as a second, independent calibration point.
- **Treating the surrogate as a proposal ranker, never the final oracle**
  (every design re-confirmed in the real simulator before being reported)
  reflects the same caution Barqawi et al. (2025) and Assareh et al.
  (2023) raise about ML-only PCM-SWH optimization pipelines that never
  validate against the underlying physics (`Barqawi2025MLPCMSWH`,
  `Barqawi2025PCMSim`, `Assareh2023ML_PCM_SolarCollector`).
- **Doing a Monte Carlo robustness pass at all, rather than reporting only
  nominal performance**, follows the same reasoning as Chopra et al.
  (2023)'s Monte Carlo techno-economic assessment of a solar
  collector-storage system (`Chopra2023MonteCarloETC`) — a design's
  nominal performance is a poor proxy for its real-world reliability.

See `docs/METHODS.md` for the full per-method justification (grey-box
simulator equations, GMM clustering carried over from Objective 1, DOE
sampling, ExtraTrees surrogate, optimization/selection rule, and
Monte-Carlo robustness), each tied to a specific citation in
`../../references.bib`.

## Documents in this folder

- `01_PHASE1_CONFIG_AND_STATE_SETUP.md` — the 4 frozen state configs side by side
- `02_PHASE2_GEOMETRY_CONSTRAINTS.md` — the shared geometry engine and the 12.9%-not-20% finding
- `03_PHASE3_GREYBOX_SIMULATOR.md` — the shared simulator, its bug-fix history, and per-state smoke numbers
- `04_PHASE4_VERIFICATION_GATES.md` — all 4 states' Gate 1–5 verdicts side by side
- `06_PHASE5_DOE.md` — all 4 states' DOE sampling plans and results
- `07_PHASE6_SURROGATE.md` — all 4 states' surrogate accuracy
- `08_PHASE7_OPTIMIZATION.md` — all 4 states' optimization results, including Assam's safety-verdict bug
- `09_NEXT_STEPS.md` — the PCM-design decision every state's team faces
- `10_PHASE8_ROBUSTNESS_HANDOFF.md` — all 4 states' robustness tables and hand-off status
- `11_MULTIFIDELITY_SURROGATE.md` — Phase 6b, run only for Tamil Nadu
- `OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` — the cross-state Objective 3 hand-off status
- `METHODS.md` — per-method justification with literature citations
- `../../references.bib` — the project bibliography (updated this pass with the physics/ML method citations these docs cite)
