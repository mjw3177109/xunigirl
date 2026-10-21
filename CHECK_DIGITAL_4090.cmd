@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\check_duix.ps1"
set "exitcode=%errorlevel%"
pause
exit /b %exitcode%
