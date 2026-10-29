from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

import generator
import metody
import postup
from statistiky import HIST_HRANY, Statistiky

POPIS_METOD = {"SZR": "severozápadný roh", "IM": "indexová metóda", "VAM": "Vogelova metóda",
               "JVR": "juhovýchodný roh (nová)", "MDD": "dvojitá diferencia (nová)",
               "PVM": "predvídavá metóda (nová)"}

stav = {"stat": Statistiky()}


def cislo(x: float, des: int = 0) -> str:
    return f"{x:,.{des}f}".replace(",", " ").replace(".", ",")


def parametre(d: dict) -> dict:
    ca, cb, pa = int(d["cena_a"]), int(d["cena_b"]), int(d["podiel_a"]) / 100
    pv, pp = int(d["vyrovnane"]) / 100, int(d["ponuka"]) / 100
    ceny = {f"1-{ca}": pa, f"1-{cb}": 1 - pa} if ca != cb else {f"1-{ca}": 1.0}
    return dict(generator.PARAMETRE, m_rozsah=[int(d["m_od"]), int(d["m_do"])],
                n_rozsah=[int(d["n_od"]), int(d["n_do"])], ceny=ceny,
                typ={"vyrovnana": pv, "prebytok_ponuky": pp, "prebytok_dopytu": round(1 - pv - pp, 10)})


def parametre_json(d_json: str) -> str:
    return json.dumps(parametre(json.loads(d_json)))


def novy_beh(mena_json: str) -> None:
    stav["stat"] = Statistiky(json.loads(mena_json))


def pridaj(riadky_json: str) -> None:
    riadky, chyby = json.loads(riadky_json)
    stav["stat"].pridaj(riadky, chyby)


def prehlad() -> str:
    s = stav["stat"]
    s.zapis_historiu()
    tabulka = {}
    for m in s.metody:
        k, opt, odch, kroky, cas = s.stat[m][:5]
        tabulka[m] = None if k == 0 else {
            "optimum": 100 * opt / k, "odchylka": odch / k, "kroky": kroky / k,
            "najlepsia": 100 * s.najlepsia[m] / max(1, s.hotovo), "cas_ms": cas / k / 1e6}
    vel = sorted(s.velkost)
    velkost = {m: [[v, s.velkost[v][m][1] / s.velkost[v][m][0], s.velkost[v][m][2] / s.velkost[v][m][0]]
                   for v in vel if s.velkost[v][m][0]] for m in s.metody}
    stredy = ((HIST_HRANY[:-1] + HIST_HRANY[1:]) / 2).tolist()
    hist = {m: (s.hist[m] / max(1, s.hist[m].sum()) * 100).tolist() for m in s.metody}
    return json.dumps({"hotovo": s.hotovo, "chyby": s.chyby, "metody": s.metody, "tabulka": tabulka,
                       "historia": [[h[0], h[1]] for h in s.historia], "velkost": velkost,
                       "stredy": stredy, "hist": hist})


def excel(info_json: str) -> bytes:
    import export_excel
    cesta = Path("/tmp/vysledky.xlsx")
    export_excel.exportuj(cesta, stav["stat"], json.loads(info_json))
    return cesta.read_bytes()


