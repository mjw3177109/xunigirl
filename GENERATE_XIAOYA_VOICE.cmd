@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Please run INSTALL.cmd first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m pip install qwen-tts
if errorlevel 1 (echo [FAIL] qwen-tts install failed.& pause & exit /b 1)
".venv\Scripts\python.exe" tools\generate_xiaoya_voice.py --force
if errorlevel 1 (echo [FAIL] Voice generation failed; original preview stays available.& pause & exit /b 1)
".venv\Scripts\python.exe" tools\configure_upstream.py
if errorlevel 1 (echo [WARN] Run CONFIGURE_VOICE.cmd after full install.)
echo [OK] Xiaoya voice generated and configured.
pause
