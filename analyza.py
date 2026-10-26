import csv
import json
import os
import sys
import time

import numpy as np
from scipy import stats
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

KOREN = os.path.dirname(os.path.abspath(__file__))
METODY = ["SZR", "IM", "VAM"]
FARBY = {"SZR": "#2a78d6", "IM": "#eb6834", "VAM": "#1baf7a"}
TYPY = ["vyrovnana", "prebytok_ponuky", "prebytok_dopytu"]
TYPY_POPIS = {"vyrovnana": "vyrovnaná", "prebytok_ponuky": "prebytok ponuky",
              "prebytok_dopytu": "prebytok dopytu"}
SKUPINY_MN = [(9, 49), (50, 99), (100, 149), (150, 249), (250, 400)]
Z95 = 1.959963984540054


def najdi_subory(arg):
    if arg is None:
        arg = "hlavny100k"
    if arg.lower().endswith(".csv"):
        csv_cesta = arg if os.path.isabs(arg) else os.path.join(KOREN, arg)
    else:
        nazov = arg[4:] if arg.startswith("beh_") else arg
        csv_cesta = os.path.join(KOREN, "vysledky", f"beh_{nazov}.csv")
    if not os.path.exists(csv_cesta):
        sys.exit(f"CSV neexistuje: {csv_cesta}")
    json_cesta = csv_cesta[:-4] + ".json"
    nazov = os.path.basename(csv_cesta)[:-4]
    nazov = nazov[4:] if nazov.startswith("beh_") else nazov
    return csv_cesta, json_cesta, nazov


