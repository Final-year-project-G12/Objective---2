# Objective 2 — Consolidated Plan (Reconciled)
## Climate-Adaptive PCM Design Optimization — Tamil Nadu, Rajasthan, Assam, Uttarakhand

**Objective 2 statement (authoritative, from project scope):** Develop an AI-driven design
optimization model to determine the optimal PCM thickness, capsule arrangement, number of PCM
capsules, and flow rate for maximizing thermal energy storage under location-specific climatic
conditions.

This document merges two prior drafts into one plan:
- the **multi-state 8-phase implementation workflow** (shared config, geometry engine, grey-box
  simulator, verification gates, DOE, surrogate, randomized search, robustness, Objective 3
  hand-off — run identically across 4 states), and
- the **design-vector correction** (capsule arrangement restored as a real decision variable,
  thickness derived from diameter instead of sampled independently).

Everything from the 8-phase workflow is kept. The one thing that changes throughout it is the
design vector and everything downstream of it (DOE stratification, surrogate features, search,
outputs). That change, and its consequences, are called out explicitly at each phase rather than
silently merged in.

---

## 0. Reconciliation notes — read this before using either prior draft again

**0.1 — Arrangement: frozen vs. restored (resolved → restored)**
The multi-state workflow froze capsule arrangement to "sphere, staggered packing" for all states
as a 40-hour scope cut, and stated this explicitly: *"The arrangement is therefore a fixed
modeling assumption, not a result to be reported as if it had been searched."* The design-vector
correction points out this directly contradicts the objective statement, which names arrangement
as one of the four things the model must determine — freezing it means the model only ever
determines 3 of 4 required parameters, with the 4th assumed.

**Resolution:** arrangement is restored as a free categorical decision variable
(`{single-layer, staggered, radial}`), searched and reported per regime, per the correction
draft. Shape stays frozen to sphere (correctly — shape was never named in the objective).

**Consequence you cannot skip:** the Tamil Nadu numbers already produced (215 DOE cases →
146 valid / 69 rejected; capsule-count bound widened to 8–37; max verified-valid PCM-volume
fraction 19.8%; surrogate R² > 0.94; 120-draw robustness runs) were all generated in a
**3-variable design space** (`d, N, ṁ`, arrangement held constant). They are legitimate evidence
for the geometry/simulator/gate methodology, but they are **not** valid evidence for "what the
optimal design is" once arrangement is unfrozen, because:
- staggered, single-layer and radial packing have different geometric packing efficiency, so the
  same tank volume supports a different feasible `(d, N)` region per arrangement;
- the N∈[8,37] bound and the 19.8% max-valid-fraction figure were derived assuming staggered
  packing only, and must be re-derived (or at least re-checked) for single-layer and radial before
  being used as a shared bound across arrangements.

So: **Tamil Nadu Phase 5 onward (DOE → surrogate → search → robustness → cards → contract) must
be rerun** under the corrected 4-variable design vector before TN can be called "done." Phases 1–4
(state prep, geometry math itself, simulator core, verification gates) do not need to be redone —
they're arrangement-agnostic infrastructure; only the *usage* of the geometry engine (branching by
arrangement) needs re-enabling, per §2 below.

**0.2 — Capsule-count bound: keep the evidence, not the assumption behind it**
The widened bound (N: 8–37, replacing an earlier 8–24) was empirically justified specifically to
make the 15–20% PCM-volume target reachable under staggered packing. Keep 8–37 as the *starting*
shared bound for all three arrangements, but Phase 2 must re-verify — with real boundary tests,
not by assumption — whether 37 is still the right upper bound for single-layer (generally lower
packing efficiency → volume target may be unreachable within 37) and radial (concentric-ring
packing → different capacity curve). If an arrangement can't reach the 15–20% volume-fraction
target within a shared count bound, that itself is a reportable geometry finding, not something to
paper over by quietly loosening the bound per-arrangement without saying so.

**0.3 — What is *not* affected by this reconciliation**
Everything else in the multi-state workflow stands as originally specified and should not be
re-litigated:
- randomized-search-ranked-by-surrogate (not Bayesian Optimization, not GA, not NSGA-II);
- active learning and full multi-objective Pareto search remain deferred future work;
- the simulator (grey-box enthalpy model, ambient tank-loss term active) is the final authority —
  surrogate is screening/ranking only;
