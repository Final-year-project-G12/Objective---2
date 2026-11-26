# Phase 5 Plots — DOE Dataset (Rajasthan)

Files: `phase5_doe_coverage.*`, `phase5_outcome_distribution.*`. Data
source: `results/phase5_design_cases.parquet` (all 165 cases).

## Plot 1 — DOE sample coverage (165 cases)

**What it is**: every one of the 165 DOE cases plotted as
(`capsule_diameter_m`, `flow_rate_kg_s`), coloured green (valid) / red
(rejected `bounds_violation`), with marker shape by sampling method
(circle = LHS, diamond = boundary, star = baseline).

**What we infer**: the LHS points fill the diameter×flow rectangle
evenly (space-filling design working as intended), and **every red point
sits at `capsule_diameter_m < 0.04 m`** — a clean vertical cut, not
scattered failures. So the 54/165 rejection count (Phase 5 doc) is one
deterministic geometric rule (derived thickness < the 0.02 m floor), the
same rule Plot 1 of `02_geometry_plots.md` shows.

**How to justify it**: *"The rejections aren't random bad luck — they're
a straight line at diameter = 0.04 m, exactly the thickness-bound edge.
The 54/165 ≈ 32.7 % rate matches the fraction of the sampled diameter
range that lies below 0.04 m, which is itself a small sanity check that
nothing else is silently rejecting cases."*

## Plot 2 — Outcome distribution across 111 valid DOE cases

**What it is**: two histograms — `useful_energy_kWh` and `solar_fraction`
across the 111 valid cases.

**What we infer**: both are smooth spreads (not a single spike, not
bimodal-degenerate) — expected, since the 165 cases deliberately span 3
climate regimes × 6 PCMs + baselines × the full geometry range. Useful
energy clusters by regime; solar fraction sits in a narrow ~0.53–0.59
band, consistent with the Phase 4 Gate 3 finding that a single PCM's
marginal effect on annual solar fraction is small at reachable PCM
fractions.

**How to justify it**: *"A smooth, sensible spread — not clustered or
degenerate — is what tells you the DOE actually explored the design space
and the simulator responds continuously to the inputs. The narrow solar-
fraction band is the same 'PCM choice barely moves annual performance'
story, seen across 111 cases instead of one comparison."*
