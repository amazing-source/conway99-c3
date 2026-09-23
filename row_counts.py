"""How constrained is one row of C?  For a Stage-Q instance, count for each independent orbit Z the LABELLED rows c in {0,1,2}^{26}
(other orbits) with: two entries 2, (10-|s_Z|) entries 1, sum_Y c_Y s_Y = t_Z, and entrywise s_Y(i) c_Y <= t_Z(i).
Counting is done over support TYPES with binomial multiplicities (exact integers).  Decides whether a row-by-row orderly generator is viable."""
import json, sys
from math import comb
from functools import lru_cache

def row_count(S, t, Z):
    others = [Y for Y in range(len(S)) if Y != Z]
    types = {}
    for Y in others: types[S[Y]] = types.get(S[Y], 0) + 1
    tl = sorted(types.items()); target = tuple(t[Z]); ns = 10 - sum(S[Z])
    @lru_cache(maxsize=None)
    def rec(k, rem, n1, n2):
        if n1 < 0 or n2 < 0 or min(rem) < 0: return 0
        if k == len(tl): return 1 if (n1 == 0 and n2 == 0 and max(rem) == 0) else 0
        s, mult = tl[k]; total = 0
        ok1 = all(s[i] * 1 <= target[i] for i in range(6)); ok2 = all(s[i] * 2 <= target[i] for i in range(6))
        for a in range(0, (min(mult, n2) if ok2 else 0) + 1):              # a columns of this type get value 2
            for b in range(0, (min(mult - a, n1) if ok1 else 0) + 1):      # b columns get value 1
                used = 2 * a + b
                nr = tuple(rem[i] - used * s[i] for i in range(6))
                sub = rec(k + 1, nr, n1 - b, n2 - a)
                if sub: total += comb(mult, a) * comb(mult - a, b) * sub
        return total
    return rec(0, target, ns, 2)

if __name__ == "__main__":
    for name in sys.argv[1:]:
        d = json.load(open("stageQ_runs/%s.in.json" % name)); F = [[0] * 6 for _ in range(6)]
        for a, b in d["edges"]: F[a][b] = F[b][a] = 1
        S = [tuple(s) for s in d["support"]]
        t = [[6 - 3 * s[i] - sum(F[i][k] * s[k] for k in range(6)) for i in range(6)] for s in S]
        counts = [row_count(S, t, Z) for Z in range(len(S))]
        import math
        print("%s: rows per orbit min=%d max=%d ; log10(product)=%.1f ; per orbit: %s" % (name, min(counts), max(counts),
              sum(math.log10(c) for c in counts if c), counts))
