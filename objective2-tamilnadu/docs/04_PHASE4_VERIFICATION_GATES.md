# 04 — Phase 4 Audit: Simulator Verification Gates

File: `src/verify/gates.py`. Output: `results/tamilnadu/simulator_verification_report.txt`.

No Phase 5 DOE row may be generated until this passes (framework doc §5).
Reduced 5-gate battery per `O2_Unified_PerState_Execution_Framework.md`.
Run with `python pipeline.py --state tamilnadu --stage verify`.

## Gate 1 — Energy conservation: **PASS**

5 diverse cases (different clusters, PCMs, a no-PCM baseline, and a
bounds-extreme design), each a full simulated year:

| Case | Residual (% of E_collector) |
|---|---|
| A: cluster0 / n-Octacosane / mid design | 0.000009% |
| B: cluster1 / RT64HC / small-capsule design | 0.000000% |
| C: cluster4 / n-Hexacosane / large-capsule design | 0.000000% |
| D: cluster2 / no-PCM plain-tank baseline | 0.000081% |
| E: cluster3 / n-Octacosane / bounds-extreme design | 0.000002% |

Mean 0.000018%, max 0.000081% — both far inside the 0.1% pass threshold.
(Before the reverse-collector-flow fix documented in the Phase 3 doc, case
A alone showed a 1.6% residual; the fix brought every case to
floating-point noise level.) Pump energy is tracked and reported
separately from this thermal balance, per the framework doc's own
instruction — see Phase 3 doc.

## Gate 2 — Limiting cases: **PASS (10/10)**

| Case | Result |
|---|---|
| Zero irradiance | E_collector = 0 exactly |
| Zero flow | Completes, residual ≈ 0, no crash |
| No PCM | E_charge = E_discharge = 0 |
| Zero latent heat | Completes; f_melt degenerates to a step function (expected — L=0 makes the melt band a point) |
| Very high PCM conductivity (×200) | Mean \|T_w−T_pcm\| gap SMALLER than nominal (0.098°C vs 0.326°C) — correct direction, and no divergence after the stiffness fix (Phase 3 doc) |
| Perfectly insulated tank | E_loss = 0 exactly |
| Empty demand | E_load = E_unmet = 0 |
| Fully solid initial PCM | f₀=0.000 → f₂₄=0.000 (stays solid, no sun yet at hour 0 in this weather trace) |
| Fully liquid initial PCM | f₀=1.000 → f₂₄=0.000 (fully discharges within the first day — small PCM mass, plausible) |
| Flow below/above [0.010,0.050] permitted range | Completes at 0.002 and 0.20 kg/s; higher flow narrows the T_w−T_pcm gap (0.474°C → 0.277°C) — correct direction |
| Capsules removed (N=0) | E_charge = 0 |

All 10/10 pass. Every expected direction was written into the test code
*before* running it (see `src/verify/gates.py::gate2_limiting_cases`),
per the framework doc's requirement.

## Gate 3 — Baseline comparison: **PASS** (with an honest, load-bearing caveat)

| Design | Useful energy | Solar fraction | Unmet energy | Mean f_melt |
|---|---|---|---|---|
| Plain tank (no PCM) | 1673.3 kWh | 52.26% | 1158.1 kWh | — |
| Fixed PCM, n-Octacosane, max feasible fraction (12.9%) | 1660.1 kWh | 51.16% | 1185.0 kWh | ~2% |
| "Optimized-looking" (10.2% fraction) | 1663.0 kWh | 51.39% | 1179.4 kWh | ~2% |

**n-Octacosane does not beat the plain tank here.** Rather than force a
pass or quietly pick numbers that happen to look better, Gate 3 runs a
**capability check**: swap in a synthetic PCM with the same fraction/
geometry but `Tm = 40 °C` (matched to this tank's actual operating
temperatures instead of Objective 1's climate/delivery-anchored 61.6 °C):

| Design | Solar fraction | Mean f_melt |
|---|---|---|
| Plain tank | 52.26% | — |
| Synthetic Tm=40°C PCM, same fraction/geometry | **55.19%** | **53.7%** |

This *does* beat the plain tank, decisively, and with the PCM actually
cycling (53.7% mean liquid fraction vs ~2% for n-Octacosane). This
confirms the simulator correctly rewards a well-matched PCM — the earlier
non-improvement is a genuine physical finding about *this specific
50 L/direct-encapsulation/n-Octacosane* combination, not a simulator
defect. Gate 3's pass/fail is therefore gated on the **capability check**
+ the ambient-loss diagnostic below, not on whether today's actual
shortlisted PCM happens to win — see `00_MASTER_OVERVIEW.md` and
`05_NEXT_STEPS.md` for what this means for Phase 5–7.

**Ambient-loss diagnostic (Bug-Fix 1, confirms the loss term is active):**
removing `U_tank` entirely raises solar fraction from 51.16% to 52.69% —
i.e. *no-loss ≥ with-loss*, confirming `Q_loss = U_tank·A_tank·(T_w−T_amb)`
is genuinely active in every case (not accidentally disabled, which was
the exact Objective 1 TN failure mode this project was warned about).

## Gate 4 — Published-benchmark calibration: **PASS-WITH-CAVEAT**

Cited benchmark band (Singh et al. 2025): 54–84% solar fraction.
This simulator's "optimized-looking" design: **51.39%** — 2.6 percentage
points below the band.

Reported honestly rather than tuned to match: this Objective 2 design is
a 50 L tank against a 300 L/day draw with **no auxiliary backup heater**
modeled, a materially smaller storage-to-demand ratio than the cited
benchmark rig, so a lower solar fraction is the expected direction, not a
red flag. Per the framework doc, a Gate 4 mismatch is a caveat to report,
not a hard release blocker.

## Gate 5 — Sensitivity & monotonicity: **PASS (3/3)**

| Check | Result |
|---|---|
| Latent heat +10% vs −10% | More PCM energy cycled with more latent heat (12.29 vs 11.92 kWh) — correct direction |
| Flow +50% vs −50% | Pump energy ≥ with higher flow (both ≈0 in this sparse-bed design — see caveat below) |
| Reduced effective tank-loss coefficient (ambient-warming proxy) | Lower E_loss (65.89 vs 72.93 kWh) — correct direction |

**Caveat on the flow check**: at the PCM fractions currently reachable
(≤12.9%, see Phase 2 doc), the packed-capsule bed is sparse enough that
Ergun-equation pressure drop — and therefore pump energy — is numerically
tiny at *any* permitted flow rate, so this check, while directionally
correct, is a weak discriminator here. It will become a more meaningful
test once Phase 5 explores denser designs.

## Go/No-Go

Framework rule: residual < 0.5% **and** ≥3/5 gates clean.
Result: max residual 0.00008%, 4/5 gates clean (Gate 4 is
PASS-WITH-CAVEAT by design, not a failure) → **GO**.

**Simulator released as `sim_v1_tamilnadu`.** Tag this at your next commit
so Phase 5's DOE cases can record which simulator version produced them
(framework doc: "never mix outputs from two simulator versions in one
training dataset without a version feature").
