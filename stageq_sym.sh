#!/bin/sh
# Solver worker (inside c99audit): sh stageq_sym.sh <seconds> name1 name2 ...
# Several workers share one list: an instance is claimed with an atomic mkdir, its CNF (full symmetry breaking) is produced by the single
# generator stageq_sym_gen.sh; the worker waits for it, solves with CaDiCaL (pysat, clauses streamed from disk, ~0.25-0.7 GB),
# decodes + exactly re-checks any SAT model.  No proof here: an UNSAT is re-run with a DRAT proof afterwards.  Progress: stageQ_sym/progress.log
T=$1; shift
mkdir -p stageQ_sym
for n in "$@"; do
  mkdir stageQ_sym/claim_$n 2>/dev/null || continue
  while [ ! -f stageQ_sym/$n.gen.json ]; do
    grep -q "^$n GEN_FAILED" stageQ_sym/progress.log 2>/dev/null && continue 2
    sleep 10
  done
  s=$(date +%s)
  timeout $T python solve_stream.py stageQ_sym/$n.cnf stageQ_sym/$n.log; rc=$?
  case $rc in 10) r=SAT; python stageq_sym.py decode $n >> stageQ_sym/progress.log 2>&1;; 20) r=UNSAT;; *) r=UNKNOWN;; esac
  echo "$n $r rc=$rc $(( $(date +%s) - s ))s worker=$(hostname)" | tee stageQ_sym/$n.res >> stageQ_sym/progress.log
  [ $rc -ne 10 ] && rm -f stageQ_sym/$n.cnf
done
