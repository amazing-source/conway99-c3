"""Create Stage-Q instances m<mask>_sP<k> from a COMPLETE enum_supports_phased_c<class>.json, one per Aut(F)-orbit of support multisets
(Stage Q is invariant under Aut(F)), skipping orbits already covered by an existing instance file of the same mask.
Prints the new names (for the cube queue).  Usage: python make_phased_instances.py <class index>"""
import json, sys, glob
from enum_supports_sym import aut, img_code
idx = int(sys.argv[1]); r = json.load(open("enum_supports_phased_c%d.json" % idx)); assert r["complete"], "not complete"
cl = json.load(open("classes_reduced.json"))[idx]; mask = cl["mask"]; edges = [tuple(e) for e in cl["edges"]]
G = aut(edges)
canon = lambda codes: min(tuple(sorted(img_code(v, p) for v in codes)) for p in G)
existing = {}
for f in glob.glob("stageQ_runs/m%05d_*.in.json" % mask):
    d = json.load(open(f)); existing[canon([int("".join(map(str, s)), 2) for s in d["support"]])] = d["name"]
new, seen = [], {}
k = len(glob.glob("stageQ_runs/m%05d_sP*.in.json" % mask))
for ms in r["supports"]:
    c = canon([int(s, 2) for s in ms])
    if c in existing: seen.setdefault(c, existing[c]); continue
    if c in seen: continue
    name = "m%05d_sP%d" % (mask, k); k += 1
    d = {"name": name, "mask": mask, "edges": cl["edges"], "support": [[int(b) for b in format(v, "06b")] for v in c], "classes": [idx]}
    json.dump(d, open("stageQ_runs/%s.in.json" % name, "w")); seen[c] = name; new.append(name)
print("class %d mask %d: %d multisets -> %d Aut(F)-orbits (|Aut F| = %d); new instances %d, already existing %d"
      % (idx, mask, len(r["supports"]), len(seen), len(G), len(new), len(seen) - len(new)))
print("NEW", " ".join(new))
