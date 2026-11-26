# Phase 8 Plots — Robustness & Objective 3 Hand-off

Files: `phase8_robustness_probabilities.*`, `phase8_useful_energy_intervals.*`.
Data source: `results/phase8_robustness.csv` (3 rows, one per regime, each
aggregating 120 real Monte Carlo simulator re-runs) and
`phase7_deployable_design_per_regime.csv` for the nominal reference point.

*(Ported from `objective2-tamilnadu/docs_objective2/plots/08_robustness_plots.md`
— same two figures, same methodology, Rajasthan's 3-regime data and
column names. See `docs/08_PHASE8_ROBUSTNESS_HANDOFF.md`, "Alignment with
the Tamil Nadu implementation," for how the two states' Phase 8 passes
converged on one shared methodology.)*

---

## Plot 1 — Robustness probabilities per regime

**What it is**: three bars per regime — P(meets delivery temperature,
`solar_fraction≥0.45`), P(meets annual demand, `solar_fraction≥0.50`,
both fixed thresholds), and P(temperature-safe) — with the framework's
75% demand and 95% temperature-safety thresholds marked as reference
lines.

**What we infer**: the purple bars (delivery temperature) sit at 100% for
every regime — that was never at risk anywhere. The blue bars (demand)
clear the 75% reference line in all three regimes (80–99%), with regime 2
closest to the line at 80%. The green bars (temperature-safety) tell a
starker story: **45–57% across all three regimes — every single one
roughly half the height of the 95% reference line**, with regime 1 the
shortest of the three. Unlike Tamil Nadu (where the PCM regime is the
visibly worst performer on both axes at once), Rajasthan's three bars are
close to each other — this is the plain tank alone failing safety in a
hot-dry climate, not a PCM-specific problem, and the chart makes that
visually obvious: there is no PCM bar to contrast against, so the eye
reads the failure as belonging to the *climate/collector-sizing
combination*, not to any one design choice.

**How to justify it**: *"Every regime in this chart is a plain
sensible-water tank — there is no PCM anywhere in Rajasthan's deployable
designs. That the green bars are still this short (45–57%, against a 95%
target) tells you the safety problem here isn't about PCM sizing at all;
it's that a 1.5 m² collector on a 50 L tank in Rajasthan's hot-dry climate
routinely overheats the water itself, with or without PCM in it. That's a
sharper, more general claim than 'the PCM design has a safety issue' —
it's a claim about the frozen collector/tank sizing meeting this specific
climate, which is exactly why Objective 3's safety shield has to protect
every regime, not just a PCM-bearing one."*

---

## Plot 2 — Useful-energy 5th–50th–95th percentile interval per regime

**What it is**: a horizontal interval (5th to 95th percentile of useful
energy across the 120 draws) per regime, with a filled circle marking
the median (P50) and a black diamond marking that regime's single
nominal (unperturbed) Phase 7 value.

**What we infer**: every nominal diamond falls inside its own regime's
interval, close to the median circle — confirming the nominal design
point Phase 7 selected is representative of its own uncertainty
distribution, not a lucky-draw outlier. Regime 1 has both the highest
median useful energy (1664 kWh) and the widest interval of the three —
consistent with it also having the highest nominal energy in Phase 7's
own table (its `configs/states/rajasthan.yaml` label is "hot,
monsoon-influenced, steady solar" — a steadier collector input than the
other two "cooler arid / erratic solar" regimes) — and its position
doesn't correlate with its Plot-1
safety ranking: regime 1 has the *most* useful energy and the *worst*
temperature safety at the same time, because both are driven by the same
underlying cause — a hotter, more consistently sunny regime delivers more
useful energy and pushes the tank over its safety limit more often, in
the same direction.

**How to justify it**: *"This is a sanity check on the nominal number
itself: if the diamond sat at the extreme edge of its own interval, or
outside it, that would suggest Phase 7's single-weather-year result was
an outlier rather than a representative performance estimate. It
doesn't — every diamond sits inside its interval, close to the median —
so quoting the Phase 7 nominal number as 'the' expected performance for
that regime is defensible, not cherry-picked. Read alongside Plot 1, it
also makes the underlying mechanism visible: regime 1's higher energy and
worse safety numbers are two symptoms of the same cause (a hotter, sunnier
regime), not two independent problems."*
