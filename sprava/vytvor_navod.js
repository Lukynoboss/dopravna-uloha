const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell, WidthType, ShadingType,
  AlignmentType, ImageRun, LevelFormat, BorderStyle, Footer, PageNumber, TableOfContents, PageBreak,
} = require("docx");

const KOREN = path.join(__dirname, "..");
const SIRKA = 9638;
const FONT = "Calibri";
const MAX_SIRKA_OBR = 470;

const beh = (t, opt = {}) => new TextRun({ text: t, ...opt });
const b = t => beh(t, { bold: true });
const i_ = t => beh(t, { italics: true });
const casti = text => (Array.isArray(text) ? text : [text]).map(t => typeof t === "string" ? beh(t) : t);

const p = (text, opt = {}) => new Paragraph({
  spacing: { after: 120, line: 276 }, alignment: AlignmentType.JUSTIFIED, ...opt, children: casti(text),
});
const h1 = t => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [beh(t)] });
const h2 = t => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [beh(t)] });
const h3 = t => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [beh(t)] });
const odr = (text, uroven = 0) => new Paragraph({
  numbering: { reference: "odrazky", level: uroven }, spacing: { after: 60, line: 276 }, children: casti(text),
});
const cis = (text, ref = "cisla") => new Paragraph({
  numbering: { reference: ref, level: 0 }, spacing: { after: 60, line: 276 }, children: casti(text),
});
const popis = t => new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { before: 60, after: 200 },
  children: [beh(t, { italics: true, size: 18, color: "555555" })],
});
const zlom = () => new Paragraph({ children: [new PageBreak()] });

const OKRAJ = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const OKRAJE = { top: OKRAJ, bottom: OKRAJ, left: OKRAJ, right: OKRAJ };

function tabulka(hlavicka, riadky, sirky, zarovnanie = null) {
  const bunka = (obsah, i, jeHlavicka) => new TableCell({
    width: { size: sirky[i], type: WidthType.DXA }, borders: OKRAJE,
    margins: { top: 50, bottom: 50, left: 90, right: 90 },
    shading: jeHlavicka ? { type: ShadingType.CLEAR, color: "auto", fill: "DCE6F1" } : undefined,
    children: [new Paragraph({
      alignment: jeHlavicka ? AlignmentType.CENTER : (zarovnanie ? zarovnanie[i] : AlignmentType.LEFT),
      children: (Array.isArray(obsah) ? obsah : [obsah]).map(t => typeof t === "string"
        ? beh(t, { bold: jeHlavicka || (i === 0 && !zarovnanie), size: 19 }) : t),
    })],
  });
  return new Table({
    width: { size: SIRKA, type: WidthType.DXA }, columnWidths: sirky,
    rows: [
      new TableRow({ tableHeader: true, children: hlavicka.map((t, i) => bunka(t, i, true)) }),
      ...riadky.map(r => new TableRow({ children: r.map((t, i) => bunka(t, i, false)) })),
    ],
  });
}

function rozmerPng(subor) {
  const d = fs.readFileSync(subor);
  return { data: d, w: d.readUInt32BE(16), h: d.readUInt32BE(20) };
}

function obrazok(subor, text, sirka = MAX_SIRKA_OBR) {
  const { data, w, h } = rozmerPng(subor);
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { before: 120 }, keepNext: true,
      children: [new ImageRun({
        type: "png", data, transformation: { width: sirka, height: Math.round(sirka * h / w) },
        altText: { title: text, description: text, name: path.basename(subor) },
      })],
    }),
    popis(text),
  ];
}

const graf = (nazov, text) => obrazok(path.join(KOREN, "grafy", nazov), text);

function citanieGrafu(co, ako, zaver) {
  return [
    p([b("Čo ukazuje: "), co]),
    p([b("Ako ho čítať: "), ako]),
    p([b("Čo z neho vyplýva: "), zaver]),
  ];
}

