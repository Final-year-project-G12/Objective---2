# Changes from the original plan

| Item | Original plan | What was done | Why |
|---|---|---|---|
| Daily demand | 100 L/day (plan Rev 9, rule R1) | 175 L/day of 45 C water (user decision 2026-11-23) | At 100 L/day the plain tank covers 99 % of the demand, so PCM cannot add energy (scan: -0.6 kWh/yr). 175 L/day is the 45 C equivalent of a 100 LPD heater rated at 60 C. 100 and 150 L/day and the legacy 300 L/day are sensitivity cases. |
| PCM candidates | O1 shortlist (Option B), optional 45 C re-rank | O1 shortlist only, nothing added (user decision) | A 45 C screen at 100 L/day showed 44-47 C PCMs would do better; kept as a limitation, not acted on. |
| O1 inputs | Frozen 2026-10-29 copy | Re-synced to the 2026-11-10 O1 run (11 files), manifest with hashes | Shortlist, ranks and labels identical; regime-0 medoid is a 24-way tie, O2 medoids kept (TNP_0006 / 0007 / 0001). |
| Stack anchor | Robust three-position objective (R7) | Implemented: every design simulated at bottom, centre, top; ranked on the mean, rejected if worst-anchor gain <= 0 or inside the band | As planned; added as code (evaluate_design_robust). |
| Search box | Four variables incl. flow | Three variables (R_in 10-40 mm, fraction 2-40 %, arrangement); flow frozen at 0.030 kg/s | Rule R6. |
| Taguchi factors | radius, fraction, flow, arrangement | radius, fraction, anchor, arrangement | Flow is frozen, anchor takes its place. |
| Fidelity screen | Cheap screen, threshold before the run | Pre-registered (configs/l5_fidelity_preregistration.json): Spearman >= 0.8, max diff <= 0.5 kWh, >= 7 of 9 pairs | As planned; finalists = top 8 per pair. |
| Search objectives | gain, overheat, PCM mass/cost | robust gain, overheat-guard hours, PCM volume | Mass replaced by volume (density cancels in ranking). |
| Search budget | NSGA-II + AL 5 rounds + vertex + 3 rounds | Up to 3 AL rounds of 6, vertex step, 3 seeds, final union thinned to 15 | Compute-time reduction, stop rule unchanged (hypervolume < 1 % twice). |
| Dense grid | 720-point grid | 162-point grid (6 radii x 9 fractions x 3 arrangements), centre anchor, cheap fidelity | Compute-time reduction; epsilon vs search reported. |
| Repeatability band | Includes years, dt, nodes, properties, mains, demand, anchor | Funnel uses the CORE band (years, dt, nodes, properties, anchor); the FULL band incl. mains and demand is reported next to it | Mains and demand are scenario shifts, not noise; the legacy 26-30 kWh band only matches the core definition. Decided before the real select/test runs but AFTER a smoke test showed demand +/-20 % moves the gain by ~99 kWh - disclosed here. |
| Funnel | S0/S1/S2 frozen before the test | Frozen in configs/funnel_frozen.json (hash) before any select-year run | As planned. |
| Overheat hours | Not specified as a trade-off | Reported as a cost: PCM tanks hold less water in the same 100 L and always show more guard hours | Found in the plant scan, same sign in all regimes and demands. |
| Year roles | R3 | As planned; 2006-2010 fetched (NASA POWER, UTC), 2011-15 legacy, 2022-25 report-only | The sunrise/sunset check covered 0 days for 2006-2010; timing verified against 2017 clear-sky profile instead. |
| Lock | Keyed to hardware hash | results/common100L_<hash>/held_out_test.lock | As planned; legacy lock refused. |
| MATLAB M1 scope | Water-only vs PCM, four PCMs, seven criteria | All seven Fluent criteria, discharge + three real day types + four PCMs + animated tank cut-aways, driven by kernel output | User request. Visualisation of simulator output (hourly records), not a MATLAB re-implementation of the physics; capsule drawing is a 2-D proxy. |
| Fluent L8 | Re-run around the new optimum | Seven criteria regenerated from the funnel winner (40 % cap, flow 0.030), same 2-D proxy rule | As planned. |
| O3/O4 | Rebuilt after O2 | Not started in this work | Out of scope of this document. |