- the 5% selection tolerance, the >15% surrogate-vs-simulator discrepancy rule, the safety-first
  tie-break order;
- the "plain-water tank as diagnostic baseline only, never the final PCM recommendation" rule;
- the requirement to report nominal safety and robustness safety as separate fields;
- the state-parameterized (not state-branched) implementation: one shared codebase, only weather /
  regimes / PCM shortlist / demand / mains-temperature swap per state.

---

## 1. Purpose and scope

Objective 2 converts the climate-specific PCM shortlist from Objective 1 into a
simulator-confirmed physical design for each climate regime in each state. The output is not a
PCM ranking alone — it is a deployable design record (geometry, arrangement, hydraulic limits,
annual thermal performance, uncertainty results) plus a hand-off contract for Objective 3.

Run the same workflow independently for **Tamil Nadu, Rajasthan, Assam, and Uttarakhand**. The
implementation is state-parameterized: simulator, geometry engine, DOE procedure, surrogate
family, search procedure, selection rule, and verification gates stay common across states. Only
weather, climate regimes, PCM shortlist, mains-water temperature, and demand profile change per
state.

Tamil Nadu remains the reference implementation in the sense that it has already exercised the
full pipeline end-to-end and surfaced the bugs this document fixes — but per §0.1, its Phase 5+
numeric results need to be regenerated under the corrected design vector before being reused as
"the" reference numbers. Rajasthan, Assam, and Uttarakhand should build directly against the
corrected spec below rather than reproducing TN's original 3-variable run.

---

## 2. Corrected design vector (replaces both prior versions)

| Variable | Role | Bounds | Notes |
|---|---|---|---|
| Capsule diameter `d` | Free | 0.02–0.08 m | True degree of freedom |
| Capsule count `N` | Free (integer) | 8–37 (shared starting bound, §0.2) | Re-verify per arrangement before treating as final |
| **Arrangement** | **Free (categorical)** | `{single-layer, staggered, radial}` | **Restored.** This is what makes "optimal capsule arrangement" an actual model output |
| Shape | Fixed (documented scope cut) | sphere | Correctly frozen — not named in the objective statement |
| PCM volume fraction | Derived | target 10–20% of tank | Computed from `N`, `d`, tank volume, and arrangement packing density — not sampled |
| Thickness (conduction distance) | Derived | `= d/2` (radius) | Removed as an independent variable — this was the root cause of "impossible dimension" outputs surviving to the shortlist |
| Flow rate `ṁ` | Free | 0.010–0.050 kg/s | True degree of freedom |

**Rule:** `d, N, arrangement, ṁ` are the four real decision variables, matching the four
parameters named in the objective exactly. Volume fraction and thickness are always computed from
them, never sampled independently.

Each arrangement has its own spacing/overlap geometry (single-layer: planar spacing; staggered:
offset-row spacing; radial: concentric-ring spacing). These formulas already exist in the full-spec
geometry engine — restoring arrangement re-enables branches that were disabled for the earlier
scope cut, it does not require new physics.

Design-vector notation for pipeline code:
`[capsule_diameter_m, capsule_count, arrangement, flow_rate_kg_s, pcm_id, regime_id]`

---

## 3. Corrected implementation decisions (frozen for all four state runs)

1. **Capsule arrangement is a searched categorical variable**, not a fixed assumption
   (supersedes the earlier "staggered-only" freeze — see §0.1). Sphere shape stays fixed.
2. **The optimizer is a randomized search ranked by a trained surrogate.** Generate feasible
   random candidates, score with the surrogate, retain top-ranked, re-run in the real simulator.
   Do not describe this as Bayesian Optimization or a Genetic Algorithm.
3. **Active learning and full NSGA-II are deferred extensions.** One DOE round → one
   surrogate-ranked search → simulator confirmation, per state. Do not claim convergence of an
   active-learning loop or a complete multi-objective Pareto front.
4. **The simulator is the final authority.** Surrogate predictions are for screening/ranking only.
   Every selected design and every robustness draw runs through the real grey-box simulator.
