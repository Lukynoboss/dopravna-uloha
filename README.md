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
  Výpočet beží na všetkých jadrách procesora a dá sa kedykoľvek zastaviť. V poli **Metódy** si vyberieš, čím
  sa počíta: metódy z prednášky (SZR, IM, VAM), len nové vymyslené metódy (JVR, SVR, JZR, MDD, PVM) alebo
  všetkých osem naraz. Export do Excelu funguje pre každý výber; podrobné Vyhodnotenie je len pre metódy z prednášky.
- **Export do Excelu** – súbor s výsledkami, grafmi a **vysvetlivkami v ľudskej reči**
  (hlavné zistenia vetami, čo znamená každý stĺpec, slovník pojmov, text „ako to vysvetliť vyučujúcemu“).
- **Vlastná úloha** – do tabuľky zadáš vlastné ceny, kapacity a požiadavky (až 10 × 10), alebo vyplníš
  príklad z prednášky. Vyberieš jednu metódu, metódy z prednášky, len nové metódy alebo všetky a program vypíše **celý postup
  krok za krokom**: ktoré pole a prečo obsadí (pri VAM aj diferencie), čo škrtá, potom potenciály u_i, v_j,
  hodnoty Δ, Dantzigov uzavretý obvod, presun t a nové riešenie až po optimum. Postup sa dá uložiť do .txt.
  Nevyrovnanú úlohu sám doplní fiktívnym dodávateľom alebo odberateľom.
- **Ukážka náhodnej úlohy** – malá náhodná úloha a riešenia všetkých troch metód + optimum, porovnateľné
  s ručným výpočtom.
- **Vyhodnotenie** uloženého behu – podrobné štatistiky (mediány, intervaly spoľahlivosti, Wilcoxonov test) a grafy.

## Nové (vymyslené) metódy: ďalšie tri rohy

Okrem severozápadného rohu z prednášky sú v programe aj tri vymyslené „rohové“ metódy. Všetky plnia
tabuľku vždy maximálnym množstvom min(a_i, b_j), bez ohľadu na ceny, a pri súčasnom vyčerpaní kapacity aj
požiadavky škrtajú riadok. Dajú sa vyskúšať vo Vlastnej úlohe aj s celým postupom.

| skratka | začína v rohu | poradie dodávateľov | poradie odberateľov |
|---|---|---|---|
| SZR (prednáška) | ľavý horný | D1, D2, … | O1, O2, … |
| **JVR** | pravý dolný | od posledného | od posledného |
| **SVR** | pravý horný | D1, D2, … | od posledného |
| **JZR** | ľavý dolný | od posledného | O1, O2, … |

**Porovnanie na 20 000 náhodných úlohách** (rovnaké úlohy ako hlavný beh, seed 20261025):

| metóda | trafila optimum | priemerná odchýlka | kroky MODI |
|---|---|---|---|
| SZR | 0,03 % | 216,8 % | 26,4 |
| JVR | 0,03 % | 216,8 % | 26,4 |
| SVR | 0,02 % | 216,1 % | 26,5 |
| JZR | 0,02 % | 216,1 % | 26,5 |
| IM | 0,92 % | 36,8 % | 10,1 |
| VAM | 5,91 % | 15,2 % | 6,3 |

**Zistenia:**

1. **JVR dá vždy presne ten istý plán ako SZR a JZR vždy ten istý ako SVR** (100 % úloh). Predstav si všetok
   tovar ako úsečku dĺžky T. Dodávatelia si ju rozdelia na úseky v nejakom poradí, odberatelia tiež. Rohová
   metóda pošle z Di do Oj presne toľko, koľko sa ich úseky prekrývajú. JVR číta tú istú úsečku ako SZR, len
   od druhého konca – a prekrytie úsekov nezávisí od smeru. Rovnako JZR je SVR čítaná odzadu. Rozdiel môže
   byť len v tom, ktoré pole s nulou sa pri degenerácii doplní do bázy; to zmení počet krokov MODI, nie optimum.
2. **SVR (a JZR) dáva iný plán ako SZR v každej úlohe** – obracia poradie len jednej strany, takže úseky sa
   prekrývajú inak. Lepšia ako SZR je však len v 50,1 % úloh, teda je to hod mincou: rohové metódy
   nehľadia na ceny, a keď sú ceny náhodné, je jedno, z ktorého rohu začneme.
3. Ani lepší z dvoch rohov (min SZR, SVR) nepomôže: odchýlka 191,6 %. Rozhodujúce je prihliadať na ceny –
   preto sú IM a VAM mnohonásobne lepšie.

## Nové (vymyslené) metódy s ohľadom na ceny: MDD a PVM

Cieľom bolo vymyslieť metódu, ktorá sa kvalitou priblíži k VAM. Vyskúšalo sa viac nápadov (napr. „ľútostná“
matica, váženie diferencie množstvom, čistá ľútosť) a vybrali sa dva najlepšie.

