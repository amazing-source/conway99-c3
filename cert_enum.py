"""Certify the COMPLETENESS of a support enumeration (research 2026-09-23).
CP-SAT's final INFEASIBLE in enum_supports_phased.py is not certified (it comes from presolve with symmetry and dual reductions; CP-SAT's
own proof output covers none of it, tested).  Here the same model is re-encoded in pure CNF, with the multisets already found blocked;
CaDiCaL + DRAT + drat-trim then certify that no other multiset exists.  Model of class c (identical content to enum_supports_phased.py):
  x[Y][i]  support bits of the 27 independent orbits, sorted (x_Y <=lex x_{Y+1}, triangle 0 = most significant bit)
  G0       sum_Y x_Yi x_Yj = G0_ij                     u, w   C = u + w, w -> u (independent block)
  TY       sum_Y x_Yi C_YZ + 3 x_Zi + sum_k F_ik x_Zk = 6      row: sum_Y C_YZ + |x_Z| = 14      dbl: sum_Y w_YZ = 2
  L1       w_YZ -> sum_i x_Yi x_Zi <= 4                 C3: w_ab w_bc w_ac -> x_ai + x_bi + x_ci = 1 for all i
  phases   y[Y][c] one-hot over the columns allowed by the level-2.5 type filter, y[Y][c] -> x_Y = support(c);
           residual equalities sum_{Y,c} y = R[3i][3j+k];  triple condition sum <= 1 for every triple and relative phase pair
  symmetry orbits with equal support: column index nondecreasing (sound: swapping two such orbits maps solutions to solutions, C included)
Modes:  gen <class> [--unblock k]   -> certs_enum/c<class>[_u<k>].cnf + .gen.json   (--unblock k: leave found multiset k unblocked)
        check <class> [--unblock k] -> solve with pysat CaDiCaL; SAT models are decoded and checked by an independent evaluator."""
import json, sys, os, itertools, hashlib
from pysat.formula import IDPool
exec(open("level25.py", encoding="utf-8").read().split("def solve25")[0])        # COLS, build_P, residual, eps_map, type_ok
from lean_encoding import tot_equals, _node
from quotient_model import dedup

def atmost(lits, k, pool, cls, cond=None):
    """sum(lits) <= k, optionally only when literal cond is true."""
    lits = dedup(lits, pool, cls)
    if k >= len(lits): return
    if k < 0:
        if cond: cls.append([-cond])
        else: f = pool.id(("FALSE",)); cls.extend([[f], [-f]])
        return
    if k == 0:
        for l in lits: cls.append(([-cond] if cond else []) + [-l])
        return
    o = _node(lits, k + 1, pool, cls)
    cls.append(([-cond] if cond else []) + [-o[k]])

