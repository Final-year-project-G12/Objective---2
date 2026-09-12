# 08 — Phase 7 Audit: Optimization Pass + Simulator Confirmation (All Four States)

Files: `src/optimize/search.py`, `src/optimize/select_deployable.py` —
used as-is by Tamil Nadu, Rajasthan, and Uttarakhand. **Assam used a
different, bespoke script instead** (`scripts/run_phase7_optimization.py`)
— see the dedicated section below before citing any Assam number here.

## Method — three states, one shared approach

1. **Search**: 400 random candidate design vectors per regime×PCM pair,
   filtered through the real Phase 2 geometry gate, scored by the Phase
   6 surrogate. Top 5/pair kept.
2. **Confirm**: every kept candidate re-run in the **real simulator**
   (never a surrogate-only number). Surrogate-vs-simulator error logged;
   >15% error → trust the simulator, log the mismatch.
3. **Select**: reject temperature-unsafe → keep everything within 5% of
   the regime's best useful energy → minimize pump energy, then PCM
   mass, then capsule count → prefer larger constraint margin as the
   final tie-break (`system_config_shared.yaml`'s
   `selection.pareto_tolerance_pct = 5%`).

## Result side by side

| | Tamil Nadu | Rajasthan | Assam (bespoke method, unvalidated) | Uttarakhand |
|---|---|---|---|---|
| Candidates searched | 400/pair × 20 pairs = 8,000 | 400/pair × 12 pairs = 4,800 | **1,000/pair × 12 pairs = 12,000** | 400/pair × 20 pairs = 8,000 |
| Candidates simulator-confirmed | 100 | 60 | **5** (of 21 "top" candidates) | 100 |
| Mean surrogate-vs-sim error | 0.02% | 0.025% | 0.00–0.51% | 0.02–0.05% |
| Plain tank selected | 4/5 regimes | **3/3 regimes** | **0/3 (as reported)** | 4/5 regimes |
| PCM selected | 1/5 (regime 4, n-Octacosane) | 0/3 | **3/3 (as reported)** | 1/5 (regime 2, PureTemp 58) |
| PCM candidates passing the 65°C/75°C safety filter | 15/80 (all regime 4) | **0/45** | reported as 3/3 "PASSED" against a **wrong threshold** — actually 0/3 | subset (regime 2 passes; regimes 0/3 PCM candidates fail) |

## Assam: the safety-verdict bug (read before citing anything from Assam's Phase 7)

`system_config_shared.yaml` sets `max_water_temp_C: 75.0` and
`max_pcm_temp_C: 65.0` — identical in all four states.
`scripts/run_phase7_optimization.py` (Assam's actual Phase 7 script)
correctly computes each candidate's margin against these real limits
(`water_temp_safety_margin_C`, `pcm_temp_safety_margin_C`), and those
margins are **negative for all 3 of Assam's selected designs**
(−1.21, −2.95, −5.09 °C, with 13/313/215 logged safety violations
respectively) — but `results/phase7_optimization_report.md`'s printed
verdict table checks those margins against a **different, hardcoded,
undocumented 90 °C PCM / 95 °C water standard** instead, and prints
"PASSED" without checking the sign of the real margin it already
computed two sections earlier in the same script. This is a bug in the
report-generation code, not a deliberate, justified relaxation of the
safety limit — nothing in `system_config_shared.yaml` or any Assam
config file documents a 90 °C/95 °C standard.

**Practical consequence**: Assam currently has **no Phase-7-validated
deployable design** under this project's own pre-declared safety rule.
Given Assam's DOE-scale finding that 79/111 (71%) of valid Phase 5 cases
already exceed 65 °C (`06_PHASE5_DOE.md`) and Gate 3's finding that even
a matched-Tm synthetic PCM loses to plain water there (`04_…`), the most
likely outcome of a corrected re-run is the plain tank winning in some or
all 3 regimes — consistent with Rajasthan's outcome under the same rule.
See `objective2-assam/docs/07_PHASE7_OPTIMIZATION.md` for the full trace.

## Uttarakhand: regime 0's selected design is itself marginally unsafe

Not a bug, but worth stating plainly: regime 0's selected plain tank
(`deployable_design_per_regime.csv`) has `meets_temperature_safety=False`
and `constraint_margin_C=-0.137` (max water 75.14 °C, 0.14 °C over the
75 °C limit, 1 flagged violation) — the selection rule's "no candidate
met the safety rule; widen to all confirmed candidates" fallback fired
for that regime because *every* candidate tried, PCM or plain, failed
the nominal safety check. This directly explains why regime 0 has the
worst Phase 8 temperature-safety probability (44.2%) of Uttarakhand's
five regimes — see `objective2-uttarakhand/docs_objective2/08_PHASE7_OPTIMIZATION.md`
and `10_PHASE8_ROBUSTNESS_HANDOFF.md`.

## The consistent, properly-validated finding (Tamil Nadu, Rajasthan, Uttarakhand)

Best PCM found beats best plain tank found by 0.07–0.15% at its
best-found geometry, in every regime of every properly-validated
state — two orders of magnitude below the pre-declared 5% Pareto
tolerance. PCM wins outright (before any tolerance tie-break) only where
the climate keeps the tank cold enough for the PCM to actually cycle
(Tamil Nadu regime 4, Uttarakhand's coldest regime 2) or never at all
(Rajasthan, where the climate is too hot for any shortlisted PCM to stay
under 65 °C). This is the optimizer and the temperature-safety filter
both working as designed, confirmed independently at Gate 3 (two
hand-picked designs), Phase 5 (the full DOE), and Phase 7 (a
400-candidate-per-pair search) in each state.

## Literature review — why a single search pass + simulator re-confirmation, not full NSGA-II

- **A single 400 (or, for Assam, 1,000)-candidate-per-pair random search,
  scored by a validated surrogate and re-confirmed in the real
  simulator**, is a deliberately reduced substitute for a full
  active-learning or multi-objective genetic-algorithm loop (e.g.
  NSGA-II), consistent with the framework's stated 40-hour-per-state
  scope. The surrogate-vs-simulator error rates achieved (0.02–0.51%
  across all four states) indicate the surrogate is smooth and accurate
  enough in this design region that a single random-search pass finds
  designs close to what a more expensive iterative scheme would likely
  find, though this is not proven by running the more expensive
  alternative.
- **The "5% Pareto tolerance, then minimize mass/pump/capsules" selection
  rule** operationalizes a standard engineering heuristic — when two
  designs are statistically indistinguishable on the primary objective
  (useful energy), prefer the cheaper/simpler one — the same logic
  Assareh et al. (2023) and Chen et al. (2025) apply when trading off
  multiple PCM-SWH design objectives rather than optimizing a single
  scalar in isolation.
- **The pre-declared, hard temperature-safety filter** (max water 75 °C,
  max PCM 65 °C, zero per-substep violations) reflects the same
  materials-stability concern Rubitherm's and PLUSS's own PCM datasheets
  document for their RT- and OM-series products (`RubithermPCM`,
  `PlussPCM`) — a melted-and-refrozen PCM repeatedly driven well past its
  rated stability temperature is a real degradation risk, not merely an
  arbitrary simulation cutoff.
