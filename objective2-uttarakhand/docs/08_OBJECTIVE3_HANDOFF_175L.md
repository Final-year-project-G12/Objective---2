# 08 - Objective 3 hand-off: 100 L / 2.0 m2 plant at 175 L/day (Uttarakhand, branch `uttarakhand-o2-175L`)

**Contract:** `results/obj3_environment_contract_uttarakhand_100L_d175.json`, written by
`src/handoff/build_obj3_contract_common100L.py` (`python pipeline.py --state uttarakhand --stage handoff`). On this branch it supersedes
`07_OBJECTIVE3_HANDOFF_COMMON100L.md` (100 L/day, water-only everywhere) and the legacy 50 L contracts in `results_legacy_50L_v3/`.
Full record and the deviation from rule R1 (100 L/day): `REBUILD_175L.md`.

## What Objective 2 hands over

| Item | Value |
|---|---|
| Plant | 100 L tank, 2.0 m2 flat-plate collector, **175 L/day**, 10-node tank, flow fixed at 0.030 kg/s |
| Service threshold | 45 C primary; 50 C secondary report for Uttarakhand (never pooled with 45 C kWh) |
| Simulator step | search 150 s; report / test 18.75 s (37.5 s fails the R5 halving gate at 175 L/day) |
| Safety | shield in the kernel: water guard 72 C / hard 75 C, PCM guard 62 C / hard 65 C |
| Regimes | 4 (medoids UKP_0014 / UKP_0029 / UKP_0025 / UKP_0041) |
| Actions | ENABLE / BYPASS of the collector loop (plan 8.3); flow is not an action |

## Installed design per regime

| Regime | Installed design | PCM mass | select g_window mean / worst anchor | test 2006-10 worst anchor | band |
|---|---|---|---|---|---|
| 0 | PureTemp 58, R 40 mm, 39.8 %, 140 capsules, staggered | 33.4 kg | +75.2 / +60.7 | +62.7 | 20.8 |
| 1 | PureTemp 58, R 40 mm, 39.8 %, 140 capsules, single-layer | 33.4 kg | +40.9 / +34.1 | +38.3 | 17.2 |
| 2 | savE OM55, R 36.1 mm, 40.0 %, 190 capsules, radial | 35.0 kg | +71.3 / +71.3 | +71.3 | 14.0 |
| 3 | **water-only 100 L tank** (best PCM reference PureTemp 53, 2 %: -0.5 / -2.9, NOT recommended) | - | - | -3.1 | 15.4 |

g_window in kWh/yr against the water-only twin at the same flow. Regime 1 is the weakest PCM case (report-year worst anchor +22.7
against a band of 17.2; 7 of 17 one-at-a-time sensitivity cases lose the PCM verdict).

## Rules for Objective 3 (from the plan)

- **Year roles (R3):** train 2016-2019; validate 2020-2021; 2022-2023 extra training only now that O2 is frozen; 2024-2025 report-only;
  2006-2010 is Objective 3's own one-shot test under its OWN lock (the O2 lock in `results/locks/` belongs to O2).
- **Exposure:** 2006-2010 was used by O2 on the 100 L/day plant, by this O2 confirmatory test, and by the old (50 L) Objective 3 test;
  disclose this.
- **Goal:** in regimes 0-2 the controller manages a PCM tank (charge before the evening window, avoid shield-hours); in regime 3 there is
  no PCM to manage and the realistic goal (plan 8.5) is fewer shield-hours at >= 95 % of B0 annual delivery. Compute the H2 headroom
  (near-oracle minus B0) before any DRL.
- **Hygiene (R9):** the water-only tank reaches >= 60 C for >= 1 h on 69 / 57 / 55 / 20 % of 2006-2010 days (regimes 0-3), longest gaps
  46 / 56 / 62 / 112 days. A controller must not make this worse than B0 by more than the band; regime 3 may need a scheduled hygiene
  cycle (plan 8.4).
- **Reward (8.5):** the form is fixed; the weights are not chosen here and must be pre-registered before training.
- **Observation schema:** unchanged; T_pcm_C and f_melt are live in regimes 0-2 and degenerate in regime 3.

## Open items carried over

- Collector area basis (aperture vs absorber) and a source for F_R(tau alpha) 0.75 / F_R U_L 4.5.
- No CFD on this plant (OpenFOAM optional per plan section 6); no hardware validation (Objective 4 / hardware).
- MATLAB checkpoint M1 passed at 175 L/day (`results/m1_matlab/m1_gate.txt`); M2 is built after the Objective 3 agent is trained.
- Auxiliary heat at 45 C (2020-2021): water-only 446 / 572 / 632 / 1175 kWh/yr; the PCM designs save 87 / 55 / 87 kWh/yr in regimes 0-2.
- All three PCM picks sit at the 40 % upper fraction bound (frozen; reported, not moved).
