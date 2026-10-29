const FARBY = { SZR: "#2b7bd6", IM: "#ee6a2c", VAM: "#1fae7a", JVR: "#8e5bd0", MDD: "#0f8b8d", PVM: "#d4a017" };
const POPIS = {
  SZR: "severozápadný roh", IM: "indexová metóda", VAM: "Vogelova metóda",
  JVR: "juhovýchodný roh (nová)", MDD: "dvojitá diferencia (nová)", PVM: "predvídavá metóda (nová)",
};
const SKUPINY = { prednaska: ["SZR", "IM", "VAM"], nove: ["JVR", "MDD", "PVM"], vsetky: ["SZR", "IM", "VAM", "JVR", "MDD", "PVM"] };
const CAS_METODY = { SZR: 0.012, IM: 0.006, VAM: 0.006, JVR: 0.012, MDD: 0.007, PVM: 0.22 };
const JADRA = navigator.hardwareConcurrency || 4;
const MAX_VLAKIEN = Math.max(1, Math.min(16, JADRA));

const $ = (id) => document.getElementById(id);

function cislo(x, des = 0) {
  const [cele, zlomok] = Math.abs(x).toFixed(des).split(".");
  const skupiny = cele.replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  return (x < 0 ? "-" : "") + skupiny + (zlomok ? "," + zlomok : "");
}

function casText(s) {
  if (s < 60) return `${Math.round(s)} s`;
  if (s < 3600) return `${Math.floor(s / 60)} min ${String(Math.floor(s % 60)).padStart(2, "0")} s`;
  return `${Math.floor(s / 3600)} h ${String(Math.floor((s % 3600) / 60)).padStart(2, "0")} min`;
}

function celeCislo(text, nazov, od = null, doH = null) {
  const t = String(text).replace(/\s/g, "");
  if (!/^-?\d+$/.test(t)) throw new Error(`${nazov}: zadaj celé číslo.`);
  const x = parseInt(t, 10);
  if (od !== null && x < od) throw new Error(`${nazov}: najmenej ${od}.`);
  if (doH !== null && x > doH) throw new Error(`${nazov}: najviac ${doH}.`);
  return x;
}

function stiahni(obsah, nazov, typ) {
  const url = URL.createObjectURL(new Blob([obsah], { type: typ }));
  const a = document.createElement("a");
  a.href = url;
  a.download = nazov;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}

