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

import cesty

KOREN = str(cesty.KOREN)
METODY = ["SZR", "IM", "VAM"]
FARBY = {"SZR": "#2a78d6", "IM": "#eb6834", "VAM": "#1baf7a", "JVR": "#8e5bd0", "MDD": "#0f8b8d", "PVM": "#d4a017"}
ROHY = {"SZR", "JVR"}
CIARY = {"JVR": (0, (5, 3)), "MDD": (0, (5, 3))}
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
    prve_id = stl["id"][0]
    METODY[:] = [mt for i_, mt in zip(stl["id"], stl["metoda"]) if i_ == prve_id]
    if not {"SZR", "IM", "VAM"} <= set(METODY):
        sys.exit("Vyhodnotenie potrebuje metódy z prednášky SZR, IM a VAM (v behu sú: " + ", ".join(METODY) + ")")
    k_ = len(METODY)
    met = np.array([METODY.index(x) for x in stl["metoda"]], dtype=np.int64)
    ids = np.array(stl["id"], dtype=np.int64)
    poradie = np.lexsort((met, ids))
    ids, met = ids[poradie], met[poradie]
    N = len(ids) // k_
    if len(ids) != k_ * N or not (np.all(met.reshape(N, k_) == list(range(k_)))
                                  and np.all(ids.reshape(N, k_) == ids.reshape(N, k_)[:, :1])):
        sys.exit(f"CSV nemá pre každú úlohu presne {k_} riadky ({', '.join(METODY)})")

    def pole(k, dt):
        return np.array(stl[k], dtype=dt)[poradie].reshape(N, k_)

    d = {
        "id": ids.reshape(N, k_)[:, 0],
        "m": pole("m", np.int64)[:, 0],
        "n": pole("n", np.int64)[:, 0],
        "typ": np.array(stl["typ"], dtype=object)[poradie].reshape(N, k_)[:, 0],
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
        ax.plot(x, y, marker="o", linestyle=CIARY.get(met, "-"), color=FARBY[met], lw=2, ms=4, label=met)
        ax.fill_between(x, lo, hi, color=FARBY[met], alpha=0.2, lw=0)
    ax.set_xlabel("veľkosť úlohy m·n (počet polí tabuľky, skupiny po 25)")
    ax.set_ylabel(ylabel)
    ax.set_title(titul)
    if logy:
        ax.set_yscale("log")
        form = matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}".replace(".", ","))
        ax.yaxis.set_major_formatter(form)
        dolna, horna = ax.get_ylim()
        ax.yaxis.set_minor_formatter(form if horna / max(dolna, 1e-12) < 30 else matplotlib.ticker.NullFormatter())
    elif ylim0:
        ax.set_ylim(bottom=0)
    ax.legend(title="metóda", frameon=False, ncol=2 if len(METODY) > 3 else 1)
    fig.text(0.99, 0.01, "pás = 95 % interval spoľahlivosti" + ("  ·  JVR (prerušovaná) leží presne na SZR"
             if "JVR" in METODY else ""), ha="right", fontsize=8, color="#52514e")
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

    detail = [m for m in METODY if m not in ROHY]
    fig, axy = plt.subplots(1, 2, figsize=(12 if len(METODY) > 3 else 10, 5),
                            gridspec_kw={"width_ratios": [3, 2]})
    for ax, mets, tit in [(axy[0], METODY, "všetky metódy"),
                          (axy[1], detail, "detail " + ", ".join(detail))]:
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
        ax.plot(np.r_[0, x[::krok], x[-1]], np.r_[0, y[::krok], 100], color=FARBY[met], lw=2, label=met,
                linestyle=CIARY.get(met, "-"))
    ax.set_xscale("symlog", linthresh=1)
    ax.set_xlabel("odchýlka od optima (%, symlog mierka)")
    ax.set_ylabel("podiel úloh s odchýlkou ≤ x (%)")
    ax.set_title("Empirická distribučná funkcia odchýlky od optima")
    if "JVR" in METODY:
        fig.text(0.99, 0.01, "JVR (prerušovaná) leží presne na SZR", ha="right", fontsize=8, color="#52514e")
    ax.set_ylim(0, 100)
    ax.legend(title="metóda", frameon=False, ncol=2 if len(METODY) > 3 else 1)
    fig.tight_layout()
    fig.savefig(cesta("ecdf_odchylky.png"), dpi=150)
    plt.close(fig)

    por = poradia(d["z"])
    fig, ax = plt.subplots(figsize=(9, 1.2 + 1.1 * len(METODY)))
    styl_osi(ax)
    odtiene = {r: a for r, a in zip(range(1, len(METODY) + 1), (1.0, 0.6, 0.35, 0.22, 0.14, 0.09, 0.06))}
    for j, met in enumerate(METODY):
        zac = 0.0
        for r in range(1, len(METODY) + 1):
            v = 100 * np.mean(por[:, j] == r)
            ax.barh(j, v, left=zac, color=FARBY[met], alpha=odtiene[r], edgecolor="white", lw=2)
            if v > 8:
                ax.text(zac + v / 2, j, f"{r}. miesto\n{f(v, 1)} %", ha="center", va="center", fontsize=8,
                        color="#0b0b0b")
            zac += v
    ax.set_yticks(range(len(METODY)), METODY)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("podiel úloh (%)")
    ax.set_ylabel("metóda")
    ax.set_title("Poradie metód v tej istej úlohe podľa z (remíza = spoločné miesto)")
    fig.tight_layout()
    fig.savefig(cesta("poradie_metod.png"), dpi=150)
    plt.close(fig)

    skupiny = [(t, c) for c in (20, 100) for t in TYPY]
    fig, ax = plt.subplots(figsize=(12 if len(METODY) > 3 else 10, 5))
    styl_osi(ax)
    sirka = 0.8 / len(METODY)
    for j, met in enumerate(METODY):
        y, e = [], []
        for t, c in skupiny:
            mk = (d["typ"] == t) & (d["cena_max"] == c)
            p, lo, hi = priemer_ci(d["odch"][mk, j])
            y.append(p); e.append(hi - p)
        x = np.arange(len(skupiny)) + (j - (len(METODY) - 1) / 2) * sirka
        ax.bar(x, y, sirka * 0.92, yerr=e, color=FARBY[met], label=met, capsize=2,
               error_kw={"ecolor": "#52514e", "lw": 1})
    ax.set_xticks(range(len(skupiny)), [f"{TYPY_POPIS[t]}\nceny 1–{c}" for t, c in skupiny], fontsize=8)
    ax.set_xlabel("typ úlohy a cenový rozsah")
    ax.set_ylabel("priemerná odchýlka od optima (%)")
    ax.set_title("Odchýlka od optima podľa typu úlohy a cenového rozsahu (úsečka = 95 % IS)")
    ax.legend(title="metóda", frameon=False, ncol=2 if len(METODY) > 3 else 1)
    fig.tight_layout()
    fig.savefig(cesta("odchylka_typ_cena.png"), dpi=150)
    plt.close(fig)
    return subory


