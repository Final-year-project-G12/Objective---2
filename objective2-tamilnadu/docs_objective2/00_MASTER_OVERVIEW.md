# 00 — Objective 2 Master Overview (Tamil Nadu, Phases 1–8 — COMPLETE)

## What this covers

Objective 2 turns Objective 1's output — climate regimes + a shortlisted
PCM per regime — into a **physical PCM-storage design and a validated
simulator** that Objective 3 can build a controller against. This
consolidated set of docs covers **all eight phases**, implemented,
verified, and completed for **Tamil Nadu** against the **2026-09-18**
data/methodology state: a refreshed Objective 1 pipeline, capsule
arrangement restored as a searched design variable, and — the most
important correction — Objective 2's PCM search space restored to
Objective 1's own actual shortlisted candidates.

> **✅ 2026-09-18 update: Objective 1's actual PCM shortlist restored as
> Objective 2's search space.** Re-reading the project's own formal
> objective statements exposed a scope violation: the 2026-09-17
> "Tm-retargeting" methodology (doc 12) had Objective 2 silently
> re-deriving its own melting-point target and re-ranking PCMs from
> scratch, so the PCM actually deployed in 2 of 3 regimes was **not** one
> of Objective 1's Top-3 candidates. Objective 1's job is to shortlist
> candidate materials; Objective 2's job is to search geometry/arrangement/
> flow for those candidates and pick among them by simulated performance —
> not substitute a different material. `configs/states/tamilnadu.yaml` was
> restored to Objective 1's literal `Tm_target_C`/`pcm_shortlist` output
> and Phases 5-8 re-run against it. See
> `18_OBJECTIVE1_SHORTLIST_RESTORED.md` for the full before/after and
> results.
>
> **2026-09-17 update (still in effect): Objective 1 data refresh +
> arrangement restoration.** Two changes landed together:
> 1. **Objective 1 was re-run** with updated scripts — GMM regime count
>    K=5→**K=3**, real elevation (was a flat 150 m placeholder), a
>    rewritten MCDM/feasibility engine. See `16_OBJECTIVE1_DATA_REFRESH.md`.
> 2. **Capsule arrangement restored as a searched variable**
>    (single-layer/staggered/radial — was frozen to staggered-only,
>    contradicting the objective statement). See
>    `17_ARRANGEMENT_RESTORATION.md`.
>
> Every doc numbered 00–15 in this folder, plus `RESULTS.md` and the
> framework audit report, **describe pre-2026-09-17 runs** and are archived
> under `docs_objective2/archive/` with supersession headers — valid
> historical record of methodology decisions (bounds widening, selection-
> rule scope correction, MCDM re-ranking + safety tie-break — docs 13-15
> still apply as-is; doc 12's Tm-retargeting is superseded as a *mechanism*
> but its diagnostic findings are still cited, see doc 18). **For the
> current, authoritative phase-by-phase record, see
> `docs_objective2/tamilnadu_phase_docs/00`–`08_*_TAMILNADU.md`** and
> `18_OBJECTIVE1_SHORTLIST_RESTORED.md` for the final numbers.

| Phase | Deliverable | Status |
|---|---|---|
| Phase 1 | D2.1 — frozen state config (`configs/states/tamilnadu.yaml`), K=3 regimes, Objective 1's own `Tm_target_C`/PCM shortlist (unedited) | COMPLETE |
| Phase 2 | D2.2 — geometry & constraint engine, arrangement-branched (3 packing models) | COMPLETE |
| Phase 3 | D2.3 — grey-box enthalpy simulator, arrangement pass-through | COMPLETE |
| Phase 4 | Simulator verification, Gates 1–5, arrangement-aware | COMPLETE — **GO**, `sim_v2_tamilnadu` |
| Phase 5 | D2.4 — DOE, arrangement-stratified — 219 cases, 107 valid | COMPLETE |
| Phase 6 | D2.5 — surrogate, arrangement one-hot feature — R²=0.9999 on `useful_energy_kWh` | COMPLETE |
| Phase 7 | D2.6 — optimization spans arrangement, simulator confirmation — surrogate-vs-sim error 0.03% | COMPLETE |
| Phase 8 | D2.7/D2.8/D2.9 — robustness, recommendation cards, Objective 3 contract | COMPLETE |

## Code map

