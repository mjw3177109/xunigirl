$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Repo = 'https://github.com/mjw3177109/xunigirl.git'
Write-Host 'XUNIGIRL: syncing V1.3 complete project to GitHub...' -ForegroundColor Cyan
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Please install Git for Windows first: https://git-scm.com/download/win' }
$Temp = Join-Path $env:TEMP ('xunigirl-publish-' + [Guid]::NewGuid().ToString('N'))
try {
    & git clone --depth 1 $Repo $Temp
    if ($LASTEXITCODE -ne 0) { throw 'GitHub clone failed. Sign into GitHub in Git Credential Manager, then retry.' }
    $skip = @('.git','.env','.venv','upstream','models','__pycache__')
    $ignoredNames = @('conversations.db','server.pid','server.stdout.log','server.stderr.log')
    $srcFiles = Get-ChildItem -LiteralPath $Root -Recurse -File -Force | Where-Object {
        $rel = $_.FullName.Substring($Root.Length).TrimStart('\','/')
        $pathParts = $rel -split '[\\/]'
        $bad = $false
        foreach($part in $pathParts) { if($skip -contains $part) { $bad=$true;break } }
        if ($ignoredNames -contains $_.Name) { $bad=$true }
        if ($_.Name -like '*.pyc' -or $_.Name -like '*.log') { $bad=$true }
        if ($rel -match '^data[\\/]' -and $rel -ne 'data\README.md') { $bad=$true }
        if ($rel -match '^voices[\\/]' -and $rel -notmatch '^voices[\\/](README.md|xiaoya[\\/](ref_audio.wav|ref_text.txt|ref_source.json))$') { $bad=$true }
        -not $bad
    }
    foreach ($f in $srcFiles) {
        $rel = $f.FullName.Substring($Root.Length).TrimStart('\','/')
        $dest = Join-Path $Temp $rel
        $dir=Split-Path $dest -Parent
        if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
        Copy-Item -LiteralPath $f.FullName -Destination $dest -Force
    }
    Set-Location $Temp
    & git add -A
    if ($LASTEXITCODE -ne 0) { throw 'git add failed' }
    & git diff --cached --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host '[OK] Remote already matches local source.' -ForegroundColor Green
        exit 0
    }
    $missingEmail = (& git config user.email)
    $missingName = (& git config user.name)
    if (-not $missingEmail -or -not $missingName) { throw 'Configure git user.name and user.email first (git config --global user.name ...).' }
    & git commit -m 'sync: VoiceCompanion V1.3 full project with Xiaoya portrait and voice'
    if ($LASTEXITCODE -ne 0) { throw 'git commit failed' }
    & git push origin HEAD:main
    if ($LASTEXITCODE -ne 0) { throw 'git push failed; do NOT force-push. Pull and resolve conflicts safely, then retry.' }
    Write-Host '[OK] V1.3 pushed to https://github.com/mjw3177109/xunigirl' -ForegroundColor Green
} finally {
    Set-Location $Root
    if (Test-Path $Temp) { Remove-Item -LiteralPath $Temp -Recurse -Force -ErrorAction SilentlyContinue }
}