const obsah = [
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 1800, after: 120 },
    children: [beh("Dopravná úloha", { bold: true, size: 52, color: "1F4E79" })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { after: 600 },
    children: [beh("Návod a vysvetlenie programu na porovnanie metód východiskového riešenia", { size: 28, color: "444444" })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { after: 80 },
    children: [beh("Ako program funguje · čo znamenajú skratky · ako čítať grafy", { size: 22, color: "666666" })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { after: 1200 },
    children: [beh("október 2026", { size: 22, color: "666666" })],
  }),
  new Paragraph({ children: [beh("Obsah", { bold: true, size: 28, color: "1F4E79" })], spacing: { after: 120 } }),
  new TableOfContents("Obsah", { hyperlink: true, headingStyleRange: "1-2" }),
  p([i_("Ak sa obsah nezobrazí, klikni naň pravým tlačidlom a vyber „Aktualizovať pole“.")], { spacing: { before: 120 } }),
  zlom(),

  h1("1. Čo program robí"),
  p("Program porovnáva metódy, ktorými sa hľadá prvé (východiskové) riešenie dopravnej úlohy. Vygeneruje veľké "
    + "množstvo náhodných úloh (napríklad 100 000), každú vyrieši všetkými vybranými metódami a potom z každého "
    + "východiskového riešenia dopočíta najlacnejšie možné riešenie (optimum) metódou MODI. Nakoniec spočíta, ktorá "
    + "metóda bola najbližšie k optimu a koľko práce potom ešte zostalo."),
  p([b("Najsprávnejšia"), " metóda je tá, ktorej prvé riešenie je v priemere najbližšie k optimu. ",
    b("Najefektívnejšia"), " je tá, po ktorej treba najmenej opravných krokov metódy MODI a najmenej času."]),
  p("Okrem metód z prednášky (SZR, IM, VAM) program obsahuje aj tri nové, vymyslené metódy (JVR, MDD, PVM), "
    + "ktoré sa dajú porovnať s tými z prednášky."),

  h1("2. Dopravná úloha v skratke"),
  p("Máme niekoľko dodávateľov, ktorí majú tovar, a niekoľko odberateľov, ktorí ho potrebujú. Poznáme cenu "
    + "prepravy jednej jednotky tovaru od každého dodávateľa ku každému odberateľovi. Hľadáme plán prepravy – kto "
    + "komu koľko pošle – pri ktorom je celková cena najnižšia."),
  p("Príklad z prednášky: 3 dodávatelia (D1–D3), 4 odberatelia (O1–O4). V tabuľke sú ceny, vpravo kapacity "
    + "dodávateľov a dole požiadavky odberateľov:"),
  tabulka(["", "O1", "O2", "O3", "O4", "kapacita a_i"],
    [["D1", "3", "5", "4", "1", "10"], ["D2", "2", "1", "3", "2", "20"], ["D3", "4", "5", "1", "3", "10"],
      ["požiadavka b_j", "10", "5", "5", "20", ""]],
    [2238, 1300, 1300, 1300, 1300, 2200],
    [AlignmentType.LEFT, AlignmentType.CENTER, AlignmentType.CENTER, AlignmentType.CENTER, AlignmentType.CENTER, AlignmentType.CENTER]),
  popis("Tabuľka 1: Príklad dopravnej úlohy z prednášky (optimum z* = 65)"),
  p("Riešenie sa hľadá v dvoch krokoch: najprv nejakou metódou nájdeme prvý prípustný plán (východiskové riešenie), "
    + "potom ho metódou MODI postupne zlepšujeme, až kým sa už zlepšiť nedá (optimum)."),

  h1("3. Skratky a pojmy"),
  h2("3.1 Metódy"),
  tabulka(["skratka", "celý názov", "čo robí v jednej vete"], [
    ["SZR", "metóda severozápadného rohu", "Plní tabuľku od ľavého horného rohu, na ceny nehľadí."],
    ["IM", "indexová metóda", "Vždy obsadí najlacnejšie voľné pole."],
    ["VAM", "Vogelova aproximačná metóda", "Obslúži riadok alebo stĺpec, kde by „zlá voľba“ najviac predražila prepravu."],
    ["MODI", "metóda potenciálov (modifikovaná distribučná)", "Z východiskového riešenia krok za krokom nájde optimum."],
    ["JVR", "metóda juhovýchodného rohu (nová)", "Ako SZR, ale začína v pravom dolnom rohu."],
    ["MDD", "metóda dvojitej diferencie (nová)", "Variácia VAM – pole dostane diferenciu riadku aj stĺpca."],
    ["PVM", "predvídavá metóda (nová)", "Vyskúša 3 kandidátov, zvyšok dopočíta VAM a vyberie najlepšieho."],
  ], [1100, 3300, 5238]),
  popis("Tabuľka 2: Skratky metód"),
  h2("3.2 Značky a pojmy"),
  tabulka(["značka / pojem", "význam"], [
    ["m, n", "počet dodávateľov (riadkov tabuľky) a počet odberateľov (stĺpcov tabuľky)"],
    ["D1, D2, … / O1, O2, …", "dodávatelia / odberatelia"],
    ["D*, O*", "fiktívny dodávateľ alebo odberateľ – pridá sa, keď sa ponuka nerovná dopytu; ceny k nemu sú 0"],
    ["a_i", "kapacita dodávateľa i – koľko tovaru má"],
    ["b_j", "požiadavka odberateľa j – koľko tovaru chce"],
    ["c_ij", "cena prepravy jednej jednotky od dodávateľa i k odberateľovi j"],
    ["x_ij", "koľko jednotiek sa prepraví od dodávateľa i k odberateľovi j (obsadené pole)"],
    ["z", "celková cena plánu = súčet x_ij · c_ij cez všetky polia"],
    ["z*", "optimum – najnižšia možná celková cena"],
    ["odchýlka od optima", "(z − z*) / z* · 100 %; o koľko percent je prvé riešenie drahšie ako optimum (0 % = trafila optimum)"],
    ["vyrovnaná úloha", "súčet kapacít = súčet požiadaviek; inak ide o prebytok ponuky alebo prebytok dopytu"],
    ["bázické pole", "pole, ktoré patrí do riešenia; má ich byť presne m + n − 1"],
    ["degenerácia, ε", "riešenie má menej obsadených polí, než treba; doplní sa pole s nulou (v prednáške ε)"],
    ["diferencia", "rozdiel dvoch najnižších cien v riadku alebo stĺpci (používa VAM a MDD)"],
    ["u_i, v_j", "potenciály riadkov a stĺpcov v metóde MODI; pre bázické polia platí u_i + v_j = c_ij"],
    ["Δ_ij", "u_i + v_j − c_ij; ak sú všetky Δ ≤ 0, riešenie je optimálne, inak sa dá zlacniť"],
    ["Dantzigov obvod", "uzavretá cesta v tabuľke, po ktorej sa presúva tovar pri jednom kroku MODI"],
    ["t", "množstvo presunuté po obvode – najmenšia hodnota v poliach so znamienkom −"],
    ["krok MODI", "jedno zlepšenie plánu presunom po obvode; menej krokov = menej práce"],
    ["seed", "„semienko“ náhody; rovnaký seed = rovnaké úlohy, výsledky sa dajú zopakovať"],
    ["m·n, max(m, n)", "veľkosť úlohy – počet polí tabuľky, resp. väčší z rozmerov"],
    ["priemer, medián", "priemer = súčet / počet; medián = prostredná hodnota (polovica úloh je pod ňou)"],
    ["kvartil", "hodnota, pod ktorou je štvrtina (1. kvartil) alebo tri štvrtiny (3. kvartil) úloh"],
    ["95 % IS", "95 % interval spoľahlivosti – rozsah, v ktorom so 95 % istotou leží skutočná priemerná hodnota"],
    ["ms, µs", "milisekunda (tisícina sekundy), mikrosekunda (milióntina sekundy)"],
  ], [2700, 6938]),
  popis("Tabuľka 3: Značky a pojmy"),

  h1("4. Ako program funguje"),
  p("Výpočet jednej úlohy prebieha vždy v rovnakých krokoch:"),
  cis([b("Vygenerovanie úlohy. "), "Z čísla seed a poradového čísla úlohy sa náhodne určí počet dodávateľov m a odberateľov n "
    + "(predvolene 3 až 20), ceny c_ij (1–20 alebo 1–100), kapacity a požiadavky. Polovica úloh je vyrovnaná, štvrtina má "
    + "prebytok ponuky a štvrtina prebytok dopytu. Rovnaký seed vždy vytvorí tie isté úlohy."]),
  cis([b("Vyrovnanie. "), "Ak sa ponuka nerovná dopytu, pridá sa fiktívny dodávateľ D* alebo odberateľ O* s cenami 0, "
    + "ktorý „zoberie“ alebo „dodá“ rozdiel."]),
  cis([b("Východiskové riešenie. "), "Každá vybraná metóda (SZR, IM, VAM, prípadne JVR, MDD, PVM) nájde svoj prvý plán. "
    + "Zmeria sa jeho cena z a čas výpočtu."]),
  cis([b("Optimum. "), "Z každého východiskového riešenia sa metódou MODI dopočíta optimum z* a spočíta sa, koľko krokov "
    + "MODI bolo treba. Všetky metódy musia dôjsť k rovnakému optimu – je to kontrola správnosti."]),
  cis([b("Zápis výsledkov. "), "Pre každú metódu sa zapíše z, z*, odchýlka od optima, či trafila optimum, počet krokov MODI "
    + "a časy. Z toho sa počítajú priemery, tabuľky a grafy."]),
  p("Úlohy sa počítajú naraz na všetkých jadrách procesora, preto aj 100 000 úloh trvá len okolo minúty a pol. "
    + "Správnosť programu je overená na príkladoch z prednášky a porovnaním optima s nezávislým riešičom (knižnica scipy) "
    + "na 2 000 náhodných úlohách – zhoda bola vo všetkých."),

  h1("5. Metódy podrobnejšie"),
  h3("SZR – metóda severozápadného rohu"),
  p("Vždy obsadí ľavé horné pole zostávajúcej tabuľky čo najväčším množstvom x = min(a_i, b_j). Dodávateľa, ktorý minul "
    + "tovar, alebo odberateľa, ktorý je uspokojený, škrtne a pokračuje. Je najjednoduchšia a najrýchlejšia, ale na ceny "
    + "vôbec nehľadí, preto býva jej riešenie ďaleko od optima."),
  h3("IM – indexová metóda"),
  p("Vždy obsadí pole s najnižšou cenou v zostávajúcej tabuľke. Pri zhode cien rozhoduje vyšší riadok, potom ľavejší "
    + "stĺpec. Hľadí na ceny, preto je mnohonásobne lepšia ako SZR."),
  h3("VAM – Vogelova aproximačná metóda"),
  p("Pre každý riadok a stĺpec spočíta diferenciu – rozdiel dvoch najnižších cien. Veľká diferencia znamená, že ak "
    + "nevyberieme najlacnejšie pole, výrazne si priplatíme. Preto obslúži riadok alebo stĺpec s najväčšou diferenciou, "
    + "a to jeho najlacnejším poľom. Pri zhode rozhoduje nižšia cena, potom riadok pred stĺpcom."),
  h3("MODI – metóda potenciálov"),
  p("Zoberie východiskové riešenie, spočíta potenciály u_i a v_j (u1 = 0, pre bázické polia u_i + v_j = c_ij) a pre "
    + "ostatné polia Δ_ij = u_i + v_j − c_ij. Ak sú všetky Δ ≤ 0, riešenie je optimálne. Inak do riešenia vstúpi pole "
    + "s najväčším Δ, nájde sa Dantzigov uzavretý obvod a po ňom sa presunie množstvo t. Opakuje sa, kým nie je optimum."),
  h3("JVR – metóda juhovýchodného rohu (nová)"),
  p("Zrkadlový obraz SZR – začína v pravom dolnom rohu a ide doľava a hore. Zaujímavé zistenie: dáva vždy presne ten "
    + "istý plán ako SZR. Ak si všetok tovar predstavíme ako úsečku, dodávatelia aj odberatelia si ju rozdelia na úseky "
    + "a rohová metóda pošle z Di do Oj toľko, koľko sa ich úseky prekrývajú. JVR číta tú istú úsečku len z druhého "
    + "konca a prekrytie sa tým nezmení."),
  h3("MDD – metóda dvojitej diferencie (nová)"),
  p("Spočíta diferencie ako VAM. Každé pole dostane skóre: diferencia jeho riadku, ak je v riadku najlacnejšie, plus "
    + "diferencia jeho stĺpca, ak je najlacnejšie v stĺpci. Obsadí pole s najväčším skóre. Pole, ktoré je najlacnejšie "
    + "v riadku aj v stĺpci zároveň, je tak „dvojnásobne naliehavé“. Kvalitou je takmer rovnaká ako VAM."),
  h3("PVM – predvídavá metóda (nová)"),
  p("V každom kroku vyberie 3 polia s najväčším skóre MDD (kandidátov). Pre každého skúsi: obsadí ho a zvyšok úlohy "
    + "dopočíta metódou VAM. Naozaj obsadí toho kandidáta, pri ktorom vyšla najnižšia celková cena – „pozrie sa dopredu“. "
    + "Je založená na známej technike pohľadu dopredu (rollout). Je asi dvakrát presnejšia ako VAM, ale počíta viac."),

  h1("6. Aplikácia"),
  p([b("Spustenie: "), "Windows – dvojklik na aplikacia.bat; macOS a Linux – aplikacia.command. Pri prvom spustení si "
    + "program sám pripraví prostredie a nainštaluje knižnice (1–3 minúty, treba internet)."]),
  h2("6.1 Záložka Simulácia"),
  ...obrazok(path.join(__dirname, "obrazky", "okno_simulacia.png"), "Obrázok 1: Záložka Simulácia po výpočte 1 000 úloh všetkými metódami", 620),
  odr([b("Koľko úloh vypočítať"), " – ľubovoľné číslo; pod ním sa ukáže odhad času a veľkosti súboru."]),
  odr([b("Spustiť / Zastaviť"), " – spustí výpočet, dá sa kedykoľvek zastaviť (doteraz vypočítané ostane)."]),
  odr([b("Metódy"), " – z prednášky (SZR, IM, VAM), len nové (JVR, MDD, PVM) alebo všetkých šesť."]),
  odr([b("Procesy, seed, náhodné úlohy"), " – počet jadier, „semienko“ náhody, veľkosť tabuliek, ceny a typy úloh."]),
  odr([b("Uloženie"), " – výsledky sa dajú uložiť do súboru CSV v priečinku vysledky."]),
  odr([b("Export do Excelu"), " – súbor s tabuľkami, grafmi a vysvetlivkami v ľudskej reči."]),
  odr([b("Vyhodnotiť"), " – podrobné štatistiky a 9 grafov (kapitola 7.2); len pre metódy z prednášky."]),
  p("Vpravo hore je priebeh výpočtu (koľko úloh, rýchlosť, čas, chyby), pod ním tabuľka priebežných výsledkov a štyri "
    + "živé grafy (kapitola 7.1)."),
  p([b("Stĺpce tabuľky: "), "trafila optimum – v koľkých % úloh bolo prvé riešenie hneď optimálne; priemerná odchýlka od "
    + "optima; kroky MODI – koľkokrát musela MODI riešenie opraviť; najlepšia v úlohe – v koľkých % úloh dala metóda "
    + "najlacnejšie riešenie zo všetkých (pri zhode sa počíta každej); čas na úlohu – metóda + MODI."]),
  h2("6.2 Záložka Vlastná úloha"),
  ...obrazok(path.join(__dirname, "obrazky", "okno_vlastna_uloha.png"), "Obrázok 2: Vlastná úloha – príklad z prednášky riešený predvídavou metódou", 620),
  p("Do tabuľky sa zadajú vlastné ceny, kapacity a požiadavky (až 10 × 10), alebo sa tlačidlom vyplní príklad "
    + "z prednášky či náhodná úloha. V zozname „Ako počítať“ sa vyberie jedna metóda alebo skupina metód. Pri zaškrtnutom "
    + "„Celý postup krok za krokom“ program vypíše každé obsadenie poľa s dôvodom (pri VAM a MDD aj diferencie, pri PVM "
    + "kandidátov), potom potenciály, tabuľku Δ, Dantzigov obvod a presun t až po optimum. Postup sa dá uložiť do súboru."),
  h2("6.3 Záložka Ukážka náhodnej úlohy"),
  p("Vygeneruje malú náhodnú úlohu a ukáže riešenia SZR, IM, VAM a optimum – vhodné na porovnanie s ručným výpočtom."),

  h1("7. Grafy – ako fungujú a čo ukazujú"),
  p("Všetky grafy používajú rovnaké farby: SZR modrá, IM oranžová, VAM zelená, JVR fialová, MDD tyrkysová, PVM žltá."),
  p([b("Čo sa v grafoch opakuje:")]),
  odr([b("Logaritmická mierka"), " – na osi idú hodnoty 1, 2, 5, 10, 20, 50, 100… namiesto rovnomerných krokov. Používa sa, "
    + "keď sú hodnoty veľmi rozdielne (SZR okolo 200 %, VAM okolo 15 %). Bez nej by malé hodnoty splynuli pri nule."]),
  odr([b("Svetlý pás okolo čiary"), " – 95 % interval spoľahlivosti. Čím je užší, tým presnejšie číslo poznáme. Pri 100 000 "
    + "úlohách je väčšinou taký úzky, že ho takmer nevidno."]),
  odr([b("Veľkosť úlohy m·n"), " – počet polí tabuľky. Úlohy sa zoskupia po 25 (napríklad 75–99 polí) a bod na čiare je "
    + "priemer skupiny."]),

  h2("7.1 Živé grafy v aplikácii"),
  p("Štyri grafy v záložke Simulácia sa prekresľujú počas výpočtu (obrázok 1)."),
  h3("Priebežný priemer odchýlky od optima"),
  ...citanieGrafu("ako sa vyvíja priemerná odchýlka každej metódy, ako pribúdajú vypočítané úlohy.",
    "vodorovná os je počet doteraz vypočítaných úloh, zvislá priemerná odchýlka (logaritmická mierka). Na začiatku čiary "
    + "kolíšu, lebo priemer je z malého počtu úloh; neskôr sa ustália.",
    "keď sú čiary rovné, ďalšie úlohy už výsledok nezmenia – úloh je dosť. Čím nižšie je čiara, tým lepšia metóda."),
  h3("Priemerná odchýlka podľa veľkosti úlohy"),
  ...citanieGrafu("priemernú odchýlku pre úlohy rôznej veľkosti; veľkosť je väčší z rozmerov tabuľky max(m, n).",
    "každý bod je priemer všetkých úloh danej veľkosti; zvislá os je logaritmická.",
    "všetky metódy sú pri väčších úlohách horšie, poradie metód sa však nemení."),
  h3("Priemerný počet krokov MODI podľa veľkosti úlohy"),
  ...citanieGrafu("koľko opravných krokov MODI bolo v priemere treba pri úlohách rôznej veľkosti.",
    "vodorovne veľkosť max(m, n), zvisle priemerný počet krokov.",
    "počet krokov rastie s veľkosťou; pri rohových metódach (SZR, JVR) rastie najrýchlejšie, pri PVM najpomalšie."),
  h3("Rozdelenie odchýlky od optima"),
  ...citanieGrafu("koľko percent úloh malo odchýlku 0–5 %, 5–10 %, 10–15 % atď. (histogram).",
    "vodorovne odchýlka po 5 %, zvisle podiel úloh. Posledný stĺpec (500 %) zahŕňa všetky väčšie odchýlky.",
    "dobré metódy majú vysoký úzky vrchol pri nule; SZR je rozliata ďaleko doprava."),

  h2("7.2 Grafy z vyhodnotenia (100 000 úloh)"),
  p("Tieto grafy vytvorí tlačidlo Vyhodnotiť (alebo príkaz analyza.py) z uloženého behu. Ukázané sú výsledky hlavného "
    + "behu so 100 000 úlohami pre metódy z prednášky. Uložené sú v priečinku grafy."),
  h3("Odchýlka od optima podľa veľkosti úlohy"),
  ...graf("odchylka_vs_velkost.png", "Obrázok 3: Priemerná odchýlka od optima podľa veľkosti úlohy m·n"),
  ...citanieGrafu("o koľko percent je prvé riešenie v priemere drahšie ako optimum, podľa počtu polí tabuľky.",
    "vodorovne m·n, zvisle priemerná odchýlka v %; svetlý pás je 95 % interval spoľahlivosti.",
    "SZR sa s veľkosťou prudko zhoršuje (zo ~75 % až na ~430 %), IM a VAM rastú pomaly. VAM je pri každej veľkosti najlepšia."),
  h3("Počet krokov MODI podľa veľkosti úlohy"),
  ...graf("kroky_modi_vs_velkost.png", "Obrázok 4: Priemerný počet krokov MODI do optima"),
  ...citanieGrafu("koľko opráv metódou MODI bolo treba, kým sa z východiskového riešenia dostalo optimum.",
    "vodorovne m·n, zvisle priemerný počet krokov.",
    "po SZR treba pri najväčších úlohách okolo 60 krokov, po IM okolo 22 a po VAM okolo 15. Lepšie východiskové riešenie = menej práce."),
  h3("Podiel úloh, kde metóda hneď trafila optimum"),
  ...graf("optimum_vs_velkost.png", "Obrázok 5: Podiel úloh s trafeným optimom podľa veľkosti"),
  ...citanieGrafu("v koľkých percentách úloh bolo prvé riešenie rovno optimálne.",
    "vodorovne m·n, zvisle percento úloh.",
    "pri malých úlohách VAM trafí optimum hneď až v 40 % prípadov, IM v 11 %. Pri úlohách nad ~150 polí to už nezvládne "
    + "žiadna metóda – vždy treba MODI."),
  h3("Celkový čas podľa veľkosti úlohy"),
  ...graf("cas_celkovy_vs_velkost.png", "Obrázok 6: Celkový čas (metóda + MODI) podľa veľkosti úlohy"),
  ...citanieGrafu("ako dlho trvá vyriešiť úlohu – východisková metóda aj MODI spolu.",
    "vodorovne m·n, zvisle čas v milisekundách (logaritmická mierka).",
    "SZR je celkovo najpomalšia, lebo MODI má po nej veľa práce. IM a VAM sú takmer rovnako rýchle – IM je mierne rýchlejšia "
    + "pri malých úlohách, pri veľkých sa vyrovnajú. Časy závisia od počítača."),
  h3("Čas samotnej metódy podľa veľkosti úlohy"),
  ...graf("cas_metody_vs_velkost.png", "Obrázok 7: Čas samotnej východiskovej metódy (bez MODI)"),
  ...citanieGrafu("koľko trvá len nájdenie východiskového riešenia, bez dopočítania optima.",
    "vodorovne m·n, zvisle čas v ms (logaritmická mierka).",
    "SZR je najrýchlejšia, VAM najpomalšia (počíta diferencie v každom kroku). VAM si však tento čas vráti tým, že MODI má po nej najmenej práce."),
  h3("Krabicové grafy odchýlok"),
  ...graf("boxplot_odchylok.png", "Obrázok 8: Rozdelenie odchýlok – krabicové grafy"),
  ...citanieGrafu("ako sú odchýlky rozložené – nielen priemer, ale aj rozptyl.",
    "krabica siaha od 1. po 3. kvartil (v nej je prostredná polovica úloh), čiara v krabici je medián, „fúzy“ ukazujú "
    + "rozsah bežných hodnôt. Vpravo je detail IM a VAM, lebo vedľa SZR by boli príliš malé.",
    "VAM má krabicu najnižšie a najužšiu – je nielen najlepšia v priemere, ale aj najspoľahlivejšia."),
  h3("Empirická distribučná funkcia odchýlky"),
  ...graf("ecdf_odchylky.png", "Obrázok 9: Empirická distribučná funkcia odchýlky od optima"),
  ...citanieGrafu("koľko percent úloh malo odchýlku najviac x.",
    "pre hodnotu x na vodorovnej osi prečítaš na zvislej, v koľkých % úloh bola odchýlka ≤ x. Os x je logaritmická "
    + "(0, 1, 10, 100, 1 000 %). Čím je krivka viac vľavo, tým lepšia metóda.",
    "napríklad pri 10 % odchýlke: VAM má takú malú odchýlku asi v polovici úloh, IM len asi v 13 % a SZR takmer nikdy."),
  h3("Poradie metód v tej istej úlohe"),
  ...graf("poradie_metod.png", "Obrázok 10: Ako často bola metóda 1., 2. alebo 3. v tej istej úlohe"),
  ...citanieGrafu("párové porovnanie – v každej úlohe sa metódy zoradia podľa z a spočíta sa, ako často bola ktorá prvá, druhá a tretia.",
    "každý pruh má 100 %, sýta farba je 1. miesto, svetlejšie 2. a 3. miesto. Pri remíze majú metódy spoločné miesto.",
    "VAM je najlepšia v 88,8 % úloh, IM v 12,4 %, SZR je takmer vždy posledná (99,4 %)."),
  h3("Odchýlka podľa typu úlohy a cenového rozsahu"),
  ...graf("odchylka_typ_cena.png", "Obrázok 11: Odchýlka od optima podľa typu úlohy a rozsahu cien"),
  ...citanieGrafu("či záleží na tom, či je úloha vyrovnaná, a aké veľké sú ceny.",
    "každá skupina stĺpcov je jeden typ úlohy a cenový rozsah; malá čiarka na vrchu stĺpca je 95 % interval spoľahlivosti.",
    "nevyrovnané úlohy (prebytok ponuky alebo dopytu) sú pre všetky metódy ťažšie a pri cenách 1–100 sú odchýlky mierne "
    + "väčšie ako pri 1–20. Poradie VAM < IM < SZR platí vo všetkých skupinách."),

  h2("7.3 Grafy v Exceli"),
  p("Export do Excelu obsahuje vlastné grafy priamo v hárkoch:"),
  odr([b("Výsledky metód"), " – dva stĺpcové grafy: priemerná odchýlka a priemerný počet krokov MODI pre každú metódu."]),
  odr([b("Podľa veľkosti"), " – dva čiarové grafy ako obrázky 3 a 4, ale podľa max(m, n)."]),
  odr([b("Rozdelenie odchýlky"), " – čiarový graf podielu úloh v pásmach odchýlky (ako živý graf v kapitole 7.1)."]),
  p("Hodnoty v Exceli sú vzorce – keď sa klikne na bunku, vidno, z čoho sa počíta."),

  h1("8. Hlavné výsledky"),
  p("Porovnanie všetkých šiestich metód na rovnakých 20 000 náhodných úlohách (seed 20261025):"),
  tabulka(["metóda", "trafila optimum", "priemerná odchýlka", "kroky MODI"], [
    ["SZR", "0,03 %", "216,8 %", "26,4"], ["IM", "0,92 %", "36,8 %", "10,1"], ["VAM", "5,91 %", "15,2 %", "6,3"],
    ["JVR (nová)", "0,03 %", "216,8 %", "26,4"], ["MDD (nová)", "4,71 %", "15,4 %", "6,4"], ["PVM (nová)", "12,34 %", "7,8 %", "5,0"],
  ], [2638, 2300, 2400, 2300],
  [AlignmentType.LEFT, AlignmentType.CENTER, AlignmentType.CENTER, AlignmentType.CENTER]),
  popis("Tabuľka 4: Porovnanie metód (20 000 úloh)"),
  odr([b("Z metód z prednášky je najsprávnejšia VAM"), " – najmenšia odchýlka a najmenej krokov MODI. Najhoršia je SZR, lebo nehľadí na ceny."]),
  odr([b("V celkovom čase sú IM a VAM približne rovnaké"), " – VAM počíta dlhšie, ale ušetrí na MODI."]),
  odr([b("JVR dáva vždy rovnaký plán ako SZR"), " – zrkadlenie rohu nič nezlepší."]),
  odr([b("MDD je takmer rovnako dobrá ako VAM"), ", PVM je asi dvakrát presnejšia ako VAM, ale počíta viac."]),
  p([i_("Podrobné čísla sú v súboroch vysledky/suhrn.md a vysledky/hlavny100k.xlsx.")]),
];

const doc = new Document({
  creator: "Dopravná úloha – simulácia",
  title: "Dopravná úloha – návod a vysvetlenie programu",
  features: { updateFields: true },
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 30, bold: true, color: "1F4E79", font: FONT },
        paragraph: { spacing: { before: 360, after: 140 }, outlineLevel: 0, keepNext: true } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, color: "2E75B6", font: FONT },
        paragraph: { spacing: { before: 260, after: 100 }, outlineLevel: 1, keepNext: true } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 23, bold: true, color: "1F4E79", font: FONT },
        paragraph: { spacing: { before: 200, after: 80 }, outlineLevel: 2, keepNext: true } },
    ],
  },
  numbering: {
    config: [
      { reference: "odrazky", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 567, hanging: 283 } } } }] },
      { reference: "cisla", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 567, hanging: 340 } } } }] },
    ],
  },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    footers: {
      default: new Footer({ children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "777777" })],
      })] }),
    },
    children: obsah,
  }],
});

Packer.toBuffer(doc).then(buf => {
  const ciel = path.join(__dirname, "navod.docx");
  fs.writeFileSync(ciel, buf);
  console.log("Uložené:", ciel);
});
