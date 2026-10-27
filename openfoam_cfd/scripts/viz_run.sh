#!/usr/bin/env bash
# viz_run.sh <case_dir>   -- run a (--viz) capsule case to its end time in WSL and copy ALL
# written time directories back, so ParaView can animate the melt front.
#   <case_dir> was written by make_case.py --viz (contains system/, constant/, 0/).
SRC="$(readlink -f "$1")"; ID="$(basename "$SRC")"; W="$HOME/o2_runs/viz_$ID"
source /usr/lib/openfoam/openfoam2406/etc/bashrc >/dev/null 2>&1
rm -rf "$W"; mkdir -p "$HOME/o2_runs"; cp -r "$SRC" "$W"; cd "$W" || exit 1
rm -rf postProcessing log.* [1-9]*
blockMesh > log.blockMesh 2>&1 || { tail -20 log.blockMesh; exit 2; }
checkMesh > log.checkMesh 2>&1; grep -q "Mesh OK" log.checkMesh || { echo "checkMesh failed"; exit 2; }
t0=$(date +%s); buoyantPimpleFoam > log.solver 2>&1; rc=$?
echo "solver exit $rc, $(( $(date +%s) - t0 )) s, $(ls -d [0-9]* | wc -l) time directories"
[ $rc -eq 0 ] || { tail -20 log.solver; exit 3; }
touch "$ID.foam"
rm -rf "$SRC"; mkdir -p "$SRC"; cp -r "$W"/. "$SRC"/
echo "copied to $SRC"
