# Objective 3 — inputs from Objective 2, and what to do next

**Written 2026-11-24 against the common-plant Objective 2 run** (`run_id test_20261124_021241`, hardware hash `5e66ebc47a07`).
It replaces the 2026-11-09 document of the same name, now in `../archive/superseded_obj3_contract_2026-11-09/`.
**Do not use that copy, or any number in it.** It describes a plant that no longer exists.

---

## 0. What changed, and why the old handoff would mislead you

| | old handoff (2026-11-09) | current |
|---|---|---|
| plant | 100 L tank, **2.5 m²** collector | 100 L tank, **2.0 m²** collector (50 L per m²) |
| daily draw | 300 L/day | **175 L/day** of 45 °C water |
| PCM fraction cap | 30 % | **40 %** |
| capsules | 98–105 | **140** (all three regimes) |
| flow | searched, 0.027–0.039 kg/s | **frozen at 0.030 kg/s**, never searched |
| one-shot test | 2011–2015 | **2006–2010**, lock keyed to a hardware hash |
| stack anchor | centre | **robust**: every design simulated at bottom, centre, top |
| PCM benefit | 178–269 kWh/yr | **122–137 kWh/yr** (different plant: not comparable) |

---

## 1. The files Objective 3 reads

| file | role |
|---|---|
| **`o3_environment_contract_tamilnadu.json`** | the environment specification: plant, limits, designs, action space, state schema, reward terms, acceptance tests, weather roles, caveats |
| `o3_contract_tamilnadu.json` | the **immutable result record** the contract points at (sealed under the one-shot lock; never edited) |
| `*.sha256` | their hashes |

The authoritative copies live in `results/common100L_5e66ebc47a07/`; the files here are copies for convenience. **Parse the JSON; do
not hand-copy numbers out of this document.** Before loading, run:

```bash
python scripts/c24_check_o3_environment_contract.py     # 33 checks; fails if anything disagrees with the sources
```

