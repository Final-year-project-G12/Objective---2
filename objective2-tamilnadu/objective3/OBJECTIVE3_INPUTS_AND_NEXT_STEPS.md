# Objective 3 — inputs from Objective 2, and what to do next

**Written 2026-11-09 against the current Objective 2 results.** This replaces
the 2026-10-27 document of the same name, which is archived at
`../archive/superseded_obj3_contract_2026-10-27/`. **Do not use that copy, or
any number in it.** It described designs that no longer exist and reported two
headline conclusions that the current results reverse.

---

## 0. What changed, and why the old document was dangerous

| | old doc (2026-10-27) | current |
|---|---|---|
| PCM | n-Hexacosane (C26), n-Pentacosane (C25) | **PureTemp 58, RT57HC** |
| arrangement | radial, single-layer | **staggered** (all three) |
| capsules | 32–35 | **98–105** |
| capsule Ø | 72–80 mm | **81.6 mm outer / 80.0 mm inner** |
| PCM mass | 4.9–7.4 kg | **23.6–25.3 kg** |
| tank / collector | 50 L / 1.5 m² | **100 L / 2.5 m²** |
| does PCM beat a plain tank? | **"no, −12.5% to −14.8% in every regime"** | **yes — 9 of 9 on held-out years** |
| P(meets demand) | **"0–4%"** | all three robustness bars met |

The last two rows are why that document had to go: a controller designed to
rescue a system that loses to a plain tank is a different controller from one
tuned to improve on a system that already wins.

---

## 1. The one file Objective 3 reads

**`results/obj3_environment_contract_tamilnadu_v3.json`**
(`contract_version: obj3_contract_v3.0_2026-11-09`), copied here beside this
document. **Parse it; do not hand-copy numbers out of it.**

Regenerate it any time Objective 2's results change:

```bash
python scripts/g25_obj3_contract.py          # or:
python scripts/tn_run_all.py --only g25_obj3_contract
```

It is stage 31 of the pipeline and reads only `g10_selection_r{0,1,2}.json`,
`g10_heldout_results.csv`, `held_out_test.lock`, `wp6_band.csv` and the two
config files. Every one of those is SHA-256 recorded in the contract's
`provenance` block, so a contract can always be traced to the run that made it.

The designs, for orientation only:

| regime | PCM | O1 rank | Ø outer | PCM fraction | capsules | flow | PCM mass |
|---|---|---|---|---|---|---|---|
| 0 | PureTemp 58 | 3 | 81.6 mm | 29.6 % | 104 | 0.0388 kg/s | 24.8 kg |
| 1 | RT57HC | 1 | 81.6 mm | 27.9 % | 98 | 0.0295 kg/s | 23.6 kg |
| 2 | RT57HC | 1 | 81.6 mm | 29.9 % | 105 | 0.0267 kg/s | 25.3 kg |

All staggered, 100 L tank, 2.5 m² collector. Every selected PCM is one of
Objective 1's own Top-3 for that regime — the generator asserts this, so a
substituted material cannot reach Objective 3 silently.

---

## 2. What Objective 2 is telling you about the system

**The environment you inherit is already safe and already delivery-reliable.**
That is the single most important difference from the old document.

- **Held-out test: done, locked, passed.** Five years (2011–2015) reserved from
  the start, evaluated once under `held_out_test.lock`
  (`run_id heldout_2da11230bfb5`, 2026-10-30T09:56:22Z). Nine designs — each
  regime's chosen design *plus* the best design of every other shortlisted PCM,
  so it cannot be a cherry-pick. **9/9 beat the water-only twin**; PCM peaks
  63.3–64.0 °C against a 65 °C limit; water peaks 72.2–72.9 °C against 75 °C.
  Margins are 178–269 kWh/yr over a repeatability band of 26–30 — **6–9× the
  noise floor.**
- **The safety shield is already enforced inside the physics**, in
  `src/simulation/tank_model.py`, not in the policy. It forces the collector off
  at 72 °C water / 62 °C PCM — a 3 °C guard band below the hard limits. So the
  acceptance-test item *"the shield cannot be bypassed by the policy"* passes
  trivially against the baseline. **Your job is a better controller than this
  blunt reactive trip** — one that anticipates the limit instead of reacting at
  it, improving shield-activation frequency and discharge timing. Not fixing a
  broken baseline.
- **No auxiliary heater exists.** "Unmet energy" means genuinely undelivered
  heat. If your reward assumes a backup, that is a stated new addition, not
  something inherited.

