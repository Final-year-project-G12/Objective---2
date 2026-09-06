# Phase 6 Plots — AI Surrogate Model

Files: `phase6_parity_plots.*`, `phase6_feature_importance.*`. Data
source: the trained models in `results/tamilnadu/surrogate/models.pkl`,
evaluated on the 30-row hold-out set (never seen during training).

---

## Plot 1 — Surrogate parity plots (hold-out set)

**What it is**: the classic ML validation plot. X-axis = the real
simulator's value; Y-axis = the surrogate's prediction for the *same,
held-out* case; dashed line = perfect agreement (y=x). One panel each for
`useful_energy_kWh` and `solar_fraction`.

**What we infer**: every point sits almost exactly on the dashed line
across the full range of both targets (useful energy ranges ~1620–1820
kWh across the 5 regimes; solar fraction ~0.505–0.545) — visually
confirming the R² values reported in `07_PHASE6_SURROGATE.md` (0.9999 and
0.9990) rather than asking the reader to trust a table. There's no
fan-out or curvature at the extremes (which would indicate the surrogate
struggles outside the bulk of its training data) — points near both ends
of the range track the line just as tightly as points in the middle.

**How to justify it**: *"A high R² number can hide a model that's
accurate on average but wildly wrong on a few points — a parity plot
can't hide that, because every single hold-out case is its own dot. Here,
30 independent hold-out cases across all 5 regimes and all 4 PCM/baseline
groups sit on the line. That's the strongest single piece of evidence
that this surrogate is trustworthy enough to drive Phase 7's search."*

---

## Plot 2 — Feature importance (useful_energy_kWh model)

**What it is**: the top-15 features by ExtraTrees `feature_importances_`
for the `useful_energy_kWh` regressor, horizontal bar chart.

**What we infer**: the top four features — `RH_mean_true`,
`GHI_daily_kWh_mean`, `HSI`, `DTR_true_mean` — are **all climate-signature
features**, and together they dwarf everything else in the list (each
over 0.1 importance vs <0.02 for everything below them). Every design
variable (`n_capsule`, `capsule_diameter_m`, `flow_rate_kg_s`) and every
PCM property (`Tm_C`, `latent_heat_kJ_kg`, `TC_W_mK`, ...) **doesn't even
make the top 15** — only two geometry-derived features
(`geom_void_fraction`, `geom_pcm_volume_fraction`) appear at all, right at
the bottom with near-zero importance.

This is not a weakness of the surrogate — it is a correct read of the
data it was trained on. Annual useful energy varies by **hundreds of
kWh** between climate regimes (1622–1818 kWh, Phase 5 doc) but by only a
**few kWh** between different PCM/geometry choices *within* the same
regime (Phase 7: PCM beats plain tank by ~0.08% at best). A model that
explains variance will naturally attribute almost all of it to whichever
features actually drive the large swings — here, climate. This is a
**third independent line of evidence**, after Gate 3's baseline
comparison and Phase 7's full search, all pointing at the same
conclusion: in this project's current design-bounds/PCM-shortlist
combination, climate — not PCM choice or geometry — is what dominates
useful energy.

**How to justify it**: *"We didn't expect design variables to rank near
zero going in — but it's consistent with, and independently confirms,
what Gate 3 and Phase 7 already found through completely different
methods (a hand-picked baseline comparison, and a 400-candidate search).
Three independent techniques — a controlled physics comparison, a full
optimization search, and now a data-driven feature-importance ranking —
all agree that within this design space, climate variation dominates
outcome variation far more than PCM/geometry choice does. That kind of
agreement across independent methods is much stronger evidence than any
one of them alone."*
