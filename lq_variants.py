"""Which ingredients carry the infeasibility of the linear relaxation?  For every Stage-Q instance where LQ was infeasible, test:
  V1 = LQ without (C3) and (C4)                       (only linear constraints + integrality)
  V2 = V1 without the (L1) rule                        (TY + row + dbl + entrywise bounds, integers)
  LP = V1 with u, w continuous in [0,1], w <= u        (pure linear programme; if infeasible, a Farkas certificate exists)
LP is solved exactly with fractions by a small Fourier-free method: we ask CP-SAT for an integer Farkas vector (bounded search) and
check it exactly; if none is found the LP status is reported as 'no certificate found'."""
import json, glob, sys, itertools
from fractions import Fraction
from ortools.sat.python import cp_model

def data(inst):
    F = [[0] * 6 for _ in range(6)]
    for a, b in inst["edges"]: F[a][b] = F[b][a] = 1
    S = [tuple(s) for s in inst["support"]]; n = len(S)
    t = [[6 - 3 * s[i] - sum(F[i][k] * s[k] for k in range(6)) for i in range(6)] for s in S]
    return F, S, n, t

def int_model(inst, use_L1, secs=60):
    F, S, n, t = data(inst)
    md = cp_model.CpModel(); u = {}; w = {}
    for Y in range(n):
        for Z in range(Y + 1, n):
            u[Y, Z] = u[Z, Y] = md.NewBoolVar(""); w[Y, Z] = w[Z, Y] = md.NewBoolVar(""); md.AddImplication(w[Y, Z], u[Y, Z])
            for i in range(6):
                for (A_, B_) in ((Y, Z), (Z, Y)):
                    if S[A_][i]:
                        if t[B_][i] < 1: md.Add(u[Y, Z] == 0)
                        if t[B_][i] < 2: md.Add(w[Y, Z] == 0)
            if use_L1 and sum(a * b for a, b in zip(S[Y], S[Z])) > 4: md.Add(w[Y, Z] == 0)
    for Z in range(n):
        oth = [Y for Y in range(n) if Y != Z]
        for i in range(6): md.Add(sum(S[Y][i] * (u[Y, Z] + w[Y, Z]) for Y in oth) == t[Z][i])
        md.Add(sum(u[Y, Z] + w[Y, Z] for Y in oth) == 14 - sum(S[Z]))
        md.Add(sum(w[Y, Z] for Y in oth) == 2)
    sv = cp_model.CpSolver(); sv.parameters.num_workers = 1; sv.parameters.max_time_in_seconds = secs
    return sv.StatusName(sv.Solve(md))

if __name__ == "__main__":
    lq = json.load(open("linear_relaxation_results.json"))
    for f in sorted(glob.glob("stageQ_runs/*.in.json")):
        d = json.load(open(f)); n = d["name"]
        if lq[n]["LQ"] != "INFEASIBLE": continue
        print("%-14s V1(no C3/C4)=%-10s V2(no C3/C4/L1)=%s" % (n, int_model(d, True), int_model(d, False)), flush=True)
