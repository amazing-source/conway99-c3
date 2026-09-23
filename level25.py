"""Level 2.5: Level 2 (exact triangle-triangle residual decomposition) + two exact vertex-level conditions on the independent orbits.
Convention for a phased column (s,p) of an independent orbit Z:  (Z,b) ~ (i, b + p_i)  for i in s.
 (A) per-type filter (pair triangle vertex (i,0) / independent vertex (Z,b)): common neighbours inside the triangles must not exceed
     lambda=1 if adjacent, mu=2 otherwise:
       i in s  : #{j in N_F(i) cap s : b + p_j = e_ij} <= 1     ;  i not in s : that count <= 2      (for every b in F3)
 (B) triple condition (pair of independent vertices (Y,0), (Z,k) from different orbits): their common triangle neighbours are the
     i in s_Y cap s_Z with p^Y_i - p^Z_i = k; there are <= 2 of them. Equivalently: for every triple {i,j,l} and every relative phase
     pair r = (p_j - p_i, p_l - p_i), at most ONE independent orbit (counted with multiplicity) contains {i,j,l} with relative phases r.
Both are necessary consequences of A^2 + A = 12I + 2J; neither involves the unknown 27x27 block."""
import itertools, json, sys, time
from multiprocessing import Pool
exec(open("level2_phased.py", encoding="utf-8").read().split("def solve_case")[0])

def eps_map(edges, eps):
    e = {}
    for (i, j), v in zip(edges, eps): e[(i, j)] = v % 3; e[(j, i)] = (-v) % 3
    return e

def type_ok(s, p, e):
    for i in range(6):
        nb = [j for j in range(6) if (i, j) in e and s[j]]
        for b in range(3):
            cnt = sum(1 for j in nb if (b + p[j]) % 3 == e[(i, j)])
            if cnt > (1 if s[i] else 2): return False
    return True

def solve25(args):
    mask, edges, eps, tlimit = args
    from ortools.sat.python import cp_model
    P = build_P(edges, eps); R = residual(P)
    if any(R[u][v] < 0 for u in range(18) for v in range(18)): return {"mask": mask, "eps": eps, "result": "R_negative"}
    e = eps_map(edges, eps)
    allowed = [c for c, (s, p) in enumerate(COLS) if type_ok(s, p, e)]
    md = cp_model.CpModel(); m = {c: md.NewIntVar(0, 27, "m%d" % c) for c in allowed}
    md.Add(sum(m.values()) == 27)
    for i in range(6):
        for j in range(i, 6):
            for k in (range(3) if i < j else (0,)):
                md.Add(sum(m[c] for c in allowed if COLS[c][0][i] and COLS[c][0][j] and (COLS[c][1][j] - COLS[c][1][i]) % 3 == k) == R[3 * i][3 * j + k])
    for T in itertools.combinations(range(6), 3):
        i, j, l = T
        for r in itertools.product(range(3), repeat=2):
            terms = [m[c] for c in allowed if all(COLS[c][0][t] for t in T) and (COLS[c][1][j] - COLS[c][1][i]) % 3 == r[0] and (COLS[c][1][l] - COLS[c][1][i]) % 3 == r[1]]
            if len(terms) > 1 or terms: md.Add(sum(terms) <= 1)
    sv = cp_model.CpSolver(); sv.parameters.num_workers = 1; sv.parameters.max_time_in_seconds = tlimit
    st = sv.Solve(md)
    res = {cp_model.OPTIMAL: "witness", cp_model.FEASIBLE: "witness", cp_model.INFEASIBLE: "ip_infeasible_uncertified"}.get(st, "unknown")
    out = {"mask": mask, "eps": eps, "result": res, "n_allowed_types": len(allowed)}
    if res == "witness":
        wit = {c: sv.Value(v) for c, v in m.items() if sv.Value(v)}
        # exact re-check of all constraints
        assert sum(wit.values()) == 27
        for i in range(6):
            for j in range(i, 6):
                for k in (range(3) if i < j else (0,)):
                    assert sum(v for c, v in wit.items() if COLS[c][0][i] and COLS[c][0][j] and (COLS[c][1][j] - COLS[c][1][i]) % 3 == k) == R[3 * i][3 * j + k]
        cl = list(wit.items())
        for a in range(len(cl)):
            ca, ma = cl[a]; sa, pa = COLS[ca]
            for b in range(a, len(cl)):
                cb, mb = cl[b]; sb, pb = COLS[cb]
                if a == b and ma < 2: continue
                for k in range(3):
                    agree = sum(1 for t in range(6) if sa[t] and sb[t] and (pa[t] - pb[t]) % 3 == k)
                    assert agree <= 2, "triple condition violated"
        out["witness"] = {str(c): v for c, v in wit.items()}
    return out

if __name__ == "__main__":
    l2 = json.load(open("level2_results.json"))
    edges_of = {r["mask"]: [tuple(e) for e in r["edges"]] for r in json.load(open("cpsat_aggregate_results.json"))}
    jobs = [(r["mask"], edges_of[r["mask"]], r["eps"], 120) for r in l2 if r["result"] == "witness"]
    W = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    print("classes surviving level 2:", len(jobs), "workers:", W, flush=True)
    out = []; t0 = time.time()
    with Pool(W) as pool:
        for r in pool.imap_unordered(solve25, jobs):
            out.append(r)
            if len(out) % 10 == 0: print("  done %d/%d t=%.0fs" % (len(out), len(jobs), time.time() - t0), flush=True)
    json.dump(out, open("level25_results.json", "w"))
    from collections import Counter, defaultdict
    print("overall:", dict(Counter(r["result"] for r in out)))
    per = defaultdict(Counter)
    for r in out: per[r["mask"]][r["result"]] += 1
    for mk in sorted(per): print("  mask %5d: %s" % (mk, dict(per[mk])))
