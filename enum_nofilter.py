"""AUDIT: re-enumerate the multisets WITHOUT the level-2.5 filters (type filter + triple condition), i.e. level 2 only, and compare the
resulting SUPPORT multisets with those used for Stage Q (enum_all.json). If the filters were wrong (too strong), extra supports appear."""
import json, sys, itertools
from ortools.sat.python import cp_model
exec(open("level2_phased.py", encoding="utf-8").read().split("def solve_case")[0])
classes = json.load(open("classes_reduced.json")); enum = {r["class"]: r for r in json.load(open("enum_all.json"))}
cap = float(sys.argv[1]); todo = [int(x) for x in sys.argv[2].split(",")]
for idx in todo:
    cls = classes[idx]; edges = [tuple(e) for e in cls["edges"]]
    R = residual(build_P(edges, cls["eps"]))
    md = cp_model.CpModel(); m = [md.NewIntVar(0, 27, "") for _ in COLS]
    md.Add(sum(m) == 27)
    for i in range(6):
        for j in range(i, 6):
            for k in (range(3) if i < j else (0,)):
                md.Add(sum(m[c] for c, (s, p) in enumerate(COLS) if s[i] and s[j] and (p[j] - p[i]) % 3 == k) == R[3 * i][3 * j + k])
    supports = set(); n = [0]
    class CB(cp_model.CpSolverSolutionCallback):
        def __init__(s): super().__init__()
        def on_solution_callback(s):
            n[0] += 1
            ms = [COLS[c][0] for c in range(len(COLS)) for _ in range(s.Value(m[c])) if any(COLS[c][0])]
            supports.add(tuple(sorted(ms + [(0,) * 6] * (27 - len(ms)))))
    sv = cp_model.CpSolver(); sv.parameters.enumerate_all_solutions = True; sv.parameters.num_workers = 1; sv.parameters.max_time_in_seconds = cap
    st = sv.Solve(md, CB())
    used = set(tuple(map(tuple, s)) for s in enum[idx]["supports"])
    print("class %2d mask %5d: level-2 only -> %d phased multisets (complete=%s), %d supports | with filters: %d supports | extra supports without filters: %d | missing: %d"
          % (idx, cls["mask"], n[0], sv.StatusName(st) == "OPTIMAL", len(supports), len(used), len(supports - used), len(used - supports)), flush=True)
