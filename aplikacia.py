from __future__ import annotations

import csv
import json
import os
import platform
import queue
import random
import re
import subprocess
import sys
import threading
import time
import tkinter as tk
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import matplotlib

matplotlib.use("TkAgg")
import matplotlib.ticker
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import generator
import metody
import postup
import simulacia
from statistiky import HIST_HRANY, Statistiky

KOREN = Path(__file__).resolve().parent
METODY = list(metody.METODY)
FARBY = {"SZR": "#2b7bd6", "IM": "#ee6a2c", "VAM": "#1fae7a", "JVR": "#8e5bd0", "SVR": "#c0398f", "JZR": "#8a6d1e",
         "MDD": "#0f8b8d", "PVM": "#d4a017"}
POPIS_METOD = {"SZR": "severozápadný roh", "IM": "indexová metóda", "VAM": "Vogelova metóda",
               "JVR": "juhovýchodný roh (nová)", "SVR": "severovýchodný roh (nová)",
               "JZR": "juhozápadný roh (nová)", "MDD": "dvojitá diferencia (nová)",
               "PVM": "predvídavá metóda (nová)"}

if sys.platform == "win32":
    PISMO, PISMO_TUCNE, MONO = "Segoe UI", "Segoe UI Semibold", "Consolas"
elif sys.platform == "darwin":
    PISMO, PISMO_TUCNE, MONO = "Helvetica Neue", None, "Menlo"
else:
    PISMO, PISMO_TUCNE, MONO = "DejaVu Sans", None, "DejaVu Sans Mono"


def pismo(velkost: int, tucne: bool = False) -> tuple:
    if not tucne:
        return (PISMO, velkost)
    return (PISMO_TUCNE, velkost) if PISMO_TUCNE else (PISMO, velkost, "bold")


def otvor(cesta) -> None:
    cesta = str(cesta)
    if sys.platform == "win32":
        os.startfile(cesta)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", cesta])
    else:
        subprocess.Popen(["xdg-open", cesta])


POZADIE = "#f4f6f9"
KARTA = "#ffffff"
TMAVA = "#1f2a3a"
TEXT = "#1f2a3a"
SIVA = "#6b7686"
AKCENT = "#2b7bd6"
CERVENA = "#d64545"
OKRAJ = "#dde3ea"


def cislo(x: float, des: int = 0) -> str:
    s = f"{x:,.{des}f}".replace(",", " ").replace(".", ",")
    return s


def cas_text(s: float) -> str:
    if s < 60:
        return f"{s:.0f} s"
    if s < 3600:
        return f"{int(s // 60)} min {int(s % 60):02d} s"
    return f"{int(s // 3600)} h {int(s % 3600 // 60):02d} min"


def nacitaj_cele(text: str, nazov: str, od: int | None = None, do: int | None = None) -> int:
    t = text.replace(" ", "").replace(" ", "")
    if not t.lstrip("-").isdigit():
        raise ValueError(f"{nazov}: zadaj celé číslo.")
    x = int(t)
    if od is not None and x < od:
        raise ValueError(f"{nazov}: najmenej {od}.")
    if do is not None and x > do:
        raise ValueError(f"{nazov}: najviac {do}.")
    return x


SKUPINY_NAZVY = {"Z prednášky: SZR, IM, VAM": "prednaska",
                 "Len nové: JVR, SVR, JZR, MDD, PVM": "nove",
                 "Všetky metódy (8)": "vsetky"}
CAS_METODY = {"SZR": 0.0062, "IM": 0.0029, "VAM": 0.0030, "JVR": 0.0062, "SVR": 0.0062, "JZR": 0.0062,
              "MDD": 0.0035, "PVM": 0.11}


def beh_na_pozadi(pocet: int, procesy: int, seed: int, p: dict, blok: int,
                  fronta: queue.Queue, stop: threading.Event, mena: list[str] | None = None):
    try:
        with ProcessPoolExecutor(max_workers=procesy) as ex:
            dalsi = 0
            bezi = set()
            while (dalsi < pocet or bezi) and not stop.is_set():
                while dalsi < pocet and len(bezi) < procesy * 3:
                    ids = list(range(dalsi, min(dalsi + blok, pocet)))
                    dalsi += len(ids)
                    bezi.add(ex.submit(simulacia.spracuj_blok, seed, ids, p, mena))
                hotove, bezi = wait(bezi, timeout=0.3, return_when=FIRST_COMPLETED)
                for f in hotove:
                    fronta.put(("data", f.result()))
            for f in bezi:
                f.cancel()
            ex.shutdown(wait=True, cancel_futures=True)
    except Exception as e:
        fronta.put(("chyba", f"{type(e).__name__}: {e}"))
    fronta.put(("koniec", stop.is_set()))