Same file layout as before the 2026-09-17 change (no new top-level
modules; existing modules edited) — see
`docs_objective2/tamilnadu_phase_docs/00_MASTER_CHANGE_PLAN_TAMILNADU.md`
for the exact file-by-file diff. `src/` remains fully state-agnostic —
`state="tamilnadu"` is just a string; running for Rajasthan/Assam/
Uttarakhand requires only their own `configs/states/<state>.yaml` plus
their `data/objective1/`, `data/weather/`, `data/demand/` folders (and,
per `obj2_revised`'s cross-state rule, this same arrangement-restoration
change applied to their copy of `design_bounds_shared.yaml` before any
comparison is valid).

## Headline result: Phase 4 verdict = **GO**, 5/5 gates clean

```
Gate 1 (conservation):        PASS   max residual = 0.000303 %  (limit: <0.5%)
Gate 2 (limiting cases):      PASS   13/13 checks
Gate 3 (baseline comparison): PASS   fixed PCM beats plain tank: 59.0% vs 56.1% solar fraction
Gate 4 (published benchmark): PASS   59.03% — inside the cited 54-84% band
Gate 5 (sensitivity):         PASS   3/3 checks

Go/No-Go: GO  ->  simulator released as sim_v2_tamilnadu
```

## The findings worth reading before anything else

**1. Every deployed PCM is now genuinely one of Objective 1's Top-3
candidates — regime 0 got Objective 1's literal #1 pick.** Deployable
designs: regime 0 = **RT57HC** (radial), regime 1 = **n-Hexacosane (C26)**
(single-layer), regime 2 = **n-Pentacosane (C25)** (single-layer). All
three beat plain tank only marginally (+0.1%, +0.1%; see caveat below for
regime 1), a far more modest — and more honest — result than the previous
Tm-retargeted run's ~59% solar-fraction claims built on PCMs Objective 1
never shortlisted. Arrangement is not a strong winner this time either:
only regime 0 picked radial; regimes 1 and 2 landed on single-layer,
consistent with Phase 6's finding that arrangement has near-zero direct
effect on the continuous performance targets. See
`docs_objective2/tamilnadu_phase_docs/07_PROMPT_PHASE7_OPTIMIZE_TAMILNADU.md`
and `18_OBJECTIVE1_SHORTLIST_RESTORED.md`.

**2. Regime 1's selection-rule tie-break leaves energy on the table —
found and reported, not smoothed over.** The safety-first tie-break
correctly excludes the single highest-energy regime-1 candidate
(n-Pentacosane, 1625.23 kWh) because it fails nominal temperature safety.
But among the remaining safety-compliant candidates, the *next* tie-break
criterion (pump energy) decides on differences of order 1e-7 kWh —
simulator noise — and it did not pick the safety-compliant candidate with
the most energy: a safety-compliant RT57HC candidate at 1624.22 kWh was
available within tolerance, ~0.06% above the design actually selected
(n-Hexacosane, 1623.22 kWh, itself ~0.05% *below* plain tank's 1623.96
kWh). The selection rule is working exactly as documented; whether its
tie-break order should be revisited (e.g. break on energy margin before
pump energy) is an open question flagged for the next iteration. See
`docs_objective2/tamilnadu_phase_docs/08_PROMPT_PHASE8_HANDOFF_TAMILNADU.md`.

**3. No selected design meets the 95% robustness bar under realistic
uncertainty.** Phase 8's Monte Carlo (120 draws/design, PCM property/
weather/demand/mains-temperature uncertainty, a real 10-year historical
weather ensemble) found P(temperature-safe) of 0%, 19%, and 0% for
regimes 0/1/2 respectively — none clear the framework's ≥95% bar, even
though P(meets demand) is 72-100% and P(meets delivery) is 99-100% across
the board. This directly follows from Phase 7's own nominal constraint
margins (regimes 0 and 2 were already negative under nominal operation;
regime 1 was a thin +0.12°C) and is the expected consequence Objective
1's actual shortlist PCMs (melting at 54-58°C) carry, flagged in advance
in doc 18. Reported plainly, not hidden — this is the direct evidence for
why Objective 3's active bypass shield is a hard requirement for every
regime in this state, not an optional feature. See
`docs_objective2/tamilnadu_phase_docs/08_PROMPT_PHASE8_HANDOFF_TAMILNADU.md`.

All three findings are the pipeline working correctly and surfacing real,
sometimes uncomfortable results, not defects to paper over — exactly what
Objective 2 exists to do.

## Final plots (interactive HTML, one folder)

