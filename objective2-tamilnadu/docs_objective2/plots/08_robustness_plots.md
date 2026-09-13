# Phase 8 Plots — Robustness & Objective 3 Hand-off

Files: `phase8_robustness_probabilities.*`, `phase8_useful_energy_intervals.*`.
Data source: `results/tamilnadu/robustness_summary.csv` (5 rows, one per
regime, each aggregating 120 real Monte Carlo simulator re-runs) and
`deployable_design_per_regime.csv` for the nominal reference point.

*(Methodology note: thresholds and weather-noise model were revised to
align with the parallel Rajasthan implementation of this framework, the
annual weather-noise component draws from a real 10-year (2016-2025)
historical weather ensemble, and — most consequentially for what these
plots now show — all 5 designs evaluated below are genuine PCM designs,
not four plain-tank plus one PCM. See `docs_objective2/
10_PHASE8_ROBUSTNESS_HANDOFF.md` and `14_SELECTION_RULE_SCOPE_
CORRECTION.md`.)*

---

## Plot 1 — Robustness probabilities per regime

> **Note (2026-09-13):** the P(temperature-safe) bar has been removed
> from this chart at the user's request. Temperature-safety numbers are
> not dropped from the project — they are still fully computed and
> reported in `robustness_summary.csv`, `10_PHASE8_ROBUSTNESS_HANDOFF.md`,
> `RESULTS.md`, and the Objective 3 hand-off contract (0% for regimes
> 0–3, 25% for regime 4) — only removed from *this specific figure*,
> which now shows delivery/demand reliability only.

**What it is**: two bars per regime — P(meets delivery temperature,
`solar_fraction≥0.45`) and P(meets annual demand, `solar_fraction≥0.50`,
both fixed thresholds) — with the framework's 75% demand threshold marked
as a reference line.

**What we infer**: the purple bars (delivery temperature) sit at 100% for
every regime — that was never at risk anywhere. The blue bars (demand)
show real variation: 80.8–98.3% for regimes 0–3, 73.3% for regime 4 (the
only one below the 75% line).

**How to justify it**: *"This chart isolates delivery and demand
reliability, which is where the real inter-regime variation is once
temperature safety is reported separately (see `robustness_summary.csv` /
`10_PHASE8_ROBUSTNESS_HANDOFF.md` for that number). Regime 4 is the only
one to miss the 75% demand bar; every other regime clears both bars shown
here comfortably."*

---

## Plot 2 — Useful-energy 5th–50th–95th percentile interval per regime

**What it is**: a horizontal interval (5th to 95th percentile of useful
energy across the 120 draws) per regime, with a filled circle marking
the median (P50) and a black diamond marking that regime's single
nominal (unperturbed) Phase 7 value.

**What we infer**: every nominal diamond falls inside its own regime's
interval, close to the median circle — confirming each PCM design's
nominal Phase 7 value is representative of its own uncertainty
distribution, not a lucky-draw outlier. Regime 4 has both the lowest and
narrowest interval of the five — consistent with it also being the
lowest-nominal-energy regime and the design operating closest to its own
safety limit (a margin of just 0.009°C nominally).

**How to justify it**: *"This is a sanity check on the nominal number
itself, independent of the safety story in Plot 1: every diamond sits
inside its own interval, close to the median, so quoting each regime's
Phase 7 nominal energy value as 'the' expected performance is defensible
— the useful-energy side of these designs is stable under uncertainty
even though the temperature-safety side (Plot 1) is not. That distinction
matters: this isn't a design that performs unpredictably; it's a design
that performs predictably well on energy and predictably poorly on
safety, which is a more precise, more actionable finding for Objective 3
than 'this design is unreliable' would be."*

## Literature

See `10_PHASE8_ROBUSTNESS_HANDOFF.md`'s "Literature" section. Most
directly relevant here: **[Chopra2023]** grounds the Monte Carlo
methodology producing these probability/interval plots; **[Rubitherm2024]**
is again the datasheet source of the 65°C limit driving the
temperature-safety collapse shown in Plot 1.
