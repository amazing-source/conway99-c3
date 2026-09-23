"""Deletion-based core minimisation by constraint FAMILY, solving sub-models from scratch (no reliance on CP-SAT's core API)."""
import json, sys, time
from ortools.sat.python import cp_model
from full_model import Model
classes = json.load(open("classes_reduced.json")); idx = int(sys.argv[1]); cls = classes[idx]
types = ["T"] * 6 + ["I"] * 27; fixed = {}; E = {}
for (i, j), e in zip(cls["edges"], cls["eps"]): E[(i, j)] = e % 3
for i in range(6):
    for j in range(i + 1, 6):
        for p in range(3): fixed[(i, j, p)] = 1 if ((i, j) in E and E[(i, j)] == p) else 0
M = Model(types, 14, fixed)
ALL = list(M.constraints())
def fam(name):
    if name[0] == "deg": return "deg_T" if name[1] < 6 else "deg_I"
    _, U, V, b = name
    t = ("T" if U < 6 else "I") + ("T" if V < 6 else "I")
    return "pair_" + t
def solve(keep, secs=120):
    md = cp_model.CpModel(); var = {}; gates = {}
    def v(key):
        if key not in var: var[key] = md.NewBoolVar("")
        return var[key]
    def p(k1, k2):
        kk = (min(k1, k2), max(k1, k2))
        if kk not in gates:
            g = md.NewBoolVar(""); a, b = v(kk[0]), v(kk[1])
            md.AddBoolAnd([a, b]).OnlyEnforceIf(g); md.AddBoolOr([a.Not(), b.Not()]).OnlyEnforceIf(g.Not()); gates[kk] = g
        return gates[kk]
    for name, terms, rhs in ALL:
        if not keep(name): continue
        const = sum(t[1] for t in terms if t[0] == "c")
        md.Add(sum(v(t[1]) if t[0] == "v" else p(t[1], t[2]) for t in terms if t[0] != "c") == rhs - const)
    for keys, lim in M.multiplicity_limits(): md.Add(sum(v(k_) for k_ in keys) <= lim)
    sv = cp_model.CpSolver(); sv.parameters.num_workers = 8; sv.parameters.max_time_in_seconds = secs
    return sv.StatusName(sv.Solve(md))
fams = sorted(set(fam(n) for n, _, _ in ALL))
print("families:", fams)
print("only pair(0,1,0):", solve(lambda n: n == ("pair", 0, 1, 0)))
for f in fams: print("only", f, "->", solve(lambda n, f=f: fam(n) == f))
print("deg_T + pair_TT:", solve(lambda n: fam(n) in ("deg_T", "pair_TT")))
print("deg_T + pair_TT + pair_TI:", solve(lambda n: fam(n) in ("deg_T", "pair_TT", "pair_TI")))
