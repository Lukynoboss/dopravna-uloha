@echo off
rem Textove menu v konzole (Windows x64 aj ARM64)
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call "%~dp0aplikacia.bat" instaluj
if not exist ".venv\Scripts\python.exe" exit /b 1
".venv\Scripts\python.exe" spusti.py
pause
