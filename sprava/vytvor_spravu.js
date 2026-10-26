// Vytvorí krátku správu sprava/sprava.docx zo záverov simulácie (čísla podľa vysledky/suhrn.md, beh hlavny100k).
// Spustenie: node sprava/vytvor_spravu.js   (potrebuje npm balík docx; ak nie je lokálne, nastav NODE_PATH)
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, AlignmentType, ImageRun, LevelFormat, BorderStyle, Footer, PageNumber,
} = require("docx");

const KOREN = path.join(__dirname, "..");
const SIRKA = 9638; // šírka textu A4 pri okrajoch 2 cm (DXA)
const FONT = "Calibri";

// ---------- pomocné funkcie ----------
const p = (text, opt = {}) => new Paragraph({
  spacing: { after: 120, line: 276 }, alignment: AlignmentType.JUSTIFIED, ...opt,
  children: (Array.isArray(text) ? text : [text]).map(t => typeof t === "string" ? new TextRun(t) : t),
});
const b = t => new TextRun({ text: t, bold: true });
const h1 = t => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const odrazka = (text) => new Paragraph({
  numbering: { reference: "odrazky", level: 0 }, spacing: { after: 80, line: 276 },
  children: (Array.isArray(text) ? text : [text]).map(t => typeof t === "string" ? new TextRun(t) : t),
});
const popis = t => new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { before: 60, after: 200 },
  children: [new TextRun({ text: t, italics: true, size: 18, color: "555555" })],
});

const OKRAJ = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const OKRAJE = { top: OKRAJ, bottom: OKRAJ, left: OKRAJ, right: OKRAJ };

function tabulka(hlavicka, riadky, sirky) {
  const bunka = (text, i, jeHlavicka, zvyraznit) => new TableCell({
    width: { size: sirky[i], type: WidthType.DXA }, borders: OKRAJE,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    shading: jeHlavicka ? { type: ShadingType.CLEAR, color: "auto", fill: "DCE6F1" }
      : zvyraznit ? { type: ShadingType.CLEAR, color: "auto", fill: "EAF5EA" } : undefined,
    children: [new Paragraph({
      alignment: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER,
      children: [new TextRun({ text, bold: jeHlavicka || (zvyraznit && i === 0), size: 19 })],
    })],
  });
  return new Table({
    width: { size: SIRKA, type: WidthType.DXA }, columnWidths: sirky,
    rows: [
      new TableRow({ tableHeader: true, children: hlavicka.map((t, i) => bunka(t, i, true)) }),
      ...riadky.map(r => new TableRow({ children: r.map((t, i) => bunka(t, i, false, r[0] === "VAM")) })),
    ],
  });
}

function graf(subor, text) {
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { before: 120 },
      children: [new ImageRun({
        type: "png", data: fs.readFileSync(path.join(KOREN, "grafy", subor)),
        transformation: { width: 496, height: 310 },
        altText: { title: text, description: text, name: subor },
      })],
    }),
    popis(text),
  ];
}

