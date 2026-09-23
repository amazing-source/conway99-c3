"""Farkas certificate for 'support multiset not realizable by any phased B' (support_phase_check.py), research 2026-09-23.
System over real m_c >= 0 (c = allowed phased columns of the class):
   E1: sum_c m_c = 27 ;  E2: residual equalities R ;  E3: support counts = given multiset ;  I: triple constraints sum <= 1.
Farkas: find y (free, for equalities) and z >= 0 (for <=) with, for every column c:  y.A_eq[:,c] + z.A_le[:,c] >= 0,  and  y.b_eq + z.b_le < 0.
Then no real m >= 0 exists.  The vector is searched with CP-SAT (bounded integers) and re-checked here in exact integer arithmetic."""
import json, sys, itertools
from collections import Counter
from ortools.sat.python import cp_model
exec(open("level25.py", encoding="utf-8").read().split("def solve25")[0])

def system(edges, eps, counts):
    R = residual(build_P(edges, eps)); e = eps_map(edges, eps)
    allowed = [c for c, (s, p) in enumerate(COLS) if type_ok(s, p, e)]
    eq = []   # (coef dict over allowed cols, rhs)
    eq.append(({c: 1 for c in allowed}, 27))
    for i in range(6):
        for j in range(i, 6):
            for k in (range(3) if i < j else (0,)):
                eq.append(({c: 1 for c in allowed if COLS[c][0][i] and COLS[c][0][j] and (COLS[c][1][j] - COLS[c][1][i]) % 3 == k}, R[3 * i][3 * j + k]))
    sups = set(COLS[c][0] for c in allowed) | set(counts)
    for s in sups: eq.append(({c: 1 for c in allowed if COLS[c][0] == s}, counts.get(s, 0)))
    le = []
    for T in itertools.combinations(range(6), 3):
        i, j, l = T
        for r in itertools.product(range(3), repeat=2):
            cs = [c for c in allowed if all(COLS[c][0][t] for t in T) and (COLS[c][1][j] - COLS[c][1][i]) % 3 == r[0] and (COLS[c][1][l] - COLS[c][1][i]) % 3 == r[1]]
            if cs: le.append(({c: 1 for c in cs}, 1))
    return allowed, eq, le

def find(allowed, eq, le, B=40, secs=120):
    md = cp_model.CpModel()
    y = [md.NewIntVar(-B, B, "") for _ in eq]; z = [md.NewIntVar(0, B, "") for _ in le]
    for c in allowed:
        md.Add(sum(y[a] * eq[a][0].get(c, 0) for a in range(len(eq)) if c in eq[a][0]) +
               sum(z[b] * le[b][0].get(c, 0) for b in range(len(le)) if c in le[b][0]) >= 0)
    md.Add(sum(y[a] * eq[a][1] for a in range(len(eq))) + sum(z[b] * le[b][1] for b in range(len(le))) <= -1)
    sv = cp_model.CpSolver(); sv.parameters.num_workers = 1; sv.parameters.max_time_in_seconds = secs
    st = sv.Solve(md)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE): return None, sv.StatusName(st)
    return ([sv.Value(v) for v in y], [sv.Value(v) for v in z]), "found"

def check(allowed, eq, le, yv, zv):
    for c in allowed:
        if sum(yv[a] * eq[a][0].get(c, 0) for a in range(len(eq))) + sum(zv[b] * le[b][0].get(c, 0) for b in range(len(le))) < 0: return False
    return sum(yv[a] * eq[a][1] for a in range(len(eq))) + sum(zv[b] * le[b][1] for b in range(len(le))) < 0 and min(zv) >= 0

if __name__ == "__main__":
    classes = json.load(open("classes_reduced.json")); out = {}
    for name in sys.argv[1:]:
        d = json.load(open("stageQ_runs/%s.in.json" % name)); counts = Counter(tuple(s) for s in d["support"])
        for idx, cls in enumerate(classes):
            if cls["mask"] != d["mask"]: continue
            edges = [tuple(x) for x in cls["edges"]]
            R = residual(build_P(edges, cls["eps"]))
            if any(R[u][v] < 0 for u in range(18) for v in range(18)):
                print(name, "class", idx, ": residual negative (trivial certificate)"); continue
            allowed, eq, le = system(edges, cls["eps"], counts)
            cert, st = find(allowed, eq, le)
            ok = cert is not None and check(allowed, eq, le, *cert)
            print("%s class %d: Farkas %s, exact check %s" % (name, idx, st, ok), flush=True)
            out["%s_class%d" % (name, idx)] = {"status": st, "checked": ok, "y": cert[0] if cert else None, "z": cert[1] if cert else None}
    json.dump(out, open("farkas_phase_results.json", "w"))
