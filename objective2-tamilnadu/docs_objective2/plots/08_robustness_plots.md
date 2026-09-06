# Phase 8 Plots — Robustness & Objective 3 Hand-off

Files: `phase8_robustness_probabilities.*`, `phase8_useful_energy_intervals.*`.
Data source: `results/tamilnadu/robustness_summary.csv` (5 rows, one per
regime, each aggregating 120 real Monte Carlo simulator re-runs) and
`deployable_design_per_regime.csv` for the nominal reference point.

*(Methodology note: thresholds and weather-noise model were revised to
align with the parallel Rajasthan implementation of this framework — see
`docs_objective2/10_PHASE8_ROBUSTNESS_HANDOFF.md`, "Alignment with the
Rajasthan implementation." Both plots below reflect the current, aligned
methodology.)*

---

## Plot 1 — Robustness probabilities per regime

**What it is**: three bars per regime — P(meets delivery temperature,
`solar_fraction≥0.45`), P(meets annual demand, `solar_fraction≥0.50`,
both fixed thresholds), and P(temperature-safe) — with the framework's
75% demand and 95% temperature-safety thresholds marked as reference
lines.

**What we infer**: the purple bars (delivery temperature) sit at 100% for
every regime — that was never at risk anywhere. The blue bars (demand)
now show real variation, because the threshold is fixed rather than
self-referential: 85–96% for the four plain-tank regimes, but only
**70%** for regime 4 — the one PCM regime, and the only one that dips
below the 75% demand line. The green bars (temperature-safety) tell a
starker story: 67–87% for the plain-tank regimes, down to **44%** for
regime 4 — every single regime below the 95% line, and regime 4 the
furthest below both of its thresholds simultaneously. Regime 4's bars
being the shortest on *both* the blue and green metrics, at the same
time, is the single most visually obvious feature of the chart.

**How to justify it**: *"Before this chart existed, using a
self-referential threshold, every regime scored a trivial 100% on
demand — that hid a real difference between regimes. Switching to a
fixed, state-independent threshold is what makes this comparable to the
parallel Rajasthan analysis, and it's what reveals that regime 4 isn't
just 'the PCM regime with a safety problem' — it's the worst-performing
regime in the state on reliability of any kind, PCM or not. That's a
sharper, more defensible claim than the temperature-only story alone,
and you can see both bars failing together in the same regime, not just
read it off two separate numbers."*

---

## Plot 2 — Useful-energy 5th–50th–95th percentile interval per regime

**What it is**: a horizontal interval (5th to 95th percentile of useful
energy across the 120 draws) per regime, with a filled circle marking
the median (P50) and a black diamond marking that regime's single
nominal (unperturbed) Phase 7 value.

**What we infer**: every nominal diamond falls inside its own regime's
interval, close to (though not always exactly on top of) the median
circle — confirming the nominal design point Phase 7 selected is
representative of its own uncertainty distribution, not a lucky-draw
outlier. Regime 4 (the PCM regime) has both the lowest interval and the
narrowest one of all five regimes — consistent with it also being the
lowest-nominal-energy regime in Phase 7's own table, and with it being
the design most exposed to the demand/safety shortfalls in Plot 1.

**How to justify it**: *"This is a sanity check on the nominal number
itself: if the diamond sat at the extreme edge of its own interval, or
outside it, that would suggest Phase 7's single-weather-year result was
an outlier rather than a representative performance estimate. It
doesn't — every diamond sits inside its interval, close to the median —
so quoting the Phase 7 nominal number as 'the' expected performance for
that regime is defensible, not cherry-picked. The median marker also lets
you check whether the distribution is skewed — most regimes show the
median close to, but not exactly on, the nominal value, which is
expected: the nominal case IS the median scenario approximately, not by
construction."*
