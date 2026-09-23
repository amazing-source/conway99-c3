"""Canonical manifest of the C3 branch (research 2026-09-23).  Purpose: byte-for-byte comparison between independent reproductions.
Every artifact is rewritten in a CANONICAL form (sorted, normalised, no timings, no discovery order) and hashed (SHA-256):
  code      : every .py / .sh file (exact bytes)
  instances : stageQ_runs/*.in.json -> {name, mask, sorted edges, sorted supports}
  enums     : enum_supports_*.json -> {complete flag, sorted list of sorted multisets}  (the SET found, not the order found)
  cubes     : cubes/<instance>/results.txt -> sorted "Z A B VERDICT" with VERDICT the final one (UNSAT/SAT beat UNKNOWN); counts
  certs     : certs/SUMMARY*.txt -> sorted "name cnf_sha256 verdict" (no timings)
Two reproductions agree on a line iff they reach the same mathematical result on the same inputs.  Timings, logs, solver traces and
DRAT proof bytes (they depend on time limits) are deliberately excluded; UNSAT claims are checked by drat-trim on a CNF of known sha256.
Usage: python manifest.py > MANIFEST.txt"""
import glob, hashlib, json, os, re

H = lambda b: hashlib.sha256(b).hexdigest()
def canon(obj): return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()

def code():
    for f in sorted(glob.glob("*.py") + glob.glob("*.sh")):
        yield "code", f, H(open(f, "rb").read()), ""

def instances():
    for f in sorted(glob.glob("stageQ_runs/*.in.json")):
        d = json.load(open(f))
        c = {"name": d["name"], "mask": d.get("mask"), "edges": sorted(sorted(e) for e in d["edges"]),
             "support": sorted("".join(map(str, s)) for s in d["support"])}
        yield "instance", d["name"], H(canon(c)), ""

def enums():
    for f in sorted(glob.glob("enum_supports_*.json")):
        d = json.load(open(f))
        ms = sorted(tuple(sorted(x)) for x in d.get("supports", []))
        c = {"complete": bool(d.get("complete")), "multisets": ms}
        yield "enum", os.path.basename(f), H(canon(c)), "complete=%s n=%d" % (c["complete"], len(ms))

def cubes():
    for d in sorted(glob.glob("cubes/m*_s*")):
        f = os.path.join(d, "results.txt"); name = os.path.basename(d)
        if name.endswith("relaxed") or not os.path.exists(f): continue
        best = {}
        for line in open(f):
            p = line.split()
            if len(p) < 4: continue
            k = (p[0], int(p[1]), int(p[2])); v = "SAT" if p[3].startswith("SAT") else p[3]
            rank = {"SAT": 3, "UNSAT": 2}.get(v, 1)
            if rank > {"SAT": 3, "UNSAT": 2}.get(best.get(k), 0): best[k] = v
        lines = sorted("%s %d %d %s" % (k[0], k[1], k[2], v) for k, v in best.items())
        n_u = sum(v == "UNSAT" for v in best.values()); n_s = sum(v == "SAT" for v in best.values())
        yield "cubes", name, H("\n".join(lines).encode()), "UNSAT=%d SAT=%d other=%d" % (n_u, n_s, len(best) - n_u - n_s)

def certs():
    rows = set()
    for f in sorted(glob.glob("certs/SUMMARY*.txt")):
        for line in open(f):
            m = re.match(r"(\S+) cadical=(\S+).*?drat_trim=(\S+).*?sha256\(cnf\)=([0-9a-f]+)", line)
            if m: rows.add("%s %s %s %s" % (m.group(1), m.group(4), m.group(2), m.group(3)))
    for r in sorted(rows):
        yield "cert", r.split()[0], H(r.encode()), r

if __name__ == "__main__":
    print("# C3 manifest: kind  name  sha256(canonical form)  summary")
    for gen in (code, instances, enums, cubes, certs):
        for kind, name, h, extra in gen():
            print("%-9s %-40s %s %s" % (kind, name, h, extra))
