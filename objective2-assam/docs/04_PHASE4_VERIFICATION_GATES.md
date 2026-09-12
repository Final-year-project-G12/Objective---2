# 04 — Phase 4 Audit: Simulator Verification Gates (Assam)

File: `src/verify/gates.py`. Output:
`results/phase4_simulator_verification_report_assam.txt`.

> This doc previously described Rajasthan's Gate results (RT50, 5/5
> clean, Gate 3 PASS). Assam's actual report is materially different —
> **Gate 3 FAILS** here. Rewritten from the real report file below.

## Gate 1 — Energy conservation: PASS

5 diverse cases (all 3 clusters, savE® OM48, a no-PCM baseline, a
bounds-extreme design), each a full simulated year:

| Case | Residual (% of E_collector) |
|---|---|
| A: cluster0 / savE® OM48 / mid design | 0.000000% |
| B: cluster1 / savE® OM48 / small-capsule design | 0.000000% |
| C: cluster2 / savE® OM48 / large-capsule design | 0.000000% |
| D: cluster2 / no-PCM plain-tank baseline | 0.000000% |
| E: cluster0 / savE® OM48 / bounds-extreme design | 0.000000% |

Mean and max residual both report as 0.000000% (below the report's
printed precision) — far inside the 0.1% pass threshold.

## Gate 2 — Limiting cases: PASS (10/10 + 1 informational)

All 10 gating checks pass (zero irradiance, zero flow, no PCM, zero
latent heat, very-high conductivity, perfectly insulated tank, empty
demand, solid/liquid initial PCM, flow at range limits, capsules
removed) — same qualitative behavior as Rajasthan/Tamil Nadu's runs of
the same state-agnostic engine.

**Informational, non-gating:** `assam_cluster0_plain_tank_overheat` —
Cluster 0's plain tank (no PCM) reaches **66.83 °C**, already above the
65 °C PCM material-stability limit, on solar input alone. Same pattern
as Rajasthan's Cluster 0 (68.6 °C) — a frozen-collector/tank-sizing
effect, not a capsule-sizing choice.

## Gate 3 — Baseline comparison: **FAIL**

| Design | Useful energy (kWh) | Solar fraction | Unmet energy (kWh) |
|---|---|---|---|
| Plain tank (no PCM) | 680.9 | **62.51%** | 399.5 |
| Fixed PCM, savE® OM48, max feasible fraction | 671.4 | 61.54% | 409.9 |
| "Optimized-looking" (~mid fraction) | 673.8 | 61.76% | 407.6 |

**The plain tank beats both PCM configurations** — savE® OM48
(Objective 1's actual rank-1 PCM for Cluster 0, Tm = 51.0 °C) does
**not** beat the plain tank in this 50 L / ~12.9%-fraction design.

**Capability check** (synthetic PCM, `Tm = 40 °C`, matched to this
tank's own operating range): SF 60.65% vs plain tank's 62.51% — **the
matched-Tm PCM still loses to plain water.** `Simulator rewards a
well-matched PCM over plain tank: False.` This is a stronger negative
result than Rajasthan or Tamil Nadu saw at this checkpoint (their
capability checks both showed a clear PCM win) — it says the failure
here is not just "the shortlisted PCM's melting point is a poor match,"
but that under Assam's colder mains temperature (16.6–19.9 °C) and
smaller 100 L/day demand, *no* single-Tm PCM at this tank's PCM
fraction outperforms plain sensible storage in this simulator.

**Ambient-loss diagnostic** (confirms `Q_loss` is genuinely active):
removing `U_tank` raises solar fraction from 61.54% to 65.10% (no-loss
≥ with-loss) — the loss term is active, so Gate 3's failure is a real
PCM-vs-water result, not a broken loss term.

**Gate 3 verdict: FAIL** — gated on the capability check and the active
loss term, exactly like Rajasthan/Tamil Nadu's Gate 3, but Assam's
capability check itself fails (the synthetic matched-Tm PCM still loses
to plain water), which the other two states did not see. This was a
clear, correctly-flagged warning at Phase 4 that the shortlisted PCMs
may not help in Assam's specific tank/demand combination — a warning
Phase 7 later did not act on (see `07_PHASE7_OPTIMIZATION.md`, "The
safety-verdict bug").

## Gate 4 — Published-benchmark calibration: PASS

Cited benchmark band (Singh et al. 2025): 54–84% solar fraction.
Chen et al. 2025 also report 94.2% storage efficiency / 31.7 h retention
on a comparable configuration (a second calibration reference, not a
second hard gate). This simulator's "optimized-looking" design: **61.76%
— inside the band.**

## Gate 5 — Sensitivity & monotonicity: PASS (3/3)

| Check | Result |
|---|---|
| Latent heat +10% vs −10% | More PCM energy cycled with more latent heat (10.31 vs 9.70 kWh charge) — correct direction |
| Flow +50% vs −50% | Pump energy direction correct (both ≈ 0 Wh at these fractions — same weak-discriminator caveat as other states) |
| Reduced effective tank-loss coefficient | Lower E_loss (59.04 vs 65.03 kWh baseline) — correct direction |

## Go/No-Go

Framework rule: residual < 0.5% **and** ≥ 3/5 gates clean.
Result: **max residual 0.000000%, but only 4/5 gates clean (Gate 3
fails)** → still **GO** per the ">=3/5" rule, but this is Assam's
weakest verification pass of the three states run so far (Rajasthan
5/5, and this one 4/5 with the one failure landing squarely on
"does the shortlisted PCM actually help" — the exact question Phase 7
needs to answer correctly).

**Simulator released as `sim_v1_assam` (dated build; tag at commit
time).** The Gate 3 failure should travel with any citation of Assam's
Phase 7 results — it is the same underlying finding Phase 7 arrived at
independently (savE® OM46/OM48 barely beats or loses to plain tank on
energy) and should have been the first signal that the 65 °C PCM safety
filter needed to be checked carefully in Phase 7, not skipped.
