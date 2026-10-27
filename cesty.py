import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    KOREN = Path.home() / "Documents" / "DopravnaUloha"
    KOREN.mkdir(parents=True, exist_ok=True)
else:
    KOREN = Path(__file__).resolve().parent
