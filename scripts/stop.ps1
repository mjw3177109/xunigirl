$Root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$file=Join-Path $Root 'data\server.pid'
if (!(Test-Path $file)){Write-Host '没有本项目运行记录';exit 0}
$id=[int](Get-Content $file | Select-Object -First 1)
$proc=Get-CimInstance Win32_Process -Filter "ProcessId=$id" -ErrorAction SilentlyContinue
if ($proc -and $proc.CommandLine -like '*backend.main:app*') {
  Stop-Process -Id $id -Force -ErrorAction SilentlyContinue
  Write-Host '[OK] 独立后端已停止。' -ForegroundColor Green
} elseif($proc){Write-Host '[WARN] PID 对应的不是本项目，未停止其他程序。' -ForegroundColor Yellow}
Remove-Item $file -Force -ErrorAction SilentlyContinue
