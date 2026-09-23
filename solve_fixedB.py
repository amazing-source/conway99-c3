"""Decide one class by splitting on its level-2.5 multisets: for each multiset, B (with phases) is fixed and only the 27x27 block remains.
Column convention bridge: level-2 column (s,p) means (Z,b)~(i,b+p_i), i.e. (i,a)~(Z,a-p_i): full-model phase q_i = -p_i.
Columns are assigned to the independent orbits 6..32 in increasing full-model code (the same order used in solve_class.py), so the
assignment is canonical: any solution can be permuted/gauged into it (sound). Remaining freedom: only the 27x27 block.
Usage: python solve_fixedB.py <class> <enum_cap_s> <per_multiset_s> <workers>"""
import json, sys, time, itertools
from ortools.sat.python import cp_model
exec(open("level25.py", encoding="utf-8").read().split("def solve25")[0])
from full_model import Model, build_cpsat, solve_cnf

def multisets(cls, cap):
    edges = [tuple(e) for e in cls["edges"]]; eps = cls["eps"]
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
    sols = []
    class CB(cp_model.CpSolverSolutionCallback):
        def __init__(s): super().__init__()
        def on_solution_callback(s): sols.append({c: s.Value(m[c]) for c in allowed if s.Value(m[c])})
    sv = cp_model.CpSolver(); sv.parameters.enumerate_all_solutions = True; sv.parameters.num_workers = 1; sv.parameters.max_time_in_seconds = cap
    st = sv.Solve(md, CB())
    return sols, sv.StatusName(st) == "OPTIMAL"

def code_of(c):
    s, p = COLS[c]
    return sum((4 ** (5 - i)) * (((-p[i]) % 3) + 1) for i in range(6) if s[i])

def solve_with_B(cls, ms, secs, workers):
    types = ["T"] * 6 + ["I"] * 27; fixed = {}; E = {}
    for (i, j), e in zip(cls["edges"], cls["eps"]): E[(i, j)] = e % 3
    for i in range(6):
        for j in range(i + 1, 6):
            for p in range(3): fixed[(i, j, p)] = 1 if ((i, j) in E and E[(i, j)] == p) else 0
    cols = sorted([c for c, k in ms.items() for _ in range(k)], key=code_of)
    cols += [None] * (27 - len(cols))                       # zero columns (code 0) go first
    cols = sorted(cols, key=lambda c: -1 if c is None else code_of(c))
    for Y, c in zip(range(6, 33), cols):
        s, p = COLS[c] if c is not None else ((0,) * 6, (0,) * 6)
        for i in range(6):
            for q in range(3): fixed[(i, Y, q)] = 1 if (s[i] and q == (-p[i]) % 3) else 0
    M = Model(types, 14, fixed)
    t0 = time.time(); name, z = solve_cnf(M, secs)
    out = {"result": name, "solve_s": round(time.time() - t0, 1)}
    if name == "SAT":
        A, ok = M.lift(z); out["lift_verified"] = bool(ok)
        import numpy as np; np.savetxt("SOLUTION_%d_%d.txt" % (cls["mask"], int(time.time())), A, fmt="%d")
    return out

if __name__ == "__main__":
    classes = json.load(open("classes_reduced.json"))
    idx, cap, secs, workers = int(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4])
    cls = classes[idx]
    sols, complete = multisets(cls, cap)
    print("class %d mask %d eps %s: %d multisets (complete=%s)" % (idx, cls["mask"], cls["eps"], len(sols), complete), flush=True)
    res = []
    for n, ms in enumerate(sols):
        r = solve_with_B(cls, ms, secs, workers); res.append(r)
        print("  multiset %d: %s" % (n, json.dumps(r)), flush=True)
    json.dump({"class": idx, "mask": cls["mask"], "eps": cls["eps"], "n_multisets": len(sols), "enumeration_complete": complete, "results": res},
              open("fixedB_class%02d.json" % idx, "w"))
