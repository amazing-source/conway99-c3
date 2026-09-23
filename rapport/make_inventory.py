"""Write rapport/INVENTAIRE.txt: every file of the research folder (except caches and the large regenerable CNF/DRAT files) with its
size and SHA-256, so that a reader can check he works on exactly the same data."""
import hashlib, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = []
for dp, dn, fn in os.walk(root):
    dn[:] = sorted(d for d in dn if d != "__pycache__")
    for f in sorted(fn):
        p = os.path.join(dp, f); rel = os.path.relpath(p, root).replace("\\", "/")
        if rel.endswith((".cnf", ".drat", ".aux", ".log.tmp", ".out", ".toc")) or rel == "rapport/INVENTAIRE.txt": continue
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        rows.append("%s  %10d  %s" % (h, os.path.getsize(p), rel))
open(os.path.join(root, "rapport", "INVENTAIRE.txt"), "w", encoding="utf-8").write(
    "# SHA-256  taille(octets)  fichier   -- dossier c3_recherche_annexe (les CNF/DRAT, volumineux et regenerables, sont exclus ;\n"
    "# l'empreinte de chaque CNF certifiee est dans certs/<nom>.gen.json)\n" + "\n".join(rows) + "\n")
print(len(rows), "files")
