"""Count the level-2.5 solutions (multisets of 27 phased columns) of one class, with a time cap."""
import json, sys, time, itertools
from ortools.sat.python import cp_model
exec(open("level25.py", encoding="utf-8").read().split("def solve25")[0])
classes = json.load(open("classes_reduced.json")); idx = int(sys.argv[1]); cap = float(sys.argv[2])
cls = classes[idx]; edges = [tuple(e) for e in cls["edges"]]; eps = cls["eps"]
P = build_P(edges, eps); R = residual(P); e = eps_map(edges, eps)
allowed = [c for c, (s, p) in enumerate(COLS) if type_ok(s, p, e)]
md = cp_model.CpModel(); m = {c: md.NewIntVar(0, 27, "") for c in allowed}
md.Add(sum(m.values()) == 27)
for i in range(6):
    for j in range(i, 6):
        for k in (range(3) if i < j else (0,)):
            md.Add(sum(m[c] for c in allowed if COLS[c][0][i] and COLS[c][0][j] and (COLS[c][1][j] - COLS[c][1][i]) % 3 == k) == R[3 * i][3 * j + k])
for T in itertools.combinations(range(6), 3):
    i, j, l = T
    for r in itertools.product(range(3), repeat=2):
        terms = [m[c] for c in allowed if all(COLS[c][0][t] for t in T) and (COLS[c][1][j] - COLS[c][1][i]) % 3 == r[0] and (COLS[c][1][l] - COLS[c][1][i]) % 3 == r[1]]
        if terms: md.Add(sum(terms) <= 1)
class CB(cp_model.CpSolverSolutionCallback):
    def __init__(s): super().__init__(); s.n = 0
    def on_solution_callback(s): s.n += 1
sv = cp_model.CpSolver(); sv.parameters.enumerate_all_solutions = True; sv.parameters.num_workers = 1; sv.parameters.max_time_in_seconds = cap
cb = CB(); st = sv.Solve(md, cb)
print("class %d mask %d: allowed types %d, multisets found %d, status %s (complete enumeration iff OPTIMAL), %.0fs" % (idx, cls["mask"], len(allowed), cb.n, sv.StatusName(st), sv.WallTime()))
