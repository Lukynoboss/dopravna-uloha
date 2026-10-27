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

**Výsledok na 100 000 úlohách:** z metód z prednášky má VAM priemernú odchýlku od optima 15,3 % (IM 36,8 %,
SZR 216,9 %) a potrebuje najmenej krokov MODI (6,4; IM 10,1; SZR 26,6). Nové metódy: MDD 15,4 %, PVM 7,8 %
(najmenej krokov MODI – 5,0), JVR rovnako ako SZR. Hlavný beh, grafy aj súhrn obsahujú všetkých šesť metód.
Podrobne: [`vysledky/suhrn.md`](vysledky/suhrn.md), grafy v priečinku [`grafy/`](grafy).

## Spustenie

### Hotová aplikácia (bez inštalácie Pythonu)

Na stránke [**Releases**](https://github.com/Lukynoboss/dopravna-uloha/releases/latest) stiahni súbor pre svoj
systém, rozbaľ ho a spusti:

| systém | súbor | spustenie |
|---|---|---|
| **Windows** | `DopravnaUloha-Windows.zip` | `DopravnaUloha.exe` v rozbalenom priečinku |
| **Mac M1–M4** | `DopravnaUloha-Mac-Apple-M1-M4.zip` | `DopravnaUloha.app` (presuň ho do Aplikácií) |
| **Mac Intel** | `DopravnaUloha-Mac-Intel.zip` | `DopravnaUloha.app` |

Aplikácia nie je podpísaná, preto ju systém pri prvom spustení zablokuje:
- **Windows:** „Systém Windows ochránil počítač“ → **Ďalšie informácie → Spustiť aj tak**.
- **Mac:** pravým tlačidlom → **Otvoriť → Otvoriť**, prípadne **Nastavenia systému → Súkromie a bezpečnosť →
  Napriek tomu otvoriť**.

Výsledky (CSV, súhrny, grafy) ukladá do priečinka **Dokumenty/DopravnaUloha**.

### Zo zdrojového kódu

1. Stiahni program: na [GitHube](https://github.com/Lukynoboss/dopravna-uloha) zelené tlačidlo **Code → Download ZIP**
   a rozbaľ ho (napr. na Plochu).
2. Spusti ho dvojklikom:

| systém | súbor |
|---|---|
| **Windows** (Intel/AMD aj ARM) | **`aplikacia.bat`** |
| **macOS** (Intel aj Apple M1–M4) | **`aplikacia.command`** |

Nič iné netreba. Pri prvom spustení si program sám nainštaluje Python (ak chýba) aj knižnice. Trvá to
1–5 minút a treba internet. Ďalšie spustenia sú okamžité.

**Mac – prvé spustenie:** macOS súbor z internetu najprv zablokuje. Klikni naň **pravým tlačidlom → Otvoriť →
Otvoriť**. Ak ani to nepomôže (macOS 15 a novší), choď do **Nastavenia systému → Súkromie a bezpečnosť** a dole
klikni **Napriek tomu otvoriť**. Ak Python chýba, otvorí sa oficiálny inštalátor z python.org – prejdi ho
tlačidlami Pokračovať a program pokračuje sám.

Ak niečo nejde:
- **Windows:** ak sa Python nenainštaluje sám, stiahni ho z [python.org](https://www.python.org/downloads/),
  zaškrtni *Add python.exe to PATH* a spusti `aplikacia.bat` znova. Program rozbaľ do krátkej cesty (napr. na
  Plochu), vo veľmi dlhej ceste inštalácia knižníc zlyhá.
- **Mac s Homebrew Pythonom:** treba navyše `brew install python-tk`.
- Ak prenášaš priečinok na iný počítač, vymaž v ňom priečinok `.venv` – vytvorí sa znova.

## Čo aplikácia vie

- **Simulácia** – zadáš ľubovoľný počet úloh (aj milióny) a parametre: veľkosť tabuľky m × n, rozsahy cien,
  podiel vyrovnaných a nevyrovnaných úloh, seed. Počas výpočtu vidíš priebeh, tabuľku a 4 živé grafy.
  Výpočet beží na všetkých jadrách procesora a dá sa kedykoľvek zastaviť. V poli **Metódy** si vyberieš, čím
  sa počíta: metódy z prednášky (SZR, IM, VAM), len nové vymyslené metódy (JVR, MDD, PVM) alebo
  všetkých šesť naraz. Export do Excelu funguje pre každý výber; podrobné Vyhodnotenie funguje, keď sú medzi
  metódami SZR, IM a VAM (výber z prednášky alebo všetky).
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

## Nová (vymyslená) metóda: juhovýchodný roh – JVR

Zrkadlový obraz metódy severozápadného rohu: tabuľka sa plní od **pravého dolného** rohu doľava a hore,
vždy maximálnym množstvom min(a_i, b_j), bez ohľadu na ceny. Pri súčasnom vyčerpaní kapacity aj požiadavky
sa škrtá riadok (rovnako ako pri SZR). Dá sa vyskúšať vo Vlastnej úlohe aj s celým postupom.

**Porovnanie na 20 000 náhodných úlohách** (rovnaké úlohy ako hlavný beh, seed 20261025):

| metóda | trafila optimum | priemerná odchýlka | kroky MODI |
|---|---|---|---|
| SZR | 0,03 % | 216,8 % | 26,4 |
| JVR | 0,03 % | 216,8 % | 26,4 |

**Zistenie:** JVR dá **vždy presne ten istý prepravný plán ako SZR** (100 % úloh). Nie je to náhoda:

> Predstav si všetok tovar ako úsečku dĺžky T. Dodávatelia si ju rozdelia na úseky v poradí D1, D2, …,
> odberatelia tiež v poradí O1, O2, … SZR pošle z Di do Oj presne toľko, koľko sa úsek Di prekrýva s úsekom Oj.
> JVR robí to isté, len úsečku číta od druhého konca – a prekrytie úsekov nezávisí od smeru.

Rozdiel môže byť len pri degenerácii – v tom, ktoré pole s nulou sa doplní do bázy. To zmení cestu metódy
MODI (iný počet krokov v asi 12 % úloh), ale nie výsledné optimum.

Skúšali sa aj „krížové“ rohy – severovýchodný (SVR) a juhozápadný (JZR). Dávali navzájom vždy rovnaký plán
a proti SZR boli len hodom mincou (lepšie v 50,1 % úloh, priemerná odchýlka 216,1 %), preto sa z programu
odstránili.

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
| `metody.py` | algoritmy SZR, IM, VAM, nové metódy JVR, MDD, PVM, MODI, vyrovnanie úlohy, degenerácia |
| `generator.py` | náhodné úlohy (úloha je určená seedom a svojím číslom → výsledky sa dajú zopakovať) |
| `simulacia.py` | hromadný výpočet na viacerých jadrách (aj z príkazového riadku) |
| `statistiky.py` | priebežné súčty výsledkov |
| `postup.py` | podrobný postup výpočtu krok za krokom (vlastná úloha) |
| `export_excel.py` | export do Excelu s vysvetlivkami |
| `analyza.py` | podrobné štatistiky a grafy z uloženého behu |
| `test_metody.py` | kontrola správnosti: príklady z prednášky + 2000 úloh porovnaných s riešičom scipy |
| `spusti.py` | jednoduché textové menu v konzole (`spusti.bat`) |
| `cesty.py` | kam sa ukladajú výsledky (priečinok programu, v hotovej aplikácii Dokumenty/DopravnaUloha) |
| `.github/workflows/vydanie.yml` | GitHub zostaví hotovú aplikáciu pre Windows a Mac a dá ju do Releases |
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

(Na Windows namiesto `python` použi `.venv\Scripts\python.exe`, na macOS `.venv/bin/python`.)

Hlavný beh: 100 000 úloh, m aj n náhodne 3–20, ceny 1–20 alebo 1–100 (polovica úloh každý rozsah),
50 % vyrovnaných úloh, 25 % s prebytkom ponuky, 25 % s prebytkom dopytu, seed 20261025.
Súbor s jednotlivými riadkami (`beh_hlavny100k.csv`, 24 MB) sa nepribaľuje – rovnakým príkazom so
seedom 20261025 vznikne presne ten istý.
