# Phase 7 Plots — Optimization Pass + Simulator Confirmation

Files: `phase7_pareto_by_regime.*`, `phase7_surrogate_vs_simulator.*`,
`phase7_safety_compliance.*`. Data source: `results/tamilnadu/
optimized_designs.csv` (all 400 simulator-confirmed candidates, plain
tank included for comparison) and `deployable_design_per_regime.csv` (the
5 final PCM-only selections) — read directly, nothing recomputed.

*(These plots reflect the current, final methodology: retargeted
`Tm_target_C`, widened design bounds, the PCM-only selection rule, the
real-MCDM shortlist, and the safety-first tie-break — see
`docs_objective2/12_TM_TARGET_RETARGETING.md`, `13_DESIGN_BOUNDS_
WIDENING.md`, `14_SELECTION_RULE_SCOPE_CORRECTION.md`, and
`15_MCDM_RERANKING_AND_SAFETY_TIEBREAK.md`.)*

---

## Plot 1 — Useful energy vs PCM mass, all 400 confirmed candidates

**What it is**: one small-multiple panel per regime (5 panels), each
showing every simulator-confirmed candidate for that regime as a point
(colored by PCM / plain-tank baseline), with the black star marking the
design the selection rule actually chose for that regime.

**What we infer**: in every regime now, the star sits *inside or at the
top edge of* a PCM point cluster, not at `x=0` — a real change from the
original run, where it sat at zero PCM mass in 4/5 regimes. The vertical
gap between the star and the best plain-tank point (still visible at
`x=0` in each panel, for comparison) is small but consistently positive
— the star's useful energy is a few kWh above the plain-tank baseline in
every panel, matching the +0.08–0.12% margins in `08_PHASE7_
OPTIMIZATION.md`. Within each PCM's own point cluster, useful energy still
trends slightly *downward* as PCM mass increases past a certain point —
more PCM is not simply "more storage, more benefit" here.

**How to justify it**: *"This plot is the direct visual evidence for the
optimal-PCM-design result: in every regime, the selected design (the
star) sits above the zero-mass plain-tank point, not on top of it. The
margin is modest — you can see it's a small vertical gap, not a dramatic
one — which is honest: this is a real but not large improvement, exactly
what the numbers in the report say. If someone asks 'is this a fair
comparison or did you force it,' point out that the plain-tank point is
still plotted in every panel for comparison — nothing was hidden, PCM
simply now sits above it."*

---

## Plot 2 — Surrogate-predicted vs simulator-confirmed useful energy

**What it is**: a parity plot (predicted vs actual, dashed y=x line) for
all 400 candidates the search proposed and then re-ran in the real
simulator (broadened from an original 100 specifically to check for a
search-coverage gap — see `08_PHASE7_OPTIMIZATION.md`) — not the Phase 6
hold-out set, a much wider, independent check across the design space.

**What we infer**: all 400 points sit tightly on the diagonal, visibly
clustering into 5 tight groups — one per climate regime — with almost no
vertical spread within each cluster. Mean error across all 400 is 0.04%
(vs. 0.02% on the original, smaller 100-candidate check) — still two
orders of magnitude below the 15% large-error threshold, and the small
increase is expected when confirming 4× more candidates including some
further from the training distribution.

**How to justify it**: *"Phase 6 tells you the surrogate is accurate on
average, on a random hold-out sample. This plot tells you it's *also*
accurate specifically where the optimizer went looking for the best
designs — over four times as many candidates as the original check,
specifically to rule out the possibility that a safe, competitive PCM
design was sitting somewhere the smaller search missed. Zero of these 400
candidates exceeded the 15% large-error threshold."*

---

## Plot 3 — Temperature-safety compliance of confirmed candidates

**What it is**: a stacked bar per regime — how many of that regime's
confirmed PCM candidates stayed within the temperature-safety envelope
(max water ≤75°C, max PCM ≤65°C, zero violations all year) vs how many
didn't.

**What we infer**: in regimes 0–3, **zero of the 60 PCM candidates tested
per region** (spanning the full 8–37 capsule / 0.02–0.08 m diameter
range) are safe — not a coverage gap, a structural result (confirmed by a
follow-up direct test: even the smallest possible PCM dose already
violates the limit by thousands of hours/year in these regimes, see
`08_PHASE7_OPTIMIZATION.md`). In regime 4, **40 of 60** PCM candidates are
safe, and — after the safety-first tie-break fix (doc 15) — the *selected*
design (RT45HC) is now one of them, with a real +0.39°C nominal margin,
not the razor-thin 0.009°C an earlier, now-superseded pick had. Phase 8
shows this still doesn't fully survive real-world uncertainty (30.8% safe
under Monte Carlo, not the ~100% this nominal-only chart might suggest),
but it's a meaningfully better starting point than before.

**How to justify it**: *"This chart shows the physical wall this project
ran into after PCM started winning on energy: PCM's 65°C material limit
is ~10°C tighter than water's own 75°C scald limit, and these climates
already push tank water into the 70-72°C range on sunny days regardless
of PCM. That's not a search-coverage problem — we tested the entire
design space in regimes 0-3 and found zero safe PCM candidates, at any
mass. It's exactly the gap Objective 3's active bypass is designed to
close, made concrete and quantified rather than assumed."*

## Literature

See `08_PHASE7_OPTIMIZATION.md`'s "Literature" section for the full
mapping. Most directly relevant here: **[Rubitherm2024]** is the
datasheet source of the 65°C limit this plot visualizes as a physical
wall; **[Assareh2023]**/**[Chen2025]** ground the search-then-select
methodology producing the candidates shown. See
`docs_objective2/15_MCDM_RERANKING_AND_SAFETY_TIEBREAK.md` for why
regime 4's star moved to a safer point in Plot 1/3.
