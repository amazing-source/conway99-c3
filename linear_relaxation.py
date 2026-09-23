"""Linear relaxation LQ of a Stage-Q instance (research test, 2026-09-22).
Keeps only the LINEAR consequences of Q^2+Q = 12I+6J, Q1 = 14*1 involving the unknown block C (27x27, entries 0/1/2, symmetric):
  (TY) for every independent Z:  sum_Y C_YZ s_Y = t_Z := 6*1 - 3 s_Z - F s_Z        (triangle x independent block, exact)
  (row) sum_Y C_YZ = 14 - |s_Z| ;  (dbl) exactly two Y with C_YZ = 2               (Lemma entries (c))
plus consequences of the (independent x independent) block that stay linear once the doubles are known:
  (L1) a double YZ needs |s_Y cap s_Z| <= 4           ((Q^2)_YZ = 4 for Q_YZ = 2)
  (C4) no 4-cycle of doubles (ibenarb: 4 (L^2)_ij = 8 > 6)
  (C3) a triangle of doubles {a,b,c} needs supports partitioning the 6 triangles (Lemma B applied to triangle rows)
It drops all quadratic terms (C^2). UNSAT(LQ) => UNSAT(Stage Q). Solved with CP-SAT (exact integers)."""
import json, glob, sys, itertools
from ortools.sat.python import cp_model

def solve(inst, secs):
    F = [[0] * 6 for _ in range(6)]
    for a, b in inst["edges"]: F[a][b] = F[b][a] = 1
    S = [tuple(s) for s in inst["support"]]; n = len(S)
    t = [[6 - 3 * s[i] - sum(F[i][k] * s[k] for k in range(6)) for i in range(6)] for s in S]
    md = cp_model.CpModel(); u = {}; w = {}
    for Y in range(n):
        for Z in range(Y + 1, n):
            u[Y, Z] = u[Z, Y] = md.NewBoolVar(""); w[Y, Z] = w[Z, Y] = md.NewBoolVar("")
            md.AddImplication(w[Y, Z], u[Y, Z])
            # entrywise necessary: s_Y(i) * C_YZ <= t_Z(i) and symmetric
            for i in range(6):
                for (A_, B_) in ((Y, Z), (Z, Y)):
                    if S[A_][i]:
                        if t[B_][i] < 1: md.Add(u[Y, Z] == 0)
                        if t[B_][i] < 2: md.Add(w[Y, Z] == 0)
            if sum(a * b for a, b in zip(S[Y], S[Z])) > 4: md.Add(w[Y, Z] == 0)       # (L1)
    for Z in range(n):
        oth = [Y for Y in range(n) if Y != Z]
        for i in range(6):
            md.Add(sum(S[Y][i] * (u[Y, Z] + w[Y, Z]) for Y in oth) == t[Z][i])         # (TY)
        md.Add(sum(u[Y, Z] + w[Y, Z] for Y in oth) == 14 - sum(S[Z]))                    # (row)
        md.Add(sum(w[Y, Z] for Y in oth) == 2)                                           # (dbl)
    # (C3): a triangle of doubles must have supports partitioning {0..5}
    for a, b, c in itertools.combinations(range(n), 3):
        ok = all(S[a][i] + S[b][i] + S[c][i] == 1 for i in range(6))
        if not ok: md.AddBoolOr([w[a, b].Not(), w[b, c].Not(), w[a, c].Not()])
    # (C4): no 4-cycle of doubles, i.e. two orbits never share two double-neighbours
    for a, c in itertools.combinations(range(n), 2):
        both = []
        for b in range(n):
            if b in (a, c): continue
            x = md.NewBoolVar(""); md.AddBoolAnd([w[a, b], w[b, c]]).OnlyEnforceIf(x)
            md.AddBoolOr([w[a, b].Not(), w[b, c].Not()]).OnlyEnforceIf(x.Not()); both.append(x)
        md.Add(sum(both) <= 1)
    sv = cp_model.CpSolver(); sv.parameters.num_workers = 1; sv.parameters.max_time_in_seconds = secs
    return sv.StatusName(sv.Solve(md))

if __name__ == "__main__":
    secs = float(sys.argv[1]) if len(sys.argv) > 1 else 60
    out = {}
    for f in sorted(glob.glob("stageQ_runs/*.in.json")):
        d = json.load(open(f)); n = d["name"]
        r = solve(d, secs); stq = json.load(open(f.replace(".in.json", ".json")))["result"] if glob.glob(f.replace(".in.json", ".json")) else "not run"
        out[n] = {"LQ": r, "stageQ": stq}; print("%-14s LQ=%-10s stageQ=%s" % (n, r, stq), flush=True)
    json.dump(out, open("linear_relaxation_results.json", "w"), indent=1)
