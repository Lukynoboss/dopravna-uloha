# Súhrn výsledkov – beh `hlavny100k`

Vygenerované skriptom `analyza.py` z CSV; všetky čísla sú dopočítateľné spustením `.venv\Scripts\python.exe analyza.py hlavny100k`.

## Parametre behu

| parameter | hodnota |
|---|--:|
| súbor | `vysledky/beh_hlavny100k.csv` |
| seed | 20261025 |
| počet úloh N | 100 000 |
| m, n | [3, 20], [3, 20] (nezávisle) |
| ceny | 1-20: 0.5, 1-100: 0.5 |
| typ úlohy | vyrovnana: 0.5, prebytok_ponuky: 0.25, prebytok_dopytu: 0.25 |
| kapacity – základ, prebytok | [10, 100], [0.05, 0.3] |
| procesy / blok | 16 / 100 |
| trvanie behu | 79,7 s |
| chyby v behu | 0 |
| prostredie | Python 3.13.15, numpy 2.5.4, Windows-11-10.0.26300-SP0, 16 log. CPU |
| dátum behu | 2026-10-25 18:13:53 |

Odchýlka = (z − z*) / z* · 100 %. Časy sú merané `perf_counter_ns` vnútri procesu pri 16 paralelných procesoch – absolútne hodnoty sú orientačné, porovnanie metód je spravodlivé (rovnaké podmienky). Intervaly v hranatých zátvorkách = 95 % interval spoľahlivosti (priemer: normálna aproximácia; podiel: Wilson; medián a kvartily: neparametrický z poradových štatistík).

Kontrola dát: z* rovnaké pre všetky 3 metódy v úlohe: **áno**; z ≥ z* všade: **áno**; stĺpec `optimum` = (z = z*): **áno**.

## 1. Celkové porovnanie – správnosť

| metóda | trafila optimum (%) | priemer odchýlky (%) | medián (%) | 1. kvartil (%) | 3. kvartil (%) | max (%) |
|---|--:|--:|--:|--:|--:|--:|
| **SZR** | 0,03 [0,02; 0,05] | 216,86 [216,08; 217,65] | 197,31 [196,31; 198,26] | 119,92 [119,01; 120,80] | 291,69 [290,51; 293,03] | 1 199,9 |
| **IM** | 0,88 [0,83; 0,94] | 36,77 [36,60; 36,94] | 30,75 [30,57; 30,95] | 16,52 [16,37; 16,67] | 50,51 [50,21; 50,79] | 264,0 |
| **VAM** | 6,00 [5,85; 6,15] | 15,26 [15,17; 15,35] | 11,24 [11,14; 11,35] | 4,04 [3,98; 4,11] | 21,96 [21,80; 22,12] | 169,7 |

## 2. Celkové porovnanie – efektívnosť

| metóda | kroky MODI – priemer | kroky MODI – medián | čas metódy (µs) priemer / medián | čas MODI (µs) priemer / medián | celkový čas (µs) priemer / medián |
|---|--:|--:|--:|--:|--:|
| **SZR** | 26,61 [26,52; 26,71] | 24 | 399,3 [396,3; 402,3] / 336,2 | 5 807,6 [5 777,7; 5 837,5] / 4 402,4 | 6 206,9 [6 176,1; 6 237,7] / 4 783,6 |
| **IM** | 10,09 [10,05; 10,12] | 9 | 618,9 [615,2; 622,6] / 515,3 | 2 249,0 [2 236,5; 2 261,5] / 1 698,3 | 2 867,9 [2 853,9; 2 881,9] / 2 279,9 |
| **VAM** | 6,37 [6,34; 6,39] | 5 | 1 529,0 [1 522,3; 1 535,8] / 1 327,2 | 1 518,9 [1 509,1; 1 528,7] / 1 064,7 | 3 048,0 [3 034,0; 3 061,9] / 2 490,7 |

| metóda | najkratší celkový čas v úlohe (%) | najmenej krokov MODI v úlohe, vrátane remíz (%) | najrýchlejšia samotná metóda (%) |
|---|--:|--:|--:|
| SZR | 1,55 | 0,18 | 97,36 |
| IM | 62,78 | 18,32 | 2,63 |
| VAM | 35,67 | 89,72 | 0,01 |

## 3. Párové porovnanie na tej istej úlohe

