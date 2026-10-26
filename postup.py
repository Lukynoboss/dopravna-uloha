from __future__ import annotations

from collections import deque

import numpy as np

import metody

NAZVY = {"SZR": "metóda severozápadného rohu", "IM": "indexová metóda", "VAM": "Vogelova aproximačná metóda"}
PRAVIDLA = {
    "SZR": "Vždy obsadíme ľavé horné (severozápadné) pole zostávajúcej tabuľky čo najväčším množstvom "
           "min(a_i, b_j). Na ceny sa neprihliada.",
    "IM": "Vždy obsadíme pole s najnižšou cenou v zostávajúcej tabuľke čo najväčším množstvom min(a_i, b_j). "
          "Pri zhode cien rozhoduje poradie: skôr vyšší riadok, potom ľavejší stĺpec.",
    "VAM": "V každom riadku a stĺpci zostávajúcej tabuľky spočítame diferenciu = rozdiel dvoch najnižších cien. "
           "V rade (riadku alebo stĺpci) s najväčšou diferenciou obsadíme pole s najnižšou cenou čo najväčším "
           "množstvom min(a_i, b_j). Pri zhode diferencií rozhoduje nižšia cena, potom riadok pred stĺpcom.",
}
SIRKA = 7


class Vypis:
    def __init__(self, riadky: list[str], stlpce: list[str]):
        self.casti: list[tuple[str, str | None]] = []
        self.r = riadky
        self.s = stlpce

    def t(self, text: str, tag: str | None = None):
        self.casti.append((text, tag))

    def pole(self, i: int, j: int) -> str:
        return f"{self.r[i]}–{self.s[j]}"

    def tabulka(self, bunky, prave=None, prava_hlavicka="", dole=None, dole_popis="", skrtnute_r=(),
                skrtnute_s=(), tag=None):
        hlavicka = "        " + "".join(f"{('×' if j in skrtnute_s else '') + s:>{SIRKA}}" for j, s in enumerate(self.s))
        if prave is not None:
            hlavicka += f"  │{prava_hlavicka:>{SIRKA + 1}}"
        self.t(hlavicka + "\n", "sivy")
        for i, riadok in enumerate(bunky):
            znak = "×" if i in skrtnute_r else " "
            text = f"   {znak}{self.r[i]:<4}" + "".join(f"{h:>{SIRKA}}" for h in riadok)
            if prave is not None:
                text += f"  │{prave[i]:>{SIRKA + 1}}"
            self.t(text + "\n", tag)
        if dole is not None:
            self.t("        " + "─" * (SIRKA * len(self.s)) + ("──┘" if prave is not None else "") + "\n", "sivy")
            self.t(f"  {dole_popis:<6}" + "".join(f"{h:>{SIRKA}}" for h in dole) + "\n", tag)


def _plan(X, baza):
    v_baze = set(baza)
    return [[str(int(X[i, j])) if (i, j) in v_baze else "·" for j in range(X.shape[1])] for i in range(X.shape[0])]


def _vzorec_z(C, X, baza):
    clenov = [f"{int(X[i, j])}·{int(C[i, j])}" for (i, j) in sorted(baza) if X[i, j]]
    return " + ".join(clenov) + f" = {metody.naklady(C, X)}"


def _diferencie(C, ri, sj):
    S = C[np.ix_(ri, sj)]
    dr, minr = metody._diferencie(S)
    ds, mins = metody._diferencie(S.T)
    return S, dr, minr, ds, mins


