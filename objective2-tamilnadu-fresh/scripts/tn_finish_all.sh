#!/usr/bin/env bash
# scripts/tn_finish_all.sh
# ========================
# Waits for the in-flight g8_s2_doe children to finish, checks they really
# completed, then runs every remaining gate with the right concurrency.
#
# Why a wait-then-run script: the DOE processes were launched by a launcher
# that had already imported the OLD tn_run_all (11 workers, g9_s6_grid as a
# 9-way "pair" stage). The launcher was stopped so the fixes take effect, but
# its children were left to finish rather than thrown away. This picks up from
# there.
set -u
cd "$(dirname "$0")/.."

# wmic is absent on this box; Get-CimInstance is the thing that reports
# command lines reliably here, so the poll goes through powershell.
doe_running() {
  powershell -NoProfile -Command \
    "(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { \$_.CommandLine -like '*g8_s2_doe*' }).Count" \
    2>/dev/null | tr -d '[:space:]'
}

echo "=== waiting for g8_s2_doe children ==="
while :; do
  n=$(doe_running)
  [ -z "$n" ] && n=0
  [ "$n" -eq 0 ] && break
  echo "  $n DOE job(s) still running  [$(date +%H:%M:%S)]"
  sleep 60
done
echo "=== DOE children done ==="

echo "=== DOE completeness (want 128 rows each) ==="
incomplete=0
for f in results/g8_s2_r*_p*.csv; do
  rows=$(( $(wc -l < "$f") - 1 ))
  printf "  %-20s %3d rows\n" "$(basename "$f")" "$rows"
  [ "$rows" -lt 128 ] && incomplete=$((incomplete+1))
done
if [ "$incomplete" -gt 0 ]; then
  echo "  $incomplete group(s) short of 128 -- topping them up (resume skips finished designs)"
  for c in 0 1 2; do for p in 1 2 3; do
    rows=$(( $(wc -l < "results/g8_s2_r${c}_p${p}.csv") - 1 ))
    [ "$rows" -lt 128 ] && echo "    resume r${c}_p${p} ($rows/128)" && \
      python scripts/g8_s2_doe.py "$c" "$p" >> "results/_log_g8_s2_doe_${c}_${p}.log" 2>&1 &
  done; done
  wait
  echo "  top-up complete"
fi

echo
echo "=== remaining gates, 4 workers ==="
python scripts/tn_run_all.py --from g8_s3_compare --keep-going --workers 4
rc=$?
echo "=== tn_run_all exited rc=$rc at $(date +%H:%M:%S) ==="
exit $rc
