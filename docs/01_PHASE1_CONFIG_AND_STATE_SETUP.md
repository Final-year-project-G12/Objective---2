# 01 — Phase 1 Audit: Frozen Configuration & State Setup (All Four States)

Files: `configs/system_config_shared.yaml`, `configs/design_bounds_shared.yaml`
(byte-identical across all four `objective2-<state>/` repos), plus each
state's own `configs/states/<state>.yaml`. Loader: `src/io_utils.py`.

## Purpose

Freeze everything Phase 2–4 needs, once per state, so the simulator can
never be compared against a moving target
(`O2_Unified_PerState_Execution_Framework.md`, Phase 0).

## The frozen shared config — identical in all four repos

| Category | Value | Source |
|---|---|---|
| Collector | 1.5 m², F_R(τα)=0.75, F_R·U_L=4.5 W/m²K | Domestic FPC baseline (Singh et al. 2025) |
| Tank | 50 L, height:diameter=2:1, U_tank=0.8 W/m²K | Chen et al. (2025), Table 1 |
| PCM integration | Direct encapsulation, Al capsule wall (0.8 mm, 205 W/mK) | Framework doc §3.1 |
| Pump | 0.010–0.050 kg/s, η=0.60 | Framework doc §3.1 |
| Safety | max water 75 °C, max PCM 65 °C, max pressure 3.5 bar | Framework doc §3.1 |
| Delivery | 45 °C in most states; **Uttarakhand uses 50 °C** to match Objective 1's own `T_DELIVERY_C` | See caveat below |
| Solver | backward-Euler (linear-implicit water node, lagged PCM), dt=300 s, adaptive sub-stepping | Barqawi (2025) §4c |
| Selection | Pareto tolerance = 5% | Framework doc §9.5 (pre-declared) |
| Verification | Gate 1 pass < 0.1%, warn < 0.5%; Gate 4 benchmark band 54–84% | Framework doc §5, Singh et al. (2025) |
| Design bounds | Sphere-only, staggered-only; diameter 0.02–0.08 m, count 8–24, PCM volume fraction 0.10–0.20 of tank, flow 0.010–0.050 kg/s | Framework doc's documented 40-hr corner cut |

**Uttarakhand's delivery-temperature deviation is worth flagging in a
methods write-up**: its `configs/system_config_shared.yaml` copy uses
`target_temp_C: 50.0`, matching Objective 1's own `T_DELIVERY_C=50.0`
used to derive `Tm_target_C=57.0`, rather than the 45 °C every other
state's copy uses. This is documented in Uttarakhand's own `01_…` doc as
a deliberate match to that state's Objective 1 pipeline, not a copy-paste
inconsistency — but it means Uttarakhand's `solar_fraction` numbers are
defined against a slightly different reference temperature than the
other three states', which a strict cross-state numeric comparison
should account for.

## Per-state config — side by side

| Field | Tamil Nadu | Rajasthan | Assam | Uttarakhand |
|---|---|---|---|---|
| K (Level-A GMM regimes) | 5 | 3 | 3 | 5 |
| `Tm_target_C` | 57.0 (all clusters) | 57.0 (all clusters) | **44.0** (all clusters — colder mains, smaller lift to delivery) | 57.0 (all clusters) |
| `T_mains_est_C` range | 24.0–26.0 | 18–30 (24.5–25.8 pt. est.) | 15–28 (16.6–19.9 pt. est.) | 7.4–21.8 (**derived** `Ta_mean − 2.0`, not independently sourced) |
| Demand | 300 L/day | 300 L/day | **100 L/day** (50 morning + 50 evening) | 300 L/day |
| PCM shortlist source | Objective 1 MCDM Top-3 (`n-Octacosane` consensus rank-1) | Objective 1 MCDM Top-3 | **Objective 1's Phase 9/10 physics-validated substitute** — K=3 MCDM returned zero confirmed candidates | Objective 1 MCDM Top-3 (`PureTemp 58` consensus rank-1) |
| Elevation handling | Flat 150 m approximation, no dedicated script | Real per-point elevation attach (`00c_attach_elevation.py`) | Valley-to-hill elevation proxy carried through unchanged | **3 inconsistent values coexist** (0 m, flat 1200 m, and a pressure-derived proxy clipped for ~37% of high-elevation readings) — the strongest of the four states' elevation limitations |
| Phase 0 climate-signature check | PASSED (GHI 5.13–5.28 kWh/m²/day, coastal-humid RH 62.5–70.2%) | PASSED, 3/3 regimes (hot-dry, GHI 5.06–5.40) | PASSED, embedded in `assam.yaml` (humid-subtropical, GHI 2.28–2.52 exported / 3.68–4.08 estimated) | **NOT independently verified** — `assam.yaml`-equivalent config self-flags RH_mean as never captured at config-write time |

