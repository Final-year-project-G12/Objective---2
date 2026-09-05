# Phase 4 Plots — Simulator Verification Gates

Files: `phase4_gate1_residuals.*`, `phase4_gate3_baseline_comparison.*`,
`phase4_gate5_sensitivity.*`.

---

## Plot 1 — Gate 1: energy-conservation residual, 5 diverse cases

**What it is**: the same 5 cases from `src/verify/gates.py::gate1_conservation`
(different clusters, PCMs, a no-PCM baseline, a bounds-extreme design),
plotted as a log-scale bar of `residual_pct_of_collector`, with the 0.1%
pass threshold and 0.5% stop threshold marked as reference lines.

**What we infer**: every bar sits many orders of magnitude below even the
0.1% pass line (values are in the 10⁻⁶–10⁻⁵% range) — the log scale is
necessary precisely because the residuals are so small that a linear
axis would show five invisible slivers at zero. This holds across
completely different designs (different clusters, different PCMs, a
plain-tank baseline, and the largest permitted design), not just one
lucky case.

**How to justify it**: *"The log scale itself is evidence: we needed it
because every residual is close enough to zero that a normal bar chart
would just show five flat lines at the bottom. This is also the plot to
show if asked 'how do you know the simulator conserves energy' — before
the reverse-collector-flow fix documented in the Phase 3 doc, this same
chart would have shown a bar around 1.6%, above even the stop threshold;
after the fix, every case dropped to noise level."*

---

## Plot 2 — Gate 3: solar fraction, plain tank vs PCM designs

**What it is**: four bars — plain tank, the maximum-feasible-PCM-fraction
design (n-Octacosane, 12.9%), an "optimized-looking" PCM design (10.2%),
and the Gate-3 capability check (a synthetic PCM with melting point
matched to this tank's real operating range, Tm=40°C instead of
n-Octacosane's 61.6°C) — all at the same weather/demand/geometry
otherwise.

**What we infer**: the two real-PCM bars (51.16%, 51.39%) sit *slightly
below* the plain tank (52.26%) — the headline "PCM doesn't clearly help
here" finding, visible directly rather than only as numbers in a table.
The capability-check bar (55.19%) sits clearly above all three, proving
the simulator rewards a well-matched PCM decisively when given one — which
is what rules out "the simulator can't model PCM benefit" as an
explanation for the other three bars looking so similar.

**How to justify it**: *"Read this chart left to right: if PCM were
useless in this simulator, the green bar (capability check) would look
like the other three. It doesn't — it's 3 percentage points higher. That
contrast is the whole argument in one picture: n-Octacosane at this tank
size isn't winning because its melting point (61.6°C) is higher than
where this tank spends most of its time, not because PCM physics is
broken in the model."* Note the y-axis intentionally starts at 0 (not
zoomed into 50–56%) so the ~1–3 point differences are shown at true
scale, not visually exaggerated.

---

## Plot 3 — Gate 5: sensitivity/monotonicity spot checks

**What it is**: two side-by-side 3-bar charts. Left: PCM charge energy at
latent heat −10% / baseline / +10%. Right: pump energy at flow −50% /
baseline / +50%.

**What we infer**: both charts step monotonically in the expected
direction — more latent heat capacity → more energy the PCM can absorb
(charge energy rises); more flow → more pumping work (pump energy rises).
Neither line dips or reverses direction, which is what "monotonicity"
means here and is exactly what Gate 5 checks for.

**How to justify it**: *"These are the two clearest of Gate 5's three
checks to show visually — each one is a direct 'if X increases, does Y
move the physically correct way' test, and both charts step up cleanly
left to right with no reversal. The third Gate-5 check (reduced
tank-loss coefficient as an ambient-warming proxy) is in the verification
report as a number rather than a chart here, since it's a single before/
after comparison rather than a three-point trend."*
