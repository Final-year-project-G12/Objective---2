# Changelog — what was done, in order (2026-10-15 → 2026-10-17)

Dates are the session dates; "found" lines are bugs or corrections discovered on the way.

## 1. WSL / OpenFOAM setup
* Ubuntu in WSL would not start (`E_UNEXPECTED`). Cause 1: a stale duplicate registration `Ubuntu` and `Ubuntu-20.04`
  pointing at a missing disk (removed from the registry after a backup). Cause 2: Ubuntu 26.04 image on an old WSL
  (2.4.11). Fix: `wsl --update` (now 3.0.3) and a fresh **Ubuntu-24.04** at `D:\WSL\Ubuntu2404`.
* OpenFOAM **v2406** installed (openfoam.com apt repo); cavity tutorial ran to the end. ParaView 6.2 installed on Windows
  (`D:\Program Files\ParaView 6.2.0`).

## 2. Reading of the project and scope
* Read Objective 2 documents and configs; the grey-box's capsule closure (`R_pcm = r/(5k)`, ×2 convection factor) was
  documented as unvalidated — that became the CFD tier's purpose. Frozen configs were never edited.

## 3. Capsule CFD (tier T2)
* Axisymmetric wedge, butterfly mesh, `buoyantPimpleFoam` + `solidificationMeltingSource`, Robin wall condition from the
  grey-box's own water-side correlation plus the 0.8 mm aluminium shell. PCM data from the O1 database.
* Found/fixed: PyYAML read `1.0e5` as a string; CRLF line endings broke WSL scripts; sampling too coarse for the energy
  gate (10 s now); results of an earlier run polluting a new one (OpenFOAM wrote `*_0.dat`) → runner cleans first;
  `set -u` broke the OpenFOAM `bashrc`; `K_conv` calibration unreachable because the ×2 factor only acts after 50 % melt →
  replaced by the PCM-resistance scale φ.
* Studies: mesh (2.0, 1.2, 0.8, 0.6 mm), Courant 0.25 vs 0.5 (0.2 %), sensitivity (μ, β, Darcy Cu), 24-case pilot, then
  **48-case DOE + 48 conduction twins**; transient WSL launch failures (7 cases) now retried automatically; a
  `controlDict` race in the early-stop edit fixed with an atomic write.
* Paired annual optimisation: 108 Phase-5 designs re-simulated frozen vs calibrated (harness check 7.7e-11 kWh) + ExtraTrees
  search and confirmation.
* **Fine-mesh repeat (0.8 mm, 48 cases)** completed 2026-10-17; analysis in `CFD_FINDINGS.md` §9.

## 4. Literature
* Read the project's 26 paper summaries, two PDFs in full (Avargani 2021, Li 2020) and the 2023 Fetsov solver paper;
  Consensus and web searches. First plan used older papers; **user asked for 2023–2026 only** → rewrote as
  `AI_OPTIMISATION_PLAN_2023_2026.md` (full titles added on request). Fetsov 2023 extracted to `.claude/Sources`.

## 5. Packed-bed solver (tier T2b)
* Cloned `fetc95/pht-openfoam-lab53iacp` (CC BY-NC) and built it on v2406. The shipped `water` example calls a solver that
  is **not in the repository** (`phtMultiSolidFoam`) and its `Tinl.csv` holds non-temperature values → case rebuilt from the paper's
  printed values; initial temperature 305 K (Fig. 7 curves start there; the text lists 298 K).
* Rajasthan 1-D bed generator; with φ = 0.47 the bed's full-melt time matches the capsule CFD, with φ = 1 it is ≈ 1.8× slow.
* Bed driven by the grey-box's hourly temperatures for each regime (9 runs): V1 agrees to 0.2–0.8 K RMSE.

## 6. Components
* **Tank** (axisymmetric): loss verified against the analytic lumped solution (0.8 %); charge and draw cases; stratification
  metrics. Found: a laminar jet at port Re ≈ 3000 makes runs slow (~75 min per simulated hour).
* **Collector** (chtMultiRegionFoam): found/fixed three bugs — missing `p` in the solid region, thin-plate diffusion-number
  time-step collapse (maxDi), and the effective ambient temperature written in °C instead of kelvin; a copy-back race
  overwrote a regenerated case (never run two jobs on one folder). Now matches the textbook estimate within 2.1 %.

## 7. Visualisation
* ParaView scripts and `.pvsm` state files for capsule, tank and collector; matplotlib snapshots; `viz_case.py` runner.
  Found: the OpenFOAM reader in ParaView 6 needs `/water/internalMesh`-style region names; `Reflect` is now
  `AxisAlignedReflect`; the liquid-fraction field name carries a private-use character for `:`.
* The project moved `openfoam_cfd/` next to `objective2-rajasthan/` during the work → `_paths.py` added.

## 8. Not done (carried to `00_INDEX.md` §6)
Validation against experiments; PCM bed inside the tank; closures into the grey-box beyond the capsule φ; sequential/
multi-fidelity AI design; re-running the paired optimisation with the fine-mesh φ.
