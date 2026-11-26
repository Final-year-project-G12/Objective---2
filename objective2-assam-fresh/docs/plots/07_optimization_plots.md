# Phase 7 Plots — Optimization Pass (Rajasthan)

Files: `phase7_pareto_by_regime.*`, `phase7_surrogate_vs_simulator.*`,
`phase7_safety_compliance.*`. Data source:
`results/phase7_optimized_designs.csv` (all 60 simulator-confirmed
candidates) + `phase7_deployable_design_per_regime.csv` (the selection).

## Plot 1 — Useful energy vs PCM mass, all 60 confirmed candidates

**What it is**: one panel per regime (3 across), each plotting the
regime's confirmed candidates as (`sim_pcm_mass_kg`,
`sim_useful_energy_kWh`), coloured by PCM, with the selected deployable
design marked as a black star.

**What we infer**: in every regime the **star sits at x = 0 (zero PCM
mass), level with — or slightly below — the PCM cluster** on useful
energy. The PCM candidates are bunched a hair above the plain-tank
points, but the gap (≈0.1–0.15 %) is invisible against the chart's
y-range. This is the "plain tank wins all 3 regimes" result as a picture:
the PCM designs aren't meaningfully higher, and they cost PCM mass.

**How to justify it**: *"The star being at zero mass, right on top of the
PCM cloud, shows *why* the selection rule picked the plain tank —
equivalent useful energy at zero PCM mass. This communicates the result
better than a table of near-identical numbers."*

## Plot 2 — Surrogate-predicted vs simulator-confirmed useful energy

**What it is**: scatter of predicted (y) vs simulator-confirmed (x)
useful energy for all 60 candidates, with the y = x line.

**What we infer**: all 60 points are on the line — mean absolute error
0.03 %, 0/60 above the 15 % large-error rule. Independent confirmation
(beyond the Phase 6 hold-out R²) that surrogate, geometry engine and
simulator are self-consistent on designs the surrogate proposed.

**How to justify it**: *"The surrogate was only ever a proposal ranker
(Bug-Fix 5) — this plot shows it also happened to be accurate to 0.03 %
on 60 fresh designs, so the ranking it produced was trustworthy and the
simulator re-confirmation found no surprises."*

## Plot 3 — Temperature-safety compliance of confirmed candidates

**What it is**: a stacked bar per regime — green = candidates that meet
`meets_temperature_safety` (max water ≤ 75 °C, max PCM ≤ 65 °C, zero
year-round violations), red = candidates that violate it.

**What we infer**: **in every regime, only the 5 plain-tank candidates
are green; all 15 PCM candidates are red.** Across all 3 regimes that is
**15/15 plain-tank pass, 0/45 PCM pass**. Unlike Tamil Nadu, where one
regime's PCM candidates cleared safety, no Rajasthan PCM candidate does —
consistent with Phase 5's finding that every valid DOE case exceeded the
65 °C PCM limit.

**How to justify it**: *"This is the single clearest picture of the
Rajasthan Objective 2 conclusion: under the frozen collector/tank sizing,
no shortlisted PCM can stay inside the safety envelope, so the plain tank
isn't just cheaper at equal performance — it's the only family that's
safe. Phase 8's Monte Carlo then shows even the plain tank needs an
active bypass to be *robustly* safe."*
