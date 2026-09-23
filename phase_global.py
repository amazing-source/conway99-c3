"""Global phase-level linear test ("Stage Q+ linear", research 2026-09-23).
For one class (F, eps) and one phased multiset B (columns assigned to orbits 0..26 in a fixed order), decide whether the 27x27 block C
(values 0/1/2 AND phases) can satisfy, simultaneously for all independent orbits Z and all (i,b):
    sum over neighbours Y of contrib(Y, psi_YZ)[i,b] = T_Z(i,b)          (vertex-level triangle x independent block, exact)
with C symmetric (a single with phase psi seen from Y is a single with phase -psi seen from Z; a double {x,y} becomes {-x,-y}),
exactly two doubles and 10-|s_Z| singles per row.  All quadratic (independent x independent) equations are dropped.
UNSAT for every phased multiset with a given support multiset  =>  that Stage-Q problem is impossible.
Role variables per unordered pair {Y,Z}: r[Y,Z,k], k in 0..5 = single psi in {0,1,2} (from Y to Z) or double missing-phase m in {0,1,2}."""
import json, sys, time
from ortools.sat.python import cp_model
exec(open("phase_lnc.py", encoding="utf-8").read().split('if __name__')[0])

def global_feasible(ms, e, secs=60, tgt=None, cnt=None, cols_override=None):
    cols = [c for c, k in ms.items() for _ in range(k)]
    zero = next(c for c, (s, p) in enumerate(COLS) if not any(s))
    cols += [zero] * (27 - len(cols)); n = 27
    if cols_override is not None: cols = list(cols_override)
    md = cp_model.CpModel(); r = {}
    for Y in range(n):
        for Z in range(Y + 1, n):
            r[Y, Z] = [md.NewBoolVar("") for _ in range(6)]
            md.Add(sum(r[Y, Z]) <= 1)
    def roles_from(Y, Z):
        """list of (bool, psi_set as seen from Y towards Z)."""
        if Y < Z:
            v = r[Y, Z]; return [(v[k], {k}) for k in range(3)] + [(v[3 + m], set(range(3)) - {m}) for m in range(3)]
        v = r[Z, Y]   # stored from Z to Y: psi(Z->Y) = q  <=>  psi(Y->Z) = -q
        return [(v[k], {(-k) % 3}) for k in range(3)] + [(v[3 + m], {(-q) % 3 for q in set(range(3)) - {m}}) for m in range(3)]
    for Z in range(n):
        sZ, pZ = COLS[cols[Z]]; T = targets(sZ, pZ, e) if tgt is None else tgt[Z]
        if min(T) < 0: return False
        acc = [[] for _ in range(18)]; sing = []; dbl = []
        for Y in range(n):
            if Y == Z: continue
            s, p = COLS[cols[Y]]
            for bvar, psis in roles_from(Y, Z):
                vec = [0] * 18
                for psi in psis:
                    for t_, x in enumerate(contrib(s, p, psi)): vec[t_] += x
                for t_ in range(18):
                    if vec[t_]: acc[t_].append(vec[t_] * bvar)
                (sing if len(psis) == 1 else dbl).append(bvar)
        for t_ in range(18):
            if acc[t_]: md.Add(sum(acc[t_]) == T[t_])
            elif T[t_] != 0: return False
        ns_, nd_ = (10 - sum(sZ), 2) if cnt is None else cnt[Z]
        md.Add(sum(sing) == ns_); md.Add(sum(dbl) == nd_)
    sv = cp_model.CpSolver(); sv.parameters.num_workers = 1; sv.parameters.max_time_in_seconds = secs
    st = sv.Solve(md)
    if st == cp_model.UNKNOWN: return None
    return st in (cp_model.OPTIMAL, cp_model.FEASIBLE)

if __name__ == "__main__":
    classes = json.load(open("classes_reduced.json"))
    todo = [int(x) for x in sys.argv[1].split(",")]; secs = float(sys.argv[2]) if len(sys.argv) > 2 else 60
    out = {}
    for idx in todo:
        cls = classes[idx]; e = eps_map([tuple(x) for x in cls["edges"]], cls["eps"])
        t0 = time.time(); sols, complete = multisets(cls, 300); per = {}
        for ms in sols:
            key = json.dumps(sorted([list(COLS[c][0]) for c, k in ms.items() for _ in range(k)] + [[0] * 6] * (27 - sum(ms.values()))))
            res = global_feasible(ms, e, secs)
            per.setdefault(key, {"phased": 0, "feasible": 0, "unknown": 0}); per[key]["phased"] += 1
            per[key]["feasible"] += int(res is True); per[key]["unknown"] += int(res is None)
        out[idx] = {"mask": cls["mask"], "complete": complete, "supports": per}
        dead = sum(1 for v in per.values() if v["feasible"] == 0 and v["unknown"] == 0)
        print("class %2d mask %5d: phased=%5d complete=%s | per support [phased/feasible/unknown]: %s | supports killed: %d/%d (%.0fs)"
              % (idx, cls["mask"], len(sols), complete, [(v["phased"], v["feasible"], v["unknown"]) for v in per.values()], dead, len(per), time.time() - t0), flush=True)
    json.dump(out, open("phase_global_%s.json" % sys.argv[1].replace(",", "_")[:40], "w"))
