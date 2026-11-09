# Objective 2 — Unified Per-State Execution Framework
## Parameterized ~40-Hour Design Optimization Plan (Any State)

**Document Version:** 3.0 (State-Agnostic Unified Framework)  
**Applies to:** Tamil Nadu, Rajasthan, Assam, Uttarakhand — **run identically per state**  
**Scope per state:** ~40 hours (one state, one operator/laptop)  
**Full-project scope:** 4 states × ~40 hrs, coordinated by shared frozen configs  

---

## HOW TO USE THIS DOCUMENT

This is **one framework, run four times** — once per state, by whoever owns that state.

- **You** run this for **your assigned state** (`<STATE>` below = your state).
- **Every reference to `<STATE>`** means: substitute your state name (e.g., `tamil_nadu`, `rajasthan`, `assam`, `uttarakhand`).
- **The shared configs** (`system_config_shared.yaml`, `design_bounds_shared.yaml`) are **frozen once for all four states** — you do NOT modify these; you consume them.
- **Only your state's weather, regime, PCM shortlist, and demand profile change.** Everything else — simulator code, geometry engine, DOE method, surrogate, optimization, selection rule — is identical across all four states.

**Why identical?** So the four states can be **compared fairly** in the final IEEE paper. If Tamil Nadu uses a 50 L tank and Rajasthan uses 60 L, the comparison is meaningless. The scientific claim — *"RT35 wins in Tamil Nadu but RT42 wins in Rajasthan"* — only holds if the methodology is state-invariant [1, §0.1].

**Coordination rule:** One person (or the guide) freezes the shared configs in Phase 0. All four state-operators pull the same frozen files. If a shared config changes mid-project, **all four states re-run from DOE onward** [1, §5.2].

---

## WHAT THIS PLAN IS (AND ISN'T)

**Is:** A scoped MVP producing all 9 deliverables (D2.1–D2.9) [1, §1.2] for one state in ~40 hours, with corners explicitly cut and named so they can be defended honestly in the report.

**Isn't:** The full 12-week / ~480-hour spec. The differences are listed below — put this table in your report's limitations section verbatim; do NOT present the scoped version as the full workflow.

| Full spec [1] | This ~40-hr per-state version |
|---|---|
| 4 states in one integrated study | One state per operator; comparison assembled at the end from four frozen outputs |
| Active-learning loop (iterate until Pareto stops changing) [1, §8] | One DOE round + one optimization pass; simulator-confirm finalists only |
| NSGA-II full multi-objective Pareto [1, §9.3] | Weighted-sum or grid/random search over the surrogate, then simulator-confirm top-N |
| Full Monte Carlo (1000s of draws, 12 uncertainty sources) [1, §11.1] | 100–200 draws, 3–4 dominant sources (PCM latent heat, weather year, demand timing, inlet temp) |
| 5 full verification gates + automated suite [1, §5] | Gates 1–3 scripted; Gate 4 single sanity check; Gate 5 light-touch spot checks |
| Separate feasibility classifier + regressors + ablation [1, §7] | One combined tree-based surrogate (Extra Trees/XGBoost); ablation deferred |
| All Level-B seasonal + member-point robustness [1, §2.2] | Medoid + 1 alternate point if time allows; seasonal cascade deferred |

**Load-bearing — do NOT cut these even under time pressure** [1, §18]:
1. Phase 4 simulator verification (energy conservation + limiting cases).
2. Phase 7 "simulator re-confirms every selected design" (never report a surrogate-only number).
3. The ambient tank-loss term staying active in the simulator (§Phase 3, Bug-Fix 1).

---

## THE 8 BUILT-IN CORRECTIONS (Applied to Every State)

These fixes are baked into the phases below. They came from auditing an earlier draft against the framework [1] and the source literature [2–5]. Every state inherits them.