5. **The ambient tank-loss term remains active** (`Q_loss = U_tank·A_tank·(T_water − T_ambient)`).
   Removing it inflates solar fraction and invalidates comparisons.
6. **Shared design bounds are frozen before the four state runs** — starting from `N ∈ [8, 37]`,
   `d ∈ [0.02, 0.08]` m, `ṁ ∈ [0.010, 0.050]` kg/s — with per-arrangement re-verification per §0.2
   before being called final. If bounds must differ by arrangement, document why, don't hide it.
7. **Objective 2 selects a PCM design.** Plain water may remain as a diagnostic baseline but must
   never silently replace the PCM design in the final per-regime recommendation.
8. **Safety is reported, not hidden.** A design can be the best PCM design within the energy
   tolerance while still requiring an active over-temperature bypass in Objective 3. Nominal
   safety and robustness safety are separate reported fields.
9. **Geometry engine enforcement is a gate at every stage, not a filter applied once** (see §4).

---

## 4. Revised pipeline — constraint enforcement as a gate, not a filter

```
generate candidate (d, N, arrangement, ṁ)
        │
        ▼
Phase 2 geometry/constraint engine   ← runs BEFORE anything else touches the candidate
   - arrangement-specific spacing/overlap check
   - N·V_capsule ≤ target volume-fraction band of V_tank
   - V_tank − N·V_capsule ≥ V_min_passage
   - pressure-drop / Reynolds check
        │
   reject (log reason code) ──────► discarded, never seen by surrogate
        │
   pass
        │
        ▼
Phase 3 simulator (DOE generation) → performance + feasibility labels
        │
        ▼
Phase 6 surrogate
   - performance regressor: trained ONLY on feasible, simulator-converged rows
     (arrangement one-hot encoded as an input feature)
   - feasibility classifier: trained on ALL rows (feasible + geometry-rejected + sim-failed),
     arrangement included
        │
        ▼
Phase 7 optimizer search
   - candidates generated by REJECTION SAMPLING through the Phase 2 engine, varying
     d, N, arrangement, ṁ jointly — engine is inside the generator loop, not a post-hoc filter
   - classifier used only to speed ranking, never as the final gate
        │
        ▼
Top candidates per regime–PCM pair (may span more than one arrangement)
        │
        ▼
Re-verified against deterministic geometry engine AGAIN, using arrangement-specific
spacing formula for each candidate (catches drift if surrogate trained on stale constraints)
        │
        ▼
Re-run in the actual simulator (non-negotiable) → apply 15%-error rule + 5%-tolerance selection
        │
        ▼
Selection rule → 1 deployable design per regime (may report multiple arrangements
if within noise margin — don't force a single winner artificially)
```

Key point carried over from the correction draft: the geometry engine appears **three times**
(generation, training-data labeling, final re-verification) — every design that reaches a
human-readable output has been checked at least twice by the deterministic engine.

---

## 5. State-specific inputs and shared inputs

### Shared across all four states (freeze and hash once)
- `configs/system_config_shared.yaml`
- `configs/design_bounds_shared.yaml` (now includes arrangement as a bound/enum, not just d/N/ṁ)
- universal code under `src/`
- solver, timestep, tolerances, safety limits, delivery target, selection tolerance
- random-seed policy and output schema

Common baseline: 1.5 m² flat-plate collector, 50 L tank, direct aluminium capsule encapsulation,
0.010–0.050 kg/s pump range, 75 °C max water temp, 65 °C max PCM temp, 3.5 bar max pressure,
45 °C delivery target, backward Euler with adaptive sub-stepping, 5% useful-energy selection
tolerance (pre-declared, not tuned after seeing results).

### Replaced per state
- Objective 1 regime identifiers and profiles
- medoid hourly weather (+ alternate/member point where available)
- Objective 1 PCM shortlist per regime
- PCM property records and uncertainty fields
- mains/inlet-water temperature range
- demand-profile path and documented daily demand total
- input hashes and Objective 1 version tag

Do not copy Tamil Nadu's regimes, PCM winners, demand curve, or weather into another state.

### State run matrix

