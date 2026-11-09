#!/bin/bash
# copy postProcessing of a still-running (or killed) case from ~/rj_runs back to the project; optional 2nd arg "kill" stops its solver first
SRC="$1"; N=$(basename "$SRC")
[ "$2" = "kill" ] && pkill -f "buoyantPimpleFoam" -u $(id -u) --oldest 2>/dev/null
mkdir -p "$SRC/postProcessing"; cp -r $HOME/rj_runs/$N/postProcessing/. "$SRC/postProcessing/"
cp $HOME/rj_runs/$N/log.* "$SRC/" 2>/dev/null; echo copied $N
