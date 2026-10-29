importScripts("https://cdn.jsdelivr.net/pyodide/v0.27.2/full/pyodide.js");

const ULOHA = new URL(self.location.href).searchParams.get("uloha");
const SUBORY = ULOHA === "hlavny"
  ? ["cesty.py", "metody.py", "generator.py", "statistiky.py", "postup.py", "export_excel.py", "most.py"]
  : ["cesty.py", "metody.py", "generator.py", "simulacia.py"];

let py = null;
let blok = null;
let excelPripraveny = null;

const pripravene = (async () => {
  py = await loadPyodide();
  await py.loadPackage("numpy");
  const texty = await Promise.all(SUBORY.map(async (s) => {
    const odpoved = await fetch("py/" + s);
    if (!odpoved.ok) throw new Error("Nepodarilo sa načítať " + s);
    return [s, await odpoved.text()];
  }));
  for (const [s, t] of texty) py.FS.writeFile("/home/pyodide/" + s, t);
  py.runPython("import sys, json\nsys.path.insert(0, '/home/pyodide')");
  if (ULOHA === "hlavny") {
    py.runPython("import most");
  } else {
    py.runPython([
      "import simulacia",
      "def blok(seed, od, do, p_json, mena_json):",
      "    return json.dumps(simulacia.spracuj_blok(seed, list(range(od, do)), json.loads(p_json), json.loads(mena_json)))",
    ].join("\n"));
  }
})();

pripravene.then(
  () => postMessage({ typ: "pripraveny" }),
  (e) => postMessage({ typ: "chyba_nacitania", chyba: String(e && e.message || e) }),
);

async function pripravExcel() {
  if (!excelPripraveny) {
    excelPripraveny = (async () => {
      await py.loadPackage("micropip");
      await py.pyimport("micropip").install("openpyxl");
    })();
  }
  return excelPripraveny;
}

onmessage = async (e) => {
  const { id, f, args } = e.data;
  try {
    await pripravene;
    let vysledok;
    if (ULOHA === "hlavny") {
      if (f === "excel") await pripravExcel();
      const most = py.pyimport("most");
      const v = most[f](...args);
      if (v && typeof v.toJs === "function") {
        vysledok = new Uint8Array(v.toJs());
        v.destroy();
      } else {
        vysledok = v;
      }
      most.destroy();
    } else {
      blok = blok || py.globals.get("blok");
      vysledok = blok(...args);
    }
    const prenos = vysledok instanceof Uint8Array ? [vysledok.buffer] : [];
    postMessage({ typ: "vysledok", id, vysledok }, prenos);
  } catch (chyba) {
    postMessage({ typ: "vysledok", id, chyba: String(chyba && chyba.message || chyba) });
  }
};