| State | Input focus | What it tests |
|---|---|---|
| Tamil Nadu | Corrected `tamilnadu.yaml`; **rerun Phase 5+ under the 4-variable design vector** (§0.1) | Reference implementation, but its arrangement-aware numbers do not exist yet — this run produces them |
| Rajasthan | Rajasthan Objective 1 regimes, hot-dry weather, shortlist, demand | High-solar, hot-dry conditions |
| Assam | Humid, monsoon-dominated regimes and weather | Cloudy/humid conditions, longer low-solar periods |
| Uttarakhand | Elevation-corrected regimes and weather | Cold, elevation-variable conditions; verify elevation isn't silently defaulted away |

Climate descriptions above are planning labels, not final cluster results — final regime
identities come from each state's frozen Objective 1 outputs.

---

## 6. Eight-phase workflow (updated for the corrected design vector)

### Phase 1 — Freeze the project and prepare one state
Unchanged in structure. Freeze shared system/design-bound files (now including arrangement enum),
record hashes and version tag, build `configs/states/<state>.yaml` by reference not copy, confirm
weather/PCM property completeness, freeze the 5% selection tolerance.
*Outputs:* state config, input manifest, climate-signature sanity report, readiness checklist.
*Go/no-go:* wrong-state weather file is a stop condition, not a patch-later item.

### Phase 2 — Geometry & constraint engine (arrangement branches re-enabled)
**Design vector reparameterization (carried in from the correction draft):** update
`design_bounds_shared.yaml` — remove thickness as a sampled field, add `derive_thickness()`
(`= diameter / 2`); regenerate any existing DOE/surrogate code that still expects thickness as a
raw input column.

Implementation:
1. Derive tank dimensions from frozen tank volume.
2. Compute spherical capsule volume/surface area.
3. Compute total PCM volume and resulting volume fraction **per arrangement's packing model**.
4. Generate packing geometry per arrangement type (single-layer: planar spacing; staggered:
   offset-row spacing; radial: concentric-ring spacing) and the resulting passage space.
5. Check diameter/thickness, count, volume, overlap, passage, flow, pressure-drop constraints —
   using the arrangement-specific formula.
6. Compute hydraulic diameter, Reynolds number, Ergun pressure drop, pump power.
7. Expose as `sample_feasible_design()` doing rejection sampling internally (callers never filter
   after the fact).
8. Return a structured result: valid flag, derived quantities, explicit reason code(s).
9. Deterministic: identical input vector → byte-identical output. ≥50 boundary test rows per
   arrangement (not just one arrangement, since this is now a genuine 3-way branch).

Re-verify, per arrangement, whether N∈[8,37] and the ~15–20% volume-fraction target are jointly
reachable (§0.2) — report per-arrangement max-valid-fraction, don't assume TN's 19.8% figure
(which was staggered-only) transfers to single-layer or radial.

*Outputs:* `src/design/geometry.py`, `src/design/constraints.py` (now arrangement-branched),
geometry boundary-test table per arrangement, valid/invalid design map, hydraulic output,
reason-code summary.
*Verification:* min/max diameter/count/flow cases per arrangement; intentional overlap/volume/
passage/pressure-drop failures; repeat boundary cases twice, confirm identical results; invalid
cases fail cleanly, never crash or silently drop.

### Phase 3 — Grey-box PCM-SWH simulator core
Unchanged. Flat-plate Hottel–Whillier–Bliss collector; tank water energy balance including active
ambient loss; PCM enthalpy formulation with clipped liquid fraction; effective UA thermal
resistance; hydraulics computed separately from thermal energy; hourly demand distributed through
sub-steps with unmet-energy tracking; backward Euler with adaptive sub-stepping; full safety and
energy-accounting logs. Ambient tank-loss term stays active (non-negotiable).
*Outputs:* `src/simulation/`, one-case annual run, temperature/melt-fraction/energy-breakdown/
residual histories, simulator version tag (`sim_v1_<state>`).
*Verification:* run one full year for one state/regime/PCM/design before DOE; must be physically
interpretable, not just "ran without crashing."

### Phase 4 — Five simulator verification gates
Unchanged.
- **Gate 1 (energy conservation):** mean residual < 0.1%, max < 0.5%.
- **Gate 2 (limiting cases):** zero irradiance, zero flow, no PCM, zero latent heat, solid/liquid
  initial states, very high conductivity, insulated tank, empty demand, flow limits — expected
  direction written *before* running.
