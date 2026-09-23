"""Level 2 for the C3 branch (x of order 3, fixed-point free, exactly 6 triangular orbits, 27 independent orbits).
For each surviving motif F (26) and each phase assignment on F's edges (modulo the gauge F3^6, i.e. only the cycle space):
  P    = 18x18 adjacency on the triangle vertices (i,a), a in F3: triangles (i,a)~(i,a+-1), matchings (i,a)~(j,a+eps_ij) on F-edges
  R    = 12 I + 2 J - P^2 - P  must equal  Y Y^T  (Y = adjacency of triangle vertices to the 81 independent vertices)
  -> R >= 0 entrywise (vertex-level lambda/mu), and R must decompose into 27 "phased columns":
     an independent orbit = (support s, phases p in F3^s up to a common shift); its 3 vertices contribute 1 to R[(i,0),(j,p_j-p_i)].
Exact IP: m_c >= 0 over the 1366 phased columns (incl. zero), sum m_c = 27, and for i<=j, k in F3:
     sum_{c: s_i=s_j=1, p_j-p_i=k} m_c = R[(i,0),(j,k)]      (diagonal i=j, k=0: row sums 12-deg_i)
Every condition is a necessary consequence of A^2+A = 12I+2J; nothing about the 27x27 independent block is used yet."""
import itertools, json, sys, time
from multiprocessing import Pool

def build_P(edges, eps):
    idx = lambda i, a: 3 * i + (a % 3)
    P = [[0] * 18 for _ in range(18)]
    for i in range(6):
        for a in range(3):
            for d in (1, 2): P[idx(i, a)][idx(i, a + d)] = 1
    for (i, j), e in zip(edges, eps):
        for a in range(3): P[idx(i, a)][idx(j, a + e)] = P[idx(j, a + e)][idx(i, a)] = 1
    return P

def residual(P):
    n = 18
    P2 = [[sum(P[u][w] * P[w][v] for w in range(n)) for v in range(n)] for u in range(n)]
    return [[12 * (u == v) + 2 - P2[u][v] - P[u][v] for v in range(n)] for u in range(n)]

def gauge_reps(edges):
    """phase assignments modulo gauge: fix eps = 0 on a spanning forest, free on the other edges."""
    parent = list(range(6))
    def find(x):
        while parent[x] != x: x = parent[x]
        return x
    tree = []
    for t, (i, j) in enumerate(edges):
        ri, rj = find(i), find(j)
        if ri != rj: parent[ri] = rj; tree.append(t)
    free = [t for t in range(len(edges)) if t not in tree]
    for vals in itertools.product(range(3), repeat=len(free)):
        eps = [0] * len(edges)
        for t, v in zip(free, vals): eps[t] = v
        yield eps

COLS = []   # (support tuple, phase tuple with p[first]=0)
for s in itertools.product((0, 1), repeat=6):
    sup = [i for i in range(6) if s[i]]
    if not sup: COLS.append((s, (0,) * 6)); continue
    for ph in itertools.product(range(3), repeat=len(sup) - 1):
        p = [0] * 6
        for i, v in zip(sup[1:], ph): p[i] = v
        COLS.append((s, tuple(p)))
assert len(COLS) == 1366

def solve_case(args):
    mask, edges, eps, tlimit = args
    from ortools.sat.python import cp_model
    P = build_P(edges, eps); R = residual(P)
    neg = [(u, v) for u in range(18) for v in range(18) if R[u][v] < 0]
    if neg:
        u, v = neg[0]
        return {"mask": mask, "eps": eps, "result": "R_negative", "cert": [u, v, R[u][v]]}
    # circulant sanity: R[(i,a),(j,b)] depends only on b-a
    for i in range(6):
        for j in range(6):
            for a in range(3):
                for b in range(3):
                    assert R[3*i+a][3*j+b] == R[3*i][3*j+(b-a) % 3]
    md = cp_model.CpModel()
    m = [md.NewIntVar(0, 27, "m%d" % c) for c in range(len(COLS))]
    md.Add(sum(m) == 27)
    rows = []
    for i in range(6):
        for j in range(i, 6):
            for k in (range(3) if i < j else (0,)):
                terms = [c for c, (s, p) in enumerate(COLS) if s[i] and s[j] and (p[j] - p[i]) % 3 == k]
                md.Add(sum(m[c] for c in terms) == R[3 * i][3 * j + k]); rows.append((i, j, k))
    sv = cp_model.CpSolver(); sv.parameters.num_workers = 1; sv.parameters.max_time_in_seconds = tlimit
    st = sv.Solve(md)
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        wit = {c: sv.Value(m[c]) for c in range(len(COLS)) if sv.Value(m[c])}
        # exact re-check against R
        tot = sum(wit.values()); ok = tot == 27
        for (i, j, k) in rows:
            val = sum(v for c, v in wit.items() if COLS[c][0][i] and COLS[c][0][j] and (COLS[c][1][j] - COLS[c][1][i]) % 3 == k)
            ok = ok and val == R[3 * i][3 * j + k]
        assert ok
        return {"mask": mask, "eps": eps, "result": "witness", "witness": {str(c): v for c, v in wit.items()}}
    name = "ip_infeasible_uncertified" if st == cp_model.INFEASIBLE else "unknown"
    return {"mask": mask, "eps": eps, "result": name}

if __name__ == "__main__":
    surv = [r for r in json.load(open("cpsat_aggregate_results.json")) if r["plain"]["result"] == "witness"]
    W = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    jobs = [(r["mask"], [tuple(e) for e in r["edges"]], eps, 60) for r in surv for eps in gauge_reps([tuple(e) for e in r["edges"]])]
    print("motifs:", len(surv), "phase classes (gauge-reduced):", len(jobs), "workers:", W, flush=True)
    out = []; t0 = time.time()
    with Pool(W) as pool:
        for r in pool.imap_unordered(solve_case, jobs, chunksize=4):
            out.append(r)
            if len(out) % 50 == 0: print("  done %d/%d  t=%.0fs" % (len(out), len(jobs), time.time() - t0), flush=True)
    json.dump(out, open("level2_results.json", "w"))
    from collections import Counter, defaultdict
    print("overall:", dict(Counter(r["result"] for r in out)))
    per = defaultdict(Counter)
    for r in out: per[r["mask"]][r["result"]] += 1
    for mk in sorted(per): print("  mask %5d: %s" % (mk, dict(per[mk])))
