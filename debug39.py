import json
from full_model import Model
classes = json.load(open("classes_reduced.json")); cls = classes[39]
types = ["T"] * 6 + ["I"] * 27; fixed = {}; E = {}
for (i, j), e in zip(cls["edges"], cls["eps"]): E[(i, j)] = e % 3
for i in range(6):
    for j in range(i + 1, 6):
        for p in range(3): fixed[(i, j, p)] = 1 if ((i, j) in E and E[(i, j)] == p) else 0
M = Model(types, 14, fixed)
for name, terms, rhs in M.constraints():
    if name == ("pair", 0, 1, 0):
        cs = [t for t in terms if t[0] == "c"]; vs = [t for t in terms if t[0] != "c"]
        print("const terms:", cs, "| n var terms:", len(vs), "| rhs:", rhs)
        print("first var terms:", vs[:4])
        break
# count constant 'c' terms vs expectation, and check degree constraints of triangles
for name, terms, rhs in M.constraints():
    if name[0] == "deg" and name[1] < 6:
        cs = sum(t[1] for t in terms if t[0] == "c"); print(name, "const=%d rhs=%d  var terms=%d" % (cs, rhs, sum(1 for t in terms if t[0] != "c")))
