"""Support-level projection enumeration for a triangle graph F (research 2026-09-23, aimed at the sparse classes).
Repeatedly solve the motif_v2 model (27 sorted supports + C with the proved linear constraints G0, TY, row, dbl, L1, C3) and after each
solution forbid its SUPPORT vector (sorted, hence canonical up to relabelling independent orbits).  Ends with:
  INFEASIBLE -> complete list of support multisets compatible with the linear content of Q^2+Q = 12I+6J  (then Stage Q on each);
  UNKNOWN    -> partial list (budget exhausted).
Usage: python enum_supports_lq.py <mask> <seconds per solve> <max solutions>"""
import json, sys, time, itertools
from ortools.sat.python import cp_model

def build(edges):
    F = [[0] * 6 for _ in range(6)]
    for a, b in edges: F[a][b] = F[b][a] = 1
    G0 = [[6 * (i == j) + 6 - 5 * F[i][j] - sum(F[i][k] * F[k][j] for k in range(6)) for j in range(6)] for i in range(6)]
    n = 27; md = cp_model.CpModel()
    x = [[md.NewBoolVar("") for i in range(6)] for Y in range(n)]
    def AND(a, b):
        g = md.NewBoolVar(""); md.AddBoolAnd([a, b]).OnlyEnforceIf(g); md.AddBoolOr([a.Not(), b.Not()]).OnlyEnforceIf(g.Not()); return g
    for i in range(6):
        for j in range(i, 6):
            md.Add(sum((x[Y][i] if i == j else AND(x[Y][i], x[Y][j])) for Y in range(n)) == G0[i][j])
    code = [sum((2 ** (5 - i)) * x[Y][i] for i in range(6)) for Y in range(n)]
    for Y in range(n - 1): md.Add(code[Y] <= code[Y + 1])
    u = {}; w = {}
    for Y in range(n):
        for Z in range(Y + 1, n):
            u[Y, Z] = u[Z, Y] = md.NewBoolVar(""); w[Y, Z] = w[Z, Y] = md.NewBoolVar(""); md.AddImplication(w[Y, Z], u[Y, Z])
            md.Add(sum(AND(x[Y][i], x[Z][i]) for i in range(6)) <= 4).OnlyEnforceIf(w[Y, Z])
    for Z in range(n):
        oth = [Y for Y in range(n) if Y != Z]
        for i in range(6):
            rhs = 6 - 3 * x[Z][i] - sum(F[i][k] * x[Z][k] for k in range(6))
            md.Add(sum(AND(x[Y][i], u[Y, Z]) + AND(x[Y][i], w[Y, Z]) for Y in oth) == rhs)
        md.Add(sum(u[Y, Z] + w[Y, Z] for Y in oth) == 14 - sum(x[Z]))
        md.Add(sum(w[Y, Z] for Y in oth) == 2)
    for a, b, c in itertools.combinations(range(n), 3):
        tri = md.NewBoolVar(""); md.AddBoolAnd([w[a, b], w[b, c], w[a, c]]).OnlyEnforceIf(tri)
        md.AddBoolOr([w[a, b].Not(), w[b, c].Not(), w[a, c].Not()]).OnlyEnforceIf(tri.Not())
        for i in range(6): md.Add(x[a][i] + x[b][i] + x[c][i] == 1).OnlyEnforceIf(tri)
    md.uw = (u, w, code)                                  # exposed for optional symmetry breaking (enum_supports_sym.py)
    return md, x

if __name__ == "__main__":
    mask, secs, cap = int(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3]); workers = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    agg = {r["mask"]: r for r in json.load(open("cpsat_aggregate_results.json"))}
    md, x = build([tuple(e) for e in agg[mask]["edges"]])
    found = []; status = "?"; t0 = time.time()
    while len(found) < cap:
        sv = cp_model.CpSolver(); sv.parameters.num_workers = workers; sv.parameters.max_time_in_seconds = secs
        st = sv.StatusName(sv.Solve(md))
        if st not in ("OPTIMAL", "FEASIBLE"): status = st; break
        vec = [[sv.Value(x[Y][i]) for i in range(6)] for Y in range(27)]
        found.append(["".join(map(str, r)) for r in vec])
        # block this support vector: at least one bit differs
        md.AddBoolOr([(x[Y][i].Not() if vec[Y][i] else x[Y][i]) for Y in range(27) for i in range(6)])
        print("mask %d: support multiset #%d found (%.0fs)" % (mask, len(found), time.time() - t0), flush=True)
    else:
        status = "CAP"
    print("mask %d: END status=%s, support multisets passing LQ: %d, complete=%s, %.0fs" % (mask, status, len(found), status == "INFEASIBLE", time.time() - t0), flush=True)
    json.dump({"mask": mask, "status": status, "complete": status == "INFEASIBLE", "supports": found}, open("enum_supports_lq_%d.json" % mask, "w"))
