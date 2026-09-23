"""Extract an unsatisfiable core (set of constraint groups) for one class, to understand WHY it is infeasible."""
import json, sys
from ortools.sat.python import cp_model
from full_model import Model
classes = json.load(open("classes_reduced.json")); idx = int(sys.argv[1]); cls = classes[idx]
types = ["T"] * 6 + ["I"] * 27; fixed = {}; E = {}
for (i, j), e in zip(cls["edges"], cls["eps"]): E[(i, j)] = e % 3
for i in range(6):
    for j in range(i + 1, 6):
        for p in range(3): fixed[(i, j, p)] = 1 if ((i, j) in E and E[(i, j)] == p) else 0
M = Model(types, 14, fixed)
md = cp_model.CpModel(); var = {}; gates = {}; lits = {}
def v(key):
    if key not in var: var[key] = md.NewBoolVar("z%d_%d_%d" % key)
    return var[key]
def p(k1, k2):
    kk = (min(k1, k2), max(k1, k2))
    if kk not in gates:
        g = md.NewBoolVar(""); a, b = v(kk[0]), v(kk[1])
        md.AddBoolAnd([a, b]).OnlyEnforceIf(g); md.AddBoolOr([a.Not(), b.Not()]).OnlyEnforceIf(g.Not()); gates[kk] = g
    return gates[kk]
for name, terms, rhs in M.constraints():
    const = sum(t[1] for t in terms if t[0] == "c")
    lin = [v(t[1]) if t[0] == "v" else p(t[1], t[2]) for t in terms if t[0] != "c"]
    L = md.NewBoolVar(str(name)); lits[L.Index()] = (name, lin, rhs - const)
    md.Add(sum(lin) == rhs - const).OnlyEnforceIf(L)
for keys, lim in M.multiplicity_limits():
    md.Add(sum(v(k_) for k_ in keys) <= lim)
md.AddAssumptions([md.GetBoolVarFromProtoIndex(i) for i in lits])
sv = cp_model.CpSolver(); sv.parameters.num_workers = 1; sv.parameters.max_time_in_seconds = 300
st = sv.Solve(md); print("status:", sv.StatusName(st))
core = [lits[i] for i in sv.SufficientAssumptionsForInfeasibility()]
print("core size:", len(core))
for name, lin, r in core: print("  ", name, "n_terms=%d rhs=%d" % (len(lin), r))
