# 04 — Phase 4 Audit: Simulator Verification Gates (Rajasthan)

File: `src/verify/gates.py`. Output: `results/phase4_simulator_verification_report.txt`.

No Phase 5 DOE row may be generated until this passes (framework doc §5).
Reduced 5-gate battery per `O2_Unified_PerState_Execution_Framework.md`.
Run with `python pipeline.py --state rajasthan --stage verify`.

> **Ported from `objective2-tamilnadu/src/verify/gates.py`.** The gate
> logic, thresholds, verdict rules and structure are the Tamil Nadu
> reference, unchanged. Only the *state-specific test inputs* differ, and
> only where the framework doc says they must:
> - Rajasthan has **3** Level-A clusters (0,1,2), not TN's 5 — Gate 1's
>   five cases are re-spread across clusters 0/1/2.
> - PCM names are Rajasthan's Objective 1 shortlist: `RT50` (cluster 0
>   rank-1), `savE® OM50` (clusters 1–2 rank-1), used wherever TN used
>   `n-Octacosane (C28)` / `RT64HC` / `n-Hexacosane (C26)`.
> - One **informational, non-gating** Gate 2 line records Cluster 0's
>   plain-tank overheating (see `docs/00_MASTER_OVERVIEW.md`).
> - Report path follows this repo's flat `results/phaseN_*` scheme rather
>   than TN's `results/<state>/` subdirectory.

## Gate 1 — Energy conservation: **PASS**

5 diverse cases (all 3 clusters, 2 PCMs, a no-PCM baseline, and a
bounds-extreme design), each a full simulated year:

| Case | Residual (% of E_collector) |
|---|---|
| A: cluster0 / RT50 / mid design | 0.000386% |
| B: cluster1 / savE® OM50 / small-capsule design | 0.000551% |
| C: cluster2 / savE® OM50 / large-capsule design | 0.001627% |
| D: cluster2 / no-PCM plain-tank baseline | 0.001628% |
| E: cluster0 / RT50 / bounds-extreme design | 0.000641% |

Mean 0.000967%, max 0.001628% — both far inside the 0.1% pass threshold
(and ~300× inside the 0.5% hard-stop). Both Phase-3-documented bug fixes
(reverse-collector-flow accounting, adaptive-substepping stiffness) are
intact in this Rajasthan run. Pump energy is tracked and reported
separately from this thermal balance, per the framework doc.

## Gate 2 — Limiting cases: **PASS (10/10)**

| Case | Result |
|---|---|
| Zero irradiance | E_collector = 0 exactly |
| Zero flow | Completes, residual ≈ 0.0003%, no crash |
| No PCM | E_charge = E_discharge = 0 |
| Zero latent heat | Completes; f_melt degenerates to a step function (expected — L=0 makes the melt band a point) |
| Very high PCM conductivity (×200) | Mean \|T_w−T_pcm\| gap SMALLER than nominal (0.108 °C vs 0.577 °C) — correct direction, no divergence after the stiffness fix |
| Perfectly insulated tank | E_loss = 0 exactly |
| Empty demand | E_load = E_unmet = 0 |
| Fully solid initial PCM | f₀ = 0.000 → f₂₄ = 0.000 (stays solid; no sun yet at hour 0 in this weather trace) |
| Fully liquid initial PCM | f₀ = 1.000 → f₂₄ = 0.000 (fully discharges within the first day — small PCM mass, plausible) |
| Flow below/above [0.010, 0.050] permitted range | Completes at 0.002 and 0.20 kg/s; higher flow narrows the T_w−T_pcm gap (0.771 °C → 0.502 °C) — correct direction |
| Capsules removed (N=0) | E_charge = 0 |

All 10/10 gating checks pass. Every expected direction was written into
the test code *before* running it (see `gate2_limiting_cases`).

**Informational, non-gating (Rajasthan-specific):**
`rajasthan_cluster0_plain_tank_overheat` — Cluster 0's **plain-tank**
(no PCM at all) water temperature reaches **68.6 °C**, above the frozen
65 °C PCM material-stability limit, on solar input alone. This is recorded
inside the verification report so the safety-limit violations seen in the
Phase 3 smoke runs are unambiguously attributed to Rajasthan Cluster 0's
hot-dry / high-clearness collector input against the frozen 50 L tank /
1.5 m² collector sizing — **not** a capsule-sizing choice. It never
changes a gate verdict. See `docs/00_MASTER_OVERVIEW.md` and
`results/README.md` (Phase 3 section) for the full context.

