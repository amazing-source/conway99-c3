"""Cross-check two independent pipelines, class by class (research 2026-09-23):
  OLD : complete phased-B enumeration (enum_all) -> Stage-Q instance files listing the class -> keep those not killed by LQ
        (linear_relaxation_results.json; the sparse sL/sP instances passed LQ by construction)
  NEW : enum_supports_phased.py (support model with LQ + level-2.5 phased columns in ONE CP-SAT model), complete list
The sets of support multisets must coincide for every class where both are complete.  Usage: python compare_phased_old.py"""
import json, glob
lq = json.load(open("linear_relaxation_results.json"))
old = {}
for f in glob.glob("stageQ_runs/*.in.json"):
    d = json.load(open(f))
    if lq.get(d["name"], {}).get("LQ") == "INFEASIBLE": continue
    ms = tuple(sorted("".join(map(str, s)) for s in d["support"]))
    for c in d.get("classes", []): old.setdefault(c, {})[ms] = d["name"]
agree = dis = 0
for f in sorted(glob.glob("enum_supports_phased_c*.json"), key=lambda s: int(s.split("_c")[1].split(".")[0])):
    r = json.load(open(f)); c = r["class"]
    if not r["complete"]: continue
    new = set(tuple(sorted(x)) for x in r["supports"]); o = set(old.get(c, {}))
    ok = new == o
    agree += ok; dis += not ok
    print("class %2d: new %3d | old %3d | common %3d -> %s%s" % (c, len(new), len(o), len(new & o), "same" if ok else "DIFFERENT",
          "" if ok else "  only new: %d, only old: %s" % (len(new - o), [old[c][m] for m in o - new])))
print("classes compared: %d, identical: %d, different: %d" % (agree + dis, agree, dis))