def vychodiskove(u: metody.Uloha, nazov: str, v: Vypis) -> metody.Riesenie:
    C = u.C
    m, n = C.shape
    zost_a, zost_b = u.a.copy(), u.b.copy()
    riadky, stlpce = np.ones(m, bool), np.ones(n, bool)
    X = np.zeros((m, n), dtype=np.int64)
    baza: list[tuple[int, int]] = []
    v.t(f"\n{nazov} – {NAZVY[nazov]}\n", nazov)
    v.t(PRAVIDLA[nazov] + "\n", "sivy")
    krok = 0
    while True:
        krok += 1
        v.t(f"\nKrok {krok}\n", "podnadpis")
        if nazov == "SZR":
            i, j = metody._szr_pole(C, riadky, stlpce)
            dovod = f"Severozápadný roh zostávajúcej tabuľky je pole {v.pole(i, j)} (cena {int(C[i, j])})."
        elif nazov == "IM":
            i, j = metody._im_pole(C, riadky, stlpce)
            dovod = f"Najnižšia cena v zostávajúcej tabuľke je {int(C[i, j])} v poli {v.pole(i, j)}."
        else:
            ri, sj = np.flatnonzero(riadky), np.flatnonzero(stlpce)
            S, dr, minr, ds, mins = _diferencie(C, ri, sj)
            v.t("Diferencie riadkov:   " + ",  ".join(f"{v.r[ri[k]]}: {int(dr[k])}" for k in range(len(ri))) + "\n")
            v.t("Diferencie stĺpcov:   " + ",  ".join(f"{v.s[sj[k]]}: {int(ds[k])}" for k in range(len(sj))) + "\n")
            kandidati = [(-dr[k], minr[k], 0, k) for k in range(len(ri))]
            kandidati += [(-ds[k], mins[k], 1, k) for k in range(len(sj))]
            d_max, _, typ, k = min(kandidati)
            zhoda = sum(1 for c in kandidati if c[0] == d_max) > 1
            i, j = metody._vam_pole(C, riadky, stlpce)
            rada = f"riadku {v.r[ri[k]]}" if typ == 0 else f"stĺpci {v.s[sj[k]]}"
            dovod = (f"Najväčšia diferencia je {int(-d_max)} v {rada}"
                     + (" (viac rád má rovnakú diferenciu – rozhodla nižšia cena / poradie)" if zhoda else "")
                     + f". Najnižšia cena v nej je {int(C[i, j])} v poli {v.pole(i, j)}.")
        q = int(min(zost_a[i], zost_b[j]))
        v.t(dovod + "\n")
        v.t(f"Obsadíme ho množstvom x = min(a = {int(zost_a[i])}, b = {int(zost_b[j])}) = {q}.\n")
        X[i, j] = q
        zost_a[i] -= q
        zost_b[j] -= q
        baza.append((i, j))
        posledny = riadky.sum() == 1 and stlpce.sum() == 1
        if posledny:
            v.t("Toto bolo posledné voľné pole – všetok tovar je rozvezený.\n")
        elif zost_a[i] == 0 and riadky.sum() > 1:
            riadky[i] = False
            text = f"Dodávateľ {v.r[i]} má vyčerpanú kapacitu → riadok {v.r[i]} škrtáme."
            if zost_b[j] == 0:
                text += (f" Zároveň je splnená aj požiadavka {v.s[j]}, stĺpec ostáva – ďalšie pole v ňom "
                         "dostane 0 (degenerácia).")
            v.t(text + "\n")
        else:
            stlpce[j] = False
            v.t(f"Požiadavka odberateľa {v.s[j]} je splnená → stĺpec {v.s[j]} škrtáme.\n")
        v.tabulka(_plan(X, baza), [str(int(x)) for x in zost_a], "zost. a", [str(int(x)) for x in zost_b],
                  "zost.b", [k for k in range(m) if not riadky[k]], [k for k in range(n) if not stlpce[k]])
        if posledny:
            break
    z = metody.naklady(C, X)
    nuly = sum(1 for p in baza if X[p] == 0)
    v.t(f"\nVýchodiskové riešenie {nazov}: ", "podnadpis")
    v.t(f"z = {_vzorec_z(C, X, baza)}\n", nazov)
    v.t(f"Obsadených (bázických) polí: {len(baza)} = m + n − 1 = {m} + {n} − 1"
        + (f", z toho {nuly} s nulovou prepravou (degenerované riešenie, v prednáške ε)." if nuly else ".") + "\n",
        "sivy")
    return metody.Riesenie(X, baza, z)