## Gate 3 — Baseline comparison: **PASS**

| Design | Useful energy | Solar fraction | Unmet energy |
|---|---|---|---|
| Plain tank (no PCM) | 1585.7 kWh | 54.97% | 1141.5 kWh |
| Fixed PCM, RT50, max feasible fraction (~12.9%) | 1580.6 kWh | **55.08%** | 1138.6 kWh |
| "Optimized-looking" (~10.2% fraction) | 1581.9 kWh | 55.07% | 1139.0 kWh |

**RT50 beats the plain tank here** on solar fraction and unmet energy —
unlike Tamil Nadu's rank-1 PCM (n-Octacosane, `Tm = 61.6 °C`), which did
not. RT50's `Tm = 48 °C` sits close to this tank's actual operating range,
so it activates as latent storage rather than merely displacing sensible
water. The margin is small (0.11 percentage points) because the reachable
PCM fraction is capped at ~12.9% (see `02_PHASE2_GEOMETRY_CONSTRAINTS.md`),
but the direction is correct without any special pleading.

**Capability check** (synthetic PCM, same geometry/fraction, `Tm = 40 °C`
matched to the tank's operating range): solar fraction 55.60%, mean liquid
fraction 0.426 — a decisive, well-cycling improvement over plain tank,
confirming the simulator rewards a well-matched PCM.

**Ambient-loss diagnostic (Bug-Fix 1, confirms the loss term is active):**
removing `U_tank` entirely raises solar fraction from 55.08% to 57.05% —
i.e. *no-loss ≥ with-loss*, confirming `Q_loss = U_tank·A_tank·(T_w−T_amb)`
is genuinely active in every case (the exact Objective 1 TN failure mode
this project was warned about).

Gate 3's pass/fail is gated on the capability check **and** the active
loss term, not on whether today's shortlisted PCM happens to win — both
pass.

## Gate 4 — Published-benchmark calibration: **PASS**

Cited benchmark band (Singh et al. 2025): 54–84% solar fraction.
This simulator's "optimized-looking" design: **55.07%** — **inside the
band**.

Unlike Tamil Nadu (51.39%, 2.6 points below the band and reported as a
PASS-WITH-CAVEAT), Rajasthan's stronger solar resource lands the same
50 L-tank / 300 L-day / no-backup-heater configuration inside the cited
range without any tuning.

## Gate 5 — Sensitivity & monotonicity: **PASS (3/3)**

| Check | Result |
|---|---|
| Latent heat +10% vs −10% | More PCM energy cycled with more latent heat (15.66 vs 14.07 kWh) — correct direction |
| Flow +50% vs −50% | Pump energy ≥ with higher flow (both ≈ 0 in this sparse-bed design — see caveat) |
| Reduced effective tank-loss coefficient (ambient-warming proxy) | Lower E_loss (70.17 vs 77.64 kWh) — correct direction |

**Caveat on the flow check** (inherited from TN): at the PCM fractions
reachable here (≤ 12.9%), the packed-capsule bed is sparse enough that
Ergun pressure drop — and therefore pump energy — is numerically tiny at
*any* permitted flow rate, so this check is directionally correct but a
weak discriminator. It becomes meaningful once Phase 5 explores denser
designs.

## Go/No-Go

Framework rule: residual < 0.5% **and** ≥ 3/5 gates clean.
Result: max residual 0.0016%, **5/5 gates clean** → **GO**.

(Rajasthan verifies one gate cleaner than Tamil Nadu, which had Gate 4 as
PASS-WITH-CAVEAT for 4/5 clean — same code, better-matched PCM and
stronger solar resource.)

**Simulator released as `sim_v1_rajasthan`.** Tag this at the next commit
so Phase 5's DOE cases can record which simulator version produced them
(framework doc: never mix outputs from two simulator versions in one
training dataset without a version feature).
