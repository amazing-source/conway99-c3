"""Independent stdlib-only checker. Re-derives G0 from the edge list and checks, for every PSD motif:
 - witness motifs: the multiplicities sum to 27 and reproduce G0 exactly;
 - excluded motifs: the integer Farkas vector y satisfies y.a(s) >= 0 for all 64 columns s and y.b < 0."""
import itertools, json
pairs = [(i, j) for i in range(6) for j in range(i, 6)]
def g0(edges):
    F = [[0] * 6 for _ in range(6)]
    for a, b in edges: F[a][b] = F[b][a] = 1
    return [[6 * (i == j) + 6 - 5 * F[i][j] - sum(F[i][k] * F[k][j] for k in range(6)) for j in range(6)] for i in range(6)]
res = json.load(open("cpsat_aggregate_results.json")); cert = {c["mask"]: c for c in json.load(open("farkas_certificates.json"))}
nw = nx = 0
for r in res:
    G = g0(r["edges"])
    if r["plain"]["result"] == "witness":
        S = [[0] * 6 for _ in range(6)]; tot = 0
        for key, m in r["plain"]["witness"].items():
            s = [int(c) for c in key]; tot += m
            for i in range(6):
                for j in range(6): S[i][j] += m * s[i] * s[j]
        assert tot == 27 and S == G, r["mask"]; nw += 1
    else:
        c = cert[r["mask"]]["certificate"]
        y0 = c["y_total"]; yp = {(int(k[0]), int(k[1])): v for k, v in c["y_pairs"].items()}
        for s in itertools.product((0, 1), repeat=6):
            assert y0 + sum(v * s[i] * s[j] for (i, j), v in yp.items()) >= 0, (r["mask"], s)
        yb = 27 * y0 + sum(v * G[i][j] for (i, j), v in yp.items())
        assert yb < 0, r["mask"]; nx += 1
print("PASS: %d witnesses exact, %d Farkas certificates exact (total %d PSD motifs)" % (nw, nx, nw + nx))
