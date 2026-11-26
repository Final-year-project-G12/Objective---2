# Objective 3 - inputs from Objective 2 (Rajasthan), and what to do next

Written 2026-11-26 against the common-plant Objective 2 run (test run `o2test_c5b9324ead83`, plant hash `eb67320ff3cb`). Do not use any legacy number (50 L plant).

## 0. What changed against the legacy handoff

| | legacy (50 L, v3) | current |
|---|---|---|
| tank / collector | 50 L / 1.5 m2 | 100 L / 2.0 m2 |
| daily draw | 300 L/day (O2 sizing study) | 175 L/day of 45 C water (declared, see `docs/REBUILD_COMMON100L.md` section 8) |
| flow | searched | fixed at 0.030 kg/s |
| PCM fraction box | 2-30 % | 2-40 %, inner radius 10-40 mm |
| held-out test | 2011-2015 | 2006-2010, lock keyed to the plant hash |
| anchor | centre | robust: bottom, centre, top |
| delivery threshold | not as here | 45 C primary, 50 C secondary report |

## 1. The file Objective 3 reads

`obj3_environment_contract_rajasthan_common100L.json` in this folder. Parse the JSON; do not hand-copy numbers from this document. Run `scripts/r24_check_o3_contract.py` first.

## 2. The designs (read from the contract)

| regime | PCM | O1 rank | capsules | inner radius | PCM fraction | PCM mass | arrangement |
|---|---|---|---|---|---|---|---|
| 0 | savE OM55 | 1 | 140 | 40.0 mm | 39.8 % | 35.1 kg | staggered |
| 1 | PureTemp 60 | 1 | 126 | 39.1 mm | 33.5 % | 30.3 kg | staggered |
| 2 | PureTemp 58 | 2 | 140 | 40.0 mm | 39.8 % | 33.4 kg | staggered |

Every PCM is in Objective 1's own Top-3 for that regime (the check asserts it). O1 regimes: 0 = Udaipur-medoid cluster, 1 = Nagaur-medoid, 2 = Jaipur-medoid (`data/objective1/`).

## 3. What the baseline is, so Objective 3 does not over-claim

B0 (always charge when the sun is up; the safety shield acts inside the kernel) on the PCM tank, test years 2006-2010, kWh/yr paired against a water-only tank:
g_window 158.2 / 70.8 / 125.2 (regimes 0 / 1 / 2); overheat-guard hours +797 / +416 / +739 h/yr more than the water-only tank. The overheat-guard hours are the room Objective 3 has: the goal is fewer guard hours at at least 95 % of B0 delivery (plan 8.5), not more delivered energy.
Regime 1 has the thinnest margin (worst-anchor gain above its band by about 12 to 28 kWh/yr in the report and test years), so any DRL gain there must be judged against that band, not against zero.

## 4. Constraints

- Objective 3 controls ENABLE / BYPASS of the collector loop only. It may not change the tank, collector, PCM, capsules, flow, safety limits or physics.
- The safety shield is inside the kernel and cannot be switched off by a policy.
- Year roles for O3 (plan R3): train 2016-2019, validate 2020-2021, extra train 2022-2023 after O2 freeze, report-only 2024-2025, and a confirmatory test on 2006-2010 under O3's own lock. 2006-2010 was already used by the OLD Rajasthan O3 test, so it is not unseen for Objective 3; declare that.
- Hygiene guardrail (plan R9): the PCM tank's share of days with stored water at 60 C or more for 1 h must not be worse than B0 by more than the band. Water-only reference: 0.879 / 0.911 / 0.861.
- No experimental validation exists. CFD is a model-to-model check only; never write "CFD-validated" (`docs/CFD_VERIFICATION.md`).

## 5. What the design is not

- It is the best found inside the declared box, not a global optimum: the 40 mm radius end binds in nearly every Pareto front.
- The PCM gain exists at 175 L/day only. With a 150 L tank, or at 100 L/day or less, it is about zero (`docs/RESULTS_COMMON_PLANT.md` section 8). If Objective 3 or 4 changes the plant, rerun Objective 2.
- Regime 0 rests on only 4 member points for its band.
- Collector area basis and parameters (F_R tau alpha 0.75, F_R U_L 4.5) have no project source.

## 6. Suggested next steps

1. Compute the headroom gate H2 (near-oracle minus B0) before any DRL training, per regime, on 2016-2021.
2. Pre-register the reward weights, then train on 2016-2019, validate 2020-2021.
3. Report guard hours, delivered energy (at least 95 % of B0) and hygiene on 2024-2025, then run the confirmatory test once under O3's own lock.
