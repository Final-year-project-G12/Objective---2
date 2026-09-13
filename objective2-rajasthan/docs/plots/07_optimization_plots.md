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

**What we infer (updated 2026-09-14 — safety shield + PCM-only selection
rule, see `docs/07_PHASE7_OPTIMIZATION.md`)**: in every regime the
**star now sits inside the PCM cluster, at a non-zero PCM mass**, level
with or slightly above the plain-tank point (x = 0) on useful energy. The
gap between plain tank and the winning PCM candidate (≈0.08–0.14 %) is
still invisible against the chart's y-range — the underlying physics
hasn't changed, PCM's energy edge over plain water is still a fraction
of a percent — but the star no longer sits at zero mass, because the
selection rule now excludes the plain tank from the winner pool and
picks among the PCM candidates instead.

**How to justify it**: *"The star sits inside the PCM cloud, not at zero
mass, because Objective 2's own selection rule only compares PCM designs
against each other for the final pick — the plain tank stays in this
chart as the diagnostic baseline it was always meant to be, but it isn't
eligible to be the star. The PCM candidates and the plain-tank point are
visually indistinguishable on the y-axis because the energy gap really is
that small (well under the 5% Pareto tolerance) — what decided the winner
wasn't a large energy difference, it's the tie-break rule (pump energy,
then PCM mass, then capsule count, then safety margin) applied to a
near-tied pool that, since 2026-09-13, all clears temperature safety
under the rule-based overheat shield."*

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

**What we infer (updated 2026-09-14)**: **every bar is now solid green —
all 60 confirmed candidates pass, in all three regimes (15/15 plain-tank
and 45/45 PCM).** This reverses the earlier unshielded-physics finding
(15/60 pass, all plain-tank, 0/45 PCM) once the rule-based overheat
safety shield became the pipeline default on 2026-09-13 (bypass at
72 °C water / 62 °C PCM). The chart's red segment, previously the
visual anchor for "no PCM clears the safety limit here," no longer
appears at all. (A prior version of this chart, generated before the
shield was the default, would have shown the earlier 15/60 split — see
`docs/09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md` §0/§6 for that
unshielded finding and its explicit "true of the unshielded physics"
qualifier.)

**How to justify it**: *"Every bar is fully green because the rule-based
overheat shield — stop the pump above 72 °C water, block PCM charging
above 62 °C, the exact mechanism IS 12976:2023 §8.2 cites as the
standard Indian overheat-protection method — is now the pipeline default
for every phase of this search, not a separate what-if. With the shield
protecting both design families equally, the safety filter stops
favouring the plain tank altogether; what decides the final pick is then
the (small but real) useful-energy edge PCM has over plain water, exactly
what Objective 2's own selection rule is designed to compare."*