| metóda | 1. miesto (%) | 2. miesto (%) | 3. miesto (%) | sama 1. (bez remízy) (%) |
|---|--:|--:|--:|--:|
| **SZR** | 0,09 [0,08; 0,12] | 0,55 [0,51; 0,60] | 99,36 [99,31; 99,40] | 0,07 |
| **IM** | 12,41 [12,21; 12,62] | 87,02 [86,81; 87,23] | 0,57 [0,52; 0,62] | 11,18 |
| **VAM** | 88,75 [88,55; 88,95] | 11,21 [11,02; 11,41] | 0,04 [0,03; 0,05] | 87,51 |

- Úlohy, kde platí **z(VAM) ≤ z(IM) ≤ z(SZR)**: **88,23 [88,03; 88,43] %** (ostro VAM < IM < SZR: 86,98 %).
- Všetky tri metódy rovnaké z: 0,01 %.

Párové testy (Wilcoxonov znamienkový poradový test na rozdieloch odchýlky v tej istej úlohe, obojstranný; nulové rozdiely vynechané):

| dvojica A vs B | A lepšia (%) | remíza (%) | B lepšia (%) | priemer rozdielu odchýlky A − B (p. b.) | medián rozdielu (p. b.) | p-hodnota |
|---|--:|--:|--:|--:|--:|--:|
| VAM vs IM | 87,57 | 1,24 | 11,20 | -21,51 [-21,66; -21,37] | -16,62 | < 1e-300 |
| VAM vs SZR | 99,88 | 0,03 | 0,09 | -201,60 [-202,34; -200,86] | -182,49 | < 1e-300 |
| IM vs SZR | 99,38 | 0,03 | 0,59 | -180,09 [-180,78; -179,40] | -162,86 | < 1e-300 |

VAM vs IM – efektívnosť (párovo):

| veličina | VAM menej (%) | rovnako (%) | IM menej (%) | priemer rozdielu VAM − IM | medián rozdielu | p-hodnota (Wilcoxon) |
|---|--:|--:|--:|--:|--:|--:|
| kroky MODI | 81,67 | 8,09 | 10,24 | -3,72 [-3,75; -3,70] | -3,00 | < 1e-300 |
| celkový čas (µs) | 36,25 | 0,01 | 63,74 | 180,06 [168,35; 191,78] | 180,60 | < 1e-300 |
| čas metódy (µs) | 1,17 | 0,00 | 98,83 | 910,15 [903,44; 916,86] | 781,40 | < 1e-300 |

## 4. Rozdelenie podľa vlastností úlohy

### 4.1 Podľa veľkosti m·n

| skupina | N | metóda | optimum (%) | priemer odchýlky (%) [95 % IS] | medián odch. (%) | kroky MODI | celk. čas (µs) | 1. miesto (%) |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| m·n 9–49 | 18121 | SZR | 0,18 | 96,57 [95,65; 97,50] | 83,01 | 8,4 | 1 383 | 0,5 |
|  |  | IM | 4,57 | 20,84 [20,53; 21,15] | 14,47 | 3,7 | 903 | 18,2 |
|  |  | VAM | 24,50 | 5,90 [5,77; 6,03] | 2,42 | 1,7 | 1 105 | 87,6 |
| m·n 50–99 | 27170 | SZR | 0,00 | 154,05 [153,13; 154,96] | 139,90 | 17,2 | 3 282 | 0,0 |
|  |  | IM | 0,20 | 29,20 [28,92; 29,48] | 23,00 | 6,9 | 1 774 | 12,2 |
|  |  | VAM | 5,36 | 10,20 [10,07; 10,33] | 6,70 | 3,8 | 1 993 | 88,1 |
| m·n 100–149 | 18251 | SZR | 0,00 | 220,88 [219,62; 222,14] | 205,77 | 26,2 | 5 580 | 0,0 |
|  |  | IM | 0,01 | 38,19 [37,82; 38,56] | 32,17 | 10,1 | 2 699 | 11,1 |
|  |  | VAM | 0,52 | 15,80 [15,60; 15,99] | 12,35 | 6,2 | 2 892 | 88,9 |
| m·n 150–249 | 23683 | SZR | 0,00 | 291,90 [290,63; 293,17] | 276,71 | 37,3 | 9 011 | 0,0 |
|  |  | IM | 0,00 | 46,77 [46,42; 47,12] | 40,97 | 13,8 | 3 990 | 10,8 |
|  |  | VAM | 0,05 | 21,48 [21,29; 21,67] | 18,11 | 9,2 | 4 154 | 89,2 |
| m·n 250–400 | 12775 | SZR | 0,00 | 376,22 [374,22; 378,22] | 358,30 | 53,2 | 14 969 | 0,0 |
|  |  | IM | 0,00 | 54,89 [54,39; 55,39] | 48,95 | 19,0 | 6 143 | 9,4 |
|  |  | VAM | 0,00 | 26,99 [26,70; 27,27] | 23,49 | 13,2 | 6 220 | 90,6 |

