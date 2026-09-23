"""Run every distinct Stage-Q instance from enum_all.json, W at a time, each in its own subprocess with a hard wall-clock limit.
Usage: python sweep_q.py <workers> <seconds_per_instance>"""
import json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
W, T = int(sys.argv[1]), float(sys.argv[2])
cls = dict(enumerate(json.load(open("classes_reduced.json"))))
inst = {}
ONLY_COMPLETE = len(sys.argv) > 3 and sys.argv[3] == 'complete'
for r in json.load(open("enum_all.json")):
    if ONLY_COMPLETE and not r['complete']: continue
    for s in r["supports"]:
        key = (r["mask"], json.dumps(s))
        inst.setdefault(key, {"mask": r["mask"], "edges": cls[r["class"]]["edges"], "support": s, "classes": []})["classes"].append(r["class"])
jobs = []
for n, (key, d) in enumerate(sorted(inst.items())):
    d["name"] = "m%05d_s%04d" % (d["mask"], n); fn = "stageQ_runs/%s.in.json" % d["name"]
    json.dump(d, open(fn, "w")); jobs.append((d["name"], fn, d["classes"]))
print("instances:", len(jobs), flush=True)
def run(job):
    name, fn, classes = job
    if os.path.exists("stageQ_runs/%s.json" % name): return name, "cached", 0, classes
    t0 = time.time()
    try:
        p = subprocess.run([sys.executable, "run_one_q.py", fn], capture_output=True, text=True, timeout=T)
        res = json.loads(p.stdout.strip().splitlines()[-1])["result"] if p.returncode == 0 else "ERROR:" + p.stderr[-200:]
    except subprocess.TimeoutExpired:
        res = "UNKNOWN"; json.dump({"name": name, "result": "UNKNOWN", "sec": T}, open("stageQ_runs/%s.json" % name, "w"))
    return name, res, time.time() - t0, classes
with ThreadPoolExecutor(W) as ex:
    for name, res, dt, classes in ex.map(run, jobs):
        print("%s classes=%s -> %s (%.0fs)" % (name, classes, res, dt), flush=True)