**MDD – metóda dvojitej diferencie.** Ako pri VAM sa spočítajú diferencie všetkých riadkov a stĺpcov
(rozdiel dvoch najnižších cien). Každé pole dostane skóre = diferencia jeho riadku, ak je v riadku
najlacnejšie, + diferencia jeho stĺpca, ak je v stĺpci najlacnejšie. Obsadí sa pole s najväčším skóre
(pri zhode nižšia cena, potom vyšší riadok a ľavejší stĺpec). Rozdiel oproti VAM: pole, ktoré je
najlacnejšie v riadku aj v stĺpci zároveň, dostane obe diferencie – je „dvojnásobne naliehavé“.
Dá sa robiť ručne rovnako ako VAM.

**PVM – predvídavá metóda.** V každom kroku zoberie 3 polia s najväčším skóre MDD (kandidátov). Pre každého
skúsi: obsadí ho a zvyšok úlohy dopočíta metódou VAM. Naozaj obsadí toho kandidáta, pri ktorom vyšla celková
cena najnižšia – „pozrie sa dopredu“, čo jej voľba spôsobí. Ručne je prácna, počítač ju zvládne rýchlo.

**Porovnanie na 20 000 náhodných úlohách** (rovnaké úlohy ako hlavný beh, seed 20261025):

| metóda | trafila optimum | priemerná odchýlka | medián | kroky MODI |
|---|---|---|---|---|
| VAM | 5,91 % | 15,2 % | 11,1 % | 6,3 |
| **MDD** | 4,71 % | **15,4 %** | 11,3 % | 6,4 |
| **PVM** | **12,34 %** | **7,8 %** | **4,9 %** | **5,0** |
| IM | 0,92 % | 36,8 % | 30,6 % | 10,1 |

- **MDD je takmer rovnako dobrá ako VAM** (15,4 % oproti 15,2 %). V 32,6 % úloh dajú rovnaké z,
  v 29,3 % je lepšia MDD, v 38,1 % VAM.
- **PVM je približne dvakrát lepšia ako VAM:** odchýlka 7,8 %, optimum trafí hneď v 12,3 % úloh a MODI
  potrebuje najmenej krokov. Lepšia ako VAM je v 83,0 % úloh, horšia len v 0,3 %. Výhoda platí pri malých
  aj veľkých úlohách (pri max(m, n) 16–20: VAM 18,3 %, PVM 9,8 %). Cenou je viac výpočtov.

## Súbory

| súbor | čo obsahuje |
|---|---|
| `aplikacia.py` | grafické okno |
| `metody.py` | algoritmy SZR, IM, VAM, nové metódy JVR, SVR, JZR, MDD, PVM, MODI, vyrovnanie úlohy, degenerácia |
| `generator.py` | náhodné úlohy (úloha je určená seedom a svojím číslom → výsledky sa dajú zopakovať) |
| `simulacia.py` | hromadný výpočet na viacerých jadrách (aj z príkazového riadku) |
| `statistiky.py` | priebežné súčty výsledkov |
| `postup.py` | podrobný postup výpočtu krok za krokom (vlastná úloha) |
| `export_excel.py` | export do Excelu s vysvetlivkami |
| `analyza.py` | podrobné štatistiky a grafy z uloženého behu |
| `test_metody.py` | kontrola správnosti: príklady z prednášky + 2000 úloh porovnaných s riešičom scipy |
| `spusti.py` | jednoduché textové menu v konzole (`spusti.bat`) |
| `vysledky/` | výsledky hlavného behu (súhrn, Excel, parametre) |
| `grafy/` | grafy hlavného behu |

## Príkazový riadok

```bash
python simulacia.py --pocet 100000 --seed 20261025 --nazov hlavny100k   # hlavný beh (~1,5 min na 16 jadrách)
python simulacia.py --pocet 20000 --metody vsetky --nazov vsetky20k      # --metody prednaska | nove | vsetky
python analyza.py hlavny100k                                             # štatistiky + grafy
python export_excel.py hlavny100k                                        # Excel s vysvetlivkami
python test_metody.py                                                    # kontrola správnosti metód
```

(Na Windows namiesto `python` použi `.venv\Scripts\python.exe`, na macOS/Linuxe `.venv/bin/python`.)

Hlavný beh: 100 000 úloh, m aj n náhodne 3–20, ceny 1–20 alebo 1–100 (polovica úloh každý rozsah),
50 % vyrovnaných úloh, 25 % s prebytkom ponuky, 25 % s prebytkom dopytu, seed 20261025.
Súbor s jednotlivými riadkami (`beh_hlavny100k.csv`, 24 MB) sa nepribaľuje – rovnakým príkazom so
seedom 20261025 vznikne presne ten istý.
