"""Consistency check between the LQ support enumeration (complete) and the older phased enumeration (possibly incomplete):
every older support multiset must either appear in the LQ list or fail LQ (checked with linear_relaxation.solve)."""
import json, sys
exec(open("linear_relaxation.py", encoding="utf-8").read().split("\nif __name__")[0])
mask = int(sys.argv[1])
lq = json.load(open("enum_supports_lq_%d.json" % mask)); agg = {r["mask"]: r for r in json.load(open("cpsat_aggregate_results.json"))}
new = set(tuple(sorted(s)) for s in lq["supports"])
old = set(tuple(sorted("".join(map(str, c)) for c in s)) for r in json.load(open("enum_all.json")) if r["mask"] == mask for s in r["supports"])
both = new & old; only_old = old - new; only_new = new - old
print("mask %d: LQ list %d (complete=%s) | old list %d | common %d | only old %d | only new %d" % (mask, len(new), lq["complete"], len(old), len(both), len(only_old), len(only_new)))
for s in only_old:
    inst = {"edges": agg[mask]["edges"], "support": [[int(c) for c in x] for x in s]}
    print("   old-only support: LQ ->", solve(inst, 60), "(must be INFEASIBLE)")