def build(cl, found, unblock=None):
    edges = [tuple(e) for e in cl["edges"]]; n = 27
    F = [[0] * 6 for _ in range(6)]
    for a, b in edges: F[a][b] = F[b][a] = 1
    G0 = [[6 * (i == j) + 6 - 5 * F[i][j] - sum(F[i][k] * F[k][j] for k in range(6)) for j in range(6)] for i in range(6)]
    pool = IDPool(); cls = []
    X = lambda Y, i: pool.id(("x", Y, i))
    U = lambda Y, Z: pool.id(("u", min(Y, Z), max(Y, Z)))
    W = lambda Y, Z: pool.id(("w", min(Y, Z), max(Y, Z)))
    def AND(a, b):
        k = ("and",) + tuple(sorted((a, b)))
        new = k not in pool.obj2id; g = pool.id(k)
        if new: cls.extend([[-g, a], [-g, b], [g, -a, -b]])
        return g
    for Y in range(n):
        for i in range(6): X(Y, i)
    for Y, Z in itertools.combinations(range(n), 2): cls.append([-W(Y, Z), U(Y, Z)])
    for i in range(6):                                                                   # G0
        for j in range(i, 6):
            tot_equals(dedup([X(Y, i) if i == j else AND(X(Y, i), X(Y, j)) for Y in range(n)], pool, cls), G0[i][j], pool, cls)
    for Y in range(n - 1):                                                               # sorted supports, x_Y <=lex x_{Y+1}
        e = pool.id(("lexeq", Y, 0)); cls.append([e])
        for i in range(6):
            a, b = X(Y, i), X(Y + 1, i)
            cls.append([-e, -a, b]); e2 = pool.id(("lexeq", Y, i + 1))
            cls.extend([[-e, a, b, e2], [-e, -a, -b, e2]]); e = e2
    for Z in range(n):
        oth = [Y for Y in range(n) if Y != Z]
        for i in range(6):                                                               # TY with the right-hand side moved left
            lits = [AND(X(Y, i), U(Y, Z)) for Y in oth] + [AND(X(Y, i), W(Y, Z)) for Y in oth] + [X(Z, i)] * 3 + [X(Z, k) for k in range(6) if F[i][k]]
            tot_equals(dedup(lits, pool, cls), 6, pool, cls)
        tot_equals(dedup([U(Y, Z) for Y in oth] + [W(Y, Z) for Y in oth] + [X(Z, i) for i in range(6)], pool, cls), 14, pool, cls)   # row
        tot_equals([W(Y, Z) for Y in oth], 2, pool, cls)                                 # dbl
    for Y, Z in itertools.combinations(range(n), 2):                                    # L1
        atmost([AND(X(Y, i), X(Z, i)) for i in range(6)], 4, pool, cls, cond=W(Y, Z))
    for a, b, c in itertools.combinations(range(n), 3):                                 # C3 (Lemma B on triangle rows)
        t = [-W(a, b), -W(b, c), -W(a, c)]
        for i in range(6):
            cls.append(t + [X(a, i), X(b, i), X(c, i)])
            for p, q in ((a, b), (b, c), (a, c)): cls.append(t + [-X(p, i), -X(q, i)])
    # phases
    R = residual(build_P(edges, cl["eps"]))
    if any(R[a][b] < 0 for a in range(18) for b in range(18)): cls.extend([[pool.id(("FALSE",))], [-pool.id(("FALSE",))]]); return cls, pool
    e = eps_map(edges, cl["eps"]); allowed = [c for c, (s, p) in enumerate(COLS) if type_ok(s, p, e)]
    Yv = lambda Y, c: pool.id(("y", Y, c))
    for Y in range(n):
        ys = [Yv(Y, c) for c in allowed]
        tot_equals(ys, 1, pool, cls)
        for c in allowed:
            for i in range(6): cls.append([-Yv(Y, c), X(Y, i) if COLS[c][0][i] else -X(Y, i)])
    for i in range(6):
        for j in range(i, 6):
            for k in (range(3) if i < j else (0,)):
                S = [c for c in allowed if COLS[c][0][i] and COLS[c][0][j] and (COLS[c][1][j] - COLS[c][1][i]) % 3 == k]
                tot_equals([Yv(Y, c) for Y in range(n) for c in S], R[3 * i][3 * j + k], pool, cls)
    for T in itertools.combinations(range(6), 3):
        i, j, l = T
        for r in itertools.product(range(3), repeat=2):
            S = [c for c in allowed if all(COLS[c][0][t] for t in T) and (COLS[c][1][j] - COLS[c][1][i]) % 3 == r[0] and (COLS[c][1][l] - COLS[c][1][i]) % 3 == r[1]]
            if S: atmost([Yv(Y, c) for Y in range(n) for c in S], 1, pool, cls)
    # symmetry: equal supports -> column index nondecreasing (prefix indicators o[Y][t] = "column index of Y >= allowed[t]")
    for Y in range(n - 1):
        eq = pool.id(("sameSupp", Y))
        for i in range(6): cls.extend([[-eq, -X(Y, i), X(Y + 1, i)], [-eq, X(Y, i), -X(Y + 1, i)]])
        cls.append([eq] + [pool.id(("diff", Y, i)) for i in range(6)])
        for i in range(6):
            d = pool.id(("diff", Y, i)); cls.extend([[-d, X(Y, i), X(Y + 1, i)], [-d, -X(Y, i), -X(Y + 1, i)]])
    O = lambda Y, t: pool.id(("pre", Y, t))
    for Y in range(n):
        for t in range(len(allowed)):
            cls.append([-Yv(Y, allowed[t]), O(Y, t)])
            if t > 0: cls.append([-O(Y, t), O(Y, t - 1)])
            cls.append([-O(Y, t), Yv(Y, allowed[t])] + ([O(Y, t + 1)] if t + 1 < len(allowed) else []))   # O(t) <-> y(t) or O(t+1)
    for Y in range(n - 1):
        for t in range(len(allowed)): cls.append([-pool.id(("sameSupp", Y)), -O(Y, t), O(Y + 1, t)])
    # block the multisets already found
    for k, ms in enumerate(found):
        if k == unblock: continue
        vec = sorted(ms)
        cls.append([(-X(Y, i) if vec[Y][i] == "1" else X(Y, i)) for Y in range(n) for i in range(6)])
    return cls, pool

