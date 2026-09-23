"""Cube-and-conquer for a hard Stage-Q instance (research 2026-09-23).
Every independent orbit Z has exactly two doubles (Lemma entries (c)), so the cubes  {w_ZA = w_ZB = 1}, over all pairs {A, B} of
independent orbits different from Z, cover every solution of the CNF.  Base CNF = stageq_sym.full_cnf (lean encoding + twin lex + full
sigma lex), identical to the Stage-Q queue.  The instance is UNSAT iff every cube is UNSAT.  No pair is filtered out in advance (a cube
violating a proved necessary condition is simply refuted by the solver), so the cover is complete by construction.
Resumable: results appended to cubes/<name>/results.txt ("A B STATUS seconds").  SAT -> decoded and checked exactly.
Usage: python cube_q.py <name> <Z | auto> <seconds per cube> <parallel K>"""
import json, sys, os, itertools, subprocess, time, gc
from concurrent.futures import ThreadPoolExecutor
import stageq_sym as SQ

def lq_candidates(inst, Z):
    """number of orbits A that pass the LQ bound for a double with Z (only used to CHOOSE Z, never to drop cubes)."""
    F = [[0] * 6 for _ in range(6)]
    for a, b in inst["edges"]: F[a][b] = F[b][a] = 1
    S = [tuple(s) for s in inst["support"]]
    t = lambda s: [6 - 3 * s[i] - sum(F[i][k] * s[k] for k in range(6)) for i in range(6)]
    tZ = t(S[Z - 6]); ok = 0
    for A in range(6, 33):
        if A == Z: continue
        tA = t(S[A - 6])
        if all(2 * S[A - 6][i] <= tZ[i] and 2 * S[Z - 6][i] <= tA[i] for i in range(6)) and sum(x * y for x, y in zip(S[A - 6], S[Z - 6])) <= 4: ok += 1
    return ok

if __name__ == "__main__":
    name, zarg, secs, K = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    inst = json.load(open("stageQ_runs/%s.in.json" % name))
    Z = min(range(6, 33), key=lambda z: (lq_candidates(inst, z), z)) if zarg == "auto" else int(zarg)
    d = "cubes/%s" % name; os.makedirs(d, exist_ok=True)
    if not os.path.exists(d + "/base.gen.json"):
        QM, cls, pool, syms = SQ.full_cnf(inst)
        nv = max(abs(l) for c in cls for l in c)
        with open(d + "/base.cnf", "w") as f:
            f.write("p cnf %d %d\n" % (nv, len(cls)))
            for c in cls: f.write(" ".join(map(str, c)) + " 0\n")
        vm = {"%s,%d,%d" % k: v for k, v in pool.obj2id.items() if isinstance(k, tuple) and len(k) == 3 and k[0] in ("u", "w")}
        json.dump({"name": name, "vars": nv, "clauses": len(cls), "symmetries": len(syms), "varmap": vm}, open(d + "/base.gen.json", "w"))
        del QM, cls, pool; gc.collect()
    vm = json.load(open(d + "/base.gen.json"))["varmap"]
    wv = lambda a, b: vm["w,%d,%d" % (min(a, b), max(a, b))]
    others = [A for A in range(6, 33) if A != Z]
    cubes = list(itertools.combinations(others, 2))
    done = set()
    if os.path.exists(d + "/results.txt"):
        for line in open(d + "/results.txt"):
            p = line.split()
            if len(p) >= 3 and p[0] == "Z%d" % Z: done.add((int(p[1]), int(p[2])))
    todo = [c for c in cubes if c not in done]
    print("%s: Z=%d (LQ double candidates %d), cubes %d, already done %d" % (name, Z, lq_candidates(inst, Z), len(cubes), len(done)), flush=True)
    def run(c):
        A, B = c; out = "%s/cube_%d_%d_%d.out" % (d, Z, A, B); t0 = time.time()
        try: rc = subprocess.run(["python", "solve_stream.py", d + "/base.cnf", out, str(wv(Z, A)), str(wv(Z, B))], timeout=secs).returncode
        except subprocess.TimeoutExpired: rc = 0
        st = {10: "SAT", 20: "UNSAT"}.get(rc, "UNKNOWN")
        if st == "SAT":
            lits = set(int(x) for line in open(out) if line.startswith("v ") for x in line.split()[1:] if int(x) > 0)
            Q, ok = SQ.decode_check(inst, vm, lits); st += "(exact=%s)" % ok
            json.dump({"name": name, "Z": Z, "cube": [A, B], "Q": Q, "exact": ok}, open("%s/SAT_%d_%d_%d.json" % (d, Z, A, B), "w"))
        elif os.path.exists(out): os.remove(out)
        with open(d + "/results.txt", "a") as f: f.write("Z%d %d %d %s %.0f\n" % (Z, A, B, st, time.time() - t0))
        return st
    with ThreadPoolExecutor(K) as ex:
        res = list(ex.map(run, todo))
    allres = [line.split()[3] for line in open(d + "/results.txt") if line.startswith("Z%d " % Z)]
    n_uns = sum(r == "UNSAT" for r in allres); n_sat = sum(r.startswith("SAT") for r in allres); n_unk = len(allres) - n_uns - n_sat
    verdict = "UNSAT (all %d cubes)" % len(cubes) if n_uns == len(cubes) else ("SAT" if n_sat else "OPEN")
    print("%s Z=%d: cubes %d -> UNSAT %d, SAT %d, UNKNOWN %d => %s" % (name, Z, len(cubes), n_uns, n_sat, n_unk, verdict), flush=True)
