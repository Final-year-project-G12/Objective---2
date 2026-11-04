# 15 — Full-MCDM Shortlist Adoption + Safety-First Tie-Break (2026-09-14)

**Status: APPLIED. `configs/states/tamilnadu.yaml`'s `pcm_shortlist` per regime replaced with the real 4-method MCDM consensus (this doc, Part 1); `src/optimize/select_deployable.py`'s tie-break order corrected to prefer temperature-safe candidates (this doc, Part 2). Phases 5–8 fully re-run against both changes. See `RESULTS.md` for final numbers.**

This is a deliberate, documented methodology revision — not a silent edit. It has two independent parts; each is justified and evidenced separately below.

---

## Part 1 — Why the real MCDM engine wasn't run, and what changed when it was

### Why it wasn't run

Objective 1's actual PCM-ranking engine (`tamilnadu_pipeline/08_mcdm_ranking.py`) implements TOPSIS + GRA + PROMETHEE II + VIKOR, combined by Borda-count consensus, checked against a 5,000-draw Monte Carlo stability test. When `Tm_target_C` was retargeted per regime (doc 12), the new shortlist needed to be re-derived — but `retarget_tm.py` substituted a much simpler method: recheck each Objective-1 feasibility survivor's melting-window pass/fail against the new target, then rank window-survivors by nothing more than `|Tm_C − new_target|` (closest wins). Doc 12 disclosed this explicitly as "a simpler, explicitly documented substitute... not a re-implementation," but never verified whether it actually agreed with the real method.

### What changed when the real method was run

`src/design/mcdm_reranking.py` (new) ports the real 4-criterion, 4-method, Borda-consensus algorithm from Objective 1's own script — same criteria (`f_Tm` Gaussian melting-point fitness, `latent_heat_margin_ratio`, `rho_H_MJ_m3`, `TC_W_mK`, `cycles_confidence`), same entropy+AHP-blended weights, same consensus rule — and applies it to the current (already-retargeted) `Tm_target_C` per regime, over the same eligibility pool `retarget_tm.py` uses (Objective 1's feasibility survivors, re-filtered against the new melting window, plus a completeness check for the properties the simulator needs).

**Result: every single regime's shortlist changed.**

| Regime | Nearest-Tm shortlist (retarget_tm.py, superseded) | Full-MCDM shortlist (adopted) |
|---|---|---|
| 0 | savE OM49, n-Tricosane (C23), n-Tetracosane (C24) | n-Tetracosane (C24), n-Docosane (C22), PureTemp 53 |
| 1 | n-Tricosane (C23), n-Tetracosane (C24), n-Pentacosane (C25) | n-Tetracosane (C24), n-Docosane (C22), RT45HC |
| 2 | savE OM49, PlusICE A52, n-Tetracosane (C24) | n-Tetracosane (C24), PureTemp 53, n-Hexacosane (C26) |
| 3 | n-Tetracosane (C24), PlusICE A52, PureTemp 53 | n-Tetracosane (C24), PureTemp 53, n-Hexacosane (C26) |
| 4 | n-Tricosane (C23), RT45HC, n-Docosane (C22) | n-Docosane (C22), RT45HC, n-Tetracosane (C24) |

The nearest-Tm method ignores latent heat, thermal conductivity, and cycling confidence entirely — it only sorts by melting-point distance. The real method weighs those in, and n-Tetracosane (C24) — the eligible candidate with the highest latent heat, 255 kJ/kg, in every regime it's eligible for — wins the Borda consensus in 4 of 5 regimes even where it isn't the closest Tm match.

