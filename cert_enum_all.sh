#!/bin/sh
# (inside c3box) sh cert_enum_all.sh : certify every COMPLETE phased enumeration that is not certified yet, one class at a time
# (generation peak ~2.5 GB, then CaDiCaL + DRAT + drat-trim).  Re-scans every 5 min while the enumerations finish; stops after 2 h idle.
idle=0
while [ $idle -lt 24 ]; do
  did=0
  for c in $(seq 0 45); do
    j=enum_supports_phased_c$c.json
    [ -f $j ] || continue
    python -c "import json,sys; sys.exit(0 if json.load(open('$j')).get('complete') else 1)" || continue
    grep -q "^enum_c$c " certs/SUMMARY_ENUM.txt 2>/dev/null && continue
    [ -f certs/enum_c$c.gen.json ] && [ ! -f certs/enum_c$c.cnf ] && continue          # being certified elsewhere
    if [ ! -f certs/enum_c$c.gen.json ]; then
      python cert_enum.py gen $c >> certs_enum/gen.log 2>&1 && mv certs_enum/c$c.cnf certs/enum_c$c.cnf && cp certs_enum/c$c.gen.json certs/enum_c$c.gen.json || continue
    fi
    sh cert_check_bin.sh enum_c$c 40000 >> certs/SUMMARY_ENUM.txt 2>&1; did=1
  done
  if [ $did -eq 0 ]; then idle=$((idle+1)); sleep 300; else idle=0; fi
done
