"""Phase realizability of a support multiset (research 2026-09-23): for a Stage-Q instance (F, support multiset) and every phase class of F
(classes_reduced.json with this mask), is there a level-2.5 phased multiset whose supports are EXACTLY this multiset?
(level 2 = exact triangle residual decomposition, + type filter + triple condition, all proved).  If no class admits one, the support
multiset cannot occur in any C3 graph, without any Stage-Q computation.  Usage: python support_phase_check.py name1 name2 ..."""
import json, sys, itertools
from collections import Counter
from ortools.sat.python import cp_model
exec(open("level25.py", encoding="utf-8").read().split("def solve25")[0])        # COLS, build_P, residual, eps_map, type_ok

def realizable(edges, eps, support_counts, secs=120):
    P = build_P(edges, eps); R = residual(P)
    if any(R[u][v] < 0 for u in range(18) for v in range(18)): return False
    e = eps_map(edges, eps)
    allowed = [c for c, (s, p) in enumerate(COLS) if type_ok(s, p, e)]
    md = cp_model.CpModel(); m = {c: md.NewIntVar(0, 27, "") for c in allowed}
    md.Add(sum(m.values()) == 27)
    for i in range(6):
        for j in range(i, 6):
            for k in (range(3) if i < j else (0,)):
                md.Add(sum(m[c] for c in allowed if COLS[c][0][i] and COLS[c][0][j] and (COLS[c][1][j] - COLS[c][1][i]) % 3 == k) == R[3 * i][3 * j + k])
    for T in itertools.combinations(range(6), 3):
        i, j, l = T
        for r in itertools.product(range(3), repeat=2):
            terms = [m[c] for c in allowed if all(COLS[c][0][t] for t in T) and (COLS[c][1][j] - COLS[c][1][i]) % 3 == r[0] and (COLS[c][1][l] - COLS[c][1][i]) % 3 == r[1]]
            if terms: md.Add(sum(terms) <= 1)
    for s, k in support_counts.items():                      # exact support multiset (zero column included)
        md.Add(sum(m[c] for c in allowed if COLS[c][0] == s) == k)
    for s in set(COLS[c][0] for c in allowed) - set(support_counts):
        md.Add(sum(m[c] for c in allowed if COLS[c][0] == s) == 0)
    sv = cp_model.CpSolver(); sv.parameters.num_workers = 1; sv.parameters.max_time_in_seconds = secs
    st = sv.Solve(md)
    return None if st == cp_model.UNKNOWN else st in (cp_model.OPTIMAL, cp_model.FEASIBLE)

if __name__ == "__main__":
    classes = json.load(open("classes_reduced.json"))
    for name in sys.argv[1:]:
        d = json.load(open("stageQ_runs/%s.in.json" % name))
        counts = Counter(tuple(s) for s in d["support"])
        res = []
        for idx, cls in enumerate(classes):
            if cls["mask"] != d["mask"]: continue
            res.append((idx, realizable([tuple(x) for x in cls["edges"]], cls["eps"], counts)))
        verdict = "REALIZABLE" if any(r is True for _, r in res) else ("UNKNOWN" if any(r is None for _, r in res) else "DEAD (no phase class realizes it)")
        print("%-14s classes %s -> %s" % (name, res, verdict), flush=True)
