# Prompt 2 — Configure and Run Objective 2 for {STATE}

Use only after `01_OBJECTIVE1_SETUP.md`'s output exists in
`data/objective1/*_{STATE}.csv`. Paste this (with `{STATE}` replaced):

---

Objective 1's output for {STATE} now exists in
`new_obj/objective2_design_optimization/data/objective1/*_{STATE}.csv`.
I want to run Objective 2 (PCM capsule/tank design optimization) for
{STATE} using the exact same pipeline code already built and validated
for Tamil Nadu — `pipeline.py` is already state-parameterized (confirmed:
it takes `--state <name>` and only uses it to select
config/weather/results paths), so no code changes should be needed, only
a new config file.

**Step 1 — read before writing anything**: read
`configs/states/tamilnadu.yaml` in full, `docs_objective2/RESULTS.md`
(the current, single reference for Tamil Nadu's real numbers and
methodology — read this, not `history/`, for current state) for the
"Algorithms used" table and the Phase-by-phase status, and
`docs_objective2/history/18_OBJECTIVE1_SHORTLIST_RESTORED.md` for *why*
each field must contain what it does under the CURRENT (correct)
methodology — in particular: `Tm_target_C` and `pcm_shortlist` must come
directly, unedited, from {STATE}'s own Objective 1 output (its
`cluster_profiles_*.csv` and `mcdm_topk_by_cluster.csv` equivalents) — do
not re-derive these via `retarget_tm.py`/`mcdm_reranking.py`, that
mechanism was reverted for Tamil Nadu as a project-objective-statement
violation and must not be reintroduced here. Also note: Tamil Nadu's
simulator and shared config now include a safety shield and a resized
100 L/2.5 m² tank/collector (`system_config_shared.yaml`,
`config_v2.0_2026-10-26`) — {STATE} inherits both automatically with no
extra config needed, but see `00_OVERVIEW.md`'s 2026-10-26/27 note on
checking (not assuming) that 100 L/2.5 m² is still adequate for
{STATE}'s own demand profile.

**Step 2 — write `configs/states/{STATE}.yaml`**: one block per {STATE}
climate regime (however many Objective 1 found — don't assume 3), each
with: `Tm_target_C`, `pcm_shortlist` (the real Top-2/Top-3 from Objective
1), and whatever else `tamilnadu.yaml`'s schema requires (check
`schema.py` for the authoritative field list — don't hand-copy
`tamilnadu.yaml`'s structure blind in case the schema has evolved since).

**Step 3 — run the real pipeline, Phase by Phase, don't skip gates**:
```
python pipeline.py --state {STATE} --stage geometry     # Phase 2 self-test
python pipeline.py --state {STATE} --stage simulate      # Phase 3 demo
python pipeline.py --state {STATE} --stage verify        # Phase 4 gates
python pipeline.py --state {STATE} --stage doe           # Phase 5
python pipeline.py --state {STATE} --stage surrogate     # Phase 6
python pipeline.py --state {STATE} --stage optimize      # Phase 7
python pipeline.py --state {STATE} --stage robustness    # Phase 8
python pipeline.py --state {STATE} --stage handoff        # recommendation cards + Objective 3 contract
```
(Check `pipeline.py --help` for the exact current stage names before
running — they may differ slightly; don't guess if the above doesn't
match what the script reports.) After Phase 4, stop and show me the gate
results before continuing to Phase 5 — don't silently proceed past a
failing gate. Note: for Tamil Nadu, Gate 3 (the capability check) fails
*honestly* even on the final, correctly-sized design — a matched-Tm
synthetic PCM still doesn't beat a plain tank once the tank is sized to
meet demand on its own (see `../RESULTS.md`'s Phase status table). Don't
treat a Gate 3 failure on {STATE} as a bug by default — check whether the
same finding holds, the same way Tamil Nadu's did, rather than assuming
either way.

**Step 4 — report real numbers, not a template**: once Phase 8/handoff
completes, give me the actual per-regime deployable design table (PCM,
capsule diameter, count, arrangement, flow rate, useful energy, solar
fraction) and the robustness summary (P(meets delivery), P(meets demand),
P(temperature-safe)) — read these from the actual output CSVs, the same
way Tamil Nadu's real numbers were reported in `../RESULTS.md`'s
"Deployable design per regime" and "Robustness" tables, not estimated.
