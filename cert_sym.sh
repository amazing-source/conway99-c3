#!/bin/sh
# Host-side (Git Bash): certify Stage-Q UNSAT results of the symmetry pipeline.  For each name:
#   1. c99audit: regenerate the exact CNF (stageq_sym.py gen: lean encoding + twin lex + full sigma lex) -> certs/<name>_sym.cnf (+ sha in .gen.json)
#   2. proofbox: native CaDiCaL with DRAT proof + drat-trim (cert_check.sh) -> line appended to certs/SUMMARY_SYM.txt
# What is certified: the CNF is UNSAT.  Relied upon: lean encoding (validate_lean.py PASS), symmetry breaking (proof in NUIT_JOURNAL.md,
# validate_symlex.py PASS).  Usage: sh cert_sym.sh <cadical_seconds> name1 name2 ...
T=$1; shift
W="$(pwd -W)"
for n in "$@"; do
  MSYS_NO_PATHCONV=1 docker run --rm --cpus 1 -m 2g -v "$W:/w" -w /w c99audit sh -c "python stageq_sym.py gen $n > /dev/null && mv stageQ_sym/$n.cnf certs/${n}_sym.cnf && cp stageQ_sym/$n.gen.json certs/${n}_sym.gen.json" || { echo "$n GEN_FAILED" >> certs/SUMMARY_SYM.txt; continue; }
  MSYS_NO_PATHCONV=1 docker run --rm --cpus 1 -m 3g -v "$W:/w" -w /w proofbox sh cert_check_bin.sh ${n}_sym $T >> certs/SUMMARY_SYM.txt 2>&1
  tail -1 certs/SUMMARY_SYM.txt
done
