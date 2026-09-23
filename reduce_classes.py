"""Reduce the 125 (F, phase) classes surviving level 2/2.5 modulo: automorphisms of F (relabel triangles), gauge (per-triangle shift
g in F3^6: eps_ij -> eps_ij + g_j - g_i) and global conjugation (a -> -a: eps -> -eps). Canonical form = lexicographic minimum."""
import itertools, json
l25 = json.load(open("level25_results.json"))
edges_of = {r["mask"]: [tuple(e) for e in r["edges"]] for r in json.load(open("cpsat_aggregate_results.json"))}
def canon(edges, eps):
    E = {}
    for (i, j), v in zip(edges, eps): E[(i, j)] = v % 3; E[(j, i)] = (-v) % 3
    best = None
    es = set(frozenset(e) for e in edges)
    for perm in itertools.permutations(range(6)):
        if set(frozenset((perm[i], perm[j])) for i, j in edges) != es: continue
        inv = {perm[i]: i for i in range(6)}
        for g in itertools.product(range(3), repeat=6):
            for sgn in (1, 2):
                vec = tuple((sgn * (E[(inv[i], inv[j])] + g[j] - g[i])) % 3 for (i, j) in edges)
                if best is None or vec < best: best = vec
    return best
reps = {}
for r in l25:
    key = (r["mask"], canon(edges_of[r["mask"]], r["eps"]))
    reps.setdefault(key, []).append(r["eps"])
print("classes:", len(l25), "-> up to symmetry:", len(reps))
from collections import Counter
print(dict(Counter(k[0] for k in reps)))
json.dump([{"mask": k[0], "edges": edges_of[k[0]], "eps": list(k[1]), "members": v} for k, v in reps.items()], open("classes_reduced.json", "w"), indent=0)