- **Gate 3 (baseline & loss-term diagnostic):** plain tank vs. fixed PCM vs. optimized-looking
  design under identical weather/demand; confirm disabling ambient loss inflates solar fraction.
- **Gate 4 (benchmark calibration):** compare against a cited published benchmark; >15% mismatch
  is logged and explained, not tuned away.
- **Gate 5 (sensitivity/monotonicity):** perturb latent heat, flow, loss parameters; confirm
  physically plausible direction of movement.
*Go/no-go:* proceed only if residual threshold + limiting cases pass and ≥3/5 gates pass cleanly.

### Phase 5 — Design-of-Experiments (now genuinely 4-variable, stratified by arrangement)
Implementation:
1. Latin Hypercube Sampling over continuous diameter/flow/volume-related variables.
2. Enumerate the integer capsule-count set within the (per-arrangement re-verified) shared bound.
3. **Stratify the LHS so each of the three arrangements gets a roughly even share of cases**
   across the diameter/count/flow space — otherwise the surrogate sees "staggered" far more often
   than "radial" and its arrangement comparison isn't trustworthy. Target ~200–350 feasible cases
   *per arrangement* per state (bumped from a flat 150–300 to give each arrangement adequate
   coverage — roughly triple the total row count of the old single-arrangement TN run).
4. Include min/max diameter/flow/count cases, per arrangement.
5. Include intended PCM-volume levels where geometrically valid, per arrangement.
6. One no-PCM diagnostic baseline per regime, clearly marked as baseline, not a candidate final
   recommendation.
7. Every shortlisted PCM in every regime.
8. Preserve invalid cases and reason codes (including arrangement-specific rejection reasons).
9. Split by complete `case_id`; stratify hold-out by regime, PCM, arrangement, and validity.
10. Record stable seed and exact config hashes.

**TN-specific note:** the original TN run (215 cases, 146 valid / 69 rejected, staggered-only)
must be regenerated under this stratified 4-variable scheme before being reported as "the" TN DOE
— the old numbers describe a different, smaller design space.
*Outputs:* `design_cases.parquet/csv`, DOE manifest, valid/invalid summary (now broken out by
arrangement), train/hold-out split labels.
*Verification:* required corners and PCM/regime/arrangement combinations present; rejected cases
retained; no duplicate case IDs; rejection fraction compared against the deterministic geometry
boundary per arrangement; hold-out has both feasible and infeasible cases.

### Phase 6 — Surrogate model (arrangement as a first-class feature)
Inputs/targets: design + geometry features, continuous climate-signature features, PCM
properties, regime info, no-PCM diagnostic flag. **Arrangement enters both models as a one-hot
categorical feature (3 columns).**
- Performance regressor (Extra Trees / XGBoost, or the frozen shared model family): trained only
  on geometrically-feasible, simulator-converged rows, with arrangement as an input — learns
  performance *as a function of* arrangement rather than holding it constant.
- Feasibility classifier: trained on the full row set (feasible + geometry-rejected +
  simulator-failed), arrangement included.