def suhrn(d, param, csv_cesta, nazov, grafy, md_cesta, trvanie_nacitania):
    N = len(d["id"])
    S, I, V = METODY.index("SZR"), METODY.index("IM"), METODY.index("VAM")
    k_ = len(METODY)
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
    L.append(f"Metódy v behu: {', '.join(METODY)}.\n")
    L.append(f"Kontrola dát: z* rovnaké pre všetky metódy ({k_}) v úlohe: **{'áno' if zopt_zhoda else 'NIE'}**; "
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
        r.append([f"**{met}**"] + [fci(podiel_ci(int(np.sum(por[:, j] == k)), N)) for k in range(1, k_ + 1)]
                 + [f(100 * np.mean((por[:, j] == 1) & (np.sum(por == 1, axis=1) == 1)))])
    L.append(tabulka(["metóda"] + [f"{k}. miesto (%)" for k in range(1, k_ + 1)] + ["sama 1. (bez remízy) (%)"], r)
             + "\n")
    z = d["z"]
    vse_rem = np.mean(np.all(z == z[:, :1], axis=1)) * 100
    poradie_ok = np.mean((z[:, V] <= z[:, I]) & (z[:, I] <= z[:, S]))
    poradie_ostre = np.mean((z[:, V] < z[:, I]) & (z[:, I] < z[:, S]))
    L.append(f"- Úlohy, kde platí **z(VAM) ≤ z(IM) ≤ z(SZR)**: **{fci(podiel_ci(int(round(poradie_ok * N)), N))} %** "
             f"(ostro VAM < IM < SZR: {f(100 * poradie_ostre)} %).")
    L.append(f"- Všetky metódy rovnaké z: {f(vse_rem)} %.\n")

    L.append("Párové testy (Wilcoxonov znamienkový poradový test na rozdieloch odchýlky v tej istej úlohe, "
             "obojstranný; nulové rozdiely vynechané):\n")
    r = []
    dvojice = [("VAM", "IM"), ("VAM", "SZR"), ("IM", "SZR"), ("JVR", "SZR"), ("MDD", "VAM"), ("PVM", "VAM"),
               ("PVM", "MDD")]
    for a, b in [(a, b) for a, b in dvojice if a in METODY and b in METODY]:
        ia, ib = METODY.index(a), METODY.index(b)
        rozd = d["odch"][:, ia] - d["odch"][:, ib]
        if np.all(rozd == 0):
            p_hod = "– (vždy rovnaké)"
        else:
            p_hod = p_text(stats.wilcoxon(rozd, zero_method="wilcox", alternative="two-sided").pvalue)
        r.append([f"{a} vs {b}", f(100 * np.mean(z[:, ia] < z[:, ib])), f(100 * np.mean(z[:, ia] == z[:, ib])),
                  f(100 * np.mean(z[:, ia] > z[:, ib])), fci(priemer_ci(rozd)), f(np.median(rozd)), p_hod])
    L.append(tabulka(["dvojica A vs B", "A lepšia (%)", "remíza (%)", "B lepšia (%)",
                      "priemer rozdielu odchýlky A − B (p. b.)", "medián rozdielu (p. b.)", "p-hodnota"], r) + "\n")
    r = []
    for meno, x in [("kroky MODI", d["kroky"].astype(float)), ("celkový čas (µs)", d["t_spolu"]),
                    ("čas metódy (µs)", d["t_met"])]:
        rozd = x[:, V] - x[:, I]
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
    jk = int(np.argmin(kroky))
    zoznam = " / ".join(METODY)
    poradie_odch = " < ".join(METODY[i] for i in np.argsort(pr_odch))
    L.append(f"- **Najsprávnejšia metóda: {METODY[js]}** – najmenšia priemerná odchýlka "
             f"({f(pr_odch[js])} %, medián {f(med_odch[js])} %) a najčastejšie trafí optimum ({f(opt[js])} %). "
             f"Poradie podľa priemernej odchýlky: {poradie_odch}. {METODY[js]} je v tej istej úlohe na 1. mieste "
             f"v {f(100 * np.mean(por[:, js] == 1))} % úloh.")
    if js != V:
        L.append(f"- **Z metód z prednášky je najsprávnejšia VAM** ({f(pr_odch[V])} %); z(VAM) ≤ z(IM) ≤ z(SZR) "
                 f"platí v {f(100 * poradie_ok)} % úloh.")
    else:
        L.append(f"- z(VAM) ≤ z(IM) ≤ z(SZR) platí v {f(100 * poradie_ok)} % úloh.")
    L.append(f"- **Najefektívnejšia podľa celkového času (metóda + MODI): {METODY[je]}** – priemer "
             f"{f(tsp[je], 0)} µs, medián {f(tmed[je], 0)} µs ({zoznam} = "
             f"{' / '.join(f(x, 0) for x in tsp)} µs). Najkratší celkový čas má v "
             f"{f(100 * np.mean(najr == je))} % úloh.")
    L.append(f"- **Najmenej krokov MODI: {METODY[jk]}** – priemerne {f(kroky[jk], 1)} krokov "
             f"({zoznam} = {' / '.join(f(x, 1) for x in kroky)}); najmenej krokov má v "
             f"{f(100 * np.mean(najk[:, jk]))} % úloh (s remízami).")
    rozd_t = d["t_spolu"][:, V] - d["t_spolu"][:, I]
    L.append(f"- **IM vs. VAM v čase:** VAM ušetrí čas MODI ({f(d['t_modi'][:, I].mean(), 0)} → "
             f"{f(d['t_modi'][:, V].mean(), 0)} µs), ale samotná VAM trvá dlhšie ({f(tmet[I], 0)} → "
             f"{f(tmet[V], 0)} µs, počítanie diferencií v každom kroku). Párovo je VAM celkovo "
             f"{'pomalšia' if rozd_t.mean() > 0 else 'rýchlejšia'} priemerne o {f(abs(rozd_t.mean()), 0)} µs "
             f"({f(100 * abs(rozd_t.mean()) / tsp[I], 1)} % času IM) – rozdiel je malý a závisí od implementácie "
             f"(Python); SZR je síce najrýchlejšia samotná metóda ({f(tmet[S], 0)} µs), no kvôli MODI je celkovo "
             "pomalá.")
    if "JVR" in METODY:
        jv = METODY.index("JVR")
        L.append(f"- **JVR (nová)** dala rovnaké z ako SZR v {f(100 * np.mean(z[:, jv] == z[:, S]))} % úloh – "
                 "juhovýchodný roh dáva vždy ten istý plán ako severozápadný.")
    if "MDD" in METODY:
        jm = METODY.index("MDD")
        L.append(f"- **MDD (nová)** má priemernú odchýlku {f(pr_odch[jm])} % (VAM {f(pr_odch[V])} %) – kvalitou "
                 f"takmer ako VAM; lepšia ako VAM je v {f(100 * np.mean(z[:, jm] < z[:, V]))} % úloh, horšia v "
                 f"{f(100 * np.mean(z[:, jm] > z[:, V]))} %.")
    if "PVM" in METODY:
        jp = METODY.index("PVM")
        L.append(f"- **PVM (nová)** má priemernú odchýlku {f(pr_odch[jp])} % a optimum trafí hneď v {f(opt[jp])} % "
                 f"úloh; lepšia ako VAM je v {f(100 * np.mean(z[:, jp] < z[:, V]))} % úloh, horšia len v "
                 f"{f(100 * np.mean(z[:, jp] > z[:, V]))} %. Samotná metóda však trvá priemerne {f(tmet[jp], 0)} µs "
                 f"(VAM {f(tmet[V], 0)} µs).")
    mal = (d["mn"] <= 49)
    vel = (d["mn"] >= 250)
    b_ = METODY[js]
    L.append(f"- **Vplyv veľkosti:** pri malých úlohách (m·n ≤ 49) trafí {b_} optimum v "
             f"{f(100 * d['opt'][mal, js].mean())} % (VAM {f(100 * d['opt'][mal, V].mean())} %, IM "
             f"{f(100 * d['opt'][mal, I].mean())} %), pri veľkých (m·n ≥ 250) v {f(100 * d['opt'][vel, js].mean())} %; "
             f"počet krokov MODI rastie s veľkosťou pri všetkých metódach ({b_} {f(d['kroky'][mal, js].mean(), 1)} → "
             f"{f(d['kroky'][vel, js].mean(), 1)}, SZR {f(d['kroky'][mal, S].mean(), 1)} → "
             f"{f(d['kroky'][vel, S].mean(), 1)}).")
    L.append(f"- Priemerný celkový čas {zoznam} pri malých úlohách (m·n ≤ 49): "
             f"{' / '.join(f(x, 0) for x in d['t_spolu'][mal].mean(axis=0))} µs, pri veľkých (m·n ≥ 250): "
             f"{' / '.join(f(x, 0) for x in d['t_spolu'][vel].mean(axis=0))} µs.")
    c20, c100 = d["cena_max"] == 20, d["cena_max"] == 100
    L.append(f"- **Cenový rozsah:** priemerná odchýlka pri cenách 1–20 / 1–100: " + ", ".join(
        f"{m} {f(d['odch'][c20, j].mean())} % / {f(d['odch'][c100, j].mean())} %" for j, m in enumerate(METODY)
        if m not in ROHY) + ".")
    L.append(f"- **Typ úlohy:** priemerná odchýlka {b_} – " + ", ".join(
        f"{TYPY_POPIS[t]} {f(d['odch'][d['typ'] == t, js].mean())} %" for t in TYPY) +
        "; poradie metód sa podľa typu nemení (pozri 4.4).")
    L.append("")
    with open(md_cesta, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))


def main(arg=None):
    t0 = time.perf_counter()
    if arg is None and len(sys.argv) > 1:
        arg = sys.argv[1]
    csv_cesta, json_cesta, nazov = najdi_subory(arg)
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