function datumSubor() {
  const d = new Date();
  const p = (x) => String(x).padStart(2, "0");
  return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}_${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}`;
}

class Pracovnik {
  constructor(uloha) {
    this.w = new Worker(`python.js?uloha=${uloha}`);
    this.dalsieId = 1;
    this.cakajuce = new Map();
    this.pripraveny = new Promise((ok, zle) => {
      this.w.addEventListener("message", (e) => {
        const d = e.data;
        if (d.typ === "pripraveny") ok();
        else if (d.typ === "chyba_nacitania") zle(new Error(d.chyba));
        else if (d.typ === "vysledok") {
          const c = this.cakajuce.get(d.id);
          this.cakajuce.delete(d.id);
          if (!c) return;
          if (d.chyba) c.zle(new Error(d.chyba));
          else c.ok(d.vysledok);
        }
      });
      this.w.addEventListener("error", (e) => zle(new Error(e.message || "chyba vlákna")));
    });
  }

  volaj(f, args = []) {
    const id = this.dalsieId++;
    return new Promise((ok, zle) => {
      this.cakajuce.set(id, { ok, zle });
      this.w.postMessage({ id, f, args });
    });
  }
}

function vykresliCasti(pre, casti) {
  pre.textContent = "";
  for (const [text, tag] of casti) {
    if (tag) {
      const s = document.createElement("span");
      s.className = tag;
      s.textContent = text;
      pre.appendChild(s);
    } else {
      pre.appendChild(document.createTextNode(text));
    }
  }
  pre.scrollTop = 0;
}

const hlavny = new Pracovnik("hlavny");

function nastavPripravenost(ok) {
  for (const id of ["spusti", "vl-vyries", "uk-vyries", "uk-nova"]) $(id).disabled = !ok;
}

hlavny.pripraveny.then(
  () => {
    $("nacitanie").textContent = "Python je pripravený";
    $("nacitanie").classList.add("hotovo");
    nastavPripravenost(true);
    ukazka();
  },
  (e) => {
    $("nacitanie").textContent = "Python sa nepodarilo načítať: " + e.message;
    $("nacitanie").classList.add("chyba");
  },
);

for (const b of document.querySelectorAll(".zalozky button")) {
  b.addEventListener("click", () => {
    for (const x of document.querySelectorAll(".zalozky button")) x.classList.toggle("aktivna", x === b);
    for (const t of document.querySelectorAll(".tab")) t.classList.toggle("aktivna", t.id === "tab-" + b.dataset.tab);
  });
}

const sim = {
  bezi: false,
  stop: false,
  pocet: 0,
  dalsi: 0,
  rozbehnute: 0,
  t0: 0,
  trvanie: 0,
  hotovo: 0,
  posledny: null,
  pracovnici: [],
  parametre: null,
  pJson: "",
  mena: SKUPINY.prednaska,
  casovac: null,
  posledneKreslenie: 0,
};

$("vlakna").value = Math.max(1, Math.min(8, JADRA - 1));
$("vlakna").max = MAX_VLAKIEN;

for (const b of document.querySelectorAll("[data-pocet]")) {
  b.addEventListener("click", () => { $("pocet").value = cislo(+b.dataset.pocet); odhad(); });
}
$("seed-nahodny").addEventListener("click", (e) => {
  e.preventDefault();
  $("seed").value = String(1 + Math.floor(Math.random() * 99999999));
});
for (const id of ["pocet", "vlakna", "skupina"]) $(id).addEventListener("input", odhad);
for (const id of ["vyrovnane", "ponuka"]) $(id).addEventListener("input", dopyt);

function odhad() {
  try {
    const n = celeCislo($("pocet").value, "počet", 1);
    const v = Math.max(1, celeCislo($("vlakna").value, "vlákna", 1));
    const mena = SKUPINY[$("skupina").value];
    const s = (n * mena.reduce((sum, m) => sum + (CAS_METODY[m] || 0.01), 0)) / Math.min(v, JADRA);
    $("odhad").textContent = `odhad: ~${casText(s)} v tomto prehliadači`;
  } catch {
    $("odhad").textContent = "";
  }
}

function dopyt() {
  const z = 100 - (parseInt($("vyrovnane").value, 10) || 0) - (parseInt($("ponuka").value, 10) || 0);
  $("dopyt").textContent = `Prebytok dopytu: ${z} % (zvyšok do 100 %)`;
  $("dopyt").classList.toggle("cervena", z < 0);
}

function nastavenia() {
  const pocet = celeCislo($("pocet").value, "Počet úloh", 1, 10_000_000);
  const vlakna = celeCislo($("vlakna").value, "Vlákna", 1, MAX_VLAKIEN);
  const seed = celeCislo($("seed").value, "Seed", 0);
  const d = {};
  for (const [k, n, od, doH] of [["m_od", "Dodávatelia m", 2, 60], ["m_do", "Dodávatelia m", 2, 60],
    ["n_od", "Odberatelia n", 2, 60], ["n_do", "Odberatelia n", 2, 60],
    ["cena_a", "Ceny – prvý rozsah", 1, 1_000_000], ["cena_b", "Ceny – druhý rozsah", 1, 1_000_000],
    ["podiel_a", "Podiel prvého rozsahu", 0, 100], ["vyrovnane", "Vyrovnané úlohy", 0, 100],
    ["ponuka", "Prebytok ponuky", 0, 100]]) {
    d[k] = celeCislo($(k).value, n, od, doH);
  }
  if (d.m_od > d.m_do || d.n_od > d.n_do) throw new Error("Veľkosť: „od“ musí byť menšie alebo rovné „do“.");
  if (d.vyrovnane + d.ponuka > 100) throw new Error("Vyrovnané + prebytok ponuky nesmie byť viac ako 100 %.");
  return { pocet, vlakna, seed, d, mena: SKUPINY[$("skupina").value] };
}

async function spusti() {
  let n;
  try {
    n = nastavenia();
  } catch (e) {
    alert(e.message);
    return;
  }
  sim.bezi = true;
  sim.stop = false;
  sim.pocet = n.pocet;
  sim.seed = n.seed;
  sim.vlakna = n.vlakna;
  sim.mena = n.mena;
  sim.dalsi = 0;
  sim.rozbehnute = 0;
  sim.hotovo = 0;
  sim.posledny = null;
  $("spusti").disabled = true;
  $("zastav").disabled = false;
  $("excel").disabled = true;
  $("stav").textContent = `Pripravujem ${n.vlakna} ${n.vlakna === 1 ? "vlákno" : n.vlakna < 5 ? "vlákna" : "vlákien"}…`;
  $("stav").style.color = "";
  try {
    sim.pJson = await hlavny.volaj("parametre_json", [JSON.stringify(n.d)]);
    sim.parametre = JSON.parse(sim.pJson);
    await hlavny.volaj("novy_beh", [JSON.stringify(n.mena)]);
    while (sim.pracovnici.length < n.vlakna) sim.pracovnici.push(new Pracovnik("vypocet"));
    await Promise.all(sim.pracovnici.slice(0, n.vlakna).map((p) => p.pripraveny));
  } catch (e) {
    alert("Chyba pri príprave výpočtu: " + e.message);
    sim.bezi = false;
    $("spusti").disabled = false;
    $("zastav").disabled = true;
    return;
  }
  if (sim.stop) {
    koniec();
    return;
  }
  vytvorTabulku(n.mena);
  sim.t0 = performance.now();
  sim.blok = Math.max(5, Math.min(200, Math.floor(n.pocet / (n.vlakna * 40)) || 5));
  $("stav").textContent = `Počítam ${cislo(n.pocet)} úloh metódami ${n.mena.join(", ")} na ${n.vlakna} vláknach…`;
  for (const p of sim.pracovnici.slice(0, n.vlakna)) pracuj(p);
  sim.casovac = setInterval(obnov, 500);
  obnov();
}

async function pracuj(p) {
  while (!sim.stop && sim.dalsi < sim.pocet) {
    const od = sim.dalsi;
    const doH = Math.min(od + sim.blok, sim.pocet);
    sim.dalsi = doH;
    sim.rozbehnute++;
    try {
      const vysledok = await p.volaj("blok", [sim.seed, od, doH, sim.pJson, JSON.stringify(sim.mena)]);
      await hlavny.volaj("pridaj", [vysledok]);
    } catch (e) {
      sim.stop = true;
      alert("Chyba výpočtu: " + e.message);
    }
    sim.rozbehnute--;
  }
  if (sim.rozbehnute === 0 && sim.bezi) koniec();
}

async function koniec() {
  if (!sim.bezi) return;
  sim.bezi = false;
  clearInterval(sim.casovac);
  sim.trvanie = (performance.now() - sim.t0) / 1000;
  await obnov(true);
  const zastavene = sim.stop;
  $("stav").textContent = `${zastavene ? "Zastavené" : "Hotovo"} – ${cislo(sim.hotovo)} úloh za ${casText(sim.trvanie)}`;
  $("stav").style.color = zastavene ? "" : "var(--zelena)";
  $("spusti").disabled = false;
  $("zastav").disabled = true;
  $("excel").disabled = !sim.hotovo;
}

$("spusti").addEventListener("click", spusti);
$("zastav").addEventListener("click", () => {
  if (!sim.bezi) return;
  sim.stop = true;
  $("zastav").disabled = true;
  $("stav").textContent = "Zastavujem – dokončujú sa rozbehnuté bloky…";
});

function vytvorTabulku(mena) {
  const tb = $("tabulka").querySelector("tbody");
  tb.textContent = "";
  for (const m of mena) {
    const tr = document.createElement("tr");
    tr.id = "r-" + m;
    tr.innerHTML = `<td style="color:${FARBY[m]}">${m} – ${POPIS[m]}</td>` + "<td>–</td>".repeat(5);
    tb.appendChild(tr);
  }
}

async function obnov(vynut = false) {
  if (sim.obnovuje) return;
  sim.obnovuje = true;
  try {
    const s = JSON.parse(await hlavny.volaj("prehlad"));
    sim.posledny = s;
    sim.hotovo = s.hotovo;
    const uplynulo = sim.bezi ? (performance.now() - sim.t0) / 1000 : sim.trvanie;
    const podiel = sim.pocet ? s.hotovo / sim.pocet : 0;
    const rychlost = uplynulo > 0 ? s.hotovo / uplynulo : 0;
    $("progres").style.width = `${100 * podiel}%`;
    $("pct").textContent = sim.pocet ? `${cislo(100 * podiel, 1)} %` : "";
    $("d-hotovo").textContent = `${cislo(s.hotovo)} / ${cislo(sim.pocet)}`;
    $("d-rychlost").textContent = s.hotovo ? cislo(rychlost) : "–";
    $("d-uplynulo").textContent = casText(uplynulo);
    $("d-zostava").textContent = sim.bezi && rychlost > 0 ? casText((sim.pocet - s.hotovo) / rychlost) : "–";
    $("d-chyby").textContent = String(s.chyby);
    $("d-chyby").style.color = s.chyby ? "var(--cervena)" : "";
    for (const m of s.metody) {
      const r = $("r-" + m);
      const t = s.tabulka[m];
      if (!r || !t) continue;
      const bunky = r.querySelectorAll("td");
      const hodnoty = [`${cislo(t.optimum, 2)} %`, `${cislo(t.odchylka, 1)} %`, cislo(t.kroky, 1),
        `${cislo(t.najlepsia, 1)} %`, `${cislo(t.cas_ms, 2)} ms`];
      hodnoty.forEach((h, i) => { bunky[i + 1].textContent = h; });
    }
    if (vynut || performance.now() - sim.posledneKreslenie > 1000) {
      sim.posledneKreslenie = performance.now();
      kresli(s);
    }
  } finally {
    sim.obnovuje = false;
  }
}

const LOG_ZNACKY = new Set([0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000]);

function novyGraf(id, y, x = {}) {
  return new Chart($(id), {
    type: "line",
    data: { datasets: [] },
    options: {
      animation: false,
      responsive: true,
      maintainAspectRatio: false,
      parsing: false,
      normalized: true,
      interaction: { mode: "nearest", intersect: false },
      plugins: { legend: { labels: { boxWidth: 12, font: { size: 11 } } } },
      scales: {
        x: { type: "linear", grid: { color: "#e8ecf1" }, ticks: { font: { size: 10 } }, ...x },
        y: { grid: { color: "#e8ecf1" }, ticks: { font: { size: 10 } }, ...y },
      },
    },
  });
}

const logOs = {
  type: "logarithmic",
  ticks: { font: { size: 10 }, callback: (v) => (LOG_ZNACKY.has(+v.toPrecision(3)) ? cislo(v, v < 1 ? 1 : 0) : "") },
};

const grafy = [
  novyGraf("g1", logOs, { title: { display: true, text: "počet vypočítaných úloh", font: { size: 10 } }, ticks: { font: { size: 10 }, callback: (v) => cislo(v) } }),
  novyGraf("g2", logOs, { title: { display: true, text: "veľkosť úlohy max(m, n)", font: { size: 10 } }, ticks: { font: { size: 10 }, stepSize: 1 } }),
  novyGraf("g3", { beginAtZero: true }, { title: { display: true, text: "veľkosť úlohy max(m, n)", font: { size: 10 } }, ticks: { font: { size: 10 }, stepSize: 1 } }),
  novyGraf("g4", { beginAtZero: true, ticks: { font: { size: 10 }, callback: (v) => `${cislo(v)} %` } },
    { min: 0, max: 500, title: { display: true, text: "odchýlka od optima (%) · posledný stĺpec = 500 % a viac", font: { size: 10 } } }),
];

function sada(m, data, navyse = {}) {
  return { label: m, data, borderColor: FARBY[m], backgroundColor: FARBY[m], borderWidth: 2, pointRadius: 0, ...navyse };
}

function kresli(s) {
  const kladne = (body) => body.filter((b) => b.y > 0);
  grafy[0].data.datasets = s.metody.map((m, i) => sada(m, kladne(s.historia.map(([x, y]) => ({ x, y: y[i] })))));
  grafy[1].data.datasets = s.metody.map((m) => sada(m, kladne(s.velkost[m].map(([x, y]) => ({ x, y }))), { pointRadius: 2 }));
  grafy[2].data.datasets = s.metody.map((m) => sada(m, s.velkost[m].map(([x, , y]) => ({ x, y })), { pointRadius: 2 }));
  grafy[3].data.datasets = s.metody.map((m) => sada(m, s.stredy.map((x, i) => ({ x, y: s.hist[m][i] })),
    { stepped: "middle", fill: "origin", backgroundColor: FARBY[m] + "2e", borderWidth: 1.6 }));
  for (const g of grafy) g.update("none");
}

$("excel").addEventListener("click", async () => {
  if (!sim.hotovo) return;
  const b = $("excel");
  b.disabled = true;
  const stary = $("stav").textContent;
  $("stav").textContent = "Vytváram Excel… (prvýkrát sa načíta knižnica openpyxl)";
  try {
    const d = new Date();
    const info = {
      nazov: null, seed: sim.seed, procesy: sim.vlakna, pocet_zadany: sim.pocet,
      parametre_generatora: sim.parametre, trvanie_s: sim.trvanie,
      datum: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`,
    };
    const bajty = await hlavny.volaj("excel", [JSON.stringify(info)]);
    stiahni(bajty, `vysledky_${datumSubor()}.xlsx`, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
    $("stav").textContent = stary;
  } catch (e) {
    $("stav").textContent = "Export do Excelu zlyhal.";
    alert("Export do Excelu zlyhal: " + e.message);
  }
  b.disabled = false;
});

