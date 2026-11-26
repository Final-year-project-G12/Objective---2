#!/bin/bash
# Rajasthan rebuild chain L4-L7 (175 L/day plant). Stops at the first failing stage. Never runs the one-shot test.
cd "$(dirname "$0")"
export PATH="D:/Final Year Project/.venv/Scripts:$PATH"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONIOENCODING=utf-8 PYTHONUTF8=1
J=${JOBS:-4}
for s in screening doe surrogate optimize grid band assess select; do
  echo "$(date '+%F %T') START $s" >> logs/chain.txt
  python pipeline.py --state rajasthan --stage $s --jobs $J > logs/stage_$s.txt 2>&1 || { echo "$(date '+%F %T') FAILED $s" >> logs/chain.txt; exit 1; }
  echo "$(date '+%F %T') DONE $s" >> logs/chain.txt
done
echo "$(date '+%F %T') CHAIN COMPLETE" >> logs/chain.txt
