#!/bin/sh
# Generator (inside c99audit): sh stageq_sym_gen.sh name1 name2 ...   one CNF at a time (transient ~1.3 GB), in priority order.
# Keeps at most 9 unsolved CNFs on disk (6 workers + 3 ahead) (disk + keeps RAM spikes rare).
mkdir -p stageQ_sym
for n in "$@"; do
  [ -f stageQ_sym/$n.gen.json ] && continue
  while [ $(ls stageQ_sym/*.cnf 2>/dev/null | grep -v _relaxed | wc -l) -ge 9 ]; do sleep 20; done
  python stageq_sym.py gen $n > stageQ_sym/$n.gen.log 2>&1 || echo "$n GEN_FAILED" >> stageQ_sym/progress.log
done
