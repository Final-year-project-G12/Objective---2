#!/usr/bin/env bash
# Waits for all 12 search outputs (g9_points_r<c>_p<k>.csv), then runs the assessment and the selection funnel (3 workers).
cd "$(dirname "$0")/.."
export PYTHONPATH=. PYTHONIOENCODING=utf-8
until [ "$(ls results/g9_points_r[0-3]_p[1-3].csv 2>/dev/null | wc -l)" -eq 12 ]; do sleep 60; done
python scripts/g9_assess.py > logs/g9_assess.log 2>&1 || { echo "assess failed"; exit 1; }
python scripts/run_jobs.py jobs/select.txt --workers 3
echo "assess+select finished $(date)"