- Fit a linear-regression baseline on the identical split for comparison.
- Report MAE/RMSE/R² pooled and **broken out by regime, PCM, and arrangement**, not only pooled.
- **New diagnostic (from the correction draft):** report feature importance for arrangement
  specifically. Near-zero importance is a legitimate, reportable finding ("arrangement had
  minimal effect in this design-space region") — not evidence it should have stayed frozen. Either
  way, this replaces assumption with evidence.
- Do not proceed by presenting a weak surrogate as reliable; add DOE cases or simplify the target
  if hold-out performance is inadequate.
*Outputs:* `surrogate_metrics.csv`, `surrogate_error_by_group.csv` (now including an
arrangement breakout), serialized models, parity/residual plots, feature-importance output
(including arrangement), config + seed.
*Verification:* hold-out genuinely unseen; check feasibility recall and error near the
feasibility boundary; check for extrapolation beyond DOE; a high pooled R² does not authorize
surrogate-only reporting.

### Phase 7 — Randomized surrogate-ranked search + simulator confirmation (searches all 4 variables jointly)
1. Generate a large set of random candidate design vectors — **d, N, arrangement, ṁ together** —
   within the (per-arrangement) shared bounds, for every regime and shortlisted PCM.
2. Apply the real geometry/constraint gate first (arrangement-specific formula).
3. Score only feasible candidates with the trained surrogate.
4. Rank by the pre-declared objective and hard constraints, **across all three arrangements per
   regime–PCM pair** — this is the step that actually answers "which arrangement is best here."
5. Retain top candidates per regime–PCM pair (TN's prior run used 20 per pair / 400 total; each
   state reports its actual retained count — this may need to increase now that the search space
   spans 3 arrangements instead of 1).
6. Re-run every retained candidate in the real simulator.
7. Compute surrogate-vs-simulator deltas; if a delta exceeds 15%, the simulator result is
   authoritative — log the discrepancy, don't use the surrogate value as final.
8. Apply the selection rule only after simulator confirmation: reject hard-infeasible; retain PCM
   candidates meeting delivery/reliability requirements; retain candidates within 5% of best
   simulator-confirmed useful energy; use temperature safety as first tie-break; then minimize
   pump energy, PCM mass, capsule count; prefer larger constraint margin and simpler designs.
9. Top 3–5 per regime–PCM pair **may span more than one arrangement type** if results are close —
   report that; don't force a single winner if the margin is inside noise.
10. Keep the plain-tank result in the comparison file as diagnostic only; it never enters the
    final PCM-only pool.

This is a **single randomized search pass ranked by the surrogate** — not Bayesian Optimization,
not a Genetic Algorithm, not full NSGA-II. Those remain deferred future work.
*Outputs:* `surrogate_top_candidates.csv`, `optimized_designs.csv`,
`deployable_design_per_regime.csv`, simulator-confirmed performance table, surrogate-vs-simulator
error table (per arrangement), nominal safety/constraint-margin fields, optimization seed +
candidate-count manifest.
*Verification:* every selected row has a simulator result, not just a surrogate one; selection
rule recalculated from the confirmed table; no plain-tank entry in the PCM-only pool; safety
evaluated with correct water/PCM limits; inspect rejected top candidates too.

### Phase 8 — Robustness, recommendation cards, Objective 3 hand-off
Robustness: ≥50 scenarios minimum, 100–200 recommended (TN's prior run used 120 draws per
selected design — repeat this per-arrangement-aware design, don't assume the old draw counts or
results transfer). Re-run every draw through the real simulator, never the surrogate. Perturb PCM
latent heat (±10%, documented distribution), weather (medoid + alternate/ensemble), demand volume
and timing, mains/inlet temperature, and any other dominant state-specific uncertainty.

Report: probability of meeting delivery temperature; probability of meeting annual demand;
useful-energy 5th/50th/95th percentiles; probability of water-temperature violation; probability
of PCM-temperature violation; draw count and type; thresholds used.

TN's prior robustness numbers (0% temperature-safe draws in regimes 0–3, 30.8% in regime 4;
76.7–98.3% demand reliability) are reportable as historical evidence of *why nominal performance
alone is insufficient*, but are not the final robustness numbers for the corrected design — they
must be regenerated once the corrected design vector's Phase 7 output exists.

