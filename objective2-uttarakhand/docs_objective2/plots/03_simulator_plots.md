# Phase 3 Plots — Grey-Box Enthalpy Simulator

Files: `phase3_temperature_timeseries.*`, `phase3_melt_fraction_year.*`,
`phase3_energy_breakdown.*`. Sample case for all three: state=uttarakhand,
cluster 0, PCM = **RT42** ($T_m = 40.5^\circ\text{C}$, this regime's
retargeted rank-1 PCM — see `12_TM_TARGET_RETARGETING.md`), design = 0.08 m
diameter / 19 capsules / 0.030 kg/s flow (the reference case in
`docs_objective2/HOW_TO_RUN.md`). The sample PCM is now selected
dynamically from the current config (`get_regime(state, 0)["pcm_shortlist"][0]`),
so this doc always describes whichever PCM cluster 0 currently recommends.

---

## Plot 1 — One representative week: T_water, T_PCM, irradiance

**What it is**: Hours 2400–2568 of the simulated year (mid-April in Uttarakhand) —
water temperature ($T_w$) and PCM capsule temperature ($T_{pcm}$) on the primary
axis, solar irradiance ($I_t$) on the secondary axis.

**What we infer**:
- Clean, stable diurnal cycles without numerical oscillations or divergence.
- Water temperature rises from mains temperature (~20.6 °C in cluster 0) up to
  ~71.1 °C during peak daytime solar radiation, tracking irradiance closely.
- Nighttime cooldown brings tank water back towards mains temperature as domestic
  hot water draws extract heat and ambient tank losses ($U_{\text{tank}} = 0.8\text{ W/m}^2\text{K}$,
  Bug-Fix 1) bleed thermal energy to ambient air.
- PCM temperature now tracks water temperature closely and cycles actively
  through RT42's 40.5 °C melting plateau on nearly every sunny day — a
  qualitatively different picture from the pre-retargeting PCM, which
  rarely reached its own (58 °C) melting point at all.

**How to justify it**: *"This plot demonstrates the required Phase 3 stability
and physics checks. Day and night cycles track climate irradiance without numerical
instability, and the thermal response of the encapsulated PCM reflects the
thermodynamics of the enthalpy formulation — now with a melting point genuinely
matched to this tank's real operating range."*

---

## Plot 2 — PCM liquid fraction over the full simulated year

**What it is**: Liquid melt fraction $f_{\text{melt}} \in [0, 1]$ for every hour
of the simulated year for the sample case.

**What we infer**:
- For RT42 ($T_m = 40.5^\circ\text{C}$) in a 50 L tank with 300 L/day draw
  and no auxiliary heater, $f_{\text{melt}}$ now cycles **actively** —
  annual mean $\approx 31.7\%$, with **196 complete melt cycles** over the
  year (up from ~5 for the pre-retargeting PCM). This is the direct visual
  confirmation that the Tm-target retargeting (doc 12) fixed the
  fundamental mismatch between PCM melting point and real tank behavior.
- The same active cycling that makes RT42 a genuinely functioning latent
  store is also *why* its temperature tracks water temperature closely
  enough to exceed the 65 °C PCM safety limit on the sunniest days — this
  case alone logs **369 hours/year** of safety violation
  (`n_safety_violations=369`), visible here as $f_{\text{melt}}$ pinning
  at 1.0 on hot days rather than staying in a moderate partial-melt band.
- The invariant $0 \le f_{\text{melt}} \le 1$ holds continuously without clipping
  violations or numeric overflows.

**How to justify it**: *"This directly visualizes both sides of the retargeting
finding: RT42 now behaves as genuine latent thermal storage, cycling 196 times a
year — but that same activity is exactly why its temperature follows the tank's
into unsafe territory on peak-irradiance days, motivating Objective 3's active
overheat protection."*

---

## Plot 3 — Annual energy breakdown (sample case)

**What it is**: A four-bar distribution of annual energy flows for the reference
case in Uttarakhand:
- Collector input energy ($E_{\text{collector}} \approx 1623\text{ kWh}$)
- Useful energy delivered to load ($E_{\text{useful}} \approx 1536\text{ kWh}$)
- Tank and pipe ambient losses ($E_{\text{loss}} \approx 88\text{ kWh}$)
- Unmet thermal shortfall ($E_{\text{unmet}} \approx 2280\text{ kWh}$)

**What we infer**:
- Heat losses to ambient account for ~5% of collector input, consistent with a
  well-insulated 50 L storage tank ($U = 0.8\text{ W/m}^2\text{K}$).
- The existence of a nonzero, physically realistic loss bar verifies that the
  ambient thermal loss term is permanently active (Bug-Fix 1).
- The unmet energy reflects the demand shortfall relative to a 300 L/day draw at
  60 °C without an auxiliary backup heater in Uttarakhand's colder climate.
- PCM charge/discharge energy is now substantial (~75 kWh each, roughly
  balanced) — another confirmation of active cycling, versus the
  pre-retargeting PCM's much smaller charge/discharge flow.

**How to justify it**: *"The energy breakdown illustrates the complete first-law
thermal accounting verified by Gate 1 to an accuracy of 0.006% for this case. The
nonzero loss bar confirms the bug fix requiring ambient losses to operate
continuously, and the now-substantial PCM charge/discharge flow confirms genuine
latent-storage activity."*
