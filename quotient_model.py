"""Quotient-level (x = 1) model for an srg(n,k,1,2) with a fixed-point-free automorphism of order 3 (all orbits of size 3).
Q (m x m, symmetric): Q_UU = 2 if U is 'T' (triangle), 0 if 'I'; Q_UV in {0,1} if U or V is 'T', in {0,1,2} if both 'I'.
Necessary conditions (proved): Q 1 = k 1;  Q^2 + Q = (k-2) I + 6 J;  every 'I' row has exactly two entries equal to 2.
Encoding: Q_UV = u_UV + w_UV with w -> u (w = [Q=2]); products expand into AND gates.  Entries can be fixed (dict (U,V)->value)."""
import itertools


class QModel:
    def __init__(self, types, k, fixed=None):
        self.types, self.k, self.m = types, k, len(types)
        self.fixed = fixed or {}                      # (U,V) U<V -> value 0/1/2

    def entry(self, U, V):
        """list of ('c',n) / ('v',key) terms whose sum is Q_UV."""
        if U == V: return [("c", 2 if self.types[U] == "T" else 0)]
        a, b = min(U, V), max(U, V)
        if (a, b) in self.fixed: return [("c", self.fixed[(a, b)])]
        t = [("v", ("u", a, b))]
        if self.types[a] == "I" and self.types[b] == "I": t.append(("v", ("w", a, b)))
        return t

    def constraints(self):
        m, k = self.m, self.k
        for U in range(m):
            yield ("rowsum", U), [t for V in range(m) for t in self.entry(U, V)], k
            if self.types[U] == "I":
                terms = []
                for V in range(m):
                    if V == U: continue
                    a, b = min(U, V), max(U, V)
                    if (a, b) in self.fixed: terms.append(("c", int(self.fixed[(a, b)] == 2)))
                    elif self.types[V] == "I": terms.append(("v", ("w", a, b)))
                yield ("doubles", U), terms, 2
            for V in range(U, m):
                terms = []
                for W in range(m):
                    for x in self.entry(U, W):
                        for y in self.entry(W, V):
                            if x[0] == "c" and y[0] == "c":
                                if x[1] * y[1]: terms.append(("c", x[1] * y[1]))
                            elif x[0] == "c":
                                if x[1]: terms += [y] * x[1]
                            elif y[0] == "c":
                                if y[1]: terms += [x] * y[1]
                            else:
                                terms.append(("p", x[1], y[1]) if x[1] != y[1] else ("v", x[1]))
                terms += self.entry(U, V)
                yield ("gram", U, V), terms, (k - 2) * (U == V) + 6

    def evaluate(self, Q):
        val = lambda t: t[1] if t[0] == "c" else (self._z(Q, t[1]) if t[0] == "v" else self._z(Q, t[1]) * self._z(Q, t[2]))
        return [name for name, terms, rhs in self.constraints() if sum(val(t) for t in terms) != rhs]

    @staticmethod
    def _z(Q, key):
        kind, a, b = key
        return int(Q[a][b] >= 1) if kind == "u" else int(Q[a][b] == 2)

    def build_cnf(self):
        from pysat.formula import IDPool
        from pysat.card import CardEnc, EncType
        pool = IDPool(); cls = []; gates = {}
        v = lambda key: pool.id(key)
        for U in range(self.m):
            for V in range(U + 1, self.m):
                if (U, V) in self.fixed: continue
                u = v(("u", U, V))
                if self.types[U] == "I" and self.types[V] == "I": cls.append([-v(("w", U, V)), u])     # w -> u
        def p(k1, k2):
            kk = (min(k1, k2), max(k1, k2))
            if kk not in gates:
                g = pool.id(("g",) + kk); a, b = v(kk[0]), v(kk[1]); cls.extend([[-g, a], [-g, b], [g, -a, -b]]); gates[kk] = g
            return gates[kk]
        for name, terms, rhs in self.constraints():
            const = sum(t[1] for t in terms if t[0] == "c")
            lits = [v(t[1]) if t[0] == "v" else p(t[1], t[2]) for t in terms if t[0] != "c"]
            lits = dedup(lits, pool, cls); r = rhs - const
            if r < 0 or r > len(lits): cls.extend([[pool.id(('FALSE',))], [-pool.id(('FALSE',))]]); continue
            if lits: cls.extend(CardEnc.equals(lits=lits, bound=r, vpool=pool, encoding=EncType.totalizer).clauses)
        return cls, pool

    def decode(self, model_set, pool):
        Q = [[0] * self.m for _ in range(self.m)]
        for U in range(self.m):
            Q[U][U] = 2 if self.types[U] == "T" else 0
            for V in range(U + 1, self.m):
                if (U, V) in self.fixed: val = self.fixed[(U, V)]
                else:
                    val = int(pool.id(("u", U, V)) in model_set)
                    if self.types[U] == "I" and self.types[V] == "I": val += int(pool.id(("w", U, V)) in model_set)
                Q[U][V] = Q[V][U] = val
        return Q


