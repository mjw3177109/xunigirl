$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $Root
function Test-Http([string]$url) {
    try {
        $r = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 5
        Write-Host ('[OK] HTTP ' + $r.StatusCode + ' ' + $url) -ForegroundColor Green
        return $true
    } catch {
        Write-Host ('[FAIL] ' + $url + ': ' + $_.Exception.Message) -ForegroundColor Yellow
        return $false
    }
}
$ok = $true
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    Write-Host '[INFO] GPU memory (MiB):' -ForegroundColor Cyan
    & nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader,nounits
} else { Write-Host '[WARN] nvidia-smi not found' -ForegroundColor Yellow; $ok=$false }
if (Get-Command docker -ErrorAction SilentlyContinue) {
    $state = & docker inspect -f '{{.State.Status}}' duix-avatar-gen-video 2>$null
    if ($LASTEXITCODE -eq 0 -and $state -eq 'running') {
        Write-Host '[OK] DUIX container running' -ForegroundColor Green
        & docker exec duix-avatar-gen-video nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader 2>$null
        if ($LASTEXITCODE -ne 0) {Write-Host '[WARN] GPU probe in Docker failed' -ForegroundColor Yellow}
    } else {Write-Host '[FAIL] DUIX container not running' -ForegroundColor Yellow; $ok=$false}
} else {Write-Host '[FAIL] Docker CLI unavailable' -ForegroundColor Yellow; $ok=$false}
# /easy/query?code=probe may return application-level "not found" but HTTP 200 proves API is listening.
if (-not (Test-Http 'http://127.0.0.1:9000/easy/query?code=probe')) { $ok=$false }
if (Test-Http 'http://127.0.0.1:8765/api/app/status') {
    if (Test-Http 'http://127.0.0.1:8765/voice/api/dh/status') {
        try {
            $d=Invoke-RestMethod -Uri 'http://127.0.0.1:8765/voice/api/dh/status' -TimeoutSec 5
            Write-Host ('[INFO] Digital Human enabled: ' + $d.enabled + '; state: ' + $d.state + '; message: ' + $d.message)
        } catch {}
    } else {$ok=$false}
} else {$ok=$false}
$avatar=Join-Path $Root 'data\duix\temp\my_avatar.mp4'
if (-not (Test-Path $avatar)) {Write-Host '[WARN] Avatar missing: data\duix\temp\my_avatar.mp4' -ForegroundColor Yellow; $ok=$false}
if ($ok) {Write-Host '[OK] All static/service probes passed. Real video generation is NOT yet verified.' -ForegroundColor Green; exit 0}
Write-Host '[CHECK] Resolve warnings; then test generating an actual digital human clip.' -ForegroundColor Yellow
exit 1
