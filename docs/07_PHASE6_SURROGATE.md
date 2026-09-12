# 07 — Phase 6 Audit: AI Surrogate Model (All Four States)

Files: `src/surrogate/features.py`, `train.py`, `evaluate.py` (same
model family/hyper-parameters across states; `features.py` remaps
column names per state's own Objective 1 table headers).

## Hold-out accuracy side by side (ExtraTrees, `useful_energy_kWh`)

| State | Features | Train / holdout (valid rows) | ExtraTrees R² | Linear R² | Tree beats linear? |
|---|---|---|---|---|---|
| Tamil Nadu | 36 | 115 / 30 | 0.9999 | 0.9999 | Yes |
| Rajasthan | 39 | 93 / 18 | 0.99983 | 0.99988 | No (tie) |
| Assam | **29** | 93 / 18 | 0.9977 | 0.9981 | No (tie) |
| Uttarakhand | 36 | 115 / 30 | 0.99989 | 0.99983 | Yes |

Every state clears the framework's >0.80 exit target with a wide margin.
**Assam's feature count (29) is the lowest of the four** — its Objective
1 climate table lacks the finer breakdown (separate `Ta_p95`/`Ta_p05`,
sunrise-specific RH/HSI, noon-specific wind, CDD/HDD, `kt_daily_mean`,
`cloudy_frac`) the other three states' tables carry, a genuine
Objective-1-table difference rather than a code change. **Rajasthan's
feature count (39) is the highest** — its table has *more* climate
columns than the shared baseline (adds CDD18/24, HDD18, `kt_daily_mean`,
`cloudy_frac`).

## Feasibility classifier — identical result in every state

100% hold-out accuracy, 100% infeasible-recall, in all four states —
expected, not suspicious, since the feasibility boundary is the same
single sharp deterministic rule everywhere (`capsule_diameter_m < 0.04 m`
→ derived thickness below floor, see `02_…`/`06_…`), trivially learnable
by a 300-tree ensemble given ~15–45 infeasible holdout examples per
state.

## `pump_energy_kWh` — the one target where states disagree on tree-vs-linear

| State | ExtraTrees R² | Linear R² | Winner |
|---|---|---|---|
| Tamil Nadu | 0.9872 | 0.99992 | Linear |
| Rajasthan | 0.326 | 0.99983 | Linear (tree much worse) |
| Assam | **0.8819** | 0.3849 | **Tree much better** |
| Uttarakhand | 0.9535 | 0.99995 | Linear |

Assam is the outlier — three states show linear regression matching or
beating the tree on this near-numerical-noise target (pump energy is
~1e-9 kWh at these sparse-bed flow rates, close to floating-point noise
either way), while Assam's tree fits this noise better than its own
linear baseline. This is not a contradiction in the methodology, just a
reminder that "which model wins on a near-null-signal target" is itself
close to noise and shouldn't be over-interpreted in any state.

## Literature review — why ExtraTrees, and why compare against a linear baseline

- **Extremely Randomized Trees** (Geurts, Ernst & Wehenkel, 2006,
  `Geurts2006ExtraTrees`) are used as the surrogate family because they
  add an extra layer of randomization over standard Random Forests
  (Breiman, 2001, `Breiman2001RandomForests`) — splitting thresholds are
  drawn randomly rather than optimized — which typically reduces
  variance further on small-to-moderate tabular datasets like this
  project's ~100–150 valid training rows per state, at negligible bias
  cost, without requiring the hyperparameter tuning a gradient-boosted
  tree family (e.g. XGBoost) would need to avoid overfitting at this
  sample size.
- **Reporting a linear-regression baseline honestly, including when it
  wins**, follows directly from the framework doc's explicit instruction
  to run this comparison and report it as-is rather than only showing
  the metric that flatters the tree model. All four states' docs report
  at least one target where linear ties or wins — this is treated as
  evidence the reported physics in this design region is close to linear
  in the sampled variables (e.g. `pcm_mass_kg` is exactly linear in
  `n_capsule·diameter³·ρ`), not as a surrogate failure.
- **scikit-learn** (Pedregosa et al., 2011, `Pedregosa2011ScikitLearn`) is
  the implementation library for every model in this phase (ExtraTrees,
  linear regression, the feasibility classifier) across all four states
  — a standard, widely-validated, open-source ML toolkit appropriate for
  reproducible student-project work.
- **The surrogate is a proposal ranker, never the final oracle, in every
  state** (Bug-Fix 5) — every design it favors is re-run in the real
  simulator in Phase 7 before being reported anywhere. This mirrors the
  explicit caution in Barqawi et al. (2025) and Assareh et al. (2023)
  against trusting an ML surrogate's prediction as ground truth for a
  physical PCM-SWH design without simulator (or experimental)
  confirmation.
