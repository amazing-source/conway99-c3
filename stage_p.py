"""Stage P (research 2026-09-23): given a quotient matrix Q (a Stage-Q solution), decide whether phases exist, i.e. whether an actual
srg(3m, k, 1, 2) with a fixed-point-free order-3 automorphism has quotient Q.  Uses the validated vertex-level model full_model.Model
(constraints lambda = 1, mu = 2, degree k) + for every orbit pair: sum_psi z(U,V,psi) = Q_UV (pairs with Q_UV = 0 are fixed to 0).
Gauge: relabelling orbit V by a shift maps a solution to a solution, so along a BFS spanning tree of the support graph of Q we fix
z(U,V,0) = 1 if Q_UV = 1 and z(U,V,0) = 0 if Q_UV = 2 (the missing phase).  SAT -> lifted adjacency matrix checked exactly.
Usage: python stage_p.py <json with "types" and "Q"> <seconds>   or  python stage_p.py --selftest"""
import json, sys
from ortools.sat.python import cp_model
from full_model import Model, build_cpsat

def stage_p(types, Q, k, secs, workers=4):
    m = len(types); fixed = {}
    for U in range(m):
        for V in range(U + 1, m):
            if Q[U][V] == 0:
                for p in range(3): fixed[(U, V, p)] = 0
    M = Model(types, k, fixed); md, var = build_cpsat(M)
    for U in range(m):
        for V in range(U + 1, m):
            if Q[U][V] > 0: md.Add(sum(var[(U, V, p)] for p in range(3)) == Q[U][V])
    seen = {0}; frontier = [0]
    while frontier:                                            # BFS spanning tree, gauge fixing
        U = frontier.pop(0)
        for V in range(m):
            if V in seen or Q[U][V] == 0: continue
            a, b = min(U, V), max(U, V)
            md.Add(var[(a, b, 0)] == (1 if Q[U][V] == 1 else 0)); seen.add(V); frontier.append(V)
    sv = cp_model.CpSolver(); sv.parameters.num_workers = workers; sv.parameters.max_time_in_seconds = secs
    st = sv.StatusName(sv.Solve(md))
    if st in ("OPTIMAL", "FEASIBLE"):
        z = {key: sv.Value(x) for key, x in var.items()}
        A, ok = M.lift(z); return "SAT", ok, A
    return ("UNSAT" if st == "INFEASIBLE" else "UNKNOWN"), None, None

if __name__ == "__main__":
    if sys.argv[1] == "--selftest":
        rookT = [[2, 1, 1], [1, 2, 1], [1, 1, 2]]                 # rows of the 3x3 rook graph as triangle orbits
        rookI = [[0, 2, 2], [2, 0, 2], [2, 2, 0]]                 # diagonals as independent orbits
        for lab, types, Q, exp in (("rook T", ["T"] * 3, rookT, "SAT"), ("rook I", ["I"] * 3, rookI, "SAT"),
                                   ("corrupt T", ["T"] * 3, [[2, 1, 0], [1, 2, 1], [0, 1, 2]], "UNSAT")):
            r, ok, _ = stage_p(types, Q, 4, 30)
            print("%-10s %s lift_ok=%s -> %s" % (lab, r, ok, "ok" if r == exp and ok is not False else "WRONG"))
    else:
        d = json.load(open(sys.argv[1])); r, ok, A = stage_p(d["types"], d["Q"], 14, float(sys.argv[2]))
        print(json.dumps({"stage_p": r, "lift_ok": ok}))
        if r == "SAT": json.dump({"A": A.tolist()}, open(sys.argv[1].replace(".json", "_graph.json"), "w"))
