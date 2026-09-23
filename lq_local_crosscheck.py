"""Independent cross-check of lq_local.py (exhaustive DP) with a per-row CP-SAT model written separately.
For each Stage-Q instance: every row flagged infeasible by lq_local must be INFEASIBLE here; every other row must be FEASIBLE here."""
import json, glob
from ortools.sat.python import cp_model
bad_rows = json.load(open("lq_local_results.json"))
agree = disagree = 0
for f in sorted(glob.glob("stageQ_runs/*.in.json")):
    d = json.load(open(f)); name = d["name"]; F = [[0] * 6 for _ in range(6)]
    for a, b in d["edges"]: F[a][b] = F[b][a] = 1
    S = [tuple(s) for s in d["support"]]; n = len(S)
    t = [[6 - 3 * s[i] - sum(F[i][k] * s[k] for k in range(6)) for i in range(6)] for s in S]
    for Z in range(n):
        md = cp_model.CpModel(); c = {}; two = {}
        for Y in range(n):
            if Y == Z: continue
            c[Y] = md.NewIntVar(0, 2, ""); two[Y] = md.NewBoolVar("")
            md.Add(c[Y] == 2).OnlyEnforceIf(two[Y]); md.Add(c[Y] <= 1).OnlyEnforceIf(two[Y].Not())
        for i in range(6): md.Add(sum(S[Y][i] * c[Y] for Y in c) == t[Z][i])
        md.Add(sum(c.values()) == 14 - sum(S[Z])); md.Add(sum(two.values()) == 2)
        sv = cp_model.CpSolver(); sv.parameters.num_workers = 1; sv.parameters.max_time_in_seconds = 60
        st = sv.Solve(md); feasible = st in (cp_model.OPTIMAL, cp_model.FEASIBLE)
        assert st != cp_model.UNKNOWN
        flagged = Z in bad_rows[name]
        if feasible != flagged: agree += 1
        else:
            disagree += 1; print("DISAGREE", name, Z, "flagged" if flagged else "not flagged", "cp-sat feasible" if feasible else "cp-sat infeasible")
print("rows checked: %d ; agreements: %d ; disagreements: %d" % (agree + disagree, agree, disagree))
