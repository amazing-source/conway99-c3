"""Is the infeasibility LOCAL?  For each independent orbit Z separately (no symmetry coupling between rows), decide whether a row
c in {0,1,2}^(other 26) exists with:  exactly two entries 2;  sum_Y c_Y = 14 - |s_Z|;  sum_Y c_Y s_Y = t_Z;  s_Y(i) c_Y <= t_Z(i).
Exhaustive exact search over column TYPES (multiset counting), no solver.  A Z with no feasible row kills the instance with a
one-line certificate.  Also reports, when every row is locally feasible, that the infeasibility is global (needs symmetry)."""
import json, glob, itertools
from functools import lru_cache

def local_rows(S, t, Z):
    others = [Y for Y in range(len(S)) if Y != Z]
    target = tuple(t[Z]); need_sum = 14 - sum(S[Z])
    # group identical columns: counts per support type (only supports matter for this row)
    types = {}
    for Y in others: types[S[Y]] = types.get(S[Y], 0) + 1
    tl = sorted(types.items())
    # allowed values per type from entrywise bounds
    def allowed(s):
        vals = []
        for c in (0, 1, 2):
            if all(s[i] * c <= target[i] for i in range(6)): vals.append(c)
        return vals
    @lru_cache(maxsize=None)
    def rec(k, rem, cnt, twos):
        if any(x < 0 for x in rem) or cnt < 0 or twos < 0: return False
        if k == len(tl): return all(x == 0 for x in rem) and cnt == 0 and twos == 0
        s, mult = tl[k]; al = allowed(s)
        # choose how many of this type get value 2, 1 (rest 0)
        for n2 in range(0, min(mult, twos) + 1 if 2 in al else 1):
            for n1 in range(0, mult - n2 + 1 if 1 in al else 1):
                used = 2 * n2 + n1
                nr = tuple(rem[i] - used * s[i] for i in range(6))
                if rec(k + 1, nr, cnt - used, twos - n2): return True
        return False
    return rec(0, target, need_sum, 2)

res = {}
for f in sorted(glob.glob("stageQ_runs/*.in.json")):
    d = json.load(open(f)); F = [[0] * 6 for _ in range(6)]
    for a, b in d["edges"]: F[a][b] = F[b][a] = 1
    S = [tuple(s) for s in d["support"]]
    t = [[6 - 3 * s[i] - sum(F[i][k] * s[k] for k in range(6)) for i in range(6)] for s in S]
    bad = [Z for Z in range(len(S)) if not local_rows(S, t, Z)]
    res[d["name"]] = bad
    print("%-14s rows with NO feasible neighbourhood: %s" % (d["name"], ["Z=%d s=%s t=%s" % (Z, "".join(map(str, S[Z])), t[Z]) for Z in bad[:2]] or "none"))
json.dump({k: v for k, v in res.items()}, open("lq_local_results.json", "w"))
