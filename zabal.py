from __future__ import annotations

import time
import zipfile
from pathlib import Path

KOREN = Path(__file__).resolve().parent
NAZOV = "DopravnaUloha"

PROGRAM = ["aplikacia.py", "metody.py", "generator.py", "simulacia.py", "statistiky.py", "export_excel.py",
           "analyza.py", "test_metody.py", "spusti.py", "postup.py",
           "aplikacia.bat", "aplikacia.command", "spusti.bat", "requirements.txt", "README.md"]
VYSLEDKY = {
    "vysledky/suhrn.md": "vysledky/suhrn.md",
    "vysledky/hlavny100k.xlsx": "vysledky/hlavny100k.xlsx",
    "vysledky/beh_hlavny100k.json": "vysledky/beh_hlavny100k.json",
    "sprava/sprava.docx": "vysledky/sprava.docx",
    "sprava/navod.docx": "Navod.docx",
}
SPUSTITELNE = {"aplikacia.command"}


def pridaj(zf: zipfile.ZipFile, zdroj: Path, ciel: str):
    info = zipfile.ZipInfo(f"{NAZOV}/{ciel}", date_time=time.localtime(zdroj.stat().st_mtime)[:6])
    info.compress_type = zipfile.ZIP_DEFLATED
    prava = 0o755 if Path(ciel).name in SPUSTITELNE else 0o644
    info.external_attr = (0o100000 | prava) << 16
    info.create_system = 3
    zf.writestr(info, zdroj.read_bytes())


def main():
    vystup = KOREN / "export" / f"{NAZOV}.zip"
    vystup.parent.mkdir(exist_ok=True)
    chyba = [s for s in PROGRAM + list(VYSLEDKY) if not (KOREN / s).exists()]
    if chyba:
        print("Chýbajú súbory:", ", ".join(chyba))
    with zipfile.ZipFile(vystup, "w") as zf:
        for s in PROGRAM:
            if (KOREN / s).exists():
                pridaj(zf, KOREN / s, s)
        for zdroj, ciel in VYSLEDKY.items():
            if (KOREN / zdroj).exists():
                pridaj(zf, KOREN / zdroj, ciel)
        for png in sorted((KOREN / "grafy").glob("*.png")):
            pridaj(zf, png, f"grafy/{png.name}")
        pocet = len(zf.namelist())
    print(f"Uložené: {vystup}  ({pocet} súborov, {vystup.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
