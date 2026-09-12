# 03 — Phase 3 Audit: Grey-Box Enthalpy Simulator (All Four States)

Files: `src/simulation/capsule_enthalpy.py`, `collector_model.py`,
`heat_transfer.py`, `hydraulic_model.py`, `demand_profile.py`,
`energy_balance.py`, `tank_model.py`, `run_case.py` — **byte-identical
across all four states**. One simulation = one full year, hourly medoid
weather, 5-minute nominal internal sub-stepping (adaptive).

## Submodels and their literature basis

| Submodel | File | Method | Basis |
|---|---|---|---|
| Collector | `collector_model.py` | Hottel-Whillier-Bliss: `Q=A_c[F_R(τα)I - F_R U_L(T_in-T_amb)]` | Hottel & Whillier (1958); Bliss (1959); standard modern form in Duffie & Beckman (2013) |
| PCM enthalpy | `capsule_enthalpy.py` | Piecewise `h(T)`, clipped liquid fraction `f=clip((h-h_s)/L, 0, 1)` | Standard enthalpy-method PCM formulation, single-group |
| Heat transfer | `heat_transfer.py` | `1/UA_eff = 1/(h_w A_w) + R_wall + R_pcm,eff`; `h_w` via Wakao & Kaguei (1982) | Wakao & Kaguei (1982) packed-bed correlation |
| Hydraulics | `hydraulic_model.py` | Ergun equation | Ergun (1952) |
| Demand | `demand_profile.py` | State's own canonical draw curve | Madadi Avargani et al. (2021) |
| Tank/water balance | `tank_model.py` | Linear-implicit backward Euler, PCM lagged one sub-step | Barqawi (2025) §4c |

## Two bug fixes found and fixed once, present in all four states' copies

1. **Reverse-collector-flow energy-conservation leak**: sub-steps that
   would imply negative collector heat now re-solve with the collector
   off (mimicking a real differential thermostat) before logging
   anything — fixed a 1.6% residual down to floating-point noise.
2. **Adaptive sub-stepping for stiff (high-conductivity) capsules**:
   sub-step count now respects the PCM's own thermal time constant
   (`dt_sub ≤ 0.5·τ_pcm`) — fixed a divergence in the "very high PCM
   conductivity" Gate-2 limiting case.

Both fixes are confirmed intact in every state's Gate 1/2 results (see
`04_PHASE4_VERIFICATION_GATES.md`).

## Solar-fraction definition (shared, with one deviation)

`solar_fraction = 1 − E_unmet / E_demand_ideal`, where `E_demand_ideal`
is the energy to heat the full daily draw from mains temperature to the
delivery target. **Three states use 45 °C** as that target; **Uttarakhand
uses 50 °C** (matching its own Objective 1 `T_DELIVERY_C`, see `01_…`) —
a documented, deliberate per-state deviation in the shared config, not an
inconsistency in the formula itself. No auxiliary/backup heater is
modeled anywhere, so every state's solar fraction is strict relative to
a real installed system with backup heating.

## Nearest verified per-state smoke numbers

| State | Cluster/design | Useful energy (kWh) | Solar fraction | Max PCM/water temp | Residual |
|---|---|---|---|---|---|
| Tamil Nadu | Cluster 0, n-Octacosane, d=0.08/n=24/flow=0.025 | ~1660 | ~51% | above 65 °C limit (see Gate 3) | ~9e-6% |
| Rajasthan | Cluster 0, RT50, d=0.08/n=24/flow=0.025 | ~1581 | ~55% | ~69 °C PCM (896 flagged sub-hours) | ~6.4e-4% |
| Assam | Cluster 0, plain tank, d=0.08/n=8/flow=0.030 (`c0_baseline_noPCM` DOE row — no standalone smoke-run file saved) | 680.9 (100 L/day demand, not comparable to the other three) | 62.5% | 66.84 °C water (plain tank!) | ~3e-12% |
| Uttarakhand | Gate 1 case A, Cluster 0, n-Octacosane, mid design | (see `04_…`) | — | — | 0.000224% |

Assam is the only state without a saved standalone
`results/phase3_simulate_*.json`; its nearest verified numbers come from
Phase 4's Gate cases and Phase 5's DOE table instead (see
`objective2-assam/docs/03_PHASE3_GREYBOX_SIMULATOR.md`).

## Literature review — why grey-box enthalpy rather than a commercial/CFD tool

- **The enthalpy method** for PCM phase-change modeling avoids explicitly
  tracking a moving solid-liquid interface, trading some resolution
  (identical-capsule, single-thermal-group assumption) for a model cheap
  enough to run thousands of times per state in Phase 5/7 — the same
  trade-off Barqawi et al. (2025) and Eldokaishi et al. (2022) make in
  their own PCM-SWH simulation and ANN-surrogate work
  (`Barqawi2025PCMSim`, `Eldokaishi2022ANNPCMSWHModel`).
- **Wakao & Kaguei (1982)**'s packed-bed correlation for the water-to-capsule
  heat-transfer coefficient is chosen over a bespoke CFD correlation for
  the same reason as the Ergun equation in Phase 2 — a standard, citable,
  decades-validated closed form appropriate to a 40-hour-per-state student
  project, not a from-scratch derivation.
- **No commercial thermal-system simulator (TRNSYS, EnergyPlus) or
  MATLAB/Simulink model is used anywhere** — the entire physics stack is
  plain Python, chosen so the same codebase, the same bug fixes, and the
  same verification gates apply identically across all four states
  without a licensing or platform dependency (see each state's
  `HOW_TO_RUN.md`, "Do you need MATLAB or any other simulator? No.").
