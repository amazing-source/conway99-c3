"""For each motif declared infeasible, search a small INTEGER Farkas certificate y for the system
   sum_s m_s * a(s) = b,  m_s >= 0,   a(s) = (1, [s_i s_j]_{i<=j}),  b = (27, [G0_ij]_{i<=j}).
Certificate: y with y.a(s) >= 0 for every s in {0,1}^6 and y.b < 0  =>  no real (a fortiori integer) solution.
The search uses CP-SAT; the certificate is then re-checked below in plain integer arithmetic (the only thing that matters)."""
import itertools, json
from ortools.sat.python import cp_model
res = json.load(open("cpsat_aggregate_results.json"))
pairs = [(i, j) for i in range(6) for j in range(i, 6)]
S = list(itertools.product((0, 1), repeat=6))
def g0(F):
    F2 = [[sum(F[i][k] * F[k][j] for k in range(6)) for j in range(6)] for i in range(6)]
    return [[6 * (i == j) + 6 - 5 * F[i][j] - F2[i][j] for j in range(6)] for i in range(6)]
out = []
for r in res:
    if r["plain"]["result"] == "witness": continue
    F = [[0] * 6 for _ in range(6)]
    for a, b in r["edges"]: F[a][b] = F[b][a] = 1
    G = g0(F); bvec = [27] + [G[i][j] for (i, j) in pairs]
    md = cp_model.CpModel(); B = 60
    y = [md.NewIntVar(-B, B, "y%d" % t) for t in range(len(bvec))]
    for s in S:
        a = [1] + [s[i] * s[j] for (i, j) in pairs]
        md.Add(sum(a[t] * y[t] for t in range(len(a))) >= 0)
    md.Add(sum(bvec[t] * y[t] for t in range(len(bvec))) <= -1)
    md.Minimize(sum(md.NewIntVar(0, B, "") for _ in []) + 0)
    sv = cp_model.CpSolver(); sv.parameters.num_workers = 1; sv.parameters.max_time_in_seconds = 30
    st = sv.Solve(md)
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        yv = [sv.Value(v) for v in y]
        # exact re-check
        ok = all(sum(([1] + [s[i] * s[j] for (i, j) in pairs])[t] * yv[t] for t in range(len(yv))) >= 0 for s in S)
        val = sum(bvec[t] * yv[t] for t in range(len(yv)))
        cert = {"y_total": yv[0], "y_pairs": {"%d%d" % p: yv[t + 1] for t, p in enumerate(pairs) if yv[t + 1]}, "y_dot_b": val, "checked": ok and val < 0}
    else:
        cert = {"none_found": sv.StatusName(st)}
    out.append({"mask": r["mask"], "edges": r["edges"], "G0": G, "certificate": cert})
    print(r["mask"], r["edges"], "->", cert)
json.dump(out, open("farkas_certificates.json", "w"), indent=1)
print("certified:", sum(1 for o in out if o["certificate"].get("checked")), "/", len(out))