// ---------- obsah ----------
const obsah = [
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { after: 80 },
    children: [new TextRun({ text: "Porovnanie metód východiskového riešenia dopravnej úlohy", bold: true, size: 34 })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { after: 300 },
    children: [new TextRun({ text: "Simulácia na 100 000 náhodných úlohách · október 2026", size: 22, color: "555555" })],
  }),

  h1("1. Cieľ"),
  p(["Cieľom bolo zistiť, ktorá z troch metód východiskového riešenia dopravnej úlohy z prednášky L5LZV 5-6 je ",
    b("najsprávnejšia"), " (jej riešenie je najbližšie k optimu) a ",
    b("najefektívnejšia"), " (najkratší čas a najmenej krokov metódy MODI do optima)."]),

  h1("2. Porovnávané metódy"),
  odrazka([b("Metóda severozápadného rohu (SZR)"), " – obsadzuje polia od ľavého horného rohu bez ohľadu na ceny."]),
  odrazka([b("Indexová metóda (IM)"), " – v každom kroku obsadí pole s najnižšou cenou spomedzi neškrtnutých riadkov a stĺpcov."]),
  odrazka([b("Vogelova aproximačná metóda (VAM)"), " – počíta diferencie dvoch najnižších cien v riadkoch a stĺpcoch a obsadzuje lacné pole v rade s najväčšou diferenciou."]),
  p("Z každého východiskového riešenia sa metódou MODI (test optimality cez potenciály u_i, v_j a Dantzigov obvod) pokračovalo až do optima. Nevyrovnané úlohy sa vyrovnali fiktívnym dodávateľom alebo odberateľom s nulovými cenami a pri degenerácii sa dopĺňali nulové bázické polia, aby mala báza vždy m + n − 1 polí. Správnosť implementácie sa overila na príkladoch z prednášky a porovnaním optima s riešičom scipy."),

  h1("3. Simulácia"),
  p("Vygenerovalo sa 100 000 náhodných úloh (pevný seed 20261025, každú úlohu možno zopakovať podľa jej čísla). Všetky tri metódy riešili tú istú úlohu, takže porovnanie je párové."),
  odrazka("počet dodávateľov m aj odberateľov n náhodne od 3 do 20 (nezávisle),"),
  odrazka("jednotkové ceny c_ij: polovica úloh z rozsahu 1–20, polovica z rozsahu 1–100,"),
  odrazka("50 % úloh vyrovnaných, 25 % s prebytkom ponuky, 25 % s prebytkom dopytu (prebytok 5–30 % objemu),"),
  odrazka("kapacity a požiadavky celé čísla, základ 10–100."),
  p("Odchýlka od optima = (z − z*) / z* · 100 %, kde z je hodnota účelovej funkcie východiskového riešenia a z* optimum. Beh trval 80 s na 16 jadrách, bez chýb."),

  h1("4. Výsledky"),
  p([b("Správnosť. "), "VAM dáva výrazne najlepšie východiskové riešenie: v priemere je len o 15 % drahšie než optimum, kým IM o 37 % a SZR o 217 %. Optimum trafí VAM priamo v 6 % úloh. V porovnaní na tej istej úlohe je VAM najlepšia v 89 % úloh a poradie z(VAM) ≤ z(IM) ≤ z(SZR) platí v 88 % úloh (rozdiely sú štatisticky významné, Wilcoxonov test p < 10⁻³⁰⁰)."]),
  tabulka(
    ["metóda", "trafila optimum", "priemerná odchýlka", "medián odchýlky", "najlepšia v úlohe"],
    [
      ["SZR", "0,03 %", "216,9 %", "197,3 %", "0,1 %"],
      ["IM", "0,88 %", "36,8 %", "30,8 %", "12,4 %"],
      ["VAM", "6,00 %", "15,3 %", "11,2 %", "88,8 %"],
    ],
    [1838, 1950, 1950, 1950, 1950],
  ),
  popis("Tabuľka 1: Správnosť východiskového riešenia (100 000 úloh; pri remíze sa počíta spoločné 1. miesto)"),

  p([b("Efektívnosť. "), "Z riešenia VAM treba v priemere len 6,4 kroku MODI do optima (IM 10,1, SZR 26,6). V celkovom čase (metóda + MODI) je však mierne rýchlejšia IM: samotný výpočet VAM s diferenciami trvá dlhšie, než koľko ušetrí na MODI. Rozdiel je malý (asi 6 %) a pri najväčších úlohách sa časy IM a VAM vyrovnajú. SZR je síce najrýchlejšia samotná metóda, ale pre zlé východiskové riešenie je celkovo najpomalšia."]),
  tabulka(
    ["metóda", "kroky MODI (priemer)", "čas metódy", "čas MODI", "celkový čas"],
    [
      ["SZR", "26,6", "0,40 ms", "5,81 ms", "6,21 ms"],
      ["IM", "10,1", "0,62 ms", "2,25 ms", "2,87 ms"],
      ["VAM", "6,4", "1,53 ms", "1,52 ms", "3,05 ms"],
    ],
    [1838, 1950, 1950, 1950, 1950],
  ),
  popis("Tabuľka 2: Efektívnosť (priemerné hodnoty; časy v Pythone, orientačné)"),

  ...graf("odchylka_vs_velkost.png", "Obrázok 1: Priemerná odchýlka od optima podľa veľkosti úlohy m·n"),
  ...graf("kroky_modi_vs_velkost.png", "Obrázok 2: Počet krokov MODI do optima podľa veľkosti úlohy"),
  ...graf("cas_celkovy_vs_velkost.png", "Obrázok 3: Celkový čas (metóda + MODI) podľa veľkosti úlohy, logaritmická mierka"),

  p([b("Vplyv vlastností úlohy. "), "S rastúcou veľkosťou sa všetky metódy zhoršujú. Pri malých úlohách (m·n ≤ 49) trafí VAM optimum v 24,5 % prípadov (IM 4,6 %), pri veľkých (m·n ≥ 250) už žiadna metóda. Nevyrovnané úlohy sú ťažšie: odchýlka VAM je 10,9 % pri vyrovnaných, ale 19,6 % pri prebytku ponuky aj dopytu. Širší rozsah cien (1–100) odchýlky mierne zvyšuje (VAM 16,1 % oproti 14,4 %). Poradie VAM < IM < SZR sa nezmenilo v žiadnej skupine."]),

  h1("5. Závery"),
  odrazka([b("Najsprávnejšia je Vogelova metóda (VAM)"), " – najmenšia odchýlka od optima, najčastejšie trafí optimum a v 89 % úloh je najlepšia."]),
  odrazka([b("Najmenej krokov MODI potrebuje VAM"), " (6,4 oproti 10,1 pri IM a 26,6 pri SZR)."]),
  odrazka([b("V celkovom čase vedie mierne indexová metóda"), " – o 6 % pred VAM; rozdiel závisí od implementácie a pri veľkých úlohách mizne."]),
  odrazka([b("Metóda severozápadného rohu je najhoršia"), " vo všetkých podmienkach – je síce najjednoduchšia, ale vyžaduje najviac práce pri optimalizácii."]),
  p("Pre ručný výpočet aj pre program je preto najvhodnejšia VAM: hoci je výpočtovo náročnejšia, jej riešenie je najbližšie k optimu a ušetrí najviac iterácií MODI. Indexová metóda je rozumný kompromis, ak záleží na jednoduchosti.", { spacing: { before: 120, after: 120, line: 276 } }),
  p([new TextRun({ text: "Podrobné tabuľky a ďalšie grafy: vysledky/suhrn.md a priečinok grafy/.", italics: true, size: 18, color: "555555" })]),
];

const doc = new Document({
  creator: "Dopravná úloha – simulácia",
  title: "Porovnanie metód východiskového riešenia dopravnej úlohy",
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [{
      id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { size: 28, bold: true, color: "1F4E79", font: FONT },
      paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 0, keepNext: true },
    }],
  },
  numbering: {
    config: [{
      reference: "odrazky",
      levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 567, hanging: 283 } } } }],
    }],
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
  const ciel = path.join(__dirname, "sprava.docx");
  fs.writeFileSync(ciel, buf);
  console.log("Uložené:", ciel);
});
