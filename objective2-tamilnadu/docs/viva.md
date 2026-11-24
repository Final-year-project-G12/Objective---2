# Objective 2 — Viva Quick Reference

PCM capsule tank design optimisation · Tamil Nadu · 3 climate regimes · **common plant: 100 L tank, 2.0 m² collector, 175 L/day**
*(refreshed 2026-11-24; the earlier version described the legacy 2.5 m² / 300 L/day plant)*

---

## 1) What Objective 2 does — in 7 points

**1. Inputs.** Three things feed in:
- **Climate data** per regime: hourly solar irradiance (GHI), air temperature, local time, for the regime's medoid point (real weather years 2006–2025).
- **Objective 1's Top-3 PCM shortlist** per regime (no PCM is added in Objective 2).
- **Fixed plant** (100 L tank, 2.0 m² collector, 175 L/day of 45 °C water, safety limits) and the **design bounds** the optimiser may move within.

**2. What we optimise.** We search for the best **capsule design** per regime: which PCM, capsule radius, PCM volume fraction (which fixes the capsule count),
and arrangement. Flow is frozen at 0.030 kg/s. The goal is to **maximise the extra hot water delivered at ≥ 45 °C between 18:00 and 09:00** compared with an
identical tank without PCM (`g_window`), while keeping PCM ≤ 65 °C and water ≤ 75 °C, then to prefer fewer overheat-guard hours and less PCM.

**3. Algorithms used (the pipeline).**
- **Sobol DOE**: 128 points per (regime, PCM) pair, 9 pairs;
- a **surrogate model**, a **stacked ensemble** chosen in a bake-off;
- **NSGA-II** (multi-objective genetic algorithm) on the surrogate, plus **committee active learning**;
- a **dense grid** (162 points) to show the search missed nothing, and a **repeatability band** that says how big a gain must be to count;
- a **selection funnel frozen before the select years were run**;
- the **fast 10-node tank model** as the evaluator of every reported number, and **ANSYS Fluent** as an independent physics cross-check.

**4. Why these, not others.**
- The surrogate bake-off compared **Gaussian process (ARD), a NN ensemble, quadratic RSM, XGBoost and a stacked ensemble** by 5-fold Spearman rank agreement.
  **Stacked won in all 9 pairs** (0.975–0.984), but XGBoost was close (0.969–0.976): the margin is small and the surrogate only *proposes*; every reported number is a simulator run.
- **NSGA-II** handles several objectives at once (gain, overheat hours, PCM volume) and was checked against the ZDT1 benchmark.
- **ANSYS Fluent rather than OpenFOAM** because OpenFOAM's standard solvers have no phase-change (latent-heat) model, so they cannot melt a PCM.

**5. Did we validate and choose the best?**
- **Simulator verification**: energy closure ≤ 4.3·10⁻¹¹ % (gate 0.1 %); timestep change per halving ≤ 0.047 % (gate 0.05 %); 10 vs 20 nodes ≤ 0.71 %;
  standing loss 2.05–4.82 °C over 16 h (IS 12976 limit 8 °C); **95 automated tests pass**.
- **Negative control**: with the latent heat set to zero, the same capsules deliver **184–298 kWh/yr less** than the real PCM in all 18 G1 cases (`results/c6_g1_pairs_r*.csv`), so the latent heat is doing the work.
- **Paired baseline**: every gain is against the same-flow plain tank, so shared model simplifications cancel.
- **Pre-registered rules**: the funnel (S0/S1/S2), the band and the fidelity-screen rule were fixed before the outcomes. The fidelity screen *failed* (0 of 9 pairs), so it
  was not used for selection and every finalist was re-evaluated at full fidelity. We report that, we did not relax the rule.
- **Cross-check**: ANSYS Fluent confirms the melting and discharge physics at capsule and whole-tank scale (2-D). It is a consistency check, **not** experimental validation.

**6. Did we test, is it finished?** Yes.
- **One-shot confirmatory test on 2006–2010**, run once under a hash-keyed lock (a second run fails closed). The winners were frozen before it and nothing was changed after.
- **PCM beat the plain tank in all 5 test years in all 3 regimes.** Report-only years 2022–2025 agree (120–130 kWh/yr).
- Objective 2 is complete; the Objective-3 contract is built and independently checked (33 checks).

**7. The actual output.** Three designs, one per regime (`results/c16_funnel_winners.csv`; sealed record `results/common100L_<hash>/o3_contract_tamilnadu.json`):

| Regime | PCM | Capsules | Outer Ø | PCM fraction | PCM mass | Flow | Test gain (kWh/yr) | Years PCM wins | Extra overheat h/yr |
|---|---|---|---|---|---|---|---|---|---|
| 0 | PureTemp 58 | **140** | 81.6 mm | 39.8 % | 33.4 kg | 0.030 kg/s (frozen) | **137.3** | 5 of 5 | +937 |
| 1 | RT57HC | **140** | 81.6 mm | 39.8 % | 33.8 kg | 0.030 kg/s (frozen) | **122.4** | 5 of 5 | +627 |
| 2 | RT57HC | **140** | 81.6 mm | 39.8 % | 33.8 kg | 0.030 kg/s (frozen) | **134.0** | 5 of 5 | +998 |

