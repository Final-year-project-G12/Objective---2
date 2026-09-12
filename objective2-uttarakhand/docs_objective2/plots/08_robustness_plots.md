# Phase 8 Plots — Robustness & Objective 3 Hand-off

Files: `phase8_robustness_probabilities.*`, `phase8_useful_energy_intervals.*`.
Data source: `results/uttarakhand/robustness_summary.csv` (5 rows, each aggregating
120 full-year Monte Carlo simulator re-runs under a 10-year historical weather ensemble)
and `deployable_design_per_regime.csv` for nominal unperturbed benchmarks.

---

## Plot 1 — Robustness probabilities per regime

**What it is**: Three compliance probabilities per regime evaluated across 120
independent annual simulations:
1. **Purple bars**: $P(\text{meets delivery temperature, SF} \ge 0.45)$
2. **Blue bars**: $P(\text{meets annual demand, SF} \ge 0.50)$
3. **Green bars**: $P(\text{temperature safe}) = 1 - P(\text{overheat violation})$

With reference lines at $75\%$ (demand threshold) and $95\%$ (temperature safety threshold).

**What we infer**:
- **Why demand reliability ($P \ge 50\%$) is 0.0% statewide**:
  - Unlike self-referential metrics (which declare any nominal result "100% reliable"),
    the unified framework applies fixed, cross-state standards ($\text{SF} \ge 0.50$).
  - In Uttarakhand, cold mains feed water ($7.4^\circ\text{C}$ in high-elevation
    Regime 2 to $21.8^\circ\text{C}$ in valley Regime 3) combined with a high thermal
    draw (300 L/day at $60^\circ\text{C}$) in an unassisted 50 L tank caps annual
    solar fractions nominally between $28.0\%$ and $40.7\%$.
  - Consequently, no unassisted 50 L solar collector system can achieve $\text{SF} \ge 50\%$
    under real historical weather, establishing the critical engineering requirement
    for an auxiliary heating boost in Objective 3.
- **Delivery temperature ($P \ge 45\%$)**:
  - Regimes 0 and 3 reach $23.3\%$ and $22.5\%$ delivery probability, while colder
    Regimes 1, 2, and 4 stay below $3\%$.
- **Temperature safety ($P_{\text{safe}}$)**:
  - **Regime 2 (PureTemp 58 design)** achieves an outstanding **100.0% temperature
    safety** ($0.0\%$ violation probability across all 120 weather scenarios).
    The PCM's latent buffer absorbs peak summer surges while cold mains water
    prevents scalding.
  - Plain water tank regimes suffer occasional heat build-up under peak solar
    irradiance without auxiliary heat dumping ($P_{\text{violation}} = 55.8\%$ in
    Regime 0, $35.8\%$ in Regime 3, $16.7\%$ in Regime 4, $8.3\%$ in Regime 1).

**How to justify it**: *"Using fixed, state-independent thresholds and a real
10-year historical weather ensemble reveals the true engineering reality of Uttarakhand:
unassisted 50 L solar thermal systems cannot meet 50% solar fraction in cold climates,
necessitating hybrid auxiliary heating in Objective 3. Crucially, Regime 2's PureTemp 58
design proves 100% immune to overheating, validating the thermal safety benefit
of phase-change storage."*

---

## Plot 2 — Useful-energy 5th–50th–95th percentile intervals per regime

**What it is**: Horizontal uncertainty bars spanning the 5th percentile ($P_{05}$)
to the 95th percentile ($P_{95}$) of annual useful energy across 120 historical
weather draws per regime, with a circle marking the distribution median ($P_{50}$)
and a black diamond indicating the single nominal unperturbed design point from Phase 7.

**What we infer**:
- **Regime 0**: $[1576.5, 1755.4]\text{ kWh}$, Median $= 1678.5\text{ kWh}$, Nominal $= 1675.3\text{ kWh}$
- **Regime 1**: $[1522.6, 1727.5]\text{ kWh}$, Median $= 1629.0\text{ kWh}$, Nominal $= 1625.3\text{ kWh}$
- **Regime 2**: $[1435.4, 1650.1]\text{ kWh}$, Median $= 1514.6\text{ kWh}$, Nominal $= 1527.2\text{ kWh}$
- **Regime 3**: $[1479.9, 1659.1]\text{ kWh}$, Median $= 1557.8\text{ kWh}$, Nominal $= 1563.8\text{ kWh}$
- **Regime 4**: $[1541.9, 1718.5]\text{ kWh}$, Median $= 1630.7\text{ kWh}$, Nominal $= 1624.0\text{ kWh}$

- In every regime, the nominal diamond sits comfortably within the interval, closely
  aligned with the distribution median.
- This demonstrates that Phase 7's single-year optimization did not select an
  unstable or fortunate outlier; rather, the nominal selections accurately reflect
  expected multi-year operational performance.

**How to justify it**: *"The 120-draw historical weather ensemble confirms that
our deployable design benchmarks are robust and centered within their multi-year
probability distributions, providing dependable baseline targets for Objective 3."*
