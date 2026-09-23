#!/bin/sh
# usage (inside c99audit): sh stageq_long.sh <seconds> name1 name2 ...   -> stageQ_long/<name>.json, UNKNOWN recorded on timeout
T=$1; shift
for n in "$@"; do
  [ -f stageQ_long/$n.json ] && continue
  s=$(date +%s)
  timeout $T python run_one_q_long.py stageQ_runs/$n.in.json > stageQ_long/$n.out 2>&1
  rc=$?
  [ $rc -eq 124 ] && echo "{\"name\": \"$n\", \"result\": \"UNKNOWN\", \"sec\": $T}" > stageQ_long/$n.json
  echo "$n rc=$rc $(( $(date +%s) - s ))s $(grep -o '"result": "[A-Z]*"' stageQ_long/$n.json)" >> stageQ_long/progress.log
done