def evaluate(cl, x, C, col):
    """independent check of a decoded solution against every constraint of the model; returns the list of violations."""
    edges = [tuple(e) for e in cl["edges"]]; n = 27; bad = []
    F = [[0] * 6 for _ in range(6)]
    for a, b in edges: F[a][b] = F[b][a] = 1
    G0 = [[6 * (i == j) + 6 - 5 * F[i][j] - sum(F[i][k] * F[k][j] for k in range(6)) for j in range(6)] for i in range(6)]
    for i in range(6):
        for j in range(6):
            if sum(x[Y][i] * x[Y][j] for Y in range(n)) != G0[i][j]: bad.append(("G0", i, j))
    if [tuple(r) for r in x] != sorted(tuple(r) for r in x): bad.append("unsorted")
    for Z in range(n):
        for i in range(6):
            if sum(x[Y][i] * C[Y][Z] for Y in range(n) if Y != Z) + 3 * x[Z][i] + sum(F[i][k] * x[Z][k] for k in range(6)) != 6: bad.append(("TY", Z, i))
        if sum(C[Y][Z] for Y in range(n) if Y != Z) + sum(x[Z]) != 14: bad.append(("row", Z))
        if sum(1 for Y in range(n) if Y != Z and C[Y][Z] == 2) != 2: bad.append(("dbl", Z))
    for Y, Z in itertools.combinations(range(n), 2):
        if C[Y][Z] == 2 and sum(a * b for a, b in zip(x[Y], x[Z])) > 4: bad.append(("L1", Y, Z))
    for a, b, c in itertools.combinations(range(n), 3):
        if C[a][b] == C[b][c] == C[a][c] == 2 and any(x[a][i] + x[b][i] + x[c][i] != 1 for i in range(6)): bad.append(("C3", a, b, c))
    e = eps_map(edges, cl["eps"]); R = residual(build_P(edges, cl["eps"]))
    for Y in range(n):
        s, p = COLS[col[Y]]
        if list(s) != list(x[Y]) or not type_ok(s, p, e): bad.append(("col", Y))
    for i in range(6):
        for j in range(i, 6):
            for k in (range(3) if i < j else (0,)):
                if sum(1 for Y in range(n) if COLS[col[Y]][0][i] and COLS[col[Y]][0][j] and (COLS[col[Y]][1][j] - COLS[col[Y]][1][i]) % 3 == k) != R[3 * i][3 * j + k]: bad.append(("R", i, j, k))
    for T in itertools.combinations(range(6), 3):
        i, j, l = T
        for r in itertools.product(range(3), repeat=2):
            if sum(1 for Y in range(n) if all(COLS[col[Y]][0][t] for t in T) and (COLS[col[Y]][1][j] - COLS[col[Y]][1][i]) % 3 == r[0] and (COLS[col[Y]][1][l] - COLS[col[Y]][1][i]) % 3 == r[1]) > 1: bad.append(("triple", T, r))
    return bad

if __name__ == "__main__":
    mode, idx = sys.argv[1], int(sys.argv[2]); unblock = int(sys.argv[sys.argv.index("--unblock") + 1]) if "--unblock" in sys.argv else None
    cl = json.load(open("classes_reduced.json"))[idx]
    en = json.load(open("enum_supports_phased_c%d.json" % idx)); found = en["supports"]
    cls, pool = build(cl, found, unblock)
    os.makedirs("certs_enum", exist_ok=True); base = "certs_enum/c%d%s" % (idx, "_u%d" % unblock if unblock is not None else "")
    nv = max(abs(l) for c in cls for l in c)
    if mode == "gen":
        with open(base + ".cnf", "w") as f:
            f.write("p cnf %d %d\n" % (nv, len(cls)))
            for c in cls: f.write(" ".join(map(str, c)) + " 0\n")
        sha = hashlib.sha256(open(base + ".cnf", "rb").read()).hexdigest()
        json.dump({"class": idx, "mask": cl["mask"], "found": len(found), "complete_claimed": en["complete"], "unblock": unblock,
                   "vars": nv, "clauses": len(cls), "cnf_sha256": sha}, open(base + ".gen.json", "w"))
        print("generated", base, "vars", nv, "clauses", len(cls), "sha256", sha[:16], flush=True)
    else:
        from pysat.solvers import Solver
        with Solver(name="cadical195", bootstrap_with=cls) as s:
            r = s.solve()
            if not r: print("class %d%s: UNSAT (%d multisets blocked)" % (idx, "" if unblock is None else " unblock %d" % unblock, len(found) - (unblock is not None))); sys.exit(0)
            m = set(l for l in s.get_model() if l > 0)
        x = [[int(pool.id(("x", Y, i)) in m) for i in range(6)] for Y in range(27)]
        C = [[0] * 27 for _ in range(27)]
        for Y, Z in itertools.combinations(range(27), 2):
            C[Y][Z] = C[Z][Y] = int(pool.id(("u", Y, Z)) in m) + int(pool.id(("w", Y, Z)) in m)
        e = eps_map([tuple(t) for t in cl["edges"]], cl["eps"]); allowed = [c for c, (s_, p) in enumerate(COLS) if type_ok(s_, p, e)]
        col = [next(c for c in allowed if pool.id(("y", Y, c)) in m) for Y in range(27)]
        bad = evaluate(cl, x, C, col)
        ms = sorted("".join(map(str, r)) for r in x)
        inlist = [k for k, f_ in enumerate(found) if sorted(f_) == ms]
        print("class %d%s: SAT, independent evaluator violations: %d, multiset = found #%s" % (idx, "" if unblock is None else " unblock %d" % unblock, len(bad), inlist or "NONE (new!)"))