Full per-candidate scores (all four methods' ranks, Borda score, entropy/AHP weights): `results/tamilnadu/mcdm_reranked_full_scores.csv`. Summary comparison: `results/tamilnadu/mcdm_reranked_shortlist_report.csv`.

### Applying it

`python -m src.design.mcdm_reranking tamilnadu` writes the two report files above without touching the pipeline (read-only mode, for review). `python -m src.design.mcdm_reranking tamilnadu --apply` backs up `configs/states/tamilnadu.yaml` (as `.bak_pre_mcdm_rerank`) and overwrites `pcm_shortlist` per regime with the MCDM consensus (`Tm_target_C` itself is untouched). Per the framework's Phase 0 gate, this requires re-running Phases 5–8, which has been done.

---

## Part 2 — Safety-first tie-break (found while verifying the re-run)

### The finding

After re-running Phase 7 against the new MCDM shortlist, inspecting the *full* confirmed candidate pool (`optimized_designs.csv`, not just the winning row) per regime — to check whether any temperature-safe candidate existed within the pre-declared 5% energy tolerance that the old tie-break order (minimize pump energy → PCM mass → capsule count → maximize margin) might have passed over — found:

- **Regimes 0–3**: zero temperature-safe candidates anywhere in the confirmed pool (60 candidates each). The old tie-break order was never actually discarding a safe option here — there wasn't one to discard.
- **Regime 4**: **40 of 60** confirmed candidates were genuinely temperature-safe (positive `constraint_margin_C`), several with *higher* useful energy than the design the old tie-break order picked (e.g. n-Docosane's best candidate: 1630.1 kWh, safe, margin +2.26°C, vs. the old winner's 1623.2 kWh, unsafe, margin −0.21°C). The old rule was choosing an unsafe, lower-mass candidate over a safe, higher-energy one purely because it minimized PCM mass first.

### The fix

`apply_selection_rule()` (`src/optimize/select_deployable.py`) now sorts the within-tolerance candidate pool by `meets_temperature_safety` (descending) **first**, ahead of pump energy/mass/count/margin. This is a strict improvement, not a trade-off within the observed data: it does not touch the 5% tolerance band, the safety limits, or which PCMs are eligible — it only changes which already energy-qualified candidate wins the tie-break, and only matters where a safe candidate actually exists within tolerance (regime 4 here; a no-op everywhere else, verified empirically above).

### Result: regime 4 is now genuinely, nominally temperature-safe

| | Old (n-Tetracosane, mass-first tie-break) | New (RT45HC, safety-first tie-break) |
|---|---|---|
| Useful energy | 1623.2 kWh | **1627.2 kWh** (higher) |
| vs. plain tank | +0.050% | **+0.299%** (higher) |
| PCM mass | 0.41 kg | 2.29 kg |
| Nominal `meets_temperature_safety` | **False** (margin −0.21°C) | **True** (margin +0.39°C) |
| P(temperature-safe), Monte Carlo | ~22–25% | **30.8%** |
| P(meets annual demand), Monte Carlo | ~72% | **76.7%** |

Regime 4 is the *only* regime where a safe alternative existed in the search results — regimes 0–3's numbers are unchanged by this fix (same designs, same Monte Carlo results, verified identical to the pre-fix run). Regime 4 is still not "robust" by the framework's 95%-threshold rule (30.8% < 95%), so Objective 3's active bypass remains necessary everywhere — but it is now the least-exposed regime by a wider, and now nominally real (not razor-thin/negative), margin.

## What this does NOT change

- The Tm-retargeting methodology itself (doc 12) — Tm_target_C values are untouched, only shortlist selection.
- The design-bounds widening (doc 13) — untouched.
- The PCM-only selection scope (doc 14) — untouched; this doc only reorders the tie-break within the already-PCM-only pool.
- The safety limits (`max_water_temp_C=75°C`, `max_pcm_temp_C=65°C`) — untouched; this doc makes the selection rule better at finding candidates that already meet them, it does not relax them.

## Literature

- **[Chen2025]**, **[Rubitherm2024]**, **[PLUSS2024]** — same PCM-property/benchmark sources already cited for docs 12–14; unaffected by this revision.
- The MCDM methodology itself (TOPSIS/GRA/PROMETHEE II/VIKOR/Borda) traces to Objective 1's own established methodology (`tamilnadu_pipeline/08_mcdm_ranking.py`), not a new citation — see that script's own docstring for its literature grounding.
