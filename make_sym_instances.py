"""Create Stage-Q instances m<mask>_sS<k> from a COMPLETE canonical (Aut(F)-reduced) support enumeration enum_supports_sym_<mask>.json,
then run the phase check on every Aut(F)-image of each multiset (a representative is DEAD only if no class realizes any image).
Prints one verdict line per instance; writes the list of live instances to stageQ_sym/NEW_<mask>.txt.
Usage: python make_sym_instances.py <mask>"""
import json, sys
from collections import Counter
from enum_supports_sym import aut, img_code
from support_phase_check import realizable
mask = int(sys.argv[1])
agg = {r["mask"]: r for r in json.load(open("cpsat_aggregate_results.json"))}
classes = json.load(open("classes_reduced.json"))
cls_idx = [i for i, c in enumerate(classes) if c["mask"] == mask]
en = json.load(open("enum_supports_sym_%d.json" % mask)); assert en["complete"], "enumeration not complete"
edges = [tuple(e) for e in agg[mask]["edges"]]; G = aut(edges)
live = []
for k, sup in enumerate(sorted(en["supports"])):
    codes = sorted(int(s, 2) for s in sup)
    name = "m%05d_sS%d" % (mask, k)
    d = {"name": name, "mask": mask, "edges": agg[mask]["edges"], "support": [[int(c) for c in format(v, "06b")] for v in codes], "classes": cls_idx}
    json.dump(d, open("stageQ_runs/%s.in.json" % name, "w"))
    images = sorted(set(tuple(sorted(img_code(v, p) for v in codes)) for p in G))
    verdict = "DEAD"; seen_unknown = False
    for img in images:
        counts = Counter(tuple(int(c) for c in format(v, "06b")) for v in img)
        for i in cls_idx:
            r = realizable([tuple(x) for x in classes[i]["edges"]], classes[i]["eps"], counts)
            if r is True: verdict = "REALIZABLE (class %d)" % i; break
            if r is None: seen_unknown = True
        if verdict != "DEAD": break
    if verdict == "DEAD" and seen_unknown: verdict = "UNKNOWN"
    print("%-12s images %3d, classes %s -> %s" % (name, len(images), cls_idx, verdict), flush=True)
    if verdict != "DEAD": live.append(name)
open("stageQ_sym/NEW_%d.txt" % mask, "w").write(" ".join(live) + "\n"); print("live:", live)