const vl = { m: 3, n: 4, C: [], a: [], b: [] };

function vlMriezka() {
  const t = $("vl-mriezka");
  t.textContent = "";
  const hlava = t.insertRow();
  hlava.appendChild(document.createElement("th"));
  for (let j = 0; j < vl.n; j++) {
    const th = document.createElement("th");
    th.textContent = `O${j + 1}`;
    hlava.appendChild(th);
  }
  const thA = document.createElement("th");
  thA.textContent = "a_i";
  hlava.appendChild(thA);
  const pole = (hodnota, uloz, trieda = "") => {
    const td = document.createElement("td");
    const i = document.createElement("input");
    i.value = hodnota ?? "";
    i.inputMode = "numeric";
    if (trieda) i.className = trieda;
    i.addEventListener("input", () => { uloz(i.value); i.classList.remove("zle"); vlSucty(); });
    i.addEventListener("keydown", (e) => { if (e.key === "Enter") vlVyries(); });
    td.appendChild(i);
    return td;
  };
  for (let i = 0; i < vl.m; i++) {
    const r = t.insertRow();
    const th = document.createElement("th");
    th.textContent = `D${i + 1}`;
    r.appendChild(th);
    for (let j = 0; j < vl.n; j++) r.appendChild(pole(vl.C[i]?.[j], (v) => { (vl.C[i] ||= [])[j] = v; }));
    const td = pole(vl.a[i], (v) => { vl.a[i] = v; }, "kapacita");
    td.classList.add("oddel");
    r.appendChild(td);
  }
  const r = t.insertRow();
  const th = document.createElement("th");
  th.textContent = "b_j";
  r.appendChild(th);
  for (let j = 0; j < vl.n; j++) r.appendChild(pole(vl.b[j], (v) => { vl.b[j] = v; }, "poziadavka"));
  vlSucty();
}

