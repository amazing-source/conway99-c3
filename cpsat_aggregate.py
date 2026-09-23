"""Aggregated incidence problem for the six triangular orbits (C3 branch), decided with CP-SAT (exact integer solver).
Witnesses are re-checked exactly; INFEASIBLE answers are solver claims (no proof certificate) and are labelled as such.
Same model as aggregate.py: m_s >= 0 (s in {0,1}^6), sum m_s = 27, sum m_s s s^T = G0 = 6I+6J-5F-F^2;
optional COL rule: 3 s_i + (F s)_i <= 6 for all i."""
import itertools, json, sys, time
from multiprocessing import Pool
from ortools.sat.python import cp_model

def g0(F):
    F2 = [[sum(F[i][k] * F[k][j] for k in range(6)) for j in range(6)] for i in range(6)]
    return [[6 * (i == j) + 6 - 5 * F[i][j] - F2[i][j] for j in range(6)] for i in range(6)]

def job(args):
    mask, edges, rule = args
    F = [[0] * 6 for _ in range(6)]
    for a, b in edges: F[a][b] = F[b][a] = 1
    G = g0(F)
    cols = [s for s in itertools.product((0, 1), repeat=6)
            if not (rule and any(3 * s[i] + sum(F[i][k] * s[k] for k in range(6)) > 6 for i in range(6)))]
    md = cp_model.CpModel(); m = {s: md.NewIntVar(0, 27, "m" + "".join(map(str, s))) for s in cols}
    md.Add(sum(m.values()) == 27)
    for i in range(6):
        for j in range(i, 6):
            md.Add(sum(m[s] for s in cols if s[i] and s[j]) == G[i][j])
    sv = cp_model.CpSolver(); sv.parameters.num_workers = 1; sv.parameters.max_time_in_seconds = 60
    t0 = time.time(); st = sv.Solve(md)
    name = {cp_model.OPTIMAL: "witness", cp_model.FEASIBLE: "witness", cp_model.INFEASIBLE: "cpsat_infeasible_uncertified"}.get(st, "unknown")
    wit = None
    if name == "witness":
        wit = {"".join(map(str, s)): sv.Value(m[s]) for s in cols if sv.Value(m[s])}
        S = [[0] * 6 for _ in range(6)]; tot = 0
        for key, mult in wit.items():
            s = [int(c) for c in key]; tot += mult
            for i in range(6):
                for j in range(6): S[i][j] += mult * s[i] * s[j]
        assert tot == 27 and S == G, "witness check failed"
        if rule:
            for key in wit:
                s = [int(c) for c in key]; assert all(3 * s[i] + sum(F[i][k] * s[k] for k in range(6)) <= 6 for i in range(6))
    return mask, rule, {"result": name, "witness": wit, "sec": round(time.time() - t0, 2)}

if __name__ == "__main__":
    cases = [c for c in json.load(open(sys.argv[1]))["cases"] if c["status"] == "psd"]
    jobs = [(c["mask"], c["edges"], rule) for c in cases for rule in (False, True)]
    rows = {c["mask"]: {"mask": c["mask"], "edges": c["edges"], "nullity": c["nullity"]} for c in cases}
    with Pool(3) as pool:
        for mask, rule, r in pool.imap_unordered(job, jobs):
            rows[mask]["col" if rule else "plain"] = r
            print("mask %6d %-5s -> %-30s %6.1fs" % (mask, "+COL" if rule else "plain", r["result"], r["sec"]), flush=True)
    out = [rows[c["mask"]] for c in cases]
    json.dump(out, open("cpsat_aggregate_results.json", "w"), indent=1)
    from collections import Counter
    print("plain:", dict(Counter(r["plain"]["result"] for r in out))); print("+COL :", dict(Counter(r["col"]["result"] for r in out)))
