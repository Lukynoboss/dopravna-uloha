# Dopravná úloha – porovnanie metód SZR, IM a VAM

Program porovnáva tri metódy hľadania **východiskového riešenia dopravnej úlohy**
(z prednášky L5LZV 5-6) na veľkom počte náhodných úloh:

| skratka | metóda |
|---|---|
| **SZR** | metóda severozápadného rohu |
| **IM** | indexová metóda |
| **VAM** | Vogelova aproximačná metóda |

Z každého východiskového riešenia sa metódou **MODI** dopočíta optimum. Sleduje sa, ktorá metóda je
**najsprávnejšia** (prvé riešenie najbližšie k optimu) a **najefektívnejšia** (najmenej krokov MODI, čas).

**Výsledok na 100 000 úlohách:** VAM má priemernú odchýlku od optima 15,3 % (IM 36,8 %, SZR 216,9 %)
a potrebuje najmenej krokov MODI (6,4; IM 10,1; SZR 26,6). Podrobne: [`vysledky/suhrn.md`](vysledky/suhrn.md).

## Spustenie

Potrebný je **Python 3.10 alebo novší** ([python.org/downloads](https://www.python.org/downloads/)).
Pri prvom spustení si spúšťač sám vytvorí prostredie `.venv` a nainštaluje knižnice
(numpy, matplotlib, openpyxl, scipy) – trvá to 1–3 minúty a treba internet. Ďalšie spustenia sú okamžité.

| systém | ako spustiť |
|---|---|
| **Windows** (Intel/AMD aj **ARM**, napr. Snapdragon) | dvojklik na **`aplikacia.bat`** |
| **macOS** (Intel aj **Apple Silicon M1–M4**) | dvojklik na **`aplikacia.command`** (prvýkrát pravým tlačidlom → Otvoriť) |
| **Linux** (x86 aj ARM, napr. Raspberry Pi) | `bash aplikacia.command` |

Poznámky:
- Na Windows ARM nainštaluj Python vo verzii **ARM64** a pri inštalácii zaškrtni *Add python.exe to PATH*.
- Na macOS použi Python z python.org (obsahuje tkinter). S Homebrew treba navyše `brew install python-tk`.
- Na Linuxe treba `sudo apt install python3-tk python3-venv`.
- Ak prenášaš priečinok na iný počítač, priečinok `.venv` vymaž – vytvorí sa znova pre daný procesor.
- Na Windows rozbaľ program do krátkej cesty (napr. na Plochu). Vo veľmi dlhej ceste inštalácia knižníc
  zlyhá na limite dĺžky cesty vo Windows.

Ručne (ktorýkoľvek systém): `python -m venv .venv`, potom `pip install -r requirements.txt` a `python aplikacia.py`.

## Čo aplikácia vie

- **Simulácia** – zadáš ľubovoľný počet úloh (aj milióny) a parametre: veľkosť tabuľky m × n, rozsahy cien,
  podiel vyrovnaných a nevyrovnaných úloh, seed. Počas výpočtu vidíš priebeh, tabuľku a 4 živé grafy.
  Výpočet beží na všetkých jadrách procesora a dá sa kedykoľvek zastaviť.
- **Export do Excelu** – súbor s výsledkami, grafmi a **vysvetlivkami v ľudskej reči**
  (hlavné zistenia vetami, čo znamená každý stĺpec, slovník pojmov, text „ako to vysvetliť vyučujúcemu“).
- **Ukážka jednej úlohy** – malá náhodná úloha a riešenia všetkých troch metód + optimum, krok za krokom
  porovnateľné s ručným výpočtom.
- **Vyhodnotenie** uloženého behu – podrobné štatistiky (mediány, intervaly spoľahlivosti, Wilcoxonov test) a grafy.

## Súbory

| súbor | čo obsahuje |
|---|---|
| `aplikacia.py` | grafické okno |
| `metody.py` | algoritmy SZR, IM, VAM, MODI, vyrovnanie úlohy, degenerácia |
| `generator.py` | náhodné úlohy (úloha je určená seedom a svojím číslom → výsledky sa dajú zopakovať) |
| `simulacia.py` | hromadný výpočet na viacerých jadrách (aj z príkazového riadku) |
| `statistiky.py` | priebežné súčty výsledkov |
| `export_excel.py` | export do Excelu s vysvetlivkami |
| `analyza.py` | podrobné štatistiky a grafy z uloženého behu |
| `test_metody.py` | kontrola správnosti: príklady z prednášky + 2000 úloh porovnaných s riešičom scipy |
| `spusti.py` | jednoduché textové menu v konzole (`spusti.bat`) |
| `vysledky/` | výsledky hlavného behu (súhrn, Excel, parametre) |
| `grafy/` | grafy hlavného behu |

## Príkazový riadok

```bash
python simulacia.py --pocet 100000 --seed 20261025 --nazov hlavny100k   # hlavný beh (~1,5 min na 16 jadrách)
python analyza.py hlavny100k                                             # štatistiky + grafy
python export_excel.py hlavny100k                                        # Excel s vysvetlivkami
python test_metody.py                                                    # kontrola správnosti metód
```

(Na Windows namiesto `python` použi `.venv\Scripts\python.exe`, na macOS/Linuxe `.venv/bin/python`.)

Hlavný beh: 100 000 úloh, m aj n náhodne 3–20, ceny 1–20 alebo 1–100 (polovica úloh každý rozsah),
50 % vyrovnaných úloh, 25 % s prebytkom ponuky, 25 % s prebytkom dopytu, seed 20261025.
Súbor s jednotlivými riadkami (`beh_hlavny100k.csv`, 24 MB) sa nepribaľuje – rovnakým príkazom so
seedom 20261025 vznikne presne ten istý.
