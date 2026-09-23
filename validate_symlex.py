"""Validate the FULL symmetry breaking of stageq_sym.py (production functions: symmetries, add_perm_lex, entry_bits, add_lex_leq,
with quotient_model.add_lex_twins and lean_encoding.build_cnf_lean), on small random models where all solutions can be enumerated.
Mock model: t triangle orbits (random F), n independent orbits with random SORTED supports (twins likely), independent block free;
constraints = the independent rows' row sums (value k_I) and 'exactly two doubles' (the Gram equations are dropped so that solutions
exist; every kept constraint is invariant under the automorphisms of the fixed data, as in Stage Q).
Checks per mock: (a) the solution set S is invariant under the full group G of the fixed data (brute force over t! n! permutations);
(b) the breaking CNF's solutions S' are a subset of S; (c) EVERY G-orbit of S keeps at least one solution in S' (soundness);
(d) the lex-min element of each orbit (string = full matrix row-major, value order 0<1<2) is in S' (the proof's witness)."""
import itertools, random, sys
from pysat.solvers import Solver
from quotient_model import QModel, add_lex_twins
from lean_encoding import build_cnf_lean
from stageq_sym import symmetries, add_perm_lex

def mock(seed):
    R = random.Random(seed)
    t = R.choice([2, 3])
    if seed % 2:                                     # symmetric mode: F empty/complete, supports = whole S_t-orbits of weight classes
        edges = [] if R.random() < 0.5 else [(a, b) for a in range(t) for b in range(a + 1, t)]
        key = []
        while len(key) < 4:
            w = R.randint(0, t); rep = R.choice([1, 1, 2])
            key += [s for s in itertools.product((0, 1), repeat=t) if sum(s) == w] * rep
        key = sorted(key[:7] if len(key) > 7 else key)
    else:
        edges = [(a, b) for a in range(t) for b in range(a + 1, t) if R.random() < 0.5]
        pool_s = [tuple(R.randint(0, 1) for _ in range(t)) for _ in range(R.choice([1, 2, 2, 3]))]
        key = sorted(R.choice(pool_s) for _ in range(R.choice([4, 5, 6])))
    n = len(key); m = t + n
    types = ["T"] * t + ["I"] * n; fixed = {}
    for i in range(t):
        for j in range(i + 1, t): fixed[(i, j)] = int((i, j) in edges)
    for Y, s in enumerate(key):
        for i in range(t): fixed[(i, t + Y)] = s[i]
    x = R.randint(0, max(0, n - 3))                  # row target |s_Y| + 4 + x : invariant under the automorphisms of the fixed data
    QM = QModel(types, 99, fixed); gen = QM.constraints
    def cons():
        for name, terms, rhs in gen():
            if name[0] == "doubles": yield name, terms, rhs
            elif name[0] == "rowsum" and types[name[1]] == "I": yield name, terms, sum(key[name[1] - t]) + 4 + x
    QM.constraints = cons
    return QM, t, n, edges, key

def matrix(QM, pool, model):
    m = QM.m; Q = [[0] * m for _ in range(m)]
    for a in range(m):
        Q[a][a] = 2 if QM.types[a] == "T" else 0
        for b in range(a + 1, m):
            if (a, b) in QM.fixed: v = QM.fixed[(a, b)]
            else:
                v = int(pool.id(("u", a, b)) in model) + (int(pool.id(("w", a, b)) in model) if QM.types[a] == QM.types[b] == "I" else 0)
            Q[a][b] = Q[b][a] = v
    return tuple(tuple(r) for r in Q)

def enumerate_all(cls, QM, pool, cap=20000):
    free = [pool.id((k, a, b)) for a in range(QM.m) for b in range(a + 1, QM.m) if (a, b) not in QM.fixed
            for k in (("u", "w") if QM.types[a] == QM.types[b] == "I" else ("u",))]
    out = set()
    with Solver(name="cadical195", bootstrap_with=cls) as s:
        while s.solve() and len(out) < cap:
            md = set(l for l in s.get_model() if l > 0); out.add(matrix(QM, pool, md))
            s.add_clause([-v if v in md else v for v in free])
    return out

def act(Q, full):
    m = len(Q); inv = [0] * m
    for a in range(m): inv[full[a]] = a
    return tuple(tuple(Q[inv[a]][inv[b]] for b in range(m)) for a in range(m))

bad = 0; tot_orbits = 0; tot_sym = 0
for seed in range(int(sys.argv[1]) if len(sys.argv) > 1 else 40):
    QM, t, n, edges, key = mock(seed); m = t + n
    cls, pool = build_cnf_lean(QM); S = enumerate_all(cls, QM, pool)
    # full group of the fixed data
    G = []
    for pT in itertools.permutations(range(t)):
        for pI in itertools.permutations(range(n)):
            full = list(pT) + [t + x for x in pI]
            if all(QM.fixed[(min(full[a], full[b]), max(full[a], full[b]))] == v for (a, b), v in QM.fixed.items()): G.append(full)
    inv_ok = all(act(Q, g) in S for Q in S for g in G)
    # production breaking
    cls2, pool2 = build_cnf_lean(QM)
    groups = {}
    for Y, s in enumerate(key): groups.setdefault(s, []).append(t + Y)
    add_lex_twins(QM, cls2, pool2, [g for g in groups.values() if len(g) > 1])
    syms = symmetries(edges, [tuple(s) for s in key], t)
    add_perm_lex(QM, cls2, pool2, [list(pi) + [t + s for s in sig] for pi, sig in syms])
    S2 = enumerate_all(cls2, QM, pool2)
    seen = set(); orbits = []
    for Q in S:
        if Q in seen: continue
        orb = set(act(Q, g) for g in G); seen |= orb; orbits.append(orb)
    lost = sum(1 for o in orbits if not (o & S2))
    minmiss = sum(1 for o in orbits if min(o, key=lambda Q: [x for r in Q for x in r]) not in S2)
    ok = inv_ok and S2 <= S and lost == 0 and minmiss == 0
    bad += not ok; tot_orbits += len(orbits); tot_sym += len(syms)
    print("seed %2d t=%d n=%d |G|=%4d syms=%3d |S|=%5d orbits=%4d |S'|=%4d lost_orbits=%d lexmin_missing=%d invariant=%s -> %s"
          % (seed, t, n, len(G), len(syms), len(S), len(orbits), len(S2), lost, minmiss, inv_ok, "ok" if ok else "WRONG"), flush=True)
print("SYMLEX VALIDATION:", "PASS" if bad == 0 else "FAIL (%d)" % bad, "| orbits checked:", tot_orbits, "| sigma constraints used:", tot_sym)
