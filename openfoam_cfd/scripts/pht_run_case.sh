#!/usr/bin/env bash
# pht_run_case.sh <name> <generator args ...>
#   e.g. bash pht_run_case.sh nallusamy nallusamy --T-init 298
#        bash pht_run_case.sh raj_rt44_d060 rajasthan --pcm RT44HC --d 0.06 --n 30 --mdot 0.03 --dT 15
# Cases are built/run in ~/pht_runs/<name> (Linux disk); summary.json is copied to
# <repo>/cases_pht/<name>/.
SD="$(cd "$(dirname "$0")" && pwd)"
source /usr/lib/openfoam/openfoam2406/etc/bashrc >/dev/null 2>&1
source "$HOME/OpenFOAM/OpenFOAM-PHT53IACP/etc/bashrc"
NAME="$1"; shift
W="$HOME/pht_runs/$NAME"; rm -rf "$W"; mkdir -p "$W"
python3 "$SD/pht_make_case.py" "$@" --out "$W" > "$W/gen.log" 2>&1 || { cat "$W/gen.log"; exit 2; }
cd "$W"
blockMesh > log.blockMesh 2>&1 || { tail -20 log.blockMesh; exit 3; }
cp -r 0.orig 0
t0=$(date +%s)
porousHeatTransferFoam > log.solver 2>&1; rc=$?
echo "solver exit $rc, $(( $(date +%s) - t0 )) s"
[ $rc -eq 0 ] || { tail -25 log.solver; exit 4; }
python3 "$SD/pht_postprocess.py" "$W"
mkdir -p "$SD/../cases_pht/$NAME"
cp case_meta.json summary.json hourly_bed.csv log.solver gen.log "$SD/../cases_pht/$NAME/" 2>/dev/null
cp -r postProcessing "$SD/../cases_pht/$NAME/" 2>/dev/null