**Recommendation card per regime** (merges both drafts' card specs) — one per state regime:
| Field | Content |
|---|---|
| Regime identity | State, cluster ID, medoid location, one-line climate description |
| Selected PCM | Name, O1 rank carried forward |
| Selected geometry | Capsule diameter, capsule count, **arrangement (chosen from the 3, not assumed)**, derived thickness |
| Arrangement rationale | Which arrangement won and by how much, or "arrangements within X% — not decisive here" |
| Flow | Nominal flow rate, min/max envelope |
| Simulator-confirmed performance | Useful energy, solar fraction, pump energy |
| Surrogate-vs-simulator delta | % error, per arrangement |
| Robustness | P(meet delivery temp), P(meet annual demand), 5th–95th percentile useful-energy interval, P(safety-temp violation) |
| Constraint margin | Distance from overlap/volume/passage limits — direct evidence the dimension bug is fixed |
| Nominal vs. robustness safety | Reported as separate fields, not conflated |
| Caveats | Imputed properties, single-pass optimization, reduced Monte Carlo draws, ±15% lumped-model uncertainty, deferred active-learning/NSGA-II work |

**Consolidated cross-state table** (the "4.11-equivalent" slide — build this, it's the single most
important O2 artifact):

| State | Regime | PCM | Capsule Ø (m) | N capsules | Arrangement | Thickness (m, derived) | Flow (kg/s) | PCM vol. % | Solar fraction | P(demand met) |
|---|---|---|---|---|---|---|---|---|---|---|

This table is the direct evidence the model determines all four objective parameters rather than
three of four with arrangement assumed. If arrangement turns out identical across every row,
that's a reportable finding — provided it's a result the search produced, not a constraint
imposed before searching.

**Objective 3 hand-off contract** — `obj3_environment_contract_<state>.json` per regime:
regime ID and selected PCM properties; final geometry (diameter, count, **arrangement**, derived
thickness); flow envelope (nominal/min/max); pressure limit; delivery-temp target; max safe
temps; simulator version tag; state-vector/action-space skeleton (charge/discharge/bypass); safety
shield conditions and guard bands; acceptance tests before controller training. The contract must
state explicitly that an active bypass is required wherever Phase 8 shows inadequate temperature
robustness. Objective 3 consumes the design; it does not retroactively change Objective 2's frozen
simulator limits or selection rule.

*Outputs:* `robustness_results.csv`, `robustness_summary.csv`, `recommendation_cards.md`,
`obj3_environment_contract_<state>.json`, uncertainty-distribution manifest, robustness plots.
*Verification:* all draws simulator-based; draw counts/seeds confirmed; one card + one contract
entry per regime; percentile calculations audited from raw draw file; safety shield ≥ hard
simulator limits; a design is not "robust" merely because it performs well in the nominal medoid
year.

---

## 7. State-by-state execution order

```
Tamil Nadu    Phase 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8   (Phases 1–4 largely reusable;
                                                       5–8 rerun under corrected design vector)
Rajasthan     Phase 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8   (built fresh against corrected spec)
Assam         Phase 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8   (built fresh against corrected spec)
Uttarakhand   Phase 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8   (built fresh against corrected spec)
```

Runs may be parallelized after shared config/code are frozen, but no state may modify the shared
simulator, bounds, solver, selection tolerance, or output schema independently. If a shared file
changes after a state has completed DOE, all affected states rerun from Phase 5 onward; if
simulator physics changes, rerun from Phase 3 or 4.

Command pattern per state:
```
python pipeline.py --state <state> --stage geometry
python pipeline.py --state <state> --stage simulate
python pipeline.py --state <state> --stage verify
python pipeline.py --state <state> --stage doe
python pipeline.py --state <state> --stage surrogate
python pipeline.py --state <state> --stage optimize
python pipeline.py --state <state> --stage robustness
python pipeline.py --state <state> --stage handoff
```
`--state` selects only the state-specific configuration and inputs, never a different physics
implementation.

---

## 8. Cross-state comparative assembly (after all four states complete)

Do not assemble this until all four state folders contain verified Phase 8 outputs run under the
**corrected 4-variable design vector** (not a mix of old TN + new other-states results).

1. PCM-by-state/regime performance comparison (simulator-confirmed useful energy / solar fraction).
2. Selected capsule count, diameter, arrangement, PCM volume, and flow-rate comparison across
   states — this is where "does climate shift the optimal arrangement, not just the PCM" gets
   answered.
3. Safety-robustness comparison, same probability definitions/thresholds across states.
4. Overlaid performance-vs-mass or performance-vs-pump-energy plots, labeled as *confirmed
   designs*, not a complete NSGA-II Pareto front.
5. Shared-config hash consistency report.
6. `results/COMPARATIVE_ANALYSIS.md` narrative separating genuine climate-driven differences from
   differences caused by missing data, unequal regime counts, or incomplete robustness coverage —
   this is the actual IEEE-paper contribution: same design-space bounds, optimum shifts by climate.

**Cross-state validity checks** — the four-state comparison is valid only if: shared system-config
hash identical; shared design-bound hash identical (including the arrangement enum and any
per-arrangement bound adjustments, documented); simulator code/version identical; selection
tolerance and tie-break order identical; output definitions and robustness thresholds identical;
each state used its own O1 weather/regimes/shortlist/mains-temp/demand; all selected designs
simulator-confirmed; all state-specific deviations documented. A difference in winning PCM,
arrangement, or flow rate is interpretable as climate-responsive only after these checks pass.

---

## 9. Objective 2 completion checklist (merged, arrangement-aware)

- [ ] Shared configs frozen and hashed (including arrangement enum and design-bound source)
- [ ] State inputs and O1 provenance frozen, per state
- [ ] Climate-signature sanity check passed, per state
- [ ] Design vector reparameterized — thickness derived (`= d/2`), never sampled
- [ ] **Arrangement restored as a searched categorical variable** (single-layer/staggered/radial), not frozen — supersedes the earlier freeze decision
- [ ] Per-arrangement geometry engine deterministic and boundary-tested (≥50 rows/arrangement)
- [ ] Per-arrangement reachability of the 15–20% volume-fraction target re-verified (don't assume TN's staggered-only 19.8% figure transfers)
- [ ] Simulator includes ambient tank loss; passes conservation, limiting-case, baseline, benchmark, sensitivity gates (≥3/5, residual <0.5%)
- [ ] DOE stratified across all three arrangements, includes feasible + infeasible cases
- [ ] Hold-out split valid; surrogate errors reported by regime, PCM, **and arrangement**
- [ ] Surrogate models include arrangement as an input feature; arrangement feature-importance reported
- [ ] Geometry engine wired as `sample_feasible_design()`, used at generation and final re-check, with arrangement-specific spacing formulas
- [ ] Randomized surrogate-ranked search documented as a single pass, spans d/N/arrangement/ṁ jointly
- [ ] All retained candidates simulator-confirmed; >15% surrogate-error rule applied
- [ ] Performance surrogate trained only on feasible rows; feasibility classifier on full set
- [ ] PCM-only final selection used; plain tank retained only as diagnostic
- [ ] Every recommendation card shows constraint margin explicitly
- [ ] Every recommendation card names which arrangement won and why (or states margin was inside noise)
- [ ] Nominal safety and robustness safety reported as separate fields
- [ ] Robustness run (≥50, preferably 100–200 draws) per final design, through the real simulator
- [ ] Consolidated cross-state table built (§6, Phase 8) — the "4.11-equivalent" slide
- [ ] Comparative assembly figures + `COMPARATIVE_ANALYSIS.md` built once all 4 states done
- [ ] `obj3_environment_contract_<state>.json` produced and schema-validated per regime, includes arrangement
- [ ] **Tamil Nadu's Phase 5–8 outputs regenerated under the corrected 4-variable design vector** — old staggered-only numbers not reused as final results
- [ ] All seeds, versions, hashes, and caveats recorded

Objective 2 is complete at the project level only after this checklist passes for all four states
and the cross-state hash/comparability checks in §8 pass. Full active-learning loop, complete
NSGA-II search, exhaustive capsule-shape search (beyond sphere), a larger uncertainty campaign, and
experimental hardware validation remain future extensions unless separately implemented and
reverified.

---

## 10. One slide-deck change to make now

Add a table matching §6's consolidated cross-state table as a new slide, titled **"5.5 Objective 2
— Final Design Recommendations,"** mirroring the existing "4.11 Objective 1 — Final PCM
Recommendations" slide. This is the single "here is the final answer per regime" slide a panel
will ask for first — currently the deck has architecture, baseline comparison, and feature
importance for O2, but no consolidated answer table.

---

## References

[1] G.-R. Chen, T.-W. Liao, C.-C. Hsieh, J. Barman, C.-Y. Huang and C.-F. J. Kuo, "Using the
Taguchi method and grey relational analysis to optimize the parameter design of flat-plate
collectors with nanofluids, and phase change materials in an integrated solar water heating
system," *Energy Conversion and Management: X*, vol. 26, p. 100910, 2025,
doi: 10.1016/j.ecmx.2025.100910.

[2] obj2_explanation, n.d.
[3] FINALIZATION_SUMMARY, n.d.
[4] obj1_explanation, n.d.
[5] O2_revised.md — design-vector correction draft (this project, internal).
[6] Objective2_MultiState_Implementation_Workflow.md — 8-phase multi-state workflow draft (this project, internal).