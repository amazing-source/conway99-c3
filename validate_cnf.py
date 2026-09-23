from full_model import Model, solve_cnf
for types, label in ((["T"] * 3, "3 triangular orbits"), (["I"] * 3, "3 independent orbits")):
    for k in (4, 5):
        M = Model(types, k); r, z = solve_cnf(M, 30)
        ok = M.lift(z)[1] if r == "SAT" else None
        print("%-22s k=%d: %s  lift_ok=%s" % (label, k, r, ok))
