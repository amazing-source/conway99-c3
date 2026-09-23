"""Exact vertex-level model of an srg(n,k,1,2) with a fixed-point-free automorphism g of order 3.
Orbits O_0..O_{m-1}, each 'T' (induces a triangle) or 'I' (independent); vertex (U,a), a in F3, g:(U,a)->(U,a+1).
Unknowns z[(U,V,psi)] (U<V, psi in F3): (U,a) ~ (V,a+psi) for all a.  At most one psi if U or V is 'T', at most two otherwise.
Constraints (for every orbit U and every vertex (V,b) != (U,0), up to the g-symmetry):
    #common neighbours((U,0),(V,b)) + adj((U,0),(V,b)) = 2        (lambda = 1, mu = 2)
    deg((U,0)) = k
The constraint generator is shared by the planted-solution evaluator (validation) and the CP-SAT builder, so a validation on a real
graph checks exactly the formulas used for solving."""
import itertools


class Model:
    def __init__(self, types, k, fixed=None):
        self.types, self.k, self.m = types, k, len(types)
        self.fixed = fixed or {}           # (U,V,psi) -> 0/1 for pairs whose adjacency is known

    def adj(self, U, a, V, b):
        """('c', value) or ('v', key) for the adjacency of (U,a) and (V,b)."""
        if U == V:
            return ("c", 1 if (self.types[U] == "T" and a != b) else 0)
        if U < V:
            key = (U, V, (b - a) % 3)
        else:
            key = (V, U, (a - b) % 3)
        if key in self.fixed:
            return ("c", self.fixed[key])
        return ("v", key)

    def pair_keys(self):
        for U in range(self.m):
            for V in range(U + 1, self.m):
                yield U, V

    def constraints(self):
        """yield (name, terms, rhs): sum(terms) == rhs; a term is ('c',n) | ('v',key) | ('p',key1,key2)."""
        m = self.m
        verts = [(W, c) for W in range(m) for c in range(3)]
        for U in range(m):
            # degree of (U,0)
            terms = [self.adj(U, 0, W, c) for (W, c) in verts if (W, c) != (U, 0)]
            yield ("deg", U), terms, self.k
            for V in range(U, m):
                for b in range(3):
                    if V == U and b == 0: continue
                    if V == U and b == 2: continue           # (U,0),(U,2) is the g^{-1}-image of (U,1),(U,0)... same as (U,0),(U,1)
                    terms = []
                    for (W, c) in verts:
                        if (W, c) in ((U, 0), (V, b)): continue
                        x = self.adj(U, 0, W, c); y = self.adj(V, b, W, c)
                        if x[0] == "c" and y[0] == "c":
                            if x[1] and y[1]: terms.append(("c", 1))
                        elif x[0] == "c":
                            if x[1]: terms.append(y)
                        elif y[0] == "c":
                            if y[1]: terms.append(x)
                        else:
                            terms.append(("p", x[1], y[1]) if x[1] != y[1] else ("v", x[1]))
                    terms.append(self.adj(U, 0, V, b))
                    yield ("pair", U, V, b), terms, 2

    def multiplicity_limits(self):
        for U, V in self.pair_keys():
            keys = [(U, V, p) for p in range(3) if (U, V, p) not in self.fixed]
            if not keys: continue
            lim = 1 if "T" in (self.types[U], self.types[V]) else 2
            yield keys, lim - sum(self.fixed.get((U, V, p), 0) for p in range(3))

    def evaluate(self, z):
        """z: dict key -> 0/1 for all non-fixed keys. Returns list of violated constraint names (empty = all satisfied)."""
        val = lambda t: t[1] if t[0] == "c" else (z[t[1]] if t[0] == "v" else z[t[1]] * z[t[2]])
        bad = [name for name, terms, rhs in self.constraints() if sum(val(t) for t in terms) != rhs]
        bad += [("mult", tuple(keys)) for keys, lim in self.multiplicity_limits() if sum(z[k_] for k_ in keys) > lim]
        return bad

    def lift(self, z):
        """99x99 (or n x n) adjacency matrix from z, and the integer check A^2 + A - (k-2) I == 2 J."""
        import numpy as np
        n = 3 * self.m; A = np.zeros((n, n), dtype=np.int64)
        for U in range(self.m):
            for a in range(3):
                for V in range(self.m):
                    for b in range(3):
                        if (U, a) == (V, b): continue
                        x = self.adj(U, a, V, b)
                        A[3 * U + a, 3 * V + b] = x[1] if x[0] == "c" else z[x[1]]
        ok = np.array_equal(A, A.T) and np.array_equal(A @ A + A - (self.k - 2) * np.eye(n, dtype=np.int64), 2 * np.ones((n, n), dtype=np.int64))
        return A, ok


