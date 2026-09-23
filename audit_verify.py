"""AUDIT: independent re-verification of the certified C3 results, written from scratch (imports none of the earlier modules and
uses none of the ChatGPT package's data).  Exact integer / rational arithmetic only.  Inputs read only for CROSS-CHECKING:
cpsat_aggregate_results.json, farkas_certificates.json, level2_results.json, classes_reduced.json.

A. The 156 graphs F on 6 vertices (networkx atlas).  For each: G0 = 6I+6J-5F-F^2.
   Negative entry -> excluded (certificate: the entry).  Else a negative principal minor -> excluded (certificate: the minor).
   Else (PSD) -> must match one of our 44 PSD motifs; for these the aggregated incidence has either an exact witness or a Farkas vector.
B. Level 2 recomputed: for each surviving motif and each phase class (cycle space mod gauge): R = 12I+2J-P^2-P; count R<0; check the
   stored witnesses decompose R exactly; the 2 non-witness classes must be the C6 with nonzero holonomy (hexagon lemma).
C. Orbit count of the surviving (F, phase) classes under Aut(F) x gauge x conjugation, recomputed with a different canonical form."""
import itertools, json
from fractions import Fraction
import networkx as nx

def G0_of(F):
    return [[6 * (i == j) + 6 - 5 * F[i][j] - sum(F[i][k] * F[k][j] for k in range(6)) for j in range(6)] for i in range(6)]

def det(M):
    M = [[Fraction(x) for x in r] for r in M]; n = len(M); d = Fraction(1)
    for c in range(n):
        p = next((r for r in range(c, n) if M[r][c] != 0), None)
        if p is None: return Fraction(0)
        if p != c: M[c], M[p] = M[p], M[c]; d = -d
        d *= M[c][c]
        for r in range(c + 1, n):
            f = M[r][c] / M[c][c]
            for k in range(c, n): M[r][k] -= f * M[c][k]
    return d

atlas = [g for g in nx.graph_atlas_g() if g.number_of_nodes() == 6]
assert len(atlas) == 156
stat = {"negative_entry": 0, "negative_minor": 0, "psd": 0}
psd_graphs = []
for g in atlas:
    F = [[int(g.has_edge(i, j)) for j in range(6)] for i in range(6)]
    G = G0_of(F)
    if any(G[i][j] < 0 for i in range(6) for j in range(6)): stat["negative_entry"] += 1; continue
    neg = None
    for k in range(1, 7):
        for S in itertools.combinations(range(6), k):
            if det([[G[i][j] for j in S] for i in S]) < 0: neg = S; break
        if neg: break
    if neg: stat["negative_minor"] += 1; continue
    stat["psd"] += 1; psd_graphs.append(g)
print("A1. 156 graphs:", stat)

# match PSD graphs with our 44 motifs, and check witness / Farkas for each
agg = json.load(open("cpsat_aggregate_results.json")); cert = {c["mask"]: c["certificate"] for c in json.load(open("farkas_certificates.json"))}
ours = []
for r in agg:
    h = nx.Graph(); h.add_nodes_from(range(6)); h.add_edges_from(r["edges"]); ours.append((h, r))
matched = 0; wit_ok = 0; far_ok = 0
pairs = [(i, j) for i in range(6) for j in range(i, 6)]
for g in psd_graphs:
    hits = [r for h, r in ours if nx.is_isomorphic(g, h)]
    assert len(hits) == 1, "PSD graph not matched exactly once"
    matched += 1; r = hits[0]
    F = [[0] * 6 for _ in range(6)]
    for a, b in r["edges"]: F[a][b] = F[b][a] = 1
    G = G0_of(F)
    if r["plain"]["result"] == "witness":
        S = [[0] * 6 for _ in range(6)]; tot = 0
        for key, m in r["plain"]["witness"].items():
            s = [int(c) for c in key]; tot += m
            for i in range(6):
                for j in range(6): S[i][j] += m * s[i] * s[j]
        assert tot == 27 and S == G; wit_ok += 1
    else:
        c = cert[r["mask"]]; y0 = c["y_total"]; yp = {(int(k[0]), int(k[1])): v for k, v in c["y_pairs"].items()}
        assert all(y0 + sum(v * s[i] * s[j] for (i, j), v in yp.items()) >= 0 for s in itertools.product((0, 1), repeat=6))
        assert 27 * y0 + sum(v * G[i][j] for (i, j), v in yp.items()) < 0; far_ok += 1
print("A2. PSD graphs matched to our motifs: %d ; exact witnesses: %d ; Farkas certificates: %d" % (matched, wit_ok, far_ok))
surv = [r for h, r in ours if r["plain"]["result"] == "witness"]

# ---------- B. Level 2 recomputed ----------
def P_of(edges, eps):
    P = [[0] * 18 for _ in range(18)]
    for i in range(6):
        for a in range(3):
            for d in (1, 2): P[3 * i + a][3 * i + (a + d) % 3] = 1
    for (i, j), e in zip(edges, eps):
        for a in range(3): P[3 * i + a][3 * j + (a + e) % 3] = P[3 * j + (a + e) % 3][3 * i + a] = 1
    return P
def R_of(P):
    return [[12 * (u == v) + 2 - sum(P[u][w] * P[w][v] for w in range(18)) - P[u][v] for v in range(18)] for u in range(18)]
