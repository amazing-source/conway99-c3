"""The lex symmetry breaking must keep at least one solution on real instances: BvLS quotient (81 'I' orbits): fix every entry except
those among a group of 6 orbits (so the free block is small), declare the 6 as interchangeable only if their fixed rows agree...
Simplest real test: 3x3 rook graph quotient with 3 'I' orbits, all interchangeable: count solutions with and without lex."""
from quotient_model import QModel, add_lex_twins, _worker
from pysat.solvers import Solver
for types in (["I"] * 3, ["T"] * 3):
    QM = QModel(types, 4)
    for lex in (False, True):
        cls, pool = QM.build_cnf()
        if lex: add_lex_twins(QM, cls, pool, [[0, 1, 2]])
        prim = [pool.id(k) for k in pool.obj2id if k[0] in ("u", "w")]
        n = 0
        with Solver(name="cadical195", bootstrap_with=cls) as s:
            while s.solve():
                mdl = s.get_model(); n += 1; s.add_clause([-l for l in mdl if abs(l) in set(prim)])
        print(types[0], "lex" if lex else "no lex", "-> quotient solutions:", n)
