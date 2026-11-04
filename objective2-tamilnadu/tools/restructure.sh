#!/bin/bash
# restructure.sh
# ==============
# Promotes rajmethod/ to the project root and retires the older implementation.
#
# WHY
#   "rajmethod" named the METHOD's origin (Manvitha's Rajasthan pipeline), not
#   the data, which made the project look like it was about Rajasthan. The
#   pipeline, the selected designs, the figures and the report all come out of
#   that directory, so it is the project -- it should not be a subfolder with a
#   misleading name.
#
# SAFETY
#   Nothing is deleted. The old implementation is MOVED to
#   archive/old_implementation/. Two parts of it are still live and are kept in
#   the new tree instead:
#     src/cfd/                   built the ANSYS tank+PCM+panel figures
#     results/tamilnadu/plots/   the ~20 phase2-8 figures, verified unshifted
#
#   rajmethod/config.py already derives every path from its own BASE_DIR, and
#   rajmethod/data/ is a complete copy (all 60 raw weather JSONs included), so
#   the promotion does not break path resolution. The few scripts that reach
#   OUT of rajmethod are fixed afterwards by fix_paths_after_restructure.py.
set -euo pipefail
cd "/c/Users/jaswi/OneDrive/Desktop/ALL/SEM_7/project/jammalamadugu/new_obj/objective2_design_optimization"

OLD=archive/old_implementation
mkdir -p "$OLD" tools

say() { echo "  $*"; }

echo "== 1. preserve the two live pieces of the old tree =="
mkdir -p .restructure_keep
[ -d src/cfd ] && cp -r src/cfd .restructure_keep/cfd && say "kept src/cfd"
[ -d results/tamilnadu/plots ] && cp -r results/tamilnadu/plots .restructure_keep/phase_figures \
  && say "kept results/tamilnadu/plots ($(ls results/tamilnadu/plots/static/*.png 2>/dev/null | wc -l) figures)"

echo "== 2. retire the old implementation =="
for d in src scripts tests configs data results _archive __pycache__; do
  [ -e "$d" ] && mv "$d" "$OLD/" && say "-> $OLD/$d"
done
for f in pipeline.py config.py run_rajasthan_pipeline.py benchmark_parallel.py \
         build_demand_profile.py build_input_package.py build_regime_weather.py \
         validate_multinode.py validate_multinode_fast.py validate_nsga2.py \
         validate_surrogates.py; do
  [ -e "$f" ] && mv "$f" "$OLD/" && say "-> $OLD/$f"
done

echo "== 3. promote rajmethod to the root =="
shopt -s dotglob
for p in rajmethod/*; do
  name=$(basename "$p")
  [ "$name" = "__pycache__" ] && { rm -rf "$p"; continue; }
  [ "$name" = "docs" ] && [ -z "$(ls -A "$p" 2>/dev/null)" ] && { rmdir "$p"; continue; }
  mv "$p" . && say "rajmethod/$name -> $name"
done
shopt -u dotglob
rmdir rajmethod 2>/dev/null && say "removed empty rajmethod/"

echo "== 4. fold the kept pieces back in =="
[ -d .restructure_keep/cfd ] && mv .restructure_keep/cfd src/cfd && say "src/cfd restored"
[ -d .restructure_keep/phase_figures ] && mkdir -p figures \
  && mv .restructure_keep/phase_figures/* figures/ 2>/dev/null \
  && say "figures/ populated from the phase2-8 plots"
rm -rf .restructure_keep

echo "== 5. clearer names =="
[ -d docs_objective2 ] && mv docs_objective2 docs && say "docs_objective2 -> docs"
# The directory is ANSYS Fluent work; the OpenFOAM tree it was named for is
# already archived, so the name actively misleads.
[ -d ansys_openfoam_case ] && mv ansys_openfoam_case ansys && say "ansys_openfoam_case -> ansys"

echo "== 6. build tooling out of the project root =="
for f in package.json package-lock.json build_tn_report.js; do
  [ -e "$f" ] && mv "$f" tools/ && say "-> tools/$f"
done
[ -d node_modules ] && mv node_modules tools/ && say "-> tools/node_modules"
[ -e archive_sweep.sh ] && mv archive_sweep.sh tools/ && say "-> tools/archive_sweep.sh"

echo
echo "done. new top level:"
ls -p | sed 's/^/    /'
