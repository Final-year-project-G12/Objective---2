#!/usr/bin/env bash
# collector_run.sh <case_dir>  -- blockMesh -> splitMeshRegions -> chtMultiRegionFoam (WSL, Linux disk)
SRC="$(readlink -f "$1")"; ID="$(basename "$SRC")"; W="$HOME/o2_runs/coll_$ID"
source /usr/lib/openfoam/openfoam2406/etc/bashrc >/dev/null 2>&1
rm -rf "$W"; mkdir -p "$HOME/o2_runs"; cp -r "$SRC" "$W"; cd "$W" || exit 1
blockMesh > log.blockMesh 2>&1 || { tail -25 log.blockMesh; exit 2; }
checkMesh > log.checkMesh 2>&1; grep -q "Mesh OK" log.checkMesh || { tail -30 log.checkMesh; exit 2; }
splitMeshRegions -cellZones -overwrite > log.split 2>&1 || { tail -25 log.split; exit 2; }
rm -rf 0; cp -r 0.regions 0
t0=$(date +%s); chtMultiRegionFoam > log.solver 2>&1; rc=$?
echo "solver exit $rc, $(( $(date +%s) - t0 )) s"
[ $rc -eq 0 ] || { tail -30 log.solver; }
postProcess -region water -dict system/water/outletT -latestTime > log.post 2>&1
grep -h "weightedAreaAverage" log.post | tail -2
touch "$ID.foam"; mkdir -p "$SRC"; cp -r "$W"/. "$SRC"/; exit $rc
