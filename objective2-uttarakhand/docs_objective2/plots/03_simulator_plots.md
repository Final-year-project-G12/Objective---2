# Phase 3 Plots — Grey-Box Enthalpy Simulator

Files: `phase3_temperature_timeseries.*`, `phase3_melt_fraction_year.*`,
`phase3_energy_breakdown.*`. Sample case for all three: state=uttarakhand,
cluster 0, PCM = PureTemp 58 ($T_m = 58.0^\circ\text{C}$), design = 0.08 m
diameter / 19 capsules / 0.030 kg/s flow (the reference case in
`docs_objective2/HOW_TO_RUN.md`).

---

## Plot 1 — One representative week: T_water, T_PCM, irradiance

**What it is**: Hours 2400–2568 of the simulated year (mid-April in Uttarakhand) —
water temperature ($T_w$) and PCM capsule temperature ($T_{pcm}$) on the primary
axis, solar irradiance ($I_t$) on the secondary axis.

**What we infer**:
- Clean, stable diurnal cycles without numerical oscillations or divergence.
- Water temperature rises from mains temperature (~19.4 °C in cluster 0) up to
  65–70 °C during peak daytime solar radiation, tracking irradiance closely.
- Nighttime cooldown brings tank water back towards mains temperature as domestic
  hot water draws extract heat and ambient tank losses ($U_{\text{tank}} = 0.8\text{ W/m}^2\text{K}$,
  Bug-Fix 1) bleed thermal energy to ambient air.
- PCM temperature rises sensibly and slows down near the 58 °C melting plateau,
  confirming the enthalpy formulation in `capsule_enthalpy.py` transitions smoothly
  between sensible and latent regimes.

**How to justify it**: *"This plot demonstrates the required Phase 3 stability
and physics checks. Day and night cycles track climate irradiance without numerical
instability, and the thermal response of the encapsulated PCM reflects the
thermodynamics of the enthalpy formulation."*

---

## Plot 2 — PCM liquid fraction over the full simulated year

**What it is**: Liquid melt fraction $f_{\text{melt}} \in [0, 1]$ for every hour
of the simulated year for the sample case.

**What we infer**:
- For PureTemp 58 ($T_m = 58.0^\circ\text{C}$) in a 50 L tank with 300 L/day draw
  and no auxiliary heater, $f_{\text{melt}}$ spends the vast majority of the year
  near zero, spiking to partial or full melt only during high-irradiance summer periods.
- This provides visual proof for the finding reported in Phase 4 Gate 3 and Phase 7:
  at this collector area and tank volume, a 58 °C PCM is largely under-melted
  because tank temperatures do not stay above 58 °C long enough to exploit the
  full latent capacity.
- The invariant $0 \le f_{\text{melt}} \le 1$ holds continuously without clipping
  violations or numeric overflows.

**How to justify it**: *"This directly visualizes why PureTemp 58 does not
dramatically outperform a plain water tank across all regimes. The simulator
faithfully captures that the PCM remains subcooled during most months, behaving
primarily as sensible storage rather than an active latent buffer."*

---

## Plot 3 — Annual energy breakdown (sample case)

**What it is**: A four-bar distribution of annual energy flows for the reference
case in Uttarakhand:
- Collector input energy ($E_{\text{collector}} \approx 1740\text{ kWh}$)
- Useful energy delivered to load ($E_{\text{useful}} \approx 1675\text{ kWh}$)
- Tank and pipe ambient losses ($E_{\text{loss}} \approx 53\text{ kWh}$)
- Unmet thermal shortfall ($E_{\text{unmet}} \approx 2316\text{ kWh}$)

**What we infer**:
- Heat losses to ambient account for ~3–4% of collector input, consistent with a
  well-insulated 50 L storage tank ($U = 0.8\text{ W/m}^2\text{K}$).
- The existence of a nonzero, physically realistic loss bar verifies that the
  ambient thermal loss term is permanently active (Bug-Fix 1).
- The unmet energy reflects the demand shortfall relative to a 300 L/day draw at
  60 °C without an auxiliary backup heater in Uttarakhand's colder climate.

**How to justify it**: *"The energy breakdown illustrates the complete first-law
thermal accounting verified by Gate 1 to an accuracy of 0.0017%. The nonzero loss
bar confirms the bug fix requiring ambient losses to operate continuously."*
