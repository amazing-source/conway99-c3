"""Stage Q (x = 1) for one class: for every distinct SUPPORT multiset among its level-2.5 solutions, fix Q on the triangle block (2I+F)
and on the triangle/independent block (B = supports, columns sorted), leave the 27x27 block C free, and decide Q^2+Q = 12I+6J
(+ row sums 14, two doubles per independent row).  UNSAT for every support multiset  =>  the class is impossible.
Usage: python stageQ.py <class> <enum_cap_s> <solve_s>"""
import json, sys, time
exec(open("solve_fixedB.py", encoding="utf-8").read().split("def code_of")[0])
from quotient_model import QModel, solve_q, solve_q_lex
classes = json.load(open("classes_reduced.json")); idx, cap, secs = int(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
cls = classes[idx]
sols, complete = multisets(cls, cap)
supp = {}
for ms in sols:
    key = tuple(sorted([COLS[c][0] for c, k in ms.items() for _ in range(k)] + [(0,) * 6] * (27 - sum(ms.values()))))
    supp.setdefault(key, 0); supp[key] += 1
print("class %d mask %d: %d phased multisets (complete=%s) -> %d support multisets" % (idx, cls["mask"], len(sols), complete, len(supp)), flush=True)
F = {tuple(e) for e in cls["edges"]}
res = []
for n, key in enumerate(supp):
    types = ["T"] * 6 + ["I"] * 27; fixed = {}
    for i in range(6):
        for j in range(i + 1, 6): fixed[(i, j)] = int((i, j) in F)
    for Y, s in zip(range(6, 33), key):
        for i in range(6): fixed[(i, Y)] = s[i]
    groups = {}
    for Y, s_ in zip(range(6, 33), key): groups.setdefault(s_, []).append(Y)
    groups = [g for g in groups.values() if len(g) > 1]
    QM = QModel(types, 14, fixed); t0 = time.time(); r, Q = solve_q_lex(QM, groups, secs)
    out = {"support_multiset": n, "result": r, "sec": round(time.time() - t0, 1)}
    if r == "SAT":
        import numpy as np; Qa = np.array(Q)
        out["numeric_check"] = bool((Qa.sum(1) == 14).all() and np.array_equal(Qa @ Qa + Qa, 12 * np.eye(33, dtype=int) + 6))
        out["Q"] = Q
    res.append(out); print("  support multiset %d: %s %.1fs %s" % (n, r, out["sec"], out.get("numeric_check", "")), flush=True)
json.dump({"class": idx, "mask": cls["mask"], "eps": cls["eps"], "complete": complete, "results": res}, open("stageQ_class%02d.json" % idx, "w"))