### 4.2 Podľa max(m, n)

| skupina | N | metóda | optimum (%) | priemer odchýlky (%) [95 % IS] | medián odch. (%) | kroky MODI | celk. čas (µs) | 1. miesto (%) |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| max 3–5 | 2781 | SZR | 1,11 | 70,41 [68,25; 72,57] | 56,90 | 4,2 | 640 | 2,5 |
|  |  | IM | 14,60 | 16,88 [16,08; 17,69] | 9,81 | 2,0 | 479 | 28,7 |
|  |  | VAM | 45,02 | 3,98 [3,69; 4,26] | 0,48 | 0,9 | 631 | 87,8 |
| max 6–8 | 8284 | SZR | 0,01 | 115,72 [114,10; 117,35] | 99,95 | 8,8 | 1 375 | 0,2 |
|  |  | IM | 3,05 | 24,43 [23,92; 24,93] | 18,03 | 3,9 | 896 | 18,5 |
|  |  | VAM | 18,10 | 8,27 [8,03; 8,51] | 4,31 | 2,1 | 1 112 | 85,8 |
| max 9–11 | 13912 | SZR | 0,00 | 157,02 [155,57; 158,48] | 141,65 | 14,9 | 2 637 | 0,0 |
|  |  | IM | 0,82 | 30,13 [29,71; 30,55] | 23,78 | 6,1 | 1 466 | 14,8 |
|  |  | VAM | 8,17 | 11,46 [11,25; 11,67] | 7,53 | 3,6 | 1 705 | 86,4 |
| max 12–14 | 19463 | SZR | 0,00 | 198,49 [197,06; 199,92] | 184,24 | 22,0 | 4 476 | 0,0 |
|  |  | IM | 0,30 | 35,24 [34,88; 35,61] | 29,26 | 8,6 | 2 246 | 12,4 |
|  |  | VAM | 4,41 | 14,32 [14,12; 14,51] | 10,43 | 5,3 | 2 485 | 88,1 |
| max 15–17 | 24879 | SZR | 0,00 | 238,50 [237,04; 239,97] | 227,31 | 30,0 | 6 925 | 0,0 |
|  |  | IM | 0,14 | 39,52 [39,19; 39,86] | 33,79 | 11,3 | 3 199 | 10,9 |
|  |  | VAM | 2,77 | 16,93 [16,74; 17,12] | 13,34 | 7,2 | 3 383 | 89,3 |
| max 18–20 | 30681 | SZR | 0,00 | 278,68 [277,16; 280,20] | 268,09 | 38,9 | 10 150 | 0,0 |
|  |  | IM | 0,06 | 43,65 [43,33; 43,97] | 37,92 | 14,2 | 4 378 | 9,4 |
|  |  | VAM | 1,84 | 19,13 [18,95; 19,31] | 15,71 | 9,2 | 4 485 | 90,7 |

### 4.3 Podľa cenového rozsahu

| skupina | N | metóda | optimum (%) | priemer odchýlky (%) [95 % IS] | medián odch. (%) | kroky MODI | celk. čas (µs) | 1. miesto (%) |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| ceny 1–20 | 50152 | SZR | 0,03 | 200,30 [199,34; 201,26] | 186,87 | 26,4 | 6 163 | 0,1 |
|  |  | IM | 0,97 | 34,03 [33,81; 34,24] | 28,95 | 9,9 | 2 828 | 12,3 |
|  |  | VAM | 6,37 | 14,38 [14,26; 14,50] | 10,70 | 6,2 | 3 011 | 89,0 |
| ceny 1–100 | 49848 | SZR | 0,03 | 233,52 [232,29; 234,75] | 210,16 | 26,8 | 6 251 | 0,1 |
|  |  | IM | 0,80 | 39,53 [39,26; 39,79] | 32,67 | 10,3 | 2 908 | 12,5 |
|  |  | VAM | 5,63 | 16,14 [16,00; 16,28] | 11,83 | 6,5 | 3 086 | 88,5 |

