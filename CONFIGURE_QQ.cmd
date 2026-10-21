@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" ( echo [ERROR] First run INSTALL.cmd & pause & exit /b 1 )
.venv\Scripts\python.exe tools\configure_qq.py
pause
