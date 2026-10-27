# Objective 2 + OpenFOAM — literature review and improvement plan

> **SUPERSEDED IN PART (2026-10-16):** the literature base below includes pre-2023 papers.
> The current plan, restricted to 2023–2026 papers, is `AI_OPTIMISATION_PLAN_2023_2026.md`.
> Validation benchmarks named here (Assis 2007, Tan 2009) are replaced there by 2023+ datasets.


Date: 2026-10-16. Scope: what published work has already done on the same
problem, where our pipeline is ahead / behind, and a prioritised plan.

**Evidence tags used throughout**
* **[P]** read in the project's own sources (`.claude/Sources/*.md` summary and/or the extracted PDF text). Numbers are as printed there.
* **[PDF]** full text of the PDF read in this review (Avargani 2021, Li 2020).
* **[C]** found via a Consensus search; **only the abstract was read**. Do not cite a number from a [C] paper before reading the full paper and adding it to `sources/` (CLAUDE.md §0).
* **[OURS]** a result of this project (`openfoam_cfd/results/`).

---

## 1. What the literature has already done

### A. Single-capsule melting (the physics our CFD tier models)
| Paper | What it did | Why it matters to us |
|---|---|---|
| Assis et al. 2007, IJHMT [C] | Experiments + Fluent on **40, 60, 80 mm** spherical shells, wall **2–20 K** above Tm; includes convection, **volumetric expansion, sinking of the solid, close-contact melting**; correlates mean Nu and melt fraction against Fo·Ste·Gr | Same diameters and ΔT range as our DOE → the natural validation benchmark. Also lists three mechanisms our model omits |
| Tan et al. 2009, IJHMT [C] | n-octadecane in a transparent sphere, thermocouples + Fluent; shows early symmetric (conduction) melting, then top-heavy convection melting, bottom waviness | Experimental benchmark for melt-front shape and stratification |
| Regin et al. 2006 [C] | **Hot water flowing over a capsule** (70–82 °C, r = 49 mm), enthalpy method, radius and Ste effects | Same boundary condition as ours (water flow over the capsule) |
| Ismail et al. 2021 [C]; Chen 2026, J. Fluid Mech. [C] | Dimensionless melt-fraction / Nu correlations for spheres; Chen identifies a critical capsule size and **Ra_c ≈ 1.9×10⁴** separating conduction- from convection-dominated melting | Gives a regime criterion (their Ra_c is for Pr ≈ 60): check whether our d = 40–80 mm cases sit above it, which would explain the 1.8–3.3× convection gain |

### B. Reliability of the enthalpy-porosity model itself
| Paper | Finding |
|---|---|
| Fadl et al. 2019 [C] | Mushy-zone constant 10⁵–10⁷ changes melt-front shape and rate (lauric acid) |
| Pan et al. 2018 [C] | Best A_mush depends on the driving ΔT; calibrate against melting-time experiments |
| Ebrahimi et al. 2019 [C] | Sensitivity to A_mush vanishes for sufficiently fine meshes (isothermal case); assess with a Péclet number |
| Rocha et al. 2023 [C] | Validating on one geometry and reusing A_mush on another gave errors up to **38 %** (5.7 % after re-tuning); **expansion coefficient β matters more than density** (liquid fraction changes 7.5 % vs 0.5 %) |
| Ye et al. 2024 [C] | A_m correlated with Gr and Ste (A ∝ Gr^0.639 Ste^−2.947 for CaCl₂·6H₂O) |
| Abdellatif 2025 review [P] | Lists **ML for mushy-zone modelling** as open future work; mushy-zone parameters "remain uncertain" |

**Our result [OURS] matches this literature:** β ×0.5/×2 moved t90 by +12 / −10 %,
μ by −9 / +11 %, Cu (A_mush analogue) by under 2 %.

