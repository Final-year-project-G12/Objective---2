# O2 Implementation Plan — Free Simulators (24–25 Sep 2026)

**Objective 2:** optimal PCM thickness, capsule arrangement, capsule count and flow rate for a climate-specific SWH.
**Inputs reviewed:** `PROJECT SUMMARY.md`, `CLAUDE.md`, the O2 survey, `O2_Unified_PerState_Execution_Framework.md`, `Objective2 Consolidated plan.md`, the Rajasthan fix plan, `docs/00–09` (Rajasthan) and `docs/METHODS.md`, `docs/11`, `O2_O3_COMPREHENSIVE_AUDIT_REPORT.md`, the simulator source (`heat_transfer.py`, `hydraulic_model.py`, `geometry.py`, configs), and the paper extracts/PDFs in `.claude/Sources/`.

---

## 1. Decision (short version)

| Role | Tool | Why |
|---|---|---|
| **Primary simulator (generates all DOE data)** | **Existing Python grey-box model** (`objective2-rajasthan/src/simulation/`) | Free, already passes 5 gates (residual ≈ 6e-4 %), same method class as Barqawi 2025 (SciPy) and Eldokaishi 2022 (Python script). Nothing free is faster or better matched to a 165–350-case DOE. |
| **Independent cross-check** | **OpenTerrace** (separate Python 3.12 env) | Only free, pip-installable, packed-bed tool that runs from Python. Validates the melting/heat-transfer core against a second code. |
| **Arrangement calibration** | **Ansys Student (Fluent)** — *conditional, see Gate G0* | Native on Windows. Only worth running if G0 shows arrangement could change the answer (it currently does not). Fallback: OpenFOAM via WSL2. |
| **Baseline sanity** | NREL SAM (optional) | Plain-tank solar fraction per state; no PCM. |
| Dropped | OpenModelica/Buildings, EnergyPlus, TRNSYS/COMSOL/MATLAB | Modelica: no PCM-capsule component, high effort, no O2 payoff. EnergyPlus already rejected (O1 Plan §10.1). Paid tools only if the lab has a licence. |

**"Best free option" = keep the Python grey-box as the engine and add OpenTerrace as the second opinion.** CFD is held back until a gate says it can matter.

---

## 2. What the review found (this changes the plan)

### 2.1 Arrangement cannot change the thermal answer — measured, not assumed
`docs/03` already shows arrangement enters only through void fraction → pump power (useful energy bit-for-bit identical). The survey's proposed fix is a CFD "arrangement multiplier on h". I tested whether that could help by scaling the water-side coefficient `h_w` over a 16× range (0.25×–4×) in the real simulator (Rajasthan, d = 0.06 m, N = 30, staggered, shield on):

| Regime / PCM | useful energy at h×0.25 | h×1 | h×4 | swing |
|---|---|---|---|---|
| Cluster 0 / Palmitic-stearic acid–EG | 1582.13 kWh | 1582.90 | 1583.10 | **0.061 %** |
| Cluster 1 / PureTemp 60 | 1839.29 kWh | 1840.08 | 1840.31 | **0.055 %** |

(Script: `scratchpad/hsens.py`, single design point, two clusters — indicative, re-run in Stage 0.) A realistic CFD arrangement factor is ±20–40 %, so it would move useful energy by **< 0.02 %**, far inside the 0.04 % noise band the pipeline already uses. Heat transfer to the capsules is not the bottleneck; the bottleneck is that PCM is ≤ 3 % of a 50 L tank and adds ~0.07 % over plain water.

### 2.2 Project state that constrains any simulator work
- Loading sweep (`docs/09 §11`): PCM helps only below ~2.5–3 % volume; worse above. Winners hold 0.6–3 % PCM.
- IS 12976:2023 (`docs/09 §7`): frozen 50 L / 1.5 m² = 33 L/m² is below the standard's 40–100 L/m² range; 112.5 L makes all PCMs pass safety and beat plain tank. **Frozen shared config not yet changed** (all 4 states would re-run from DOE).
- Fix plan (2026-09-20) steps 4, 7, 8 are open: Tm re-target not run; clean re-run not done; docs stale.
- Only Rajasthan has the arrangement change; TN/Assam/Uttarakhand configs diverge.
- Delivery target: O1 = 60 °C, O2 = 45 °C (documented divergence).

