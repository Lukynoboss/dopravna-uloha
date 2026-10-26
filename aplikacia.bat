@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    call :instaluj || exit /b 1
)
if /i "%~1"=="instaluj" exit /b 0

start "" ".venv\Scripts\pythonw.exe" aplikacia.py
exit /b 0

:instaluj
echo.
echo  Prve spustenie - pripravujem prostredie (1 az 3 minuty, potrebny internet)...
echo.
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (
    where python >nul 2>nul && set "PY=python"
)
if not defined PY (
    echo  Python nie je nainstalovany.
    echo  Stiahni ho z https://www.python.org/downloads/ ^(na ARM pocitaci verziu "ARM64"^)
    echo  a pri instalacii zaskrtni "Add python.exe to PATH". Potom spusti tento subor znova.
    pause
    exit /b 1
)
%PY% -m venv .venv
if errorlevel 1 (
    echo  Nepodarilo sa vytvorit prostredie .venv.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install numpy matplotlib openpyxl
if errorlevel 1 (
    echo  Instalacia kniznic zlyhala. Skontroluj internet a skus znova.
    rmdir /s /q .venv
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -m pip install scipy || echo  Upozornenie: scipy sa nenainstaloval, tlacidlo Vyhodnotit nebude fungovat.
echo.
echo  Hotovo.
exit /b 0
