"""Enumerate, for ONE phase class c of F, the support multisets that are BOTH
   (i)  compatible with the linear content LQ (enum_supports_lq.build: sorted supports + C + G0, TY, row, dbl, L1, C3), and
   (ii) realized by a level-2.5 phased B of class c (support_phase_check.realizable: 27 phased columns, exact residual, type filter,
        triple condition), with the support multiset of B equal to (i)'s multiset.
Every C3 graph whose class (in a representative labelling) is c has its support multiset in this list, so the list replaces
enum_supports_lq + support_phase_check for class c.  Each found multiset is blocked (support vector, canonical since sorted);
INFEASIBLE at the end => complete list.  Research 2026-09-23.
Usage: python enum_supports_phased.py <class index> <seconds per solve> <max solutions> [workers]"""
import json, sys, time, itertools
from ortools.sat.python import cp_model
exec(open("level25.py", encoding="utf-8").read().split("def solve25")[0])        # COLS, build_P, residual, eps_map, type_ok
from enum_supports_lq import build

def model(edges, eps):
    md, x = build(edges); u, w, code = md.uw; n = 27
    R = residual(build_P(edges, eps))
    if any(R[a][b] < 0 for a in range(18) for b in range(18)): return None, None
    e = eps_map(edges, eps)
    allowed = [c for c, (s, p) in enumerate(COLS) if type_ok(s, p, e)]
    m = {c: md.NewIntVar(0, 27, "") for c in allowed}
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
    # link: number of phased columns with support code v  ==  number of sorted supports equal to v
    bY = [[md.NewBoolVar("") for v in range(64)] for Y in range(n)]
    for Y in range(n):
        md.AddExactlyOne(bY[Y]); md.Add(code[Y] == sum(v * bY[Y][v] for v in range(64)))
    codeof = lambda s: sum(s[i] << (5 - i) for i in range(6))
    for v in range(64):
        md.Add(sum(m[c] for c in allowed if codeof(COLS[c][0]) == v) == sum(bY[Y][v] for Y in range(n)))
    return md, x

if __name__ == "__main__":
    idx, secs, cap = int(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3]); workers = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    cl = json.load(open("classes_reduced.json"))[idx]
    md, x = model([tuple(e) for e in cl["edges"]], cl["eps"])
    found = []; status = "?"; t0 = time.time()
    if md is None: status = "R_NEGATIVE"
    else:
        while len(found) < cap:
            sv = cp_model.CpSolver(); sv.parameters.num_workers = workers; sv.parameters.max_time_in_seconds = secs
            st = sv.StatusName(sv.Solve(md))
            if st not in ("OPTIMAL", "FEASIBLE"): status = st; break
            vec = [[sv.Value(x[Y][i]) for i in range(6)] for Y in range(27)]
            found.append(["".join(map(str, r)) for r in vec])
            md.AddBoolOr([(x[Y][i].Not() if vec[Y][i] else x[Y][i]) for Y in range(27) for i in range(6)])
            print("class %d (mask %d): multiset #%d found (%.0fs)" % (idx, cl["mask"], len(found), time.time() - t0), flush=True)
            json.dump({"class": idx, "mask": cl["mask"], "status": "PARTIAL", "complete": False, "supports": found}, open("enum_supports_phased_c%d.json" % idx, "w"))
        else:
            status = "CAP"
    print("class %d (mask %d): END status=%s, LQ+phase multisets: %d, complete=%s, %.0fs" % (idx, cl["mask"], status, len(found), status in ("INFEASIBLE", "R_NEGATIVE"), time.time() - t0), flush=True)
    json.dump({"class": idx, "mask": cl["mask"], "status": status, "complete": status in ("INFEASIBLE", "R_NEGATIVE"), "supports": found}, open("enum_supports_phased_c%d.json" % idx, "w"))
