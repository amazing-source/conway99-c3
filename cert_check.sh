#!/bin/sh
# Run inside proofbox:  sh cert_check.sh <name> <cadical_seconds>
# Solves certs/<name>.cnf with native CaDiCaL (DRAT proof, text format), then checks the proof with drat-trim.
n=$1; t=$2; b=certs/$n
start=$(date +%s); cadical -q --no-binary -t $t $b.cnf $b.drat > $b.cadical.log 2>&1; rc=$?; mid=$(date +%s)
if [ $rc -eq 20 ]; then
  drat-trim $b.cnf $b.drat -t 40000 > $b.drat.log 2>&1; end=$(date +%s)
  # drat-trim prints its progress with carriage returns: strip them, then match the whole line exactly
  v=$(tr -d '\015' < $b.drat.log | grep -c -x 's VERIFIED')
  echo "$n cadical=UNSAT solve=$((mid-start))s drat_trim=$( [ $v -ge 1 ] && echo VERIFIED || echo NOT_VERIFIED ) check=$((end-mid))s sha256(cnf)=$(sha256sum $b.cnf | cut -c1-16)"
  [ $v -ge 1 ] && rm -f $b.drat
else
  echo "$n cadical rc=$rc (10=SAT, 0=unknown/timeout) after $((mid-start))s"
fi
