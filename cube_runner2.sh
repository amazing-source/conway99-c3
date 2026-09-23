#!/bin/sh
# Cube runner with a DYNAMIC queue (inside c99audit): sh cube_runner2.sh <seconds per cube>
# Re-reads cubes/LIST.txt after every instance, claims the first unclaimed name (atomic mkdir cubes/claim_<name>), solves all its cubes.
T=$1
mkdir -p cubes
while true; do
  n=""
  for x in $(cat cubes/LIST.txt); do mkdir cubes/claim_$x 2>/dev/null && { n=$x; break; }; done
  [ -z "$n" ] && break
  mkdir -p cubes/$n
  python -u cube_q.py $n auto $T 1 > cubes/$n/cube.log 2>&1
  echo "$(date '+%H:%M') $(tail -n 1 cubes/$n/cube.log) runner=$(hostname)" >> cubes/PROGRESS.txt
done