| # | Fix | Where | Source |
|---|---|---|---|
| 1 | Ambient tank-loss term must be explicit AND validated (was the Objective 1 solar-fraction blow-up failure mode) | Phase 3 + Gate 3 | [1, §4.6] |
| 2 | Demand profile must be explicitly chosen and documented per state, not left ambiguous | Phase 1 + Phase 3 | [1, §3.1] |
| 3 | Any published/audit benchmark used in Gate 4 must carry a formal citation | Phase 4 Gate 4 | [3, §4e] |
| 4 | Quantitative go/no-go thresholds for the simulator (not "fix it before Day 2") | Phase 4 | [1, §5.2] |
| 5 | Explicit rule for large surrogate-vs-simulator error (>15% → trust simulator, log it) | Phase 6 + Phase 7 | [1, §6]; [5, §7] |
| 6 | Concrete Monte Carlo distributions + minimum draw count (never <50) | Phase 8 | [1, §11.1] |
| 7 | Pareto/selection tolerance pre-declared in Phase 1 (not chosen after seeing results) | Phase 1 + Phase 7 | [1, §9.5] |
| 8 | Climate-signature sanity check so you don't silently run the wrong state's weather | Phase 0 | [1, §2] |

---

## CRITICAL DESIGN DECISIONS — FROZEN FOR ALL STATES

From the multi-state framework [1, §3]. **Locked once, consumed by every state. Do not re-optimize.**

| Parameter | Fixed Value | Source / Rationale |
|-----------|-------------|-------------------|
| Collector type & area | Flat-plate, 1.5 m² | Domestic SWH baseline [2, §3]; same for all states |
| Collector optical efficiency | 0.75 | Typical FPC [3] |
| Tank volume | 50 L | Domestic standard; matches Chen et al. [3, Table 1] |
| Tank insulation | 5 cm foam, U = 0.8 W/m²·K | Standard thermal resistance [1, §3.1] |
| PCM integration | Direct encapsulation (not indirect HX) | Simplifies scope; same for all states |
| Capsule wall material | Aluminium | Corrosion-resistant, low cost [1, §3.1] |
| Pump modulation range | 0.010–0.050 kg/s | Domestic pump envelope [1, §3.1] |
| Pump efficiency | 60% | Typical AC pump [1, §3.1] |
| Max safe water temp | 75 °C | Scald prevention [1, §3.1] |
| Max safe PCM temp | 65 °C | Material stability per Rubitherm datasheets [2, Table 2] |
| Max pressure | 3.5 bar | Domestic piping standard [1, §3.1] |
| Delivery temp target | 45 °C | Usable hot water; consistent across states [1, §3.1] |
| Solver | Backward Euler + adaptive sub-stepping | Stable for phase change [4, §4c] |
| Timestep | 300 s (5 min) | Speed/accuracy balance [1, §4.1] |
| Solver tolerance | 1e-6 abs, 1e-9 rel | Stringent energy balance [1, §4.1] |
| Pareto/selection tolerance | 5% of best useful energy | Pre-declared [1, §9.5] |

### What VARIES per state (the only state-specific inputs)

| Input | Source | Example values by state [1, §2] |
|-------|--------|---|
| Medoid + member-point hourly weather | Objective 1 | RJ ~6.0 kWh/m²/d dry; AS ~4.2 humid/cloudy; TN ~4.8 coastal; UK ~4.9 elevation-corrected |
| Climate regimes (2–3 per state) | Objective 1 | Level-A regimes; do not re-cluster |
| PCM shortlist (Top-2/Top-3) | Objective 1 | RJ→RT42/RT50; AS→RT35/RT37; TN→RT35/RT37; UK→RT42/RT45 |
| Mains water temperature | Objective 1 | RJ 18–30 °C; AS 15–28 °C; TN 22–30 °C; UK 12–24 °C |
| Demand profile | Your `demand_profile_<STATE>.csv` | Document the daily total (e.g., 100 L/day standard, or your audited state value) and why |

**Rule:** These five inputs are the ONLY things that differ between states. If you find yourself editing simulator physics, geometry math, or design bounds per state — stop. That breaks the comparison [1, §3].

---

## DESIGN-SPACE BOUNDS — IDENTICAL FOR ALL STATES

From [1, §6.1]. Frozen in `design_bounds_shared.yaml`.

| Variable | Type | Bounds | 40-hr choice | Notes |
|----------|------|--------|--------------|-------|
| PCM thickness (max conduction distance) | Continuous | 0.02–0.10 m | Full range | Paraffin diffusivity timescale [2, §5a] |
| Capsule diameter (sphere) | Continuous | 0.02–0.08 m | Full range | Practical encapsulation [2, §5a] |
| Capsule count (N_capsule) | Integer | 8–24 | Narrow to 12–16 if time-tight | Chen baseline 14 [3] |
| Capsule shape | Categorical | {sphere, cylinder} | **Sphere only** (40-hr) | Simpler volume/area math |
| Capsule arrangement | Categorical | {single-layer, staggered, radial} | **Staggered only** (40-hr) | Common practice [2, Table 1] |
| PCM volume fraction | Continuous (derived) | 10–20% of tank | Test 10/15/20% | Chen audit baseline [3, §3] |
| Flow rate (ṁ) | Continuous | 0.010–0.050 kg/s | Full range | Barqawi precedent [4, §4b] |

