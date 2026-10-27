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
echo  Prve spustenie - pripravujem program (1 az 5 minut, potrebny internet)...
echo.
call :najdi_python
if not defined PY (
    echo  Python sa nenasiel, instalujem ho automaticky...
    where winget >nul 2>nul && winget install -e --id Python.Python.3.13 --scope user --silent --accept-package-agreements --accept-source-agreements
    call :najdi_python
)
if not defined PY (
    echo.
    echo  Python sa nepodarilo nainstalovat automaticky.
    echo  Stiahni ho z https://www.python.org/downloads/ ^(na ARM pocitaci verziu "ARM64"^),
    echo  pri instalacii zaskrtni "Add python.exe to PATH" a spusti tento subor znova.
    start "" https://www.python.org/downloads/
    pause
    exit /b 1
)
"%PY%" -m venv .venv
if errorlevel 1 (
    echo  Nepodarilo sa vytvorit prostredie .venv.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    ".venv\Scripts\python.exe" -m pip install numpy matplotlib openpyxl
    if errorlevel 1 (
        echo  Instalacia kniznic zlyhala. Skontroluj internet a skus znova.
        rmdir /s /q .venv
        pause
        exit /b 1
    )
    echo  Upozornenie: scipy sa nenainstaloval, tlacidlo Vyhodnotit nebude fungovat.
)
echo.
echo  Hotovo.
exit /b 0

:najdi_python
set "PY="
for /f "delims=" %%p in ('py -3 -c "import sys,tkinter;print(sys.executable) if sys.version_info>=(3,10) else exit(1)" 2^>nul') do set "PY=%%p"
if defined PY exit /b 0
for /f "delims=" %%p in ('python -c "import sys,tkinter;print(sys.executable) if sys.version_info>=(3,10) else exit(1)" 2^>nul') do set "PY=%%p"
if defined PY exit /b 0
for /d %%d in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if exist "%%d\python.exe" (
        "%%d\python.exe" -c "import sys,tkinter;exit(sys.version_info<(3,10))" >nul 2>nul && set "PY=%%d\python.exe"
    )
)
exit /b 0