`docs_objective2/final_plots_html/` collects the headline-result plots
from **both** objectives in one place — Objective 1's are otherwise
scattered across ~10 subfolders under `tamilnadu_pipeline/data/plots/`,
and this avoids having to hunt through them. Objective 1's regime map +
final PCM shortlist + MCDM winner map, and Objective 2's Phase 7
candidate-pool Pareto plot + Phase 8 robustness bars — each self-contained
and openable directly in a browser. See
`docs_objective2/final_plots_html/README.md` for the full list with exact
data provenance per plot. (These are copies for convenience; Objective 2's
complete 17-plot interactive set remains the source of truth at
`results/tamilnadu/plots/interactive/`, and Objective 1's plots are
regenerated from `tamilnadu_pipeline/plots/generate_tamilnadu_plots.py`,
never from this project.)

## Documents in this folder

**Current (2026-09-18) phase-by-phase record** — primary reference:
`docs_objective2/tamilnadu_phase_docs/00_MASTER_CHANGE_PLAN_TAMILNADU.md`
through `08_PROMPT_PHASE8_HANDOFF_TAMILNADU.md`, plus
`18_OBJECTIVE1_SHORTLIST_RESTORED.md` for the final, authoritative
results table.

**Still-current methodology docs** (re-applied unchanged against the
current data — see `16_OBJECTIVE1_DATA_REFRESH.md` for why they remain
valid):
- `13_DESIGN_BOUNDS_WIDENING.md` — why `capsule_count.max` was widened
  24→37
- `14_SELECTION_RULE_SCOPE_CORRECTION.md` — why plain tank is excluded
  from the final PCM-only selection pool
- `15_MCDM_RERANKING_AND_SAFETY_TIEBREAK.md` — why safety is the first
  tie-break among energy-qualified candidates (still applies; the
  "real 4-method MCDM engine replaces a substitute shortlist" part is
  superseded by doc 18 — Objective 2 no longer re-ranks PCMs at all)

**Superseded as a mechanism, kept as a cited diagnostic** (see doc 18):
- `12_TM_TARGET_RETARGETING.md` — re-deriving `Tm_target_C` from the
  tank's own simulated behavior is no longer how Objective 2 chooses its
  search space, but the diagnostic question it answers ("does the
  simulator's own optimum disagree with Objective 1's formula?") remains a
  legitimate, reported finding, not Objective 2's actual mechanism.

**Change summaries** (index docs, point to the detailed phase docs for
mechanics/results):
- `16_OBJECTIVE1_DATA_REFRESH.md` — what changed upstream (2026-09-17) and
  why the older docs are archived, not deleted
- `17_ARRANGEMENT_RESTORATION.md` — the arrangement-as-searched-variable
  change (2026-09-17), phase by phase, including the void-fraction physics
  bug found and fixed while implementing it
- `18_OBJECTIVE1_SHORTLIST_RESTORED.md` — **(2026-09-18, most recent)**
  the PCM-shortlist scope correction and final Phase 5-8 results

**Reference / governing specs** (`reference/` subfolder, unchanged
content, still the governing methodology documents):
- `reference/O2_Unified_PerState_Execution_Framework.md`
- `reference/Objective2_PCM_Design_Optimization_Workflow.md`

**Archived** (`archive/` subfolder, pre-2026-09-17 snapshots, superseded —
kept for historical record only, each with a supersession header):
- `archive/RESULTS.md`
- `archive/O2_Framework_Audit_Report_TamilNadu.md`
- Phase docs `01`–`04`, `06`–`08`, `10`, `11` in this folder's root
  describe the pre-refresh (K=5, staggered-only, `sim_v1`) run — read them
  for historical context on methodology only, not for current numbers.

**Still accurate as-is** (structural/reference, not results):
- `HOW_TO_RUN.md` — commands (update pending: add `--arrangement` flag
  documentation)
- `REFERENCES.md` — literature base, mapped per-phase (unaffected by the
  data refresh)
- `OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` — update pending, see caveat there
- `plots/*.md` — describe the pre-refresh plot set; the plots themselves
  (`results/tamilnadu/plots/`) are regenerated and current as of
  2026-09-18, but these narrative `.md` companions have not been rewritten
  to match

## Literature

Every phase doc has its own "Literature" section pointing at the specific
citations that ground its design choices; `REFERENCES.md` is the single
master list all of them link back to. At the whole-project level:
**[Chen2025]** and **[Singh2025]** anchor the collector/tank baseline and
the Gate 4 benchmark band (now genuinely met, 59.03%); **[Rubitherm2024]**/
**[PLUSS2024]** anchor PCM material properties including the 65°C safety
limit behind Finding 2 above; **[Chopra2023]** anchors the Monte Carlo
robustness methodology (Phase 8); **[Sivaraj2023]** and **[Emami2026]**
anchor the Objective 3 hand-off's DRL framing.