def build_cpsat(M):
    """CP-SAT model for Model M (shared by validation and by the Conway runs). Returns (cp_model, var dict)."""
    from ortools.sat.python import cp_model
    md = cp_model.CpModel(); var = {}; gates = {}
    def v(key):
        if key not in var: var[key] = md.NewBoolVar("z%d_%d_%d" % key)
        return var[key]
    def p(k1, k2):
        kk = (min(k1, k2), max(k1, k2))
        if kk not in gates:
            g = md.NewBoolVar(""); a, b = v(kk[0]), v(kk[1])
            md.AddBoolAnd([a, b]).OnlyEnforceIf(g)                 # g -> a and b
            md.AddBoolOr([a.Not(), b.Not()]).OnlyEnforceIf(g.Not())  # not g -> not (a and b)
            gates[kk] = g
        return gates[kk]
    for name, terms, rhs in M.constraints():
        const = sum(t[1] for t in terms if t[0] == "c")
        lin = [v(t[1]) if t[0] == "v" else p(t[1], t[2]) for t in terms if t[0] != "c"]
        if lin: md.Add(sum(lin) == rhs - const)
        elif const != rhs: md.AddBoolOr([])                         # constant contradiction
    for keys, lim in M.multiplicity_limits():
        md.Add(sum(v(k_) for k_ in keys) <= lim)
    for U, V in M.pair_keys():                                      # make sure every free key exists as a variable
        for q in range(3):
            if (U, V, q) not in M.fixed: v((U, V, q))
    return md, var


def build_cnf(M, extra_units=()):
    """Pure CNF for Model M (Tseitin AND gates + pysat cardinality encodings). Returns (CNF clauses list, key->var id, IDPool)."""
    from pysat.formula import IDPool
    from pysat.card import CardEnc, EncType
    pool = IDPool(); cls = []
    def v(key): return pool.id(("z",) + key)
    gates = {}
    def p(k1, k2):
        kk = (min(k1, k2), max(k1, k2))
        if kk not in gates:
            g = pool.id(("g",) + kk[0] + kk[1]); a, b = v(kk[0]), v(kk[1])
            cls.extend([[-g, a], [-g, b], [g, -a, -b]]); gates[kk] = g
        return gates[kk]
    def card_eq(lits, k):
        if k < 0 or k > len(lits): cls.extend([[pool.id(('FALSE',))], [-pool.id(('FALSE',))]]); return
        if not lits: return
        cls.extend(CardEnc.equals(lits=lits, bound=k, vpool=pool, encoding=EncType.seqcounter).clauses)
    def card_le(lits, k):
        if k < 0: cls.extend([[pool.id(('FALSE',))], [-pool.id(('FALSE',))]]); return
        if k >= len(lits): return
        cls.extend(CardEnc.atmost(lits=lits, bound=k, vpool=pool, encoding=EncType.seqcounter).clauses)
    for U, V in M.pair_keys():
        for q in range(3):
            if (U, V, q) not in M.fixed: v((U, V, q))
    for name, terms, rhs in M.constraints():
        const = sum(t[1] for t in terms if t[0] == "c")
        lits = [v(t[1]) if t[0] == "v" else p(t[1], t[2]) for t in terms if t[0] != "c"]
        card_eq(dedup(lits, pool, cls), rhs - const)
    for keys, lim in M.multiplicity_limits():
        card_le([v(k_) for k_ in keys], lim)
    cls.extend([[u] for u in extra_units])
    keymap = {key: v(key) for U, V in M.pair_keys() for key in ((U, V, 0), (U, V, 1), (U, V, 2)) if key not in M.fixed}
    return cls, keymap, pool


def _solve_worker(cls, keymap, solver, q):
    from pysat.solvers import Solver
    with Solver(name=solver, bootstrap_with=cls) as s:
        r = s.solve()
        if r:
            mdl = set(l for l in s.get_model() if l > 0)
            q.put(("SAT", {k: int(x in mdl) for k, x in keymap.items()}))
        else:
            q.put(("UNSAT", None))


def solve_cnf(M, seconds, solver="cadical195"):
    """Solve in a separate process with a HARD wall-clock limit (the process is terminated on timeout).
    Returns ('SAT', z) | ('UNSAT', None) | ('UNKNOWN', None)."""
    import multiprocessing as mp, queue
    cls, keymap, pool = build_cnf(M)
    q = mp.Queue(); pr = mp.Process(target=_solve_worker, args=(cls, keymap, solver, q)); pr.start()
    try:
        res = q.get(timeout=seconds)
    except queue.Empty:
        res = ("UNKNOWN", None)
    pr.terminate(); pr.join()
    return res


def dedup(lits, pool, cls):
    """Replace repeated literals by fresh equivalent copies (x' <-> x), so cardinality encodings never see duplicates."""
    seen = set(); out = []
    for l in lits:
        if l in seen:
            c = pool.id(("copy", len(cls), l)); cls.extend([[-c, l], [c, -l]]); out.append(c)
        else:
            seen.add(l); out.append(l)
    return out
