import json, sys
from ortools.sat.python import cp_model
import solve_class as sc
src = open("solve_class.py", encoding="utf-8").read()
# rebuild without gauge fixing and ordering
code = src.split("    # gauge fixing")[0] + "    return M, md, var\n"
ns = {}; exec(code.split('if __name__')[0], ns)
classes = json.load(open("classes_reduced.json")); idx = int(sys.argv[1])
M, md, var = ns["build"](classes[idx])
sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = float(sys.argv[2]); sv.parameters.num_workers = int(sys.argv[3])
st = sv.Solve(md)
print(idx, classes[idx]["mask"], classes[idx]["eps"], "NO SYMMETRY BREAKING ->", sv.StatusName(st), "t=%.1fs conflicts=%d" % (sv.WallTime(), sv.NumConflicts()))
