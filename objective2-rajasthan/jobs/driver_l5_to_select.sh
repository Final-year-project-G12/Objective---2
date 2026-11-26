#!/usr/bin/env bash
cd "/d/Final Year Project/OBJECTIVE2/Objective---2/objective2-rajasthan"
export PYTHONPATH=. PYTHONIOENCODING=utf-8
until grep -q "^finished:" logs/run_l4_l5.log; do sleep 60; done
grep -q "finished: 0 failed" logs/run_l4_l5.log || { echo "L4/L5 had failures; chain not started" > logs/chain_status.txt; exit 1; }
python scripts/g8_s2_repair.py > logs/g8_s2_repair.log 2>&1
bash jobs/chain_l5b_to_select.sh > logs/chain_l5b_to_select.log 2>&1 && echo "chain finished $(date)" > logs/chain_status.txt || echo "chain FAILED $(date)" > logs/chain_status.txt
