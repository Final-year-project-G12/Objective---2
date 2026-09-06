# Phase 3 Plots — Grey-Box Enthalpy Simulator (Rajasthan)

Files: `phase3_temperature_timeseries.*`, `phase3_melt_fraction_year.*`,
`phase3_energy_breakdown.*`. Sample case for all three: state=rajasthan,
cluster 0, PCM = **RT50** (Tm = 48 °C), design = 0.08 m diameter / 19
capsules / 0.030 kg/s flow.

## Plot 1 — One representative week: T_water, T_PCM, irradiance

**What it is**: hours 2400–2568 of the simulated year (≈ one week in
April) — water and PCM temperature on the left axis, irradiance on the
right, same time base.

**What we infer**: seven clean daily cycles. Water climbs from ≈25 °C
(mains) up to the high 60s–low 70s °C tracking irradiance almost exactly
(peaks coincide), then falls overnight as demand draws pull in
mains-temperature water and the always-active ambient tank-loss term
(Bug-Fix 1) bleeds off the rest. **The PCM temperature plateaus near
47–49 °C instead of following the water up** — that flat top is the
enthalpy model's melting band (RT50's Tm = 48 °C ± 1 K) absorbing energy
as latent heat. Because RT50's melting point (48 °C) sits *inside* this
tank's real operating range, the plateau is hit on essentially every
sunny day — more often than Tamil Nadu's n-Octacosane (Tm 61.6 °C), which
rarely melted.

**How to justify it**: *"This is the Phase-3 exit check the framework
specifies: 'T_w and T_pcm histories are physically plausible on a quick
plot.' No chaotic noise, no runaway temperatures, no discontinuities —
clean day/night cycles that track irradiance, plus a melting plateau
exactly at RT50's known melting point. That plateau is the clearest
visual evidence the enthalpy method (not a plain sensible model) is
active."*

## Plot 2 — PCM liquid fraction over the full simulated year

**What it is**: `f_melt` (0 = solid, 1 = liquid) for every hour of the
year for the same case.

**What we infer**: `f_melt` cycles between ≈0 overnight and higher values
on sunny days, reaching 1 on the hottest — a much fuller cycle than Tamil
Nadu's (whose PCM barely melted). It never leaves [0, 1] anywhere in the
year — the clipped liquid-fraction invariant the enthalpy model must
preserve.

**How to justify it**: *"RT50 actually cycles as latent storage here —
you can watch it happen across the whole year, not infer it from one
number. And `f_melt` staying inside [0,1] everywhere is a genuine
simulator-correctness check on the enthalpy model's clipping."*

## Plot 3 — Annual energy breakdown (sample case)

**What it is**: a 4-bar summary of the case's annual totals — collector
input, delivered-to-load, tank/pipe loss, unmet (shortfall) — in
kWh/year.

**What we infer**: collector input (≈1.66 MWh) splits into delivered load
(≈1.58 MWh) plus loss (≈77 kWh) plus the separately-accounted unmet
shortfall (≈1.14 MWh — not subtracted from collector input). The loss bar
is ≈4–5 % of collector input — small, believable for a 50 L tank at
U = 0.8 W/m²K — not zero and not dominant.

**How to justify it**: *"This is the same energy ledger Gate 1 verifies
balances to ~10⁻³ % (Phase 4), made visual. The loss bar being
small-but-nonzero is a direct visual confirmation the ambient tank-loss
term is active — the non-negotiable Bug-Fix 1 requirement — without
reading the verification report."*
