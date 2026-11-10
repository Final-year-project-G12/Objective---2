# Phase 6b Plots — Multi-Fidelity Surrogate Augmentation

File: `phase6b_multifidelity.*`.
Data source: `results/tamilnadu/multifidelity_speedup_report.json` and
`multifidelity_sample_efficiency.csv`.

---

## Plot — speedup (left) + sample-efficiency curve (right)

**What it is**: a two-panel figure. Left: a bar chart comparing total
simulator runtime across all 215 DOE cases at high fidelity (Phase 5's
original adaptive sub-stepping) vs. low fidelity (fixed timestep, no
sub-stepping), with the speedup ratio annotated. Right: hold-out R² for
`useful_energy_kWh` as a line chart against the fraction of high-fidelity
training data used (25/50/75/100%), with one line for the existing
high-fidelity-only surrogate and one for the same model augmented with
the free low-fidelity prediction as an extra feature.

**What we infer**: the left panel shows a real but modest 1.53× speedup —
not the "identical work, half the time" result you might expect, because
this project's actual PCM design spends nearly all year outside the melt
band, so the adaptive sub-stepping mechanism the low-fidelity mode
disables was already rarely triggering. The right panel's two curves sit
close together for `useful_energy_kWh` specifically, because that target
is already at the R² ceiling (>0.999) with the existing high-fidelity-only
approach — this is the one target where multi-fidelity augmentation has
little room to help. (The full `solar_fraction` curve, where the two
lines separate meaningfully at every fraction below 100%, is in
`multifidelity_sample_efficiency.csv` — not plotted here to keep this
figure to two panels, but it's the stronger of the two stories and is
written up in full in `11_MULTIFIDELITY_SURROGATE.md`.)

**How to justify it**: *"We didn't just cite multi-fidelity modeling as a
future-work idea — we built it and measured it. The speedup is honest and
modest (1.53×, not an inflated number), and we explain exactly why:
this project's PCM barely cycles, so the expensive adaptive-stepping
mechanism we're bypassing wasn't doing much work in the first place. The
more interesting result is on the accuracy side, in the full sample-
efficiency table: for solar_fraction, augmenting a much smaller
high-fidelity training set with the free low-fidelity feature recovers
most of the accuracy gap versus using the full expensive dataset alone.
That's the actual practical promise of multi-fidelity modeling — less
expensive simulation, comparable accuracy — demonstrated with real
numbers on our own data, not just asserted from the literature."*

**One honesty note worth repeating if asked**: an earlier version of the
speedup measurement was wrong — it compared a freshly-timed low-fidelity
run against a high-fidelity timing recorded in a separate process run
days earlier, producing a nonsensical result where low fidelity looked
*slower*. This was caught (a "low fidelity is doing strictly less
computation, it cannot legitimately be slower" sanity check) and fixed by
re-timing both fidelities fresh, back-to-back, in randomized order, in
the same process. The 1.53× figure is from that corrected measurement.
Volunteering this if asked ("did you get this right on the first try?")
is a stronger answer than pretending it was clean from the start.
