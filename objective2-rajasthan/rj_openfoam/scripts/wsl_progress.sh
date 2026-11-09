#!/bin/bash
# prints "<case> <time_s> <liquid_fraction>" of every running/finished case in ~/rj_runs; with a case name argument copies its postProcessing to cases/_live/
for d in $HOME/rj_runs/*/; do n=$(basename $d); f=$d/postProcessing/meltAndTemp/0/volFieldValue.dat; [ -f $f ] && echo "$n $(tail -1 $f | awk '{print $1, $3}')"; done