**40-hr corner cut (document it):** single shape (sphere) + single arrangement (staggered) reduces the categorical space ~4×. Full spec explores all shape×arrangement combos — note as future work.

**Hypothesis you're testing (the paper's point):** with bounds held identical, the *optimum within those bounds shifts by climate*. Expect capsule count, flow rate, and winning PCM to differ between states even though the search space is the same [1, §12].

---

## FILE / REPO LAYOUT (Per-State, Shared Configs)

```
pcm-climate-framework/
├── config/
│   ├── system_config_shared.yaml     # FROZEN — all states
│   ├── design_bounds_shared.yaml     # FROZEN — all states
│   └── states/
│       └── <STATE>.yaml              # weather path, regime ids, pcm ids, mains temp, demand path
├── data/
│   ├── objective1/<STATE>_regimes.json
│   ├── weather/<STATE>_medoid_hourly.csv
│   ├── weather/<STATE>_member1_hourly.csv   # alternate point (robustness)
│   ├── pcm/pcm_database.json                # shared source of truth
│   └── demand/demand_profile_<STATE>.csv
├── src/                              # ALL universal — no per-state branches
│   ├── pipeline.py                   # entry point: --state <STATE> --stage <stage>
│   ├── design/{geometry.py, constraints.py}
│   ├── simulation/{tank_model.py, capsule_enthalpy.py, heat_transfer.py,
│   │               collector_model.py, hydraulic_model.py, demand_profile.py,
│   │               run_case.py, energy_balance.py}
│   ├── doe/{generate_cases.py, run_batch.py, split_cases.py}
│   ├── surrogate/{features.py, train.py, evaluate.py}
│   ├── optimize/{search.py, select_deployable.py}
│   └── robustness/{monte_carlo.py}
├── results/<STATE>/
│   ├── design_cases.parquet
│   ├── surrogate_metrics.csv
│   ├── optimized_designs.csv
│   ├── robustness_results.csv
│   ├── recommendation_card.md
│   └── obj3_environment_contract_<STATE>.json
└── results/COMPARATIVE_ANALYSIS.md   # assembled once all 4 states finish
```

**Entry point contract:**
```bash
python pipeline.py --state <STATE> --stage geometry
python pipeline.py --state <STATE> --stage doe
python pipeline.py --state <STATE> --stage surrogate
python pipeline.py --state <STATE> --stage optimize
python pipeline.py --state <STATE> --stage robustness
python pipeline.py --state <STATE> --stage handoff
```
`--state` selects only the config/weather/PCM/demand inputs. The code path is identical for every state.

---

# PHASE 0 — Pre-flight & Shared-Config Freeze (0.5–2 hrs)

**Two parts: (A) done once for the whole project; (B) done by every state-operator.**

### 0A. One-time project freeze (whoever owns shared configs)
- [ ] Write & version `system_config_shared.yaml` (collector, tank, PCM integration mode, pump, safety limits, solver, timestep, tolerance, Pareto tolerance = 5%).
- [ ] Write & version `design_bounds_shared.yaml` (thickness, capsule count, shape=sphere, arrangement=staggered, PCM-volume levels, flow range).
- [ ] Guide (Dr. Deepika) approves both. Tag: `config_v1.0_<date>`.
- [ ] Distribute frozen files to all four state-operators.

**Gate:** No state starts Phase 1 until these two files are frozen and shared. A later change = all four states re-run from DOE [1, §5.2].

### 0B. Per-state input confirmation (each operator, your `<STATE>`)
Confirms D2.1 for your state [1, §2]:
- [ ] `data/objective1/<STATE>_regimes.json` exists (≥2 Level-A regimes; do not re-cluster).
- [ ] `data/weather/<STATE>_medoid_hourly.csv` present (hourly GHI, DNI, DHI, T_amb, humidity, wind, pressure).
- [ ] At least one member-point weather file for robustness (else note as future work).
- [ ] PCM shortlist (Top-2/Top-3) with full property records + uncertainty in `pcm_database.json`.
- [ ] `demand_profile_<STATE>.csv` present; **record its daily total and why** (Bug-Fix 2).
- [ ] Mains water temperature range for `<STATE>` recorded in `states/<STATE>.yaml`.
- [ ] All inputs hashed + Objective 1 version recorded (e.g., `o1_v2.3_<STATE>_<hash>`).