function vlSucty() {
  const sucet = (pole, k) => {
    let s = 0;
    for (let i = 0; i < k; i++) {
      const t = String(pole[i] ?? "").replace(/\s/g, "");
      if (!/^\d+$/.test(t)) return null;
      s += +t;
    }
    return s;
  };
  const sa = sucet(vl.a, vl.m);
  const sb = sucet(vl.b, vl.n);
  if (sa === null || sb === null) {
    $("vl-sucty").textContent = "Ponuka spolu: –   ·   Dopyt spolu: –";
    return;
  }
  const stavText = sa === sb ? "vyrovnaná úloha"
    : sa > sb ? `prebytok ponuky ${cislo(sa - sb)} → pridá sa fiktívny odberateľ`
      : `prebytok dopytu ${cislo(sb - sa)} → pridá sa fiktívny dodávateľ`;
  $("vl-sucty").textContent = `Ponuka spolu: ${cislo(sa)}   ·   Dopyt spolu: ${cislo(sb)}   ·   ${stavText}`;
}

function vlNastav(C, a, b) {
  vl.m = a.length;
  vl.n = b.length;
  vl.C = C.map((r) => r.map(String));
  vl.a = a.map(String);
  vl.b = b.map(String);
  $("vl-m").value = vl.m;
  $("vl-n").value = vl.n;
  vlMriezka();
}

