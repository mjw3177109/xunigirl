@echo off
setlocal
cd /d "%~dp0"
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (where py >nul 2>&1 && (set "PY=py -3.11") || set "PY=python")
%PY% tools\apply_digital_profile.py quality
if errorlevel 1 (echo [FAIL] Profile update failed. & pause & exit /b 1)
echo.
echo [NEXT] If this is the first 1.7B install: INSTALL.cmd, then CONFIGURE_VOICE.cmd.
echo [NEXT] START_DUIX.cmd, START.cmd, then toggle Digital Human in the browser.
pause
