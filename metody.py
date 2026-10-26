"""Dopravná úloha – metódy východiskového riešenia a MODI.

Podľa prednášky L5LZV 5-6 (D. Hrabec, FLKŘ):
  - metóda severozápadného rohu (SZR)
  - indexová metóda (IM)
  - Vogelova aproximačná metóda (VAM)
  - test optimality (potenciály u, v) a presun po Dantzigovom obvode (MODI)

Všetky výpočty sú v celých číslach (numpy int64), aby test optimality bol presný.
Báza má vždy m + n - 1 polí – pri degenerácii obsahuje aj polia s nulovou prepravou
(ε z prednášky).
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

import numpy as np


@dataclass
class Uloha:
    """Vyrovnaná dopravná úloha. `fiktivny` hovorí, či sa pridal riadok/stĺpec."""
    C: np.ndarray            # matica jednotkových nákladov m × n
    a: np.ndarray            # kapacity dodávateľov (m)
    b: np.ndarray            # požiadavky odberateľov (n)
    fiktivny: str | None = None   # None, "odberatel" alebo "dodavatel"


@dataclass
class Riesenie:
    X: np.ndarray                    # prepravný plán m × n
    baza: list[tuple[int, int]]      # bázické polia (m + n - 1)
    z: int                           # hodnota účelovej funkcie
    kroky_modi: int = 0              # počet presunov po Dantzigovom obvode
    postup: list[str] = field(default_factory=list)


def naklady(C: np.ndarray, X: np.ndarray) -> int:
    return int((C * X).sum())


# ---------------------------------------------------------------------------
# Vyváženie úlohy
# ---------------------------------------------------------------------------

def vyvaz(C, a, b, penale_odb=None, penale_dod=None) -> Uloha:
    """Prevedie úlohu na vyrovnanú pridaním fiktívneho účastníka.

    penale_odb – náklady na nevyužitú kapacitu (stĺpec fiktívneho odberateľa), predvolene 0
    penale_dod – penalizácia za neuspokojený dopyt (riadok fiktívneho dodávateľa), predvolene 0
    """
    C = np.asarray(C, dtype=np.int64)
    a = np.asarray(a, dtype=np.int64)
    b = np.asarray(b, dtype=np.int64)
    sa, sb = int(a.sum()), int(b.sum())
    if sa > sb:
        stlpec = np.zeros(len(a), dtype=np.int64) if penale_odb is None else np.asarray(penale_odb, dtype=np.int64)
        return Uloha(np.column_stack([C, stlpec]), a, np.append(b, sa - sb), "odberatel")
    if sa < sb:
        riadok = np.zeros(len(b), dtype=np.int64) if penale_dod is None else np.asarray(penale_dod, dtype=np.int64)
        return Uloha(np.vstack([C, riadok]), np.append(a, sb - sa), b, "dodavatel")
    return Uloha(C, a, b)


# ---------------------------------------------------------------------------
# Spoločná kostra východiskových metód
# ---------------------------------------------------------------------------

def _obsadzuj(u: Uloha, vyber_pole) -> Riesenie:
    """Opakuje: vyber pole → obsaď min(a_i, b_j) → vyškrtni riadok alebo stĺpec.

    V každom kroku sa vyškrtne práve jedna rada (pri súčasnom vyčerpaní kapacity
    aj požiadavky sa vyškrtne len riadok, stĺpec zostane s nulou). Tak vznikne
    presne m + n - 1 bázických polí aj pri degenerácii.
    """
    m, n = u.C.shape
    zost_a, zost_b = u.a.copy(), u.b.copy()
    riadky, stlpce = np.ones(m, bool), np.ones(n, bool)
    X = np.zeros((m, n), dtype=np.int64)
    baza = []
    while True:
        i, j = vyber_pole(u.C, riadky, stlpce)
        q = min(zost_a[i], zost_b[j])
        X[i, j] = q
        zost_a[i] -= q
        zost_b[j] -= q
        baza.append((i, j))
        if riadky.sum() == 1 and stlpce.sum() == 1:
            break
        if zost_a[i] == 0 and riadky.sum() > 1:
            riadky[i] = False
        else:
            stlpce[j] = False
    return Riesenie(X, baza, naklady(u.C, X))


def _szr_pole(C, riadky, stlpce):
    return int(np.argmax(riadky)), int(np.argmax(stlpce))


def _im_pole(C, riadky, stlpce):
    # najlacnejšie neškrtnuté pole; pri zhode podľa poradia riadkov a stĺpcov
    maska = np.where(riadky[:, None] & stlpce[None, :], C, np.iinfo(np.int64).max)
    k = int(np.argmin(maska))
    return divmod(k, C.shape[1])


def _diferencie(M):
    """Rozdiel dvoch najnižších cien v každom riadku M (pri jednom prvku 0)."""
    if M.shape[1] == 1:
        return np.zeros(M.shape[0], dtype=np.int64), M[:, 0]
    s = np.partition(M, 1, axis=1)
    return s[:, 1] - s[:, 0], s[:, 0]


def _vam_pole(C, riadky, stlpce):
    ri, sj = np.flatnonzero(riadky), np.flatnonzero(stlpce)
    S = C[np.ix_(ri, sj)]
    dr, minr = _diferencie(S)
    ds, mins = _diferencie(S.T)
    # rada s najväčšou diferenciou; pri zhode tá s lacnejším poľom, potom riadky pred stĺpcami
    kandidati = [(-dr[k], minr[k], 0, k) for k in range(len(ri))]
    kandidati += [(-ds[k], mins[k], 1, k) for k in range(len(sj))]
    _, _, typ, k = min(kandidati)
    if typ == 0:
        return int(ri[k]), int(sj[np.argmin(S[k])])
    return int(ri[np.argmin(S[:, k])]), int(sj[k])


def szr(u: Uloha) -> Riesenie:
    """Metóda severozápadného rohu."""
    return _obsadzuj(u, _szr_pole)


def indexova(u: Uloha) -> Riesenie:
    """Indexová metóda (metóda minimálnych nákladov)."""
    return _obsadzuj(u, _im_pole)


def vam(u: Uloha) -> Riesenie:
    """Vogelova aproximačná metóda."""
    return _obsadzuj(u, _vam_pole)


METODY = {"SZR": szr, "IM": indexova, "VAM": vam}


# ---------------------------------------------------------------------------
# Test optimality a MODI
# ---------------------------------------------------------------------------

def potencialy(C, baza):
    """u_i + v_j = c_ij pre bázické polia, u_1 = 0."""
    m, n = C.shape
    u = np.full(m, np.iinfo(np.int64).min)
    v = np.full(n, np.iinfo(np.int64).min)
    susedia_r = [[] for _ in range(m)]
    susedia_s = [[] for _ in range(n)]
    for i, j in baza:
        susedia_r[i].append(j)
        susedia_s[j].append(i)
    u[0] = 0
    fronta = deque([(0, 0)])          # (typ 0 = riadok / 1 = stĺpec, index)
    while fronta:
        typ, k = fronta.popleft()
        if typ == 0:
            for j in susedia_r[k]:
                if v[j] == np.iinfo(np.int64).min:
                    v[j] = C[k, j] - u[k]
                    fronta.append((1, j))
        else:
            for i in susedia_s[k]:
                if u[i] == np.iinfo(np.int64).min:
                    u[i] = C[i, k] - v[k]
                    fronta.append((0, i))
    return u, v


def je_optimalne(C, baza) -> bool:
    u, v = potencialy(C, baza)
    return bool(((u[:, None] + v[None, :]) <= C).all())


def _obvod(baza, m, i0, j0):
    """Dantzigov obvod: cesta v strome bázy z riadku i0 do stĺpca j0."""
    susedia = {}
    for (i, j) in baza:
        susedia.setdefault(("r", i), []).append((("s", j), (i, j)))
        susedia.setdefault(("s", j), []).append((("r", i), (i, j)))
    start, ciel = ("r", i0), ("s", j0)
    odkial = {start: None}
    fronta = deque([start])
    while fronta:
        uzol = fronta.popleft()
        if uzol == ciel:
            break
        for sused, pole in susedia.get(uzol, []):
            if sused not in odkial:
                odkial[sused] = (uzol, pole)
                fronta.append(sused)
    cesta = []
    uzol = ciel
    while odkial[uzol] is not None:
        uzol, pole = odkial[uzol]
        cesta.append(pole)
    cesta.reverse()            # od riadku i0 po stĺpec j0
    return cesta               # znamienka na ceste: −, +, −, ..., −


def modi(u: Uloha, start: Riesenie, max_krokov: int = 10_000, zapisuj: bool = False) -> Riesenie:
    """Od východiskového riešenia k optimu (test optimality + Dantzigov obvod)."""
    C = u.C
    m, n = C.shape
    X = start.X.copy()
    baza = list(start.baza)
    postup = []
    for krok in range(max_krokov + 1):
        up, vp = potencialy(C, baza)
        delta = up[:, None] + vp[None, :] - C          # kladné = dá sa zlepšiť
        for (i, j) in baza:
            delta[i, j] = 0
        k = int(np.argmax(delta))
        i0, j0 = divmod(k, n)
        if delta[i0, j0] <= 0:
            return Riesenie(X, baza, naklady(C, X), krok, postup)
        cesta = _obvod(baza, m, i0, j0)
        minus = cesta[0::2]
        plus = cesta[1::2]
        t = min(X[p] for p in minus)
        odchadza = next(p for p in minus if X[p] == t)
        X[i0, j0] += t
        for p in plus:
            X[p] += t
        for p in minus:
            X[p] -= t
        baza.remove(odchadza)
        baza.append((i0, j0))
        if zapisuj:
            postup.append(f"krok {krok + 1}: vstupuje {(i0 + 1, j0 + 1)}, odchádza "
                          f"{(odchadza[0] + 1, odchadza[1] + 1)}, t = {t}, z = {naklady(C, X)}")
    raise RuntimeError("MODI neskončila – pravdepodobne zacyklenie pri degenerácii")
