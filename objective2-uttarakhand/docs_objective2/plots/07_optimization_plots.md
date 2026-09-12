# Phase 7 Plots — Optimization Pass & Simulator Confirmation

Files: `phase7_pareto_by_regime.*`, `phase7_surrogate_vs_simulator.*`,
`phase7_safety_compliance.*`.
Data source: `results/uttarakhand/optimized_designs.csv` (100 simulator-confirmed
candidates) and `deployable_design_per_regime.csv` (5 deployable selections).

---

## Plot 1 — Useful energy vs PCM mass across all 5 climate regimes

**What it is**: Five small-multiple panels (one per climate regime) displaying
every simulator-confirmed candidate (colored by PCM shortlist material or plain-tank
baseline), with a black star marking the final deployable design chosen by the
two-stage Pareto selection rule (5% performance tolerance, then minimize PCM mass).

**What we infer**:
- In **Regimes 0, 1, 3, and 4**, the black star sits at $x = 0$ (zero PCM mass,
  plain water tank). The useful energy of the plain tank sits within a fraction of
  a percent ($< 0.15\%$) of the best PCM candidates. Under the 5% Pareto tolerance
  rule, the optimizer correctly rejects the complexity, cost, and risk of PCM
  capsules when there is no tangible performance gain.
- In **Regime 2** (high-elevation cluster with cold mains water $T_{\text{mains}} = 7.4^\circ\text{C}$),
  the black star selects a PCM configuration: **PureTemp 58 with 0.392 kg mass**
  (10 capsules of 43.8 mm diameter, flow 0.0116 kg/s), providing stable thermal
  storage without overheating.
- Within each PCM material group, increasing PCM mass beyond an optimal threshold
  does not produce monotonic energy gains, because excess capsules displace hot
  water volume and increase hydraulic flow obstruction.

**How to justify it**: *"This plot visually justifies our deployable design selections.
In four of the five regimes, the plain tank is virtually indistinguishable in
energy delivery from the PCM designs, making zero-mass water storage the robust,
cost-effective choice. Only in Regime 2 does the thermal environment justify
deploying PureTemp 58."*

---

## Plot 2 — Surrogate-predicted vs simulator-confirmed useful energy

**What it is**: Parity plot comparing surrogate-predicted useful energy against
real full-year simulator re-runs for all 100 search candidates across the 5 regimes.

**What we infer**:
- All 100 candidate designs sit tightly along the $y = x$ line, grouping into 5
  compact clusters representing Uttarakhand's 5 climate regimes.
- The mean error across all 100 candidate designs is an exceptional **0.02%**
  (maximum error $< 0.15\%$).
- Crucially, zero of the 100 candidates exceeded the 15% threshold for large
  surrogate error, proving that the surrogate remains highly accurate in the
  optimal regions of design space where candidates are concentrated.

**How to justify it**: *"Phase 6 proved the surrogate was accurate on random
holdout points. This plot proves the surrogate is equally accurate in the high-performance
regions explored during optimization. The 0.02% agreement across 100 independent
full-year simulations validates the optimizer's selections without requiring
thousands of brute-force physical runs."*

---

## Plot 3 — Temperature-safety compliance of confirmed candidates

**What it is**: Stacked bar chart for each regime showing the count of confirmed
candidates that remain strictly within the safety envelope (maximum water
temperature $\le 75^\circ\text{C}$, maximum PCM temperature $\le 65^\circ\text{C}$)
versus those with safety violations.

**What we infer**:
- In high-irradiance regimes without auxiliary heat rejection, unencapsulated plain
  tanks and low-flow PCM designs can experience brief summer temperature spikes
  exceeding $75^\circ\text{C}$.
- In Regime 2, the selected PureTemp 58 design remains safely within the envelope
  ($T_{w,\max} = 58.04^\circ\text{C}$, $T_{pcm,\max} = 57.03^\circ\text{C}$,
  margin $+7.97^\circ\text{C}$), utilizing the PCM's latent capacity to cap peak
  water temperatures.
- The chart confirms that temperature safety was rigorously evaluated as an
  explicit constraint for all candidate configurations.

**How to justify it**: *"Safety compliance is an essential deployment filter.
Evaluating peak temperatures over 8,760 hours ensures that our recommended
designs do not just optimize annual energy, but also avoid scalding and degradation
risks."*
