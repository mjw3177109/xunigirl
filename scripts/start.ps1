$ErrorActionPreference='Stop'
$Root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $Root
$Python=Join-Path $Root '.venv\Scripts\python.exe'
if (!(Test-Path $Python)){throw '请先运行 INSTALL.cmd 或 INSTALL_TEXT_ONLY.cmd'}
$pidFile=Join-Path $Root 'data\server.pid'
if (Test-Path $pidFile) {
  $savedPid=(Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
  if($savedPid) {
    $candidate=Get-CimInstance Win32_Process -Filter "ProcessId=$savedPid" -ErrorAction SilentlyContinue
    if($candidate -and $candidate.CommandLine -like '*backend.main:app*' -and $candidate.ExecutablePath -eq $Python) {
      try {
        $r=Invoke-RestMethod -Uri 'http://127.0.0.1:8765/api/app/status' -TimeoutSec 3
        if($r.ok) {
          Write-Host '服务已经在运行。' -ForegroundColor Green
          Start-Process 'http://127.0.0.1:8765/'
          exit 0
        }
      } catch {}
    }
  }
}
$occupied=Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue
if ($occupied) {throw '端口 8765 已被其他程序占用。请先停止占用此端口的程序。'}
New-Item -ItemType Directory -Path (Join-Path $Root 'data') -Force | Out-Null
$stdout=Join-Path $Root 'data\server.stdout.log'
$stderr=Join-Path $Root 'data\server.stderr.log'
$proc=Start-Process -FilePath $Python -ArgumentList @('-m','uvicorn','backend.main:app','--host','127.0.0.1','--port','8765') -WorkingDirectory $Root -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
Set-Content -Path $pidFile -Value $proc.Id -Encoding ASCII
$ready=$false
for($i=0;$i -lt 35;$i++){
  Start-Sleep -Milliseconds 600
  try{$r=Invoke-RestMethod -Uri 'http://127.0.0.1:8765/api/app/status' -TimeoutSec 2; if($r.ok){$ready=$true;break}}catch{}
}
if (!$ready){Write-Host '[FAIL] 服务未能启动，查看 data\server.stderr.log' -ForegroundColor Red;exit 1}
Write-Host '[OK] 独立服务已启动 http://127.0.0.1:8765/' -ForegroundColor Green
Start-Process 'http://127.0.0.1:8765/'
