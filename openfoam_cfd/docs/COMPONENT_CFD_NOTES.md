# Solar-water-heater component CFD (tank, collector) — status 2026-10-17

Scope chosen: **tank + collector CFD**, each feeding a closure back into the grey-box; pipes and pump stay
analytic (Ergun, `src/design/geometry.py`). Stages: (1) tank, water only; (2) PCM bed inside the tank;
(3) collector strip; (4) closures into the grey-box.

## 1. Tank (OpenFOAM `buoyantPimpleFoam`, axisymmetric wedge) — scripts `tank_make_case.py`, `tank_run.sh`, `tank_postprocess.py`
Geometry and loss are the frozen ones: 50 L, H/D = 2 (D = 0.317 m, H = 0.634 m), wall U = 0.8 W/m²K, water
cp/ρ/k/Pr from `system_config_shared.yaml`. Expansion β = 4.6e-4 1/K is a standard water value **not in the
project config (assumed)**. Laminar (port Reynolds number ≈ 3000 at 0.03 kg/s with a 20 mm port — near
transition, so a turbulence model is the next upgrade); central 20 mm ports; no diffuser; no coil; 4 200–6 000 cells.

| Check / case | Result |
|---|---|
| **Standing-loss verification** (idle, 55 °C start, 25 °C ambient, 2 h) | mean-temperature drop 0.649 K (CFD) vs 0.644 K (analytic lumped exp(−UA t/mcp), UA = 0.631 W/K): **0.8 % difference** |
| **Charge** (hot 60 °C at the top port, 0.03 kg/s, tank starts at 25 °C) | stratified fill: hot layer grows downward, outlet stays at 25 °C until ≈ 24 min (plug-flow time 28 min) then jumps; MIX number 0.05–0.2 during the fill (well stratified) |
| **Draw** (0.03 kg/s of 25 °C mains at the bottom; tank starts with 30 L at 55 °C above 20 L at 25 °C) | outlet stays ≈ 55 °C until 18 L, falls below the 45 °C delivery target at **27 L = 90 % of the hot volume** (thermocline mixing costs ≈ 10 %); MIX rises 0.03 → 0.53 → 0.86 |

**Why it matters for the grey-box (single node).** The same stored energy as the draw case corresponds to a
fully mixed temperature of (30 × 55 + 20 × 25)/50 = 43 °C — **below the 45 °C target**. A single node would
therefore deliver *no* water at ≥ 45 °C, while the stratified tank delivers 27 L at ≥ 45 °C. The grey-box
computes unmet energy from an **energy deficit** against the target (`run_case.py`), so its energy totals are not
affected directly; but any *temperature-threshold* metric (`delivery_temp_hours`, hours within ± 2 K) is
biased by the single-node assumption in the direction of **under-estimating** delivery from a partly hot tank.
This is a CFD-based quantification of a limitation the project already lists; not yet applied to any result.

Run time: ~75 min of wall time per simulated hour at 0.03 kg/s (jet-limited time step); the idle case 5 min.
Not done: turbulence, diffuser/stratifier, inlet height sweep, 112.5 L (IS 12976) tank, PCM bed.

## 2. Collector strip (OpenFOAM `chtMultiRegionFoam`) — scripts `collector_make_case.py`, `collector_run.sh`, `collector_postprocess.py`, `collector_sweep.py`
One half riser strip: copper plate + tube + laminar water, conjugate heat transfer, 14 800 cells, 300 s to steady
state in ≈ 140 s of wall time. **[ASSUMED]** inputs (not in the project config): riser pitch 0.12 m, length 1.2 m,
tube flow area of a 10 mm tube (square channel of equal area — fully developed Nu 3.6 instead of 4.36), wall 0.8 mm,
plate 0.3 mm copper, **U_L = 5 W/m²K, τα = 0.80, G = 1000 W/m²**. From the project: collector area 1.5 m² (→ 10.4
risers), loop flow split equally over the risers, water properties. Top boundary: absorbed flux and loss written
as `q'' = U_L (T − T_a) − S` through `externalWallHeatFluxTemperature` with `Ta_eff = T_a + S/U_L` (kelvin!).

Bug found and fixed on the way: the first run wrote `Ta_eff` in °C, which cooled the plate (outlet 23.7 °C below
the 30 °C inlet); after the fix the energy balance closed against the textbook estimate.

| Case (loop flow, inlet T) | Re (channel) | η CFD | η textbook | outlet T CFD / textbook [°C] | F_R CFD / textbook |
|---|---|---|---|---|---|
| 0.03 kg/s, 30 °C | 500 | 0.690 | 0.683 | 38.24 / 38.16 | 0.890 / 0.881 |
| 0.03, 40 | 500 | 0.645 | 0.639 | 47.71 / 47.63 | 0.890 / 0.881 |
| 0.03, 50 | 500 | 0.601 | 0.595 | 57.17 / 57.10 | 0.890 / 0.881 |
| 0.03, 60 | 500 | 0.556 | 0.551 | 66.64 / 66.58 | 0.890 / 0.881 |
| 0.03, 70 | 500 | 0.512 | 0.507 | 76.11 / 76.05 | 0.890 / 0.881 |
| 0.01, 40 | 167 | 0.593 | 0.606 | 61.25 / 61.70 | 0.818 / 0.836 |
| 0.05, 40 | 833 | 0.656 | 0.646 | 44.70 / 44.63 | 0.905 / 0.891 |

CFD and the Duffie–Beckman estimate agree within **2.1 % in η** at every point (max), outlet temperatures within
0.5 K. Fit to the 0.03 kg/s series: **F_R·τα = 0.712, F_R·U_L = 4.45 W/m²K** (η = F_Rτα − F_R U_L (T_in − T_a)/G).

**What this says about the frozen numbers** (`F_R·τα = 0.75`, `F_R·U_L = 4.5`): F_R·U_L = 4.45 is reproduced
(U_L = 5 gives F_R = 0.89); F_R·τα = 0.712 vs 0.75 corresponds to τα = 0.84 instead of the assumed 0.80. So the
frozen pair is **consistent with a physically sensible strip (F_R ≈ 0.89–0.90)**, but CFD cannot confirm τα or
U_L themselves (optical and loss inputs) — those need a measurement or datasheet. F_R falls with lower flow
(0.82 at 0.01 kg/s) and rises slightly with higher flow (0.905 at 0.05): the grey-box uses a fixed F_R, so at the
low end of the flow bounds the collector is over-credited by ≈ 8 % in F_R. Not applied to the grey-box.

## 2b. Seeing these cases
ParaView state files and headless image scripts are described in `VISUALISATION.md` (tank: `cases_tank/<case>/<case>_T.pvsm`; collector: `cases_collector/test_T30/collector_T.pvsm`). Images already generated: `cases_tank/{charge,draw}/paraview/`, `cases_collector/test_T30/paraview/` (cross-sections at x = 0.05, 0.6, 1.19 m and a longitudinal section), `tank_profiles.png` in each tank case.

## 3. Still open
* Stage 2: PCM capsule bed inside the tank CFD (needs a coupled porous source; the packed-bed solver of
  Fetsov & Lutsenko has no buoyancy in its shipped cases — check before relying on it).
* Tank: turbulence model, diffuser, inlet-height and aspect-ratio sweep, IS 12976 volume (112.5 L).
* Stage 4: feed `F_R(ṁ)` and a stratified-delivery correction into the grey-box through the same in-memory
  closure mechanism used for the capsule (`cfd_calibrated_greybox.py`), then re-run the paired annual comparison.
* Pipes and pump: analytic only (Ergun); no CFD.
