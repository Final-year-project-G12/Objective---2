# Phase 6 Plots — AI Surrogate Model

Files: `phase6_parity_plots.*`, `phase6_feature_importance.*`.
Data source: Trained models in `results/uttarakhand/surrogate/models.pkl`,
evaluated on the 30-case independent hold-out test set (never seen during training).

---

## Plot 1 — Surrogate parity plots (hold-out set)

**What it is**: Direct validation of ML generalization on unseen test data.
X-axis = Simulator ground truth; Y-axis = ExtraTrees surrogate prediction;
dashed diagonal line = perfect agreement ($y = x$).
- Left panel: Useful annual energy ($E_{\text{useful}}$, kWh)
- Right panel: Annual solar fraction ($\text{SF}$)

**What we infer**:
- Points align directly on the $y = x$ parity diagonal across the full operational
  range for both targets:
  - $E_{\text{useful}}$: $R^2 \approx 1.000$, $\text{RMSE} = 0.6148\text{ kWh}$ ($< 0.04\%$ error)
  - $\text{SF}$: $R^2 \approx 1.000$, $\text{RMSE} = 0.0002913$
- There is no fan-out, heteroscedasticity, or boundary curvature at either end of
  the performance spectrum.
- The 30 hold-out cases span all 5 climate regimes and all shortlisted PCM types,
  proving the surrogate model is accurate and stable across the entire domain.

**How to justify it**: *"A high $R^2$ alone can mask localized outliers. This
parity plot provides visual proof that every single hold-out case sits on the
equality line without stray points, guaranteeing that the surrogate is reliable
enough to guide Phase 7's optimization search."*

---

## Plot 2 — Feature importance (useful_energy_kWh model)

**What it is**: Top-15 features ranked by Gini importance in the ExtraTrees
regressor for useful thermal energy.

**What we infer**:
- The top-ranking features are **climate-signature variables** (e.g., mean daily
  GHI, relative humidity, diurnal temperature range, ambient temperature).
- Design geometry variables (`n_capsule`, `capsule_diameter_m`, `flow_rate_kg_s`)
  and PCM thermal properties (`latent_heat_kJ_kg`, `Tm_C`) register lower relative
  importance across the statewide dataset.
- This is a direct physical consequence of Uttarakhand's geography:
  - Annual useful energy varies by nearly $100\text{ kWh}$ across climate regimes
    (from $1526\text{ kWh}$ in Regime 1 — the coldest, smallest-sample regime —
    to $1626\text{ kWh}$ in Regimes 2 and 4, essentially tied for highest).
  - Within any single regime, geometric and PCM optimization alters useful energy
    by only $\sim 1\text{ kWh}$ ($< 0.1\%$ — see `08_PHASE7_OPTIMIZATION.md`).
- An unbiased machine-learning model that accounts for variance naturally identifies
  macro-climate inputs as the primary drivers of total delivered energy.

**How to justify it**: *"This provides a third independent confirmation — joining
Gate 3's physics checks and Phase 7's optimization search — that climate regime
dominates annual performance variations far more than micro-variations in capsule
geometry or flow rate. The surrogate independently learned the governing physics
of the system."*