### C. Packed-bed / tank-scale models with capsules
| Paper | Method | Takeaway |
|---|---|---|
| **Madadi Avargani 2021 [PDF]** | COMSOL; **volume-averaged porous medium, two-temperature (local thermal non-equilibrium)**; interstitial `h_sf` with `1/h_sf = 2r/(k Nu) + 2r/(β k_s)`, **β = 10**, Wakao–Kaguei Nu; 55 mm capsules, porosity 0.2–0.5, 0.005–0.15 kg/s; validated against Nallusamy 2006 experiments; mesh criterion = energy balance < 3 % | The grey-box's `R_pcm = r/(5k)` **is this correlation** (2r/(10k)). It was derived for conduction in a sphere, not for convection-driven melting — so φ ≈ 0.47 [OURS] is an expected consequence, not a coding error. Our energy-balance gate (< 3 %) is the same one they use |
| Sponagle et al. 2025, IJHMT [C] | **Detailed single-capsule simulation → heat-flux dataset → 1-D finite-volume bed model**; validated on 6 experiments | Exactly our multi-scale idea; supports the method and shows the next step (a 1-D bed model) |
| Grabo 2021 [C]; Kumar 2024 [C]; Sun 2021 [C] | Non-spherical capsules (+20 % capacity), rigid-body packing for porosity, Schumann two-equation model | Capsule shape and realistic packing are active levers |
| He 2023 [C]; Zhou 2024 [C]; Mao 2020 [C]; Liu 2022 [C] | **Cascaded layers with different capsule diameters / melting points**; best size mix **20–30 mm** (He); GA on layer heights: −28 % charge time, +17.7 % TES rate density (Zhou); three-layer capsule tank for **SWH** improves stratification (Liu) | Our design space (one diameter, one PCM, 40–80 mm) excludes the configurations reported to work best |
| Huang 2020 [C]; Elbahjaoui 2023 [C] | **PCM unit in series with the water tank**: optimal PCM volume ratio **0.67–0.78**, solar fraction ~**+30 %**; cascaded RT44HC/RT54HC/RT62HC slabs, 3.5 % higher collection efficiency | Different architecture from "capsules inside the tank"; explains why a PCM-in-tank loading of a few % can look useless |

### D. System-level DHW studies
| Paper | Finding |
|---|---|
| Eldokaishi 2022 [P] | ANN on validated model: 90 L PCM tank ≈ 210 L water tank (≈ 57 % volume saving); +13 % SF at V_f 0 → 0.5 in 90 L but only +5 % in 150 L; Sobol sampling 44 % / 16 % lower MAE than LHS / MC; 20 mm cylindrical modules |
| Abdelsalam 2020 [C]; Ding 2020 [C]; Batista 2021 [C] | Benefit depends strongly on region and Tm; PCM helps **only when the mean tank temperature is near Tm** (Batista); direct-heat-exchange stratification gives 18–23 % higher SF |
| Bouhal 2018 [C]; Carmona 2020 [C] | Two numerical codes (apparent-Cp vs enthalpy) give different results; Carmona validates a PCM-bottle DHW tank over full 24 h cycles |
| Avargani 2021 [PDF] | Objective is **constant outlet temperature**: up to 300 L at 60 ± 2 °C for 7 h (one collector), 1200 L (two in series) |
| Li 2020 [PDF] | Central composite DOE → RSM quadratic surrogates → NSGA-II → LINMAP/TOPSIS; TRNSYS; swimming-pool heating, not capsules |
| Assareh 2023 [P] | MOEA/D + RSM + TOPSIS/LINMAP/AHP; Pareto of discharge duration vs net stored energy; tube diameter and area sensitivity; 1-D flow assumption |
| Chen 2025 [P] | L36 Taguchi + GRA in TRNSYS; flow 0.02 kg/s; PCM material only 2.6 % of heat-retention variance |

