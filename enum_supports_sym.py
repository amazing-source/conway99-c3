"""enum_supports_lq.py + symmetry breaking under Aut(F) (research 2026-09-23).
A support multiset is its count vector c[v] = #{Y : support of Y = v}, v in {0,1}^6 read as the 6-bit code (bit 5-i = triangle i).
pi in Aut(F) acts by relabelling triangles: (pi.c)[pi(v)] = c[v].  Lex-leader (sound: the lex-MAX element of every Aut(F)-orbit
satisfies it): c >=lex pi.c for every pi in Aut(F), positions compared in the order v = 0, 1, ..., 63.
So the enumeration returns one representative per Aut(F)-orbit of support multisets.  Consequence for the phase check: a class c of F
kills a representative mu only if it realizes NO image pi(mu) (support_phase_check_sym.py).  Stage Q is pi-invariant: run it on mu.
Usage: python enum_supports_sym.py <mask> <seconds per solve> <max solutions> [workers]"""
import json, sys, time, itertools
from ortools.sat.python import cp_model
from enum_supports_lq import build

def aut(edges):
    E = set(frozenset(e) for e in edges)
    return [p for p in itertools.permutations(range(6)) if set(frozenset((p[a], p[b])) for a, b in edges) == E]

def img_code(v, p):
    """code of the support obtained from support code v by relabelling triangle i -> p[i]."""
    s = [(v >> (5 - i)) & 1 for i in range(6)]; t = [0] * 6
    for i in range(6): t[p[i]] = s[i]
    return sum(t[i] << (5 - i) for i in range(6))

def add_lex_leader(md, x, edges):
    n = len(x); G = [p for p in aut(edges) if list(p) != list(range(6))]
    b = [[md.NewBoolVar("") for v in range(64)] for Y in range(n)]
    for Y in range(n):
        md.AddExactlyOne(b[Y])
        code = sum((2 ** (5 - i)) * x[Y][i] for i in range(6))
        md.Add(code == sum(v * b[Y][v] for v in range(64)))
    c = [md.NewIntVar(0, n, "") for v in range(64)]
    for v in range(64): md.Add(c[v] == sum(b[Y][v] for Y in range(n)))
    for p in G:
        pinv_img = [None] * 64                            # (pi.c)[w] = c[pi^-1(w)]
        for v in range(64): pinv_img[img_code(v, p)] = v
        A = c; B = [c[pinv_img[w]] for w in range(64)]
        e = None                                          # e = "prefix so far equal" (None = true)
        for k in range(64):
            if A[k] is B[k]: continue
            if e is None: md.Add(A[k] >= B[k])
            else: md.Add(A[k] >= B[k]).OnlyEnforceIf(e)
            eq = md.NewBoolVar(""); md.Add(A[k] == B[k]).OnlyEnforceIf(eq); md.Add(A[k] != B[k]).OnlyEnforceIf(eq.Not())
            e2 = md.NewBoolVar("")
            if e is None: md.Add(e2 == eq)
            else: md.AddBoolAnd([e, eq]).OnlyEnforceIf(e2); md.AddBoolOr([e.Not(), eq.Not()]).OnlyEnforceIf(e2.Not())
            e = e2
    return len(G)

def add_twin_lex(md, n=27):
    """orbits Y, Y+1 with equal support codes are interchangeable: then row_Y <=lex row_{Y+1} of C over columns W not in {Y, Y+1},
    value order 0<1<2 = bits (u, w).  Sound (row-wise lex of interchangeable vertices, same argument as quotient_model.add_lex_twins);
    compatible with the Aut(F) lex-leader since twin swaps do not change the count vector."""
    u, w, code = md.uw
    def AND(a, b):
        g = md.NewBoolVar(""); md.AddBoolAnd([a, b]).OnlyEnforceIf(g); md.AddBoolOr([a.Not(), b.Not()]).OnlyEnforceIf(g.Not()); return g
    for Y in range(n - 1):
        e = md.NewBoolVar(""); md.Add(code[Y] == code[Y + 1]).OnlyEnforceIf(e); md.Add(code[Y] != code[Y + 1]).OnlyEnforceIf(e.Not())
        for W in range(n):
            if W in (Y, Y + 1): continue
            for (a, b) in ((u[Y, W], u[Y + 1, W]), (w[Y, W], w[Y + 1, W])):
                md.AddBoolOr([e.Not(), a.Not(), b])                         # e and a -> b  (a <= b)
                eq = md.NewBoolVar(""); md.Add(a == b).OnlyEnforceIf(eq); md.Add(a != b).OnlyEnforceIf(eq.Not())
                e = AND(e, eq)

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    mask, secs, cap = int(args[0]), float(args[1]), int(args[2]); workers = int(args[3]) if len(args) > 3 else 1
    agg = {r["mask"]: r for r in json.load(open("cpsat_aggregate_results.json"))}
    edges = [tuple(e) for e in agg[mask]["edges"]]
    md, x = build(edges); ng = add_lex_leader(md, x, edges)
    twins = "--twins" in sys.argv; suffix = "_tw" if twins else ""
    if twins: add_twin_lex(md)
    print("mask %d: |Aut F| = %d, lex-leader constraints: %d, twin lex: %s" % (mask, ng + 1, ng, twins), flush=True)
    found = []; status = "?"; t0 = time.time()
    while len(found) < cap:
        sv = cp_model.CpSolver(); sv.parameters.num_workers = workers; sv.parameters.max_time_in_seconds = secs
        st = sv.StatusName(sv.Solve(md))
        if st not in ("OPTIMAL", "FEASIBLE"): status = st; break
        vec = [[sv.Value(x[Y][i]) for i in range(6)] for Y in range(27)]
        found.append(["".join(map(str, r)) for r in vec])
        md.AddBoolOr([(x[Y][i].Not() if vec[Y][i] else x[Y][i]) for Y in range(27) for i in range(6)])
        print("mask %d: canonical support multiset #%d found (%.0fs)" % (mask, len(found), time.time() - t0), flush=True)
    else:
        status = "CAP"
    print("mask %d: END status=%s, canonical multisets: %d, complete=%s, %.0fs" % (mask, status, len(found), status == "INFEASIBLE", time.time() - t0), flush=True)
    json.dump({"mask": mask, "status": status, "complete": status == "INFEASIBLE", "aut": ng + 1, "supports": found}, open("enum_supports_sym_%d%s.json" % (mask, suffix), "w"))
