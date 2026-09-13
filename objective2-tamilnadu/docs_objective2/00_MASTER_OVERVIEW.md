# 00 — Objective 2 Master Overview (Tamil Nadu, Phases 1–8 — COMPLETE)

## What this covers

Objective 2 turns Objective 1's output — climate regimes + a shortlisted
PCM per regime — into a **physical PCM-storage design and a validated
simulator** that Objective 3 can build a controller against. This
consolidated set of docs covers **all eight phases** of the ~40-hour
per-state execution plan (`O2_Unified_PerState_Execution_Framework.md`),
implemented, verified, and completed for **Tamil Nadu**. Objective 2 is
done for this state — see `RESULTS.md` (project root) for the full
results digest and `OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` for the hand-off.

> **✅ 2026-09-13 update: fully re-run, current.** Three methodology
> revisions were made and are now **fully reflected everywhere** —
> Tm-target retargeting (`12_TM_TARGET_RETARGETING.md`), design-bounds
> widening (`13_DESIGN_BOUNDS_WIDENING.md`), and a selection-rule scope
> correction (`14_SELECTION_RULE_SCOPE_CORRECTION.md`) that removed the
> zero-PCM "plain tank" option from the final per-regime pick (it was
> never actually requested by Objective 2's problem statement). Phases
> 2 and 5–8 have all been re-run against all three changes. **Every
> regime's Objective 2 recommendation is now a genuine, optimal PCM
> design** — see the updated "two findings" section below and
> `RESULTS.md` for the full current numbers.

| Phase | Deliverable | Status |
|---|---|---|
| Phase 1 | D2.1 — frozen state config (`configs/states/tamilnadu.yaml`), incl. retargeted `Tm_target_C`/shortlist | COMPLETE |
| Phase 2 | D2.2 — geometry & constraint engine (`src/design/`), widened bounds reach ~19.8% PCM-volume fraction | COMPLETE |
| Phase 3 | D2.3 — grey-box enthalpy simulator (`src/simulation/`) | COMPLETE |
| Phase 4 | Simulator verification, Gates 1–5 (`src/verify/gates.py`) | COMPLETE — **GO** |
| Phase 5 | D2.4 — DOE (`src/doe/`) — 215 cases, 144 valid, retargeted PCMs + widened bounds | COMPLETE |
| Phase 6 | D2.5 — surrogate (`src/surrogate/`) — R²>0.97 every target | COMPLETE |
| Phase 6b | Multi-fidelity surrogate augmentation (`src/surrogate/multifidelity.py`) — ⚠ stale, pre-dates today's revisions | COMPLETE (historical) |
| Phase 7 | D2.6 — optimization + simulator confirmation (`src/optimize/`) — **PCM selected in all 5 regimes** | COMPLETE |
| Phase 8 | D2.7/D2.8/D2.9 — robustness (real 10-yr historical weather ensemble), recommendation cards, Objective 3 contract with a fully specified reward function (`src/robustness/`, `src/handoff/`) | COMPLETE |

## Code map

```
objective2_design_optimization/
├── config.py                          # path constants (already existed)
├── build_input_package.py             # Phase 0 — freezes Obj1 outputs   (already existed)
├── build_regime_weather.py            # Phase 0 — per-regime weather     (already existed)
├── build_demand_profile.py            # Phase 0 — canonical demand curve (already existed)
├── pipeline.py                        # NEW — CLI entry point for Phases 2-4
├── configs/
│   ├── system_config_shared.yaml      # NEW — Phase 0A, frozen for all 4 states
│   ├── design_bounds_shared.yaml      # NEW — Phase 0A, frozen for all 4 states
│   └── states/tamilnadu.yaml          # NEW — Phase 1, this state's inputs
├── src/
│   ├── io_utils.py                    # NEW — shared config/data loaders
│   ├── design/
│   │   ├── schema.py                  # NEW — DesignVector
│   │   ├── geometry.py                # NEW — Phase 2 geometry + Ergun hydraulics
│   │   └── constraints.py             # NEW — Phase 2 valid/invalid + reason codes
│   ├── simulation/
│   │   ├── capsule_enthalpy.py        # NEW — Phase 3 enthalpy model
│   │   ├── collector_model.py         # NEW — Phase 3 flat-plate collector
│   │   ├── heat_transfer.py           # NEW — Phase 3 UA_eff (Wakao-Kaguei)
│   │   ├── hydraulic_model.py         # NEW — Phase 3 runtime pump-power wrapper
│   │   ├── demand_profile.py          # NEW — Phase 3 demand-curve model
│   │   ├── energy_balance.py          # NEW — Phase 3/4 energy accounting
│   │   ├── tank_model.py              # NEW — Phase 3 core timestep solver
│   │   └── run_case.py                # NEW — Phase 3 one-case orchestrator
│   ├── verify/
│   │   └── gates.py                   # NEW — Phase 4 Gates 1-5 + report writer
│   ├── doe/
│   │   ├── generate_cases.py          # NEW — Phase 5 LHS + boundary + baseline sampling
│   │   ├── run_batch.py               # NEW — Phase 5 runs every case through Phase 2+3
│   │   └── split_cases.py             # NEW — Phase 5 case-level train/holdout split
│   ├── surrogate/
│   │   ├── features.py                # NEW — Phase 6 feature table (design+climate+PCM+confidence)
│   │   ├── train.py                   # NEW — Phase 6 ExtraTrees + linear baseline + feasibility clf
│   │   ├── evaluate.py                # NEW — Phase 6 error breakdown by regime/PCM
│   │   └── multifidelity.py           # NEW — Phase 6b low-fidelity speedup + sample-efficiency experiment
│   ├── optimize/
│   │   ├── search.py                  # NEW — Phase 7 surrogate-scored random search
│   │   └── select_deployable.py       # NEW — Phase 7 simulator-confirm + selection rule
│   ├── robustness/
│   │   ├── monte_carlo.py             # NEW — Phase 8 Monte Carlo robustness analysis
│   │   └── weather_ensemble.py        # NEW — Phase 8 real 10-year historical weather ensemble
│   ├── handoff/
│   │   ├── build_recommendation_cards.py  # NEW — Phase 8 per-regime cards
│   │   └── build_obj3_contract.py         # NEW — Phase 8 Objective 3 environment contract
│   └── plots/
│       └── make_plots.py              # NEW — justification figures for Phases 2-8
├── RESULTS.md                          # NEW — full results digest, all 8 phases
└── results/tamilnadu/
    ├── simulator_verification_report.txt      # Phase 4 output (GO)
    ├── design_cases.parquet / .csv            # Phase 5 output (215 cases)
    ├── surrogate_metrics.csv, surrogate/models.pkl   # Phase 6 output
    ├── surrogate_error_by_group.csv            # Phase 6 output
    ├── design_cases_lowfid.parquet / .csv       # Phase 6b low-fidelity re-run of every DOE case
    ├── multifidelity_speedup_report.json        # Phase 6b speedup + low-fidelity accuracy
    ├── multifidelity_sample_efficiency.csv      # Phase 6b sample-efficiency experiment
    ├── surrogate_top_candidates.csv            # Phase 7 intermediate output
    ├── optimized_designs.csv                   # Phase 7 PCM-comparison report
    ├── deployable_design_per_regime.csv        # Phase 7 final selection
    ├── robustness_results.csv, robustness_summary.csv  # Phase 8 Monte Carlo output (real 10-yr weather ensemble)
    ├── recommendation_cards.md                 # Phase 8 per-regime cards
    ├── obj3_environment_contract_tamilnadu.json  # Phase 8 Objective 3 hand-off
    └── plots/
        ├── interactive/*.html                  # 18 self-contained interactive figures
        └── static/*.png                        # same 18 figures as flat images
```

Everything under `src/` is **state-agnostic** — `state="tamilnadu"` is just
a string passed in; running the same code for Rajasthan/Assam/Uttarakhand
only requires their own `configs/states/<state>.yaml` plus their
`data/objective1/`, `data/weather/`, `data/demand/` folders (built the same
way `build_input_package.py` / `build_regime_weather.py` /
`build_demand_profile.py` already build Tamil Nadu's).

## Headline result: Phase 4 verdict = **GO**

```
Gate 1 (conservation):        PASS   max residual = 0.00008 %  (limit: <0.5%)
Gate 2 (limiting cases):      PASS   10/10 checks
Gate 3 (baseline comparison): PASS   (see caveat below)
Gate 4 (published benchmark): PASS-WITH-CAVEAT (52% vs cited 54-84% band)
Gate 5 (sensitivity):         PASS   3/3 checks

Go/No-Go: GO  ->  simulator released as sim_v1_tamilnadu
```

## The two findings worth reading before anything else

**1. PCM now wins — genuinely — in every regime, after two real design-space
fixes.** Gate 3 (Phase 4) originally found that Objective 1's climate-
anchored PCM shortlist (n-Octacosane, Tm=61.6°C, from a `Tm_target_C=57°C`
formula) did *not* clearly beat a plain sensible-water tank, while a
diagnostic PCM matched to the tank's real operating range (Tm=40°C) beat
it decisively — ruling out a simulator bug and pointing at a target-
mismatch instead. Two fixes followed directly from that diagnostic:
**retargeting `Tm_target_C`** to each regime's own simulated charging-hour
water temperature (46.5–51.5°C, see `12_TM_TARGET_RETARGETING.md`) and
**widening the PCM-volume design bounds** to reach the literature's
15–20% test levels (`13_DESIGN_BOUNDS_WIDENING.md`, ~19.8% now reachable
vs. 12.9% before). Together with a **selection-rule scope correction**
(`14_SELECTION_RULE_SCOPE_CORRECTION.md` — Objective 2's actual problem
statement asks for the optimal PCM design, not whether to use PCM at all,
so the zero-mass "plain tank" option was removed from the final pick),
every regime's optimal PCM design now beats plain tank on useful energy
(+0.08% to +0.12%) — genuine, simulator-confirmed, not a marginal
statistical tie (`08_PHASE7_OPTIMIZATION.md`).

**2. No PCM design is temperature-robust under realistic uncertainty —
and this is now a universal finding across all 5 regimes, not one.**
Phase 8's Monte Carlo robustness analysis (120 draws/design, PCM
property/weather/demand/mains-temperature uncertainty, a real 10-year
historical weather ensemble) found that delivery-temperature reliability
is never a problem, but **regimes 0–3 are 0% temperature-safe across all
120 draws each** — never safe — and **regime 4 (the one climate mild
enough to be nominally safe, by a margin of just 0.009°C) is only 25%
safe** once real-world variability is applied. A follow-up direct test
confirmed the root cause is structural, not fixable by more PCM tuning:
these climates push tank water to 70–72°C on sunny days regardless of
PCM choice or mass, which is ~5–7°C above PCM's fixed 65°C material-
stability ceiling (10°C tighter than water's own 75°C scald limit) — even
the smallest possible PCM dose (8 capsules) already violates it by
thousands of hours per year in regimes 0–3 (`08_PHASE7_OPTIMIZATION.md`).
This is a genuine consequence of having no active high-temperature safety
shield anywhere in Phases 1–7's physics, not a bug — and it is now a
specified, non-optional, universal requirement (with a 3°C precautionary
guard band and a fully specified default reward function) in the
Objective 3 hand-off contract.

Both findings are the optimizer/analysis working correctly, not a defect
— exactly the kind of result Objective 2 exists to surface. See
`14_SELECTION_RULE_SCOPE_CORRECTION.md` for the full PCM-design story and
`OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` for what Objective 3 must do about
the safety finding.

## Documents in this folder

- `01_PHASE1_CONFIG_AND_STATE_SETUP.md` — frozen configs, per-state input file
- `02_PHASE2_GEOMETRY_CONSTRAINTS.md` — geometry engine, Ergun hydraulics, bounds finding
- `03_PHASE3_GREYBOX_SIMULATOR.md` — enthalpy model, energy balance, solver design + the energy-conservation bug that was found and fixed
- `04_PHASE4_VERIFICATION_GATES.md` — full Gate 1-5 methodology and results
- `06_PHASE5_DOE.md` — 215-case DOE sampling plan and result
- `07_PHASE6_SURROGATE.md` — surrogate features, models, hold-out accuracy
- `08_PHASE7_OPTIMIZATION.md` — optimization search, simulator confirmation, the (now-winning) PCM-vs-plain-tank finding
- `09_NEXT_STEPS.md` — the original PCM-design decision (RESOLVED — see status update at top)
- `10_PHASE8_ROBUSTNESS_HANDOFF.md` — Monte Carlo methodology (including the real 10-year historical weather ensemble), the temperature-safety finding, recommendation cards, Objective 3 contract
- `11_MULTIFIDELITY_SURROGATE.md` — Phase 6b's low-fidelity speedup and sample-efficiency experiment (stale, pre-dates today's revisions)
- `12_TM_TARGET_RETARGETING.md` — why and how `Tm_target_C` was re-derived from the tank's own behavior
- `13_DESIGN_BOUNDS_WIDENING.md` — why and how the PCM-volume design bounds were widened
- `14_SELECTION_RULE_SCOPE_CORRECTION.md` — why plain tank was removed from the final selection pool, and what it changed
- `OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` — what Objective 3 needs from this project and what to do first
- `plots/00_INDEX.md` and `plots/02_...` through `plots/08_...md` — the 18
  justification figures (interactive HTML + static PNG) for Phases 2-8,
  with what each one shows, what to infer, and how to explain it
- `HOW_TO_RUN.md` — exact commands to reproduce everything above (and whether any external simulator/MATLAB is needed — it isn't)
- `REFERENCES.md` — the project's frozen literature base, mapped per-phase
  to the specific design choice or finding each citation grounds (not
  just a flat bibliography)
- `../RESULTS.md` (project root) — the complete results digest for all 8 phases
- `../O2_Framework_Audit_Report_TamilNadu.md` (project root) — external-style
  audit report cross-referencing this project's methodology against
  published literature, phase-by-phase

## Literature

Every phase doc above has its own "Literature" section pointing at the
specific citations that ground its design choices; `REFERENCES.md` is the
single master list all of them link back to (frozen source:
`vertopal.com_references.txt`, project root). At the whole-project level,
worth calling out: **[Chen2025]** and **[Singh2025]** anchor the
collector/tank baseline and the Gate 4 benchmark band; **[Rubitherm2024]**/
**[PLUSS2024]** anchor every PCM material property in
`pcm_database_tamilnadu.csv` including the 65°C safety limit that turns
out to be the binding constraint behind Finding 2 above; **[Chopra2023]**
anchors the Monte Carlo robustness methodology (Phase 8); **[Sivaraj2023]**
and **[Emami2026]** anchor the Objective 3 hand-off's DRL framing.
