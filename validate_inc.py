"""Validate incremental cubing (assumptions + conflict budget, as in cube_q_inc.py) against independent fresh solves with the cube as
UNIT CLAUSES (as in cube_q.py), cube by cube, on a formula that has both SAT and UNSAT cubes: the relaxed m23221_s0027 CNF
(independent x independent Gram equations dropped; symmetry breaking kept).  Also times the first real cubes of m16420_sL1 both ways.
Every verdict must agree; every SAT model is checked against the CNF clause by clause."""
import sys, json, time, itertools
from pysat.solvers import Solver
from cube_q import lq_candidates

def clauses(path):
    for line in open(path):
        if line[0] in "pc": continue
        yield [int(x) for x in line.split()[:-1]]

def check_model(path, model, units):
    m = set(model)
    return all(any(l in m for l in c) for c in clauses(path)) and all(u in m for u in units)

def compare(cnf, varmap, Z, cubes, budget):
    wv = lambda a, b: varmap["w,%d,%d" % (min(a, b), max(a, b))]
    inc = Solver(name="cadical195")
    for c in clauses(cnf): inc.add_clause(c)
    agree = dis = sat = uns = 0; t_inc = t_fresh = 0.0
    for (A, B) in cubes:
        u = [wv(Z, A), wv(Z, B)]
        t = time.time(); inc.conf_budget(budget); r1 = inc.solve_limited(assumptions=u); t_inc += time.time() - t
        if r1 is True: assert check_model(cnf, inc.get_model(), u), "incremental SAT model violates the CNF"
        fr = Solver(name="cadical195")
        for c in clauses(cnf): fr.add_clause(c)
        for l in u: fr.add_clause([l])
        t = time.time(); r2 = fr.solve(); t_fresh += time.time() - t
        if r2: assert check_model(cnf, fr.get_model(), u), "fresh SAT model violates the CNF"
        fr.delete()
        if r1 is None: continue
        if r1 == r2: agree += 1; sat += r1; uns += (not r1)
        else: dis += 1; print("DISAGREEMENT cube", A, B, "inc", r1, "fresh", r2, flush=True)
    inc.delete()
    return agree, dis, sat, uns, t_inc, t_fresh

if __name__ == "__main__":
    g = json.load(open("stageQ_sym/m23221_s0027_relaxed.gen.json"))
    cubes = list(itertools.combinations([A for A in range(7, 33)], 2))
    a, d, s_, u_, ti, tf = compare("stageQ_sym/m23221_s0027_relaxed.cnf", g["varmap"], 6, cubes, 10 ** 6)
    print("relaxed m23221_s0027, Z=6, 325 cubes: agree %d (SAT %d, UNSAT %d), disagree %d | solve time incremental %.1fs, fresh %.1fs" % (a, s_, u_, d, ti, tf), flush=True)
    g2 = json.load(open("cubes/m16420_sL1/base.gen.json"))
    a2, d2, s2, u2, ti2, tf2 = compare("cubes/m16420_sL1/base.cnf", g2["varmap"], 6, [(7, 8), (7, 9), (12, 20), (15, 30)], 10 ** 6)
    print("m16420_sL1, 4 real cubes: agree %d (UNSAT %d), disagree %d | solve time incremental %.1fs, fresh %.1fs" % (a2, u2, d2, ti2, tf2))
    print("INCREMENTAL VALIDATION:", "PASS" if d == 0 and d2 == 0 and s_ > 0 and u_ > 0 else "FAIL (or no SAT/UNSAT mix)")
