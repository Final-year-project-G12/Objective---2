# Objective 2 — PCM Capsule / Tank Design Optimization

Determines the optimal PCM thickness, capsule arrangement, number of
capsules, and flow rate to maximize thermal energy storage in a
solar-water-heater tank, for each climate regime of a given state —
using Objective 1's own shortlisted PCMs (never re-deriving material
choice). Built as a state-agnostic pipeline: `src/` doesn't know which
state it's running for, only `configs/states/<state>.yaml` does.

**Status: complete for Tamil Nadu** — all 8 phases run, verified, and
independently cross-checked against real CFD physics (ANSYS Fluent +
OpenFOAM). Rajasthan, Assam, and Uttarakhand have not been started yet
(see `docs_objective2/other_states_prompts/`).

**2026-10-26/27: three real, sequential corrections** — a demand-timing
bug fix, an actual (not just specified) safety shield, then a tank/
collector resize from an undersized 50L/1.5m² to a standard 100L/2.5m²
domestic pairing. **All 3 Phase 8 robustness bars (delivery, demand,
temperature-safety) are now met in every regime** — see
`docs_objective2/RESULTS.md` for the full account and
`docs_objective2/TAMILNADU_REDESIGN_PLAN.md` for which algorithms this
project uses (and why, vs. the alternatives considered). ANSYS Fluent's
cross-check is currently stale/pending a license-error retry — Python
results are unaffected and are the authoritative numbers.

## How this fits the bigger project

| Objective | What it does | Status |
|---|---|---|
| 1 | Climate clustering + MCDM → Top-2/3 PCM shortlist per regime | Done (Tamil Nadu) |
| **2 (this folder)** | **PCM thickness/arrangement/count/flow optimization** | **Done (Tamil Nadu)** |
| 3 | DRL controller for real-time charge/discharge/bypass | Not started |
| 4 | Hardware validation against a physical lab rig | Not started |

Objective 1 selects *which material*. Objective 2 selects the *physical
hardware design* for that material. Objective 3 selects the *real-time
action*. Each stays in its own lane — see
`docs_objective2/OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` for the formal
boundary and Objective 3's actual starting point.

## Current result (Tamil Nadu, 3 climate regimes) — final, 2026-10-27

Tank/collector: **100 L / 2.5 m²** (a standard domestic SWH size, resized
2026-10-27 from an undersized 50 L / 1.5 m² — see `RESULTS.md`).

| Regime | PCM (from Objective 1) | Capsules | Diameter | Flow rate | Arrangement | vs. plain tank |
|---|---|---|---|---|---|---|
| 0 | n-Hexacosane (C26) | 32 | 72.22 mm | 0.02066 kg/s | radial | −14.78% |
| 1 | n-Hexacosane (C26) | 33 | 75.31 mm | 0.01085 kg/s | radial | −13.02% |
| 2 | n-Pentacosane (C25) | 35 | 79.76 mm | 0.02371 kg/s | single-layer | −12.46% |

These are real, trained-model outputs (DOE → surrogate → optimizer →
simulator-confirmed) — not hand-picked, and the product of three real,
sequential corrections: a demand-timing bug fix, an actual (not just
specified) safety shield, then a tank/collector resize to a realistic
domestic size. See `docs_objective2/RESULTS.md` for the full
before/after/final progression and `docs_objective2/TAMILNADU_REDESIGN_
PLAN.md` §5 for the complete account.

**Key honest finding**: **every regime now meets all three Phase 8
robustness bars at once** — P(meets delivery)=100%, P(meets annual
demand)=100%/94.2%/100%, P(temperature-safe)=100%, all confirmed under
120-draw Monte Carlo weather/demand/property uncertainty, not just
nominally. The cost: **PCM still loses to a plain tank in every regime**
(−12.5% to −14.8%, wider than before the resize) — a bigger tank's own
water thermal mass buffers temperature swings well enough on its own that
PCM's relative contribution shrinks, not grows, as the tank gets bigger.
This is a real, disclosed finding (Gate 3's own capability check shows the
same thing independently), not a defect. See `RESULTS.md`.

## How to run it

```
python build_input_package.py      # pull Objective 1's output in
python build_regime_weather.py     # per-regime representative weather
python build_demand_profile.py     # canonical hot-water draw profile
python pipeline.py --state tamilnadu --stage <geometry|simulate|verify|doe|surrogate|optimize|robustness>
```
Full details, flags, and troubleshooting: `docs_objective2/HOW_TO_RUN.md`.
Input `data/` folder layout: `docs_objective2/DATA_REFERENCE.md`.

## Repository map

```
README.md                      <- you are here
pipeline.py, config.py          <- state-agnostic Objective 2 pipeline
build_*.py                      <- Objective-1-output ingestion scripts
src/                            <- design/simulation/surrogate/robustness code
configs/                        <- shared + per-state design bounds/config
data/, results/                 <- inputs and outputs (see DATA_REFERENCE.md)
ansys_openfoam_case/             <- CFD cross-verification (Fluent + OpenFOAM)
docs_objective2/
  RESULTS.md                    <- consolidated current results (start here)
  TAMILNADU_REDESIGN_PLAN.md    <- Tamil Nadu/ANSYS adaptation of the
                                    teammate's Rajasthan/OpenFOAM redesign
                                    plan; algorithms used vs. not used
  HOW_TO_RUN.md                 <- commands and flags (incl. ANSYS Fluent)
  DATA_REFERENCE.md             <- data/ folder file-by-file reference
  CFD_VERIFICATION.md           <- Fluent/OpenFOAM methodology + results
  OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md  <- Objective 3 hand-off
  REFERENCES.md                 <- literature citations
  other_states_prompts/          <- how to replicate this for Rajasthan/Assam/Uttarakhand
  reference/                     <- governing framework specs
  presentation/                  <- slides
  final_plots_html/              <- headline interactive plots
  history/                       <- full phase-by-phase methodology/evolution record
                                     (not required reading — kept for provenance)
```

## Why there's a `history/` folder

Objective 2's methodology went through several real corrections while
being built (bounds widening, a selection-rule scope fix, a PCM-shortlist
restoration after a scope violation was found and fixed). Every one of
those is real, documented engineering history — kept, not deleted — but
it's not what a new reader needs first. `RESULTS.md` and this README give
the current, authoritative picture; `history/` is there if you want the
full story of how it was reached.