### 4.4 Podľa typu úlohy

| skupina | N | metóda | optimum (%) | priemer odchýlky (%) [95 % IS] | medián odch. (%) | kroky MODI | celk. čas (µs) | 1. miesto (%) |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| vyrovnaná | 49926 | SZR | 0,05 | 192,38 [191,43; 193,34] | 177,41 | 25,9 | 5 983 | 0,1 |
|  |  | IM | 1,55 | 23,59 [23,44; 23,73] | 20,83 | 8,7 | 2 546 | 16,0 |
|  |  | VAM | 8,42 | 10,86 [10,77; 10,96] | 8,03 | 5,5 | 2 827 | 86,0 |
| prebytok ponuky | 25041 | SZR | 0,02 | 242,34 [240,63; 244,05] | 221,75 | 27,4 | 6 402 | 0,1 |
|  |  | IM | 0,23 | 50,02 [49,65; 50,39] | 45,62 | 11,5 | 3 176 | 8,9 |
|  |  | VAM | 3,63 | 19,66 [19,45; 19,87] | 15,71 | 7,2 | 3 259 | 91,4 |
| prebytok dopytu | 25033 | SZR | 0,01 | 240,19 [238,48; 241,89] | 220,49 | 27,3 | 6 458 | 0,1 |
|  |  | IM | 0,20 | 49,81 [49,44; 50,18] | 45,24 | 11,5 | 3 202 | 8,7 |
|  |  | VAM | 3,56 | 19,62 [19,41; 19,83] | 15,70 | 7,2 | 3 278 | 91,6 |

### 4.5 Podľa degenerácie východiskového riešenia

Degenerácia sa týka konkrétnej metódy (počet bázických polí s nulovou prepravou), preto sa skupiny tvoria pre každú metódu zvlášť.

| metóda | degenerované riešenie (%) | priemerný počet nulových bázických polí | max |
|---|--:|--:|--:|
| **SZR** | 14,57 [14,35; 14,79] | 0,158 | 4 |
| **IM** | 16,54 [16,31; 16,77] | 0,181 | 5 |
| **VAM** | 16,45 [16,23; 16,69] | 0,181 | 4 |

| metóda | skupina | N | optimum (%) | priemer odchýlky (%) [95 % IS] | kroky MODI | celk. čas (µs) |
|---|--:|--:|--:|--:|--:|--:|
| SZR | nedegenerované | 85428 | 0,03 | 210,23 [209,39; 211,07] | 25,6 | 5 898 |
| SZR | degenerované | 14572 | 0,02 | 255,73 [253,64; 257,82] | 32,8 | 8 020 |
| IM | nedegenerované | 83460 | 0,96 | 35,96 [35,77; 36,14] | 9,7 | 2 724 |
| IM | degenerované | 16540 | 0,51 | 40,87 [40,44; 41,29] | 12,2 | 3 592 |
| VAM | nedegenerované | 83546 | 6,48 | 14,71 [14,61; 14,81] | 6,0 | 2 903 |
| VAM | degenerované | 16454 | 3,56 | 18,06 [17,82; 18,29] | 8,1 | 3 783 |

Pozn.: degenerácia súvisí s veľkosťou a typom úlohy (napr. ceny 1–20 → viac remíz), takže rozdiely v tejto tabuľke nie sú čistým účinkom degenerácie.

## 5. Grafy

- Priemerná odchýlka od optima vs. veľkosť m·n: [`../grafy/odchylka_vs_velkost.png`](../grafy/odchylka_vs_velkost.png)
- Priemerný počet krokov MODI vs. veľkosť m·n: [`../grafy/kroky_modi_vs_velkost.png`](../grafy/kroky_modi_vs_velkost.png)
- Podiel trafeného optima vs. veľkosť m·n: [`../grafy/optimum_vs_velkost.png`](../grafy/optimum_vs_velkost.png)
- Celkový čas (metóda + MODI) vs. veľkosť m·n: [`../grafy/cas_celkovy_vs_velkost.png`](../grafy/cas_celkovy_vs_velkost.png)
- Čas samotnej metódy vs. veľkosť m·n: [`../grafy/cas_metody_vs_velkost.png`](../grafy/cas_metody_vs_velkost.png)
- Krabicové grafy odchýlok: [`../grafy/boxplot_odchylok.png`](../grafy/boxplot_odchylok.png)
- Empirická distribučná funkcia odchýlky: [`../grafy/ecdf_odchylky.png`](../grafy/ecdf_odchylky.png)
- Poradie metód v tej istej úlohe: [`../grafy/poradie_metod.png`](../grafy/poradie_metod.png)
- Odchýlka podľa typu úlohy a cenového rozsahu: [`../grafy/odchylka_typ_cena.png`](../grafy/odchylka_typ_cena.png)

