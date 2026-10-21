@echo off
cd /d "%~dp0"
docker compose -f docker\compose-4090.yml down
pause