---

## 3. Three constraints you must not violate

1. **The boundary.** Objective 1 chose the PCM. Objective 2 chose the hardware
   and the envelope. **Objective 3 chooses the real-time action and nothing
   else.** Do not change PCM identity, capsule geometry, tank volume, safety
   limits or the physics model, and do not re-cluster or merge regimes.
2. **The weather roles.** Train on 2016–2020, validate on 2021–2023. **Never
   tune against 2011–2015** (spent by the held-out test) **or 2024–2025**
   (spent by the v1 test). `src/weather/roles.py` enforces this — it refuses a
   year whose role differs from the stated purpose.
3. **The flow envelope.** 0.010–0.050 kg/s, hard. Never command outside it.

---

## 4. Two things the inherited design is *not*

Both are in the contract under `design_space_caveats`, and both matter to you:

- **It is not a global optimum.** It is the best design found *within* the
  declared bounds under a pre-declared rule. The **30 % PCM-fraction cap is
  binding** — at 40 % the gain is higher by more than the repeatability band in
  every regime, with both peaks still inside limits. That run is planned, not
  done.
- **The nominal flow may be a model artefact.** `flow_dependent_fr` is
  **disabled**, so the collector's F_R does not vary with flow in this model.
  Any optimum sitting at the low flow bound is therefore suspect. **Do not treat
  the inherited flow value as a physical optimum to defend** — it is a starting
  point inside a verified-safe envelope, and flow is exactly what you are about
  to make an action variable.

---

## 5. Concrete first steps

1. **Load the contract.** Do not re-run Objective 2's optimiser or re-pick a PCM.
2. **Build a stepper, not a new simulator.** `tank_model.run_year()` runs a
   whole year in one call. Refactor its *inner timestep loop* into a stateful
   `step(action) -> (obs, reward, done, info)`. **Reuse the physics unchanged** —
   enthalpy model, heat transfer, collector, hydraulics. Only the control
   surface changes: `flow_rate_kg_s` becomes an action instead of a constant.
3. **Mind the two timesteps.** The search step is 150 s; the *confirmation*
   step is 37.5 s, and it is the only one that passes the dt-halving gate. Every
   reported Objective 2 number is at 37.5 s. Decide deliberately which your RL
   loop uses, and report it.
4. **Run the acceptance test with a trivial rule-based controller first** —
   "charge when irradiance is high and the PCM isn't full, discharge during
   demand hours, bypass otherwise". If it fails any item in the contract's
   `acceptance_test_before_drl_training`, fix the environment before writing any
   learning code.
5. **Set your own reward weights.** The contract gives the formula and term
   definitions but **deliberately no weights** — the old `w1..w5` defaults came
   from retired designs and are not carried over. Normalise against the
   water-only twin over the explore years.
6. **Benchmark several learners** (DQN / PPO / SAC family) on one environment
   and reward before committing — precedent [Sivaraj2023], [Emami2026]. An
   ANN-MPC baseline is a useful non-DRL contrast [Terfai2025].

---

## 6. What Objective 2 did *not* resolve

Read before assuming any of these are done. Full list in the contract's
`deferred_future_work`.

- The **40 % PCM-fraction run** the widened-bound diagnostic points to.
- **Flow-dependent collector F_R** — still off, hence the artefact caveat.
- **Dense-grid cross-check for rank-2/3 PCM pairs** — only rank-1 pairs have one.
- **`g18` novert/vert runs** — that with/without comparison is incomplete.
- **No experimental validation of any kind.** The CFD is a *model consistency
  cross-check* — one capsule, six hours, three cases returning 0 % liquid
  fraction, a symmetry mesh excluding melt convection. Objective 4 owns real
  measurement.
- **Objective 1's shortlist is not physics-confirmed.** Its MCDM-vs-physics
  agreement is weak and *not statistically significant* (mean ρ = +0.169,
  p = 0.12–0.96, n = 8–10). You inherit a consensus ranking, not a proven one.
- **Hourly-shape weather confirmation** — the robustness analysis drew annual
  magnitudes from a real 10-year ensemble but used medoid-only hourly shapes
  with synthetic jitter.

---

## 7. Other states

Rajasthan, Assam and Uttarakhand have **not** had the K=5→K=3 refresh or the
shortlist restoration applied, and no Objective 2 run in this tree. When their
contracts exist, build **one** contract-consuming Objective 3 codebase taking
`--state`, rather than forking per-state controller code.
