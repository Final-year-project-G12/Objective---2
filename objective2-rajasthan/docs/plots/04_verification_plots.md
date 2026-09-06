# Phase 4 Plots — Simulator Verification Gates (Rajasthan)

Files: `phase4_gate1_residuals.*`, `phase4_gate3_baseline_comparison.*`,
`phase4_gate5_sensitivity.*`. The gate cases mirror
`src/verify/gates.py` for Rajasthan (3 clusters, PCMs `RT50` /
`savE® OM50`).

## Plot 1 — Gate 1: energy-conservation residual, 5 diverse cases

**What it is**: the same 5 cases from `gate1_conservation` (different
clusters, PCMs, a no-PCM baseline, a bounds-extreme design), as a
log-scale bar of `residual_pct_of_collector`, with the 0.1 % pass and
0.5 % stop thresholds marked.

**What we infer**: every bar is well below the 0.1 % pass line — Rajasthan
residuals are ~4×10⁻⁴ % to 1.6×10⁻³ % (a bit higher than Tamil Nadu's
~10⁻⁵ %, still ≈60× inside the pass threshold and ≈300× inside the stop
threshold). The log axis is needed because a linear one would show five
slivers at zero. Holds across completely different designs.

**How to justify it**: *"The log scale itself is the evidence — every
residual is close enough to zero that a normal bar chart would be five
flat lines at the bottom. Before the reverse-collector-flow fix (Phase 3
doc) this chart would have shown a bar around 1.6 %, above the stop
threshold; after the fix, every case is at noise level."*

## Plot 2 — Gate 3: solar fraction, plain tank vs PCM designs

**What it is**: four bars — plain tank, the max-feasible-PCM-fraction
design (`RT50`, ~12.9 %), an "optimized-looking" PCM design (~10.2 %),
and the Gate-3 capability check (a synthetic PCM with Tm = 40 °C matched
to this tank's operating range) — same weather/demand/geometry otherwise.

**What we infer**: the two real-`RT50` bars (55.08 %, 55.07 %) sit
*slightly above* the plain tank (54.97 %) — **the opposite of Tamil
Nadu**, where the shortlisted PCM lost to plain water. RT50's 48 °C
melting point is close enough to this tank's operating range that it
activates as latent storage. The capability-check bar (55.60 %) is higher
still, confirming the simulator rewards a well-matched PCM decisively. The
y-axis starts at 0 so the ~0.1–0.6 point differences are shown at true
scale, not exaggerated.

**How to justify it**: *"Read left to right: RT50 beats plain water here,
just barely (+0.1 point), and the capability check beats it more (+0.6).
So the simulator clearly can reward PCM — the reason RT50's margin is
tiny is the ≤12.9 % PCM fraction the frozen bounds allow, not broken
physics. This is why the Phase 7 selection rule treats RT50 and plain
tank as equivalent on energy and picks the lower mass."*

## Plot 3 — Gate 5: sensitivity / monotonicity spot checks

**What it is**: two side-by-side 3-bar charts. Left: PCM charge energy at
latent heat −10 % / baseline / +10 %. Right: pump energy at flow −50 % /
baseline / +50 %.

**What we infer**: both step monotonically in the expected direction —
more latent heat → more charge energy; more flow → more pump work.
Neither reverses.

**How to justify it**: *"Each chart is a direct 'if X increases, does Y
move the physically correct way' test, and both step up cleanly with no
reversal. The third Gate-5 check (reduced tank-loss coefficient as an
ambient-warming proxy) is a single before/after number in the
verification report rather than a chart."*
