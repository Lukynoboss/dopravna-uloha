from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import sys
import time
from pathlib import Path

import numpy as np

import cesty
import generator
import metody

PRIECINOK = cesty.KOREN / "vysledky"

STLPCE = ["id", "m", "n", "typ", "cena_max", "fiktivny", "metoda", "degeneracia",
          "z", "z_opt", "odchylka_pct", "optimum", "cas_metody_ns", "cas_modi_ns", "kroky_modi"]


def _degeneracia(r: metody.Riesenie) -> int:
    return sum(1 for p in r.baza if r.X[p] == 0)


def spracuj_ulohu(seed: int, id_: int, p: dict | None = None, mena: list[str] | None = None):
    nu = generator.generuj(seed, id_, p or generator.PARAMETRE)
    u = metody.vyvaz(nu.C, nu.a, nu.b)
    zaznamy = []
    for nazov in mena or metody.METODY:
        f = metody.VSETKY_METODY[nazov]
        t0 = time.perf_counter_ns()
        start = f(u)
        t1 = time.perf_counter_ns()
        opt = metody.modi(u, start)
        t2 = time.perf_counter_ns()
        zaznamy.append((nazov, start, opt, t1 - t0, t2 - t1))

    z_opt_vsetky = [o.z for _, _, o, _, _ in zaznamy]
    z_opt = min(z_opt_vsetky)
    chyby = []
    if len(set(z_opt_vsetky)) > 1:
        chyby.append({"id": id_, "chyba": f"MODI dala rôzne z*: {z_opt_vsetky}"})

    m, n = nu.C.shape
    riadky = []
    for nazov, start, opt, t_met, t_modi in zaznamy:
        odch = 100.0 * (start.z - z_opt) / z_opt if z_opt else 0.0
        riadky.append([id_, m, n, nu.typ, nu.cena_max, u.fiktivny or "", nazov,
                       _degeneracia(start), start.z, z_opt, round(odch, 6),
                       int(start.z == z_opt), t_met, t_modi, opt.kroky_modi])
    return riadky, chyby


def spracuj_blok(seed: int, ids: list[int], p: dict | None = None, mena: list[str] | None = None):
    riadky, chyby = [], []
    for id_ in ids:
        try:
            r, ch = spracuj_ulohu(seed, id_, p, mena)
            riadky.extend(r)
            chyby.extend(ch)
        except Exception as e:
            chyby.append({"id": id_, "chyba": f"{type(e).__name__}: {e}"})
    return riadky, chyby


class ZivyPriebeh:
    def __init__(self, pocet: int, procesy: int, zapnuty: bool = True, mena: list[str] | None = None):
        self.pocet, self.procesy, self.zapnuty = pocet, procesy, zapnuty
        self.hotovo = 0
        self.chyby = 0
        self.stat = {nazov: [0, 0, 0.0, 0, 0] for nazov in mena or metody.METODY}
        self.prvy_najlepsi = {nazov: 0 for nazov in mena or metody.METODY}
        self.t0 = time.perf_counter()
        self.posledny_vypis = 0.0
        self.riadkov_vypisu = 0
        if zapnuty and sys.platform == "win32":
            os.system("")

    def pridaj(self, riadky: list, chyby: list):
        self.chyby += len(chyby)
        uloha: dict[int, dict[str, int]] = {}
        for r in riadky:
            nazov = r[6]
            st = self.stat[nazov]
            st[0] += 1
            st[1] += r[11]
            st[2] += r[10]
            st[3] += r[14]
            st[4] += r[12] + r[13]
            uloha.setdefault(r[0], {})[nazov] = r[8]
        self.hotovo += len(uloha)
        for z in uloha.values():
            najmensie = min(z.values())
            for nazov, hodnota in z.items():
                self.prvy_najlepsi[nazov] += hodnota == najmensie
        if self.zapnuty and (time.perf_counter() - self.posledny_vypis > 0.25 or self.hotovo >= self.pocet):
            self.vypis()

    def vypis(self):
        self.posledny_vypis = time.perf_counter()
        uplynulo = self.posledny_vypis - self.t0
        podiel = self.hotovo / self.pocet if self.pocet else 1.0
        rychlost = self.hotovo / uplynulo if uplynulo > 0 else 0.0
        zostava = (self.pocet - self.hotovo) / rychlost if rychlost > 0 else 0.0
        sirka = 40
        plne = int(round(podiel * sirka))
        riadky = [
            f"Simulácia – {self.procesy} procesov",
            f"[{'█' * plne}{'░' * (sirka - plne)}] {100 * podiel:5.1f} %   "
            f"{self.hotovo:,} / {self.pocet:,} úloh".replace(",", " "),
            f"čas {uplynulo:6.1f} s   rýchlosť {rychlost:7.0f} úloh/s   zostáva ~{zostava:5.0f} s   chyby {self.chyby}",
            "",
            f"{'metóda':<7}{'trafila optimum':>16}{'priem. odchýlka':>17}{'kroky MODI':>12}{'najlepšia':>11}{'čas/úloha':>11}",
        ]
        for nazov, (k, opt, odch, kroky, cas) in self.stat.items():
            if k == 0:
                riadky.append(f"{nazov:<7}{'–':>16}{'–':>17}{'–':>12}{'–':>11}{'–':>11}")
                continue
            riadky.append(
                f"{nazov:<7}{100 * opt / k:15.2f} %{odch / k:15.1f} %{kroky / k:12.1f}"
                f"{100 * self.prvy_najlepsi[nazov] / self.hotovo:10.1f} %{cas / k / 1e6:8.2f} ms"
            )
        vystup = (f"\x1b[{self.riadkov_vypisu}F" if self.riadkov_vypisu else "") + \
            "".join(f"\x1b[2K{r}\n" for r in riadky)
        sys.stdout.write(vystup)
        sys.stdout.flush()
        self.riadkov_vypisu = len(riadky)


