"""Create Stage-Q instance files m<mask>_sL<k> from a complete LQ support enumeration and append them to stageQ_long/QUEUE.txt."""
import json, sys
mask = int(sys.argv[1]); classes = [int(x) for x in sys.argv[2].split(",")]
agg = {r["mask"]: r for r in json.load(open("cpsat_aggregate_results.json"))}
lq = json.load(open("enum_supports_lq_%d.json" % mask)); assert lq["complete"], "enumeration not complete"
names = []
for k, sup in enumerate(sorted(lq["supports"])):
    d = {"name": "m%05d_sL%d" % (mask, k), "mask": mask, "edges": agg[mask]["edges"], "support": [[int(c) for c in s] for s in sorted(sup)], "classes": classes}
    json.dump(d, open("stageQ_runs/%s.in.json" % d["name"], "w")); names.append(d["name"])
open("stageQ_long/QUEUE.txt", "a").write("\n".join(names) + "\n"); print("queued", names)
