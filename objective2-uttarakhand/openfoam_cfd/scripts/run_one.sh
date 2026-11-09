#!/usr/bin/env bash
# run_one.sh -- run ONE generated case inside WSL/Ubuntu on the fast Linux disk.
#
#   usage: run_one.sh <case_dir> [work_root]
#
# <case_dir> may live on /mnt/d (Windows). It is copied to ~/o2_runs (ext4,
# 5-10x faster than /mnt/d), meshed, solved, early-stopped once the PCM is
# fully melted and nearly fully charged, and the postProcessing/ + logs are
# copied BACK into <case_dir>. Exit codes: 0 ok, 2 mesh fail, 3 solver fail.
# (no set -u: the OpenFOAM bashrc references unset variables)
SRC="$(readlink -f "$1")"
WORK="${2:-$HOME/o2_runs}"
ID="$(basename "$SRC")"

# shellcheck disable=SC1091
source /usr/lib/openfoam/openfoam2406/etc/bashrc >/dev/null 2>&1

mkdir -p "$WORK"
rm -rf "${WORK:?}/$ID"
cp -r "$SRC" "$WORK/$ID"
cd "$WORK/$ID" || exit 1
# never inherit results of an earlier run (OpenFOAM would write *_0.dat beside the old file)
rm -rf postProcessing log.* last_time kpi.json

blockMesh  > log.blockMesh 2>&1 || { echo "[$ID] blockMesh failed"; cp log.* "$SRC"/; exit 2; }
checkMesh  > log.checkMesh 2>&1
grep -q "Mesh OK" log.checkMesh || { echo "[$ID] checkMesh failed"; cp log.* "$SRC"/; exit 2; }

buoyantPimpleFoam > log.solver 2>&1 &
PID=$!

# early stop: fully melted AND within 15 % of the final sensible swing
Tm=$(python3 -c "import json;m=json.load(open('case_meta.json'));print(m['Tm_C']+273.15)")
Th=$(python3 -c "import json;m=json.load(open('case_meta.json'));print(m['T_hot_C']+273.15)")
DAT=postProcessing/meltAndTemp/0/volFieldValue.dat
while kill -0 "$PID" 2>/dev/null; do
  sleep 20
  [ -f "$DAT" ] || continue
  read -r T A < <(tail -n 1 "$DAT" | awk '{print $2, $3}')
  [ -n "${T:-}" ] || continue
  if awk -v t="$T" -v a="$A" -v tm="$Tm" -v th="$Th" \
       'BEGIN{exit !( a>=0.9995 && (th-t) <= 0.15*(th-tm) )}'; then
    NOW=$(tail -n 1 "$DAT" | awk '{print $1}')
    # atomic update: the solver re-reads controlDict (runTimeModifiable); never let it see a half-written file
    cp system/controlDict system/controlDict.tmp
    foamDictionary -entry endTime -set "$(awk -v n="$NOW" 'BEGIN{print n+5}')" system/controlDict.tmp >/dev/null 2>&1
    mv -f system/controlDict.tmp system/controlDict
    break
  fi
done
wait "$PID"; RC=$?
# a solver that died AFTER the PCM was fully melted and data were written is still a usable run
if [ "$RC" -ne 0 ] && [ -f "$DAT" ]; then
  A_LAST=$(tail -n 1 "$DAT" | awk '{print $3}')
  if awk -v a="${A_LAST:-0}" 'BEGIN{exit !(a>=0.9995)}'; then
    echo "[$ID] solver exit $RC after full melt (alpha=$A_LAST) -> accepted"; RC=0
  fi
fi

mkdir -p "$SRC"
rm -rf "$SRC/postProcessing"
cp -r postProcessing "$SRC"/ 2>/dev/null
cp log.* "$SRC"/
# keep the last written field for ParaView, drop the rest (disk)
LAST=$(ls -d [0-9]* 2>/dev/null | sort -g | tail -n 1)
[ -n "$LAST" ] && { mkdir -p "$SRC/last_time"; cp -r "$LAST" "$SRC/last_time/"; }
[ "$RC" -eq 0 ] && echo "[$ID] done (last time $LAST s)" || echo "[$ID] solver exit $RC"
[ "$RC" -eq 0 ] || exit 3
exit 0
