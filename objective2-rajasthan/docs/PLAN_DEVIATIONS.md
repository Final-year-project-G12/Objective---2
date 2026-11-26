# Changes from the original plan (Rajasthan)

| Item | Original plan | What was done | Why |
|---|---|---|---|
| Daily demand | 100 L/day (plan Rev 9, rule R1) | 175 L/day of 45 C water, declared 2026-11-25 before any L4-L9 result on this plant | At 100 L/day the plain tank covers 98-99 % of the demand, so PCM adds about 0 (scan: -1.1 / -3.6 / -4.6 kWh/yr). Same value as Tamil Nadu so the states stay comparable. 70, 100 and 150 L/day, a 150 L tank and the legacy 300 L/day are supplementary cases. |
| Search box | Four variables incl. flow | Three variables (radius 10-40 mm, fraction 2-40 %, arrangement); flow fixed 0.030 kg/s | Rule R6. |
| Stack anchor | Robust three-position objective (R7) | As planned | Every design at bottom, centre, top; ranked on the mean, rejected if the worst anchor is not above the band. |
| Dense grid | 720 points | 240 designs per regime on the rank-1 PCM (213 simulated, 27 rejected by geometry), centre anchor, cheap fidelity | Compute time. Epsilon vs search is reported (0 / 0.96 / 0 kWh, inside the band). |
| Search budget | NSGA-II + AL 5 rounds + vertex | 3-5 active-learning rounds per pair, hypervolume stop rule | Compute time; stop rule unchanged. |
| Repeatability band | Years, dt, nodes, properties, members, demand, mains | As planned (the full band was used in the funnel) | Unlike Tamil Nadu, no core-band substitution was needed; the worst-anchor select gains are 1.7-4x the band. |
| Test and report years | R3 | 2006-2010 one-shot test, 2022-2025 report-only, 2016-2019 explore, 2020-2021 select | As planned. |
| Overheat hours | Not a trade-off in the plan | Reported as a cost in every table | PCM tanks hold less water; guard hours rise in every regime. |
| MATLAB M1 | Water-only vs PCM, PCM alternatives, gate | Done as planned (12 runs, gate PASS). Not extended to Tamil Nadu's seven Fluent criteria, animations or day-type figures | Those belong to the Fluent study (L8), which Rajasthan does not have. |
| ANSYS Fluent (L8) | Tamil Nadu only | Not done | Out of scope by decision. |
| Objective 3 | Rebuilt after O2 | Contract and folder only; no O3 code or training | Out of scope of this document. |
