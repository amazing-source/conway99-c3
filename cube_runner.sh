#!/bin/sh
# Cube runner (inside c99audit): sh cube_runner.sh <seconds per cube> name1 name2 ...
# Claims an instance with an atomic mkdir (cubes/claim_<name>), then solves all its cubes sequentially (cube_q.py, K=1).
T=$1; shift
mkdir -p cubes
for n in "$@"; do
  mkdir cubes/claim_$n 2>/dev/null || continue
  mkdir -p cubes/$n
  python -u cube_q.py $n auto $T 1 > cubes/$n/cube.log 2>&1
  echo "$(date '+%H:%M') $(tail -n 1 cubes/$n/cube.log) runner=$(hostname)" >> cubes/PROGRESS.txt
done
