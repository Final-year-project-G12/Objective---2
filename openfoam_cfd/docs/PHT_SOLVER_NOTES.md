# Packed-bed OpenFOAM solver (Fetsov & Lutsenko 2023) — status in this project

| Item | Status (2026-10-16) |
|---|---|
| Source | `github.com/fetc95/pht-openfoam-lab53iacp`, cloned to `~/OpenFOAM/OpenFOAM-PHT53IACP` in WSL (17 MB, CC BY-NC 4.0 — non-commercial use, cite the paper) |
| Build | `./Allwmake` against **OpenFOAM v2406** (README targets v2412): exit 0; binaries `porousHeatTransferFoam`, `phtEnthalpyFoam` in `$FOAM_USER_APPBIN`; libs `libsolidPHT53Thermo.so`, `libreactionPHT53Thermo.so` |
| Smoke test | shipped `PCMValidations/GR27` ran 6 h of simulated time in 40 s, exit 0 (`gnuplot` missing → plot step skipped; harmless) |
| Paper §4.3 water case | reproduced with the values printed in the paper (see below) |
| Rajasthan 50 L bed | generator and two runs done (see below) |
| NOT done | quantitative comparison with the experimental points (not in the repo; only Fig. 7 of the paper); 2-D beds; annual runs; parameter sweep |
| Reinstall | `bash scripts/install_pht_solver.sh` |

## How it fits our chain
The solver takes the interphase coefficient `α` (W/m³K) as an **input**; it does
not resolve convection inside a capsule. Our single-capsule CFD supplies exactly
that missing resistance:

`capsule CFD (d, ṁ, ΔT, PCM)  →  effective α_eff(f_melt)  →  porousHeatTransferFoam bed  →  annual/climate runs`

Their water-HTF validation case (paper §4.3, Nallusamy 2007 experiment, 55 mm
capsules) is the natural first bed-scale check: HTF temperature deviation about
3–4 K, PCM temperature locally off in 315–333 K (property uncertainty).

## Results (2026-10-16)

Files: `cases_pht/<name>/summary.json`, `postProcessing/`; generator `scripts/pht_make_case.py`,
runner `scripts/pht_run_case.sh`, summariser `scripts/pht_postprocess.py`.

### A. Paper §4.3 water-HTF case (Nallusamy et al. 2007 experiment) — `nallusamy_T305`
Why a re-build and not the shipped `water` example: that example calls
`phtMultiSolidFoam`, which is **not in the repository** (only `porousHeatTransferFoam`,
`phtEnthalpyFoam`, `phtMetalExtractionFoam`), and its `Tinl.csv` holds values
(598–738) that are not temperatures. The case was therefore rebuilt on
`porousHeatTransferFoam` from the values printed in the paper (Eq. 32): a = 0.5,
H = 0.46 m, D_eq = 0.36 m, k1 = 1e-5 m², k2 = 127, α = 3000 W/m³K, 2 L/min, water
at 343 K, PCM: effective properties with the steel shell folded in (λ ≈ 0.28,
ρ ≈ 824.7, ΔH ≈ 198 kJ/kg, mushy 332–334 K). **Initial temperature is 305 K** —
the paper's text lists Ta = 298 K but the curves in its Fig. 7 start at 305 K.

| Probe x/H | Fully melted, this run (T_solid ≥ 334 K) | Paper Fig. 7a, calculated curves (read by eye) |
|---|---|---|
| 0.25 | 68 min | ≈ 68 min |
| 0.50 | 85 min | ≈ 85–90 min |
| 0.75 | 101 min | ≈ 100–105 min |
| 1.00 | 116.5 min | ≈ 115–120 min |

All probes reach 343 K by 160 min as in the paper. **Status: consistent with the
paper's own calculated curves within the precision of reading a figure (a few
minutes); not a comparison against the experimental data points**, which are not
available in text form. The paper itself reports ≈ 3–4 K maximum water-temperature
deviation against the experiment and local PCM-temperature errors in 315–333 K.

### B. Rajasthan 50 L bed (1-D, water HTF) — RT44HC, d = 60 mm, N = 30, 0.03 kg/s, inlet Tm+15 K
Bed: D = 0.317 m, H = 0.634 m, PCM volume fraction 6.8 %, specific area 6.8 m²/m³, water-side h_w = 180 W/m²K.
**D/d = 5.3 — below the 7–8 the paper validates**, so the continuum assumption is
outside its demonstrated range for this design.

| Internal-resistance scale φ on r/(5k) | α_eff [W/m³K] | All cells fully melted (T ≥ Tm+1 K) |
|---|---|---|
| 1.0 (grey-box frozen closure) | 222 | 4410–4560 s |
| 0.47 (CFD-calibrated) | 392 | 2520–2640 s |

