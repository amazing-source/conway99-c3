#!/bin/sh
# Incremental cube runner (inside c99audit): sh cube_runner_inc.sh <conflict budget B>
# Dynamic queue cubes/LIST.txt, re-read after each instance; claim = atomic mkdir cubes/iclaim_<name>; cube_q_inc.py (one solver per
# instance, cubes under assumptions, budgets B, 10B, 100B; resumes from cubes/<name>/results.txt, retries UNKNOWN cubes).
B=$1
while true; do
  n=""
  for x in $(cat cubes/LIST.txt); do mkdir cubes/iclaim_$x 2>/dev/null && { n=$x; break; }; done
  [ -z "$n" ] && break
  mkdir -p cubes/$n
  python -u cube_q_inc.py $n auto $B > cubes/$n/cube_inc.log 2>&1
  echo "$(date '+%H:%M') $(tail -n 1 cubes/$n/cube_inc.log) runner=$(hostname)" >> cubes/PROGRESS.txt
done