function vlRozmer() {
  try {
    vl.m = celeCislo($("vl-m").value, "Dodávatelia m", 1, 10);
    vl.n = celeCislo($("vl-n").value, "Odberatelia n", 1, 10);
    vlMriezka();
  } catch (e) {
    alert(e.message);
  }
}

$("vl-m").addEventListener("change", vlRozmer);
$("vl-n").addEventListener("change", vlRozmer);
$("vl-priklad").addEventListener("click", () => vlNastav([[3, 5, 4, 1], [2, 1, 3, 2], [4, 5, 1, 3]], [10, 20, 10], [10, 5, 5, 20]));
$("vl-vymaz").addEventListener("click", () => { vl.C = []; vl.a = []; vl.b = []; vlMriezka(); });
$("vl-nahodne").addEventListener("click", async () => {
  try {
    const d = JSON.parse(await hlavny.volaj("nahodna", [vl.m, vl.n]));
    vlNastav(d.C, d.a, d.b);
  } catch (e) {
    alert(e.message);
  }
});

async function vlVyries() {
  if ($("vl-vyries").disabled) return;
  const chyby = [];
  const vstupy = $("vl-mriezka").querySelectorAll("input");
  let k = 0;
  const hodnota = (text, nazov, minimum) => {
    const vstup = vstupy[k++];
    const t = String(text ?? "").replace(/\s/g, "");
    if (/^\d+$/.test(t) && +t >= minimum && +t <= 1_000_000_000) return +t;
    chyby.push(nazov);
    vstup?.classList.add("zle");
    return 0;
  };
  const C = [];
  const a = [];
  for (let i = 0; i < vl.m; i++) {
    C.push([]);
    for (let j = 0; j < vl.n; j++) C[i].push(hodnota(vl.C[i]?.[j], `c${i + 1}${j + 1}`, 0));
    a.push(hodnota(vl.a[i], `a${i + 1}`, 1));
  }
  const b = [];
  for (let j = 0; j < vl.n; j++) b.push(hodnota(vl.b[j], `b${j + 1}`, 1));
  if (chyby.length) {
    alert("Tieto polia sú prázdne alebo nesprávne (sú označené červenou):\n" + chyby.slice(0, 20).join(", ")
      + (chyby.length > 20 ? "…" : "")
      + "\n\nCeny musia byť celé čísla 0 alebo viac, kapacity a požiadavky celé čísla 1 alebo viac.");
    return;
  }
  $("vl-vyries").disabled = true;
  try {
    const casti = JSON.parse(await hlavny.volaj("vlastna", [JSON.stringify({ C, a, b, metoda: $("vl-metoda").value, postup: $("vl-postup").checked })]));
    vykresliCasti($("vl-text"), casti);
  } catch (e) {
    alert("Výpočet zlyhal: " + e.message);
  }
  $("vl-vyries").disabled = false;
}