Single-capsule CFD for the same design (`results/cfd_mesh_results.csv`): t90 ≈ 1.9e3 s,
t99 ≈ 2.2e3 s (1.2 mm) – 2.5e3 s (0.6 mm). The bed with φ = 0.47 therefore matches
the capsule CFD's full-melt time to within a few percent, while φ = 1 is ≈ 1.8×
too slow — the same ~2× pessimism the paired annual runs found. This is a
consistency check of the chain, not an independent validation: φ was fitted to
the same CFD.

The bed is almost isothermal along its length (cells fully melted within ≈ 150 s
of each other) because 0.03 kg/s of water carries far more heat than 30 small
capsules store at this loading — the axial stratification question (P2 of the plan)
is therefore weak at this operating point; higher PCM loading or lower flow would
test it.

### C. Bed solver driven by the grey-box's hourly temperatures — Phase-7 deployable design per regime
Script `scripts/pht_vs_greybox.py`; results `results/pht_vs_greybox.csv`; forcing files
`cases_pht/_forcing/`; bed runs `cases_pht/bed_r<regime>_V<k>/`. 48 h from the grey-box
state at 00:00 of the representative day (median daily collector energy among days with a
complete melt-and-freeze cycle: day 202 / 252 / 52 of the year for regimes 0 / 1 / 2).
Time step 5 s (checked against 1 s on a 4 h case: full-melt times equal to ≤ 2 %).
D/d = 0.317/0.040–0.043 ≈ 7.4–7.9, i.e. **inside** the paper's validated range.

| Regime / PCM | Variant (inlet water, φ) | RMSE T_pcm [K] | mean bed − grey [K] | RMSE f_melt | hours f > 0.5 (grey / bed) | 50 % melt / freeze hour (grey / bed) |
|---|---|---|---|---|---|---|
| 0 RT44HC | V1 T_w, φ = 1 | **0.50** | +0.07 | 0.08 | 20 / 21 | 5 / 5 · 18 / 18 |
| 0 | V2 collector outlet, φ = 1 | 1.88 | +1.09 | 0.19 | 20 / 25 | 5 / 5 · 18 / 18 |
| 0 | V3 collector outlet, φ = 0.53 | 2.29 | +1.05 | 0.20 | 20 / 25 | 5 / 5 · 18 / 18 |
| 1 savE® OM49 | V1 | **0.22** | +0.01 | 0.04 | 26 / 25 | 5 / 5 · 18 / 18 |
| 1 | V2 | 2.60 | +1.46 | 0.09 | 26 / 26 | 5 / 5 · 18 / 18 |
| 1 | V3 (φ = 0.58) | 2.72 | +1.49 | 0.10 | 26 / 26 | 5 / 5 · 18 / 18 |
| 2 Lauric acid | V1 | **0.82** | −0.07 | 0.11 | 24 / 24 | 6 / 6 · 18 / 18 |
| 2 | V2 | 3.04 | +1.67 | 0.12 | 24 / 26 | 6 / 5 · 18 / 18 |
| 2 | V3 (φ = 0.43) | 4.11 | +1.69 | 0.16 | 24 / 26 | 6 / 5 · 18 / 18 |

Reading (what is and is not supported):
* **V1 isolates model form** (same forcing, same closure): the continuum bed and the
  single-node grey-box agree to 0.2–0.8 K RMSE over 48 h, with identical 50 %
  melt/freeze hours. For these designs and flows, axial structure does **not** change
  the PCM response — consistent with Krol et al. 2026 [C] (small stratification effect on
  solar fraction) and supporting the single-node tank assumption.
* **V2/V3 differ mainly because the forcing is hotter** (collector outlet is up to a few
  kelvin above the water node) — the +1.1 to +1.7 K mean offset and 4–5 extra melted
  hours are forcing, not model, differences. They are not errors of either model.
* **V3 vs V2**: the CFD-calibrated closure moves the bed PCM temperature relative to the
  frozen grey-box by an additional 0.1–1.1 K RMSE (largest for lauric acid, φ = 0.43) — the
  same direction and modest size as the paired annual runs (+0.06–0.16 % energy).
* Not a validation: both models share the lumped-capsule assumption; no measured data.
* Differences left in: the bed's α is constant (the grey-box doubles k after 50 % melt),
  no water draw at night (the bed gets no discharge load), hourly values used as
  samples at the start of each hour, one-way coupling.

## Next steps
1. Digitise the experimental points of the paper's Fig. 7 (or obtain Nallusamy 2007) and score the model quantitatively.
2. Replace the single φ by `α_eff(d, ṁ, ΔT, f_melt)` from the CFD DOE (AI_OPTIMISATION_PLAN §5) and run the three Phase-7 designs for all regimes with the hourly weather as the inlet-temperature table.
3. Add the missing `D/d` guard: flag designs below 7 and compare with the single-node grey-box on the same inputs.
