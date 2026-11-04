# ANSYS Fluent figures — what each one shows

All three are current and were produced from solved Fluent cases, not sketched.

---

## 01_system_mesh_zones.png — the tank, capsules and collector panel

The 2-D planar slice of the whole system, coloured by Fluent **cell zone**, with
the cell count of each. It answers "is the thing I meshed actually the thing I
meant to model?"

| zone | cells | what it is |
|---|---|---|
| Tank water | 31,008 | the 100 L store |
| PCM | 4,847 | 34 capsules, outer Ø 42 mm |
| Capsule shell (Al) | 511 | the aluminium wall |
| Collector channel | 3,200 | the flow passage in the panel |
| Absorber plate | 1,200 | where solar flux lands |
| Riser | 2,200 | the pipe returning hot water to the tank |

Tank is 399 × 799 mm. **This is the figure that shows the tank + PCM + panel
structure together.**

What to check in it: the capsules sit in the lower-middle of the tank in a
staggered arrangement, the collector loop is to the left of the tank, and the
riser connects them. Geometry comes from the optimiser's deployable design.

---

## 02_system_temperature_field.png — where the heat actually is

Two panels of the **same solved case**. The left is the whole system on one
colour scale; the right is the tank and capsules only, rescaled.

Two panels are needed because the absorber reaches ~139 °C while the tank sits
near 32 °C. On a single scale the entire tank is one flat black block and you
can see nothing — the right-hand panel is the same data with the scale set to
the tank's own range.

The temperature chain, printed under the figure:

> absorber 139 °C → panel 125 °C → riser 61 °C → water 32.2 °C → PCM 31.6 °C

**What it indicates, and its limitation.** It shows the heat path works end to
end: flux lands on the absorber, conducts through the panel, and the riser
carries it toward the tank. But the caption also says *"PCM stays solid (melts
at 56.5 °C); energy-only, momentum frozen"* — with momentum frozen there is no
circulation to carry panel heat into the store, so the water only reaches
32 °C and **nothing melts in this figure.**

So read this one as a geometry-and-heat-path check, **not** as evidence the PCM
works. That evidence is figure 03.

---

## 03_pcm_melt_comparison.png — the PCM result

The four shortlisted PCMs melted on **one mesh under one duty**, so the only
difference between the curves is the material. Left panel: liquid fraction
against time. Right panel: capsule mean temperature, with each PCM's melt point
as a dotted line in its own colour.

Duty: capsule Ø 42 mm starting at 30 °C solid, immersed in water at 70 °C
(the collector delivery temperature), for a 6 h charging window.

| PCM | melt point | k (W/m·K) | melt fraction at 6 h |
|---|---|---|---|
| **n-Pentacosane (C25)** | 54.0 °C | 0.239 | **0.60** |
| n-Hexacosane (C26) | 56.5 °C | 0.238 | 0.50 |
| RT57HC | 56.5 °C | 0.200 | 0.47 |
| PureTemp 58 | 58.0 °C | 0.150 | 0.38 |

**Why the ordering is believable**, in three independent ways:

- C25 has the lowest melt point, so it starts melting earliest and melts most.
- C26 and RT57HC have the *same* melt point — and the one with higher
  conductivity melts more.
- PureTemp 58 has both the highest melt point and the lowest conductivity, so
  it melts least.

The curves are ordered by physics, not by chance.

**All four solved with zero divergences.** C25 had failed every earlier
attempt; it was fixed by switching the pressure–velocity coupling to Coupled
with first-order upwind, after six other hypotheses were tested and disproved
(see `docs/CFD_VERIFICATION.md`).

**Read the ordering, not the absolute values.** First-order upwind is more
numerically diffusive than second order, so these melt fractions are
conservative — an earlier second-order run of the three PCMs that would solve
gave 0.76 / 0.72 / 0.60 against 0.50 / 0.47 / 0.38 here. The relative ordering
is identical. First order is used because it is the only setting under which
all four PCMs solve, and a comparison is only meaningful when every run shares
the same settings.

Regenerate with `python plot_v4_pcm_comparison.py`.

---

## Not here any more

`mesh_verification.png` was moved to `archive/superseded_docs/`. It documented
a real gmsh bug (`addDisk` created a full circle extending below the symmetry
axis, meaningless for an axisymmetric model) but it describes the **v1
axisymmetric** case on a mesh that is now archived. The melting cases are
**planar**, so keeping it beside current work would mislead.
