#!/bin/sh
# Run inside proofbox:  sh cert_check_bin.sh <name> <cadical_seconds>
# Like cert_check.sh but with a BINARY DRAT proof (2-3x smaller); aborts the proof if the disk would fall under 8 GB free.
n=$1; t=$2; b=certs/$n
start=$(date +%s)
cadical -q -t $t $b.cnf $b.drat > $b.cadical.log 2>&1 &
p=$!
while kill -0 $p 2>/dev/null; do
  free=$(df -k /w | awk 'NR==2 {print $4}')
  if [ "$free" -lt 8000000 ]; then kill $p; echo "$n ABORTED: disk under 8 GB free, proof size $(du -h $b.drat | cut -f1)"; rm -f $b.drat; exit 1; fi
  sleep 10
done
wait $p; rc=$?; mid=$(date +%s)
if [ $rc -eq 20 ]; then
  sz=$(du -h $b.drat | cut -f1)
  drat-trim $b.cnf $b.drat -t 40000 > $b.drat.log 2>&1; end=$(date +%s)
  v=$(tr -d '\015' < $b.drat.log | grep -c -x 's VERIFIED')
  echo "$n cadical=UNSAT solve=$((mid-start))s proof=$sz drat_trim=$( [ $v -ge 1 ] && echo VERIFIED || echo NOT_VERIFIED ) check=$((end-mid))s sha256(cnf)=$(sha256sum $b.cnf | cut -c1-16)"
  [ $v -ge 1 ] && rm -f $b.drat
else
  echo "$n cadical rc=$rc (10=SAT, 0=unknown/timeout) after $((mid-start))s"
fi
