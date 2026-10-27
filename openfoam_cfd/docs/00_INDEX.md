# openfoam_cfd — index and status (updated 2026-10-17)

Objective 2 (Rajasthan): AI-driven optimisation of PCM thickness, capsule arrangement, capsule count and
flow rate. This folder is the **OpenFOAM tier** added to the existing Python pipeline
(`../objective2-rajasthan`). Nothing here edits a frozen config or `src/`.

## 1. Documents in this folder

| File | What it contains |
|---|---|
| `00_INDEX.md` | this page: status, file map, how to run, open items |
| `CFD_FINDINGS.md` | **capsule CFD results**: verification, mesh and sensitivity studies, grey-box vs CFD, paired annual optimisation, fine-mesh repeat (§9) |
| `PHT_SOLVER_NOTES.md` | packed-bed OpenFOAM solver (Fetsov & Lutsenko 2023): install, paper case, Rajasthan bed, comparison with the grey-box |
| `COMPONENT_CFD_NOTES.md` | tank and flat-plate collector CFD (water-only tank, collector strip) |
| `VISUALISATION.md` | how to see every result in ParaView (and without it) |
| `SCRIPTS_REFERENCE.md` | every script: purpose, inputs, outputs, command |
| `CHANGELOG.md` | chronological list of what was done, including bugs found and fixed |
| `AI_OPTIMISATION_PLAN_2023_2026.md` | literature (2023–2026) and the staged plan for the AI optimisation; §11 tracks progress |
| `IMPROVEMENT_PLAN.md` | first, broader plan (partly superseded by the 2023–2026 plan; kept for the reasoning) |

## 2. Status by tier

| Tier | Tool | State |
|---|---|---|
| T0 grey-box annual simulator | Python (`../src`) | existing; harness reproduces its results to 1e-10 kWh |
| T2 single-capsule CFD | `buoyantPimpleFoam` + `solidificationMeltingSource` | **built, run, QC-gated**: 48 + 48 conduction + 48 fine-mesh + 6 sensitivity cases |
| T2b packed-bed OpenFOAM | `porousHeatTransferFoam` (cloned, built on v2406) | **built; paper case reproduced; 3 Rajasthan beds driven by hourly grey-box temperatures** |
| Tank | `buoyantPimpleFoam`, axisymmetric | built; loss check 0.8 %; charge and draw run (laminar, water only) |
| Collector | `chtMultiRegionFoam`, one riser strip | built; matches textbook within 2.1 % over 7 cases |
| Pipes / pump | analytic (Ergun) | no CFD |
| AI loop | ExtraTrees + search on calibrated grey-box | run once (paired annual, φ from CFD); sequential / multi-fidelity design **not yet built** |
| External validation | `validate_sphere.py` harness | harness ready and plumbing-checked; **no experiment compared yet** (needs the papers' data) |

## 3. Headline results (all numbers sourced in the linked document)

* The grey-box's lumped PCM resistance `r/(5k)` is about **2× too high**: φ = 0.30–0.73 (1.2 mm mesh, median 0.47) and
  0.34–0.77 (0.8 mm mesh, median 0.52); grey-box melt time is 1.2–2.5× the CFD value (`CFD_FINDINGS.md` §3, §9).
* Natural convection shortens 90 % melt by a median 2.35× (1.8–3.3×) versus conduction only.
* Using the CFD-calibrated closure changes annual useful energy by **0.06–0.16 %**; the Objective-2 conclusion
  (PCM ≈ plain tank, inside the 5 % tolerance) is unchanged (`CFD_FINDINGS.md` §4).
* The single-node grey-box and the packed-bed OpenFOAM model agree to 0.2–0.8 K RMSE on the PCM temperature over
  48 h when given identical forcing — axial structure does not change the PCM response for the Phase-7 designs
  (`PHT_SOLVER_NOTES.md` §C).
* A stratified tank delivers 27 L at ≥ 45 °C from a state where a fully mixed single node (43 °C) delivers none;
  energy totals are unaffected, temperature-threshold metrics are (`COMPONENT_CFD_NOTES.md` §1).
* The collector CFD reproduces the frozen `F_R·U_L = 4.5` (CFD 4.45) and, with τα = 0.84, `F_R·τα = 0.75`
  (`COMPONENT_CFD_NOTES.md` §2).

## 4. What is NOT validated (read before citing anything)

1. **No capsule or tank CFD result has been compared with a measurement.** Only internal checks exist
   (energy balance < 3 %, analytic loss, textbook collector, paper-curve reproduction by eye).
2. **Assumed inputs:** liquid viscosity and expansion of the PCMs (±10–12 % melt time, `CFD_FINDINGS.md` §2), water
   β, all collector geometry/optics (pitch, tube, plate, U_L, τα).
3. **Discretisation:** 1.2 mm mesh under-predicts t90 by ≈ 6–9 % (0.8 mm repeat, 0.6 mm single case).
4. **Omitted physics in the capsule model:** volume change on melting, solid sinking / close-contact melting,
   supercooling; isothermal melting at Tm.
5. **Tank:** laminar at port Reynolds number ≈ 3000, no diffuser, ports on the axis; **collector:** square channel
   replaces the round tube.
6. Arrangement is **not** resolved by CFD (one capsule has no neighbours).

## 5. How to run the main things (Windows PowerShell, from `scripts/`)

```powershell
cd "D:\Final Year Project\OBJECTIVE2\Objective---2\openfoam_cfd\scripts"
python run_doe.py --mode doe --n-per-pcm 16 --workers 8                 # capsule DOE (1.2 mm)
python run_doe.py --mode doe --n-per-pcm 16 --workers 8 --cell-size 0.0008 --tag fine
python cfd_calibrated_greybox.py --workers 8                            # calibrated annual optimisation
python pht_vs_greybox.py --dt 5                                         # packed-bed vs grey-box, 3 regimes
python collector_sweep.py --workers 3                                   # collector efficiency sweep
python viz_case.py --name my_capsule --pcm RT44HC --d 0.06 --mdot 0.03 --dT 15 --t-end-h 1.2   # for ParaView
```

All other commands are in `SCRIPTS_REFERENCE.md`; visualisation in `VISUALISATION.md`.

## 6. Open items (in priority order)

1. Validate against **2023+ experimental data** (papers to supply are listed in `AI_OPTIMISATION_PLAN_2023_2026.md` §9; Fetsov 2023 already added).
2. Replace assumed μ, β with datasheet or measured values.
3. Re-run `cfd_calibrated_greybox.py` with the fine-mesh φ (§9 of `CFD_FINDINGS.md`).
4. PCM capsule bed inside the tank CFD (needs buoyancy-capable porous coupling).
5. Feed collector `F_R(ṁ)` and the stratified-delivery correction into the grey-box and re-run the paired annual comparison.
6. Tank: turbulence model, diffuser, inlet-height sweep, 112.5 L (IS 12976) case.
7. Reconcile the 17–18 % PCM loading recommendation with the project's loading sweep.
8. Sequential (GP) design and multi-fidelity chain from the plan.