def _worker(cls, q):
    from pysat.solvers import Solver
    with Solver(name="cadical195", bootstrap_with=cls) as s:
        r = s.solve(); q.put((r, [l for l in s.get_model() if l > 0] if r else None))


def solve_q(QM, seconds):
    import multiprocessing as mp, queue
    cls, pool = QM.build_cnf()
    q = mp.Queue(); pr = mp.Process(target=_worker, args=(cls, q)); pr.start()
    try: r, mdl = q.get(timeout=seconds)
    except queue.Empty: r, mdl = None, None
    pr.terminate(); pr.join()
    if r is True:
        Q = QM.decode(set(mdl), pool); return "SAT", Q
    return ("UNSAT" if r is False else "UNKNOWN"), None


def dedup(lits, pool, cls):
    """Replace repeated literals by fresh equivalent copies (x' <-> x), so cardinality encodings never see duplicates."""
    seen = set(); out = []
    for l in lits:
        if l in seen:
            c = pool.id(("copy", len(cls), l)); cls.extend([[-c, l], [c, -l]]); out.append(c)
        else:
            seen.add(l); out.append(l)
    return out


def add_lex_twins(QM, cls, pool, groups):
    """Sound symmetry breaking (Codish-Miller-Prosser-Stuckey 2013, row-wise lex order of interchangeable vertices):
    for interchangeable independent orbits i < j (same fixed row outside the free block), require row_i <=lex row_j, comparing the
    free entries Q[i][W], Q[j][W] for W not in {i, j} (value order 0<1<2 = bit order on (u, w))."""
    def bits(U, W):
        a, b = min(U, W), max(U, W)
        if (a, b) in QM.fixed: return None
        out = [pool.id(("u", a, b))]
        if QM.types[a] == "I" and QM.types[b] == "I": out.append(pool.id(("w", a, b)))
        return out
    for grp in groups:
        for i, j in zip(grp, grp[1:]):
            X, Y = [], []
            for W in range(QM.m):
                if W in (i, j): continue
                bi, bj = bits(i, W), bits(j, W)
                if bi is None or bj is None: continue
                X += bi; Y += bj
            e = pool.id(("lex", i, j, 0)); cls.append([e])
            for t, (x, y) in enumerate(zip(X, Y)):
                cls.append([-e, -x, y])                                      # prefix equal -> x <= y
                e2 = pool.id(("lex", i, j, t + 1))
                cls.append([-e, x, y, e2]); cls.append([-e, -x, -y, e2])       # prefix stays equal if x == y
                e = e2


def solve_q_lex(QM, groups, seconds):
    import multiprocessing as mp, queue
    cls, pool = QM.build_cnf(); add_lex_twins(QM, cls, pool, groups)
    q = mp.Queue(); pr = mp.Process(target=_worker, args=(cls, q)); pr.start()
    try: r, mdl = q.get(timeout=seconds)
    except queue.Empty: r, mdl = None, None
    pr.terminate(); pr.join()
    if r is True: return "SAT", QM.decode(set(mdl), pool)
    return ("UNSAT" if r is False else "UNKNOWN"), None
