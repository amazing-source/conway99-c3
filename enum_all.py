"""Enumerate level-2.5 multisets for all 46 classes (cap per class), collect distinct (F, support multiset) Stage-Q instances."""
import json, sys, time
from multiprocessing import Pool
exec(open("solve_fixedB.py", encoding="utf-8").read().split("def code_of")[0])
def one(idx):
    cls = json.load(open("classes_reduced.json"))[idx]
    sols, complete = multisets(cls, float(sys.argv[1]))
    supp = sorted(set(tuple(sorted([COLS[c][0] for c, k in ms.items() for _ in range(k)] + [(0,) * 6] * (27 - sum(ms.values())))) for ms in sols))
    return idx, cls["mask"], len(sols), complete, supp
if __name__ == "__main__":
    out = []
    with Pool(8) as pool:
        for idx, mask, n, comp, supp in pool.imap_unordered(one, range(46)):
            out.append({"class": idx, "mask": mask, "n_phased": n, "complete": comp, "supports": [list(map(list, s)) for s in supp]})
            print("class %2d mask %5d: %6d phased multisets (complete=%s), %5d support multisets" % (idx, mask, n, comp, len(supp)), flush=True)
    json.dump(sorted(out, key=lambda r: r["class"]), open("enum_all.json", "w"))
    inst = {}
    for r in out:
        for s in r["supports"]: inst.setdefault((r["mask"], tuple(map(tuple, s))), []).append(r["class"])
    print("distinct Stage-Q instances (F, support multiset):", len(inst), "| all enumerations complete:", all(r["complete"] for r in out))
