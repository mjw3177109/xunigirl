@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_duix.ps1"
set "exitcode=%errorlevel%"
if not "%exitcode%"=="0" echo [FAIL] DUIX start/preflight failed. See message above.
pause
exit /b %exitcode%
