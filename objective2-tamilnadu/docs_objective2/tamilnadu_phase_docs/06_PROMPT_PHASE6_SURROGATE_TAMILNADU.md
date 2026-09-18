# 06 — Phase 6 (Tamil Nadu): Arrangement as a Surrogate Feature

**Files touched:** `src/surrogate/features.py`, `src/surrogate/evaluate.py`.
**Not touched:** `src/surrogate/train.py` (no logic change needed — it
already builds its feature set generically from `features.py`, so adding
columns there was sufficient), model family (ExtraTrees + LinearRegression
baseline), seed policy. Adapted from
`a Rajasthan-pilot change plan (source removed from this project after adaptation, see docs_objective2/tamilnadu_phase_docs/)`.

## What was actually run (Tamil Nadu)

1. **`features.py`**: added 3 one-hot columns (`arr_single_layer`,
   `arr_staggered`, `arr_radial`) to the design/geometry feature group
   (9→12 features in that group). No-PCM baseline rows get all three
   forced to zero (paired with `is_no_pcm=1`), not the "staggered" label
   their dummy geometry happens to carry — so the model can't mistake "no
   PCM" for a 4th arrangement category.
2. **Schema fix required by the same Objective 1 data refresh as Phase 1**:
   `monte_carlo_stability.csv` renamed `name`→`pcm_id` and
   `top3_inclusion_probability`→`mc_top3_inclusion_pct` (now a 0-100
   percentage, not a 0-1 probability) — `features.py`'s confidence-feature
   join was updated to match and renormalize back to [0,1].
3. **`evaluate.py`**: error breakdown now includes an `arrangement` group
   and a finer `regime_pcm_arrangement` group (200 rows total, up from the
   pre-arrangement regime/PCM-only file). Added the required arrangement
   feature-importance diagnostic (combined + per-column, per target).

```
python pipeline.py --state tamilnadu --stage surrogate
```

## Results

*(Updated 2026-09-18 for the Objective-1-shortlist restoration — see
[docs_objective2/18_OBJECTIVE1_SHORTLIST_RESTORED.md](../18_OBJECTIVE1_SHORTLIST_RESTORED.md).)*

**80 train / 27 holdout rows** (Phase 5's 107 valid rows split ~75/25).

| Target | ExtraTrees R² | Linear R² | Winner |
|---|---|---|---|
| useful_energy_kWh | **0.99986** | 0.99965 | tree (narrowly) |
| solar_fraction | **0.99935** | 0.98976 | tree |
| unmet_energy_kWh | **0.99993** | 0.99892 | tree |
| pump_energy_kWh | 0.99868 | **0.99992** | linear |
| pcm_mass_kg | 0.99383 | **0.99406** | linear (near-tie) |
| feasibility classifier | accuracy 1.000, infeasible-recall 1.000 | — | — |

`useful_energy_kWh` (the primary Phase 7 ranking objective) clears the
>0.80 exit bar comfortably. `pcm_mass_kg` and `pump_energy_kWh` favoring
linear still makes physical sense — both are near-linear functions of the
design vector (mass ∝ diameter³×count, pump power ∝ a smooth function of
flow) — the same "linear ties/beats tree on near-linear targets" pattern
as before.

**Arrangement feature importance — reported honestly, not forced to look
meaningful:**

| Target | arr_single_layer | arr_staggered | arr_radial | Combined | Finding |
|---|---|---|---|---|---|
| useful_energy_kWh | 0.0000 | 0.0000 | 0.0000 | 0.0000 | minimal effect |
| solar_fraction | 0.0000 | 0.0000 | 0.0001 | 0.0001 | minimal effect |
| unmet_energy_kWh | 0.0000 | 0.0000 | 0.0000 | 0.0000 | minimal effect |
| pump_energy_kWh | 0.0015 | 0.0013 | 0.0002 | 0.0030 | minimal effect |
| pcm_mass_kg | 0.0005 | 0.0005 | 0.0005 | 0.0015 | minimal effect |

Arrangement has essentially **no** direct influence on any continuous
regression target in this design-space region — consistent with Phase 3's
finding (arrangement only changes packing feasibility and pressure
drop/pump power, not the heat-transfer physics itself). Its real effect
shows up as a **feasibility** gate (Phase 5's rejection-rate table), which
the separate feasibility classifier — not these regressors — is
responsible for learning, and which it learned perfectly (1.000
infeasible-class recall).

## Exit check before moving to Phase 7

`useful_energy_kWh` hold-out R² (0.99986) clears 0.80 — proceed with the
surrogate as a ranker, per the framework's own rule that a surrogate is
never the final oracle regardless of how high its R² is.