def _potencialy(C, baza, v: Vypis):
    m, n = C.shape
    prazdne = np.iinfo(np.int64).min
    up = np.full(m, prazdne)
    vp = np.full(n, prazdne)
    susedia_r = [[] for _ in range(m)]
    susedia_s = [[] for _ in range(n)]
    for i, j in baza:
        susedia_r[i].append(j)
        susedia_s[j].append(i)
    up[0] = 0
    rovnice = [f"u{1} = 0"]
    fronta = deque([(0, 0)])
    while fronta:
        typ, k = fronta.popleft()
        if typ == 0:
            for j in susedia_r[k]:
                if vp[j] == prazdne:
                    vp[j] = C[k, j] - up[k]
                    rovnice.append(f"v{j + 1} = c{k + 1},{j + 1} − u{k + 1} = {int(C[k, j])} − ({int(up[k])}) = {int(vp[j])}")
                    fronta.append((1, j))
        else:
            for i in susedia_s[k]:
                if up[i] == prazdne:
                    up[i] = C[i, k] - vp[k]
                    rovnice.append(f"u{i + 1} = c{i + 1},{k + 1} − v{k + 1} = {int(C[i, k])} − ({int(vp[k])}) = {int(up[i])}")
                    fronta.append((0, i))
    for r in rovnice:
        v.t("    " + r + "\n")
    return up, vp


def modi(u: metody.Uloha, start: metody.Riesenie, v: Vypis, max_krokov: int = 10_000) -> metody.Riesenie:
    C = u.C
    m, n = C.shape
    X = start.X.copy()
    baza = list(start.baza)
    v.t("\nTest optimality a zlepšovanie (metóda MODI)\n", "nadpis")
    v.t("Pre bázické polia platí u_i + v_j = c_ij (volíme u1 = 0). Pre nebázické polia počítame "
        "Δ_ij = u_i + v_j − c_ij. Ak sú všetky Δ ≤ 0, riešenie je optimálne. Inak vstupuje do bázy pole "
        "s najväčším kladným Δ a tovar presunieme po Dantzigovom uzavretom obvode.\n", "sivy")
    for krok in range(max_krokov + 1):
        v.t(f"\nIterácia {krok + 1}   (z = {metody.naklady(C, X)})\n", "podnadpis")
        v.t("Potenciály:\n", "sivy")
        up, vp = _potencialy(C, baza, v)
        delta = up[:, None] + vp[None, :] - C
        v_baze = set(baza)
        for (i, j) in baza:
            delta[i, j] = 0
        bunky = [["B" if (i, j) in v_baze else str(int(delta[i, j])) for j in range(n)] for i in range(m)]
        v.t("Δ_ij = u_i + v_j − c_ij  (B = bázické pole):\n", "sivy")
        v.tabulka(bunky, [str(int(x)) for x in up], "u_i", [str(int(x)) for x in vp], "v_j")
        k = int(np.argmax(delta))
        i0, j0 = divmod(k, n)
        if delta[i0, j0] <= 0:
            v.t("Všetky Δ ≤ 0 → riešenie je optimálne.\n", "opt")
            z = metody.naklady(C, X)
            v.t("\nOptimálne riešenie\n", "nadpis")
            v.tabulka(_plan(X, baza), tag="opt")
            v.t(f"z* = {_vzorec_z(C, X, baza)}\n", "opt")
            v.t(f"MODI potrebovala {krok} {'krok' if krok == 1 else 'krokov' if krok == 0 or krok >= 5 else 'kroky'}.\n",
                "sivy")
            return metody.Riesenie(X, baza, z, krok)
        kladne = int((delta > 0).sum())
        v.t(f"Kladných Δ je {kladne} → riešenie nie je optimálne. Najväčšie Δ = {int(delta[i0, j0])} má pole "
            f"{v.pole(i0, j0)} → vstupuje do bázy.\n")
        cesta = metody._obvod(baza, m, i0, j0)
        minus = cesta[0::2]
        plus = cesta[1::2]
        obvod = [f"+{v.pole(i0, j0)} ({int(X[i0, j0])})"]
        obvod += [f"{'−' if k_ % 2 == 0 else '+'}{v.pole(*p)} ({int(X[p])})" for k_, p in enumerate(cesta)]
        v.t("Dantzigov uzavretý obvod:  " + " → ".join(obvod) + f" → späť do {v.pole(i0, j0)}\n")
        t = int(min(X[p] for p in minus))
        odchadza = next(p for p in minus if X[p] == t)
        v.t("t = min{" + ", ".join(str(int(X[p])) for p in minus) + f"}} = {t}  (hodnoty v poliach so znamienkom −)\n")
        v.t(f"V poliach + pripočítame {t}, v poliach − odpočítame {t}. Z bázy odchádza pole {v.pole(*odchadza)}"
            + (" (t = 0 – degenerovaný krok, zmení sa len báza)." if t == 0 else ".") + "\n")
        X[i0, j0] += t
        for p in plus:
            X[p] += t
        for p in minus:
            X[p] -= t
        baza.remove(odchadza)
        baza.append((i0, j0))
        v.t("Nové riešenie:\n", "sivy")
        v.tabulka(_plan(X, baza))
        v.t(f"z = {_vzorec_z(C, X, baza)}\n")
    raise RuntimeError("MODI neskončila – pravdepodobne zacyklenie pri degenerácii")


