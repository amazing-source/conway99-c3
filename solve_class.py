"""Solve the complete C3 problem for one (F, phase) class with CP-SAT, using the validated full_model.py.
Orbits 0..5 = triangles (T), 6..32 = independent (I). Triangle-triangle adjacencies are fixed by (F, eps): (i,a) ~ (j, a + eps_ij).
Symmetry breaking (sound):
  - gauge: for every independent Y, the smallest triangle adjacent to Y is joined with phase 0;
  - order: independent orbits sorted by the code  sum_i 4^(5-i) * (1 + phase of Y on T_i, or 0)  (non-decreasing).
Any SAT answer is lifted to a 99x99 matrix and checked with the integer identity A^2 + A - 12I = 2J.
Usage: python solve_class.py <class_index> <seconds> <workers>"""
import json, sys, time
from ortools.sat.python import cp_model
from full_model import Model, build_cpsat

def build(cls):
    types = ["T"] * 6 + ["I"] * 27
    fixed = {}
    E = {}
    for (i, j), e in zip(cls["edges"], cls["eps"]): E[(i, j)] = e % 3
    for i in range(6):
        for j in range(i + 1, 6):
            for p in range(3): fixed[(i, j, p)] = 1 if ((i, j) in E and E[(i, j)] == p) else 0
    M = Model(types, 14, fixed)
    md, var = build_cpsat(M)
    v = lambda key: var[key]
    # gauge fixing
    for Y in range(6, 33):
        for i in range(6):
            nz = [v((i, Y, q)) for q in (1, 2)]
            earlier = [v((j, Y, q)) for j in range(i) for q in range(3)]
            for x in nz: md.AddBoolOr(earlier + [x.Not()])
    # ordering of independent orbits
    codes = []
    for Y in range(6, 33):
        codes.append(sum((4 ** (5 - i)) * (q + 1) * v((i, Y, q)) for i in range(6) for q in range(3)))
    for a_, b_ in zip(codes, codes[1:]): md.Add(a_ <= b_)
    return M, md, var

if __name__ == "__main__":
    classes = json.load(open("classes_reduced.json"))
    idx, secs, workers = int(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3])
    cls = classes[idx]; t0 = time.time()
    M, md, var = build(cls)
    tb = time.time() - t0
    sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = secs; sv.parameters.num_workers = workers
    st = sv.Solve(md)
    name = {cp_model.OPTIMAL: "SAT", cp_model.FEASIBLE: "SAT", cp_model.INFEASIBLE: "UNSAT", cp_model.UNKNOWN: "UNKNOWN"}.get(st, str(st))
    out = {"class": idx, "mask": cls["mask"], "eps": cls["eps"], "result": name, "build_s": round(tb, 1), "solve_s": round(sv.WallTime(), 1),
           "conflicts": sv.NumConflicts(), "branches": sv.NumBranches(), "vars": len(var)}
    if name == "SAT":
        z = {k_: int(sv.Value(x)) for k_, x in var.items()}
        for U, V in M.pair_keys():
            for q in range(3):
                if (U, V, q) not in M.fixed and (U, V, q) not in z: z[(U, V, q)] = 0
        A, ok = M.lift(z); out["lift_verified"] = bool(ok)
        import numpy as np; np.savetxt("SOLUTION_class%d.txt" % idx, A, fmt="%d")
    print(json.dumps(out), flush=True)
    json.dump(out, open("full_class%02d.json" % idx, "w"))
