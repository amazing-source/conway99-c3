"""Validate lean_encoding.py.
(1) tot_equals, exhaustive: n <= 8, every r in [-1, n+1], every assignment of the n literals: CNF + assumptions SAT  <=>  sum == r.
(2) build_cnf_lean vs build_cnf on the real BvLS srg(243,22,1,2) quotients (81 'T' / 81 'I'): with a band of rows left free and the rest
    fixed to the planted values, both encodings SAT and the decoded Q passes QModel.evaluate; with one fixed entry corrupted, both UNSAT.
(3) rook 3x3 quotients: k=4 SAT (numeric check), k=5 UNSAT, with the lean encoding.
(4) Stage-Q instances: certified-UNSAT m05033_s0009 and m29481_s0030 -> UNSAT; SAT control (m23221_s0027 with the independent x independent
    Gram equations dropped) -> SAT.  Also reports clause counts old vs lean."""
import sys, itertools, random, json, time
import numpy as np
sys.path.insert(0, "/repo/code/z2")
from pysat.formula import IDPool
from pysat.solvers import Solver
from quotient_model import QModel
from lean_encoding import tot_equals, build_cnf_lean
ok_all = True

# (1)
bad = 0; tests = 0
for n in range(1, 9):
    for r in range(-1, n + 2):
        pool = IDPool(); lits = [pool.id(("x", i)) for i in range(n)]; cls = []
        tot_equals(lits, r, pool, cls)
        with Solver(name="cadical195", bootstrap_with=cls) as s:
            for bits in itertools.product((0, 1), repeat=n):
                tests += 1
                got = s.solve(assumptions=[l if b else -l for l, b in zip(lits, bits)])
                if got != (sum(bits) == r): bad += 1
print("(1) tot_equals exhaustive: %d assignments tested, %d wrong" % (tests, bad)); ok_all &= bad == 0

# (2)
from control_bvls import bvls
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
def solve_cls(cls):
    with Solver(name="cadical195", bootstrap_with=cls) as s:
        r = s.solve(); return r, (set(l for l in s.get_model() if l > 0) if r else None)
random.seed(1)
for v, label in ((cols[0], "81 T"), (next(x for x in V if any(x) and x not in S), "81 I")):
    types, Q = planted(v); m = len(Q)
    free_rows = set(random.sample(range(m), 6))
    fixed = {(a, b): Q[a][b] for a in range(m) for b in range(a + 1, m) if a not in free_rows and b not in free_rows}
    for corrupt in (False, True):
        fx = dict(fixed)
        if corrupt:
            a, b = next((a, b) for (a, b), val in fx.items() if val == 1); fx[(a, b)] = 0
        M = QModel(types, 22, fx); res = []
        for builder in ("old", "lean"):
            cls, pool = M.build_cnf() if builder == "old" else build_cnf_lean(M)
            r, mdl = solve_cls(cls)
            chk = (M.evaluate(M.decode(mdl, pool)) == []) if r else None
            res.append((builder, r, chk, len(cls)))
        exp = not corrupt
        good = all(r == exp and (chk is True if exp else True) for _, r, chk, _ in res)
        print("(2) BvLS %s %s: %s -> %s" % (label, "corrupted" if corrupt else "planted, 6 free rows", res, "ok" if good else "WRONG")); ok_all &= good

# (3)
for types in (["T"] * 3, ["I"] * 3):
    for k in (4, 5):
        M = QModel(types, k); cls, pool = build_cnf_lean(M); r, mdl = solve_cls(cls)
        chk = None
        if r:
            Qa = np.array(M.decode(mdl, pool)); chk = bool((Qa.sum(1) == k).all() and np.array_equal(Qa @ Qa + Qa, (k - 2) * np.eye(3, dtype=int) + 6))
        good = (r and chk) if k == 4 else (r is False)
        print("(3) rook %s k=%d lean: %s numeric=%s -> %s" % (types[0], k, r, chk, "ok" if good else "WRONG")); ok_all &= bool(good)

# (4)
import stageq_sym as SQ
def inst_model(name, relaxed):
    inst = json.load(open("stageQ_runs/%s.in.json" % name))
    F = {tuple(e) for e in inst["edges"]}; key = [tuple(s) for s in inst["support"]]
    types = ["T"] * 6 + ["I"] * 27; fixed = {}
    for i in range(6):
        for j in range(i + 1, 6): fixed[(i, j)] = int((i, j) in F)
    for Y, s in zip(range(6, 33), key):
        for i in range(6): fixed[(i, Y)] = s[i]
    M = QModel(types, 14, fixed)
    if relaxed:
        gen = M.constraints
        M.constraints = lambda: (c for c in gen() if not (c[0][0] == "gram" and c[0][1] >= 6 and c[0][2] >= 6 and c[0][1] != c[0][2]))
    return M, key
from quotient_model import add_lex_twins
for name, relaxed, exp in (("m05033_s0009", False, False), ("m29481_s0030", False, False), ("m23221_s0027", True, True)):
    M, key = inst_model(name, relaxed)
    n_old = len(M.build_cnf()[0])
    cls, pool = build_cnf_lean(M)
    groups = {}
    for Y, s in zip(range(6, 33), key): groups.setdefault(s, []).append(Y)
    add_lex_twins(M, cls, pool, [g for g in groups.values() if len(g) > 1])
    t0 = time.time(); r, mdl = solve_cls(cls)
    chk = (M.evaluate(M.decode(mdl, pool)) == []) if r else None
    good = (r == exp) and (chk is not False)
    print("(4) %s%s: clauses old %d / lean %d ; lean result %s (%.1fs) evaluate_ok=%s -> %s" % (name, " relaxed" if relaxed else "", n_old, len(cls), "SAT" if r else "UNSAT", time.time() - t0, chk, "ok" if good else "WRONG"), flush=True)
    ok_all &= good
print("LEAN ENCODING VALIDATION:", "PASS" if ok_all else "FAIL")
