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

**What we infer (updated 2026-09-14 — safety shield + PCM-only selection
rule, see `docs/08_PHASE8_ROBUSTNESS_HANDOFF.md`)**: the purple bars
(delivery temperature) sit at ~100% for every regime, and the blue bars
(demand) clear the 75% reference line in all three regimes (83–98%) —
neither of those changed. The green bars (temperature-safety) now tell a
completely different story from before: **all three sit at a flat 100%**,
at or above the 95% reference line, for all three regimes — every one of
Rajasthan's now-PCM deployable designs is robustly safe under weather,
demand and mains-temperature uncertainty. This reverses the earlier
45–57% result (kept below, not deleted) once the rule-based overheat
shield became the pipeline default and Phase 7's selection rule was
corrected to let PCM win outright rather than being tie-broken away by a
still-eligible plain tank.

**How to justify it**: *"Every regime in this chart is now a shortlisted
PCM design, each protected by the same rule-based overheat shield — stop
the pump above 72 °C water, block PCM charging above 62 °C — that IS
12976:2023 §8.2 cites as the standard Indian method for SWH overheat
protection. That the green bars sit at a clean 100% here, versus 45–57%
before the shield was the pipeline default, is the single clearest
before/after picture of what the shield buys: it isn't a PCM-specific
fix, it protects the same water/PCM interface regardless of which design
is installed, which is exactly why the earlier plain-tank-only chart
looked just as unsafe."*

---

### Superseded result (unshielded physics / pre-2026-09-14 selection rule — kept for the record, not deleted)

Before the shield was the pipeline default and before the plain tank was
excluded from the Phase 7 winner pool, every Rajasthan deployable design
was the plain (sensible-only) tank, and its robustness was: the green
bars (temperature-safety) sat at **45–57% across all three regimes —
every single one roughly half the height of the 95% reference line**,
with regime 1 the shortest of the three. Unlike Tamil Nadu (where the
PCM regime was the visibly worst performer on both axes at once),
Rajasthan's three bars were close to each other — that was the plain
tank alone failing safety in a hot-dry climate, not a PCM-specific
problem: there was no PCM bar in the chart at all, so the failure clearly
belonged to the climate/collector-sizing combination, not to any one
design choice. This was the finding that originally motivated framing an
active overheat bypass as an Objective 3 requirement.

---

## Plot 2 — Useful-energy 5th–50th–95th percentile interval per regime

**What it is**: a horizontal interval (5th to 95th percentile of useful
energy across the 120 draws) per regime, with a filled circle marking
the median (P50) and a black diamond marking that regime's single
nominal (unperturbed) Phase 7 value.

**What we infer (updated 2026-09-14)**: every nominal diamond falls
inside its own regime's interval, close to the median circle —
confirming the nominal design point Phase 7 selected is representative
of its own uncertainty distribution, not a lucky-draw outlier. Regime 1
still has both the highest median useful energy (1650 kWh) and the
widest interval of the three — consistent with it also having the
highest nominal energy in Phase 7's own table (its
`configs/states/rajasthan.yaml` label is "hot, monsoon-influenced, steady
solar" — a steadier collector input than the other two "cooler arid /
erratic solar" regimes). Unlike the earlier unshielded reading, this no
longer trades off against safety: with the shield now the pipeline
default, regime 1 has the *most* useful energy **and** a clean 100%
temperature-safe record on Plot 1, at the same time — the shield caps the
same high-temperature tail regardless of how sunny the regime is, so more
solar input now shows up entirely as more useful energy rather than partly
as more safety violations.

**How to justify it**: *"This is a sanity check on the nominal number
itself: if the diamond sat at the extreme edge of its own interval, or
outside it, that would suggest Phase 7's single-weather-year result was
an outlier rather than a representative performance estimate. It
doesn't — every diamond sits inside its interval, close to the median —
so quoting the Phase 7 nominal number as 'the' expected performance for
that regime is defensible, not cherry-picked. Read alongside Plot 1, it
also shows the shield working as intended: regime 1's higher energy no
longer comes bundled with worse safety, because the shield puts a hard
ceiling on the temperature excursions that used to explain that
trade-off."*
