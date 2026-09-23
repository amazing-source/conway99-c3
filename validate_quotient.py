"""Validate quotient_model.py: (1) the planted quotient of BvLS srg(243,22,1,2) under x->x+v (v in S: 81 'T'; v not in S: 81 'I')
satisfies every generated constraint and a corrupted one does not; (2) the CNF path on the 3x3 rook graph: SAT for k=4 (decoded Q
checked numerically), UNSAT for k=5."""
import sys, random
import numpy as np
sys.path.insert(0, "/repo/code/z2")
from control_bvls import bvls
from quotient_model import QModel, solve_q
A, V, ix, cols, neg = bvls(); S = set(cols) | set(neg(c) for c in cols)
add = lambda x, y: tuple((np.array(x) + np.array(y)) % 3)
def planted(v):
    seen = set(); reps = []
    for x in V:
        if x in seen: continue
        orb = [x, add(x, v), add(add(x, v), v)]; seen.update(orb); reps.append(orb)
    m = len(reps); types = ["T" if A[ix[o[0]], ix[o[1]]] else "I" for o in reps]
    Q = [[sum(A[ix[reps[U][0]], ix[y]] for y in reps[W]) for W in range(m)] for U in range(m)]
    return types, Q
ok_all = True
for v, label in ((cols[0], "81 T"), (next(x for x in V if any(x) and x not in S), "81 I")):
    types, Q = planted(v); M = QModel(types, 22)
    bad = M.evaluate(Q)
    Q2 = [r[:] for r in Q]; U = next(i for i in range(len(Q)) if types[i] == types[0]); W = next(j for j in range(len(Q)) if j != U and Q[U][j] == 1)
    Q2[U][W] = Q2[W][U] = 0
    print("BvLS %s: planted violations = %d, corrupted violations = %d" % (label, len(bad), len(M.evaluate(Q2))))
    ok_all &= (not bad) and len(M.evaluate(Q2)) > 0
for types in (["T"] * 3, ["I"] * 3):
    for k in (4, 5):
        M = QModel(types, k); r, Q = solve_q(M, 30)
        chk = None
        if r == "SAT":
            Qa = np.array(Q); chk = bool((Qa.sum(1) == k).all() and np.array_equal(Qa @ Qa + Qa, (k - 2) * np.eye(3, dtype=int) + 6))
        print("rook quotient %s k=%d: %s numeric_check=%s" % (types[0], k, r, chk))
        ok_all &= (r == "SAT" and chk) if k == 4 else (r == "UNSAT")
print("QUOTIENT MODEL VALIDATION:", "PASS" if ok_all else "FAIL")
