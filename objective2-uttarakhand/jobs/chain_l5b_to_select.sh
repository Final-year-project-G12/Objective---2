#!/usr/bin/env bash
# Rebuild chain after L4/L5: surrogate comparison -> L6 search + L7 grid/band -> assessment -> selection funnel.
# The one-shot 2006-2010 test is NOT part of this chain (it is started by hand after the selection has been checked).
set -e
cd "$(dirname "$0")/.."
export PYTHONPATH=. PYTHONIOENCODING=utf-8
[ -f results/g8_s3_selection.csv ] || python scripts/g8_s3_compare.py > logs/g8_s3_compare.log 2>&1
python scripts/run_jobs.py jobs/l6_l7.txt --workers 3
python scripts/g9_assess.py > logs/g9_assess.log 2>&1
python scripts/run_jobs.py jobs/select.txt --workers 3
echo "chain finished $(date)"