class Aplikacia(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Dopravná úloha – porovnanie metód SZR, IM, VAM")
        self.configure(bg=POZADIE)
        self.geometry("1440x900")
        self.minsize(1150, 720)
        try:
            if sys.platform.startswith("linux"):
                self.attributes("-zoomed", True)
            else:
                self.state("zoomed")
        except tk.TclError:
            pass
        self._styly()

        self.fronta: queue.Queue = queue.Queue()
        self.stop = threading.Event()
        self.vlakno: threading.Thread | None = None
        self.stat = Statistiky()
        self.bezi = False
        self.zatvarat = False
        self.f_csv = None
        self.w_csv = None
        self.posledny_beh: str | None = None
        self.posledne_kreslenie = 0.0

        self._hlavicka()
        zalozky = ttk.Notebook(self)
        zalozky.pack(fill="both", expand=True, padx=14, pady=(8, 14))
        self.tab_sim = ttk.Frame(zalozky, style="Pozadie.TFrame")
        self.tab_uk = ttk.Frame(zalozky, style="Pozadie.TFrame")
        self.tab_vl = ttk.Frame(zalozky, style="Pozadie.TFrame")
        zalozky.add(self.tab_sim, text="  Simulácia  ")
        zalozky.add(self.tab_vl, text="  Vlastná úloha  ")
        zalozky.add(self.tab_uk, text="  Ukážka náhodnej úlohy  ")
        self._tab_simulacia()
        self._tab_vlastna()
        self._tab_ukazka()

        self.protocol("WM_DELETE_WINDOW", self._zatvor)
        self.report_callback_exception = lambda typ, chyba, tb: messagebox.showerror(
            "Neočakávaná chyba", f"{typ.__name__}: {chyba}", parent=self)
        self.after(150, self._citaj_frontu)

    def _styly(self):
        st = ttk.Style(self)
        st.theme_use("clam")
        zaklad = pismo(10)
        self.option_add("*Font", zaklad)
        st.configure(".", background=POZADIE, foreground=TEXT, font=zaklad)
        st.configure("Pozadie.TFrame", background=POZADIE)
        st.configure("Karta.TFrame", background=KARTA)
        st.configure("Karta.TLabel", background=KARTA, foreground=TEXT)
        st.configure("Sivy.TLabel", background=KARTA, foreground=SIVA, font=pismo(9))
        st.configure("Nadpis.TLabel", background=KARTA, foreground=TEXT, font=pismo(11, True))
        st.configure("Velke.TLabel", background=KARTA, foreground=TEXT, font=pismo(18, True))
        st.configure("Karta.TCheckbutton", background=KARTA)
        st.configure("Karta.TRadiobutton", background=KARTA)
        st.configure("TNotebook", background=POZADIE, borderwidth=0)
        st.configure("TNotebook.Tab", padding=(14, 6), font=pismo(10, True))
        st.map("TNotebook.Tab", background=[("selected", KARTA)], foreground=[("selected", AKCENT)])
        st.configure("TEntry", padding=4)
        st.configure("TSpinbox", padding=3)
        st.configure("Akcent.TButton", background=AKCENT, foreground="white",
                     font=pismo(11, True), padding=(12, 8), borderwidth=0)
        st.map("Akcent.TButton", background=[("disabled", "#9dbbe0"), ("active", "#1f66b8")])
        st.configure("Stop.TButton", background=CERVENA, foreground="white",
                     font=pismo(11, True), padding=(12, 8), borderwidth=0)
        st.map("Stop.TButton", background=[("disabled", "#e6b0b0"), ("active", "#b83434")])
        st.configure("Maly.TButton", padding=(6, 2), font=pismo(9))
        st.configure("Horizontal.TProgressbar", troughcolor="#e6ebf1", background=AKCENT,
                     bordercolor="#e6ebf1", lightcolor=AKCENT, darkcolor=AKCENT, thickness=16)
        st.configure("Treeview", rowheight=25, font=pismo(10), background=KARTA,
                     fieldbackground=KARTA, bordercolor=OKRAJ)
        st.configure("Treeview.Heading", font=pismo(9, True), background="#eef2f7",
                     foreground=SIVA, relief="flat")

    def _karta(self, rodic, nadpis: str | None = None, **pack):
        ram = tk.Frame(rodic, bg=KARTA, highlightbackground=OKRAJ, highlightthickness=1)
        ram.pack(**pack)
        vnutro = ttk.Frame(ram, style="Karta.TFrame", padding=(14, 6))
        vnutro.pack(fill="both", expand=True)
        if nadpis:
            ttk.Label(vnutro, text=nadpis, style="Nadpis.TLabel").pack(anchor="w", pady=(0, 4))
        return vnutro

    def _hlavicka(self):
        h = tk.Frame(self, bg=TMAVA, height=64)
        h.pack(fill="x")
        tk.Label(h, text="Dopravná úloha", bg=TMAVA, fg="white",
                 font=pismo(17, True)).pack(side="left", padx=(20, 10), pady=12)
        tk.Label(h, text="porovnanie metód východiskového riešenia  ·  SZR · IM · VAM  +  MODI do optima",
                 bg=TMAVA, fg="#aeb9c8", font=pismo(11)).pack(side="left", pady=12)
        for m in reversed(METODY):
            tk.Label(h, text=f"● {m} – {POPIS_METOD[m]}", bg=TMAVA, fg=FARBY[m],
                     font=pismo(10)).pack(side="right", padx=10)

    def _tab_simulacia(self):
        lavy = ttk.Frame(self.tab_sim, style="Pozadie.TFrame", width=330)
        lavy.pack(side="left", fill="y", padx=(0, 12), pady=10)
        pravy = ttk.Frame(self.tab_sim, style="Pozadie.TFrame")
        pravy.pack(side="left", fill="both", expand=True, pady=10)

        self.v = {
            "pocet": tk.StringVar(value="10 000"), "procesy": tk.StringVar(value=str(os.cpu_count() or 1)),
            "seed": tk.StringVar(value="20261025"),
            "m_od": tk.StringVar(value="3"), "m_do": tk.StringVar(value="20"),
            "n_od": tk.StringVar(value="3"), "n_do": tk.StringVar(value="20"),
            "cena_a": tk.StringVar(value="20"), "cena_b": tk.StringVar(value="100"),
            "podiel_a": tk.StringVar(value="50"),
            "vyrovnane": tk.StringVar(value="50"), "ponuka": tk.StringVar(value="25"),
            "ulozit": tk.BooleanVar(value=False), "nazov": tk.StringVar(value=""),
        }

        k = self._karta(lavy, "Koľko úloh vypočítať", fill="x", pady=(0, 8))
        e = ttk.Entry(k, textvariable=self.v["pocet"], font=pismo(16, True), width=14, justify="right")
        e.pack(fill="x")
        rychle = ttk.Frame(k, style="Karta.TFrame")
        rychle.pack(fill="x", pady=(6, 0))
        for text, hodnota in (("1 000", 1000), ("10 000", 10_000), ("100 000", 100_000), ("1 000 000", 1_000_000)):
            ttk.Button(rychle, text=text, style="Maly.TButton",
                       command=lambda h=hodnota: self.v["pocet"].set(cislo(h))).pack(side="left", padx=(0, 4))
        self.lbl_odhad = ttk.Label(k, text="", style="Sivy.TLabel")
        self.lbl_odhad.pack(anchor="w", pady=(6, 0))
        self.v["pocet"].trace_add("write", lambda *_: self._odhad())
        self.v["procesy"].trace_add("write", lambda *_: self._odhad())

        tl = ttk.Frame(lavy, style="Pozadie.TFrame")
        tl.pack(fill="x", pady=(0, 6))
        self.btn_start = ttk.Button(tl, text="▶  Spustiť", style="Akcent.TButton", command=self._spusti)
        self.btn_start.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.btn_stop = ttk.Button(tl, text="■  Zastaviť", style="Stop.TButton", command=self._zastav,
                                   state="disabled")
        self.btn_stop.pack(side="left", fill="x", expand=True)
        tl2 = ttk.Frame(lavy, style="Pozadie.TFrame")
        tl2.pack(fill="x", pady=(0, 10))
        self.btn_vyhodnot = ttk.Button(tl2, text="Vyhodnotiť", command=self._vyhodnot,
                                       state="disabled")
        self.btn_vyhodnot.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.btn_excel = ttk.Button(tl2, text="Export do Excelu", command=self._export_excel, state="disabled")
        self.btn_excel.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ttk.Button(tl2, text="Otvoriť výsledky", command=lambda: otvor(simulacia.PRIECINOK)
                   if simulacia.PRIECINOK.exists() else None).pack(side="left", fill="x", expand=True)

        k = self._karta(lavy, "Výpočet", fill="x", pady=(0, 8))
        self._riadok(k, "Procesy (jadrá)", ttk.Spinbox(k, from_=1, to=max(64, os.cpu_count() or 1),
                                                       textvariable=self.v["procesy"], width=6))
        seed_ram = ttk.Frame(k, style="Karta.TFrame")
        ttk.Entry(seed_ram, textvariable=self.v["seed"], width=11).pack(side="left")
        ttk.Button(seed_ram, text="náhodný", style="Maly.TButton",
                   command=lambda: self.v["seed"].set(str(random.randint(1, 99_999_999)))).pack(side="left", padx=4)
        self._riadok(k, "Seed", seed_ram)
        self.v["skupina"] = tk.StringVar(value="prednaska")
        vyber = ttk.Combobox(k, values=list(SKUPINY_NAZVY), state="readonly", width=31, font=pismo(10))
        vyber.set(next(iter(SKUPINY_NAZVY)))
        vyber.bind("<<ComboboxSelected>>", lambda _: self.v["skupina"].set(SKUPINY_NAZVY[vyber.get()]))
        nazvy_skupin = {v: k_ for k_, v in SKUPINY_NAZVY.items()}
        self.v["skupina"].trace_add("write", lambda *_: vyber.set(nazvy_skupin[self.v["skupina"].get()]))
        self._riadok(k, "Metódy", vyber)
        self.v["skupina"].trace_add("write", lambda *_: self._odhad())

        k = self._karta(lavy, "Náhodné úlohy", fill="x", pady=(0, 8))
        self._riadok(k, "Dodávatelia m", self._od_do(k, "m_od", "m_do"))
        self._riadok(k, "Odberatelia n", self._od_do(k, "n_od", "n_do"))
        ceny = ttk.Frame(k, style="Karta.TFrame")
        ttk.Label(ceny, text="1 –", style="Karta.TLabel").pack(side="left")
        ttk.Entry(ceny, textvariable=self.v["cena_a"], width=5).pack(side="left", padx=3)
        ttk.Label(ceny, text="alebo 1 –", style="Karta.TLabel").pack(side="left")
        ttk.Entry(ceny, textvariable=self.v["cena_b"], width=5).pack(side="left", padx=3)
        self._riadok(k, "Ceny c_ij", ceny)
        self._riadok(k, "Podiel prvého rozsahu %", ttk.Spinbox(k, from_=0, to=100, increment=5,
                                                               textvariable=self.v["podiel_a"], width=6))
        self._riadok(k, "Vyrovnané úlohy %", ttk.Spinbox(k, from_=0, to=100, increment=5,
                                                         textvariable=self.v["vyrovnane"], width=6))
        self._riadok(k, "Prebytok ponuky %", ttk.Spinbox(k, from_=0, to=100, increment=5,
                                                         textvariable=self.v["ponuka"], width=6))
        self.lbl_dopyt = ttk.Label(k, text="", style="Sivy.TLabel")
        self.lbl_dopyt.pack(anchor="w")
        for kluc in ("vyrovnane", "ponuka"):
            self.v[kluc].trace_add("write", lambda *_: self._dopyt())
        self._dopyt()

        k = self._karta(lavy, "Uloženie", fill="x", pady=(0, 8))
        ttk.Checkbutton(k, text="Uložiť výsledky do CSV (vysledky/)", variable=self.v["ulozit"],
                        style="Karta.TCheckbutton").pack(anchor="w")
        self._riadok(k, "Názov behu", ttk.Entry(k, textvariable=self.v["nazov"], width=16))
        ttk.Label(k, text="prázdny = vytvorí sa automaticky", style="Sivy.TLabel").pack(anchor="w")

        k = self._karta(pravy, None, fill="x", pady=(0, 10))
        hore = ttk.Frame(k, style="Karta.TFrame")
        hore.pack(fill="x")
        self.lbl_stav = ttk.Label(hore, text="Pripravené – nastav parametre a stlač Spustiť.", style="Nadpis.TLabel")
        self.lbl_stav.pack(side="left")
        self.lbl_pct = ttk.Label(hore, text="", style="Nadpis.TLabel")
        self.lbl_pct.pack(side="right")
        self.progres = ttk.Progressbar(k, mode="determinate", maximum=1000)
        self.progres.pack(fill="x", pady=8)
        dlazdice = ttk.Frame(k, style="Karta.TFrame")
        dlazdice.pack(fill="x")
        self.dlazdice = {}
        for kluc, nazov in (("hotovo", "vypočítané úlohy"), ("rychlost", "úloh za sekundu"),
                            ("uplynulo", "uplynulo"), ("zostava", "zostáva"), ("chyby", "chyby")):
            ram = ttk.Frame(dlazdice, style="Karta.TFrame")
            ram.pack(side="left", expand=True, fill="x")
            lbl = ttk.Label(ram, text="–", style="Velke.TLabel")
            lbl.pack(anchor="w")
            ttk.Label(ram, text=nazov, style="Sivy.TLabel").pack(anchor="w")
            self.dlazdice[kluc] = lbl

        k = self._karta(pravy, "Priebežné výsledky metód", fill="x", pady=(0, 10))
        stlpce = ("metoda", "optimum", "odchylka", "kroky", "najlepsia", "cas")
        nazvy = ("metóda", "trafila optimum", "priemerná odchýlka od optima", "kroky MODI (priemer)",
                 "najlepšia v úlohe", "čas na úlohu")
        self.tabulka = ttk.Treeview(k, columns=stlpce, show="headings", height=3, selectmode="none")
        for s, n, sirka in zip(stlpce, nazvy, (190, 120, 210, 160, 130, 120)):
            self.tabulka.heading(s, text=n, anchor="w" if s == "metoda" else "e")
            self.tabulka.column(s, width=sirka, anchor="w" if s == "metoda" else "e")
        self._tabulka_riadky(METODY)
        self.tabulka.pack(fill="x")

        k = self._karta(pravy, None, fill="both", expand=True)
        self.fig = Figure(figsize=(10, 5.4), dpi=100, facecolor=KARTA)
        self.ax = [self.fig.add_subplot(2, 2, i + 1) for i in range(4)]
        self.fig.subplots_adjust(left=0.07, right=0.985, top=0.93, bottom=0.11, hspace=0.68, wspace=0.18)
        self.canvas = FigureCanvasTkAgg(self.fig, master=k)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self._kresli()
        self._odhad()

    def _riadok(self, rodic, text: str, widget):
        ram = ttk.Frame(rodic, style="Karta.TFrame")
        ram.pack(fill="x", pady=1)
        ttk.Label(ram, text=text, style="Karta.TLabel").pack(side="left")
        widget.pack(in_=ram, side="right")
        widget.lift(ram)

    def _od_do(self, rodic, k_od: str, k_do: str):
        ram = ttk.Frame(rodic, style="Karta.TFrame")
        ttk.Spinbox(ram, from_=2, to=60, textvariable=self.v[k_od], width=4).pack(side="left")
        ttk.Label(ram, text=" až ", style="Karta.TLabel").pack(side="left")
        ttk.Spinbox(ram, from_=2, to=60, textvariable=self.v[k_do], width=4).pack(side="left")
        return ram

    def _dopyt(self):
        try:
            zvysok = 100 - int(self.v["vyrovnane"].get()) - int(self.v["ponuka"].get())
            self.lbl_dopyt.config(text=f"Prebytok dopytu: {zvysok} % (zvyšok do 100 %)",
                                  foreground=SIVA if zvysok >= 0 else CERVENA)
        except ValueError:
            self.lbl_dopyt.config(text="")

    def _tabulka_riadky(self, mena):
        self.tabulka.delete(*self.tabulka.get_children())
        self.tabulka.configure(height=len(mena))
        for m in mena:
            self.tabulka.insert("", "end", iid=m, values=(f"{m} – {POPIS_METOD[m]}", "–", "–", "–", "–", "–"),
                                tags=(m,))
            self.tabulka.tag_configure(m, foreground=FARBY[m])

    def _odhad(self):
        try:
            n = nacitaj_cele(self.v["pocet"].get(), "počet", 1)
            pr = max(1, nacitaj_cele(self.v["procesy"].get(), "procesy", 1))
        except ValueError:
            self.lbl_odhad.config(text="")
            return
        mena = metody.SKUPINY[self.v["skupina"].get()] if "skupina" in self.v else list(METODY)
        sekundy = n * sum(CAS_METODY.get(m, 0.005) for m in mena) / min(pr, os.cpu_count() or pr)
        mb = n * len(mena) * 80 / 1e6
        self.lbl_odhad.config(text=f"odhad: ~{cas_text(sekundy)}  ·  CSV by malo ~{cislo(mb, 0 if mb >= 10 else 1)} MB")

    def _nastavenia(self):
        v = self.v
        pocet = nacitaj_cele(v["pocet"].get(), "Počet úloh", 1)
        procesy = nacitaj_cele(v["procesy"].get(), "Procesy", 1, 256)
        seed = nacitaj_cele(v["seed"].get(), "Seed", 0)
        m_od, m_do = (nacitaj_cele(v[k].get(), "Dodávatelia m", 2, 60) for k in ("m_od", "m_do"))
        n_od, n_do = (nacitaj_cele(v[k].get(), "Odberatelia n", 2, 60) for k in ("n_od", "n_do"))
        if m_od > m_do or n_od > n_do:
            raise ValueError("Veľkosť: „od“ musí byť menšie alebo rovné „do“.")
        ca = nacitaj_cele(v["cena_a"].get(), "Ceny – prvý rozsah", 1, 1_000_000)
        cb = nacitaj_cele(v["cena_b"].get(), "Ceny – druhý rozsah", 1, 1_000_000)
        pa = nacitaj_cele(v["podiel_a"].get(), "Podiel prvého rozsahu", 0, 100) / 100
        pv = nacitaj_cele(v["vyrovnane"].get(), "Vyrovnané úlohy", 0, 100) / 100
        pp = nacitaj_cele(v["ponuka"].get(), "Prebytok ponuky", 0, 100) / 100
        if pv + pp > 1 + 1e-9:
            raise ValueError("Vyrovnané + prebytok ponuky nesmie byť viac ako 100 %.")
        ceny = {f"1-{ca}": pa, f"1-{cb}": 1 - pa} if ca != cb else {f"1-{ca}": 1.0}
        p = dict(generator.PARAMETRE, m_rozsah=[m_od, m_do], n_rozsah=[n_od, n_do], ceny=ceny,
                 typ={"vyrovnana": pv, "prebytok_ponuky": pp, "prebytok_dopytu": round(1 - pv - pp, 10)})
        return pocet, procesy, seed, p, metody.SKUPINY[v["skupina"].get()]

    def _spusti(self):
        try:
            pocet, procesy, seed, p, mena = self._nastavenia()
        except ValueError as e:
            messagebox.showwarning("Skontroluj nastavenia", str(e), parent=self)
            return

        self.nazov = None
        if self.v["ulozit"].get():
            nazov = self.v["nazov"].get().strip() or f"gui_{time.strftime('%Y%m%d_%H%M%S')}"
            nazov = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in nazov)
            cesta = simulacia.PRIECINOK / f"beh_{nazov}.csv"
            if cesta.exists() and not messagebox.askyesno(
                    "Beh už existuje", f"Súbor {cesta.name} už existuje. Prepísať ho?", parent=self):
                return
            simulacia.PRIECINOK.mkdir(exist_ok=True)
            self.f_csv = open(cesta, "w", newline="", encoding="utf-8")
            self.w_csv = csv.writer(self.f_csv)
            self.w_csv.writerow(simulacia.STLPCE)
            self.nazov = nazov
            self.cesta_csv = cesta

        self.parametre = {"pocet": pocet, "procesy": procesy, "seed": seed, "p": p, "metody": mena}
        self.stat = Statistiky(mena)
        self._tabulka_riadky(mena)
        self.pocet = pocet
        self.t0 = time.perf_counter()
        self.bezi = True
        self.stop.clear()
        blok = max(5, min(200, pocet // (procesy * 40) or 5))
        self.vlakno = threading.Thread(target=beh_na_pozadi, daemon=True,
                                       args=(pocet, procesy, seed, p, blok, self.fronta, self.stop, mena))
        self.vlakno.start()
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.btn_vyhodnot.config(state="disabled")
        self.btn_excel.config(state="disabled")
        self.lbl_stav.config(text=f"Počítam {cislo(pocet)} úloh metódami {', '.join(mena)} na {procesy} "
                                  "procesoch…", foreground=TEXT)
        self._aktualizuj()
        self._kresli()

    def _zastav(self):
        if self.bezi:
            self.stop.set()
            self.btn_stop.config(state="disabled")
            self.lbl_stav.config(text="Zastavujem – dokončujú sa rozbehnuté bloky…")

    def _koniec_behu(self, zastavene: bool):
        self.bezi = False
        trvanie = time.perf_counter() - self.t0
        self.stat.zapis_historiu()
        if self.f_csv:
            self.f_csv.close()
            self.f_csv = self.w_csv = None
            p = self.parametre
            info = {
                "nazov": self.nazov, "zdroj": "aplikacia.py", "seed": p["seed"],
                "pocet_uloh_zadany": p["pocet"], "pocet_uloh_vypocitany": self.stat.hotovo,
                "zastavene_pouzivatelom": zastavene, "procesy": p["procesy"], "metody": p["metody"],
                "parametre_generatora": p["p"],
                "generovanie": "np.random.default_rng([seed, id]); úloha je určená seedom a id",
                "poradie_riadkov": "podľa dokončenia blokov (nie podľa id)",
                "trvanie_behu_s": round(trvanie, 3), "pocet_chyb": self.stat.chyby,
                "python": sys.version.split()[0], "numpy": np.__version__,
                "pocitac": platform.platform(), "cpu_logicke": os.cpu_count(),
                "datum": time.strftime("%Y-%m-%d %H:%M:%S"), "csv": self.cesta_csv.name,
            }
            with open(self.cesta_csv.with_suffix(".json"), "w", encoding="utf-8") as f:
                json.dump(info, f, ensure_ascii=False, indent=2)
            self.posledny_beh = self.nazov
            self.btn_vyhodnot.config(state="normal" if p["metody"] == list(metody.METODY) else "disabled")
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.btn_excel.config(state="normal" if self.stat.hotovo else "disabled")
        self.trvanie = trvanie
        text = ("Zastavené" if zastavene else "Hotovo") + \
            f" – {cislo(self.stat.hotovo)} úloh za {cas_text(trvanie)}"
        if self.nazov:
            text += f"  ·  uložené: vysledky/beh_{self.nazov}.csv"
        self.lbl_stav.config(text=text, foreground="#178a5e" if not zastavene else TEXT)
        self._aktualizuj()
        self._kresli()
        if self.zatvarat:
            self.destroy()

    def _citaj_frontu(self):
        koniec = None
        t = time.perf_counter()
        try:
            while time.perf_counter() - t < 0.15:
                druh, obsah = self.fronta.get_nowait()
                if druh == "data":
                    riadky, chyby = obsah
                    self.stat.pridaj(riadky, chyby)
                    if self.w_csv:
                        self.w_csv.writerows(riadky)
                elif druh == "chyba":
                    messagebox.showerror("Chyba výpočtu", obsah, parent=self)
                elif druh == "koniec":
                    koniec = obsah
                    break
        except queue.Empty:
            pass
        if self.bezi:
            self._aktualizuj()
            if time.perf_counter() - self.posledne_kreslenie > 1.0:
                self.stat.zapis_historiu()
                self._kresli()
        if koniec is not None:
            self._koniec_behu(koniec)
        self.after(200, self._citaj_frontu)

    def _aktualizuj(self):
        s = self.stat
        uplynulo = time.perf_counter() - self.t0 if hasattr(self, "t0") else 0
        pocet = getattr(self, "pocet", 0)
        podiel = s.hotovo / pocet if pocet else 0
        self.progres["value"] = 1000 * podiel
        self.lbl_pct.config(text=f"{cislo(100 * podiel, 1)} %" if pocet else "")
        rychlost = s.hotovo / uplynulo if uplynulo > 0 else 0
        self.dlazdice["hotovo"].config(text=f"{cislo(s.hotovo)} / {cislo(pocet)}" if pocet else "–")
        self.dlazdice["rychlost"].config(text=cislo(rychlost) if s.hotovo else "–")
        self.dlazdice["uplynulo"].config(text=cas_text(uplynulo) if pocet else "–")
        zostava = (pocet - s.hotovo) / rychlost if rychlost > 0 and self.bezi else 0
        self.dlazdice["zostava"].config(text=cas_text(zostava) if self.bezi and rychlost > 0 else "–")
        self.dlazdice["chyby"].config(text=str(s.chyby) if pocet else "–",
                                      foreground=CERVENA if s.chyby else TEXT)
        for m in s.metody:
            k, opt, odch, kroky, cas = s.stat[m][:5]
            if k == 0:
                hodnoty = ("–",) * 5
            else:
                hodnoty = (f"{cislo(100 * opt / k, 2)} %", f"{cislo(odch / k, 1)} %", cislo(kroky / k, 1),
                           f"{cislo(100 * s.najlepsia[m] / s.hotovo, 1)} %", f"{cislo(cas / k / 1e6, 2)} ms")
            self.tabulka.item(m, values=(f"{m} – {POPIS_METOD[m]}", *hodnoty))

    def _kresli(self):
        self.posledne_kreslenie = time.perf_counter()
        s = self.stat
        a1, a2, a3, a4 = self.ax
        for a in self.ax:
            a.clear()
            a.set_facecolor(KARTA)
            for strana in ("top", "right"):
                a.spines[strana].set_visible(False)
            for strana in ("left", "bottom"):
                a.spines[strana].set_color("#c4ccd6")
            a.tick_params(colors="#55606e", labelsize=8)
            a.grid(True, color="#e8ecf1", linewidth=0.8)
            a.set_axisbelow(True)

        def log_os(a):
            a.set_yscale("log")
            a.yaxis.set_major_locator(matplotlib.ticker.FixedLocator([1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]))
            a.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda y, _: f"{y:g}"))
            a.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())

        def nadpis(a, text):
            a.set_title(text, fontsize=10, color=TEXT, loc="left", pad=6)

        nadpis(a1, "Priebežný priemer odchýlky od optima (%)")
        a1.set_xlabel("počet vypočítaných úloh", fontsize=8, color=SIVA)
        if s.historia:
            x = [h[0] for h in s.historia]
            for i, m in enumerate(s.metody):
                a1.plot(x, [h[1][i] for h in s.historia], color=FARBY[m], lw=2, label=m)
            log_os(a1)
            a1.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: cislo(x)))
            a1.legend(fontsize=7 if len(s.metody) > 3 else 8, frameon=False, loc="upper right",
                      ncol=4 if len(s.metody) > 3 else 3)

        vel = sorted(s.velkost)
        nadpis(a2, "Priemerná odchýlka podľa veľkosti úlohy (%)")
        a2.set_xlabel("veľkosť úlohy max(m, n)", fontsize=8, color=SIVA)
        nadpis(a3, "Priemerný počet krokov MODI podľa veľkosti úlohy")
        a3.set_xlabel("veľkosť úlohy max(m, n)", fontsize=8, color=SIVA)
        if vel:
            for m in s.metody:
                pocty = np.array([s.velkost[v][m][0] for v in vel], dtype=float)
                ok = pocty > 0
                x = np.array(vel)[ok]
                a2.plot(x, np.array([s.velkost[v][m][1] for v in vel])[ok] / pocty[ok],
                        color=FARBY[m], lw=2, marker="o", ms=3, label=m)
                a3.plot(x, np.array([s.velkost[v][m][2] for v in vel])[ok] / pocty[ok],
                        color=FARBY[m], lw=2, marker="o", ms=3, label=m)
            log_os(a2)
            for a in (a2, a3):
                a.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
            if len(s.metody) <= 3:
                a2.legend(fontsize=8, frameon=False, ncol=3)
                a3.legend(fontsize=8, frameon=False, ncol=3)

        nadpis(a4, "Rozdelenie odchýlky od optima (podiel úloh)")
        a4.set_xlabel("odchýlka od optima (%)  ·  posledný stĺpec = 500 % a viac", fontsize=8, color=SIVA)
        if s.hotovo:
            stredy = (HIST_HRANY[:-1] + HIST_HRANY[1:]) / 2
            for m in s.metody:
                h = s.hist[m] / max(1, s.hist[m].sum()) * 100
                a4.fill_between(stredy, h, step="mid", color=FARBY[m], alpha=0.18)
                a4.step(stredy, h, where="mid", color=FARBY[m], lw=1.6, label=m)
            a4.set_xlim(0, 500)
            a4.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda y, _: f"{y:.0f} %"))
            if len(s.metody) <= 3:
                a4.legend(fontsize=8, frameon=False, ncol=3)

        if not s.hotovo:
            for a in self.ax:
                a.text(0.5, 0.5, "čaká na výpočet", transform=a.transAxes, ha="center", va="center",
                       color="#a7b0bc", fontsize=10)
        self.canvas.draw_idle()

    def _export_excel(self):
        if not self.stat.hotovo:
            return
        simulacia.PRIECINOK.mkdir(exist_ok=True)
        navrh = (self.nazov or f"vysledky_{time.strftime('%Y%m%d_%H%M%S')}") + ".xlsx"
        cesta = filedialog.asksaveasfilename(parent=self, title="Uložiť výsledky do Excelu",
                                             initialdir=simulacia.PRIECINOK, initialfile=navrh,
                                             defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if not cesta:
            return
        p = self.parametre
        info = {"nazov": self.nazov, "seed": p["seed"], "procesy": p["procesy"], "pocet_zadany": p["pocet"],
                "parametre_generatora": p["p"], "trvanie_s": getattr(self, "trvanie", 0),
                "datum": time.strftime("%Y-%m-%d %H:%M")}
        self.btn_excel.config(state="disabled")
        self.lbl_stav.config(text="Vytváram Excel…")
        stat = self.stat

        def praca():
            try:
                import export_excel
                export_excel.exportuj(Path(cesta), stat, info)
                self.after(0, lambda: hotovo(None))
            except Exception as e:
                self.after(0, lambda: hotovo(f"{type(e).__name__}: {e}"))

        def hotovo(chyba):
            self.btn_excel.config(state="normal")
            if chyba:
                self.lbl_stav.config(text="Export do Excelu zlyhal.")
                messagebox.showerror("Export do Excelu zlyhal", chyba, parent=self)
                return
            self.lbl_stav.config(text=f"Excel uložený: {cesta}")
            try:
                otvor(cesta)
            except OSError:
                pass

        threading.Thread(target=praca, daemon=True).start()

    def _vyhodnot(self):
        if not self.posledny_beh:
            return
        self.lbl_stav.config(text=f"Vyhodnocujem beh {self.posledny_beh} (analyza.py)…")
        self.update_idletasks()
        vysledok = subprocess.run([sys.executable, str(KOREN / "analyza.py"), self.posledny_beh],
                                  cwd=KOREN, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if vysledok.returncode != 0:
            messagebox.showerror("Vyhodnotenie zlyhalo", vysledok.stderr[-2000:] or vysledok.stdout[-2000:],
                                 parent=self)
            return
        self.lbl_stav.config(text=f"Vyhodnotené: vysledky/suhrn_{self.posledny_beh}.md a grafy/{self.posledny_beh}/")
        priecinok = KOREN / "grafy" / self.posledny_beh
        if priecinok.exists():
            otvor(priecinok)

    def _textove_pole(self, rodic):
        ram = tk.Frame(rodic, bg=KARTA, highlightbackground=OKRAJ, highlightthickness=1)
        txt = tk.Text(ram, font=(MONO, 11), bg=KARTA, fg=TEXT, relief="flat", wrap="word", padx=16, pady=12)
        sb = ttk.Scrollbar(ram, command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        txt.pack(fill="both", expand=True)
        txt.tag_configure("nadpis", font=pismo(12, True), spacing1=10, spacing3=4)
        txt.tag_configure("sivy", foreground=SIVA)
        txt.tag_configure("opt", foreground="#178a5e", font=(MONO, 11, "bold"))
        txt.tag_configure("krok", foreground="#3d4a5c")
        txt.tag_configure("podnadpis", font=pismo(11, True), foreground="#1f4e79", spacing1=6)
        for m in metody.VSETKY_METODY:
            txt.tag_configure(m, foreground=FARBY[m], font=pismo(12, True), spacing1=10, spacing3=4)
        return ram, txt

    def _tab_ukazka(self):
        k = self._karta(self.tab_uk, None, fill="x", pady=10)
        self.uk = {"m": tk.StringVar(value="4"), "n": tk.StringVar(value="5"),
                   "id": tk.StringVar(value=str(random.randint(1, 99_999)))}
        ttk.Label(k, text="Vygeneruje jednu malú náhodnú úlohu a vyrieši ju metódami SZR, IM a VAM, "
                          "potom MODI do optima.", style="Karta.TLabel").pack(anchor="w", pady=(0, 8))
        riadok = ttk.Frame(k, style="Karta.TFrame")
        riadok.pack(anchor="w")
        for text, kluc in (("Dodávatelia m", "m"), ("Odberatelia n", "n")):
            ttk.Label(riadok, text=text, style="Karta.TLabel").pack(side="left", padx=(0, 4))
            ttk.Spinbox(riadok, from_=2, to=10, textvariable=self.uk[kluc], width=4).pack(side="left", padx=(0, 16))
        ttk.Label(riadok, text="Číslo úlohy", style="Karta.TLabel").pack(side="left", padx=(0, 4))
        ttk.Entry(riadok, textvariable=self.uk["id"], width=10).pack(side="left", padx=(0, 16))
        ttk.Button(riadok, text="Vyriešiť", style="Akcent.TButton", command=self._ukazka).pack(side="left", padx=4)
        ttk.Button(riadok, text="Nová náhodná úloha", style="Akcent.TButton",
                   command=lambda: (self.uk["id"].set(str(random.randint(1, 99_999))), self._ukazka())
                   ).pack(side="left", padx=4)

        ram, self.txt = self._textove_pole(self.tab_uk)
        ram.pack(fill="both", expand=True, pady=(0, 10))
        self._ukazka()

    def _ukazka(self):
        try:
            m_ = nacitaj_cele(self.uk["m"].get(), "Dodávatelia m", 2, 10)
            n_ = nacitaj_cele(self.uk["n"].get(), "Odberatelia n", 2, 10)
            id_ = nacitaj_cele(self.uk["id"].get(), "Číslo úlohy", 0)
        except ValueError as e:
            messagebox.showwarning("Skontroluj zadanie", str(e), parent=self)
            return
        p = dict(generator.PARAMETRE, m_rozsah=[m_, m_], n_rozsah=[n_, n_])
        nu = generator.generuj(20261025, id_, p)
        self._vypis_ulohu(self.txt, nu.C, nu.a, nu.b, f"Úloha č. {id_}")

    def _vypis_ulohu(self, t, C, a, b, nazov: str, kroky: bool = False, vyber=None):
        C = np.asarray(C, dtype=np.int64)
        a = np.asarray(a, dtype=np.int64)
        b = np.asarray(b, dtype=np.int64)
        m_, n_ = C.shape
        if a.sum() == b.sum():
            typ = "vyrovnaná"
        elif a.sum() > b.sum():
            typ = f"prebytok ponuky ({cislo(a.sum())} > {cislo(b.sum())})"
        else:
            typ = f"prebytok dopytu ({cislo(a.sum())} < {cislo(b.sum())})"
        u = metody.vyvaz(C, a, b)
        m, n = u.C.shape
        riadky = [f"D{i + 1}" for i in range(m)]
        stlpce = [f"O{j + 1}" for j in range(n)]
        if u.fiktivny == "dodavatel":
            riadky[-1] = "D*"
        elif u.fiktivny == "odberatel":
            stlpce[-1] = "O*"

        t.configure(state="normal")
        t.delete("1.0", "end")
        t.insert("end", f"{nazov}: {m_} dodávatelia × {n_} odberatelia, {typ}", "nadpis")
        if u.fiktivny:
            t.insert("end", f"   (pridaný fiktívny {'dodávateľ D*' if u.fiktivny == 'dodavatel' else 'odberateľ O*'}"
                            " s nulovými cenami)", "sivy")
        t.insert("end", "\n\nCeny c_ij, vpravo kapacity a_i, dole požiadavky b_j\n", "sivy")
        t.insert("end", "      " + "".join(f"{s:>6}" for s in stlpce) + "  │   a_i\n")
        for r, riadok, ai in zip(riadky, u.C, u.a):
            t.insert("end", f"  {r:<4}" + "".join(f"{int(c):>6}" for c in riadok) + f"  │ {int(ai):>5}\n")
        t.insert("end", "  " + "─" * (4 + 6 * n) + "──┘\n")
        t.insert("end", "  b_j " + "".join(f"{int(bj):>6}" for bj in u.b) + "\n")

        vysledky = []
        for nazov_m, f in metody.VSETKY_METODY.items():
            if (vyber and nazov_m not in vyber) or (not vyber and nazov_m not in metody.METODY):
                continue
            t0 = time.perf_counter_ns()
            start = f(u)
            t1 = time.perf_counter_ns()
            opt = metody.modi(u, start, zapisuj=kroky)
            t2 = time.perf_counter_ns()
            vysledky.append((nazov_m, start, opt, (t1 - t0) / 1e3, (t2 - t1) / 1e3))
        z_opt = min(o.z for _, _, o, _, _ in vysledky)

        def plan(X, tag=None):
            t.insert("end", "      " + "".join(f"{s:>6}" for s in stlpce) + "\n", "sivy")
            for r, riadok in zip(riadky, X):
                t.insert("end", f"  {r:<4}" + "".join(f"{(str(int(x)) if x else '·'):>6}" for x in riadok) + "\n",
                         tag)

        def pole(zhoda):
            return f"{riadky[int(zhoda.group(1)) - 1]}–{stlpce[int(zhoda.group(2)) - 1]}"

        for nazov_m, start, opt, _, _ in vysledky:
            odch = 100 * (start.z - z_opt) / z_opt if z_opt else 0
            t.insert("end", f"\n{nazov_m} – {POPIS_METOD[nazov_m]}:  z = {start.z}", nazov_m)
            t.insert("end", f"   (odchýlka {cislo(odch, 1)} %, MODI potrebovala {opt.kroky_modi} krokov)\n", "sivy")
            plan(start.X)
            if kroky and opt.postup:
                t.insert("end", "  Kroky MODI:\n", "sivy")
                for riadok in opt.postup:
                    t.insert("end", "    " + re.sub(r"\((\d+), (\d+)\)", pole, riadok) + "\n", "krok")

        t.insert("end", f"\nOptimálne riešenie (MODI):  z* = {z_opt}\n", "nadpis")
        plan(vysledky[-1][2].X, "opt")

        t.insert("end", "\nPorovnanie\n", "nadpis")
        t.insert("end", f"  {'metóda':<8}{'z':>8}{'odchýlka':>11}{'kroky MODI':>13}{'čas metódy':>13}{'čas MODI':>12}\n",
                 "sivy")
        for nazov_m, start, opt, t_met, t_modi in vysledky:
            odch = 100 * (start.z - z_opt) / z_opt if z_opt else 0
            t.insert("end", f"  {nazov_m:<8}{start.z:>8}{cislo(odch, 1):>9} %{opt.kroky_modi:>13}"
                            f"{cislo(t_met):>10} µs{cislo(t_modi):>9} µs\n")
        t.configure(state="disabled")

    def _tab_vlastna(self):
        self.vl_m = tk.StringVar(value="3")
        self.vl_n = tk.StringVar(value="4")
        self.vl_postup = tk.BooleanVar(value=True)
        self.vl_metoda = tk.StringVar(value="VSETKY")
        self.vl_c: dict[tuple[int, int], tk.StringVar] = {}
        self.vl_a: dict[int, tk.StringVar] = {}
        self.vl_b: dict[int, tk.StringVar] = {}
        self.vl_polia: dict[str, tk.Entry] = {}

        lavy = ttk.Frame(self.tab_vl, style="Pozadie.TFrame")
        lavy.pack(side="left", fill="y", padx=(0, 12), pady=10)
        pravy = ttk.Frame(self.tab_vl, style="Pozadie.TFrame")
        pravy.pack(side="left", fill="both", expand=True, pady=10)

        k = self._karta(lavy, "Vlastná úloha", fill="x", pady=(0, 10))
        ttk.Label(k, text="Do tabuľky napíš ceny prepravy jednej jednotky. Vpravo je, koľko má každý "
                          "dodávateľ (a_i), dole koľko chce každý odberateľ (b_j). Ak sa ponuka nerovná dopytu, "
                          "program pridá fiktívneho dodávateľa alebo odberateľa s cenou 0.",
                  style="Sivy.TLabel", wraplength=560, justify="left").pack(anchor="w", pady=(0, 8))
        riadok = ttk.Frame(k, style="Karta.TFrame")
        riadok.pack(anchor="w", pady=(0, 6))
        for text, var in (("Dodávatelia m", self.vl_m), ("Odberatelia n", self.vl_n)):
            ttk.Label(riadok, text=text, style="Karta.TLabel").pack(side="left", padx=(0, 4))
            ttk.Spinbox(riadok, from_=1, to=10, textvariable=var, width=4,
                        command=self._vl_tabulka).pack(side="left", padx=(0, 16))
        ttk.Button(riadok, text="Zmeniť veľkosť", style="Maly.TButton", command=self._vl_tabulka).pack(side="left")
        riadok2 = ttk.Frame(k, style="Karta.TFrame")
        riadok2.pack(anchor="w")
        ttk.Button(riadok2, text="Príklad z prednášky", style="Maly.TButton",
                   command=self._vl_priklad).pack(side="left", padx=(0, 4))
        ttk.Button(riadok2, text="Vyplniť náhodne", style="Maly.TButton",
                   command=self._vl_nahodne).pack(side="left", padx=(0, 4))
        ttk.Button(riadok2, text="Vymazať", style="Maly.TButton", command=self._vl_vymaz).pack(side="left")

        self.vl_karta = self._karta(lavy, "Tabuľka", fill="x", pady=(0, 10))
        self.vl_mriezka = ttk.Frame(self.vl_karta, style="Karta.TFrame")
        self.vl_mriezka.pack(anchor="w")
        self.vl_sucty = ttk.Label(self.vl_karta, text="", style="Sivy.TLabel")
        self.vl_sucty.pack(anchor="w", pady=(8, 0))

        k = self._karta(lavy, "Ako počítať", fill="x", pady=(0, 10))
        moznosti = {"Všetky tri metódy z prednášky a ich porovnanie": "VSETKY",
                    "SZR – metóda severozápadného rohu": "SZR",
                    "IM – indexová metóda": "IM",
                    "VAM – Vogelova aproximačná metóda": "VAM",
                    "JVR – juhovýchodný roh (nová)": "JVR",
                    "SVR – severovýchodný roh (nová)": "SVR",
                    "JZR – juhozápadný roh (nová)": "JZR",
                    "MDD – dvojitá diferencia (nová)": "MDD",
                    "PVM – predvídavá metóda (nová)": "PVM",
                    "Len nové metódy (JVR, SVR, JZR, MDD, PVM) a ich porovnanie": "NOVE",
                    "Všetky metódy (aj nové) a ich porovnanie": "VSETKO"}
        nazvy = {v: k_ for k_, v in moznosti.items()}
        vyber = ttk.Combobox(k, values=list(moznosti), state="readonly", width=48, font=pismo(10))
        vyber.set(nazvy[self.vl_metoda.get()])
        vyber.bind("<<ComboboxSelected>>", lambda _: self.vl_metoda.set(moznosti[vyber.get()]))
        self.vl_metoda.trace_add("write", lambda *_: vyber.set(nazvy.get(self.vl_metoda.get(), vyber.get())))
        vyber.pack(anchor="w", fill="x")
        ttk.Checkbutton(k, text="Celý postup krok za krokom (obsadzovanie polí, potenciály, Δ, obvod)",
                        variable=self.vl_postup, style="Karta.TCheckbutton").pack(anchor="w", pady=(6, 0))

        dole = ttk.Frame(lavy, style="Pozadie.TFrame")
        dole.pack(fill="x")
        ttk.Button(dole, text="▶  Vyriešiť", style="Akcent.TButton", command=self._vl_vyries).pack(
            side="left", fill="x", expand=True, padx=(0, 6))
        ttk.Button(dole, text="Uložiť postup…", command=self._vl_uloz).pack(side="left", fill="y")

        ram, self.vl_txt = self._textove_pole(pravy)
        ram.pack(fill="both", expand=True)
        self.vl_txt.insert("end", "Vyplň tabuľku vľavo a stlač Vyriešiť (alebo Enter).\n\n"
                                  "Tip: tlačidlo „Príklad z prednášky“ vyplní úlohu z prednášky L5LZV 5-6 "
                                  "(optimum z* = 65).", "sivy")
        self.vl_txt.configure(state="disabled")
        self._vl_priklad()

    def _vl_premenna(self, slovnik, kluc):
        if kluc not in slovnik:
            slovnik[kluc] = tk.StringVar(value="")
            slovnik[kluc].trace_add("write", lambda *_: self._vl_sucty())
        return slovnik[kluc]

    def _vl_tabulka(self):
        try:
            m = nacitaj_cele(self.vl_m.get(), "Dodávatelia m", 1, 10)
            n = nacitaj_cele(self.vl_n.get(), "Odberatelia n", 1, 10)
        except ValueError as e:
            messagebox.showwarning("Skontroluj veľkosť", str(e), parent=self)
            return
        for w in self.vl_mriezka.winfo_children():
            w.destroy()
        self.vl_polia = {}

        def bunka(var, riadok, stlpec, farba=KARTA):
            e = tk.Entry(self.vl_mriezka, textvariable=var, width=6, justify="center", font=pismo(11),
                         relief="solid", bd=1, highlightthickness=0, bg=farba)
            e.zakladna_farba = farba
            e.grid(row=riadok, column=stlpec, padx=2, pady=2, ipady=3)
            e.bind("<Return>", lambda _: self._vl_vyries())
            self.vl_polia[str(var)] = e

        def popis(text, riadok, stlpec):
            tk.Label(self.vl_mriezka, text=text, bg=KARTA, fg=SIVA, font=pismo(10, True)).grid(
                row=riadok, column=stlpec, padx=4, pady=2)

        for j in range(n):
            popis(f"O{j + 1}", 0, j + 1)
        popis("a_i", 0, n + 2)
        for i in range(m):
            popis(f"D{i + 1}", i + 1, 0)
            for j in range(n):
                bunka(self._vl_premenna(self.vl_c, (i, j)), i + 1, j + 1)
            tk.Frame(self.vl_mriezka, bg=OKRAJ, width=2).grid(row=i + 1, column=n + 1, sticky="ns", padx=4)
            bunka(self._vl_premenna(self.vl_a, i), i + 1, n + 2, "#eef6f1")
        tk.Frame(self.vl_mriezka, bg=OKRAJ, height=2).grid(row=m + 1, column=1, columnspan=n, sticky="ew", pady=4)
        popis("b_j", m + 2, 0)
        for j in range(n):
            bunka(self._vl_premenna(self.vl_b, j), m + 2, j + 1, "#eef3fb")
        self._vl_sucty()

    def _vl_rozmer(self):
        return int(self.vl_m.get()), int(self.vl_n.get())

    def _vl_sucty(self):
        if not hasattr(self, "vl_sucty"):
            return
        try:
            m, n = self._vl_rozmer()
            sa = sum(int(self.vl_a[i].get()) for i in range(m))
            sb = sum(int(self.vl_b[j].get()) for j in range(n))
        except (ValueError, KeyError):
            self.vl_sucty.config(text="Ponuka spolu: –   ·   Dopyt spolu: –")
            return
        if sa == sb:
            stav = "vyrovnaná úloha"
        elif sa > sb:
            stav = f"prebytok ponuky {cislo(sa - sb)} → pridá sa fiktívny odberateľ"
        else:
            stav = f"prebytok dopytu {cislo(sb - sa)} → pridá sa fiktívny dodávateľ"
        self.vl_sucty.config(text=f"Ponuka spolu: {cislo(sa)}   ·   Dopyt spolu: {cislo(sb)}   ·   {stav}")

    def _vl_nastav(self, C, a, b):
        self.vl_m.set(str(len(a)))
        self.vl_n.set(str(len(b)))
        for i, riadok in enumerate(C):
            for j, c in enumerate(riadok):
                self._vl_premenna(self.vl_c, (i, j)).set(str(c))
        for i, x in enumerate(a):
            self._vl_premenna(self.vl_a, i).set(str(x))
        for j, x in enumerate(b):
            self._vl_premenna(self.vl_b, j).set(str(x))
        self._vl_tabulka()

    def _vl_priklad(self):
        self._vl_nastav([[3, 5, 4, 1], [2, 1, 3, 2], [4, 5, 1, 3]], [10, 20, 10], [10, 5, 5, 20])

    def _vl_nahodne(self):
        try:
            m, n = self._vl_rozmer()
        except ValueError:
            m, n = 3, 4
        rng = np.random.default_rng()
        C = rng.integers(1, 21, size=(m, n))
        a = rng.integers(10, 61, size=m)
        b = generator._rozdel(rng, int(a.sum()), n, 10, 60)
        self._vl_nastav(C.tolist(), a.tolist(), b.tolist())

    def _vl_vymaz(self):
        for var in [*self.vl_c.values(), *self.vl_a.values(), *self.vl_b.values()]:
            var.set("")

    def _vl_vyries(self):
        try:
            m, n = self._vl_rozmer()
        except ValueError:
            messagebox.showwarning("Skontroluj veľkosť", "Počet dodávateľov a odberateľov musí byť celé číslo.",
                                   parent=self)
            return
        chyby = []
        for e in self.vl_polia.values():
            e.config(bg=e.zakladna_farba)

        def hodnota(var, nazov, minimum):
            text = var.get().replace(" ", "")
            if text.lstrip("-").isdigit() and minimum <= int(text) <= 1_000_000_000:
                return int(text)
            chyby.append(nazov)
            if str(var) in self.vl_polia:
                self.vl_polia[str(var)].config(bg="#fde2e2")
            return 0

        C = [[hodnota(self.vl_c[(i, j)], f"c{i + 1}{j + 1}", 0) for j in range(n)] for i in range(m)]
        a = [hodnota(self.vl_a[i], f"a{i + 1}", 1) for i in range(m)]
        b = [hodnota(self.vl_b[j], f"b{j + 1}", 1) for j in range(n)]
        if chyby:
            messagebox.showwarning(
                "Skontroluj tabuľku",
                "Tieto polia sú prázdne alebo nesprávne (sú označené červenou):\n" + ", ".join(chyby[:20])
                + ("…" if len(chyby) > 20 else "")
                + "\n\nCeny musia byť celé čísla 0 alebo viac, kapacity a požiadavky celé čísla 1 alebo viac.",
                parent=self)
            return
        metoda = self.vl_metoda.get()
        if not self.vl_postup.get():
            vyber = {"VSETKY": None, "VSETKO": list(metody.VSETKY_METODY),
                     "NOVE": list(metody.NOVE_METODY)}.get(metoda, [metoda])
            self._vypis_ulohu(self.vl_txt, C, a, b, "Vlastná úloha", vyber=vyber)
            return
        casti, vysledky = postup.cely_postup(C, a, b, metoda)
        t = self.vl_txt
        t.configure(state="normal")
        t.delete("1.0", "end")
        for text, tag in casti:
            t.insert("end", text, tag)
        if len(vysledky) > 1:
            z_opt = min(o.z for _, o in vysledky.values())
            t.insert("end", "\nPorovnanie metód\n", "nadpis")
            t.insert("end", f"  {'metóda':<8}{'z':>8}{'odchýlka':>11}{'kroky MODI':>13}\n", "sivy")
            for nazov_m, (start, opt) in vysledky.items():
                odch = 100 * (start.z - z_opt) / z_opt if z_opt else 0
                t.insert("end", f"  {nazov_m:<8}{start.z:>8}{cislo(odch, 1):>9} %{opt.kroky_modi:>13}\n", nazov_m)
            t.insert("end", f"\nOptimum z* = {z_opt}\n", "opt")
        t.configure(state="disabled")
        t.see("1.0")

    def _vl_uloz(self):
        obsah = self.vl_txt.get("1.0", "end").strip()
        if not obsah:
            return
        cesta = filedialog.asksaveasfilename(parent=self, title="Uložiť postup", initialdir=simulacia.PRIECINOK,
                                             initialfile="postup_vlastna_uloha.txt", defaultextension=".txt",
                                             filetypes=[("Text", "*.txt")])
        if cesta:
            Path(cesta).write_text(obsah + "\n", encoding="utf-8")
            otvor(cesta)

    def _zatvor(self):
        if self.bezi:
            if not messagebox.askyesno("Výpočet beží", "Výpočet ešte beží. Zastaviť ho a zavrieť okno?", parent=self):
                return
            self.zatvarat = True
            self._zastav()
        else:
            self.destroy()


def main():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    os.chdir(KOREN)
    app = Aplikacia()
    app.mainloop()


if __name__ == "__main__":
    main()
