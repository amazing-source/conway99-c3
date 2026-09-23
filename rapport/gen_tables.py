"""Generate the LaTeX tables of the audit report directly from the result files (no manual transcription)."""
import json, glob, os
os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/..")
agg = json.load(open("cpsat_aggregate_results.json")); far = {c["mask"]: c for c in json.load(open("farkas_certificates.json"))}
classes = json.load(open("classes_reduced.json")); enum = {r["class"]: r for r in json.load(open("enum_all.json"))}
spec = json.load(open("spectral_results.json")) if os.path.exists("spectral_results.json") else {}


def deg(edges):
    d = [0] * 6
    for a, b in edges: d[a] += 1; d[b] += 1
    return "".join(map(str, sorted(d, reverse=True)))


def E(edges):
    return " ".join("%d%d" % (a, b) for a, b in edges) if edges else "---"


out = []
# ---- Table A: the 44 PSD motifs ----
out.append(r"% table A: the 44 motifs F with PSD Gram G0")
out.append(r"\begin{longtable}{rrlll}\toprule masque & $|E|$ & degr\'es & ar\^etes $ij$ & incidence agr\'eg\'ee\\\midrule\endhead")
for r in sorted(agg, key=lambda r: (len(r["edges"]), r["mask"])):
    if r["plain"]["result"] == "witness":
        st = r"t\'emoin exact"
    else:
        st = r"exclu, Farkas ($y\cdot b=%d$)" % far[r["mask"]]["certificate"]["y_dot_b"]
    out.append(r"%d & %d & %s & %s & %s\\" % (r["mask"], len(r["edges"]), deg(r["edges"]), E(r["edges"]), st))
out.append(r"\bottomrule\end{longtable}")
out.append("")
# ---- Table B: the 46 classes and the enumeration of B ----
out.append(r"% table B: the 46 (F, phase) classes up to symmetry and the enumeration of B")
out.append(r"\begin{longtable}{rrlrrcr}\toprule classe & masque & phases $\varepsilon$ & membres & $B$ phas\'es & \'enum.\ compl\`ete & supports\\\midrule\endhead")
for i, c in enumerate(classes):
    e = enum[i]
    out.append(r"%d & %d & %s & %d & %d & %s & %d\\" % (i, c["mask"], "".join(map(str, c["eps"])) or "---", len(c["members"]),
                                                     e["n_phased"], "oui" if e["complete"] else r"\textbf{non}", len(e["supports"])))
out.append(r"\bottomrule\end{longtable}")
out.append("")
# ---- Table C: Stage-Q instances ----
out.append(r"% table C: Stage-Q instances of the 33 completely enumerated classes")
out.append(r"\begin{longtable}{llrlrl}\toprule instance & classes & $\operatorname{rang}M$ & \'etage Q (pysat/CaDiCaL) & temps & preuve DRAT (drat-trim)\\\midrule\endhead")
for f in sorted(glob.glob("stageQ_runs/*.in.json")):
    d = json.load(open(f)); n = d["name"]; o = "stageQ_runs/%s.json" % n
    r = json.load(open(o)) if os.path.exists(o) else {"result": r"non termin\'e", "sec": None}
    cert = "---"
    lg = "certs/%s.drat.log" % n
    if os.path.exists(lg):
        txt = open(lg, encoding="utf-8", errors="replace").read().replace("\r", "\n")
        cert = r"\textbf{v\'erifi\'ee}" if "\ns VERIFIED" in "\n" + txt else r"non v\'erifi\'ee"
    elif r["result"] == "UNSAT":
        cert = r"\`a faire"
    out.append(r"%s & %s & %s & %s & %s & %s\\" % (n.replace("_", r"\_"), ",".join(map(str, d["classes"])), spec.get(n, {}).get("rank_M", "?"),
                                                 r["result"], ("%.0f\\,s" % r["sec"]) if r.get("sec") else "---", cert))
out.append(r"\bottomrule\end{longtable}")
txt = "\n".join(out) + "\n"
parts = txt.split("% table ")[1:]
assert len(parts) == 3
for tag, part in zip("ABC", parts):
    open("rapport/tables_%s.tex" % tag, "w", encoding="utf-8").write("% table " + part)
print("written rapport/tables_A.tex, tables_B.tex, tables_C.tex")
