from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

import metody

METODY = list(metody.METODY)
HIST_HRANY = np.arange(0, 505, 5.0)
VZORKA_ULOH = 20_000

I_ID, I_M, I_N, I_TYP, I_CENA, I_FIKT, I_MET, I_DEG, I_Z, I_ZOPT, I_ODCH, I_OPT, I_TMET, I_TMODI, I_KROKY = range(15)


class Statistiky:
    def __init__(self):
        self.hotovo = 0
        self.chyby = 0
        self.stat = {m: [0, 0, 0.0, 0, 0, 0, 0, 0] for m in METODY}
        self.najlepsia = {m: 0 for m in METODY}
        self.velkost: dict[int, dict[str, list]] = {}
        self.typ: dict[str, dict[str, list]] = {}
        self.hist = {m: np.zeros(len(HIST_HRANY) - 1) for m in METODY}
        self.historia: list[tuple[int, list[float]]] = []
        self.vzorka: list[list] = []

    def pridaj(self, riadky: list, chyby: list):
        self.chyby += len(chyby)
        if len(self.vzorka) < VZORKA_ULOH * len(METODY):
            self.vzorka.extend(riadky[:VZORKA_ULOH * len(METODY) - len(self.vzorka)])
        odch_batch = {m: [] for m in METODY}
        for i in range(0, len(riadky), len(METODY)):
            trojica = riadky[i:i + len(METODY)]
            najmensie = min(r[I_Z] for r in trojica)
            vel = max(trojica[0][I_M], trojica[0][I_N])
            skupina = self.velkost.setdefault(vel, {m: [0, 0.0, 0, 0] for m in METODY})
            podla_typu = self.typ.setdefault(trojica[0][I_TYP], {m: [0, 0.0, 0, 0] for m in METODY})
            for r in trojica:
                m = r[I_MET]
                st = self.stat[m]
                st[0] += 1
                st[1] += r[I_OPT]
                st[2] += r[I_ODCH]
                st[3] += r[I_KROKY]
                st[4] += r[I_TMET] + r[I_TMODI]
                st[5] += r[I_TMET]
                st[6] += r[I_TMODI]
                st[7] += r[I_DEG] > 0
                self.najlepsia[m] += r[I_Z] == najmensie
                for g in (skupina[m], podla_typu[m]):
                    g[0] += 1
                    g[1] += r[I_ODCH]
                    g[2] += r[I_KROKY]
                    g[3] += r[I_OPT]
                odch_batch[m].append(r[I_ODCH])
            self.hotovo += 1
        for m, hodnoty in odch_batch.items():
            if hodnoty:
                h = np.clip(hodnoty, 0, HIST_HRANY[-1] - 1e-9)
                self.hist[m] += np.histogram(h, bins=HIST_HRANY)[0]

    def zapis_historiu(self):
        if self.hotovo and (not self.historia or self.historia[-1][0] != self.hotovo):
            self.historia.append((self.hotovo, [self.stat[m][2] / max(1, self.stat[m][0]) for m in METODY]))

    @classmethod
    def z_csv(cls, cesta: Path, blok: int = 3000) -> "Statistiky":
        s = cls()
        typy = (int, int, int, str, int, str, str, int, int, int, float, int, int, int, int)
        davka = []
        with open(cesta, encoding="utf-8", newline="") as f:
            citac = csv.reader(f)
            next(citac)
            for riadok in citac:
                davka.append([t(x) for t, x in zip(typy, riadok)])
                if len(davka) >= blok and len(davka) % len(METODY) == 0:
                    s.pridaj(davka, [])
                    davka = []
        if davka:
            s.pridaj(davka, [])
        return s
