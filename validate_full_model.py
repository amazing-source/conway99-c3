"""Validation of full_model.py on a REAL graph: the Berlekamp-van Lint-Seidel srg(243,22,1,2) (Cayley graph on F_3^5) with the
fixed-point-free order-3 automorphism x -> x + v.  v in S: every orbit is a triangle (81 'T'); v not in S: every orbit independent (81 'I').
Checks: planted assignment satisfies every generated constraint; lift passes the integer identity; a corrupted assignment is rejected."""
import itertools, sys, random
import numpy as np
sys.path.insert(0, "/repo/code/z2")
from control_bvls import bvls
from full_model import Model
A, V, ix, cols, neg = bvls()
S = set(cols) | set(neg(c) for c in cols)
add = lambda x, y: tuple((np.array(x) + np.array(y)) % 3)
def run(v, label):
    seen = set(); reps = []
    for x in V:
        if x in seen: continue
        orb = [x, add(x, v), add(add(x, v), v)]; seen.update(orb); reps.append(x)
    m = len(reps); types = []
    for r in reps:
        types.append("T" if A[ix[r], ix[add(r, v)]] else "I")
    z = {}
    for U in range(m):
        for W in range(U + 1, m):
            for psi in range(3):
                target = reps[W]
                for _ in range(psi): target = add(target, v)
                z[(U, W, psi)] = int(A[ix[reps[U]], ix[target]])
    M = Model(types, 22)
    bad = M.evaluate(z)
    Al, ok = M.lift(z)
    print("%s: %d orbits (%s), violated constraints on planted = %d, lift identity = %s" % (label, m, types[0], len(bad), ok))
    rnd = random.Random(1); keys = [k for k, val in z.items() if val]; kk = rnd.choice(keys)
    z2 = dict(z); z2[kk] = 0
    print("   corrupted (one edge-orbit removed): violated = %d (must be > 0)" % len(M.evaluate(z2)))
    return len(bad) == 0 and ok and len(M.evaluate(z2)) > 0
v_in = cols[0]
v_out = next(x for x in V if any(x) and x not in S)
r1 = run(v_in, "v in S (all triangles)"); r2 = run(v_out, "v not in S (all independent)")
print("FULL MODEL VALIDATION:", "PASS" if (r1 and r2) else "FAIL")
