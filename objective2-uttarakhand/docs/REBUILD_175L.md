# Uttarakhand Objective 2 on the 100 L / 2.0 m2 plant at 175 L/day (branch `uttarakhand-o2-175L`)

Written 2026-11-23, BEFORE any run of the chain at 175 L/day. Everything not listed here is unchanged from the common-plant rebuild
(`docs/REBUILD_COMMON100L.md`: frozen decisions section 2, search protocol 3d, selection funnel 3e, band recipe 5).

## 1. Decision

- **Demand: 175 L/day** (litres drawn from the tank per day, 45 C delivery threshold). Tank 100 L, collector 2.0 m2, flow 0.030 kg/s,
  45 C primary / 50 C secondary, fraction 2-40 %, robust bottom/centre/top anchor (R7), year roles (R3) - all unchanged.
- **Who:** user / project team decision of 2026-11-23 (group G12). Approval by the guide is to be recorded here when given.
- **Basis:** the plan itself (Revision 9, section 1.1) states that the 100 LPD rating is quoted at about 60 C, "which is roughly
  175 L/day of 45 C water, so 100 L/day at 45 C is the lighter reading". 175 L/day is therefore the plan's own 45 C reading of the
  same 100 LPD plant, not a new plant size.
- **Profile:** the same hourly shape as the 100 L/day profile, every hour x 1.75 (`data/demand/demand_profile_uttarakhand.csv`;
  the 100 L/day profile is kept at `data/legacy/demand_profile_uttarakhand_100L.csv`).

## 2. Deviation from the common rulebook (stated openly)

Rule R1 fixes 100 L/day in all four states. This branch departs from R1 for Uttarakhand only. Results here are therefore **not
pooled** with other states' 100 L/day results without saying so. The 100 L/day result (water-only in all four regimes) is kept as
a reported result (branch `uttarakhand-o2-common100L`, and `results_archive_100Lday/` on this branch); it is not deleted or hidden.

## 3. Prior exposure (what was seen before this decision)

This decision was **not** made blind. Before it, the following had been seen:

1. The full 100 L/day rebuild, including its one-shot 2006-2010 test (lock `results_archive_100Lday/locks/`), its select-year and
   report-year results: water-only in every regime.
2. Post-result plant-case diagnostics on ONE representative explore year per regime, centre/three anchors, coarse grid
   (`results_archive_100Lday/supp_case_d150.csv`, `supp_case_d175.csv`, `supp_case_d200.csv`): at 175 L/day the best worst-anchor
   g_window was about +37 (regime 0), +3 (regime 1), +37 (regime 2), -9 (regime 3) kWh/yr. These were the reason for the choice.

Consequences, declared now:
- The 2006-2010 weather was used once for Objective 2 on the 100 L/day plant (design outcomes only, water-only designs and the
  reference PCM designs). The 175 L/day one-shot test runs under a new lock (the plant hash now includes the demand profile), but it
  is **not** an untouched test of the 175 L/day choice of demand. Report it as "confirmatory test, 2006-2010, prior O2 exposure on
  the 100 L/day plant".
- The choice of demand was informed by explore-year diagnostics. The design itself (PCM, radius, fraction, arrangement) is chosen
  only by the frozen chain below.

## 4. What is frozen before the run (no change after results are seen)

- Search protocol and fidelities: `REBUILD_COMMON100L.md` 3d (cheap 150 s representative year; full 37.5 s; Spearman >= 0.7).
- Selection funnel: `REBUILD_COMMON100L.md` 3e, including R7 (worst-anchor gain must exceed the band) and the water-only verdict.
- Band recipe: `REBUILD_COMMON100L.md` 5, unchanged, **including the demand term**, which now means 175 L/day x 0.8 and x 1.2
  (140 and 210 L/day). The band is re-measured at 175 L/day; it is not reused from the 100 L/day run and the demand term is not
  dropped (contrast: Assam deviation D1, plan Revision 14).
- Expected from the diagnostics (stated so the result can be checked against it, not used to choose anything): PCM likely in
  regimes 0 and 2; regime 1 borderline / water-only; regime 3 water-only. Whatever the frozen chain gives is the result.

## 5. Code changes on this branch

- `configs/states/uttarakhand.yaml`: `daily_total_L: 175.0`; demand CSV regenerated x 1.75.
- `src/weather/roles.py`: the plant hash also covers the demand CSV (plan R20), so the 175 L/day lock path differs from the 100 L/day one.
- `scripts/r10_supplementary.py`: demand cases in absolute L/day (d70, d100, d150, d200, legacy 2.5 m2 / 300 L/day, t150).
- `src/handoff/build_obj3_contract_common100L.py`: writes `obj3_environment_contract_uttarakhand_100L_d175.json`.
- `results/` of the 100 L/day run moved to `results_archive_100Lday/` (git mv; untouched).

## 5b. L1-L3 findings at 175 L/day (2026-11-23; `results/l3_*.csv`)

- L1 / L2: O1 manifest and weather inventory regenerated (inputs unchanged; new plant hash `672763eebb7c` before the step change below).
- **Energy closure:** residual 0.0 % of collector energy in every case. Pass.
- **Time step (plan R5 / 4.2, gate < 0.05 % per halving of E_del45_window):** 37.5 -> 18.75 s changes the water-only tank by
  **0.057 %** in regime 0 (0.047 / 0.042 / 0.003 % in regimes 1-3; PCM designs <= 0.012 %), so **37.5 s fails the gate** at
  175 L/day (it passed at 100 L/day). One more halving (`scripts/r3b_timestep_extend.py`): 18.75 -> 9.375 s changes it by at most
  0.028 % -> **18.75 s passes**. Applied by the frozen rule: the report / selection / test step is **18.75 s**
  (`configs/design_space.yaml` model.report_timestep_s); the search (cheap) step stays 150 s. The band's time-step term becomes the
  report step against its half (18.75 vs 9.375 s) and its node term is measured at 18.75 s (`scripts/g9_band.py` variants dt_report,
  dt_half, nodes20_report) - same recipe as section 5 of REBUILD_COMMON100L.md, "the remaining discretisation error at the report step".
- **Nodes 10 -> 20** (37.5 s, informational; the band re-measures it at 18.75 s): paired gain +4.6 to +8.6 kWh/yr in regimes 0-2,
  -4.3 to -4.7 in regime 3. A large band component again.
- **IS 12976 standing loss:** unchanged by demand (no draw): 4.8 K at 20 C (pass); cold case 6.9 / 7.4 / 7.6 K pass, 9.4 K in
  regime 3 at -18.3 C (fail, cold-climate limitation, reported).
- Verification designs V30 / V40 (R 30 mm, staggered, centre, 2018, 37.5 s): g_window +47 / +52 (regime 0), +18 / +18 (1),
  +8 / +6 (2), -48 / -65 (3) kWh/yr. Physics check only, not a design result.

## 6. Level tracker

| Level | Status |
|---|---|
| L0 decision record (this file) | done 2026-11-23 |
| L1-L3 o1 / weather / verify | done 2026-11-23: section 5b (report step 18.75 s by the R5 gate) |
| L4-L7 baseline ... select | pending |
| L9 test, report, handoff | pending |
| M1, figures, supplementary, manifest | pending |
