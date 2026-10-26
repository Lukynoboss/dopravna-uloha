import numpy as np
from scipy.optimize import linprog

from metody import METODY, VSETKY_METODY, je_optimalne, modi, vyvaz

C1 = [[3, 5, 4, 1], [2, 1, 3, 2], [4, 5, 1, 3]]

chyby = 0


def over(nazov, dostal, cakal):
    global chyby
    ok = dostal == cakal
    chyby += not ok
    print(f"  {'OK ' if ok else 'CHYBA'} {nazov}: {dostal} (očakávané {cakal})")


def optimum_scipy(u):
    m, n = u.C.shape
    A_eq, b_eq = [], []
    for i in range(m):
        r = np.zeros(m * n); r[i * n:(i + 1) * n] = 1
        A_eq.append(r); b_eq.append(u.a[i])
    for j in range(n):
        r = np.zeros(m * n); r[j::n] = 1
        A_eq.append(r); b_eq.append(u.b[j])
    res = linprog(u.C.ravel(), A_eq=A_eq, b_eq=b_eq, method="highs")
    return round(res.fun)


print("Príklad 1 (str. 8–28): a = (10, 20, 10), b = (10, 5, 5, 20)")
u = vyvaz(C1, [10, 20, 10], [10, 5, 5, 20])
over("SZR", METODY["SZR"](u).z, 100)
over("IM", METODY["IM"](u).z, 65)
over("VAM", METODY["VAM"](u).z, 65)
for meno, f in METODY.items():
    over(f"optimum z {meno} cez MODI", modi(u, f(u)).z, 65)

print("Nová metóda JVR (juhovýchodný roh) na príklade 1")
u = vyvaz(C1, [10, 20, 10], [10, 5, 5, 20])
r = VSETKY_METODY["JVR"](u)
over("JVR", r.z, 100)
over("JVR plán", r.X.tolist(), [[10, 0, 0, 0], [0, 5, 5, 10], [0, 0, 0, 10]])
over("optimum z JVR cez MODI", modi(u, r).z, 65)

print("Nové krížové rohy SVR a JZR na príklade 1")
for meno in ("SVR", "JZR"):
    r = VSETKY_METODY[meno](u)
    over(meno, r.z, 90)
    over(f"{meno} plán", r.X.tolist(), [[0, 0, 0, 10], [0, 5, 5, 10], [10, 0, 0, 0]])
    over(f"optimum z {meno} cez MODI", modi(u, r).z, 65)

print("Nové metódy MDD (dvojitá diferencia) a PVM (predvídavá) na príklade 1")
for meno in ("MDD", "PVM"):
    r = VSETKY_METODY[meno](u)
    over(meno, r.z, 65)
    over(f"{meno} plán", r.X.tolist(), [[0, 0, 0, 10], [10, 5, 0, 5], [0, 0, 5, 5]])
    over(f"{meno} je optimálne", je_optimalne(u.C, r.baza), True)

print("Prebytok ponuky (str. 43–46): a = (15, 20, 10)")
u = vyvaz(C1, [15, 20, 10], [10, 5, 5, 20])
r = METODY["IM"](u)
over("IM", r.z, 65)
over("IM plán", r.X.tolist(), [[0, 0, 0, 10, 5], [10, 5, 0, 5, 0], [0, 0, 5, 5, 0]])
over("optimum", modi(u, r).z, 55)

print("Prebytok dopytu (str. 48–50): b = (10, 10, 5, 20)")
u = vyvaz(C1, [10, 20, 10], [10, 10, 5, 20])
r = METODY["VAM"](u)
over("VAM", r.z, 60)
over("VAM je optimálne", je_optimalne(u.C, r.baza), True)

print("Penalizácia 10 za neuspokojenie O1 (str. 51)")
u = vyvaz(C1, [10, 20, 10], [10, 10, 5, 20], penale_dod=[10, 0, 0, 0])
over("optimum", modi(u, METODY["VAM"](u)).z, 60)

print("Náhodné úlohy voči scipy (2000 úloh, aj nevyrovnané a degenerované)")
rng = np.random.default_rng(1)
zle = 0
for _ in range(2000):
    m, n = rng.integers(2, 9, size=2)
    C = rng.integers(1, 21, size=(m, n))
    a = rng.integers(1, 6, size=m) * 5
    b = rng.integers(1, 6, size=n) * 5
    u = vyvaz(C, a, b)
    opt = optimum_scipy(u)
    for meno, f in VSETKY_METODY.items():
        s = f(u)
        assert len(s.baza) == sum(u.C.shape) - 1, meno
        assert (s.X.sum(1) == u.a).all() and (s.X.sum(0) == u.b).all(), meno
        assert s.z >= opt, meno
        if modi(u, s).z != opt:
            zle += 1
over("MODI = optimum scipy (počet nezhôd)", zle, 0)

print("\nVÝSLEDOK:", "PREŠLO" if chyby == 0 else f"NEPREŠLO ({chyby} chýb)")
