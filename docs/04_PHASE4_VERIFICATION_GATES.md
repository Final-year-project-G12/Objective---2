# 04 — Phase 4 Audit: Simulator Verification Gates (All Four States)

File: `src/verify/gates.py` (byte-identical logic/thresholds across
states; only per-state test inputs — clusters, PCM names — differ).
Reduced 5-gate battery per `O2_Unified_PerState_Execution_Framework.md`.

## Gate verdicts side by side

| Gate | Tamil Nadu | Rajasthan | Assam | Uttarakhand |
|---|---|---|---|---|
| 1 — Energy conservation | PASS (max 0.00008%) | PASS (max 0.0016%) | PASS (0.000000% all 5 cases) | PASS (max 0.002764%) |
| 2 — Limiting cases | PASS 10/10 | PASS 10/10 + 1 informational | PASS 10/10 + 1 informational | PASS 10/10 |
| 3 — Baseline comparison | PASS (with caveat: PCM doesn't beat plain tank; capability check does) | **PASS** — RT50 (Tm=48°C) beats plain tank outright (55.08% vs 54.97% SF) | **FAIL** — plain tank beats PCM AND the matched-Tm capability check | PASS (with caveat: PCM doesn't beat plain tank; capability check does) |
| 4 — Published benchmark | PASS-WITH-CAVEAT (51.39% vs 54–84% band) | **PASS** (55.07%, inside band) | PASS (61.76%, inside band) | PASS-WITH-CAVEAT (40.41% vs 54–84% band) |
| 5 — Sensitivity/monotonicity | PASS 3/3 | PASS 3/3 | PASS 3/3 | PASS 3/3 |
| **Gates clean** | 4/5 | **5/5** | **4/5** | 4/5 |
| **Go/No-Go** | GO | GO | GO | GO |

All four states clear the framework's "residual < 0.5% AND ≥3/5 gates
clean" rule, so all four release a `sim_v1_<state>` simulator tag. **Only
Rajasthan achieves a fully clean 5/5** — its rank-1 PCM (RT50, Tm=48°C)
happens to sit close enough to this tank's actual operating range to win
outright at Gate 3, and its stronger solar resource lands the
"optimized-looking" design inside the Gate-4 benchmark band without any
tuning. **Assam is the only state where Gate 3 outright fails** — its
capability check (a synthetic PCM matched to the tank's own operating
range) *still* loses to plain water, a stronger negative signal than
either Tamil Nadu's or Uttarakhand's Gate 3 caveat, where the capability
check does clearly win.

## Gate 3 detail — the capability check across states

| State | Plain tank SF | Shortlisted PCM SF | Matched-Tm synthetic PCM SF | Capability check confirms simulator rewards good PCM? |
|---|---|---|---|---|
| Tamil Nadu | 52.26% | 51.16–51.39% (loses) | 55.19% (Tm=40°C) | **Yes** |
| Rajasthan | 54.97% | 55.07–55.08% (**wins**) | 55.60% (Tm=40°C) | Yes (and the actual PCM already wins) |
| Assam | 62.51% | 61.54–61.76% (loses) | 60.65% (Tm=40°C) | **No — the capability check itself loses too** |
| Uttarakhand | 40.71% | 40.32–40.41% (loses) | 41.27% (Tm=40°C) | Yes |

Assam's Gate 3 is qualitatively different from the other three: in
Tamil Nadu, Rajasthan, and Uttarakhand, a synthetic PCM with a melting
point matched to the tank's actual operating range clearly beats plain
water, ruling out a simulator bug and confirming the non-improvement is
specific to the *shortlisted* PCM's melting point. In Assam, **even the
matched-Tm synthetic PCM loses** — a genuinely different and stronger
finding that Assam's own Phase 7 optimization run did not act on (see
`08_PHASE7_OPTIMIZATION.md`).

## Ambient-loss diagnostic (all four states — confirms `Q_loss` is genuinely active)

Removing `U_tank` raises solar fraction in every state (Tamil Nadu
51.16%→52.69%; Rajasthan 55.08%→57.05%; Assam 61.54%→65.10%; Uttarakhand
40.32%→41.42%) — the no-loss-≥-with-loss direction confirms the ambient
loss term is genuinely active everywhere, ruling out the specific
Objective 1 Tamil Nadu failure mode (an accidentally-disabled loss term)
that motivated this diagnostic in the first place.

## Literature review — why a 5-gate reduced battery, and why these specific benchmarks

- **The gate structure itself** (conservation → limiting cases → baseline
  comparison → published-benchmark calibration → sensitivity) follows
  standard simulation-verification-and-validation practice: check the
  model obeys its own physics before checking it against any external
  reference, then check it against one, then check its response
  direction is physically sensible — the same ordering Barqawi et al.
  (2025) and Eldokaishi et al. (2022) implicitly follow when validating
  their own PCM-SWH numerical models before drawing design conclusions
  from them.
- **The 54–84% Gate-4 solar-fraction band** is drawn directly from Singh
  et al. (2025)'s comprehensive review of published PCM-SWH solar
  fractions (`Singh2025PCMSWH`) — a review, not a single experiment, so
  it is treated here explicitly as "a calibration target, not a universal
  constant," per the framework's own instruction, which is why a
  below-band result (Tamil Nadu, Uttarakhand) is reported as a caveat
  rather than tuned away.
- **The independent 94.2%-storage-efficiency / 31.7-hour-retention
  reference** from Chen et al. (2025) is used as a second calibration
  anchor precisely because it comes from a different experimental rig
  than Singh et al.'s review sample — agreement or disagreement with two
  independent sources is more informative than either alone.
