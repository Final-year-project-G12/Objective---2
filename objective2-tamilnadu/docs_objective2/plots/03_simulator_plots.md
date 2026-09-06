# Phase 3 Plots — Grey-Box Enthalpy Simulator

Files: `phase3_temperature_timeseries.*`, `phase3_melt_fraction_year.*`,
`phase3_energy_breakdown.*`. Sample case for all three: state=tamilnadu,
cluster 0, PCM = n-Octacosane (C28), design = 0.08 m diameter / 19
capsules / 0.030 kg/s flow (the same case documented in
`docs_objective2/HOW_TO_RUN.md`'s Phase 3 example).

---

## Plot 1 — One representative week: T_water, T_PCM, irradiance

**What it is**: hours 2400–2568 of the simulated year (≈ one week in
April) — water temperature and PCM temperature on the left axis,
irradiance on the right axis, all on the same time base.

**What we infer**: seven clean daily cycles. Water temperature climbs
from ≈26 °C (mains temperature) up to 67–70 °C tracking irradiance almost
exactly (peaks coincide), then falls back to ≈26 °C overnight as the
demand draws pull mains-temperature water in and the ambient tank-loss
term (always active — Bug-Fix 1) bleeds off the rest. **The PCM
temperature visibly plateaus around 60–62 °C instead of following the
water all the way to 70 °C** — that flat top is the enthalpy-model's
melting band (n-Octacosane's Tm = 61.6 °C ± 1 K) absorbing energy as
latent heat instead of raising temperature, exactly as the piecewise
enthalpy model in `capsule_enthalpy.py` is supposed to produce. The small
notch partway up each morning curve is the demand draw's effect on the
water node.

**How to justify it**: *"This is the literal Phase-3 exit check the
framework itself specifies: 'T_w and T_pcm histories are physically
plausible on a quick plot.' There's no chaotic noise, no runaway
temperatures, no discontinuities — just clean day/night cycles that track
irradiance, plus a visible melting plateau exactly at the PCM's known
melting point. That plateau is the single clearest piece of visual
evidence that the enthalpy method (not a simple sensible-heat model) is
actually active in the simulator."*

---

## Plot 2 — PCM liquid fraction over the full simulated year

**What it is**: `f_melt` (0 = fully solid, 1 = fully liquid) for every
hour of the year for the same case.

**What we infer**: `f_melt` spends the overwhelming majority of the year
near 0, with narrow spikes toward 1 on the sunniest days — visually
confirming the "mean_f_melt ≈ 1.4–2%" number reported in the Phase 3/4/7
docs. This is not a plotting artifact; it is the same physical story as
Plot 1's plateau: the PCM only fully melts on the hottest days, so most of
the year it sits sub-cooled, contributing little latent storage.

**How to justify it**: *"This plot is the direct visual version of the
'PCM barely melts' finding we report in Phase 4 Gate 3 and Phase 7 — you
can see it happen across the whole year, not just infer it from one
summary number. It's also a genuine simulator-correctness check: `f_melt`
never goes outside [0,1] anywhere in the year, which is the clipped
liquid-fraction invariant the enthalpy model is required to preserve."*

---

## Plot 3 — Annual energy breakdown (sample case)

**What it is**: a 4-bar summary of the same case's annual energy
totals — collector input, delivered-to-load, tank/pipe loss, and unmet
(shortfall) energy, all in kWh/year.

**What we infer**: collector input (≈1740 kWh) splits into delivered load
(≈1660 kWh useful) plus loss (≈73 kWh) plus the energy that
*would have been* needed to fully meet demand but wasn't (unmet, ≈1180
kWh — this is a separate accounting of shortfall, not subtracted from
collector input). The loss term is a small, believable fraction of
collector input (≈4%), not zero and not dominant — consistent with a
50 L tank with U=0.8 W/m²K insulation.

**How to justify it**: *"This is the same accounting that Gate 1
verifies balances to within 0.00002% — this chart is just that same
energy ledger made visual. The loss bar being small-but-nonzero is a
direct visual confirmation that the ambient tank-loss term is active
(the non-negotiable Bug-Fix 1 requirement) without needing to read the
verification report's numbers."*
