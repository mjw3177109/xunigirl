@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\publish_github.ps1"
if errorlevel 1 ( echo [FAIL] GitHub push failed. & pause & exit /b 1 )
echo [OK] GitHub sync finished.
pause