def classes_mod_gauge(edges):
    # independent construction: BFS spanning forest from vertex 0.., free edges = the rest
    adj = {i: [] for i in range(6)}
    for t, (i, j) in enumerate(edges): adj[i].append((j, t)); adj[j].append((i, t))
    seen, tree = set(), set()
    for root in range(6):
        if root in seen: continue
        seen.add(root); stack = [root]
        while stack:
            u = stack.pop()
            for v, t in adj[u]:
                if v not in seen: seen.add(v); tree.add(t); stack.append(v)
    free = [t for t in range(len(edges)) if t not in tree]
    for vals in itertools.product(range(3), repeat=len(free)):
        eps = [0] * len(edges)
        for t, v in zip(free, vals): eps[t] = v
        yield eps
l2 = json.load(open("level2_results.json"))
l2map = {(r["mask"], tuple(r["eps"])): r for r in l2}
tot = neg = wit = other = 0; hexagon = []
for r in surv:
    edges = [tuple(e) for e in r["edges"]]
    for eps in classes_mod_gauge(edges):
        tot += 1; R = R_of(P_of(edges, eps))
        if any(R[u][v] < 0 for u in range(18) for v in range(18)):
            neg += 1; continue
        # find the stored run for the same phase class (stored representatives may use another spanning tree: compare holonomy data
        # by recomputing R and matching it)
        def gauge_eq(e1, e2):
            return any(all((e1[t] + g[j] - g[i]) % 3 == e2[t] % 3 for t, (i, j) in enumerate(edges)) for g in itertools.product(range(3), repeat=6))
        cand = [x for x in l2 if x["mask"] == r["mask"] and gauge_eq(eps, x["eps"])]
        assert len(cand) == 1, "phase class must match exactly one stored run (got %d)" % len(cand)
        x = cand[0]
        assert x["result"] != "R_negative", "stored run says R negative but recomputation says R >= 0"
        R = R_of(P_of(edges, x["eps"]))
        if x["result"] == "witness":
            # verify the witness: columns are indices into the 1366 phased columns, rebuilt here independently
            cols = []
            for s in itertools.product((0, 1), repeat=6):
                sup = [i for i in range(6) if s[i]]
                if not sup: cols.append((s, (0,) * 6)); continue
                for ph in itertools.product(range(3), repeat=len(sup) - 1):
                    p = [0] * 6
                    for i, v in zip(sup[1:], ph): p[i] = v
                    cols.append((s, tuple(p)))
            W = {int(c): m for c, m in x["witness"].items()}
            assert sum(W.values()) == 27
            for i in range(6):
                for j in range(i, 6):
                    for k in (range(3) if i < j else (0,)):
                        val = sum(m for c, m in W.items() if cols[c][0][i] and cols[c][0][j] and (cols[c][1][j] - cols[c][1][i]) % 3 == k)
                        assert val == R[3 * i][3 * j + k]
            wit += 1
        else:
            other += 1; hexagon.append((r["mask"], eps))
print("B. phase classes: %d ; R has a negative entry: %d ; exact decompositions verified: %d ; remaining (IP-infeasible): %d -> %s"
      % (tot, neg, wit, other, hexagon))
for mask, eps in hexagon:
    e = next(r for r in surv if r["mask"] == mask)["edges"]
    g = nx.Graph(); g.add_edges_from(e)
    cyc = nx.cycle_basis(g); hol = None
    if nx.is_isomorphic(g, nx.cycle_graph(6)):
        # holonomy around the 6-cycle: orient edges along the cycle
        E = {}
        for (i, j), v in zip(e, eps): E[(i, j)] = v % 3; E[(j, i)] = (-v) % 3
        c = cyc[0]; hol = sum(E[(c[t], c[(t + 1) % 6])] for t in range(6)) % 3
    print("   IP-infeasible class: mask %d, is C6: %s, holonomy: %s" % (mask, nx.is_isomorphic(g, nx.cycle_graph(6)), hol))

# ---------- C. orbit count under Aut(F) x gauge x conjugation (different canonical form: sorted tuple of all images) ----------
survivors = [(r["mask"], tuple(r["eps"])) for r in l2 if r["result"] == "witness"]
edges_of = {r["mask"]: [tuple(e) for e in r["edges"]] for r in surv}
def orbit(mask, eps):
    edges = edges_of[mask]; E = {}
    for (i, j), v in zip(edges, eps): E[(i, j)] = v % 3; E[(j, i)] = (-v) % 3
    es = set(frozenset(x) for x in edges); imgs = set()
    for perm in itertools.permutations(range(6)):
        if set(frozenset((perm[i], perm[j])) for i, j in edges) != es: continue
        inv = {perm[i]: i for i in range(6)}
        for g in itertools.product(range(3), repeat=6):
            for sg in (1, 2):
                imgs.add(tuple((sg * (E[(inv[i], inv[j])] + g[j] - g[i])) % 3 for (i, j) in edges))
    return frozenset(imgs)
orbits = {}
for mask, eps in survivors: orbits.setdefault((mask, orbit(mask, eps)), []).append(eps)
print("C. surviving (F, phase) classes: %d -> orbits: %d  (reduced list has %d)" % (len(survivors), len(orbits), len(json.load(open("classes_reduced.json")))))
