@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" ( echo [ERROR] First run INSTALL_TEXT_ONLY.cmd & pause & exit /b 1 )
.venv\Scripts\python.exe -m pip install -q pytest
.venv\Scripts\python.exe -m pytest -q tests
if errorlevel 1 (echo [FAIL] Unit tests failed. & pause & exit /b 1)
echo [OK] Local source tests passed. GPU model inference is not included in these tests.
pause
