"""Solve ONE Stage-Q instance (F edges + support multiset) with twin lex symmetry breaking; no internal timeout (the caller kills it).
Writes stageQ_runs/<name>.json.  Usage: python run_one_q.py <instance_json_file>"""
import json, sys, time
import numpy as np
from quotient_model import QModel, add_lex_twins
from pysat.solvers import Solver
inst = json.load(open(sys.argv[1]))
F = {tuple(e) for e in inst["edges"]}; key = [tuple(s) for s in inst["support"]]
types = ["T"] * 6 + ["I"] * 27; fixed = {}
for i in range(6):
    for j in range(i + 1, 6): fixed[(i, j)] = int((i, j) in F)
for Y, s in zip(range(6, 33), key):
    for i in range(6): fixed[(i, Y)] = s[i]
groups = {}
for Y, s in zip(range(6, 33), key): groups.setdefault(s, []).append(Y)
groups = [g for g in groups.values() if len(g) > 1]
QM = QModel(types, 14, fixed); cls, pool = QM.build_cnf(); add_lex_twins(QM, cls, pool, groups)
t0 = time.time()
with Solver(name="cadical195", bootstrap_with=cls) as s:
    r = s.solve(); out = {"name": inst["name"], "result": "SAT" if r else "UNSAT", "sec": round(time.time() - t0, 1), "stats": s.accum_stats()}
    if r:
        Q = QM.decode(set(l for l in s.get_model() if l > 0), pool); Qa = np.array(Q)
        out["numeric_check"] = bool((Qa.sum(1) == 14).all() and np.array_equal(Qa @ Qa + Qa, 12 * np.eye(33, dtype=int) + 6))
        out["Q"] = Q
json.dump(out, open("stageQ_runs/%s.json" % inst["name"], "w"))
print(json.dumps({k: v for k, v in out.items() if k != "Q"}))