def nacitaj(csv_cesta):
    stl = {k: [] for k in ["id", "m", "n", "typ", "cena_max", "fiktivny", "metoda",
                           "degeneracia", "z", "z_opt", "odchylka_pct", "optimum",
                           "cas_metody_ns", "cas_modi_ns", "kroky_modi"]}
    with open(csv_cesta, newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        hlavicka = next(r)
        idx = [hlavicka.index(k) for k in stl]
        zoznamy = list(stl.values())
        for riadok in r:
            for z, i in zip(zoznamy, idx):
                z.append(riadok[i])
    met = np.array([METODY.index(x) for x in stl["metoda"]], dtype=np.int64)
    ids = np.array(stl["id"], dtype=np.int64)
    poradie = np.lexsort((met, ids))
    ids, met = ids[poradie], met[poradie]
    N = len(ids) // 3
    if len(ids) != 3 * N or not (np.all(met.reshape(N, 3) == [0, 1, 2])
                                 and np.all(ids.reshape(N, 3) == ids.reshape(N, 3)[:, :1])):
        sys.exit("CSV nemá pre každú úlohu presne 3 riadky SZR/IM/VAM")

    def pole(k, dt):
        return np.array(stl[k], dtype=dt)[poradie].reshape(N, 3)

    d = {
        "id": ids.reshape(N, 3)[:, 0],
        "m": pole("m", np.int64)[:, 0],
        "n": pole("n", np.int64)[:, 0],
        "typ": np.array(stl["typ"], dtype=object)[poradie].reshape(N, 3)[:, 0],
        "cena_max": pole("cena_max", np.int64)[:, 0],
        "deg": pole("degeneracia", np.int64),
        "z": pole("z", np.int64),
        "z_opt": pole("z_opt", np.int64),
        "odch": pole("odchylka_pct", np.float64),
        "opt": pole("optimum", np.int64).astype(bool),
        "t_met": pole("cas_metody_ns", np.float64) / 1000.0,
        "t_modi": pole("cas_modi_ns", np.float64) / 1000.0,
        "kroky": pole("kroky_modi", np.int64),
    }
    d["t_spolu"] = d["t_met"] + d["t_modi"]
    d["mn"] = d["m"] * d["n"]
    return d


def priemer_ci(x):
    x = np.asarray(x, dtype=float)
    if len(x) < 2:
        return float(np.mean(x)) if len(x) else np.nan, np.nan, np.nan
    p = x.mean()
    h = Z95 * x.std(ddof=1) / np.sqrt(len(x))
    return p, p - h, p + h


def podiel_ci(k, n):
    if n == 0:
        return np.nan, np.nan, np.nan
    p = k / n
    zz = Z95 ** 2
    s = (p + zz / (2 * n)) / (1 + zz / n)
    h = Z95 * np.sqrt(p * (1 - p) / n + zz / (4 * n * n)) / (1 + zz / n)
    return 100 * p, 100 * (s - h), 100 * (s + h)


def kvantil_ci(x, q):
    xs = np.sort(np.asarray(x, dtype=float))
    n = len(xs)
    hodnota = float(np.quantile(xs, q))
    lo = int(stats.binom.ppf(0.025, n, q))
    hi = int(stats.binom.ppf(0.975, n, q)) + 1
    lo = min(max(lo, 1), n) - 1
    hi = min(max(hi, 1), n) - 1
    return hodnota, xs[lo], xs[hi]


def poradia(z):
    return 1 + (z[:, None, :] < z[:, :, None]).sum(axis=2)


def f(x, des=2):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "–"
    s = f"{x:,.{des}f}".replace(",", " ").replace(".", ",")
    return s


def fci(t, des=2):
    p, lo, hi = t
    return f"{f(p, des)} [{f(lo, des)}; {f(hi, des)}]"


def tabulka(hlavicka, riadky):
    out = ["| " + " | ".join(hlavicka) + " |",
           "|" + "|".join(["---"] + ["--:"] * (len(hlavicka) - 1)) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in riadky]
    return "\n".join(out)


def p_text(p):
    return "< 1e-300" if p == 0 else f"{p:.2e}".replace(".", ",")


def styl_osi(ax):
    ax.grid(True, color="#e3e2de", linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#9a9994")
    ax.tick_params(colors="#52514e")


def biny_mn(mn, sirka=25):
    hrany = np.arange(0, 401 + sirka, sirka)
    hrany[0] = 9
    b = np.digitize(mn, hrany[1:-1], right=True)
    stredy = (hrany[:-1] + hrany[1:]) / 2
    return b, stredy, len(hrany) - 1


def graf_ciara(d, hodnota, ylabel, titul, subor, podiel=False, logy=False, ylim0=True):
    b, stredy, nb = biny_mn(d["mn"])
    fig, ax = plt.subplots(figsize=(8, 5))
    styl_osi(ax)
    for j, met in enumerate(METODY):
        y, lo, hi, x = [], [], [], []
        for k in range(nb):
            maska = b == k
            if maska.sum() < 30:
                continue
            v = hodnota[maska, j]
            t = podiel_ci(int(v.sum()), len(v)) if podiel else priemer_ci(v)
            x.append(stredy[k]); y.append(t[0]); lo.append(t[1]); hi.append(t[2])
        ax.plot(x, y, "-o", color=FARBY[met], lw=2, ms=4, label=met)
        ax.fill_between(x, lo, hi, color=FARBY[met], alpha=0.2, lw=0)
    ax.set_xlabel("veľkosť úlohy m·n (počet polí tabuľky, skupiny po 25)")
    ax.set_ylabel(ylabel)
    ax.set_title(titul)
    if logy:
        ax.set_yscale("log")
        form = matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}".replace(".", ","))
        ax.yaxis.set_major_formatter(form)
        ax.yaxis.set_minor_formatter(form)
    elif ylim0:
        ax.set_ylim(bottom=0)
    ax.legend(title="metóda", frameon=False)
    fig.text(0.99, 0.01, "pás = 95 % interval spoľahlivosti", ha="right", fontsize=8, color="#52514e")
    fig.tight_layout()
    fig.savefig(subor, dpi=150)
    plt.close(fig)


def vsetky_grafy(d, adr):
    os.makedirs(adr, exist_ok=True)
    subory = []

    def cesta(meno):
        p = os.path.join(adr, meno)
        subory.append(p)
        return p

    graf_ciara(d, d["odch"], "priemerná odchýlka od optima (%)",
               "Odchýlka východiskového riešenia od optima podľa veľkosti úlohy",
               cesta("odchylka_vs_velkost.png"))
    graf_ciara(d, d["kroky"].astype(float), "priemerný počet krokov MODI",
               "Počet krokov MODI do optima podľa veľkosti úlohy",
               cesta("kroky_modi_vs_velkost.png"))
    graf_ciara(d, d["opt"], "úlohy s trafeným optimom (%)",
               "Podiel úloh, kde metóda hneď trafila optimum",
               cesta("optimum_vs_velkost.png"), podiel=True)
    graf_ciara(d, d["t_spolu"] / 1000.0, "priemerný celkový čas (ms, log. mierka)",
               "Celkový čas (metóda + MODI) podľa veľkosti úlohy",
               cesta("cas_celkovy_vs_velkost.png"), logy=True)
    graf_ciara(d, d["t_met"] / 1000.0, "priemerný čas metódy (ms, log. mierka)",
               "Čas samotnej východiskovej metódy podľa veľkosti úlohy",
               cesta("cas_metody_vs_velkost.png"), logy=True)

    fig, axy = plt.subplots(1, 2, figsize=(10, 5), gridspec_kw={"width_ratios": [3, 2]})
    for ax, mets, tit in [(axy[0], METODY, "všetky metódy"), (axy[1], ["IM", "VAM"], "detail IM a VAM")]:
        styl_osi(ax)
        bp = ax.boxplot([d["odch"][:, METODY.index(m)] for m in mets], showfliers=False,
                        patch_artist=True, widths=0.55, medianprops={"color": "#0b0b0b", "lw": 2})
        for patch, m in zip(bp["boxes"], mets):
            patch.set_facecolor(FARBY[m]); patch.set_alpha(0.75); patch.set_edgecolor("#52514e")
        ax.set_xticks(range(1, len(mets) + 1), mets)
        ax.set_xlabel("metóda")
        ax.set_ylabel("odchýlka od optima (%)")
        ax.set_title(tit)
        ax.set_ylim(bottom=0)
    fig.suptitle("Rozdelenie odchýlok od optima (krabica = kvartily, čiara = medián, fúzy = 1,5·IQR, bez odľahlých)")
    fig.tight_layout()
    fig.savefig(cesta("boxplot_odchylok.png"), dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    styl_osi(ax)
    for j, met in enumerate(METODY):
        x = np.sort(d["odch"][:, j])
        y = np.arange(1, len(x) + 1) / len(x) * 100
        krok = max(1, len(x) // 4000)
        ax.plot(np.r_[0, x[::krok], x[-1]], np.r_[0, y[::krok], 100], color=FARBY[met], lw=2, label=met)
    ax.set_xscale("symlog", linthresh=1)
    ax.set_xlabel("odchýlka od optima (%, symlog mierka)")
    ax.set_ylabel("podiel úloh s odchýlkou ≤ x (%)")
    ax.set_title("Empirická distribučná funkcia odchýlky od optima")
    ax.set_ylim(0, 100)
    ax.legend(title="metóda", frameon=False)
    fig.tight_layout()
    fig.savefig(cesta("ecdf_odchylky.png"), dpi=150)
    plt.close(fig)

    por = poradia(d["z"])
    fig, ax = plt.subplots(figsize=(8, 4.5))
    styl_osi(ax)
    odtiene = {1: 1.0, 2: 0.6, 3: 0.3}
    for j, met in enumerate(METODY):
        zac = 0.0
        for r in (1, 2, 3):
            v = 100 * np.mean(por[:, j] == r)
            ax.barh(j, v, left=zac, color=FARBY[met], alpha=odtiene[r], edgecolor="white", lw=2)
            if v > 4:
                ax.text(zac + v / 2, j, f"{r}. miesto\n{f(v, 1)} %", ha="center", va="center", fontsize=8,
                        color="#0b0b0b")
            zac += v
    ax.set_yticks(range(3), METODY)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("podiel úloh (%)")
    ax.set_ylabel("metóda")
    ax.set_title("Poradie metód v tej istej úlohe podľa z (remíza = spoločné miesto)")
    fig.tight_layout()
    fig.savefig(cesta("poradie_metod.png"), dpi=150)
    plt.close(fig)

    skupiny = [(t, c) for c in (20, 100) for t in TYPY]
    fig, ax = plt.subplots(figsize=(10, 5))
    styl_osi(ax)
    sirka = 0.26
    for j, met in enumerate(METODY):
        y, e = [], []
        for t, c in skupiny:
            mk = (d["typ"] == t) & (d["cena_max"] == c)
            p, lo, hi = priemer_ci(d["odch"][mk, j])
            y.append(p); e.append(hi - p)
        x = np.arange(len(skupiny)) + (j - 1) * sirka
        ax.bar(x, y, sirka * 0.92, yerr=e, color=FARBY[met], label=met, capsize=2,
               error_kw={"ecolor": "#52514e", "lw": 1})
    ax.set_xticks(range(len(skupiny)), [f"{TYPY_POPIS[t]}\nceny 1–{c}" for t, c in skupiny], fontsize=8)
    ax.set_xlabel("typ úlohy a cenový rozsah")
    ax.set_ylabel("priemerná odchýlka od optima (%)")
    ax.set_title("Odchýlka od optima podľa typu úlohy a cenového rozsahu (úsečka = 95 % IS)")
    ax.legend(title="metóda", frameon=False)
    fig.tight_layout()
    fig.savefig(cesta("odchylka_typ_cena.png"), dpi=150)
    plt.close(fig)
    return subory


def suhrn(d, param, csv_cesta, nazov, grafy, md_cesta, trvanie_nacitania):
    N = len(d["id"])
    L = []
    rel = lambda p: os.path.relpath(p, os.path.dirname(md_cesta)).replace("\\", "/")
    L.append(f"# Súhrn výsledkov – beh `{nazov}`\n")
    L.append("Vygenerované skriptom `analyza.py` z CSV; všetky čísla sú dopočítateľné spustením "
             f"`.venv\\Scripts\\python.exe analyza.py {nazov}`.\n")

    L.append("## Parametre behu\n")
    pg = param.get("parametre_generatora", {})
    riadky = [
        ["súbor", f"`vysledky/{os.path.basename(csv_cesta)}`"],
        ["seed", param.get("seed", "–")],
        ["počet úloh N", f"{N:,}".replace(",", " ")],
        ["m, n", f"{pg.get('m_rozsah')}, {pg.get('n_rozsah')} (nezávisle)"],
        ["ceny", ", ".join(f"{k}: {v}" for k, v in pg.get("ceny", {}).items())],
        ["typ úlohy", ", ".join(f"{k}: {v}" for k, v in pg.get("typ", {}).items())],
        ["kapacity – základ, prebytok", f"{pg.get('kapacity_zaklad')}, {pg.get('prebytok_podiel')}"],
        ["procesy / blok", f"{param.get('procesy')} / {param.get('blok')}"],
        ["trvanie behu", f"{f(param.get('trvanie_behu_s', np.nan), 1)} s"],
        ["chyby v behu", param.get("pocet_chyb", "–")],
        ["prostredie", f"Python {param.get('python')}, numpy {param.get('numpy')}, "
                       f"{param.get('pocitac')}, {param.get('cpu_logicke')} log. CPU"],
        ["dátum behu", param.get("datum", "–")],
    ]
    L.append(tabulka(["parameter", "hodnota"], riadky) + "\n")
    L.append("Odchýlka = (z − z*) / z* · 100 %. Časy sú merané `perf_counter_ns` vnútri procesu pri "
             f"{param.get('procesy')} paralelných procesoch – absolútne hodnoty sú orientačné, "
             "porovnanie metód je spravodlivé (rovnaké podmienky). Intervaly v hranatých zátvorkách = 95 % "
             "interval spoľahlivosti (priemer: normálna aproximácia; podiel: Wilson; medián a kvartily: "
             "neparametrický z poradových štatistík).\n")

    zopt_zhoda = bool(np.all(d["z_opt"] == d["z_opt"][:, :1]))
    z_ge = bool(np.all(d["z"] >= d["z_opt"]))
    opt_zhoda = bool(np.all(d["opt"] == (d["z"] == d["z_opt"])))
    L.append(f"Kontrola dát: z* rovnaké pre všetky 3 metódy v úlohe: **{'áno' if zopt_zhoda else 'NIE'}**; "
             f"z ≥ z* všade: **{'áno' if z_ge else 'NIE'}**; stĺpec `optimum` = (z = z*): "
             f"**{'áno' if opt_zhoda else 'NIE'}**.\n")

    L.append("## 1. Celkové porovnanie – správnosť\n")
    r = []
    for j, met in enumerate(METODY):
        o = d["odch"][:, j]
        r.append([f"**{met}**",
                  fci(podiel_ci(int(d["opt"][:, j].sum()), N)),
                  fci(priemer_ci(o)),
                  fci(kvantil_ci(o, 0.5)),
                  fci(kvantil_ci(o, 0.25)),
                  fci(kvantil_ci(o, 0.75)),
                  f(o.max(), 1)])
    L.append(tabulka(["metóda", "trafila optimum (%)", "priemer odchýlky (%)", "medián (%)",
                      "1. kvartil (%)", "3. kvartil (%)", "max (%)"], r) + "\n")

    L.append("## 2. Celkové porovnanie – efektívnosť\n")
    r = []
    for j, met in enumerate(METODY):
        k = d["kroky"][:, j].astype(float)
        r.append([f"**{met}**",
                  fci(priemer_ci(k)), f(np.median(k), 0),
                  f"{fci(priemer_ci(d['t_met'][:, j]), 1)} / {f(np.median(d['t_met'][:, j]), 1)}",
                  f"{fci(priemer_ci(d['t_modi'][:, j]), 1)} / {f(np.median(d['t_modi'][:, j]), 1)}",
                  f"{fci(priemer_ci(d['t_spolu'][:, j]), 1)} / {f(np.median(d['t_spolu'][:, j]), 1)}"])
    L.append(tabulka(["metóda", "kroky MODI – priemer", "kroky MODI – medián",
                      "čas metódy (µs) priemer / medián", "čas MODI (µs) priemer / medián",
                      "celkový čas (µs) priemer / medián"], r) + "\n")
    najr = np.argmin(d["t_spolu"], axis=1)
    najk = d["kroky"] == d["kroky"].min(axis=1, keepdims=True)
    L.append(tabulka(["metóda", "najkratší celkový čas v úlohe (%)", "najmenej krokov MODI v úlohe, vrátane remíz (%)",
                      "najrýchlejšia samotná metóda (%)"],
                     [[met, f(100 * np.mean(najr == j)), f(100 * np.mean(najk[:, j])),
                       f(100 * np.mean(np.argmin(d['t_met'], axis=1) == j))] for j, met in enumerate(METODY)]) + "\n")

    L.append("## 3. Párové porovnanie na tej istej úlohe\n")
    por = poradia(d["z"])
    r = []
    for j, met in enumerate(METODY):
        r.append([f"**{met}**"] + [fci(podiel_ci(int(np.sum(por[:, j] == k)), N)) for k in (1, 2, 3)]
                 + [f(100 * np.mean((por[:, j] == 1) & (np.sum(por == 1, axis=1) == 1)))])
    L.append(tabulka(["metóda", "1. miesto (%)", "2. miesto (%)", "3. miesto (%)", "sama 1. (bez remízy) (%)"], r) + "\n")
    z = d["z"]
    vse_rem = np.mean((z[:, 0] == z[:, 1]) & (z[:, 1] == z[:, 2])) * 100
    poradie_ok = np.mean((z[:, 2] <= z[:, 1]) & (z[:, 1] <= z[:, 0]))
    poradie_ostre = np.mean((z[:, 2] < z[:, 1]) & (z[:, 1] < z[:, 0]))
    L.append(f"- Úlohy, kde platí **z(VAM) ≤ z(IM) ≤ z(SZR)**: **{fci(podiel_ci(int(round(poradie_ok * N)), N))} %** "
             f"(ostro VAM < IM < SZR: {f(100 * poradie_ostre)} %).")
    L.append(f"- Všetky tri metódy rovnaké z: {f(vse_rem)} %.\n")

    L.append("Párové testy (Wilcoxonov znamienkový poradový test na rozdieloch odchýlky v tej istej úlohe, "
             "obojstranný; nulové rozdiely vynechané):\n")
    r = []
    for a, b in [("VAM", "IM"), ("VAM", "SZR"), ("IM", "SZR")]:
        ia, ib = METODY.index(a), METODY.index(b)
        rozd = d["odch"][:, ia] - d["odch"][:, ib]
        test = stats.wilcoxon(rozd, zero_method="wilcox", alternative="two-sided")
        r.append([f"{a} vs {b}", f(100 * np.mean(z[:, ia] < z[:, ib])), f(100 * np.mean(z[:, ia] == z[:, ib])),
                  f(100 * np.mean(z[:, ia] > z[:, ib])), fci(priemer_ci(rozd)), f(np.median(rozd)),
                  p_text(test.pvalue)])
    L.append(tabulka(["dvojica A vs B", "A lepšia (%)", "remíza (%)", "B lepšia (%)",
                      "priemer rozdielu odchýlky A − B (p. b.)", "medián rozdielu (p. b.)", "p-hodnota"], r) + "\n")
    r = []
    for meno, x in [("kroky MODI", d["kroky"].astype(float)), ("celkový čas (µs)", d["t_spolu"]),
                    ("čas metódy (µs)", d["t_met"])]:
        rozd = x[:, 2] - x[:, 1]
        test = stats.wilcoxon(rozd, zero_method="wilcox")
        r.append([meno, f(100 * np.mean(rozd < 0)), f(100 * np.mean(rozd == 0)), f(100 * np.mean(rozd > 0)),
                  fci(priemer_ci(rozd)), f(np.median(rozd)), p_text(test.pvalue)])
    L.append("VAM vs IM – efektívnosť (párovo):\n")
    L.append(tabulka(["veličina", "VAM menej (%)", "rovnako (%)", "IM menej (%)", "priemer rozdielu VAM − IM",
                      "medián rozdielu", "p-hodnota (Wilcoxon)"], r) + "\n")

    def blok_skupin(titul, popis_sk, masky):
        L.append(f"### {titul}\n")
        r = []
        for meno, mk in zip(popis_sk, masky):
            nn = int(mk.sum())
            if nn == 0:
                continue
            for j, met in enumerate(METODY):
                r.append([meno if j == 0 else "", f"{nn}" if j == 0 else "", met,
                          f(podiel_ci(int(d["opt"][mk, j].sum()), nn)[0]),
                          fci(priemer_ci(d["odch"][mk, j])), f(np.median(d["odch"][mk, j])),
                          f(np.mean(d["kroky"][mk, j]), 1), f(np.mean(d["t_spolu"][mk, j]), 0),
                          f(100 * np.mean(por[mk, j] == 1), 1)])
        L.append(tabulka(["skupina", "N", "metóda", "optimum (%)", "priemer odchýlky (%) [95 % IS]",
                          "medián odch. (%)", "kroky MODI", "celk. čas (µs)", "1. miesto (%)"], r) + "\n")

    L.append("## 4. Rozdelenie podľa vlastností úlohy\n")
    blok_skupin("4.1 Podľa veľkosti m·n", [f"m·n {a}–{b}" for a, b in SKUPINY_MN],
                [(d["mn"] >= a) & (d["mn"] <= b) for a, b in SKUPINY_MN])
    mx = np.maximum(d["m"], d["n"])
    sk = [(3, 5), (6, 8), (9, 11), (12, 14), (15, 17), (18, 20)]
    blok_skupin("4.2 Podľa max(m, n)", [f"max {a}–{b}" for a, b in sk], [(mx >= a) & (mx <= b) for a, b in sk])
    blok_skupin("4.3 Podľa cenového rozsahu", ["ceny 1–20", "ceny 1–100"],
                [d["cena_max"] == 20, d["cena_max"] == 100])
    blok_skupin("4.4 Podľa typu úlohy", [TYPY_POPIS[t] for t in TYPY], [d["typ"] == t for t in TYPY])

    L.append("### 4.5 Podľa degenerácie východiskového riešenia\n")
    L.append("Degenerácia sa týka konkrétnej metódy (počet bázických polí s nulovou prepravou), preto sa "
             "skupiny tvoria pre každú metódu zvlášť.\n")
    r = []
    for j, met in enumerate(METODY):
        dg = d["deg"][:, j]
        r.append([f"**{met}**", fci(podiel_ci(int((dg > 0).sum()), N)), f(dg.mean(), 3), int(dg.max())])
    L.append(tabulka(["metóda", "degenerované riešenie (%)", "priemerný počet nulových bázických polí",
                      "max"], r) + "\n")
    r = []
    for j, met in enumerate(METODY):
        for meno, mk in [("nedegenerované", d["deg"][:, j] == 0), ("degenerované", d["deg"][:, j] > 0)]:
            nn = int(mk.sum())
            if nn == 0:
                r.append([met, meno, 0, "–", "–", "–", "–"]); continue
            r.append([met, meno, nn, f(100 * d["opt"][mk, j].mean()), fci(priemer_ci(d["odch"][mk, j])),
                      f(d["kroky"][mk, j].mean(), 1), f(d["t_spolu"][mk, j].mean(), 0)])
    L.append(tabulka(["metóda", "skupina", "N", "optimum (%)", "priemer odchýlky (%) [95 % IS]",
                      "kroky MODI", "celk. čas (µs)"], r) + "\n")
    L.append("Pozn.: degenerácia súvisí s veľkosťou a typom úlohy (napr. ceny 1–20 → viac remíz), "
             "takže rozdiely v tejto tabuľke nie sú čistým účinkom degenerácie.\n")

    L.append("## 5. Grafy\n")
    popisy = {
        "odchylka_vs_velkost.png": "Priemerná odchýlka od optima vs. veľkosť m·n",
        "kroky_modi_vs_velkost.png": "Priemerný počet krokov MODI vs. veľkosť m·n",
        "optimum_vs_velkost.png": "Podiel trafeného optima vs. veľkosť m·n",
        "cas_celkovy_vs_velkost.png": "Celkový čas (metóda + MODI) vs. veľkosť m·n",
        "cas_metody_vs_velkost.png": "Čas samotnej metódy vs. veľkosť m·n",
        "boxplot_odchylok.png": "Krabicové grafy odchýlok",
        "ecdf_odchylky.png": "Empirická distribučná funkcia odchýlky",
        "poradie_metod.png": "Poradie metód v tej istej úlohe",
        "odchylka_typ_cena.png": "Odchýlka podľa typu úlohy a cenového rozsahu",
    }
    for g in grafy:
        meno = os.path.basename(g)
        L.append(f"- {popisy.get(meno, meno)}: [`{rel(g)}`]({rel(g)})")
    L.append("")
    for g in grafy:
        L.append(f"![{popisy.get(os.path.basename(g), '')}]({rel(g)})\n")

    L.append("## 6. Záver\n")
    pr_odch = d["odch"].mean(axis=0)
    med_odch = np.median(d["odch"], axis=0)
    opt = 100 * d["opt"].mean(axis=0)
    kroky = d["kroky"].mean(axis=0)
    tsp = d["t_spolu"].mean(axis=0)
    tmed = np.median(d["t_spolu"], axis=0)
    tmet = d["t_met"].mean(axis=0)
    js = int(np.argmin(pr_odch))
    je = int(np.argmin(tsp))
    poradie_odch = " < ".join(METODY[i] for i in np.argsort(pr_odch))
    L.append(f"- **Najsprávnejšia metóda: {METODY[js]}** – najmenšia priemerná odchýlka "
             f"({f(pr_odch[js])} %, medián {f(med_odch[js])} %) a najčastejšie trafí optimum ({f(opt[js])} %). "
             f"Poradie podľa priemernej odchýlky: {poradie_odch}. VAM je v tej istej úlohe na 1. mieste "
             f"v {f(100 * np.mean(por[:, 2] == 1))} % úloh; z(VAM) ≤ z(IM) ≤ z(SZR) platí v {f(100 * poradie_ok)} % úloh.")
    jk = int(np.argmin(kroky))
    rozd_t = d["t_spolu"][:, 2] - d["t_spolu"][:, 1]
    L.append(f"- **Najefektívnejšia podľa celkového času (metóda + MODI): {METODY[je]}** – priemer "
             f"{f(tsp[je], 0)} µs, medián {f(tmed[je], 0)} µs (SZR / IM / VAM = "
             f"{' / '.join(f(x, 0) for x in tsp)} µs). Najkratší celkový čas má v "
             f"{f(100 * np.mean(najr == je))} % úloh.")
    L.append(f"- **Najmenej krokov MODI: {METODY[jk]}** – priemerne {f(kroky[jk], 1)} krokov "
             f"(SZR / IM / VAM = {' / '.join(f(x, 1) for x in kroky)}); najmenej krokov má v "
             f"{f(100 * np.mean(najk[:, jk]))} % úloh (s remízami).")
    L.append(f"- **IM vs. VAM v čase:** VAM ušetrí čas MODI ({f(d['t_modi'][:, 1].mean(), 0)} → "
             f"{f(d['t_modi'][:, 2].mean(), 0)} µs), ale samotná VAM trvá dlhšie ({f(tmet[1], 0)} → "
             f"{f(tmet[2], 0)} µs, počítanie diferencií v každom kroku). Párovo je VAM celkovo pomalšia "
             f"priemerne o {f(rozd_t.mean(), 0)} µs ({f(100 * rozd_t.mean() / tsp[1], 1)} % času IM) a rýchlejšia "
             f"len v {f(100 * np.mean(rozd_t < 0))} % úloh – rozdiel je malý a závisí od implementácie "
             f"(Python); SZR je síce najrýchlejšia samotná metóda ({f(tmet[0], 0)} µs), no kvôli MODI je celkovo "
             "najpomalšia.")
    L.append(f"- **Celkovo:** VAM je jednoznačne najsprávnejšia a potrebuje najmenej krokov MODI; v celkovom "
             f"čase je {METODY[je]} {'mierne ' if abs(tsp[2] - tsp[1]) / tsp[1] < 0.15 else ''}vpredu. "
             "SZR je vo všetkých podmienkach výrazne najhoršia.")
    mal = (d["mn"] <= 49)
    vel = (d["mn"] >= 250)
    L.append(f"- **Vplyv veľkosti:** pri malých úlohách (m·n ≤ 49) trafí VAM optimum v "
             f"{f(100 * d['opt'][mal, 2].mean())} % (IM {f(100 * d['opt'][mal, 1].mean())} %), pri veľkých "
             f"(m·n ≥ 250) už len v {f(100 * d['opt'][vel, 2].mean())} %; počet krokov MODI rastie s veľkosťou "
             f"pri všetkých metódach (VAM {f(d['kroky'][mal, 2].mean(), 1)} → {f(d['kroky'][vel, 2].mean(), 1)}, "
             f"SZR {f(d['kroky'][mal, 0].mean(), 1)} → {f(d['kroky'][vel, 0].mean(), 1)}).")
    tmal = d["t_spolu"][mal].mean(axis=0)
    L.append(f"- Pri malých úlohách (m·n ≤ 49) je priemerný celkový čas SZR / IM / VAM = "
             f"{f(tmal[0], 0)} / {f(tmal[1], 0)} / {f(tmal[2], 0)} µs, pri veľkých (m·n ≥ 250) "
             f"{' / '.join(f(x, 0) for x in d['t_spolu'][vel].mean(axis=0))} µs.")
    c20, c100 = d["cena_max"] == 20, d["cena_max"] == 100
    L.append(f"- **Cenový rozsah:** pri cenách 1–20 trafí VAM optimum v {f(100 * d['opt'][c20, 2].mean())} %, "
             f"pri 1–100 v {f(100 * d['opt'][c100, 2].mean())} %; priemerná odchýlka VAM "
             f"{f(d['odch'][c20, 2].mean())} % vs. {f(d['odch'][c100, 2].mean())} %.")
    L.append(f"- **Typ úlohy:** priemerná odchýlka VAM – " + ", ".join(
        f"{TYPY_POPIS[t]} {f(d['odch'][d['typ'] == t, 2].mean())} %" for t in TYPY) +
        "; poradie metód sa podľa typu nemení (pozri 4.4).")
    L.append("")
    with open(md_cesta, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))


def main():
    t0 = time.perf_counter()
    csv_cesta, json_cesta, nazov = najdi_subory(sys.argv[1] if len(sys.argv) > 1 else None)
    param = {}
    if os.path.exists(json_cesta):
        with open(json_cesta, encoding="utf-8") as fh:
            param = json.load(fh)
    print(f"Načítavam {csv_cesta} ...")
    d = nacitaj(csv_cesta)
    print(f"  {len(d['id'])} úloh, {time.perf_counter() - t0:.1f} s")
    hlavny = nazov == "hlavny100k"
    adr_grafy = os.path.join(KOREN, "grafy") if hlavny else os.path.join(KOREN, "grafy", nazov)
    md = os.path.join(KOREN, "vysledky", "suhrn.md" if hlavny else f"suhrn_{nazov}.md")
    grafy = vsetky_grafy(d, adr_grafy)
    print(f"  grafy: {len(grafy)} v {adr_grafy}")
    suhrn(d, param, csv_cesta, nazov, grafy, md, time.perf_counter() - t0)
    print(f"  súhrn: {md}")
    print(f"Hotovo za {time.perf_counter() - t0:.1f} s")


if __name__ == "__main__":
    main()