### E. AI / surrogate methods around CFD
| Paper | Method |
|---|---|
| Yan 2025 [P] | 60 CFD cases → PR/SVR/RF/XGBoost; XGBoost 92 %, ±5 min; SVR overfits; importance: fin width 51 %, HTF T 47 % |
| Zheng 2024 [C] | **Surrogate-assisted multi-objective evolutionary algorithm** + CFD: GP models from only **80 CFD cases**, batch recommendation, −91 % computational cost |
| Han 2026 [C] | **Physics-informed NN built on a 0-D lumped-capacitance model, trained on 15 CFD cases**, R² > 0.999, then NSGA-II |
| Kim 2024 [C] | Random forest best among 4 surrogates for tree-fin LHTES |
| Do 2023 [C]; Pellegrini 2022 [C] | Multi-fidelity Bayesian optimisation / active learning that chooses *which fidelity* to query |
| Liu 2025 review [P] | Notes CFD-coupled optimisation is expensive; real-time/field validation rare; physics-informed hybrids needed |
| Martinez 2025 [P] | Measured DSC properties differ from datasheets (RT 55 ΔH −28 %, k +34 %; RT 64 HC ΔH −31 %; E 58 −91 %) → **property uncertainty is large** |

---

## 2. Where we stand relative to that work

**Ahead of most of the literature**
* A full chain O1 climate regime → O2 design → CFD calibration → annual simulation, per Indian climate regime. Many studies are single-climate (Toronto [P], Marrakech [C], a 33°N 44°E reference [P]); Ding 2020 [C] covers six cities.
* Energy-balance QC on every CFD case, paired frozen-vs-calibrated runs, and a harness that reproduces the frozen results to 1e-10 kWh.
* Honest null result: PCM ≈ plain tank inside the tolerance — reported, not hidden.

**Behind / exposed**
1. **The CFD has no experimental validation.** Every comparable paper ([C] Assis, Tan, Regin; [PDF] Avargani) validates before using. This is the single biggest weakness.
2. **Discretisation and property uncertainty are of the same order as the effect** (t90 ≈ 9 % mesh, ±10–12 % μ/β) — acceptable for "grey-box is ~2× pessimistic", not for absolute design numbers.
3. **Omitted physics** that Assis includes: volumetric expansion, solid sinking, close-contact melting.
4. **Single-node tank, constant ΔT in CFD** — literature shows stratification matters (Abdelsalam 18–23 %, Liu 2022) and wall temperature varies hourly.
5. **Design space is narrow**: one diameter, one PCM, 40–80 mm; the literature's best designs are cascaded and 20–30 mm.
6. **Objective does not discriminate**: annual useful energy differs by < 0.5 % between designs; the literature reports value as tank-volume reduction, solar fraction, auxiliary saving or delivery-temperature stability.
7. **Surrogate step is one-shot LHS + ExtraTrees**; the CFD-era literature uses sequential/multi-fidelity learning with uncertainty.
8. **An unreconciled result:** the calibrated search recommends 17–18 % PCM loading in regime 0, against our own loading sweep (gains negative above ≈ 2.5–3 %).

---

## 3. Improvement plan (prioritised)

Effort in working days for one person; "gate" = the check that decides whether to continue.

### P0 — make the CFD credible (≈ 5 days)
| # | Action | How | Gate |
|---|---|---|---|
| 0.1 | **Reproduce a published sphere-melting experiment** | Add Assis 2007 (40/60/80 mm, 2–20 K) and/or Tan 2009 to `sources/`; set `make_case.py` to a constant-wall-temperature BC (`h → ∞`, no shell) with their PCM properties; compare melt fraction vs time and final melt time | Melt-time error ≤ 10–15 % over the three diameters, else adjust Cu per Pan 2018 / Rocha 2023 and re-test on a **second** geometry |
| 0.2 | Mesh to asymptote | Re-run DOE at 0.8 mm (t90 changes 2.9 % from 0.8 → 0.6 mm [OURS]); report GCI | t90 change between last two meshes < 3 % |
| 0.3 | Replace assumed μ, β | Datasheet or DSC/viscometer values; if unavailable, carry them as **uncertain inputs** (±) through the whole chain (§P4) | φ range reported with property bounds |
| 0.4 | Quantify the omitted physics | Run the Assis cases with and without expansion / close-contact (Fluent not available → estimate bias from their published comparison) and state a bias band | Bias band stated in the paper |
| 0.5 | Reconcile the 17 % loading result | Re-run `scripts/sweep_pcm_loading.py` with the calibrated closure; add a **latent-utilisation** KPI (fraction of hours water temperature within Tm ± band; Neri 40 % benchmark [P]) | Either the sweep reproduces, or the discrepancy is explained (Batista: benefit only when T_tank ≈ Tm) |

