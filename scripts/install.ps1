param([switch]$TextOnly)
$ErrorActionPreference='Stop'
$Root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $Root
function Say($s){Write-Host $s -ForegroundColor Cyan}
function Run($program,[string[]]$argv) {
    & $program @argv
    if ($LASTEXITCODE -ne 0) { throw "Command failed: $program $($argv -join ' ') (exit $LASTEXITCODE)" }
}
Say '[1/6] 检查 Python 3.11 和安装虚拟环境'
$py = Get-Command py -ErrorAction SilentlyContinue
if ($py) {
    $ver = & py -3.11 --version 2>&1
    if ($LASTEXITCODE -ne 0){throw '请安装 Python 3.11 64-bit（不要装 3.14 作为默认）。下载 https://www.python.org/downloads/'}
    if (!(Test-Path '.venv\Scripts\python.exe')){Run -program 'py' -argv @('-3.11','-m','venv','.venv')}
} else {
    $ver=& python --version 2>&1
    if ($ver -notmatch '^Python 3\.11\.') {throw '请安装 Python 3.11 64-bit 并添加到 PATH'}
    if (!(Test-Path '.venv\Scripts\python.exe')){Run -program 'python' -argv @('-m','venv','.venv')}
}
$Exe=Join-Path $Root '.venv\Scripts\python.exe'
Say '[2/6] 安装基础独立服务依赖'
Run -program $Exe -argv @('-m','pip','install','--upgrade','pip')
Run -program $Exe -argv @('-m','pip','install','-r','requirements-core.txt')
if (!(Test-Path '.env')){
    Copy-Item '.env.example' '.env'
    Write-Host '[TODO] 请在 .env 填写 DEEPSEEK_API_KEY' -ForegroundColor Yellow
}
if ($TextOnly){
    Say '[DONE] 文字版已配置。编辑 .env 后直接运行 START.cmd。'
    exit 0
}
Say '[3/6] 获取已固定版本的原项目源码（仅依赖原项目 Python 语音代码，不安装 DSH）'
$Commit='480bbabada7335735cad591eaa55f32fe54a4214'
if (!(Test-Path 'upstream\bridge\voice_bridge.py')){
    $cache=Join-Path $Root 'data\upstream-source.zip'
    $url='https://codeload.github.com/beiyege-01/dsh-voice-ai-girlfriend/zip/'+$Commit
    New-Item -ItemType Directory -Force -Path 'data' | Out-Null
    Invoke-WebRequest -Uri $url -OutFile $cache -UseBasicParsing
    $tmp=Join-Path $Root 'data\source_unzip'
    if(Test-Path $tmp){Remove-Item $tmp -Recurse -Force}
    Expand-Archive -Path $cache -DestinationPath $tmp -Force
    $src=Get-ChildItem $tmp -Directory | Select-Object -First 1
    if(!$src -or !(Test-Path (Join-Path $src.FullName 'bridge\voice_bridge.py'))){throw '源码压缩包未包含 bridge/voice_bridge.py'}
    Move-Item $src.FullName (Join-Path $Root 'upstream')
    Remove-Item $tmp -Force -Recurse
    Remove-Item $cache -Force
}
Say '[4/6] 修正原作者电脑的硬编码路径并关闭默认数字人'
Run -program $Exe -argv @('tools\configure_upstream.py')
Say '[5/6] 安装本地语音运行依赖（体积较大）'
Run -program $Exe -argv @('-m','pip','install','-r','upstream\bridge\requirements.txt')
# Installed here explicitly because upstream imports it but does not pin it.
Run -program $Exe -argv @('-m','pip','install','httpx','gradio_client')
Say '[6/6] 下载 STT、TTS、VAD 模型；模型占用数 GB'
Run -program $Exe -argv @('tools\download_models.py')
Say '[VOICE] 为小雅生成自然甜美的中文参考声音（首次需要下载可选的 0.6B CustomVoice 模型）'
try {
    Run -program $Exe -argv @('-m','pip','install','qwen-tts')
    Run -program $Exe -argv @('tools\generate_xiaoya_voice.py','--auto')
} catch {
    Write-Host ('[WARN] 自然音色生成暂未成功，保留已内置的合成试听样音。稍后可运行 GENERATE_XIAOYA_VOICE.cmd：' + $_.Exception.Message) -ForegroundColor Yellow
}
Run -program $Exe -argv @('tools\configure_upstream.py')
Say '[DONE] 安装流程结束。'
Write-Host '下一步：编辑 .env 配置 DeepSeek Key；小雅音色已经预置，启动后可用 SMOKE_TTS.cmd 检查；未完成自然音色生成可运行 GENERATE_XIAOYA_VOICE.cmd。' -ForegroundColor Yellow
