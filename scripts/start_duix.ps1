# Start the OPTIONAL DUIX video-only container; do not start DSH, FunASR or extra TTS containers.
$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $Root
$Compose = Join-Path $Root 'docker\compose-4090.yml'
$Avatar = Join-Path $Root 'data\duix\temp\my_avatar.mp4'
New-Item -ItemType Directory -Force (Split-Path $Avatar) | Out-Null
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host '[FAIL] Docker CLI not found. Install/start Docker Desktop.' -ForegroundColor Red
    exit 1
}
try {
    & docker info --format '{{.ServerVersion}}' 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Docker Desktop engine unavailable' }
    & docker compose -f $Compose config -q
    if ($LASTEXITCODE -ne 0) { throw 'DUIX compose configuration invalid' }
} catch { Write-Host ('[FAIL] ' + $_) -ForegroundColor Red; exit 1 }
# The container can start without an avatar, but speaking cannot work until one is prepared.
if (-not (Test-Path $Avatar)) {
    Write-Host '[WARN] 缺少 data\duix\temp\my_avatar.mp4；容器可以启动，但生成视频前必须准备经过 DUIX 适配/预处理的形象素材。' -ForegroundColor Yellow
} else {
    Write-Host ('[OK] Found avatar candidate: ' + $Avatar) -ForegroundColor Green
}
Write-Host '[INFO] Starting DUIX video worker only (RTX 4090)...' -ForegroundColor Cyan
& docker compose -f $Compose up -d
if ($LASTEXITCODE -ne 0) { Write-Host '[FAIL] Docker compose up failed' -ForegroundColor Red; exit 1 }
Write-Host '[OK] Container started/starting. Warming up may require additional time.' -ForegroundColor Green
try {
    & docker exec duix-avatar-gen-video nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader
    if ($LASTEXITCODE -ne 0) {Write-Host '[WARN] GPU detection in container failed. Check Docker Desktop GPU support.' -ForegroundColor Yellow}
} catch { Write-Host '[WARN] Could not run nvidia-smi in container.' -ForegroundColor Yellow }
Write-Host '[NEXT] Run START.cmd, enable Digital Human in browser, then CHECK_DIGITAL_4090.cmd.' -ForegroundColor Cyan
