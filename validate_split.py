"""Validate the recursive splitting of cube_q_inc.py: on the relaxed m23221_s0027 CNF (SAT and UNSAT cubes both occur), run
cube_q_inc.py --relaxed with a TINY conflict budget (so that most cubes go through the split pass), then compare every cube verdict
with an independent fresh solve (cube as unit clauses, no budget).  Every verdict must agree (UNKNOWN allowed only if the budget ran out).
Usage: python validate_split.py <first N cubes> <budget>"""
import sys, json, subprocess, itertools, os
from pysat.solvers import Solver
N, B = int(sys.argv[1]), int(sys.argv[2])
d = "cubes/m23221_s0027_relaxed"
if os.path.exists(d + "/results_incval.txt"): os.remove(d + "/results_incval.txt")
if os.path.exists(d + "/subcubes.txt"): os.remove(d + "/subcubes.txt")
subprocess.run(["python", "cube_q_inc.py", "m23221_s0027", "6", str(B), str(N), "--relaxed"], check=True)          # N < 0: last |N| cubes
vm = json.load(open(d + "/base.gen.json"))["varmap"]; wv = lambda a, b: vm["w,%d,%d" % (min(a, b), max(a, b))]
clauses = [[int(x) for x in l.split()[:-1]] for l in open(d + "/base.cnf") if l[0] not in "pc"]
got = {}
for line in open(d + "/results_incval.txt"):
    p = line.split(); got[(int(p[1]), int(p[2]))] = (p[3], " ".join(p[5:]))
allc = list(itertools.combinations(range(7, 33), 2)); cubes = allc[:N] if N > 0 else allc[N:]
agree = dis = unk = 0; via_split = 0
for (A, Bc) in cubes:
    with Solver(name="cadical195", bootstrap_with=clauses) as s:
        s.add_clause([wv(6, A)]); s.add_clause([wv(6, Bc)]); fresh = "SAT" if s.solve() else "UNSAT"
    st, tag = got.get((A, Bc), ("MISSING", ""))
    via_split += "split" in tag
    if st.startswith("UNKNOWN"): unk += 1
    elif st.split("(")[0] == fresh: agree += 1
    else: dis += 1; print("DISAGREEMENT", A, Bc, st, tag, "fresh", fresh)
n_sub = sum(1 for _ in open(d + "/subcubes.txt")) if os.path.exists(d + "/subcubes.txt") else 0
print("split validation: %d cubes, agree %d, disagree %d, unknown %d, decided through the split pass %d, sub-cube nodes logged %d" % (len(cubes), agree, dis, unk, via_split, n_sub))
print("SPLIT VALIDATION:", "PASS" if dis == 0 and via_split > 0 else "FAIL")
