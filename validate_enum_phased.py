"""Validate enum_supports_phased.py on classes whose answer is known from the independent older pipeline
(complete phased enumeration enum_all -> Stage-Q instances, then linear_relaxation LQ; or enum_supports_lq + support_phase_check):
the set of multisets found must equal the expected set exactly, and the enumeration must be complete.
Usage: python validate_enum_phased.py   (reads enum_supports_phased_c<k>.json produced beforehand)"""
import json
lq = json.load(open("linear_relaxation_results.json"))
def ms(name): return tuple(sorted("".join(map(str, s)) for s in json.load(open("stageQ_runs/%s.in.json" % name))["support"]))
expected = {0: ["m16927_s0019", "m16927_s0020", "m16927_s0021", "m16927_s0022"], 30: ["m12295_s0015"], 15: ["m21041_s0025"],
            42: ["m00028_sL0"], 25: ["m08290_sL0"], 32: ["m09313_sL0"]}
ok_all = True
for c, names in expected.items():
    try: r = json.load(open("enum_supports_phased_c%d.json" % c))
    except FileNotFoundError: print("class %d: no result file" % c); ok_all = False; continue
    got = set(tuple(sorted(x)) for x in r["supports"]); exp = set(ms(n) for n in names)
    good = r["complete"] and got == exp
    print("class %2d: complete=%s found %d expected %d (%s) common %d -> %s" % (c, r["complete"], len(got), len(exp), ",".join(names), len(got & exp), "ok" if good else "MISMATCH"))
    ok_all &= good
print("ENUM_PHASED VALIDATION:", "PASS" if ok_all else "FAIL")
