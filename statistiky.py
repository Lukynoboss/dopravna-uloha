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
    def __init__(self, mena: list[str] | None = None):
        self.metody = list(mena or METODY)
        self.hotovo = 0
        self.chyby = 0
        self.stat = {m: [0, 0, 0.0, 0, 0, 0, 0, 0] for m in self.metody}
        self.najlepsia = {m: 0 for m in self.metody}
        self.velkost: dict[int, dict[str, list]] = {}
        self.typ: dict[str, dict[str, list]] = {}
        self.hist = {m: np.zeros(len(HIST_HRANY) - 1) for m in self.metody}
        self.historia: list[tuple[int, list[float]]] = []
        self.vzorka: list[list] = []

    def pridaj(self, riadky: list, chyby: list):
        self.chyby += len(chyby)
        if len(self.vzorka) < VZORKA_ULOH * len(self.metody):
            self.vzorka.extend(riadky[:VZORKA_ULOH * len(self.metody) - len(self.vzorka)])
        odch_batch = {m: [] for m in self.metody}
        for i in range(0, len(riadky), len(self.metody)):
            trojica = riadky[i:i + len(self.metody)]
            najmensie = min(r[I_Z] for r in trojica)
            vel = max(trojica[0][I_M], trojica[0][I_N])
            skupina = self.velkost.setdefault(vel, {m: [0, 0.0, 0, 0] for m in self.metody})
            podla_typu = self.typ.setdefault(trojica[0][I_TYP], {m: [0, 0.0, 0, 0] for m in self.metody})
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
            self.historia.append((self.hotovo, [self.stat[m][2] / max(1, self.stat[m][0]) for m in self.metody]))

    @classmethod
    def z_csv(cls, cesta: Path, blok: int = 3000) -> "Statistiky":
        typy = (int, int, int, str, int, str, str, int, int, int, float, int, int, int, int)
        mena = []
        with open(cesta, encoding="utf-8", newline="") as f:
            citac = csv.reader(f)
            next(citac)
            prve_id = None
            for riadok in citac:
                if prve_id is None:
                    prve_id = riadok[I_ID]
                if riadok[I_ID] != prve_id:
                    break
                mena.append(riadok[I_MET])
        s = cls(mena)
        davka = []
        with open(cesta, encoding="utf-8", newline="") as f:
            citac = csv.reader(f)
            next(citac)
            for riadok in citac:
                davka.append([t(x) for t, x in zip(typy, riadok)])
                if len(davka) >= blok and len(davka) % len(s.metody) == 0:
                    s.pridaj(davka, [])
                    davka = []
        if davka:
            s.pridaj(davka, [])
        return s
