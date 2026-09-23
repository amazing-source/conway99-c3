"""Validate the index conventions of phase_lnc.py on random structures (not SRGs): build a real 99-vertex adjacency matrix from random
(F, eps, phased columns, C with phases) through full_model.Model.adj, count common neighbours directly, and compare with
  (1) targets():  T(i,b) == (1 if (i,0)~(Z,b) else 2) - #common neighbours of (i,0),(Z,b) among TRIANGLE vertices
  (2) contrib():  #common neighbours among INDEPENDENT vertices == sum over neighbours Y and C-phases psi of contrib(s_Y,p_Y,psi)[i,b]."""
import random, json
import numpy as np
exec(open("phase_lnc.py", encoding="utf-8").read().split('if __name__')[0])
from full_model import Model
rng = random.Random(7)
motifs = [r for r in json.load(open("cpsat_aggregate_results.json")) if r["plain"]["result"] == "witness"]
bad1 = bad2 = checks = 0
for trial in range(30):
    edges = [tuple(x) for x in rng.choice(motifs)["edges"]]; eps = [rng.randrange(3) for _ in edges]; e = eps_map(edges, eps)
    types = ["T"] * 6 + ["I"] * 27; fixed = {}
    for i in range(6):
        for j in range(i + 1, 6):
            for q in range(3): fixed[(i, j, q)] = int((i, j) in e and e[(i, j)] == q)
    colidx = [rng.randrange(len(COLS)) for _ in range(27)]
    for k, c in enumerate(colidx):
        s, p = COLS[c]; Y = 6 + k
        for i in range(6):
            for q in range(3): fixed[(i, Y, q)] = int(bool(s[i]) and q == (-p[i]) % 3)   # (Y,b)~(i,b+p_i)  <=>  (i,a)~(Y,a-p_i)
    z = {}
    for Y in range(6, 33):
        for Zz in range(Y + 1, 33):
            k_ = rng.choice([0, 0, 1, 2]); ps = rng.sample(range(3), k_)
            for q in range(3): z[(Y, Zz, q)] = int(q in ps)
    M = Model(types, 14, fixed); A, _ = M.lift(z)
    V = lambda U, a: 3 * U + a
    for k, c in enumerate(colidx):
        Zo = 6 + k; sZ, pZ = COLS[c]; T = targets(sZ, pZ, e)
        for i in range(6):
            for b in range(3):
                u, v = V(i, 0), V(Zo, b)
                tri = sum(A[u, w] * A[v, w] for w in range(18)); ind = sum(A[u, w] * A[v, w] for w in range(18, 99))
                checks += 1
                if T[3 * i + b] != (1 if A[u, v] else 2) - tri: bad1 += 1
                pred = 0
                for k2, c2 in enumerate(colidx):
                    Yo = 6 + k2
                    if Yo == Zo: continue
                    s2, p2 = COLS[c2]
                    for q in range(3):
                        # psi such that (Y,c)~(Z,c+psi)
                        if Yo < Zo and z[(Yo, Zo, q)]: pred += contrib(s2, p2, q)[3 * i + b]
                        if Zo < Yo and z[(Zo, Yo, q)]: pred += contrib(s2, p2, (-q) % 3)[3 * i + b]
                if pred != ind: bad2 += 1
print("checks: %d ; target-formula mismatches: %d ; contribution-formula mismatches: %d" % (checks, bad1, bad2))
print("PHASE-LNC CONVENTIONS:", "PASS" if bad1 == 0 and bad2 == 0 else "FAIL")
