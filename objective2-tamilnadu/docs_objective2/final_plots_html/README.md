# Final Plots (Interactive HTML) — Objective 1 & Objective 2

One folder with the headline/final-result plots from both objectives, so
they don't have to be hunted down across `tamilnadu_pipeline/`'s many plot
subfolders (`comprehensive/`, `raw_interactive/`, `post_preprocess_interactive/`,
`processed/clustering/interactive/`, `tamilnadu_objective1/`, `outputs/`...)
or Objective 2's own `results/tamilnadu/plots/interactive/`.

These are **copies**, not the source of truth — see "Source" under each
plot below for where each one is actually generated and regenerated from.
Objective 1's plots were copied from `tamilnadu_pipeline/` (read-only for
Objective 2 — that folder is never written to by this project); Objective
2's plots are copied from this repo's own `results/tamilnadu/plots/interactive/`,
which already holds the complete set of 17 interactive plots if you need
one not collected here (Phases 2-8, not just the final result).

Open any `.html` file directly in a browser — each is self-contained
(loads Plotly from `cdn.plot.ly`, no other local files required), so they
work from this folder regardless of where the original was generated.

## Objective 1 — climate regimes + PCM shortlist

| File | What it shows | Source data |
|---|---|---|
| `objective1/02_climate_regime_map_interactive.html` | Spatial GMM clustering of Tamil Nadu into the **K=3 climate regimes** Objective 2 designs against | `tamilnadu_pipeline/data/processed/clustering/cluster_assignments_tamilnadu.csv` (lat/lon + `cluster_id` per grid point) |
| `objective1/13_recommended_pcm_summary_interactive.html` | **The literal Objective 1 → Objective 2 handoff artifact**: Top-3 PCM per regime, ranked by 4-method MCDM consensus (TOPSIS+GRA+PROMETHEE II+VIKOR, Borda-combined) | `tamilnadu_pipeline/data/processed/pcm/mcdm_topk_by_cluster.csv`, filtered to `consensus_rank<=3` — this exact file is what `configs/states/tamilnadu.yaml`'s `pcm_shortlist` was copied from (see [18_OBJECTIVE1_SHORTLIST_RESTORED.md](../18_OBJECTIVE1_SHORTLIST_RESTORED.md)) |
| `objective1/14_mcdm_winner_map_interactive.html` | Geographic map of which PCM wins consensus rank 1 at each surveyed point, colored by winning PCM | Same `mcdm_topk_by_cluster.csv`, `consensus_rank==1`, merged onto `cluster_assignments_tamilnadu.csv`'s lat/lon |

Regenerate from `tamilnadu_pipeline/plots/generate_tamilnadu_plots.py` (Objective 1's own script — not touched or run by Objective 2).

## Objective 2 — physical design search + robustness

| File | What it shows | Source data |
|---|---|---|
| `objective2/phase7_pareto_by_regime.html` | All 240 simulator-confirmed candidate designs (useful energy vs. PCM mass) per regime, black star = the design actually selected. Hover any point for its exact arrangement/geometry/flow values | `results/tamilnadu/optimized_designs.csv` (Phase 7 real-simulator confirmation) + `deployable_design_per_regime.csv` (the winners) |
| `objective2/phase8_robustness_probabilities.html` | Final robustness validation: P(meets delivery), P(meets demand), P(temperature-safe) per regime under 120 Monte Carlo draws/design, against the framework's pre-declared thresholds | `results/tamilnadu/robustness_summary.csv` |

Regenerate with `python -m src.plots.make_plots tamilnadu` from
`objective2_design_optimization/` (writes the full 17-plot set to
`results/tamilnadu/plots/`; re-copy the two files above into this folder
if regenerated).

## Headline result these plots support

RT57HC (regime 0) / n-Hexacosane (C26) (regime 1) / n-Pentacosane (C25)
(regime 2) — every one confirmed present in Objective 1's actual Top-3
shortlist for its regime, each beating plain tank only marginally, none
robust to the 95% temperature-safety bar. Full writeup:
[18_OBJECTIVE1_SHORTLIST_RESTORED.md](../18_OBJECTIVE1_SHORTLIST_RESTORED.md).
