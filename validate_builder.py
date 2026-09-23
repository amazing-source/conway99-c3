"""Validate build_cpsat on real graphs: srg(9,4,1,2) (3x3 rook graph) with its two kinds of fixed-point-free order-3 automorphisms.
 - (x,y)->(x+1,y): orbits are columns -> 3 triangular orbits;  (x,y)->(x+1,y+1): orbits are diagonals -> 3 independent orbits.
Solve WITHOUT planting; every solution found is lifted and checked with the integer identity; enumerate all; negative control k=5."""
from ortools.sat.python import cp_model
from full_model import Model, build_cpsat
class Enum(cp_model.CpSolverSolutionCallback):
    def __init__(s, M, var): super().__init__(); s.M, s.var, s.n, s.bad = M, var, 0, 0
    def on_solution_callback(s):
        z = {k: s.Value(x) for k, x in s.var.items()}; A, ok = s.M.lift(z); s.n += 1; s.bad += (not ok)
for types, label in ((["T"] * 3, "3 triangular orbits"), (["I"] * 3, "3 independent orbits")):
    for k in (4, 5):
        M = Model(types, k); md, var = build_cpsat(M)
        sv = cp_model.CpSolver(); sv.parameters.enumerate_all_solutions = True; sv.parameters.num_workers = 1
        cb = Enum(M, var); st = sv.Solve(md, cb)
        print("%-22s k=%d: status=%s, solutions=%d, failing integer check=%d" % (label, k, sv.StatusName(st), cb.n, cb.bad))
