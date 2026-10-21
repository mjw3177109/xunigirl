@echo off
setlocal
cd /d "%~dp0"
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (
  where py >nul 2>&1 && (set "PY=py -3.11") || (set "PY=python")
)
%PY% tools\preflight_4090.py --mode digital
if errorlevel 1 (
 echo [WARN] Preflight script reported an error.
)
echo.
echo [REPORT] data\preflight_4090.json
pause