### 0B-check. Climate-signature sanity check (Bug-Fix 8) [1, §2]
Confirm the medoid actually looks like YOUR state, not a teammate's:
- [ ] Annual mean GHI in the expected band for `<STATE>` (e.g., RJ high ~6.0; AS ~4.2; TN ~4.8; UK ~4.9 kWh/m²/d).
- [ ] Humidity / temperature-range signature matches (e.g., TN coastal humid >60%; RJ hot-dry low humidity).
- [ ] Elevation field correct (critical for Uttarakhand — the repaired elevation, not flat) [1, §2.2].
- [ ] **If the signature looks like another state → STOP, escalate to Objective 1.** Do not proceed on wrong weather.

**Exit:** D2.1 is frozen for your state. Do not touch it again; an Objective 1 change is a stop-and-rebuild event, not a mid-run patch.

---

# DAY 1 — Phases 1–4 (~19 hrs): Config → Geometry → Simulator → Verify

## Phase 1 — Consume shared config, set state inputs (2 hrs)
**Goal:** `states/<STATE>.yaml` completed and pinned; shared configs consumed unchanged.

- [ ] Load `system_config_shared.yaml` and `design_bounds_shared.yaml` (read-only — you do not edit these).
- [ ] In `states/<STATE>.yaml`, set: weather file paths, regime ids, PCM ids, **mains temperature for `<STATE>`**, **demand profile path + documented daily total** (Bug-Fix 2).
- [ ] Confirm Pareto/selection tolerance = 5% is inherited from shared config (Bug-Fix 7) — do not override.
- [ ] Commit `states/<STATE>.yaml` with tag `state_config_<STATE>_v1.0`.

**Exit check:** Your state config is version-locked and references (not copies) the shared files. Not edited again after Phase 4 begins.

## Phase 2 — Geometry & constraint engine (5 hrs)
**Goal (D2.2):** given a design vector, return volume/area/spacing/pressure-drop + valid/invalid flag with reason. **This code is universal — identical for every state.**

- [ ] Sphere volume `V = (4/3)πr³`, surface area `A = 4πr²` (r = diameter/2).
- [ ] Enforce: `N_capsule·V_capsule ≤ 0.20·V_tank`; `V_tank − N_capsule·V_capsule ≥ V_min_passage`; `spacing ≥ diameter + spacing_min`.
- [ ] Reject with a single reason code: `overlap`, `volume_exceeded`, `passage_blocked`, `pressure_drop_limit`.
- [ ] Compute hydraulic diameter, Reynolds number, pressure drop (standard correlation — do not derive from scratch) [1, §3.2], pump power `P = Δp·Q/η`.
- [ ] Determinism check: same design vector twice → identical output.

**Exit check:** boundary cases (min/max thickness, min/max count) each return a clean valid/invalid + reason, no crashes. ≥50 pre-computed test rows.

## Phase 3 — Grey-box enthalpy simulator core (8 hrs)
**Goal (D2.3):** the physics model — largest, most important phase. **Universal code; only weather/PCM/demand inputs differ by state.**

- [ ] **State vector:** `T_w, T_collector_out, T_pcm[groups], f_melt[groups], H_pcm, T_tank_wall, ṁ, D_t, I_t, T_amb_t`.
- [ ] **Enthalpy model** with clipped liquid fraction `f = clip((H−H_s)/L, 0, 1)` — use the interval, not a binary switch [1, §4.3]. Three-phase structure per Barqawi [4, Eqs 1–16].
- [ ] **Energy balances**, explicit documented sign for `Q_pcm`:
      `m_w c_w dT_w/dt = Q_collector − Q_load − Q_pcm − Q_loss`; `dH_pcm/dt = Q_pcm`.