### 2.3 Corrections to the survey
| Survey statement | Finding |
|---|---|
| OpenTerrace "GPL-3.0" | GitHub says GPL-3.0; PyPI metadata says MIT. Check the repo `LICENSE` before citing. Either is fine for academic use. |
| OpenTerrace `pip install` works | **Not in the project env.** PyPI: needs Python ≥ 3.11.8, `numpy<2`, `numba<0.60`. Project venv is Python 3.10 with numpy 2.2.6 → install fails. Python 3.12 is installed on this machine: use a separate venv. |
| Ansys Student "4 cores" | A 2026 search gave 1 M cells and **16 cores**. Confirm on your install. |
| Chen 2025 TRNSYS; Yan 2025 Fluent; Barqawi `solve_ivp`; Eldokaishi Python script; Assareh MATLAB; Avargani COMSOL | **Verified** against extracts/PDFs. |
| Li 2020 "MATLAB + TRNSYS 17" | MATLAB + TRNSYS verified; that system is an **outdoor swimming pool** heater, not an SWH tank. Cite as method precedent only. |
| Eldokaishi "then an ANN" | Python script generates cases; the ANN is trained in MATLAB's toolbox. |
| OpenTerrace covers PCM | README says PCM can be plugged in as an extension module. **Unverified that latent-heat particles work out of the box** → Stage 2 spike. |
| OpenTerrace models our system | It models a **flow-through packed bed**. Our tank has capsules immersed in a mixed tank (single-node water). Like-for-like only for the bed itself; see Stage 2. |

---

## 3. Stages and gates

Work in the Rajasthan copy first (pilot state), branch per stage. **Rule: nothing below edits `system_config_shared.yaml` / `design_bounds_shared.yaml`; use in-memory overrides** (`system_config_overrides`, same seam as the existing `check_*.py` scripts).

