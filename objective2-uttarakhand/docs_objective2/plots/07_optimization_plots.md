# Phase 7 Plots — Optimization Pass & Simulator Confirmation

Files: `phase7_pareto_by_regime.*`, `phase7_surrogate_vs_simulator.*`,
`phase7_safety_compliance.*`.
Data source: `results/uttarakhand/optimized_designs.csv` (400 simulator-confirmed
candidates, plain tank included for reference) and
`deployable_design_per_regime.csv` (5 deployable, PCM-only selections).

**This is the final version of this doc (2026-09-14)**, reflecting the
Tm-target retargeting (doc 12), design-bounds widening (doc 13), and the
selection-rule scope correction (`08_PHASE7_OPTIMIZATION.md`).

---

## Plot 1 — Useful energy vs PCM mass across all 5 climate regimes

**What it is**: Five small-multiple panels (one per climate regime) displaying
every simulator-confirmed candidate (colored by PCM shortlist material or plain-tank
baseline), with a black star marking the final deployable design chosen by the
scope-corrected selection rule (plain tank excluded from winning; among PCM
candidates, highest useful energy within 5% tolerance, then pump-energy/mass tie-break).

**What we infer**:
- In **every regime**, the best PCM candidate now beats its own best
  plain-tank candidate on useful energy (0.01–0.14%) — a real, if narrow,
  margin that did not exist before retargeting.
- The black star **never** sits on the plain-tank series anymore — it is
  always a PCM candidate, per the scope correction.
- **Regime 1** (coldest, smallest-sample cluster) selects **Myristic acid
  (C14)** — its old, climate-*mismatched* shortlist (no retargeted
  candidate survives its ~28°C target, doc 12) — with by far the largest
  nominal safety margin (+11.9°C) of any regime, precisely because it
  barely activates as latent storage at all.
- **Regimes 0, 2, 3 and 4** select RT42, RT42, RT44HC and savE® OM42
  respectively — all retargeted PCMs with melting points 40.5–44.0°C,
  genuinely matched to the tank's real operating range — but all four
  have a **negative** nominal constraint margin (they exceed the 65°C
  PCM limit on hot days).
- Within each PCM material group, increasing PCM mass beyond an optimal
  threshold does not produce monotonic energy gains, because excess
  capsules displace hot water volume and increase hydraulic flow
  obstruction.

**How to justify it**: *"After retargeting the PCM melting point to this
tank's real operating range, every regime's optimal PCM design genuinely
beats plain water — but the plot also shows plainly that 4 of the 5 winning
designs sit in the temperature-unsafe region at nominal conditions. Regime
1 is the outlier not because retargeting succeeded there, but because no
suitable low-temperature PCM exists in the database for its climate, so it
keeps an older, barely-active PCM that happens to stay safe by inactivity."*

---

## Plot 2 — Surrogate-predicted vs simulator-confirmed useful energy

**What it is**: Parity plot comparing surrogate-predicted useful energy against
real full-year simulator re-runs for all 400 search candidates across the 5 regimes.

**What we infer**:
- All 400 candidate designs sit tightly along the $y = x$ line, grouping into 5
  compact clusters representing Uttarakhand's 5 climate regimes.
- The mean error across all 400 candidate designs is **0.03%**.
- Zero of the 400 candidates exceeded the 15% threshold for large
  surrogate error, proving that the surrogate remains highly accurate in the
  optimal regions of design space even after the design-space widening
  (doc 13) quadrupled the candidate pool searched per regime×PCM pair
  (5→20 kept per pair, 100→400 total confirmed).

**How to justify it**: *"Phase 6 proved the surrogate was accurate on random
holdout points. This plot proves the surrogate is equally accurate in the
high-performance regions explored during a much wider optimization search.
The 0.03% agreement across 400 independent full-year simulations validates
the optimizer's selections without requiring thousands of brute-force
physical runs."*

---

## Plot 3 — Temperature-safety compliance of confirmed candidates

**What it is**: Stacked bar chart for each regime showing the count of confirmed
candidates that remain strictly within the safety envelope (maximum water
temperature $\le 75^\circ\text{C}$, maximum PCM temperature $\le 65^\circ\text{C}$)
versus those with safety violations.

**What we infer**:
- **Regime 1**'s pool has many temperature-safe candidates (its PCM barely
  activates, so it rarely threatens either limit) — the selected design
  (Myristic acid (C14)) has margin **+11.9°C**, the largest of any regime.
- **Regimes 0, 2, 3 and 4** have a much smaller safe fraction of their
  candidate pools — their retargeted PCMs cycle actively enough that many
  candidates, including the eventual useful-energy winner in each regime,
  exceed 65°C PCM temperature on hot days (nominal margins −4.2°C to
  −7.8°C).
- The chart confirms that temperature safety was rigorously evaluated as
  an explicit, reported metric for all 400 candidate configurations — it
  is no longer a *selection filter* (see the scope correction in
  `08_PHASE7_OPTIMIZATION.md`), which is exactly why the winning star in
  4 of 5 panels in Plot 1 lands in unsafe territory: the rule now
  optimizes energy first and reports safety as a deployment precondition.

**How to justify it**: *"Safety compliance is evaluated explicitly for
every one of 400 candidates over 8,760 simulated hours each — the data
shows plainly that 4 of 5 regimes' energy-optimal PCM designs need active
overheat protection before deployment. This is reported transparently as
Objective 3's central task, not hidden inside an aggregate pass/fail."*
