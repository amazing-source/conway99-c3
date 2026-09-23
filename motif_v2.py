"""Motif-level test (research, 2026-09-22): for a triangle graph F, do there exist 27 column supports s_Y (the B matrix) and a symmetric
C in {0,1,2}^{27x27} satisfying ONLY proved LINEAR consequences of Q^2+Q = 12I+6J, Q1 = 14*1 ?
  (G0)  sum_Y s_Y s_Y^T = G0 = 6I+6J-5F-F^2                       (triangle block)
  (TY)  sum_{Y != Z} C_YZ s_Y(i) = 6 - 3 s_Z(i) - (F s_Z)_i        (triangle x independent block)
  (row) sum_Y C_YZ = 14 - |s_Z| ;  (dbl) exactly two Y with C_YZ = 2
  (L1)  a double YZ has |s_Y cap s_Z| <= 4                          ((Q^2)_YZ = 4 when Q_YZ = 2)
  (C3)  three mutually double orbits have supports partitioning {0..5}   (Lemma B, triangle rows)
Quadratic terms in C are dropped, phases are ignored: UNSAT here => no C3 graph with this triangle graph F at all.
Symmetry breaking (sound): columns sorted by support code (all independent orbits are interchangeable at this level)."""
import json, sys, time, itertools
from multiprocessing import Pool

def run(args):
    mask, edges, secs = args
    from ortools.sat.python import cp_model
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
            inter = sum(AND(x[Y][i], x[Z][i]) for i in range(6))
            md.Add(inter <= 4).OnlyEnforceIf(w[Y, Z])                                            # (L1)
    for Z in range(n):
        oth = [Y for Y in range(n) if Y != Z]
        for i in range(6):
            rhs = 6 - 3 * x[Z][i] - sum(F[i][k] * x[Z][k] for k in range(6))
            md.Add(sum(AND(x[Y][i], u[Y, Z]) + AND(x[Y][i], w[Y, Z]) for Y in oth) == rhs)      # (TY)
        md.Add(sum(u[Y, Z] + w[Y, Z] for Y in oth) == 14 - sum(x[Z]))                            # (row)
        md.Add(sum(w[Y, Z] for Y in oth) == 2)                                                   # (dbl)
    for a, b, c in itertools.combinations(range(n), 3):                                          # (C3)
        tri = md.NewBoolVar(""); md.AddBoolAnd([w[a, b], w[b, c], w[a, c]]).OnlyEnforceIf(tri)
        md.AddBoolOr([w[a, b].Not(), w[b, c].Not(), w[a, c].Not()]).OnlyEnforceIf(tri.Not())
        for i in range(6): md.Add(x[a][i] + x[b][i] + x[c][i] == 1).OnlyEnforceIf(tri)
    sv = cp_model.CpSolver(); sv.parameters.num_workers = 1; sv.parameters.max_time_in_seconds = secs
    t0 = time.time(); st = sv.StatusName(sv.Solve(md))
    sol = None
    if st in ("OPTIMAL", "FEASIBLE"):
        sol = ["".join(str(sv.Value(x[Y][i])) for i in range(6)) for Y in range(n)]
    return mask, len(edges), st, round(time.time() - t0, 1), sol

if __name__ == "__main__":
    secs = float(sys.argv[1]); W = int(sys.argv[2])
    agg = json.load(open("cpsat_aggregate_results.json"))
    motifs = [(r["mask"], r["edges"], secs) for r in agg if r["plain"]["result"] == "witness"]
    motifs.sort(key=lambda m: -len(m[1]))
    out = {}
    with Pool(W) as p:
        for mask, ne, st, dt, sol in p.imap_unordered(run, motifs):
            out[mask] = {"edges": ne, "status": st, "sec": dt, "supports": sol}
            print("motif %5d |E|=%d -> %-10s %6.1fs" % (mask, ne, st, dt), flush=True)
    json.dump(out, open("motif_v2_results.json", "w"), indent=1)
