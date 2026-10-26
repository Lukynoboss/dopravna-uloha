"""Generátor náhodných dopravných úloh.

Každá úloha je jednoznačne určená dvojicou (seed, id):
    rng = np.random.default_rng([seed, id])
takže ju možno kedykoľvek znovu vytvoriť bez ukladania matíc
a nezávisí od poradia ani od rozdelenia úloh medzi procesy.

Parametre (dohodnuté s používateľom):
  - m aj n nezávisle rovnomerne z {3, ..., 20} (aj obdĺžnikové úlohy)
  - ceny c_ij celé, s pravdepodobnosťou 1/2 z {1..20}, inak z {1..100}
  - typ: 50 % vyrovnaná, 25 % prebytok ponuky, 25 % prebytok dopytu
  - kapacity a požiadavky celé čísla, "základ" rovnomerne z {10..100}
  - pri nevyrovnanej úlohe je prebytok 5–30 % súčtu menšej strany
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Predvolené parametre – ukladajú sa aj do vysledky/beh_<názov>.json
PARAMETRE = {
    "m_rozsah": [3, 20],
    "n_rozsah": [3, 20],
    "ceny": {"1-20": 0.5, "1-100": 0.5},
    "typ": {"vyrovnana": 0.50, "prebytok_ponuky": 0.25, "prebytok_dopytu": 0.25},
    "kapacity_zaklad": [10, 100],
    "prebytok_podiel": [0.05, 0.30],
    "fiktivne_ceny": 0,
}

TYPY = ("vyrovnana", "prebytok_ponuky", "prebytok_dopytu")


@dataclass
class NahodnaUloha:
    id: int
    C: np.ndarray        # m × n, int64
    a: np.ndarray        # kapacity dodávateľov
    b: np.ndarray        # požiadavky odberateľov
    typ: str             # vyrovnana / prebytok_ponuky / prebytok_dopytu
    cena_max: int        # 20 alebo 100


def _rozdel(rng, spolu: int, k: int, lo: int, hi: int) -> np.ndarray:
    """Rozdelí celé číslo `spolu` na k kladných celých častí.

    Váhy sa ťahajú rovnomerne z {lo..hi}, každá časť dostane aspoň 1 a zvyšok
    sa rozdelí úmerne váham (metóda najväčších zvyškov), takže súčet sedí presne.
    """
    w = rng.integers(lo, hi + 1, size=k).astype(np.float64)
    volne = spolu - k                       # po 1 kus pre každého
    podiel = volne * w / w.sum()
    casti = np.floor(podiel).astype(np.int64)
    zvysok = volne - int(casti.sum())
    if zvysok > 0:
        poradie = np.argsort(-(podiel - casti), kind="stable")
        casti[poradie[:zvysok]] += 1
    return casti + 1


def generuj(seed: int, id_: int, p: dict = PARAMETRE) -> NahodnaUloha:
    rng = np.random.default_rng([seed, id_])
    m = int(rng.integers(p["m_rozsah"][0], p["m_rozsah"][1] + 1))
    n = int(rng.integers(p["n_rozsah"][0], p["n_rozsah"][1] + 1))
    # rozsah cien "1-K" vyberá jedno náhodné číslo podľa pravdepodobností v p["ceny"]
    # (pre predvolené {"1-20": 0.5, "1-100": 0.5} rovnaké ako pôvodne: r < 0.5 → 20, inak 100)
    r = rng.random()
    rozsahy = list(p["ceny"].items())
    cena_max = int(rozsahy[-1][0].split("-")[1])
    hranica = 0.0
    for kluc, pravd in rozsahy:
        hranica += pravd
        if r < hranica:
            cena_max = int(kluc.split("-")[1])
            break
    C = rng.integers(1, cena_max + 1, size=(m, n), dtype=np.int64)

    r = rng.random()
    pv = p["typ"]["vyrovnana"]
    pp = p["typ"]["prebytok_ponuky"]
    typ = TYPY[0] if r < pv else (TYPY[1] if r < pv + pp else TYPY[2])

    lo, hi = p["kapacity_zaklad"]
    # základný objem: priemer očakávaných súčtov oboch strán (symetricky k m, n)
    a0 = rng.integers(lo, hi + 1, size=m)
    b0 = rng.integers(lo, hi + 1, size=n)
    T = int(round((a0.sum() + b0.sum()) / 2))
    T = max(T, m, n)                         # aby každá časť bola aspoň 1

    if typ == "vyrovnana":
        A = B = T
    else:
        q = rng.uniform(*p["prebytok_podiel"])
        nadbytok = max(1, int(round(q * T)))
        A, B = (T + nadbytok, T) if typ == "prebytok_ponuky" else (T, T + nadbytok)

    a = _rozdel(rng, A, m, lo, hi)
    b = _rozdel(rng, B, n, lo, hi)
    return NahodnaUloha(id_, C, a, b, typ, cena_max)


if __name__ == "__main__":
    # rýchla ukážka
    for i in range(3):
        u = generuj(20261025, i)
        print(u.id, u.C.shape, u.typ, u.cena_max, u.a.sum(), u.b.sum())
