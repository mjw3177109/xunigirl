@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install.ps1"
if errorlevel 1 ( echo [ERROR] Installation failed. See message above. & pause & exit /b 1 )
echo Installation succeeded. Please configure .env and voice reference audio.
pause
