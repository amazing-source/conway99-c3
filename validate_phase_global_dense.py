"""Planted control for phase_global.global_feasible: random columns, random symmetric C (roles with phases), targets/counts computed
from the planted C from each row's own perspective; the global model must accept.  Tests the psi -> -psi symmetric role conversion."""
import random
src = open("phase_global.py", encoding="utf-8").read()
exec(src.split("\nif __name__")[0])
rng = random.Random(29); acc = 0; N = 10; stats = []
for trial in range(N):
    cols = [rng.randrange(len(COLS)) for _ in range(27)]
    role = {}
    for Y in range(27):
        for Z in range(Y + 1, 27):
            role[Y, Z] = rng.choice([None] * 6 + [0, 1, 2, 3, 4, 5])      # stored from Y to Z (Y<Z)
    tgt = []; cnt = []
    for Z in range(27):
        T = [0] * 18; ns = nd = 0
        for Y in range(27):
            if Y == Z: continue
            k = role[min(Y, Z), max(Y, Z)]
            if k is None: continue
            psis = {k} if k < 3 else set(range(3)) - {k - 3}                   # as stored from min to max
            if Y > Z: psis = {(-q) % 3 for q in psis}                          # psi as seen from Y towards Z
            s, p = COLS[cols[Y]]
            for psi in psis:
                for t_, x in enumerate(contrib(s, p, psi)): T[t_] += x
            if len(psis) == 1: ns += 1
            else: nd += 1
        tgt.append(T); cnt.append((ns, nd))
    res = global_feasible({}, {}, 90, tgt=tgt, cnt=cnt, cols_override=cols); stats.append(res); acc += bool(res)
    print('trial', trial, '->', res, flush=True)
print("planted symmetric blocks accepted: %d/%d ; statuses: %s" % (acc, N, stats))
