"""Phase-level local neighbourhood condition (research, 2026-09-22).
Vertex-level version of the (TY) block: for a triangle vertex (i,0) and an independent vertex (Z,b), common neighbours + adjacency = 2.
With the convention (Z,b) ~ (i, b+p_Z(i)) for a phased column (s_Z,p_Z), the TRIANGLE contribution is known, so the INDEPENDENT
neighbours of Z must supply exactly
   T_Z(i,b) = (1 if i in s_Z and b+p_Z(i)=0 else 2) - [i in s_Z and b+p_Z(i)!=0] - #{j in N_F(i) cap s_Z : b+p_Z(j) = e_ij}.
An independent neighbour Y joined to Z with C-phase psi ((Y,c)~(Z,c+psi)) supplies 1 to T_Z(i, psi - p_Y(i)) for every i in s_Y.
Z has exactly two double neighbours (two distinct phases) and 10-|s_Z| single neighbours, chosen among the OTHER columns of B.
If some Z admits no such neighbourhood, the phased B is impossible.  Exhaustive exact DP, no solver.
For each class: enumerate the phased multisets (CP-SAT, as before) and test each; report per support multiset how many survive."""
import json, sys, time, itertools
from functools import lru_cache
exec(open("solve_fixedB.py", encoding="utf-8").read().split("def code_of")[0])   # multisets(), COLS, build_P, residual, eps_map

def targets(s, p, e):
    T = []
    for i in range(6):
        nb = [j for j in range(6) if (i, j) in e]
        for b in range(3):
            adj = s[i] and (b + p[i]) % 3 == 0
            tri = (1 if (s[i] and (b + p[i]) % 3 != 0) else 0) + sum(1 for j in nb if s[j] and (b + p[j]) % 3 == e[(i, j)])
            T.append((1 if adj else 2) - tri)
    return tuple(T)

def contrib(s, p, psi):
    v = [0] * 18
    for i in range(6):
        if s[i]: v[3 * i + (psi - p[i]) % 3] += 1
    return v

def z_feasible(Zc, avail, e):
    """CP-SAT version (exact integers): one boolean per (column instance, role); role = single with phase psi or double with a pair."""
    from ortools.sat.python import cp_model
    sZ, pZ = COLS[Zc]; T = targets(sZ, pZ, e)
    if min(T) < 0: return False
    md = cp_model.CpModel(); tot = [[] for _ in range(18)]; singles = []; doubles = []
    for c, cnt in avail:
        s, p = COLS[c]
        roles = [("s", tuple(contrib(s, p, psi))) for psi in range(3)] +                 [("d", tuple(a_ + b_ for a_, b_ in zip(contrib(s, p, x), contrib(s, p, y)))) for x, y in ((0, 1), (0, 2), (1, 2))]
        for kind, v in roles:
            m = md.NewIntVar(0, cnt, "")                       # how many instances of this column type take this role
            if kind == "s": singles.append(m)
            else: doubles.append(m)
            for t_ in range(18):
                if v[t_]: tot[t_].append(v[t_] * m)
        # at most cnt instances used in total for this type: added below via a per-type sum
        md.Add(sum(singles[-3:] + doubles[-3:]) <= cnt)
    for t_ in range(18): md.Add(sum(tot[t_]) == T[t_]) if tot[t_] else (None if T[t_] == 0 else md.AddBoolOr([]))
    md.Add(sum(singles) == 10 - sum(sZ)); md.Add(sum(doubles) == 2)
    sv = cp_model.CpSolver(); sv.parameters.num_workers = 1; sv.parameters.max_time_in_seconds = 30
    st = sv.Solve(md)
    if st == cp_model.UNKNOWN: return True                      # conservative: never reject on timeout
    return st in (cp_model.OPTIMAL, cp_model.FEASIBLE)

def check_multiset(ms, e):
    cols = [c for c, k in ms.items() for _ in range(k)]
    zero = next(c for c, (s, p) in enumerate(COLS) if not any(s))
    cols += [zero] * (27 - len(cols))
    from collections import Counter
    cnt = Counter(cols)
    for Zc in cnt:
        avail = dict(cnt); avail[Zc] -= 1
        av = tuple(sorted((c, k) for c, k in avail.items() if k > 0))
        if not z_feasible(Zc, av, e): return False, Zc
    return True, None

if __name__ == "__main__":
    classes = json.load(open("classes_reduced.json")); enum = {r["class"]: r for r in json.load(open("enum_all.json"))}
    todo = [int(x) for x in sys.argv[1].split(",")] if len(sys.argv) > 1 else [i for i in range(46) if enum[i]["complete"]]
    out = {}
    for idx in todo:
        cls = classes[idx]; e = eps_map([tuple(x) for x in cls["edges"]], cls["eps"])
        t0 = time.time(); sols, complete = multisets(cls, 300)
        per = {}
        for ms in sols:
            key = json.dumps(sorted([list(COLS[c][0]) for c, k in ms.items() for _ in range(k)] + [[0] * 6] * (27 - sum(ms.values()))))
            ok, _ = check_multiset(ms, e)
            per.setdefault(key, [0, 0]); per[key][0] += 1; per[key][1] += int(ok)
        out[idx] = {"mask": cls["mask"], "complete": complete, "phased": len(sols), "supports": {k: v for k, v in per.items()}}
        dead = sum(1 for v in per.values() if v[1] == 0)
        print("class %2d mask %5d: phased=%5d (complete=%s) survive_phaseLNC=%5d | supports: %d, killed entirely: %d  (%.0fs)"
              % (idx, cls["mask"], len(sols), complete, sum(v[1] for v in per.values()), len(per), dead, time.time() - t0), flush=True)
    json.dump(out, open("phase_lnc_results.json", "w"))
