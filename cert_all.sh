#!/bin/sh
# sequential DRAT certification of the Stage-Q UNSAT instances (one at a time, low memory)
for n in m29481_s0030 m29481_s0031 m05033_s0009 m05033_s0010 m05033_s0011 m06717_s0013 m16927_s0018; do
  MSYS_NO_PATHCONV=1 docker run --rm --cpus 1 -m 2g -v "$(pwd -W):/w" -w /w c99audit python cert_q.py stageQ_runs/$n.in.json 0 gen
  MSYS_NO_PATHCONV=1 docker run --rm --cpus 1 -m 3g -v "$(pwd -W):/w" -w /w proofbox sh cert_check.sh $n 1800
  rm -f certs/$n.cnf
done
echo ALL_DONE