![Priemerná odchýlka od optima vs. veľkosť m·n](../grafy/odchylka_vs_velkost.png)

![Priemerný počet krokov MODI vs. veľkosť m·n](../grafy/kroky_modi_vs_velkost.png)

![Podiel trafeného optima vs. veľkosť m·n](../grafy/optimum_vs_velkost.png)

![Celkový čas (metóda + MODI) vs. veľkosť m·n](../grafy/cas_celkovy_vs_velkost.png)

![Čas samotnej metódy vs. veľkosť m·n](../grafy/cas_metody_vs_velkost.png)

![Krabicové grafy odchýlok](../grafy/boxplot_odchylok.png)

![Empirická distribučná funkcia odchýlky](../grafy/ecdf_odchylky.png)

![Poradie metód v tej istej úlohe](../grafy/poradie_metod.png)

![Odchýlka podľa typu úlohy a cenového rozsahu](../grafy/odchylka_typ_cena.png)

## 6. Záver

- **Najsprávnejšia metóda: VAM** – najmenšia priemerná odchýlka (15,26 %, medián 11,24 %) a najčastejšie trafí optimum (6,00 %). Poradie podľa priemernej odchýlky: VAM < IM < SZR. VAM je v tej istej úlohe na 1. mieste v 88,75 % úloh; z(VAM) ≤ z(IM) ≤ z(SZR) platí v 88,23 % úloh.
- **Najefektívnejšia podľa celkového času (metóda + MODI): IM** – priemer 2 868 µs, medián 2 280 µs (SZR / IM / VAM = 6 207 / 2 868 / 3 048 µs). Najkratší celkový čas má v 62,78 % úloh.
- **Najmenej krokov MODI: VAM** – priemerne 6,4 krokov (SZR / IM / VAM = 26,6 / 10,1 / 6,4); najmenej krokov má v 89,72 % úloh (s remízami).
- **IM vs. VAM v čase:** VAM ušetrí čas MODI (2 249 → 1 519 µs), ale samotná VAM trvá dlhšie (619 → 1 529 µs, počítanie diferencií v každom kroku). Párovo je VAM celkovo pomalšia priemerne o 180 µs (6,3 % času IM) a rýchlejšia len v 36,25 % úloh – rozdiel je malý a závisí od implementácie (Python); SZR je síce najrýchlejšia samotná metóda (399 µs), no kvôli MODI je celkovo najpomalšia.
- **Celkovo:** VAM je jednoznačne najsprávnejšia a potrebuje najmenej krokov MODI; v celkovom čase je IM mierne vpredu. SZR je vo všetkých podmienkach výrazne najhoršia.
- **Vplyv veľkosti:** pri malých úlohách (m·n ≤ 49) trafí VAM optimum v 24,50 % (IM 4,57 %), pri veľkých (m·n ≥ 250) už len v 0,00 %; počet krokov MODI rastie s veľkosťou pri všetkých metódach (VAM 1,7 → 13,2, SZR 8,4 → 53,2).
- Pri malých úlohách (m·n ≤ 49) je priemerný celkový čas SZR / IM / VAM = 1 383 / 903 / 1 105 µs, pri veľkých (m·n ≥ 250) 14 969 / 6 143 / 6 220 µs.
- **Cenový rozsah:** pri cenách 1–20 trafí VAM optimum v 6,37 %, pri 1–100 v 5,63 %; priemerná odchýlka VAM 14,38 % vs. 16,14 %.
- **Typ úlohy:** priemerná odchýlka VAM – vyrovnaná 10,86 %, prebytok ponuky 19,66 %, prebytok dopytu 19,62 %; poradie metód sa podľa typu nemení (pozri 4.4).