### P1 — fix the closure properly (≈ 4 days)
1. **Dynamic validation:** replay the grey-box hourly water temperature of a representative sunny day (from `phase3_simulate_*` outputs) into OpenFOAM via the existing `ta_table` input and compare stored energy and melt fraction vs time with the grey-box `f_melt(t)`. This removes the "constant ΔT" caveat.
2. **Replace constant φ by a correlation**: fit melt fraction / effective resistance against Fo·Ste, Ra and Bi (the form used by Assis, Ismail, Chen 2026), and implement as a drop-in `ua_eff` variant with its own config version (never editing frozen `heat_transfer.py`; use the same in-memory seam as `cfd_calibrated_greybox.py`).
3. Make the ×2 convection factor **melt-fraction dependent** (CFD: convection gain 1.8–3.3× [OURS]; the frozen switch at f = 0.5 cannot reproduce the early melt).

### P2 — resolve what the single-node tank hides (≈ 7 days)
1. **1-D packed-bed (Schumann / two-temperature) model in Python** using the CFD-derived capsule closure — Sponagle 2025 and Avargani 2021 are the templates. It gives axial stratification and makes `void fraction`, `Nu_arr`, flow direction and capsule count *physical* instead of just a pressure-drop term.
2. **Arrangement unit-cell CFD** (2-D periodic cell, in-line vs staggered; radial handled as a ring) for Nu_arr and ΔP — cheap, closes the question with data instead of the G0 inference. Expected effect < 0.02 % [project G0 analysis]; if confirmed, it becomes a one-paragraph, evidence-backed statement.
3. Compare 1-D bed vs single-node on the Phase-5 designs: how much does stratification change useful energy and ranking?

### P3 — widen the design space where the literature says the gain is (≈ 6 days)
1. **Capsule diameter below 40 mm.** Literature optima are 20–30 mm (He 2023 [C]; Eldokaishi uses 20 mm [P]). Our 40 mm floor comes from the derived `pcm_thickness_m ≥ 0.02` bound; check its source before relying on it (design_bounds_shared.yaml note) — it may simply exclude the optimum.
2. **Cascaded capsules** (two diameters or two Tm along the flow, Liu 2022 / Zhou 2024 / Elbahjaoui 2023). The 1-D bed model makes this a 2-parameter extension (layer fraction, second PCM from the O1 shortlist).
3. **Series PCM unit** (Huang 2020) as an alternative architecture — only if the group decides the scope allows.
4. **Capsule shape** (Grabo 2021) — keep as stated future work; not worth the effort for an FYP.

