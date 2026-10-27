# OpenFOAM capsule CFD — findings (full run, 2026-10-15)

Every number is read from a file in `../results/` (file named per table).
48-case DOE (16 per PCM), 48 conduction-only twins, 6 sensitivity cases, mesh
and time-step checks. Pilot (8 per PCM) archived as `*_pilot8.*`; its
conclusions are unchanged.

## 1. Verification status

| Check | Result | File |
|---|---|---|
| `checkMesh` | OK; sphere volume within 0.5 % of analytic | `cases/*/log.checkMesh` |
| Energy balance (wall-flux integral vs stored energy) | **48/48 DOE cases < 3 %** (max 2.05 %) | `cfd_doe_results.csv` |
| Harness check: grey-box with φ = 1 vs project's Phase-5 results | max difference 7.7e-11 kWh over 108 designs | `o2_cfd_paired_annual.csv` |
| Every capsule melted inside the 6 h window | 48/48 (`f_melt_window` ≥ 0.95) | `cfd_doe_results.csv` |
| Mesh independence (60 mm RT44HC, 15 K) | t50: 986 / 998 / 1022 / 1030 s; **t90: 1773 / 1890 / 2025 / 2082 s** for 256 / 576 / 1444 / 2500 cells. Last refinement (0.8 → 0.6 mm) moves t90 by +2.9 %; the production mesh (576 cells) is **≈ 9 % below the 0.6 mm value** | `cfd_mesh_results.csv`, `cfd_mesh_extra_results.csv` |
| Time step | Courant 0.25 vs 0.5 on the production mesh: t90 1887 vs 1890 s (**0.2 %**) | `cfd_mesh_extra_results.csv` |
| Assumed liquid properties (production mesh, base t90 = 1890 s) | see §2 | `cfd_sens_results.csv` |

Read: t90 on the production mesh is **under-predicted by roughly 9 %** relative
to the finest mesh; the effect is a *shift of the same sign in every case*, so it
rescales melt times but not the grey-box-vs-CFD comparison direction. For
publication, run the DOE at 0.8 mm (`numerics.cell_size_m: 0.0008`; ~5× cost).

## 2. Sensitivity to the properties not in the project data

Reference: 60 mm RT44HC, 0.03 kg/s, 15 K; t90 = 1890 s, φ = 0.46.

| Perturbation | t50 change | t90 change | φ |
|---|---|---|---|
| liquid viscosity × 0.5 | −8.2 % | −9.2 % | 0.39 |
| liquid viscosity × 2 | +9.4 % | +11.1 % | 0.54 |
| expansion β × 0.5 | +11.3 % | +12.4 % | 0.55 |
| expansion β × 2 | −10.0 % | −10.0 % | 0.38 |
| mushy Darcy Cu × 0.1 | −7.3 % | −1.7 % | 0.45 |
| mushy Cu × 10 | +2.5 % | +0.9 % | 0.46 |

μ and β (both **assumed**, not in the O1 database) move melt time by ±10–12 %
and φ over 0.38–0.55. Cu is immaterial. So the *size* of the grey-box error is
uncertain by about ±0.1 in φ until μ and β are taken from datasheets; its
*existence* is not (φ < 0.6 in every sensitivity case).

## 3. Does the grey-box capsule model match CFD?

48 cases, d = 40–80 mm, ṁ = 0.010–0.050 kg/s, drive 5.2–24.3 K above Tm
(`cfd_doe_results.csv`):

| PCM | grey-box t90 ÷ CFD t90 (min / median / max) | φ (min / median / max) | Biot |
|---|---|---|---|
| RT44HC | 1.23 / 1.60 / 2.06 | 0.38 / 0.48 / 0.73 | 15–33 |
| savE® OM49 | 1.25 / 1.50 / 1.84 | 0.42 / 0.56 / 0.69 | 11–23 |
| Lauric acid (C12) | 1.67 / 2.08 / 2.47 | 0.30 / 0.39 / 0.47 | 19–42 |
| **all** | **1.23 / 1.67 / 2.47** | **0.30 / 0.47 / 0.73** | |

* The grey-box is slower than CFD in **every** case, by a median factor 1.7.
* Equivalent statement: the lumped `R_pcm = r/(5k)` is about **2× too high**
  (φ median 0.47) — largest for the lowest-conductivity PCM (lauric acid).
* Natural convection is real and large: conduction-only t90 ÷ full-physics t90
  = **1.8–3.3, median 2.35** (`cfd_convection_gain.csv`; lauric 2.3–3.3,
  RT44HC 1.9–3.0, OM49 1.8–2.5). The frozen "×2" is therefore the right order of
  magnitude **but is applied only after 50 % melt**, which is why it does not
  recover the CFD melt time.

Caveats: constant wall-water temperature in CFD (real tank varies hourly);
isothermal melting at Tm (grey-box ±1 K band); μ, β assumed (§2); t90 under-
resolved by ≈ 9 % (§1).

## 4. Does it change the Objective-2 answer?

Paired annual simulation of the project's own 108 Phase-5 designs, frozen vs
CFD-calibrated closure (`o2_cfd_paired_summary.csv`):

| Regime / PCM | mean Δ useful energy | max \|Δ\| | best design vs plain tank, frozen → calibrated |
|---|---|---|---|
| 0 / RT44HC | +2.1 kWh (+0.13 %) | 5.8 kWh | +0.20 % → +0.46 % |
| 1 / savE® OM49 | +1.2 kWh (+0.06 %) | 3.1 kWh | +0.13 % → +0.15 % |
| 2 / Lauric acid | +2.9 kWh (+0.16 %) | 8.6 kWh | +0.13 % → +0.21 % |

* Calibration changes annual useful energy by **0.06–0.16 %**, in the expected
  direction (PCM charges faster than the grey-box said).
