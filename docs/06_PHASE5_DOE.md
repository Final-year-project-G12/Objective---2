# 06 — Phase 5 Audit: Design-of-Experiments Dataset (All Four States)

Files: `src/doe/generate_cases.py` (byte-identical across states),
`run_batch.py`, `split_cases.py` (differ only in the simulator-version
tag, output path, and `n_lhs_per_pair`).

## Sampling plan and result, side by side

| | Tamil Nadu | Rajasthan | Assam | Uttarakhand |
|---|---|---|---|---|
| Regimes × PCMs (pairs) | 5 × 3 = 15 | 3 × 3 = 9 | 3 × 3 = 9 | 5 × 3 = 15 |
| LHS draws/pair | 8 | 12 | 12 | 8 |
| Boundary cases/pair | 6 | 6 | 6 | 6 |
| No-PCM baselines | 5 | 3 | 3 | 5 |
| **Total cases** | **215** | **165** | **165** | **215** |
| Valid (simulated) | 145 | 111 | 111 | 145 |
| Rejected (`bounds_violation`) | 70 (32.6%) | 54 (32.7%) | 54 (32.7%) | 70 (32.6%) |
| Train / holdout split | 170 / 45 | 138 / 27 | 138 / 27 | 170 / 45 |

**Rajasthan and Assam use 12 LHS draws/pair (not Tamil Nadu/Uttarakhand's
8)** because both have only 3 Level-A regimes (9 pairs, not 15) — 12/pair
lands their totals inside the framework's 150–300-case target the same
way 8/pair does for the 5-regime states. **The infeasibility rate is
essentially identical in all four states (32.6–32.7%)** — direct
confirmation that this rejection rate is a property of the frozen
geometry bounds alone (any `capsule_diameter_m` in `[0.02, 0.04)`
produces a derived thickness below the 0.02 m floor, ≈33% of the
diameter range), completely independent of climate or PCM shortlist —
see `02_PHASE2_GEOMETRY_CONSTRAINTS.md`.

## DOE-scale safety-limit finding, per state

| State | Valid cases exceeding 65 °C PCM limit | Valid cases exceeding 75 °C water limit |
|---|---|---|
| Tamil Nadu | not separately re-audited this pass; Gate 3/Phase 7 show PCM candidates fail safety in 4/5 regimes | 0 (not separately re-audited) |
| Rajasthan | **108 / 111 (97%)** | 0 |
| Assam | **79 / 111 (71%)** | 0 |
| Uttarakhand | not separately re-audited this pass; regime 0's *selected* plain tank alone is already marginally over 75°C (see `08_…`) | see previous column |

Rajasthan's near-universal overheating (108/111) reflects its hot-dry,
high-clearness climate against the frozen 1.5 m² collector / 50 L tank.
Assam's narrower but still substantial rate (79/111, entirely on the PCM
limit, never the water limit) reflects a cooler but still solar-rich
climate. Both figures were directly counted from each state's
`results/.../design_cases.csv`, not assumed to carry over from one
state to another — a useful methodological note for anyone extending
this table to Tamil Nadu/Uttarakhand.

## Literature review — why Latin Hypercube Sampling for the DOE

- **Latin Hypercube Sampling** (McKay, Beckman & Conover, 1979,
  `McKayBeckmanConover1979LHS`) is used over the design variables
  (diameter, flow, capsule count) because it guarantees each variable's
  marginal range is evenly stratified across the sample, which a
  comparably-sized simple random sample does not guarantee — important
  here because Phase 6's surrogate needs the DOE to cover the design
  space efficiently at only ~150–300 simulated cases per state (each
  case costs a full-year physics simulation, ~2–5 seconds), not the
  thousands a purely random or full-factorial design would need for
  comparable coverage.
- **Keeping infeasible (`bounds_violation`) rows in the dataset rather
  than discarding them** follows the framework doc's explicit
  requirement (§6.1–6.2) and is what makes Phase 6's feasibility
  classifier learnable at all — every state's ~100% feasibility-classifier
  accuracy (`07_PHASE6_SURROGATE.md`) depends on this design choice, since
  a classifier trained only on valid rows would never see a negative
  example.
- **Stratifying the train/holdout split by `(regime_id, pcm_id, valid)`**,
  not just `(regime_id, pcm_id)`, ensures the holdout set used to *report*
  the feasibility classifier's accuracy actually contains infeasible
  examples — a fix Tamil Nadu's own audit records as a bug found and
  corrected during Phase 5/6 development (the first `split_cases.py`
  version scored the classifier's infeasible-recall as `NaN`, since
  holdout had zero infeasible rows under the coarser stratification).