$("vl-vyries").addEventListener("click", vlVyries);
$("vl-uloz").addEventListener("click", () => {
  const text = $("vl-text").textContent.trim();
  if (text) stiahni(text + "\n", "postup_vlastna_uloha.txt", "text/plain;charset=utf-8");
});

$("uk-id").value = String(1 + Math.floor(Math.random() * 99999));

async function ukazka() {
  let m, n, id;
  try {
    m = celeCislo($("uk-m").value, "Dodávatelia m", 2, 10);
    n = celeCislo($("uk-n").value, "Odberatelia n", 2, 10);
    id = celeCislo($("uk-id").value, "Číslo úlohy", 0);
  } catch (e) {
    alert(e.message);
    return;
  }
  try {
    vykresliCasti($("uk-text"), JSON.parse(await hlavny.volaj("ukazka", [m, n, id])));
  } catch (e) {
    alert("Výpočet zlyhal: " + e.message);
  }
}

$("uk-vyries").addEventListener("click", ukazka);
$("uk-nova").addEventListener("click", () => { $("uk-id").value = String(1 + Math.floor(Math.random() * 99999)); ukazka(); });

vytvorTabulku(SKUPINY.prednaska);
vlNastav([[3, 5, 4, 1], [2, 1, 3, 2], [4, 5, 1, 3]], [10, 20, 10], [10, 5, 5, 20]);
odhad();
dopyt();
kresli({ metody: [], historia: [], velkost: {}, stredy: [], hist: {} });
