"""Spúšťač projektu – jednoduché menu v termináli.

Spustenie: dvojklik na spusti.bat, alebo
    .venv\\Scripts\\python.exe spusti.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

import generator
import metody
import simulacia

KOREN = Path(__file__).resolve().parent


def otazka(text: str, predvolene: str) -> str:
    odpoved = input(f"{text} [{predvolene}]: ").strip()
    return odpoved or predvolene


def cele_cislo(text: str, predvolene: int) -> int:
    while True:
        odpoved = otazka(text, str(predvolene)).replace(" ", "")
        if odpoved.isdigit() and int(odpoved) > 0:
            return int(odpoved)
        print("  Zadaj kladné celé číslo.")


def ziva_simulacia():
    pocet = cele_cislo("Počet úloh", 10_000)
    procesy = cele_cislo("Počet procesov (jadier)", os.cpu_count() or 1)
    seed = cele_cislo("Seed", 20261025)
    nazov = otazka("Názov behu", f"zivy_{pocet}")
    if (simulacia.PRIECINOK / f"beh_{nazov}.csv").exists():
        if otazka(f"Beh '{nazov}' už existuje. Prepísať? (a/n)", "n").lower() != "a":
            print("Zrušené.")
            return
    # menšie bloky → plynulejší priebežný výpis (výsledky od veľkosti bloku nezávisia)
    blok = max(10, min(100, pocet // (procesy * 20) or 10))
    print()
    simulacia.main(["--pocet", str(pocet), "--procesy", str(procesy), "--seed", str(seed),
                    "--nazov", nazov, "--blok", str(blok)])
    if otazka("Vyhodnotiť tento beh (štatistiky a grafy)? (a/n)", "a").lower() == "a":
        vyhodnotenie(nazov)


def vypis_maticu(nazov: str, M: np.ndarray, riadky: list[str], stlpce: list[str], sirka: int = 5):
    print(f"  {nazov}")
    print("  " + " " * 4 + "".join(f"{s:>{sirka}}" for s in stlpce))
    for r, riadok in zip(riadky, M):
        print("  " + f"{r:<4}" + "".join(f"{(str(int(x)) if x else '·'):>{sirka}}" for x in riadok))


def ukazka_ulohy():
    """Jedna malá náhodná úloha: tabuľka, východiskové riešenia troch metód a optimum."""
    p = dict(generator.PARAMETRE, m_rozsah=[3, 5], n_rozsah=[3, 6])
    id_ = cele_cislo("Číslo úlohy (iné číslo = iná úloha)", int(time.time()) % 100_000)
    nu = generator.generuj(20261025, id_, p)
    u = metody.vyvaz(nu.C, nu.a, nu.b)
    m, n = u.C.shape
    riadky = [f"D{i + 1}" for i in range(m)]
    stlpce = [f"O{j + 1}" for j in range(n)]
    if u.fiktivny == "dodavatel":
        riadky[-1] = "D*"
    elif u.fiktivny == "odberatel":
        stlpce[-1] = "O*"

    print(f"\nÚloha č. {id_}: {nu.C.shape[0]} dodávateľov × {nu.C.shape[1]} odberateľov, "
          f"typ: {nu.typ.replace('_', ' ')}" + (" (pridaný fiktívny " + u.fiktivny + ")" if u.fiktivny else ""))
    print("\n  Ceny c_ij, vpravo kapacity a_i, dole požiadavky b_j:")
    print("  " + " " * 4 + "".join(f"{s:>5}" for s in stlpce) + "    a_i")
    for r, riadok, a in zip(riadky, u.C, u.a):
        print("  " + f"{r:<4}" + "".join(f"{int(c):>5}" for c in riadok) + f"  | {int(a)}")
    print("  b_j " + "".join(f"{int(b):>5}" for b in u.b))

    vysledky = []
    for nazov, f in metody.METODY.items():
        t0 = time.perf_counter_ns()
        start = f(u)
        t1 = time.perf_counter_ns()
        opt = metody.modi(u, start)
        t2 = time.perf_counter_ns()
        vysledky.append((nazov, start, opt, (t1 - t0) / 1e3, (t2 - t1) / 1e3))
        print()
        vypis_maticu(f"{nazov} – východiskové riešenie, z = {start.z}", start.X, riadky, stlpce)

    z_opt = min(o.z for _, _, o, _, _ in vysledky)
    print()
    vypis_maticu(f"Optimálne riešenie (MODI), z* = {z_opt}", vysledky[-1][2].X, riadky, stlpce)
    print(f"\n  {'metóda':<7}{'z':>8}{'odchýlka':>11}{'kroky MODI':>12}{'čas metódy':>13}{'čas MODI':>11}")
    for nazov, start, opt, t_met, t_modi in vysledky:
        odch = 100 * (start.z - z_opt) / z_opt if z_opt else 0.0
        print(f"  {nazov:<7}{start.z:>8}{odch:10.1f} %{opt.kroky_modi:>12}{t_met:10.0f} µs{t_modi:8.0f} µs")


def vyhodnotenie(nazov: str | None = None):
    behy = sorted(p.stem.removeprefix("beh_") for p in simulacia.PRIECINOK.glob("beh_*.csv"))
    if not behy:
        print("Zatiaľ nie je žiadny beh simulácie.")
        return
    if nazov is None:
        print("Dostupné behy: " + ", ".join(behy))
        nazov = otazka("Ktorý beh vyhodnotiť", "hlavny100k" if "hlavny100k" in behy else behy[-1])
    subprocess.run([sys.executable, str(KOREN / "analyza.py"), nazov], cwd=KOREN)


def test_metod():
    subprocess.run([sys.executable, str(KOREN / "test_metody.py")], cwd=KOREN)


MENU = [
    ("Simulácia s priebežnými výsledkami", ziva_simulacia),
    ("Ukážka jednej malej úlohy (SZR, IM, VAM a optimum)", ukazka_ulohy),
    ("Vyhodnotenie behu (štatistiky a grafy)", vyhodnotenie),
    ("Test správnosti metód", test_metod),
]


def main():
    os.chdir(KOREN)
    while True:
        print("\n=== Dopravná úloha – porovnanie metód SZR, IM, VAM ===")
        for i, (text, _) in enumerate(MENU, 1):
            print(f"  {i}. {text}")
        print("  0. Koniec")
        volba = input("Voľba: ").strip()
        if volba == "0" or volba.lower() in ("q", "koniec"):
            break
        if volba.isdigit() and 1 <= int(volba) <= len(MENU):
            print()
            try:
                MENU[int(volba) - 1][1]()
            except KeyboardInterrupt:
                print("\nPrerušené (Ctrl+C).")
        else:
            print("Neplatná voľba.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print()
