"""LQB relaxation (research 2026-09-23): LQ (linear_relaxation.py) + for every pair of independent orbits i != j the exact inequality
obtained from (Q^2+Q)_ij = 6 by dropping ONLY the single-single common neighbours (the (S^2) term restricted to independent orbits):
    |s_i cap s_j| + s_ij + 2 w_ij + 2 * sum_k (s_ik w_kj + w_ik s_kj) + 4 * sum_k w_ik w_kj  <=  6
with C = s + 2w on the independent block (s = single indicator, w = double indicator, exclusive).  Relaxation of Stage Q:
UNSAT(LQB) => UNSAT(Stage Q).  (ibenarb's "layer B" budget, extended with the triangle supports.)"""
import json, glob, sys, itertools
from ortools.sat.python import cp_model

def solve(inst, secs):
    F = [[0] * 6 for _ in range(6)]
    for a, b in inst["edges"]: F[a][b] = F[b][a] = 1
    S = [tuple(x) for x in inst["support"]]; n = len(S)
    t = [[6 - 3 * s[i] - sum(F[i][k] * s[k] for k in range(6)) for i in range(6)] for s in S]
    md = cp_model.CpModel(); sg = {}; w = {}
    def AND(a, b):
        g = md.NewBoolVar(""); md.AddBoolAnd([a, b]).OnlyEnforceIf(g); md.AddBoolOr([a.Not(), b.Not()]).OnlyEnforceIf(g.Not()); return g
    for Y in range(n):
        for Z in range(Y + 1, n):
            sg[Y, Z] = sg[Z, Y] = md.NewBoolVar(""); w[Y, Z] = w[Z, Y] = md.NewBoolVar(""); md.AddBoolOr([sg[Y, Z].Not(), w[Y, Z].Not()])
            for i in range(6):
                for (A_, B_) in ((Y, Z), (Z, Y)):
                    if S[A_][i]:
                        if t[B_][i] < 1: md.Add(sg[Y, Z] + w[Y, Z] == 0)
                        if t[B_][i] < 2: md.Add(w[Y, Z] == 0)
    for Z in range(n):
        oth = [Y for Y in range(n) if Y != Z]
        for i in range(6): md.Add(sum(S[Y][i] * (sg[Y, Z] + 2 * w[Y, Z]) for Y in oth) == t[Z][i])   # (TY)
        md.Add(sum(sg[Y, Z] + 2 * w[Y, Z] for Y in oth) == 14 - sum(S[Z]))                            # (row)
        md.Add(sum(w[Y, Z] for Y in oth) == 2)                                                         # (dbl)
    for i, j in itertools.combinations(range(n), 2):                                                   # (B) budget
        inter = sum(a * b for a, b in zip(S[i], S[j]))
        terms = []
        for k in range(n):
            if k in (i, j): continue
            terms += [2 * AND(sg[i, k], w[k, j]), 2 * AND(w[i, k], sg[k, j]), 4 * AND(w[i, k], w[k, j])]
        md.Add(inter + sg[i, j] + 2 * w[i, j] + sum(terms) <= 6)
    for a, b, c in itertools.combinations(range(n), 3):                                                # (C3) Lemma B on triangle rows
        if not all(S[a][i] + S[b][i] + S[c][i] == 1 for i in range(6)):
            md.AddBoolOr([w[a, b].Not(), w[b, c].Not(), w[a, c].Not()])
    sv = cp_model.CpSolver(); sv.parameters.num_workers = 1; sv.parameters.max_time_in_seconds = secs
    return sv.StatusName(sv.Solve(md))

if __name__ == "__main__":
    secs = float(sys.argv[1]); names = sys.argv[2:]
    files = ["stageQ_runs/%s.in.json" % n for n in names] if names else sorted(glob.glob("stageQ_runs/*.in.json"))
    lq = json.load(open("linear_relaxation_results.json"))
    for f in files:
        d = json.load(open(f)); n = d["name"]
        if lq.get(n, {}).get("LQ") == "INFEASIBLE": continue
        print("%-14s LQB=%s" % (n, solve(d, secs)), flush=True)
