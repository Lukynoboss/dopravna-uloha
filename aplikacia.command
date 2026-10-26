#!/bin/bash
cd "$(dirname "$0")" || exit 1

if [ ! -x .venv/bin/python ]; then
    echo
    echo "Prvé spustenie – pripravujem prostredie (1 až 3 minúty, potrebný internet)..."
    echo
    if ! command -v python3 >/dev/null 2>&1; then
        echo "Python 3 nie je nainštalovaný. Stiahni ho z https://www.python.org/downloads/"
        echo "(na Macu s čipom M1/M2/M3/M4 je inštalátor „universal2“ – funguje natívne na ARM)."
        read -r -p "Stlač Enter..."
        exit 1
    fi
    if ! python3 -c "import tkinter" >/dev/null 2>&1; then
        echo "Tento Python nemá tkinter (grafické okno)."
        echo "macOS: použi Python z python.org, alebo  brew install python-tk"
        echo "Linux: sudo apt install python3-tk python3-venv"
        read -r -p "Stlač Enter..."
        exit 1
    fi
    python3 -m venv .venv || { echo "Nepodarilo sa vytvoriť prostredie .venv."; read -r -p "Stlač Enter..."; exit 1; }
    .venv/bin/python -m pip install --upgrade pip
    if ! .venv/bin/python -m pip install numpy matplotlib openpyxl; then
        echo "Inštalácia knižníc zlyhala. Skontroluj internet a skús znova."
        rm -rf .venv
        read -r -p "Stlač Enter..."
        exit 1
    fi
    .venv/bin/python -m pip install scipy || echo "Upozornenie: scipy sa nenainštaloval, tlačidlo Vyhodnotiť nebude fungovať."
fi

if [ "$1" = "instaluj" ]; then
    exit 0
fi
exec .venv/bin/python aplikacia.py
