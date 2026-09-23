"""Invariant ansatz for a Stage-Q instance (research 2026-09-23): look for a quotient matrix Q with Q^sigma = Q for a chosen symmetry sigma
of the instance (stageq_sym.symmetries).  SAT => Stage Q is SAT for this instance (the model is exactly Stage Q + equalities; decoded and
checked exactly).  UNSAT => only 'no sigma-invariant solution' (says nothing in general).  No lex constraints here (they would conflict
with the invariance).  Usage: python ansatz_q.py <name> <seconds per sigma> [max sigmas]"""
import json, sys, multiprocessing as mp, queue, time
from quotient_model import QModel
from lean_encoding import build_cnf_lean
from stageq_sym import symmetries, decode_check

def order(full):
    k, cur = 1, list(full)
    while cur != list(range(len(full))): cur = [full[x] for x in cur]; k += 1
    return k

def work(cls, q):
    from pysat.solvers import Solver
    with Solver(name="cadical195", bootstrap_with=cls) as s:
        r = s.solve(); q.put((r, [l for l in s.get_model() if l > 0] if r else None))

if __name__ == "__main__":
    name, secs = sys.argv[1], float(sys.argv[2]); cap = int(sys.argv[3]) if len(sys.argv) > 3 else 99
    inst = json.load(open("stageQ_runs/%s.in.json" % name))
    F = {tuple(e) for e in inst["edges"]}; key = [tuple(s) for s in inst["support"]]
    types = ["T"] * 6 + ["I"] * 27; fixed = {}
    for i in range(6):
        for j in range(i + 1, 6): fixed[(i, j)] = int((i, j) in F)
    for Y, s in zip(range(6, 33), key):
        for i in range(6): fixed[(i, Y)] = s[i]
    syms = symmetries([tuple(e) for e in inst["edges"]], key)
    fulls = [list(pi) + [6 + s for s in sig] for pi, sig in syms]
    def ctype(f):                                   # cycle type of the permutation of the 33 orbits
        seen, lens = set(), []
        for a in range(33):
            if a in seen: continue
            k, x = 0, a
            while x not in seen: seen.add(x); x = f[x]; k += 1
            lens.append(k)
        return tuple(sorted(lens))
    reps = {}
    for f in fulls: reps.setdefault((order(f), ctype(f)), f)
    pref = {3: 0, 2: 1, 4: 2, 6: 3}
    chosen = [reps[k] for k in sorted(reps, key=lambda k: (pref.get(k[0], 9), -len(k[1])))][:cap]
    for full in chosen:
        QM = QModel(types, 14, fixed); cls, pool = build_cnf_lean(QM)
        for a in range(6, 33):
            for b in range(a + 1, 33):
                x, y = sorted((full[a], full[b]))
                for k in ("u", "w"):
                    p, r = pool.id((k, a, b)), pool.id((k, x, y))
                    if p != r: cls += [[-p, r], [p, -r]]
        import subprocess, gc, os
        vm = {"%s,%d,%d" % k: v for k, v in pool.obj2id.items() if isinstance(k, tuple) and len(k) == 3 and k[0] in ("u", "w")}
        nv = max(abs(l) for c in cls for l in c); cnf = "/tmp/ansatz.cnf"; out = "/tmp/ansatz.out"
        with open(cnf, "w") as f:
            f.write("p cnf %d %d\n" % (nv, len(cls)))
            for c in cls: f.write(" ".join(map(str, c)) + " 0\n")
        del cls, QM; gc.collect(); t0 = time.time()
        try: rc = subprocess.run(["python", "solve_stream.py", cnf, out], timeout=secs).returncode
        except subprocess.TimeoutExpired: rc = 0
        r = True if rc == 10 else (False if rc == 20 else None); mdl = None
        if r: mdl = [int(x) for line in open(out) if line.startswith("v ") for x in line.split()[1:] if int(x) > 0]
        os.remove(cnf)
        res = "SAT" if r else ("UNSAT" if r is False else "UNKNOWN")
        line = "%s sigma order %d: %s (%.0fs)" % (name, order(full), res, time.time() - t0)
        if r:
            Q, ok = decode_check(inst, vm, set(mdl)); line += " exact check Q^2+Q=12I+6J: %s" % ok
            json.dump({"name": name, "sigma": full, "Q": Q, "exact": ok}, open("ansatz_%s.json" % name, "w"))
        print(line, flush=True)
        if r: break