All staggered. PCM peak ≤ 62.5 °C, water peak ≤ 72.2 °C, zero hours over the limits.

> **In one line:** Objective 2 takes the climate and Objective 1's PCM shortlist, searches the capsule-design space with a surrogate and NSGA-II, picks one design per regime with a
> funnel frozen in advance, proves it once on unseen years, and cross-checks the physics in ANSYS Fluent.

---

## 2) The capsule count: is it physically possible?

The designs call for **140 capsules of 81.6 mm outer diameter**. The check:

- One capsule's outer volume = 4⁄3 · π · (0.0408 m)³ ≈ **0.2845 L**.
- **140 × 0.2845 L ≈ 39.8 L**, i.e. **39.8 % of the 100 L tank** (the design's PCM fraction), leaving about 60 L of water.
- **Packing:** 40 % is below the random close-packing limit of spheres (about 64 %), and the project's geometry engine checks every design for spacing (≥ 3 mm) and a free flow passage
  (≥ 5 %). Of 780 grid points over the whole box, 702 were valid and the chosen design is one of them.
- **Hardware:** spherical PCM capsules of this size order are commercially available; confirm a specific product and shell wall with a supplier before quoting one.

**Honest notes for the viva:**
1. **The CFD pictures show 34 capsules**. The 2-D slice cannot hold 140, so every scenario is drawn with `drawn = round(N × 34/140)` (the proxy rule). Different zoom level, not a contradiction.
2. **Both the capsule radius (40 mm) and the PCM fraction (40 %) sit at their upper bounds** in every regime: the optimum is the corner of the search box. The cap moved from 30 % to 40 % in this rebuild and the
   optimum moved with it, so the true optimum may lie beyond the box. It is feasible and it is a box-limited answer.
3. **All three regimes ended at the same geometry** (40 mm, 140 capsules, staggered); they differ only in PCM and weather.

---

## 3) The questions you should expect

**Why 175 L/day?** At the first target of 100 L/day the plain tank already met 99 % of demand, so a PCM had nothing to add (gain ≈ −0.6 kWh/yr). A plant scan found the rule:
*PCM adds delivered energy only when the plain tank leaves demand unmet.* 175 L/day of 45 °C water is the 45 °C equivalent of a 100 LPD heater rated at 60 °C. 100, 150 and the legacy 300 L/day are
reported as sensitivity cases, never used for selection.

**Does the PCM win everywhere?** On delivered energy, hold time and serve time, yes. On **overheat-guard hours, no**: the capsules displace water in a fixed 100 L tank, so the collector trips the shield more
often (+627 to +998 h/yr). No plant setting makes PCM better in every category. We state it instead of hiding it.

**How sure are you of the margin?** The sign is solid (5 of 5 years, 3 of 3 regimes). The size depends on how noise is counted: **4.5–6.3× the core band** (years, timestep, nodes, PCM properties, anchor), but only
**1.4–1.8× the full band** (which adds mains temperature and demand variation). The funnel used the core band; this was decided after a smoke test and is disclosed.

**Is the optimum found in ANSYS?** No. The tank model plus NSGA-II choose the design; ANSYS only confirms the melting physics.

**Why is the tank 100 L?** A project instruction for all states (the common plant). With the 2.0 m² collector that is 50 L per m², inside the 40–100 L/m² range of IS 12976:2023.

**What was not done?** F_R·τα and F_R·U_L were not re-fitted for the 2.0 m² basis (the configs are sealed under the test lock, so it is reported as a sensitivity), the search box was not widened, there is no
experimental validation (Objective 4), and PCMs come only from Objective 1's shortlist.

---

## 4) Handy facts

- **Two simulators:** the fast 10-node tank model *chooses*; ANSYS Fluent *checks* (chooses nothing).
- **Charging vs discharge:** hot water *melts* the PCM (charge); in the evening the PCM *solidifies and heats the water* (discharge). Both are shown at single-capsule and whole-tank scale.
- **Collector equation:** Hottel–Whillier–Bliss, cited through Eldokaishi et al. 2022 (*Applied Thermal Engineering* 204:118009).
- **Seven what-if criteria** (`ansys/criteria_*/`): the optimum, max-of-everything, min-of-everything, a real funnel finalist, only 30 capsules, 10 % and 50 % of the optimum.
  Each is explained by the funnel: e.g. 30 capsules still beats the plain tank but is eliminated at S0 for being too far below the best.
- **Year roles:** 2016–19 explore · 2020–21 select · 2006–10 one-shot test · 2022–25 report-only · 2011–15 legacy (unused).
- **Capsule-scale CFD ordering (earlier mesh):** C25 > C26 > RT57HC > PureTemp 58 in melt fraction, following melt point and conductivity.