### Stage 0 — Freeze the baseline and re-measure sensitivity (0.5 day)
1. Finish fix-plan steps 4, 7 (Tm re-target, one clean Phase 2→8 re-run, byte-identical rerun check). This is the reference all simulators are compared to.
2. Promote `hsens.py` into `scripts/sweep_htc_sensitivity.py`: 3 regimes × 3 arrangements × 3 designs (low/mid/high loading) × h scale {0.25, 0.5, 1, 2, 4}. Output `results/g0_htc_sensitivity.csv`.
3. **Gate G0:** if max swing in useful energy over the plausible CFD range (0.7×–1.4×) is **< 0.04 %** (the pipeline's noise band), **skip Stage 3** and report arrangement as "not decisive; tested" with this table as evidence.

### Stage 1 — Make the design problem able to discriminate (1–2 days) — needs your decision
Simulator fidelity is not the limiting factor (§2.1). Decide one of:
- **A (recommended):** run the DOE under IS 12976 sizing (112.5 L / 1.5 m²) as an in-memory override for a full Phase 4→8 pass, alongside the frozen result. Cited, safe, and PCM wins outright (`docs/09 §7`).
- **B:** keep frozen sizing; report O2 as "PCM ≈ plain tank, arrangement non-decisive" — an honest result but a weak O2 story.
- **C:** add a dedicated PCM packed-bed configuration (Avargani-style bed: 55 mm capsules, porosity 0.2–0.5, 0.005–0.15 kg/s) as a second design case where arrangement/flow genuinely matter. Highest scientific value, highest effort; also the case where OpenTerrace applies directly.

Deliverable: `docs/12_STAGE1_DESIGN_CASE_DECISION.md` recording the choice and its cost (per fix-plan rule, a shared-config change means all 4 states re-run).

### Stage 2 — OpenTerrace cross-check (2–3 days)
1. **Env:** `py -3.12 -m venv .venv-ot` → `pip install openterrace` (pins numpy<2). Keep it out of the main venv.
2. **Spike (½ day, go/no-go):** reproduce one packaged OpenTerrace example; then set up a sphere bed with a custom PCM substance (enthalpy–temperature curve from `pcm_database_rajasthan.csv`) and confirm it melts and conserves energy. If latent heat is not supported without patching core code, **stop and fall back** to the alternative below.
3. **Matched cases (8–10):** same PCM, capsule diameter, count/bed fraction, flow, inlet-temperature history. Use a **charge/discharge test on the bed alone** (constant hot inlet, then cold inlet), and run the same in the grey-box with the tank replaced by a fixed-temperature source. This isolates the melting/heat-transfer core; do not compare full-year tank results.
4. **Metrics:** time-to-50 %/90 % melt, stored energy vs time, outlet temperature curve. Report Spearman ρ of trends (diameter, flow, N) and % difference in absolute values. Suggested pass: ρ ≥ 0.8 on trends; absolute melt time within ±25 % (state the figure before running).
5. **Fallback if the spike fails:** validate the grey-box against published data instead (Avargani 2021 bed, Bouhal 2018 two-code comparison, Eldokaishi 2022 tank) — no new simulator needed.

Outputs: `scripts/openterrace_crosscheck.py`, `results/xcheck_openterrace.csv`, `docs/13_OPENTERRACE_CROSSCHECK.md`. Frame as trend validation, not as proof of accuracy (neither code is experimentally validated here; `docs/03` says the same of the grey-box).

### Stage 3 — Arrangement calibration in Ansys Student (only if G0 fails; 3–5 days)
Scope it small so the 1 M-cell limit is not an issue:
1. Steady, **no phase change**: isothermal-wall spheres (d = 0.04, 0.06, 0.08 m) in a 2-D slice or small 3-D periodic cell for staggered / in-line (single-layer) / radial-ring layouts, at the 3 flow rates → Nu vs Re per arrangement.
2. Fit `Nu_arr = f_arr · Nu_WK` (Wakao–Kaguei, `heat_transfer.py:49`); store `f_arr` per arrangement in `configs/` as a cited, versioned parameter.
3. Mesh-independence check (2 meshes), report the difference.
4. Re-run Stage 0's sensitivity with the fitted `f_arr` to show the effect size honestly.
5. OpenFOAM (WSL2) only if Ansys licensing/limits block; expect 2–3× the effort.

### Stage 4 — Re-run O2 with the chosen setup (1–2 days compute + writing)
`pipeline.py --state rajasthan --stage doe → surrogate → optimize → robustness → handoff`, DOE 24 LHS/pair as now, arrangement-stratified, ≥ 25 valid cases per cell, seeds pinned. Then:
- SAM plain-tank check per state (fix TN/Uttarakhand Gate-4 band question).
- Extend to TN/Assam/Uttarakhand **only after** Rajasthan passes and shared-config divergences (D4) are resolved; otherwise mark cross-state tables stale.

### Stage 5 — Documentation (1 day)
Update phase docs and cards with final numbers only; add limitations: single-node tank; lumped R_pcm = r/(5k); ×2 convection factor; second-code check is trend-level; arrangement result (decisive or not, with G0 numbers).

---

## 4. Effort and order

| Stage | Days | Blocks |
|---|---|---|
| 0 baseline + G0 | 1 | fix-plan steps 4, 7 |
| 1 decision | 0.5 (+1–2 if A/C) | your choice |
| 2 OpenTerrace | 2–3 | Python 3.12 venv |
| 3 Ansys | 3–5 (skipped if G0 passes) | G0 |
| 4 re-run | 1–2 | 0, 1 |
| 5 docs | 1 | all |
| **Total** | **~6–8 days without CFD; ~10–13 with** | |

## 5. Risks

| Risk | Mitigation |
|---|---|
| OpenTerrace lacks usable PCM support | ½-day spike with an explicit fallback (§Stage 2.5) |
| G0 fails and CFD result is still tiny | Report it; the null result is a finding, not a failure |
| Shared-config change breaks cross-state comparability | Use overrides; declare divergence in `docs/09`; re-run all 4 states only by explicit decision |
| Two-simulator disagreement | Report it, log which physical assumption differs (lumped R_pcm, ×2 convection); do not tune either code to match |
| Fabricated/stale numbers (happened before, `docs/09 §6`) | Every table in the docs must come from a saved results file with a manifest sidecar |

## 6. Decisions needed from you
1. Stage 1: A, B or C (recommendation: **A**, and **C** only if time allows).
2. Confirm Ansys Student is installable on your Windows machine (and its limits), or choose OpenFOAM/WSL2.
3. Threshold for G0 (I used the pipeline's 0.04 % noise band) and for the OpenTerrace agreement (ρ ≥ 0.8, ±25 %).

## 7. Sources
- Local: papers listed in §2.3 (`.claude/Sources/`), `docs/03`, `docs/09 §6–§11`, fix plan, consolidated plan.
- OpenTerrace: [GitHub](https://github.com/OpenTerrace/openterrace-python), [PyPI metadata](https://pypi.org/project/openterrace/) (Python ≥ 3.11.8, numpy<2, numba<0.60).
- Ansys Student limits: [Ansys forum](https://innovationspace.ansys.com/forum/forums/topic/limitations-to-student-license/), [CFDLand](https://cfdland.com/ansys-for-student-free-cfd-software/) (verify on your install).
