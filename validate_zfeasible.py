"""Planted-solution control for phase_lnc.z_feasible: build a random VALID neighbourhood (2 doubles with distinct phases, 10-|s_Z| singles)
from random available columns, compute the target it produces, force z_feasible to use that target: it must answer True.
Negative control: add +1 to one target entry whose row sum is already fixed by the counts: must answer False."""
import random
exec(open("phase_lnc.py", encoding="utf-8").read().split('if __name__')[0])

rng = random.Random(3); ok_pos = ok_neg = 0; N = 200
orig_targets = targets
for trial in range(N):
    sZ = tuple(rng.randint(0, 1) for _ in range(6)); nsing = 10 - sum(sZ)
    avail_cols = [rng.randrange(len(COLS)) for _ in range(26)]
    roles = rng.sample(range(26), 2 + nsing)
    V = [0] * 18
    for k, idx in enumerate(roles):
        s, p = COLS[avail_cols[idx]]
        if k < 2:
            x, y = rng.sample(range(3), 2); V = [a + b + c for a, b, c in zip(V, contrib(s, p, x), contrib(s, p, y))]
        else:
            V = [a + b for a, b in zip(V, contrib(s, p, rng.randrange(3)))]
    from collections import Counter
    av = tuple(sorted(Counter(avail_cols).items()))
    Zc = next(c for c, (s, p) in enumerate(COLS) if s == sZ)
    globals()["targets"] = lambda s, p, e, V=tuple(V): V
    ok_pos += z_feasible(Zc, av, {})
    W = list(V); W[0] += 1                                          # breaks sum_b T(i,b) consistency with counts in general
    globals()["targets"] = lambda s, p, e, W=tuple(W): W
    ok_neg += (not z_feasible(Zc, av, {}))
globals()["targets"] = orig_targets
print("planted neighbourhoods accepted: %d/%d ; perturbed targets rejected: %d/%d" % (ok_pos, N, ok_neg, N))