### P4 — change the objective and the AI loop (≈ 5 days)
1. **Objectives that discriminate** (all computable from existing runs):
   * tank-volume reduction at equal solar fraction (iso-performance; Eldokaishi's 90 L ≡ 210 L);
   * hours of delivery within ± 2 K of target (Avargani's metric);
   * auxiliary / unmet energy and peak-hour shifting;
   * latent utilisation and exergy.
2. **Sobol instead of LHS** for new DOE points (Eldokaishi: 44 % lower MAE at small N) — a one-line change in `run_doe.py`.
3. **Sequential design:** GP surrogate with predictive variance and a batch acquisition rule (Zheng 2024: 80 CFD cases suffice) so new CFD runs go where the optimum is uncertain, not on a fixed grid.
4. **Multi-fidelity chain:** grey-box (seconds) → 1-D bed (minutes) → CFD capsule (≈ 1–20 min) with fidelity selection (Do 2023, Pellegrini 2022). This is the AI contribution that is genuinely new for PCM-SWH.
5. **Physics-informed residual model** (Han 2026): learn only the *correction* to the 0-D grey-box from CFD instead of the whole response — reduces data need, which is our φ model generalised.
6. **Uncertainty propagation:** treat μ, β, k, ΔH (Martinez: ΔH off by up to −31 %) as distributions; report design robustness, not a single optimum. Extends Phase 8 to the CFD tier.
7. **Multi-objective selection** with NSGA-II + TOPSIS/LINMAP (Li 2020, Assareh 2023) replacing the "5 % tolerance then tie-break" rule for the CFD-tier results; keep the frozen rule for the headline comparison.
8. **Climate index → design rule** (Kou 2025 [P] regressed energy-saving ratio on a single climate index across 61 cities, R² > 0.98): regress the O2 optimum (d*, N*, ṁ*) on O1 cluster features across the four states to give a transferable rule.

### P5 — hardware validation hook for O4 (≈ 3 days design, lab time separate)
* A **single-capsule melting test**: instrumented aluminium sphere (DS18B20 inside, one at the wall) in a stirred, controlled hot-water bath at 5–20 K above Tm — the same experiment as Regin 2006 / Tan 2009 at student-lab scale. It calibrates φ and A_mush with real data and gives the first O4 measurement.
* Then a 24 h cycle on a small PCM-bottle tank (Carmona 2020 protocol) for dynamic validation.

---

## 4. Suggested sequence and decision points

| Week | Work | Decision gate |
|---|---|---|
| 1 | P0.1–0.3 (validate vs Assis/Tan, mesh 0.8 mm, property bounds) | If validation error > 15 %: stop adding features; tune Cu on one geometry, test on another |
| 2 | P0.5, P1.1–1.3 (loading reconciliation, dynamic replay, closure correlation) | If φ-correlation changes annual energy < 0.05 %: freeze closure, move on |
| 3 | P2.1–2.3 (1-D bed, arrangement cell) | If stratification changes ranking: report it as a model-form finding |
| 4 | P3.1–3.2 (d < 40 mm, cascade) and P4.1–4.3 (objectives, Sobol, GP) | Only keep extensions that change an iso-performance metric by more than the noise band |
| 5 | P4.4–4.8, write-up, P5 experiment design | Decide what goes in the paper vs future work |

Scope warning (CLAUDE.md §6): P2 (1-D bed) and P4.4 (multi-fidelity) are the two items
that are research-level; everything else is incremental. If time is short, do
**P0 → P1.1 → P4.1–4.3** — validated CFD, dynamic replay, a discriminating
objective and a sequential design is already a complete, defensible contribution.

## 5. Claims to avoid until the above is done
* "CFD-validated" — not until P0.1 passes.
* Absolute melt times or absolute φ — only the *direction and rough size* (~2×) of the grey-box error is supported today.
* "Optimal capsule diameter / count / flow" — differences between designs are below 0.5 % of annual energy and inside the simulator noise band.
* Any statement on arrangement from CFD.
* Any number from a [C] paper in this document without reading the full text.

## 6. Papers to obtain and extract into `sources/` (per CLAUDE.md §5)
Assis 2007; Tan 2009; Regin 2006; Sponagle 2025; Han 2026; Zheng 2024; Rocha 2023;
Pan 2018; Huang 2020; Liu 2022 (three-layer SWH tank); Carmona 2020; Nallusamy 2006
(the experiment Avargani validates against). These are mostly paywalled; they need
institutional access — the CFD tier cannot be called validated without at least
the first two.
