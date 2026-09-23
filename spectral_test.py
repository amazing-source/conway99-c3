"""Spectral necessary condition for Stage Q (derived during the audit, exact arithmetic).
With Q = [[2I+F, B],[B^T, C]] and Q^2+Q = 12I+6J, Q1 = 14*1:
   B C = 6J - (3I+F) B   and   C 1 = 14*1 - B^T 1   =>   C M = M K,   M = [B^T | 1] (27x7),
   K = [[-(3I+F), -1_6], [6*1_6^T, 14]].
C symmetric => C preserves W = Im M and W^perp; on W^perp: B x = 0, J x = 0 => C^2 + C = 12 I => eigenvalues in {3, -4}.
char poly of C|W = charpoly(K) / charpoly(K restricted to ker M).  With r = rank M:  a + b = 27 - r,  tr C = 0 = tr(C|W) + 3a - 4b.
Necessary: a, b nonnegative integers; eigenvalues of C|W real; tr(C^3) >= 0 and = 0 mod 6 (C >= 0, zero diagonal, symmetric);
sanity: tr(C^2) = sum_Y (18 - |s_Y|)."""
import json, glob, sys
import sympy as sp
x = sp.symbols("x")
def analyse(edges, support):
    F = sp.zeros(6, 6)
    for i, j in edges: F[i, j] = F[j, i] = 1
    Bt = sp.Matrix([list(s) for s in support])                  # 27 x 6
    M = Bt.row_join(sp.ones(27, 1))
    K = (-(3 * sp.eye(6) + F)).row_join(-sp.ones(6, 1)).col_join((6 * sp.ones(1, 6)).row_join(sp.Matrix([[14]])))
    assert M * K == M * K  # placeholder
    r = M.rank()
    ker = M.nullspace()
    chiK = K.charpoly(x).as_expr()
    if ker:
        Nk = sp.Matrix.hstack(*ker)                              # basis of ker M (7 x d); K Nk = Nk R
        R = (Nk.T * Nk).inv() * Nk.T * K * Nk
        assert sp.simplify(K * Nk - Nk * R) == sp.zeros(7, len(ker)), "ker M not K-invariant?!"
        chiKer = R.charpoly(x).as_expr()
        chiW = sp.cancel(chiK / chiKer)
    else:
        chiW = chiK
    chiW = sp.Poly(chiW, x)
    assert chiW.degree() == r
    trW = -chiW.all_coeffs()[1]
    num = 4 * (27 - r) - trW                                      # 7a = 4(27-r) - trW
    a = sp.Rational(num, 7); b = (27 - r) - a
    sq = sp.Poly(sp.sqf_part(chiW.as_expr()), x)
    real = (sq.count_roots() == sq.degree())   # Sturm counts DISTINCT real roots: test the square-free part
    # power sums of C|W from the characteristic polynomial (Newton identities, exact)
    e = [(-1) ** k * c for k, c in enumerate(chiW.all_coeffs())]   # e_0..e_r
    p = [sp.Integer(r)]
    for k in range(1, 4):
        s_ = (-1) ** (k - 1) * k * (e[k] if k <= r else 0)
        for i in range(1, k): s_ += (-1) ** (i - 1) * (e[i] if i <= r else 0) * p[k - i]
        p.append(sp.nsimplify(s_))
    tr2 = p[2] + 9 * a + 16 * b; tr3 = p[3] + 27 * a - 64 * b
    expect_tr2 = sum(18 - sum(s) for s in support)
    ok = a.is_integer and b.is_integer and a >= 0 and b >= 0 and real and tr3 >= 0 and (tr3 % 6 == 0 if tr3.is_integer else False)
    return {"rank_M": int(r), "a": str(a), "b": str(b), "eig_W_real": bool(real), "tr2": str(tr2), "tr2_expected": expect_tr2,
            "tr2_consistent": bool(tr2 == expect_tr2), "tr3": str(tr3), "passes": bool(ok), "charpoly_W": str(chiW.as_expr())}
res = {}
for f in sorted(glob.glob("stageQ_runs/*.in.json")):
    d = json.load(open(f)); out = analyse([tuple(e) for e in d["edges"]], [tuple(s) for s in d["support"]])
    st = json.load(open(f.replace(".in.json", ".json")))["result"] if glob.glob(f.replace(".in.json", ".json")) else "not run"
    res[d["name"]] = dict(out, stageQ=st)
    print("%-14s rank=%d a=%-4s b=%-4s real=%-5s tr2=%s/%s tr3=%-6s spectral=%-5s | stageQ=%s" % (d["name"], out["rank_M"], out["a"], out["b"], out["eig_W_real"], out["tr2"], out["tr2_expected"], out["tr3"], "PASS" if out["passes"] else "FAIL", st), flush=True)
json.dump(res, open("spectral_results.json", "w"), indent=1)
