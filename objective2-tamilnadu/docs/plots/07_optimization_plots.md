# Phase 7 Plots — Optimization Pass + Simulator Confirmation

Files: `phase7_pareto_by_regime.*`, `phase7_surrogate_vs_simulator.*`,
`phase7_safety_compliance.*`. Data source: `results/tamilnadu/
optimized_designs.csv` (all 100 simulator-confirmed candidates) and
`deployable_design_per_regime.csv` (the 5 final selections) — read
directly, nothing recomputed.

---

## Plot 1 — Useful energy vs PCM mass, all 100 confirmed candidates

**What it is**: one small-multiple panel per regime (5 panels), each
showing every simulator-confirmed candidate for that regime as a point
(colored by PCM / plain-tank baseline), with the black star marking the
design the selection rule actually chose for that regime.

**What we infer**: in regimes 0–3, the star sits at `x=0` (zero PCM mass,
the plain tank) at a height only marginally below the PCM point clusters
above it — visually, the vertical gap between the star and the nearest
PCM cluster is tiny relative to the chart's y-range. In regime 4, the
star sits essentially *at the top* of its own PCM cluster (n-Octacosane),
matching the table in `08_PHASE7_OPTIMIZATION.md` where that regime's PCM
candidate edged out its own plain-tank optimum. Within each PCM's own
point cluster, useful energy trends slightly *downward* as PCM mass
increases past a certain point — more PCM is not simply "more storage,
more benefit" here, an important nuance the summary table alone doesn't
show.

**How to justify it**: *"This is the single plot that explains the
'plain tank wins 4/5 regimes' result better than any table of numbers
can. You can see with your own eyes that the star isn't far below the
PCM clusters — it's almost touching them. The selection rule (5% Pareto
tolerance, then minimize PCM mass) is doing exactly what it's designed to
do: when performance is this close, prefer the simpler, zero-mass
design. If someone asks 'are you sure PCM doesn't help,' point at how
close the star sits to the colored clusters — it's a marginal-benefit
story, not a no-benefit story, and this chart shows the margin directly."*

---

## Plot 2 — Surrogate-predicted vs simulator-confirmed useful energy

**What it is**: a parity plot (predicted vs actual, dashed y=x line) for
all 100 candidates the search proposed and then re-ran in the real
simulator — not the Phase 6 hold-out set, a completely separate 100-point
check from a much wider part of the design space (400 random candidates
per regime×PCM pair).

**What we infer**: all 100 points sit tightly on the diagonal, visibly
clustering into 5 tight groups — one per climate regime — with almost no
vertical spread within each cluster. This is a second, independent
confirmation of surrogate accuracy beyond Phase 6's hold-out R² — this
time over designs sampled specifically because the surrogate thought they
were *good* (the region of the design space an optimizer actually cares
about, not just wherever the DOE happened to land).

**How to justify it**: *"Phase 6 tells you the surrogate is accurate on
average, on a random hold-out sample. This plot tells you it's *also*
accurate specifically where the optimizer went looking for the best
designs — which is the part of the design space where a surrogate is
most likely to be fooled by a sharp, unlearned feature. Zero of these 100
candidates exceeded the 15% large-error threshold; that's why we could
trust the surrogate's ranking in Plot 1 without re-running thousands of
cases in the real simulator."*

---

## Plot 3 — Temperature-safety compliance of confirmed candidates

**What it is**: a stacked bar per regime — how many of that regime's 20
confirmed candidates stayed within the temperature-safety envelope (max
water ≤75°C, max PCM ≤65°C, zero violations all year) vs how many didn't.

**What we infer**: in regimes 0–3, only the 5 plain-tank candidates (out
of 20) are safe — **every PCM candidate confirmed in those regimes
tripped the safety limit at some point in the year.** In regime 4, 15/20
are safe, including several PCM candidates (consistent with that regime
selecting a PCM winner). This was not something Gate 3's two hand-picked
designs surfaced — it only became visible once 100 candidates across the
whole design space were actually checked.

**How to justify it**: *"This is an example of a finding the broader
search caught that a smaller, hand-picked test wouldn't have: PCM designs
in this collector/tank combination run measurably hotter than plain
water, often past the 65°C PCM safety limit, under Tamil Nadu's
irradiance with no active overheat protection modeled. It reinforces the
plain-tank result from a completely different angle — safety, not just
useful energy — and it's a concrete, first-principles reason to add an
explicit high-temperature safety shield/bypass before pursuing wider PCM
fractions, which is exactly what `09_NEXT_STEPS.md` recommends."*