def _prehlad_ulohy(C, a, b, nazov: str, vyber=None) -> list:
    C = np.asarray(C, dtype=np.int64)
    a = np.asarray(a, dtype=np.int64)
    b = np.asarray(b, dtype=np.int64)
    casti = []

    def t(text, tag=None):
        casti.append((text, tag))

    m_, n_ = C.shape
    if a.sum() == b.sum():
        typ = "vyrovnaná"
    elif a.sum() > b.sum():
        typ = f"prebytok ponuky ({cislo(a.sum())} > {cislo(b.sum())})"
    else:
        typ = f"prebytok dopytu ({cislo(a.sum())} < {cislo(b.sum())})"
    u, riadky, stlpce = postup.popis_ulohy(C, a, b)
    n = u.C.shape[1]

    t(f"{nazov}: {m_} dodávatelia × {n_} odberatelia, {typ}", "nadpis")
    if u.fiktivny:
        t(f"   (pridaný fiktívny {'dodávateľ D*' if u.fiktivny == 'dodavatel' else 'odberateľ O*'}"
          " s nulovými cenami)", "sivy")
    t("\n\nCeny c_ij, vpravo kapacity a_i, dole požiadavky b_j\n", "sivy")
    t("      " + "".join(f"{s:>6}" for s in stlpce) + "  │   a_i\n")
    for r, riadok, ai in zip(riadky, u.C, u.a):
        t(f"  {r:<4}" + "".join(f"{int(c):>6}" for c in riadok) + f"  │ {int(ai):>5}\n")
    t("  " + "─" * (4 + 6 * n) + "──┘\n")
    t("  b_j " + "".join(f"{int(bj):>6}" for bj in u.b) + "\n")

    vysledky = []
    for nazov_m, f in metody.VSETKY_METODY.items():
        if (vyber and nazov_m not in vyber) or (not vyber and nazov_m not in metody.METODY):
            continue
        t0 = time.perf_counter_ns()
        start = f(u)
        t1 = time.perf_counter_ns()
        opt = metody.modi(u, start)
        t2 = time.perf_counter_ns()
        vysledky.append((nazov_m, start, opt, (t1 - t0) / 1e3, (t2 - t1) / 1e3))
    z_opt = min(o.z for _, _, o, _, _ in vysledky)

    def plan(X, tag=None):
        t("      " + "".join(f"{s:>6}" for s in stlpce) + "\n", "sivy")
        for r, riadok in zip(riadky, X):
            t(f"  {r:<4}" + "".join(f"{(str(int(x)) if x else '·'):>6}" for x in riadok) + "\n", tag)

    for nazov_m, start, opt, _, _ in vysledky:
        odch = 100 * (start.z - z_opt) / z_opt if z_opt else 0
        t(f"\n{nazov_m} – {POPIS_METOD[nazov_m]}:  z = {start.z}", nazov_m)
        t(f"   (odchýlka {cislo(odch, 1)} %, MODI potrebovala {opt.kroky_modi} krokov)\n", "sivy")
        plan(start.X)

    t(f"\nOptimálne riešenie (MODI):  z* = {z_opt}\n", "nadpis")
    plan(vysledky[-1][2].X, "opt")

    t("\nPorovnanie\n", "nadpis")
    t(f"  {'metóda':<8}{'z':>8}{'odchýlka':>11}{'kroky MODI':>13}{'čas metódy':>13}{'čas MODI':>12}\n", "sivy")
    for nazov_m, start, opt, t_met, t_modi in vysledky:
        odch = 100 * (start.z - z_opt) / z_opt if z_opt else 0
        t(f"  {nazov_m:<8}{start.z:>8}{cislo(odch, 1):>9} %{opt.kroky_modi:>13}"
          f"{cislo(t_met):>10} µs{cislo(t_modi):>9} µs\n")
    return casti


def ukazka(m: int, n: int, id_: int) -> str:
    p = dict(generator.PARAMETRE, m_rozsah=[m, m], n_rozsah=[n, n])
    nu = generator.generuj(20261025, id_, p)
    return json.dumps(_prehlad_ulohy(nu.C, nu.a, nu.b, f"Úloha č. {id_}"))


def vlastna(zadanie_json: str) -> str:
    d = json.loads(zadanie_json)
    C, a, b, metoda = d["C"], d["a"], d["b"], d["metoda"]
    if not d["postup"]:
        vyber = {"VSETKY": None, "VSETKO": list(metody.VSETKY_METODY),
                 "NOVE": list(metody.NOVE_METODY)}.get(metoda, [metoda])
        return json.dumps(_prehlad_ulohy(C, a, b, "Vlastná úloha", vyber))
    casti, vysledky = postup.cely_postup(C, a, b, metoda)
    if len(vysledky) > 1:
        z_opt = min(o.z for _, o in vysledky.values())
        casti.append(("\nPorovnanie metód\n", "nadpis"))
        casti.append((f"  {'metóda':<8}{'z':>8}{'odchýlka':>11}{'kroky MODI':>13}\n", "sivy"))
        for nazov_m, (start, opt) in vysledky.items():
            odch = 100 * (start.z - z_opt) / z_opt if z_opt else 0
            casti.append((f"  {nazov_m:<8}{start.z:>8}{cislo(odch, 1):>9} %{opt.kroky_modi:>13}\n", nazov_m))
        casti.append((f"\nOptimum z* = {z_opt}\n", "opt"))
    return json.dumps(casti)


def nahodna(m: int, n: int) -> str:
    rng = np.random.default_rng()
    C = rng.integers(1, 21, size=(m, n))
    a = rng.integers(10, 61, size=m)
    b = generator._rozdel(rng, int(a.sum()), n, 10, 60)
    return json.dumps({"C": C.tolist(), "a": a.tolist(), "b": b.tolist()})
