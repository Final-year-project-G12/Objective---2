"""
scripts/organize_repo.py
===========================
Moves files that are not part of the live Objective-2 deliverable into
`_archive/`, and Objective-3 hand-off material into `objective3/`.

NOTHING IS DELETED. Every move is reversible, and `--dry-run` (the
default) prints the plan without touching anything. The repository has no
git history to fall back on, so delete-in-place would be unrecoverable;
archive-in-place is not.

WHAT COUNTS AS ARCHIVE
  * superseded planning docs and the dated history/ trail -- useful for
    provenance, not for running or reading the current result
  * prompt packs for the other three states (out of scope here, and the
    v3.0 config change invalidates their results anyway -- that is noted
    in the config, not silently ignored)
  * one-off exploratory HTML plot dumps
  * stale result files produced before the 2026-10-28 shield fix and the
    v3.0 design space: these are WRONG, not merely old, so leaving them
    next to current results would be worse than archiving them

WHAT STAYS
  * the simulator, the pipeline, the configs, the current results
  * the validation scripts (they are the evidence for the physics claims
    and are meant to be re-runnable)
  * the docs a reader needs: README, HOW_TO_RUN, RESULTS, DATA_REFERENCE,
    REFERENCES, CFD_VERIFICATION, and the Rajasthan port progress log

OBJECTIVE 3 goes to its own folder rather than the archive: it is live
work, just not Objective 2's, and the user asked for it kept out of
`results/`.
"""

import argparse
import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ARCHIVE = BASE / "_archive"
OBJ3 = BASE / "objective3"

# (source relative to BASE, destination subdir under _archive, reason)
ARCHIVE_PLAN = [
    ("docs_objective2/history", "docs/history",
     "dated development trail -- provenance only"),
    ("docs_objective2/other_states_prompts", "docs/other_states_prompts",
     "other three states; out of scope and invalidated by config v3.0"),
    ("docs_objective2/final_plots_html", "docs/final_plots_html",
     "one-off exploratory HTML plot dump"),
    ("docs_objective2/presentation", "docs/presentation",
     "superseded presentation material"),
    ("OBJECTIVE2_REDESIGN_PROPOSED_PLAN.md", "docs/OBJECTIVE2_REDESIGN_PROPOSED_PLAN.md",
     "proposal superseded by the implemented port"),
    ("docs_objective2/TAMILNADU_REDESIGN_PLAN.md", "docs/TAMILNADU_REDESIGN_PLAN.md",
     "plan superseded by the implemented port"),
]

# Objective-3 OUTPUTS and docs move; the generator code does NOT.
# src/handoff/ stays where it is because pipeline.py imports from it --
# including build_recommendation_cards, which is an Objective-2
# deliverable, not an Objective-3 one. Moving the package would break the
# pipeline's "handoff" stage for the sake of tidiness, which is a bad
# trade. objective3/README.md points at the generator instead.
OBJ3_PLAN = [
    ("docs_objective2/OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md", "OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md",
     "Objective-3 hand-off doc"),
    ("results/tamilnadu/obj3_environment_contract_tamilnadu.json",
     "obj3_environment_contract_tamilnadu.json",
     "Objective-3 contract output -- kept out of results/ per request"),
]

# Result files produced BEFORE the 2026-10-28 shield fix / v3.0 design space.
# These are superseded and wrong, not just old.
STALE_RESULT_GLOBS = [
    "results/tamilnadu/optimized_designs.csv",
    "results/tamilnadu/deployable_design_per_regime.csv",
    "results/tamilnadu/robustness_results.csv",
    "results/tamilnadu/robustness_summary.csv",
    "results/tamilnadu/recommendation_cards.md",
    "results/tamilnadu/surrogate_top_candidates.csv",
    "results/tamilnadu/surrogate_error_by_group.csv",
    "results/tamilnadu/sobol_smoke.csv",
]


def _move(src: Path, dst: Path, dry: bool, reason: str, log: list):
    if not src.exists():
        return
    log.append((str(src.relative_to(BASE)), str(dst.relative_to(BASE)), reason))
    if dry:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        # never clobber a previous archive entry
        stem, suffix = dst.stem, dst.suffix
        n = 2
        while dst.exists():
            dst = dst.with_name(f"{stem}__{n}{suffix}")
            n += 1
    shutil.move(str(src), str(dst))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="actually move files (default is a dry run)")
    ap.add_argument("--include-stale-results", action="store_true", default=True,
                    help="also archive pre-2026-10-28 result files")
    args = ap.parse_args()
    dry = not args.apply
    log = []

    for rel, dest, reason in ARCHIVE_PLAN:
        _move(BASE / rel, ARCHIVE / dest, dry, reason, log)
    for rel, dest, reason in OBJ3_PLAN:
        _move(BASE / rel, OBJ3 / dest, dry, reason, log)
    if args.include_stale_results:
        for rel in STALE_RESULT_GLOBS:
            _move(BASE / rel, ARCHIVE / "results_pre_shield_fix" / Path(rel).name,
                  dry, "superseded by the 2026-10-28 shield fix + config v3.0", log)

    width = max((len(a) for a, _, _ in log), default=10)
    print(f"{'PLAN (dry run)' if dry else 'MOVED'}: {len(log)} entries\n")
    for src, dst, reason in log:
        print(f"  {src:<{width}}  ->  {dst}\n      {reason}")
    if dry:
        print("\nNothing moved. Re-run with --apply to perform these moves.")
    else:
        for marker, text in [
            (ARCHIVE / "README.md",
             "# _archive\n\nSuperseded material, kept for provenance. Nothing here is "
             "part of the current Objective-2 deliverable.\n\n`results_pre_shield_fix/` "
             "holds result files produced BEFORE the 2026-10-28 two-part-shield fix and "
             "the v3.0 design space. Those numbers are wrong, not merely old -- see "
             "docs_objective2/RAJASTHAN_METHOD_PORT_PROGRESS.md.\n"),
            (OBJ3 / "README.md",
             "# objective3\n\nObjective-3 hand-off material, kept out of Objective 2's "
             "`results/` on purpose.\n\nThe environment contract here must be regenerated "
             "after the Objective-2 rebuild completes: it was written from the "
             "pre-shield-fix designs.\n\nThe GENERATOR stays in the Objective-2 tree at "
             "`src/handoff/build_obj3_contract.py` (run via `python pipeline.py --stage "
             "handoff`), because `pipeline.py` imports that package and it also holds "
             "`build_recommendation_cards`, which is an Objective-2 deliverable.\n"),
        ]:
            if marker.parent.exists():
                marker.write_text(text, encoding="utf-8")
        print(f"\nwrote {ARCHIVE / 'README.md'} and {OBJ3 / 'README.md'}")


if __name__ == "__main__":
    main()
