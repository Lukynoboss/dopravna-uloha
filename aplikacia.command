#!/bin/bash
cd "$(dirname "$0")" || exit 1

PKG_URL="https://www.python.org/ftp/python/3.13.1/python-3.13.1-macos11.pkg"

najdi_python() {
    PY=""
    kandidati=(/Library/Frameworks/Python.framework/Versions/3.1[0-9]/bin/python3 /opt/homebrew/bin/python3 /usr/local/bin/python3)
    for v in 13 12 11 10 14; do
        p=$(command -v "python3.$v" 2>/dev/null) && kandidati+=("$p")
    done
    xcode-select -p >/dev/null 2>&1 && kandidati+=(/usr/bin/python3)
    for p in "${kandidati[@]}"; do
        if [ -x "$p" ] && "$p" -c "import sys, tkinter; sys.exit(sys.version_info < (3, 10))" >/dev/null 2>&1; then
            PY="$p"
            return 0
        fi
    done
    return 1
}

koniec() {
    read -r -p "Stlač Enter..."
    exit 1
}

if [ ! -x .venv/bin/python ]; then
    echo
    echo "Prvé spustenie – pripravujem program (1 až 5 minút, potrebný internet)..."
    echo
    if ! najdi_python; then
        echo "Python 3.10+ s grafickým oknom sa nenašiel. Sťahujem oficiálny inštalátor z python.org..."
        if curl -fL -o /tmp/python-instalator.pkg "$PKG_URL"; then
            open -W /tmp/python-instalator.pkg
        fi
        if ! najdi_python; then
            echo "Python sa nepodarilo nainštalovať. Stiahni ho ručne z https://www.python.org/downloads/"
            echo "a potom spusti tento súbor znova."
            open "https://www.python.org/downloads/"
            koniec
        fi
    fi
    "$PY" -m venv .venv || { echo "Nepodarilo sa vytvoriť prostredie .venv."; koniec; }
    .venv/bin/python -m pip install --upgrade pip
    if ! .venv/bin/python -m pip install -r requirements.txt; then
        if ! .venv/bin/python -m pip install numpy matplotlib openpyxl; then
            echo "Inštalácia knižníc zlyhala. Skontroluj internet a skús znova."
            rm -rf .venv
            koniec
        fi
        echo "Upozornenie: scipy sa nenainštaloval, tlačidlo Vyhodnotiť nebude fungovať."
    fi
    echo
    echo "Hotovo."
fi

if [ "$1" = "instaluj" ]; then
    exit 0
fi
exec .venv/bin/python aplikacia.py
