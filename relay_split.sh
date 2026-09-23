#!/bin/sh
# (inside c99audit) sh relay_split.sh <name> : finish an instance whose remaining cubes already failed passes 1-2 (straight to the split pass),
# then keep working as a normal incremental runner.  The instance's claim cubes/iclaim_<name> is kept by the caller.
n=$1
python -u cube_q_inc.py $n auto 5000 --from-split > cubes/$n/cube_inc_split.log 2>&1
echo "$(date '+%H:%M') $(tail -n 1 cubes/$n/cube_inc_split.log) runner=$(hostname) (split)" >> cubes/PROGRESS.txt
exec sh cube_runner_inc.sh 5000
