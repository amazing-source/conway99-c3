"""Solve a DIMACS file with pysat's CaDiCaL 1.9.5, streaming clauses from disk (no Python clause list kept in memory).
Writes the model as DIMACS 'v' lines to <out> when SAT.  No internal timeout: the caller kills it (timeout(1)).
Exit code 10 = SAT, 20 = UNSAT (same convention as the native binary).  Usage: python solve_stream.py <cnf> <out> [unit literals ...]
(extra unit literals = a cube, used by cube_q.py)"""
import sys, time
from pysat.solvers import Solver
cnf, out = sys.argv[1], sys.argv[2]; units = [int(a) for a in sys.argv[3:]]
t0 = time.time()
with Solver(name="cadical195") as s:
    with open(cnf) as f:
        for line in f:
            if line[0] in "pc": continue
            s.add_clause([int(x) for x in line.split()[:-1]])
    for l in units: s.add_clause([l])
    t1 = time.time(); r = s.solve()
    with open(out, "w") as g:
        g.write("c load %.1fs solve %.1fs\n" % (t1 - t0, time.time() - t1))
        if r:
            g.write("s SATISFIABLE\nv " + " ".join(map(str, s.get_model())) + " 0\n")
        else:
            g.write("s UNSATISFIABLE\n")
sys.exit(10 if r else 20)
