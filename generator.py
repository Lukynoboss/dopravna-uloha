from __future__ import annotations

from dataclasses import dataclass

import numpy as np

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
    C: np.ndarray
    a: np.ndarray
    b: np.ndarray
    typ: str
    cena_max: int


def _rozdel(rng, spolu: int, k: int, lo: int, hi: int) -> np.ndarray:
    w = rng.integers(lo, hi + 1, size=k).astype(np.float64)
    volne = spolu - k
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
    a0 = rng.integers(lo, hi + 1, size=m)
    b0 = rng.integers(lo, hi + 1, size=n)
    T = int(round((a0.sum() + b0.sum()) / 2))
    T = max(T, m, n)

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
    for i in range(3):
        u = generuj(20261025, i)
        print(u.id, u.C.shape, u.typ, u.cena_max, u.a.sum(), u.b.sum())
