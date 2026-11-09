#!/usr/bin/env bash
# tank_run.sh <case_dir>  -- run a tank_make_case.py case in WSL (blockMesh, setFields if present,
# checkMesh, buoyantPimpleFoam) on the Linux disk and copy everything back.
SRC="$(readlink -f "$1")"; ID="$(basename "$SRC")"; W="$HOME/o2_runs/tank_$ID"
source /usr/lib/openfoam/openfoam2406/etc/bashrc >/dev/null 2>&1
rm -rf "$W"; mkdir -p "$HOME/o2_runs"; cp -r "$SRC" "$W"; cd "$W" || exit 1
rm -rf postProcessing log.*
blockMesh > log.blockMesh 2>&1 || { tail -25 log.blockMesh; exit 2; }
[ -f system/setFieldsDict ] && setFields > log.setFields 2>&1
checkMesh > log.checkMesh 2>&1; grep -q "Mesh OK" log.checkMesh || { tail -30 log.checkMesh; exit 2; }
t0=$(date +%s); buoyantPimpleFoam > log.solver 2>&1; rc=$?
echo "solver exit $rc, $(( $(date +%s) - t0 )) s, $(ls -d [0-9]* | wc -l) time dirs"
[ $rc -eq 0 ] || { tail -25 log.solver; }
touch "$ID.foam"; mkdir -p "$SRC"; cp -r "$W"/. "$SRC"/; exit $rc
