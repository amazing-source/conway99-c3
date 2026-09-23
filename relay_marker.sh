#!/bin/sh
# Host side: sh relay_marker.sh <runner container> <instance>
# Relay WITHOUT a new container: mark the instance FROM_SPLIT, kill only the runner's cube_q_inc.py process (the loop, PID 1, survives),
# release the claim and put the instance at the front of cubes/LIST.txt -> the same loop re-claims it at once with the current code.
c=$1; n=$2
touch cubes/$n/FROM_SPLIT
echo "$n $(tr ' ' '\n' < cubes/LIST.txt | grep -v -x "$n" | tr '\n' ' ')" > cubes/LIST.txt
rmdir cubes/iclaim_$n
docker exec $c sh -c 'for p in /proc/[0-9]*; do a=$(tr "\000" " " < $p/cmdline 2>/dev/null); case "$a" in *cube_q_inc.py*) kill ${p#/proc/};; esac; done'
