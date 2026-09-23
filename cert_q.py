"""Certify a Stage-Q UNSAT: regenerate the exact CNF (same generator as run_one_q.py, incl. the twin lex symmetry breaking), solve it with
the native CaDiCaL binary emitting a DRAT proof, and check the proof with drat-trim.  Run inside the 'proofbox' image.
What this certifies: the CNF is unsatisfiable (independently of the solver).  What it relies on: that the CNF encodes the mathematics
(generator validated on real graphs, see validate_quotient.py) and that the lex breaking is sound (Codish et al. 2013).
Usage: python3 cert_q.py <instance .in.json> <cadical_seconds>"""
import json, subprocess, sys, time, hashlib, os
from quotient_model import QModel, add_lex_twins
inst = json.load(open(sys.argv[1])); secs = int(sys.argv[2])
F = {tuple(e) for e in inst["edges"]}; key = [tuple(s) for s in inst["support"]]
types = ["T"] * 6 + ["I"] * 27; fixed = {}
for i in range(6):
    for j in range(i + 1, 6): fixed[(i, j)] = int((i, j) in F)
for Y, s in zip(range(6, 33), key):
    for i in range(6): fixed[(i, Y)] = s[i]
groups = {}
for Y, s in zip(range(6, 33), key): groups.setdefault(s, []).append(Y)
groups = [g for g in groups.values() if len(g) > 1]
QM = QModel(types, 14, fixed); cls, pool = QM.build_cnf(); add_lex_twins(QM, cls, pool, groups)
nv = max(abs(l) for c in cls for l in c)
os.makedirs("certs", exist_ok=True)
base = "certs/%s" % inst["name"]
with open(base + ".cnf", "w") as f:
    f.write("p cnf %d %d\n" % (nv, len(cls)))
    for c in cls: f.write(" ".join(map(str, c)) + " 0\n")
sha = hashlib.sha256(open(base + ".cnf", "rb").read()).hexdigest()
if len(sys.argv) > 3 and sys.argv[3] == 'gen':
    json.dump({'name': inst['name'], 'cnf_sha256': sha, 'vars': nv, 'clauses': len(cls)}, open(base + '.gen.json', 'w')); print('generated', base, sha[:16], nv, len(cls)); sys.exit(0)
t0 = time.time()
p = subprocess.run(["cadical", "-q", "--no-binary", "-t", str(secs), base + ".cnf", base + ".drat"], capture_output=True, text=True)
solve_s = time.time() - t0
status = "UNSAT" if p.returncode == 20 else ("SAT" if p.returncode == 10 else "UNKNOWN")
out = {"name": inst["name"], "cnf_sha256": sha, "vars": nv, "clauses": len(cls), "cadical": status, "solve_s": round(solve_s, 1)}
if status == "UNSAT":
    t1 = time.time()
    d = subprocess.run(["drat-trim", base + ".cnf", base + ".drat", "-t", "20000"], capture_output=True, text=True)
    out["drat_trim"] = "VERIFIED" if "s VERIFIED" in d.stdout else "NOT VERIFIED"
    out["check_s"] = round(time.time() - t1, 1)
    out["drat_tail"] = d.stdout.strip().splitlines()[-3:]
    if out["drat_trim"] == "VERIFIED": os.remove(base + ".drat")      # proofs are large; the CNF + hash are kept
json.dump(out, open(base + ".cert.json", "w"), indent=1)
print(json.dumps(out))