def popis_ulohy(C, a, b):
    C = np.asarray(C, dtype=np.int64)
    a = np.asarray(a, dtype=np.int64)
    b = np.asarray(b, dtype=np.int64)
    u = metody.vyvaz(C, a, b)
    m, n = u.C.shape
    riadky = [f"D{i + 1}" for i in range(m)]
    stlpce = [f"O{j + 1}" for j in range(n)]
    if u.fiktivny == "dodavatel":
        riadky[-1] = "D*"
    elif u.fiktivny == "odberatel":
        stlpce[-1] = "O*"
    return u, riadky, stlpce


def cely_postup(C, a, b, metoda: str, nazov: str = "Vlastná úloha") -> tuple[list[tuple[str, str | None]], dict]:
    u, riadky, stlpce = popis_ulohy(C, a, b)
    v = Vypis(riadky, stlpce)
    m_, n_ = np.asarray(C).shape
    sa, sb = int(np.sum(a)), int(np.sum(b))
    typ = "vyrovnaná" if sa == sb else f"prebytok ponuky ({sa} > {sb})" if sa > sb else f"prebytok dopytu ({sa} < {sb})"
    v.t(f"{nazov}: {m_} dodávatelia × {n_} odberatelia, {typ}\n", "nadpis")
    if u.fiktivny == "odberatel":
        v.t(f"Ponuka je väčšia ako dopyt → pridáme fiktívneho odberateľa O* s požiadavkou {sa - sb} a cenami 0.\n",
            "sivy")
    elif u.fiktivny == "dodavatel":
        v.t(f"Dopyt je väčší ako ponuka → pridáme fiktívneho dodávateľa D* s kapacitou {sb - sa} a cenami 0.\n",
            "sivy")
    v.t("\nZadanie – ceny c_ij, vpravo kapacity a_i, dole požiadavky b_j\n", "sivy")
    v.tabulka([[str(int(c)) for c in r] for r in u.C], [str(int(x)) for x in u.a], "a_i",
              [str(int(x)) for x in u.b], "b_j")
    metody_ = list(metody.METODY) if metoda == "VSETKY" else [metoda]
    vysledky = {}
    for nazov_m in metody_:
        start = vychodiskove(u, nazov_m, v)
        opt = modi(u, start, v)
        vysledky[nazov_m] = (start, opt)
    return v.casti, vysledky