- [ ] **`UA_eff`** resistance model; document which terms are measured / correlated / assumed [1, §4.5].
- [ ] **Collector submodel** produces zero heat at zero/low irradiance.
- [ ] **⚠️ Ambient tank loss MUST stay active (Bug-Fix 1):** `Q_loss = U_tank·A_tank·(T_w − T_amb)`. Omitting this was the Objective 1 solar-fraction blow-up failure mode [1, §4.6]. This term is non-negotiable.
- [ ] **Pump power** from flow + pressure drop, integrated, reported separately from thermal energy.
- [ ] **Demand** driven from `demand_profile_<STATE>.csv` hourly (Bug-Fix 2) — not a hand-picked number. Track `unmet_energy`.
- [ ] **Solver:** backward Euler with sub-stepping when `f_melt` changes fast; log convergence/residual per step.

**Exit check:** one full case (one design, your medoid weather, one PCM, one year of hourly demand) runs end-to-end; T_w and T_pcm histories are physically plausible on a quick plot.

## Phase 4 — Verification (reduced gates) (4 hrs) — DO NOT SKIP
**Goal:** don't generate a single DOE row until this passes [1, §5]. Same gates for every state.

**Gate 1 — Conservation:** `E_collector + E_initial ≈ E_load + E_loss + E_pump + E_final + E_residual` across ~5 diverse cases.
- Accept: mean residual <0.1%, max <0.5%.

**Gate 2 — Limiting cases:** zero irradiance → no heat; zero flow → no delivery; no PCM/zero latent → plain-tank behaviour; solid vs liquid initial PCM → melt fraction starts/moves correctly.

**Gate 3 — Baseline comparison:** plain tank vs fixed PCM (20%/14) vs one optimized-looking design, same weather/demand → PCM beats plain tank on all metrics. **Also verify the no-loss vs with-loss diagnostic** (Bug-Fix 1): confirm removing ambient loss inflates solar fraction — proving the term is active.

**Gate 4 — Light calibration (Bug-Fix 3):** compare the fixed-PCM run against a **cited** benchmark — e.g., your `<STATE>` phase-audit figure *[cite the actual audit file]*, or Chen's 94.2% storage efficiency / 31.7 h retention on a comparable config [3, §8]. Within a defensible range → note it; if mismatch >15% → report honestly, do NOT tune to match.

**Gate 5 — Sensitivity (light):** 2–3 spot checks (latent heat ±10%, flow ±50%, ambient +5 °C) go the physically correct direction. Full ANOVA deferred.

**Go/No-Go (Bug-Fix 4) [1, §5.2]:**
- Residual <0.1% → proceed.
- 0.1–0.5% → document, proceed only if other gates pass.
- >0.5% or any limiting case unphysical → **STOP and fix before Day 2.**
- Proceed to Phase 5 only when ≥3 of 5 gates pass cleanly.