def main(argv: list[str] | None = None):
    from concurrent.futures import ProcessPoolExecutor
    ap = argparse.ArgumentParser(description="Simulácia metód dopravnej úlohy")
    ap.add_argument("--pocet", type=int, default=1000, help="počet úloh")
    ap.add_argument("--seed", type=int, default=20261025)
    ap.add_argument("--nazov", default="test1k", help="názov behu (súbory beh_<názov>.*)")
    ap.add_argument("--procesy", type=int, default=os.cpu_count() or 1)
    ap.add_argument("--blok", type=int, default=100, help="počet úloh v jednom bloku")
    ap.add_argument("--ticho", action="store_true", help="bez priebežného výpisu v termináli")
    ap.add_argument("--metody", choices=list(metody.SKUPINY), default="prednaska",
                    help="prednaska = SZR, IM, VAM; nove = JVR, MDD, PVM; vsetky = všetkých šesť")
    arg = ap.parse_args(argv)
    mena = metody.SKUPINY[arg.metody]

    PRIECINOK.mkdir(exist_ok=True)
    cesta_csv = PRIECINOK / f"beh_{arg.nazov}.csv"
    cesta_json = PRIECINOK / f"beh_{arg.nazov}.json"

    bloky = [list(range(z, min(z + arg.blok, arg.pocet))) for z in range(0, arg.pocet, arg.blok)]
    chyby = []
    pocet_riadkov = 0
    zivo = ZivyPriebeh(arg.pocet, arg.procesy, zapnuty=not arg.ticho and sys.stdout.isatty(), mena=mena)
    t0 = time.perf_counter()
    with open(cesta_csv, "w", newline="", encoding="utf-8") as fcsv:
        w = csv.writer(fcsv)
        w.writerow(STLPCE)
        if arg.procesy <= 1:
            vysledky = (spracuj_blok(arg.seed, b, None, mena) for b in bloky)
            for riadky, ch in vysledky:
                w.writerows(riadky)
                pocet_riadkov += len(riadky)
                chyby.extend(ch)
                zivo.pridaj(riadky, ch)
        else:
            with ProcessPoolExecutor(max_workers=arg.procesy) as ex:
                for riadky, ch in ex.map(spracuj_blok, [arg.seed] * len(bloky), bloky,
                                         [None] * len(bloky), [mena] * len(bloky)):
                    w.writerows(riadky)
                    pocet_riadkov += len(riadky)
                    chyby.extend(ch)
                    zivo.pridaj(riadky, ch)
    trvanie = time.perf_counter() - t0

    info = {
        "nazov": arg.nazov,
        "seed": arg.seed,
        "pocet_uloh": arg.pocet,
        "metody": mena,
        "procesy": arg.procesy,
        "blok": arg.blok,
        "parametre_generatora": generator.PARAMETRE,
        "generovanie": "np.random.default_rng([seed, id]); úloha je určená seedom a id",
        "zdovodnenie_kapacit": (
            "Základ kapacít/požiadaviek 10–100 (rád porovnateľný s cenami, dosť veľký na rôznorodé "
            "plány). Celkový objem T = priemer súčtov náhodných a_i a b_j, potom sa T rozdelí "
            "úmerne náhodným váham 10–100 (každý ≥ 1), aby boli súčty presné. Pri nevyrovnanej "
            "úlohe má väčšia strana navyše 5–30 % T – realistický prebytok, fiktívny účastník "
            "s nulovými cenami (metody.vyvaz) nie je zanedbateľný ani dominantný."
        ),
        "z_opt": "z MODI (minimum zo štartov všetkých metód; nezhoda = chyba)",
        "degeneracia": "počet bázických polí s nulovou prepravou vo východiskovom riešení",
        "casy": "cas_metody_ns a cas_modi_ns merané perf_counter_ns vo vnútri procesu",
        "trvanie_behu_s": round(trvanie, 3),
        "pocet_riadkov": pocet_riadkov,
        "pocet_chyb": len(chyby),
        "chyby": chyby[:100],
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "pocitac": platform.platform(),
        "cpu_logicke": os.cpu_count(),
        "datum": time.strftime("%Y-%m-%d %H:%M:%S"),
        "csv": cesta_csv.name,
    }
    with open(cesta_json, "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)

    if zivo.zapnuty:
        print()
    print(f"Hotovo: {arg.pocet} úloh, {pocet_riadkov} riadkov, {len(chyby)} chýb, "
          f"čas {trvanie:.1f} s ({arg.procesy} procesov)")
    print(f"Výstup: {cesta_csv}")
    return cesta_csv


if __name__ == "__main__":
    main()
