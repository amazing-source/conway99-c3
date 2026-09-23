"""Incremental cube-and-conquer for a Stage-Q instance (research 2026-09-23): same cubes and same base CNF as cube_q.py, but ONE solver
per instance (base CNF streamed once), each cube solved under ASSUMPTIONS [w_ZA, w_ZB] with a conflict budget (learned clauses, all
implied by the base CNF, are reused across cubes).  Pass 1 with budget B, pass 2 with 10 B, then every undecided cube is SPLIT
(depth <= 4) on the second double of an orbit that has exactly one assumed double (25 children, complete cover since every independent
orbit has exactly two doubles); children at 10 B, leaves at 30 B.  --relaxed: validation mode on the relaxed CNF (cubes/<name>_relaxed).
UNSAT under assumptions == base CNF + the two units is UNSAT.  Results appended to cubes/<name>/results.txt as "Z A B STATUS secs inc".
Usage: python cube_q_inc.py <name> <Z | auto> <conflict budget B> [only-first-N cubes, for validation]"""
import json, sys, os, itertools, time, gc
from pysat.solvers import Solver
import stageq_sym as SQ
from cube_q import lq_candidates

if __name__ == "__main__":
    relaxed = "--relaxed" in sys.argv; from_split = "--from-split" in sys.argv; args = [a for a in sys.argv[1:] if not a.startswith("--")]
    name, zarg, B = args[0], args[1], int(args[2]); firstN = int(args[3]) if len(args) > 3 else None
    inst = json.load(open("stageQ_runs/%s.in.json" % name))
    Z = min(range(6, 33), key=lambda z: (lq_candidates(inst, z), z)) if zarg == "auto" else int(zarg)
    d = "cubes/%s%s" % (name, "_relaxed" if relaxed else ""); os.makedirs(d, exist_ok=True)
    from_split = from_split or os.path.exists(d + "/FROM_SPLIT")          # marker: remaining cubes already failed passes 1-2
    if not os.path.exists(d + "/base.cnf"):              # fresh clone: base.cnf is not in git; regenerate it and check its SHA-256
        import hashlib
        QM, cls, pool, syms = SQ.full_cnf(inst, relaxed)
        nv = max(abs(l) for c in cls for l in c)
        with open(d + "/base.cnf", "w", newline="\n") as f:
            f.write("p cnf %d %d\n" % (nv, len(cls)))
            for c in cls: f.write(" ".join(map(str, c)) + " 0\n")
        sha = hashlib.sha256(open(d + "/base.cnf", "rb").read()).hexdigest()
        vm = {"%s,%d,%d" % k: v for k, v in pool.obj2id.items() if isinstance(k, tuple) and len(k) == 3 and k[0] in ("u", "w")}
        if os.path.exists(d + "/base.gen.json"):
            old = json.load(open(d + "/base.gen.json"))
            if old.get("cnf_sha256") and old["cnf_sha256"] != sha:
                sys.exit("REGENERATED CNF DIFFERS from the recorded one (%s != %s): stop, results.txt refers to another CNF" % (sha[:16], old["cnf_sha256"][:16]))
            if old["varmap"] != vm: sys.exit("REGENERATED VARIABLE MAP DIFFERS: stop")
        json.dump({"name": name, "vars": nv, "clauses": len(cls), "symmetries": len(syms), "varmap": vm, "cnf_sha256": sha}, open(d + "/base.gen.json", "w"))
        del QM, cls, pool; gc.collect()
    vm = json.load(open(d + "/base.gen.json"))["varmap"]
    wv = lambda a, b: vm["w,%d,%d" % (min(a, b), max(a, b))]
    cubes = list(itertools.combinations([A for A in range(6, 33) if A != Z], 2))
    if firstN: cubes = cubes[:firstN] if firstN > 0 else cubes[firstN:]          # validation: first N or last |N| cubes
    resfile = d + ("/results_incval.txt" if firstN else "/results.txt")
    done = set()
    if os.path.exists(resfile):
        for line in open(resfile):
            p = line.split()
            if len(p) >= 4 and p[0] == "Z%d" % Z and p[3] in ("UNSAT",) or (len(p) >= 4 and p[3].startswith("SAT")): done.add((int(p[1]), int(p[2])))
    todo = [c for c in cubes if c not in done]
    t0 = time.time()
    with Solver(name="cadical195") as s:
        with open(d + "/base.cnf") as f:
            for line in f:
                if line[0] in "pc": continue
                s.add_clause([int(x) for x in line.split()[:-1]])
        print("%s: Z=%d, cubes %d, to do %d, base loaded in %.0fs" % (name, Z, len(cubes), len(todo), time.time() - t0), flush=True)
        def attempt(edges, budget):
            """edges: assumed doubles (pairs).  Returns 'UNSAT' | 'SAT...' | None (budget exhausted)."""
            s.conf_budget(budget)
            r = s.solve_limited(assumptions=[wv(a, b) for a, b in edges])
            if r is True:
                lits = set(l for l in s.get_model() if l > 0)
                Q, ok = SQ.decode_check(inst, vm, lits)
                json.dump({"name": name, "Z": Z, "edges": edges, "Q": Q, "exact": ok}, open("%s/SAT_%s.json" % (d, "_".join("%d-%d" % e for e in edges)), "w"))
                return "SAT(exact=%s)" % ok
            return "UNSAT" if r is False else None

        def split(edges, budget, depth):
            """Every independent orbit has exactly two doubles: pick an orbit V with exactly one assumed double (partner P);
            its second double W ranges over all independent orbits except V and P -> children cover the node completely."""
            deg = {}
            for a, b in edges: deg[a] = deg.get(a, 0) + 1; deg[b] = deg.get(b, 0) + 1
            V = next((v for a, b in edges for v in (b, a) if deg[v] == 1), None)
            if V is None or depth == 0:
                r = attempt(edges, 3 * budget); log(edges, r, 3 * budget); return r or "UNKNOWN"
            P = next(b if a == V else a for a, b in edges if V in (a, b))
            out = "UNSAT"
            for W in range(6, 33):
                if W in (V, P): continue
                child = edges + [(V, W)]
                r = attempt(child, budget)
                if r is None: r = split(child, budget, depth - 1)
                else: log(child, r, budget)
                if r.startswith("SAT"): return r
                if r != "UNSAT": out = "UNKNOWN"
            return out

        def log(edges, r, budget):
            with open(d + "/subcubes.txt", "a") as f: f.write("%s %s b=%d\n" % (" ".join("%d-%d" % e for e in edges), r or "UNKNOWN", budget))

        for budget in (("split",) if from_split else (B, 10 * B, "split")):          # --from-split: remaining cubes already failed 10 B
            left = []
            for (A, Bc) in todo:
                t1 = time.time()
                if budget == "split":
                    st = split([(Z, A), (Z, Bc)], 10 * B, 4); tag = "inc-split b=%d" % (10 * B)
                else:
                    st = attempt([(Z, A), (Z, Bc)], budget); tag = "inc b=%d" % budget
                if st is None: left.append((A, Bc)); continue
                with open(resfile, "a") as f: f.write("Z%d %d %d %s %.1f %s\n" % (Z, A, Bc, st, time.time() - t1, tag))
            print("%s: pass %s -> %d undecided (%.0fs)" % (name, budget, len(left), time.time() - t0), flush=True)
            todo = left
            if not todo: break
    res = {}
    for line in open(resfile):
        p = line.split()
        if len(p) >= 4 and p[0] == "Z%d" % Z:
            k = (int(p[1]), int(p[2])); st = p[3]
            if st.startswith("SAT") or res.get(k) is None or (st == "UNSAT" and not res[k].startswith("SAT")): res[k] = st
    n_uns = sum(1 for c in cubes if res.get(c) == "UNSAT"); n_sat = sum(1 for c in cubes if res.get(c, "").startswith("SAT"))
    verdict = "UNSAT (all %d cubes)" % len(cubes) if n_uns == len(cubes) else ("SAT" if n_sat else "OPEN")
    print("%s Z=%d: cubes %d -> UNSAT %d, SAT %d, other %d => %s (%.0fs)" % (name, Z, len(cubes), n_uns, n_sat, len(cubes) - n_uns - n_sat, verdict, time.time() - t0), flush=True)
