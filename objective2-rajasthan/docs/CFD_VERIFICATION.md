# CFD cross-check for Rajasthan Objective 2 (OpenFOAM only)

Written 2026-11-26. **This is a model-to-model consistency check of single capsules, not validation.** The setup does not reproduce the literature benchmark, the mesh is not converged, no experiment of the project capsules exists, and no reported result depends on it. Never write "CFD-validated". ANSYS Fluent was not used for Rajasthan (Tamil Nadu only); there is no OpenFOAM-versus-Fluent comparison.

Source material: `docs/07_OPENFOAM_VALIDATION.md` (legacy file name, content current to 2026-11-14), `rj_openfoam/` (cases, scripts, results), and the Objective 4 capsule diagnosis summarised there. No CFD run was made for the common-plant rebuild.

## 1. What was checked and why

The simulator treats each capsule as one lumped node: conduction resistance `r/(5k)` (constant c = 5) and a liquid-convection factor F = 2 once the melt fraction passes 0.5. Both are assumed, not measured. The CFD asks whether those two numbers are plausible for capsules of the size the optimiser chooses (inner radius near 40 mm).

Method (`rj_openfoam/README.md`): one spherical capsule, 2-D axisymmetric 5-degree wedge, enthalpy-porosity melting (`solidificationMeltingSource`, Boussinesq liquid) in OpenFOAM v2406 under WSL2; melting band Tm +/- 1 K as in the simulator.

## 2. Findings (all from `rj_openfoam/results/`)

- **Literature benchmarks not reproduced.** Against Tan et al. 2009 (n-octadecane sphere) and Dong et al. 2022 the CFD melts about 1.6 to 2 times faster than both experiments. The frozen lumped model is slower than both experiments, so it is conservative for charging.
- **Mesh not converged.** Going from 40 to 80 cells moves t50 by +14.3 % and t90 by +15.8 % (criterion: below 2 %). From the 20 / 40 / 80-cell meshes the observed order is p = -2.81 (t50) and -0.30 (t90), so the study is not in the asymptotic range and no grid-convergence index can be quoted (`of_gci.csv`). A 160-cell mesh was not run (about 16 times the cost).
- **Time step is not the cause:** halving the Courant limit changed t50 by -2.1 % and t90 by 0 % on the 20-cell mesh.
- **Freezing (discharge) check, r0:** minutes to liquid fraction 0.9 / 0.5 / 0.1 are CFD 1.7 / 26.7 / 111 (40 cells) against lumped frozen 7.8 / 23.3 / 55. The frozen model matches at half freeze (within 15 %) and freezes the last 10 % about twice as fast as the CFD (`of_freeze_check.csv`).
- **Design spot-checks, 70 C wall from 30 C (`of_spotcheck.csv`):** the frozen lumped model is 4.3 to 6.5 times slower than the CFD at 50 % melt in all three regimes (minutes to 50 %: r0 CFD 16.3 vs 106.3; r1 28.7 vs 123.0; r2 19.3 vs 93.2).
- **`cfd_closure_v1` (c = 10, F = 5)** was fitted to one CFD case at the edge of the search grid on a mesh that is not converged. It is unvalidated, off by default, and used for no reported result.

## 3. Tank-level check (Objective 4 follow-up, 2026-11-14)

Amanowicz and Turski 2025 (a 6.75 L tank with RT44HC capsules, compared with the paper's printed fits) was run on the same simulator kernel. With sphere dimensions that keep the PCM mass and surface-to-volume ratio of the paper's cuboid capsules, the frozen c = 5, F = 2 give an RMSE of 1.06 K (1.41 K with the tank loss fitted to the water-only case). The fitted c on that benchmark is 5.03, a null result against 5. The single-capsule experiments disagree on the direction (Tan wants c near 10, Dong near 6). Conclusion: the frozen constants stay; the decision of 2026-10-30 is not contradicted.

## 4. How this applies to the common plant

| common-plant design | PCM | inner radius | legacy CFD spot-check | PCM | radius |
|---|---|---|---|---|---|
| regime 0 | savE OM55 | 40.0 mm | r0 | savE OM55 | 39.5 mm |
| regime 1 | PureTemp 60 | 39.1 mm | r1 | PureTemp 60 | 40 mm |
| regime 2 | PureTemp 58 | 40.0 mm | r2 | PureTemp 58 | 40 mm |

The three PCMs are the same and the radii differ by at most 1 mm, so the single-capsule findings above describe nearly the same capsules. What changed is the plant (tank 100 L, collector 2.0 m2, demand 175 L/day), which the CFD never modelled: it simulates one capsule with a fixed wall temperature, not the tank. Viscosity and expansion coefficient of these PCMs are still unsourced, so every CFD number that uses them is provisional.

## 5. What this does and does not support

- Supports: the frozen lumped capsule is not faster than the CFD or the experiments at melting, so PCM benefit is not overstated by capsule speed; at tank level the constants are not contradicted.
- Does not support: any claim that the simulator, the design or the gains are validated. There is no experiment of the project capsules and no CFD of the full tank on the common plant.
- Open: reproduce the benchmark with a converged mesh; source PCM viscosity and expansion; a tank-level CFD or measurement on the 100 L plant.

## 6. Files

`rj_openfoam/results/of_model_parity.csv`, `of_mesh_study.csv`, `of_gci.csv`, `of_v0_benchmark.csv`, `of_v1_benchmark.csv`, `of_freeze_check.csv`, `of_spotcheck.csv`, `of_lumped_vs_benchmarks.csv`, `calib_r0_charge_70_n*.csv`, `paraview/` (3-D revolved copies of the wedge fields), `runs/` (logs and `.dat` files).