* Spearman ρ between frozen and calibrated design rankings: −0.24 / 0.70 /
  0.19 (regimes 0 / 1 / 2). Within each regime the whole design set spans
  ≈ 5 kWh (< 0.3 %), i.e. the ordering is inside the simulator's 0.04 % noise
  band to begin with — **do not read ρ as "the best design changed".**
* AI search (ExtraTrees, 6 000 constrained candidates, top-5 confirmed in the
  calibrated simulator; `o2_cfd_calibrated_recommendation.csv`):

  | Regime | d [mm] | N | ṁ [kg/s] | arrangement | vs plain tank |
  |---|---|---|---|---|---|
  | 0 RT44HC | 77–78 | 34–36 | 0.048–0.050 | single-layer | +0.47–0.49 % |
  | 1 OM49 | 51–54 | 33–37 | 0.040–0.044 | radial | +0.15–0.16 % |
  | 2 Lauric | 51–69 | 32–33 | 0.047–0.050 | radial | +0.20–0.22 % |

  Surrogate error versus the simulator: 0.1–0.7 kWh. All recommended designs
  reach `max_pcm_temp ≈ 62.1 °C`, the shield limit.

## 5. What you can claim

1. CFD shows the grey-box's lumped PCM resistance is about 2× pessimistic
   (φ median 0.47; range 0.30–0.73; grey-box melt time 1.2–2.5× CFD).
2. Natural convection speeds 90 % melt by a median 2.35× (1.8–3.3×) — the
   frozen ×2 factor has the right magnitude but the wrong *timing*.
3. Using the CFD-calibrated closure moves annual useful energy by < 0.2 % and
   PCM-vs-plain-tank margins by ≤ 0.26 percentage points: **the Objective-2
   conclusion (PCM ≈ plain tank, margin well inside the 5 % tolerance) is
   unchanged**, and individual designs are not resolvable above noise.

## 6. What you cannot claim

* That CFD found a better design — it did not.
* The exact value of φ: ±0.1 from the assumed μ/β, plus ≈ 9 % melt-time
  discretisation error at the production mesh.
* That the regime-0 recommendation (≈ 17–18 % PCM volume, 34–36 capsules) is
  robustly better. The project's loading sweep (`docs/09 §11`) found gains turn
  negative above ≈ 2.5–3 % for the O1 rank-1 PCMs; this CFD-calibrated result
  disagrees and has **not** been reconciled — check it against Phase 3.5 before
  recommending it.
* Anything about arrangement from CFD (not resolved; README §6). Regime 0
  prefers single-layer and regimes 1–2 radial, but the differences are
  inside noise.

## 7. Operational notes

* 7 of 48 DOE cases (all RT44HC) first failed with a transient WSL launch error
  (`rc=2`, no solver output) under 8-way parallel load; they were re-run
  unchanged and passed. `run_doe.py` now retries automatically.
* One sensitivity case failed because the solver re-read `controlDict` while the
  early-stop edit was writing it; `run_one.sh` now writes the file atomically.
* Early stop: runs end when alpha ≥ 0.9995 and the water-to-PCM sensible gap is
  < 15 %; `E_window_kJ` for those runs is the end-of-run value (flagged in
  `extrapolated_to_window`).

## 8. Next steps for the paper

1. Re-run the DOE at `cell_size_m: 0.0008` (or apply a stated Richardson
   correction).
2. Replace assumed μ and β with datasheet values and cite them.
3. Reconcile the 17 % loading recommendation with the Phase 3.5 loading sweep.
4. If arrangement must be CFD-supported, add a multi-capsule array case
   (`snappyHexMesh`); the G0 analysis predicts a < 0.02 % effect.

## 9. Fine-mesh (0.8 mm) repeat of the 48-case DOE — added 2026-10-17

Same 48 design points (same seed) re-run at 0.8 mm cells (`cases_fine/`, `results/cfd_doe_results_fine.csv`,
`--cell-size 0.0008 --tag fine`). All 48 cases pass the energy-balance gate (max 2.31 %), all melt inside the
window, wall time per case median 11 min (max 72 min) vs 1.8 min at 1.2 mm.

| Quantity (fine vs 1.2 mm, per case) | Mean | Range |
|---|---|---|
| t50 | +2.2 % | +0.8 … +3.6 % |
| t90 | +5.8 % | +3.0 … +9.0 % |
| t99 | +5.8 % | +2.4 … +10.0 % |

* The mesh shift is systematic and of the size seen in the single-case mesh study (§1: +9 % to 0.6 mm); melt times
  rise on refinement in every case.
* **Grey-box ÷ CFD t90** is 1.58 median (fine) vs 1.67 (coarse); by PCM: lauric acid 1.55–2.29, RT44HC 1.19–1.92,
  OM49 1.21–1.73.
* **φ (PCM-resistance scale)** is 0.34–0.77, median **0.52** (coarse: 0.30–0.73, median 0.47); the ordering of
  cases is preserved (Spearman ρ = 0.994 between meshes). Lauric acid 0.34–0.53, RT44HC 0.42–0.77, OM49 0.46–0.73.
* Conclusion: the grey-box lumped resistance is ≈ 2× too high on either mesh (φ ≈ 0.5, not 0.47); the coarse-mesh
  φ was slightly low because the coarse mesh melts slightly too fast.
* **Not done:** the paired annual optimisation (`cfd_calibrated_greybox.py`) was **not** re-run with the fine φ.
  Expect the same direction and a marginally smaller effect than the +0.06–0.16 % energy shift in §4. To re-run
  without overwriting the 1.2 mm results, pass `--cfd-csv results/cfd_doe_results_fine.csv` and copy the outputs
  first (the script writes fixed filenames).