Rebuild (only after Objective 2's inputs change; the lock stays spent):

```bash
python scripts/c23_build_o3_environment_contract.py
```

The legacy generators (`scripts/g25_obj3_contract.py`, `src/handoff/build_obj3_contract_tamilnadu.py`) are **disabled**: they read legacy
results and would rebuild the old contract.

---

## 2. The designs (read from the contract)

| regime | PCM | O1 rank | capsules | outer Ø | PCM fraction | PCM mass | flow |
|---|---|---|---|---|---|---|---|
| 0 | PureTemp 58 | 3 | 140 | 81.6 mm | 39.8 % | 33.4 kg | 0.030 kg/s |
| 1 | RT57HC | 1 | 140 | 81.6 mm | 39.8 % | 33.8 kg | 0.030 kg/s |
| 2 | RT57HC | 1 | 140 | 81.6 mm | 39.8 % | 33.8 kg | 0.030 kg/s |

All staggered. Every PCM is one of Objective 1's own Top-3 for that regime; the contract check asserts it.

---

## 3. What Objective 2 tells you about the system

**One-shot test, 2006–2010 (run once, locked):**

| regime | gain over plain tank (kWh/yr) | worst of 3 anchors | years PCM wins | × core band | × full band | extra overheat-guard hours/yr |
|---|---|---|---|---|---|---|
| 0 | 137.3 | 132.4 | 5 of 5 | 4.5 | 1.38 | +937 |
| 1 | 122.4 | 108.8 | 5 of 5 | 4.5 | 1.84 | +627 |
| 2 | 134.0 | 127.9 | 5 of 5 | 6.3 | 1.49 | +998 |

PCM peaks stay at or below 62.46 °C (limit 65) and water peaks at or below 72.17 °C (limit 75); zero hours over the limits.
Report-only 2022–2025 gains: 129.7 / 120.3 / 123.6 kWh/yr.

**Three things to hold on to:**

1. **PCM wins on delivered energy, but costs overheat-guard hours in every regime.** The capsules displace water in a fixed 100 L tank, so
   the collector trips the shield more often. This is the real opening for a controller: anticipate the limit instead of reacting at it.
2. **The margin depends on how you count noise.** Against the *core* band (years, timestep, nodes, PCM properties, anchor) the gain is 4.5–6.3
   times the band. Against the *full* band (which adds mains-temperature and demand variation) it is only 1.4–1.8 times. The sign never
   changes (PCM wins in every test year); the size is what is uncertain.
3. **The plain tank is already strong at 175 L/day.** At 70 L/day the PCM gain collapses to single digits (`parameter_sensitivity` in the
   contract). The benefit is a function of the draw.

---

## 4. Three constraints you must not violate

1. **The boundary.** Objective 1 chose the PCM. Objective 2 chose the hardware. **Objective 3 chooses the real-time action and nothing
   else.** Do not change PCM identity, capsule geometry, tank volume, collector area, safety limits or the physics model, and do not
   re-cluster or merge regimes.
2. **The weather roles** (`src/weather/roles.py` enforces them):

   | purpose | years | note |
   |---|---|---|
   | train | 2016–2019 | role `explore` |
   | validate | 2020–2021 | role `select`; these two years also chose the O2 *design*: say so in any report |
   | final report | 2022–2023 | recommendation: pre-register before the first run |
   | **never** | 2006–2010, 2011–2015, 2024–2025 | one-shot test spent / legacy / project-exposed |

3. **The flow envelope** 0.010–0.050 kg/s, hard. Never command outside it.

---

## 5. What the inherited design is *not*

- **Not a global optimum.** It is the corner of the search box: **both** the 40 mm radius bound **and** the 40 % fraction cap are binding in
  all three regimes. When the cap moved from 30 % to 40 % the optimum moved with it. The three regimes ended at the **same geometry**;
  they differ only in PCM and weather.
- **The flow is not an optimum.** It was frozen at 0.030 kg/s, and `flow_dependent_fr` is **off**, so the collector's F_R does not respond
  to flow. Any flow behaviour you learn is partly a model artefact. Do not defend 0.030 as physical.
- **F_R·τα and F_R·U_L were not re-fitted for 2.0 m².** They are the legacy typical values. The configs are sealed under the lock, so this
  is a stated sensitivity: ±10 % on F_R·τα moves the gain by roughly −14 / +7 kWh (regime 0).
- **The cheap-screen fidelity rule failed (0 of 9 pairs).** The cheap screen ranked perfectly (Spearman 1.00) but differed by 3.7–4.3 kWh
  against a 0.5 kWh limit, so it was not used for selection; all finalists were re-evaluated at full fidelity.
- **No experiment, no hardware.** The Fluent work is a *model consistency cross-check*, not validation.

---

## 6. Concrete first steps

1. **Load the contract and run the checker.** Do not re-run Objective 2's optimiser or re-pick a PCM.
2. **Build a stepper, not a new simulator.** Refactor the inner timestep loop of the multi-node tank model into a stateful
   `step(action) -> (obs, reward, done, info)`. Reuse the physics unchanged; only `flow_rate_kg_s` becomes an action.
3. **Decide the timestep deliberately.** The search step is 150 s; the confirmation step is 37.5 s and every number in the sealed record
   was produced at 37.5 s. Report which one you use.
4. **Pass the acceptance tests with a trivial rule-based controller first** (the contract lists them, including: the baseline controller must
   reproduce the c17 paired gains to within the repeatability band). Fix the environment before writing any learning code.
5. **Set your own reward weights.** The contract gives the terms and deliberately no weights. Normalise against the regime's water-only twin
   over the explore years.
6. **Benchmark several learners** (DQN / PPO / SAC family) on one environment and one reward before committing.

---

## 7. What Objective 2 did not resolve

Full list in the contract's `deferred_future_work`:

- re-fitting F_R for the 2.0 m² basis (needs a new lock and a new test),
- a larger search box (both bounds bind),
- flow-dependent collector F_R,
- PCMs outside Objective 1's shortlist (a 45 °C screen favoured lower-melting PCMs; not acted on by decision),
- the regime-0 medoid is one of 24 tied points; each regime uses a single medoid weather point,
- experimental validation (Objective 4).

---

## 8. Other states

Rajasthan, Assam and Uttarakhand have no Objective 2 run in this tree. When their contracts exist, build **one** contract-consuming
Objective 3 codebase that takes `--state`, rather than forking per-state controller code.
