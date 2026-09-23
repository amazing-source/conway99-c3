"""Lean CNF for the quotient model (research 2026-09-23).  Same variables, same constraints as quotient_model.QModel.build_cnf; only the
cardinality encoding changes: 'sum(lits) == r' by ONE bidirectional totalizer whose node outputs are capped at r+1
(o_j <-> sum >= j for j <= r+1), instead of pysat's CardEnc.equals (which encodes the at-least half as at-most n-r on negations,
i.e. an almost full O(n^2) totalizer when r is small).  Both are arc-consistent; the capped one has O(n r^2) clauses.
Validation: validate_lean.py (exhaustive small cases, BvLS / rook quotients, certified-UNSAT and SAT-control Stage-Q instances)."""
import itertools
from quotient_model import dedup
_ctr = itertools.count()


def _node(lits, cap, pool, cls):
    """outputs o_1..o_c (c = min(len, cap)) with o_j <-> (sum of lits >= j) for j < c, and o_c <-> (sum >= c)."""
    if len(lits) == 1: return [lits[0]]
    h = len(lits) // 2
    a = _node(lits[:h], cap, pool, cls); b = _node(lits[h:], cap, pool, cls)
    full_a, full_b = len(lits[:h]), len(lits[h:])          # true sizes (a, b may be capped)
    c = min(len(lits), cap)
    o = [pool.id(("tot", next(_ctr))) for j in range(1, c + 1)]
    A = [None] + a; B = [None] + b; O = [None] + o          # 1-based
    p, q = len(a), len(b)
    # upward: sum_a >= i and sum_b >= j  ->  sum >= i + j   (capped)
    for i in range(0, p + 1):
        for j in range(0, q + 1):
            if i + j == 0: continue
            k = min(i + j, c); cl = [O[k]]
            if i: cl.append(-A[i])
            if j: cl.append(-B[j])
            cls.append(cl)
    # downward: sum_a <= i and sum_b <= j  ->  sum <= i + j, i.e. (not a_{i+1}) and (not b_{j+1}) -> not o_{i+j+1}, needs i+j+1 <= c
    for i in range(0, p + 1):
        for j in range(0, q + 1):
            k = i + j + 1
            if k > c: continue
            cl = [-O[k]]
            if i + 1 <= p: cl.append(A[i + 1])
            elif i + 1 <= full_a: continue                   # a capped: cannot certify sum_a <= i (does not happen since k <= c)
            if j + 1 <= q: cl.append(B[j + 1])
            elif j + 1 <= full_b: continue
            cls.append(cl)
    return o


def tot_equals(lits, r, pool, cls):
    """clauses forcing sum(lits) == r (lits distinct)."""
    n = len(lits)
    if r < 0 or r > n: f = pool.id(("FALSE",)); cls.extend([[f], [-f]]); return
    if n == 0: return
    if r == 0: cls.extend([[-l] for l in lits]); return
    if r == n: cls.extend([[l] for l in lits]); return
    o = _node(lits, r + 1, pool, cls)
    cls.append([o[r - 1]])                                    # sum >= r
    if len(o) > r: cls.append([-o[r]])                        # not (sum >= r+1)


def build_cnf_lean(QM):
    from pysat.formula import IDPool
    pool = IDPool(); cls = []; gates = {}
    v = lambda key: pool.id(key)
    for U in range(QM.m):
        for V in range(U + 1, QM.m):
            if (U, V) in QM.fixed: continue
            u = v(("u", U, V))
            if QM.types[U] == "I" and QM.types[V] == "I": cls.append([-v(("w", U, V)), u])
    def p(k1, k2):
        kk = (min(k1, k2), max(k1, k2))
        if kk not in gates:
            g = pool.id(("g",) + kk); a, b = v(kk[0]), v(kk[1]); cls.extend([[-g, a], [-g, b], [g, -a, -b]]); gates[kk] = g
        return gates[kk]
    for name, terms, rhs in QM.constraints():
        const = sum(t[1] for t in terms if t[0] == "c")
        lits = [v(t[1]) if t[0] == "v" else p(t[1], t[2]) for t in terms if t[0] != "c"]
        lits = dedup(lits, pool, cls)
        tot_equals(lits, rhs - const, pool, cls)
    return cls, pool