## Literature review — why these specific frozen values

- **Collector area / U-loss coefficient** and **tank volume/proportions**
  are read directly off recent (2025) PCM-SWH literature rather than
  chosen arbitrarily: the 1.5 m² flat-plate baseline follows Singh et al.
  (2025)'s comprehensive review of PCM-SWH configurations
  (`Singh2025PCMSWH`), and the 50 L / H:D=2:1 tank proportion follows
  Chen et al. (2025)'s Taguchi+GRA-optimized flat-plate/PCM/nanofluid SWH
  rig (`Chen2025TaguchiGRAPCM`, Table 1) — the same paper whose 10/15/20%
  PCM-volume sweep motivates Phase 2's bounds-interaction finding
  (`02_PHASE2_GEOMETRY_CONSTRAINTS.md`).
- **The 300 L/day (Assam: 100 L/day) canonical demand draw** follows
  Madadi Avargani et al. (2021)'s experimental PCM-tank study, which this
  project's Objective 1 pipeline explicitly cites for its own
  `L_required` derivation (`MADADIAVARGANI2021101350`) — Objective 2
  inherits this rather than re-deriving it, so Objective 1's PCM sizing
  target and Objective 2's simulated solar fraction evaluate the same
  household.
- **The backward-Euler, adaptive-sub-stepping solver family** is
  justified the same way Barqawi et al. (2025)'s dynamic PCM-SWH
  simulation study justifies its own numerical scheme — an implicit
  method for the fast (water) state, explicit/lagged coupling for the
  slower (PCM) state, to keep the fast node unconditionally stable
  without needing sub-second timesteps everywhere (`Barqawi2025PCMSim`).
- **The 54–84% Gate-4 solar-fraction calibration band** and Chen et al.
  (2025)'s 94.2% storage-efficiency / 31.7 h retention figure are both
  used as calibration references, not hard release gates — consistent
  with how Singh et al. (2025) itself frames the wide reported range of
  PCM-SWH solar fractions across differing tank/collector/demand ratios
  in the literature it surveys.

## Known, documented Objective 1 limitations carried forward unchanged

Every state carries at least one Objective 1 data-quality caveat into
Objective 2 unchanged (not fixed, per the framework's "Objective 1
changes are a stop-and-rebuild event" rule): Tamil Nadu's flat 150 m
elevation approximation, Rajasthan's real-but-unaudited elevation attach,
Assam's carried-through valley-to-hill proxy, and Uttarakhand's three
mutually-inconsistent elevation values (its own audit finding, the
strongest limitation of the four). None of Phase 2/3 reads elevation
directly, but all four states' climate-regime *assignment* depends on it
upstream in Objective 1.

## How Phase 1 was verified (same method in every state)

`load_state_config(<state>)` in `src/io_utils.py` is exercised on every
Phase 2+ run in every state, so every successful downstream run is an
implicit Phase 1 integration test. There is no separate Phase 1 script
to run in any state beyond the state-specific Phase-0 sanity check.
