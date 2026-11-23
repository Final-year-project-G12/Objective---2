# 07 - Objective 3 hand-off on the common 100 L plant (Uttarakhand)

**Contract:** `results/obj3_environment_contract_uttarakhand_common100L.json`, written by
`src/handoff/build_obj3_contract_common100L.py` (`PYTHONPATH=. python -m src.handoff.build_obj3_contract_common100L`). It supersedes the
legacy 50 L contracts in `results_legacy_50L_v3/` (plan section 2.2), which must not be used. Full record: `REBUILD_COMMON100L.md`.

## What Objective 2 hands over

| Item | Value |
|---|---|
| Plant | 100 L tank, 2.0 m2 flat-plate collector, 100 L/day, 10-node tank, flow fixed at 0.030 kg/s |
| Service threshold | 45 C primary; 50 C secondary report for Uttarakhand (never pooled with 45 C kWh) |
| Safety | shield in the kernel: water guard 72 C / hard 75 C, PCM guard 62 C / hard 65 C |
| Regimes | 4 (medoids UKP_0014 / UKP_0029 / UKP_0025 / UKP_0041) |
| **Installed design** | **water-only 100 L tank in every regime**: no PCM design's worst-anchor gain exceeds the repeatability band (5-6 kWh/yr) on 2020-2021, and the one-shot 2006-2010 test confirms it |
| Best PCM design per regime | recorded and tested under `best_pcm_design_reference`, NOT recommended (gains -0.3 to +1.9 kWh/yr) |
| Actions | ENABLE / BYPASS of the collector loop (plan 8.3); flow is not an action |

## Rules for Objective 3 (from the plan)

- **Year roles (R3):** train 2016-2019; validate 2020-2021; 2022-2023 extra training only now that O2 is frozen; 2024-2025 report-only;
  2006-2010 is Objective 3's own one-shot test under its OWN lock (the O2 lock in `results/locks/` belongs to O2).
- **Exposure:** 2006-2010 is unseen for Objective 2, but the old (50 L) Uttarakhand Objective 3 test used it; disclose this.
- **Goal:** with a water-only tank there is no PCM to manage; the realistic goal (plan 8.5) is fewer shield-hours at >= 95 % of B0
  annual delivery in every regime, with evening retention reported. Compute the H2 headroom (near-oracle minus B0) before any DRL.
- **Hygiene (R9):** the water-only tank reaches >= 60 C for >= 1 h on 76 / 68 / 65 / 33 % of 2006-2010 days (regimes 0-3), with gaps up
  to 90 days in regime 3. A controller must not make this worse than B0 by more than the band; regime 3 may need a scheduled hygiene
  cycle (plan 8.4).
- **Reward (8.5):** the form is fixed; the weights are not chosen here and must be pre-registered before training.
- **Observation schema:** kept from the legacy contract; T_pcm_C and f_melt are degenerate (no PCM) on the water-only design.

## Open items carried over

- Collector area basis (aperture vs absorber) and a source for F_R(tau alpha) 0.75 / F_R U_L 4.5.
- No CFD on the common plant (OpenFOAM optional per plan section 6); no hardware validation (Objective 4 / hardware).
- MATLAB checkpoint M1 passed (results/m1_matlab/m1_gate.txt); M2 is built after the Objective 3 agent is trained.
- Auxiliary heat: an ideal booster would need 45-292 kWh/yr at 45 C on the water-only tank (regime 3 the most); PCM does not reduce it.
- PCM becomes useful only when the daily draw exceeds the tank volume: at 150 L/day on the 100 L tank the best worst-anchor gains are
  +28 / +5 / +32 / -7 kWh/yr (regimes 0-3), on the legacy 2.5 m2 / 300 L/day plant +119 / +70 / +113 / -10, while 70 L/day and a
  150 L tank at 150 L/day stay water-only (`REBUILD_COMMON100L.md` 3i; sensitivity cases, never used for selection).