**Exit:** write `results/<STATE>/simulator_verification_report.txt` with gate status, residuals, caveats. Tag simulator `sim_v1_<STATE>_<date>` (same code across states; the tag records which state's verification run it passed on).

---

# DAY 2 — Phases 5–8 (~19 hrs): DOE → Surrogate → Optimize → Robustness → Cards

## Phase 5 — Reduced DOE (4 hrs)
**Goal (D2.4):** a design-cases table (one row per completed simulation, not per timestep).

- [ ] LHS for continuous vars (thickness, flow, PCM volume fraction); enumerate the small integer set (capsule counts) with fixed shape=sphere, arrangement=staggered.
- [ ] Target ~150–300 cases across your PCM shortlist × your state's regimes. **State the count + sampling method in the report.**
- [ ] Must include: min/max thickness & flow; min/max capsule count; the 10/15/20% PCM-volume baselines; one no-PCM baseline per regime; ≥1 case per shortlisted PCM per regime.
- [ ] **Keep failed/infeasible cases** (with reason codes) — they define the feasibility boundary [1, §6.2].
- [ ] Split by whole `case_id` into 80/20 train/hold-out; note that a proper unseen-weather-year hold-out is future work if not fitted.

**Exit check:** `results/<STATE>/design_cases.parquet` with case_id, regime_id, pcm_id, design vector, geometry outputs, performance outputs, constraint pass/fail — one row per simulation.

## Phase 6 — Surrogate (single model, no ablation) (3.5 hrs)
**Goal (D2.5):** a fast stand-in so optimization doesn't need thousands of physics runs.

- [ ] One family: Extra Trees or XGBoost regressors for key outputs (useful energy, solar fraction, unmet energy at minimum) + optional feasibility classifier if the split is sharp [1, §7.3][5, Table 3].
- [ ] Compare against a linear-regression baseline (cheap, confirms the tree adds value).
- [ ] Report MAE / RMSE / R² on hold-out. Ablation deferred to future work.
- [ ] **Surrogate is a proposal ranker, not the final oracle (Bug-Fix 5):** final numbers always come from the simulator in Phase 7 [1, §6].

**Exit check:** hold-out R² high enough to trust ranking (target >0.80 useful energy). If <0.75, add DOE cases or reduce to a single target.

## Phase 7 — One optimization pass + simulator confirmation (5 hrs)
**Goal (D2.6):** a simulator-confirmed short-list per regime–PCM pair. No active-learning loop, no full NSGA-II.

- [ ] Search the surrogate over the design grid — coarse grid, random search, or a single weighted-sum run (weights over useful energy vs PCM mass vs pump energy). **State it's a single pass**, not the full loop.
- [ ] Apply hard constraints before ranking [1, §9.2]: non-overlap, volume/passage, temperature safety, flow limits, min delivery temp.
- [ ] Take top 3–5 predicted designs per regime–PCM and **re-run them in the actual simulator** (non-negotiable).
- [ ] **Large-error rule (Bug-Fix 5):** if surrogate-vs-simulator error >15%, trust the simulator, log it, note the single-pass limitation; never report the surrogate value as final.
- [ ] Apply the pre-declared selection rule [1, §9.5]: reject infeasible → meet delivery/reliability targets → within **5%** of best useful energy (Bug-Fix 7) → minimise pump energy then PCM mass → prefer simpler/lower capsule count → prefer larger constraint margin → confirm on an unseen weather year if available.

**Exit check:** one simulator-confirmed deployable design per regime (per shortlisted PCM, or the winning PCM if tight), with surrogate-vs-simulator shown side by side.

## Phase 8 — Light robustness + card + Obj3 handoff (6.5 hrs)
**Goal:** D2.7, D2.8, D2.9 — what Objective 3 needs to start.

**Robustness (2.5 hrs) — Bug-Fix 6 [1, §11.1]:** 100–200 Monte Carlo draws per final design with concrete distributions:
- PCM latent heat: ±10% uniform.
- Weather: medoid + 1 member point (or medoid + noise if no alternate).
- Demand: ±20% volume, ±30 min timing shift.
- Inlet/mains temperature: ±2 °C.
- **Never fewer than 50 draws.** Report: P(meet delivery temp), P(meet annual demand), useful-energy 5th–95th percentile interval, P(any safety-temperature violation). State which 3–4 sources you covered and why.
- Robust if P(demand) ≥ ~75% and P(temp-safe) ≥ ~95%; otherwise report as a caveat, don't hide it.

**Recommendation card (2 hrs) [1, §12]:** one per regime — regime/climate summary, PCM shortlist with Objective 1 rank, selected geometry + flow, simulator-confirmed performance, robustness probabilities, surrogate-vs-simulator delta, decision rationale, and an explicit **caveats** block (missing/imputed properties, single-pass optimization, reduced Monte Carlo, single-state scope, lumped-model ±15%).

**Objective 3 handoff (2 hrs) [1, §13]:** `obj3_environment_contract_<STATE>.json` — regime_id, selected pcm_id + properties, geometry, flow envelope (nominal/min/max), pressure limit, delivery-temp target, max safe temps, `sim_v1_<STATE>` version tag, and the state-vector / action-space skeleton (charge/discharge/bypass) plus safety-shield conditions.

**Exit check:** every regime for your state has a card and appears in the contract file. This is your Objective 2 "done" line for the ~40-hr version; full multi-state comparison, active-learning, and full-draw robustness are explicitly deferred and named as future work — not silently dropped.

---

# AFTER ALL FOUR STATES FINISH — Comparative Assembly (shared, ~2–3 hrs)

This is the payoff step that turns four independent runs into the IEEE contribution [1, §12]. Done once, by whoever coordinates, after all four `results/<STATE>/` folders exist.

- [ ] **PCM × State heatmap:** useful energy (or solar fraction) for each PCM in each state — reveals e.g. "RT35 wins TN, RT42 wins RJ" [1, §12.2].
- [ ] **Design-parameter shift chart:** optimal capsule count and flow rate by state — shows climate-driven shifts within identical bounds.
- [ ] **Overlaid Pareto fronts:** useful energy vs PCM mass, one curve per state.
- [ ] **Consistency check:** confirm all four used the same `system_config_shared.yaml`, `design_bounds_shared.yaml`, and simulator code (compare config hashes). If any differs, the comparison is invalid — re-run the offending state [1, §3].
- [ ] Write `results/COMPARATIVE_ANALYSIS.md` with the three figures + a short narrative.

**This section is what makes the paper.** A single-state result is a case study; four states under identical methodology is a comparative finding [1, §0.1].

---

## IF YOU RUN OUT OF TIME (per state) — Prioritized Cut List [1, §18]

Cut in this order; stop when you run out of hours:
1. Drop to 2–3 shortlisted PCMs → 1 PCM per regime for the optimization pass.
2. Cut Monte Carlo draws to ~30–50 (some robustness beats none) — never zero.
3. Reduce the surrogate to feasibility + one target (useful energy).
4. Use medoid only; defer the member-point re-evaluation.

**Never cut:** Phase 4 verification, the Phase 7 simulator re-confirmation, or the ambient tank-loss term. These are what make the numbers defensible in a viva.

Document every cut in your Limitations section using the "Full spec vs. 40-hr version" table above.

---

## PER-STATE READINESS CHECKLIST (copy into each operator's tracker)

- [ ] Shared configs frozen (Phase 0A) and pulled unchanged.
- [ ] `<STATE>` regimes, weather, PCM shortlist, demand profile confirmed (Phase 0B).
- [ ] Climate-signature sanity check passed (Bug-Fix 8).
- [ ] `states/<STATE>.yaml` version-locked (mains temp + demand total documented).
- [ ] Geometry engine deterministic; boundary cases clean.
- [ ] Simulator includes active ambient tank-loss term (Bug-Fix 1).
- [ ] Phase 4: ≥3/5 gates pass; residual <0.5%; report written.
- [ ] DOE ~150–300 cases, failures retained, 80/20 split.
- [ ] Surrogate hold-out R² acceptable; beats linear baseline.
- [ ] Optimization single-pass; top-N simulator-confirmed; 5% tolerance applied.
- [ ] Robustness ≥50 draws, 3–4 sources, distributions documented.
- [ ] Recommendation card(s) + `obj3_environment_contract_<STATE>.json` produced.
- [ ] Config hashes recorded for the final consistency check.

---

## REFERENCES (IEEE)

**[1]** Objective 2 Multi-State Design Optimization Framework (internal project specification), 2026. *Sections cited: §0 (framing), §2 (climate inputs), §3 (frozen configuration), §4 (simulator), §5 (verification), §6 (design space), §7 (surrogate), §8 (active learning), §9 (optimization & selection rule), §11 (robustness), §12 (comparative analysis), §13 (Objective 3 handoff), §18 (cut-priority).*

**[2]** B. Singh, R. S. Rai, P. Yadav, S. Srivastava, and C. Yadav, "Application of phase change materials in solar water heating systems—A comprehensive review," *Sol. Energy Mater. Sol. Cells*, vol. 293, p. 113888, 2025, doi: 10.1016/j.solmat.2025.113888.

**[3]** G.-R. Chen, T.-W. Liao, C.-C. Hsieh, J. Barman, C.-Y. Huang, and C.-F. J. Kuo, "Using the Taguchi method and grey relational analysis to optimize the parameter design of flat-plate collectors with nanofluids and phase change materials in an integrated solar water heating system," *Energy Convers. Manag.: X*, vol. 26, p. 100910, 2025, doi: 10.1016/j.ecmx.2025.100910.

**[4]** F. A. Barqawi, "Dynamic simulation of phase change material-integrated solar water heating systems: A machine learning approach to energy conversion optimization," *Muthanna J. Eng. Technol.*, vol. 13, no. 3, pp. 1–14, 2025, doi: 10.52113/3/eng/mjet/2025-13-03/-1-14.

**[5]** S. Liu, J. Han, Y. Shen, S. Y. Khan, W. Ji, H. Jin, and M. Kumar, "The contribution of artificial intelligence to phase change materials in thermal energy storage: From prediction to optimization," *Renew. Energy*, vol. 238, p. 121973, 2025, doi: 10.1016/j.renene.2024.121973.

---

**Document status:** State-agnostic; run once per state, assemble the comparison at the end.  
**Prepared for:** Group 12, Amrita School of Engineering, B.Tech CSE.  
**Supervisor:** Dr. T. Deepika.  
**Project:** Climate-Adaptive Intelligent Control and Optimization of PCM Thermal Storage for Solar Water Heating.
