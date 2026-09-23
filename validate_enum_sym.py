"""Validate enum_supports_sym.py against the complete (unbroken) enumerations of enum_supports_lq.py on the masks already finished:
the Aut(F)-orbits of the old complete list must be exactly the orbits of the new canonical list, one canonical element per orbit.
Usage: python validate_enum_sym.py mask1 mask2 ...  (reads enum_supports_lq_<m>.json and enum_supports_sym_<m>.json)"""
import json, sys
from enum_supports_sym import aut, img_code
agg = {r["mask"]: r for r in json.load(open("cpsat_aggregate_results.json"))}
def canon_counts(ms):             # multiset of codes as a sorted tuple
    return tuple(sorted(int(s, 2) for s in ms))
ok_all = True
suffix = "_tw" if "--twins" in sys.argv else ""
for m in [int(a) for a in sys.argv[1:] if not a.startswith("--")]:
    old = json.load(open("enum_supports_lq_%d.json" % m)); new = json.load(open("enum_supports_sym_%d%s.json" % (m, suffix)))
    G = aut([tuple(e) for e in agg[m]["edges"]])
    orbit = lambda ms: frozenset(tuple(sorted(img_code(v, p) for v in ms)) for p in G)
    O_old = set(orbit(canon_counts(ms)) for ms in old["supports"])
    O_new = [orbit(canon_counts(ms)) for ms in new["supports"]]
    good = old["complete"] and new["complete"] and set(O_new) == O_old and len(O_new) == len(set(O_new))
    print("mask %5d |Aut F|=%3d: old complete=%s %d multisets in %d orbits | new complete=%s %d canonical, distinct orbits %d -> %s"
          % (m, len(G), old["complete"], len(old["supports"]), len(O_old), new["complete"], len(new["supports"]), len(set(O_new)), "ok" if good else "MISMATCH"))
    ok_all &= good
print("ENUM_SYM VALIDATION:", "PASS" if ok_all else "FAIL")
