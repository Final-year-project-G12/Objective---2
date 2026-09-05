# Phase 5 Plots — Design-of-Experiments Dataset

Files: `phase5_doe_coverage.*`, `phase5_outcome_distribution.*`. Data
source: `results/tamilnadu/design_cases.parquet` (all 215 cases, read
directly — nothing recomputed).

---

## Plot 1 — DOE sample coverage

**What it is**: every one of the 215 DOE cases plotted as
`capsule_diameter_m` vs `flow_rate_kg_s`, colored green (valid) / red
(rejected), with marker shape distinguishing LHS draws (circle), boundary
cases (diamond), and baselines (star). Hover text (interactive version)
shows the exact `case_id` for any point.

**What we infer**: the red points cleanly occupy the `diameter < 0.04`
strip regardless of flow rate — the same boundary as the Phase 2 validity
map, now shown at actual DOE sample density rather than a full grid.
Green points span the whole rest of the diameter×flow rectangle with no
visible gaps, confirming the Latin Hypercube + boundary-case combination
achieved the space-filling coverage it was designed for (not clustered in
one corner).

**How to justify it**: *"This is the DOE we actually ran, not a diagram
of the sampling plan — every dot is a real case with a real `case_id` you
can look up in `design_cases.parquet`. The clean vertical split confirms
the 70/215 rejection count (Phase 5 doc) isn't randomly scattered bad luck
in the LHS draw; it's the same deterministic geometric boundary Phase 2
already established, now visible in the actual sampled data."*

---

## Plot 2 — Outcome distribution across 145 valid DOE cases

**What it is**: two histograms side by side — `useful_energy_kWh` and
`solar_fraction` — across every valid (simulated) DOE case.

**What we infer**: both distributions are smooth and multi-modal/spread
rather than a single spike — expected, since the 215 cases deliberately
span 5 climate regimes (different weather → different collector input)
crossed with different PCMs/geometries/flows. No case landed at zero or
some obviously-broken value (e.g., negative energy, solar fraction >1),
which would indicate a simulator crash silently producing garbage instead
of failing loudly.

**How to justify it**: *"This is a basic sanity check made visual: 145
independent physics simulations, none of them degenerate. If the
simulator had a bug that only manifested for certain geometries — say, a
divide-by-zero that got silently caught somewhere — you'd expect to see
a spike of identical or NaN-adjacent values in one of these histograms.
Instead the spread looks like what you'd expect from sweeping 5 different
climates and dozens of geometries."*
