# 10 — Phase 8 Audit: Robustness, Recommendation Cards, Objective 3 Hand-off (All Four States)

Files: `src/robustness/monte_carlo.py`, `src/robustness/weather_ensemble.py`
(Tamil Nadu/Uttarakhand only — see below), `src/handoff/build_recommendation_cards.py`,
`src/handoff/build_obj3_contract.py`. **Rajasthan and Tamil Nadu jointly
originated this phase's methodology** (each independently building the
first version, then converging via cross-review); Uttarakhand adopted it
unchanged; **Assam has not run this phase at all.**

## Status side by side

| | Tamil Nadu | Rajasthan | Assam | Uttarakhand |
|---|---|---|---|---|
| Phase 8 run? | Yes | Yes | **No** | Yes |
| Draws/design | 120 | 120 | — | 120 |
| Weather-noise source | **Real 10-year (2016–2025) historical ensemble** + per-hour synthetic jitter | Assumed uniform range (`U(0.93,1.07)` GHI, `U(-1.5,1.5)°C` T_amb) + per-hour jitter | — | **Real 10-year historical ensemble** + per-hour jitter |
| Fixed thresholds | `solar_fraction≥0.45` (delivery), `≥0.50` (demand) | same | — | same |
| Contract file | `obj3_environment_contract_tamilnadu.json` | `obj3_environment_contract_rajasthan.json` | **does not exist** | `obj3_environment_contract_uttarakhand.json` |

**Tamil Nadu and Uttarakhand use a real 10-year historical weather
ensemble for the annual-scale component of each Monte Carlo draw**
(closing an external-audit gap that flagged the original assumed-range
approach); **Rajasthan still uses the assumed-range version** — a
methodological difference between states worth stating explicitly if
these robustness numbers are ever compared directly. Assam cannot be
compared at all on this phase since it was never run.

## Result table — all three completed states

| State | Regime | Design | P(meets demand) | P(temp-safe) | Robust? |
|---|---|---|---|---|---|
| Tamil Nadu | 0 | Plain tank | 89.2% | 92.5% | No |
| Tamil Nadu | 1 | Plain tank | 90.0% | 80.0% | No |
| Tamil Nadu | 2 | Plain tank | 94.2% | 71.7% | No |
| Tamil Nadu | 3 | Plain tank | 95.0% | 79.2% | No |
| Tamil Nadu | 4 | n-Octacosane | **69.2%** | **40.8%** | No |
| Rajasthan | 0 | Plain tank | 87.5% | 56.7% | No |
| Rajasthan | 1 | Plain tank | 99.2% | 45.0% | No |
| Rajasthan | 2 | Plain tank | 80.0% | 53.3% | No |
| Uttarakhand | 0 | Plain tank (nominally unsafe, see `08_…`) | 0.0% | 44.2% | No |
| Uttarakhand | 1 | Plain tank | 0.0% | 91.7% | No |
| Uttarakhand | 2 | PureTemp 58 | 0.0% | **100.0%** | No |
| Uttarakhand | 3 | Plain tank | 0.0% | 64.2% | No |
| Uttarakhand | 4 | Plain tank | 0.0% | 83.3% | No |

**Not one regime, in any completed state, is "robust" by the framework's
own rule** (P(demand) ≥ 75% and P(temp-safe) ≥ 95%). Three distinct
failure patterns emerge:
- **Tamil Nadu**: the one PCM regime is the *worst* performer on both
  axes at once (a PCM design must respect two temperature limits instead
  of one).
- **Rajasthan**: demand reliability is fine everywhere, but temperature
  safety fails badly and uniformly (45–57%) even though every selected
  design is a plain tank — a pure consequence of the hot-dry climate
  against the frozen collector/tank sizing, with no PCM even present to
  blame.
- **Uttarakhand**: demand reliability is **zero everywhere** (nominal
  solar fractions structurally below the fixed 50% bar in this cold
  climate), while temperature safety is *reversed* from Tamil Nadu — the
  one PCM regime (2) is the **safest** (100%), because the cold climate
  keeps the tank from overheating in the first place.

## Literature review — why Monte Carlo robustness, and why fixed (not self-referential) thresholds

- **Running a Monte Carlo robustness pass at all**, rather than reporting
  only nominal (single-weather-year) performance, follows the same
  reasoning as Chopra et al. (2023)'s Monte Carlo techno-economic
  assessment of a solar collector-storage system
  (`Chopra2023MonteCarloETC`) — nominal performance is a poor predictor
  of real-world reliability once weather, demand, and mains-temperature
  variability are accounted for.
- **Fixed, state-independent "meets demand/delivery" thresholds**
  (`solar_fraction ≥ 0.50` / `≥ 0.45`), rather than a threshold defined
  relative to each design's own nominal value, is a deliberate
  methodological choice recorded in Tamil Nadu's own Phase 8 audit: an
  early version used a self-referential threshold and found every regime
  trivially scored 100% reliable, which hid real differences (e.g.
  Tamil Nadu regime 4's genuine demand-reliability weakness). Switching
  to a fixed, cross-state-comparable threshold is what actually reveals
  Uttarakhand's 0%-everywhere demand result — an uncomfortable but real
  finding a self-referential metric would have hidden.
- **Drawing the annual weather-noise component from a real 10-year
  historical ensemble** (Tamil Nadu, Uttarakhand) rather than an assumed
  uniform range is the more defensible methodological claim for a paper
  — "we sampled the actual 10 years this region experienced" versus "we
  assumed a plausible range" — even though, in Tamil Nadu's case, the
  real observed variability turned out to be narrower than the original
  assumption and moved every regime's numbers by only a few points.
