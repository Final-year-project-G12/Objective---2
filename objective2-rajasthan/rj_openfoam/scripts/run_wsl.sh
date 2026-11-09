#!/bin/bash
# Run one generated case in WSL on the Linux filesystem (the project path has spaces, which OpenFOAM rejects, and /mnt/d is slow),
# then copy everything back.   usage (inside WSL):  [MESH_ONLY=1] scripts/run_wsl.sh /mnt/d/.../cases/<case>
SRC="$(readlink -f "$1")"; NAME="$(basename "$SRC")"; RUN=$HOME/rj_runs/$NAME
source /usr/lib/openfoam/openfoam2406/etc/bashrc
mkdir -p $HOME/rj_runs; rm -rf "$RUN"; cp -r "$SRC" "$RUN"; cd "$RUN"
START=$(date +%s)
if [ -n "$MESH_ONLY" ]; then
  blockMesh > log.blockMesh 2>&1; checkMesh -allGeometry -allTopology > log.checkMesh 2>&1
else
  ./Allrun
fi
echo "wall_seconds $(( $(date +%s) - START ))" > wall_time.txt
cp -r "$RUN"/. "$SRC"/
