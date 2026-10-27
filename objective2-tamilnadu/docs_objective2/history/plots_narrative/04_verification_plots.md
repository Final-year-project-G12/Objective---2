# Phase 4 Plots — Simulator Verification Gates

> **Note (2026-09-13):** Plot 2 was regenerated at the user's request to
> reflect the current, post-revision state (Tm-retargeting + bounds
> widening + selection-rule correction, docs 12–14) instead of the
> original n-Octacosane/Tm=61.6°C pre-fix diagnostic. **The original
> Gate 3 verification run itself is unchanged** — the pass/fail verdict,
> `simulator_verification_report.txt`, and `04_PHASE4_VERIFICATION_GATES.md`
> still describe the original diagnostic (that is what proved the
> simulator wasn't broken and motivated the fixes); this plot is now a
> separate, current-state comparison layered on top, not a re-run of
> Gate 3's actual pass/fail logic. The engine-verification plots (Gate 1,
> Gate 5) are unaffected by any revision.

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

## Plot 2 — Gate 3 (current): solar fraction, plain tank vs PCM designs

**What it is**: four bars, all for regime 0, all computed fresh from the
current config (post Tm-retargeting + bounds-widening) — plain tank, the
current shortlist PCM (n-Tetracosane, C24) at the widened max-feasible
fraction (`capsule_count.max=37`), that same PCM at its actual Phase 7
deployable geometry (the current optimum: 0.0433 m diameter, 11 capsules,
0.0235 kg/s), and the same synthetic-Tm=40°C capability check as before —
all at the same weather/demand otherwise.

**What we infer**: every PCM bar now sits *above* plain tank (52.26%):
max-feasible fraction reaches 53.46%, the actual deployable/optimum design
reaches 52.32% (a modest but real +0.06 pp — matching the +0.11%
useful-energy margin reported in `08_PHASE7_OPTIMIZATION.md`, since these
are two different normalizations of nearly the same gap), and the
capability check reaches 56.00%, still comfortably the highest bar. This
is the direct visual consequence of the two design-space fixes (doc
12/13) plus using the actual current shortlist PCM instead of the
original n-Octacosane: what used to be the "PCM barely helps" diagnostic
picture is now a "PCM wins, and the simulator was always capable of
showing an even bigger win with a better-matched melting point" picture.

**How to justify it**: *"This is the same Gate-3-style comparison, now
run with the current, corrected PCM/design instead of the original
diagnostic snapshot. Every real-PCM bar clears plain tank, and the
capability-check bar (still the highest) shows there's more headroom left
if an even better-matched PCM existed — consistent with, not
contradicting, the original Gate 3 diagnosis that started this whole
correction chain."* Note the original Gate 3 pass/fail verdict itself is
unchanged (see the note above this plot) — only this comparison chart was
regenerated.

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
