param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
    $pythonPath = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    $workspacePath = Split-Path -Parent (Split-Path -Parent $projectRoot)
    $packagePath = Join-Path $workspacePath 'work\packages'
    $pdfPackagePath = Join-Path $workspacePath 'work\pdfpackages'
    if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf) -or -not (Test-Path -LiteralPath (Join-Path $packagePath 'streamlit\__init__.py'))) {
        throw 'No usable Python environment found. Install Python 3.12 and follow README.md.'
    }
    $env:PYTHONPATH = $pdfPackagePath + ';' + $packagePath
    $modelCachePath = Join-Path $workspacePath 'work\hf-cache'
    if (Test-Path -LiteralPath $modelCachePath) { $env:HF_HOME = $modelCachePath }
}
$env:PYTHONUTF8 = '1'
& $pythonPath -c "import sys, streamlit, fitz, dotenv; print('Python:', sys.version.split()[0]); print('App dependencies: OK')"
if ($LASTEXITCODE -ne 0) { throw 'Dependencies are missing. See README.md.' }
if ($CheckOnly) { exit 0 }
Write-Host ''
# Select a free loopback port rather than advertising an occupied default port.
$chatbotPort = $null
foreach ($candidatePort in 8501..8520) {
    $probe = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $candidatePort)
    try {
        $probe.Start()
        $chatbotPort = $candidatePort
        break
    } catch [System.Net.Sockets.SocketException] {
        continue
    } finally {
        $probe.Stop()
    }
}
if ($null -eq $chatbotPort) { throw 'Ports 8501-8520 are occupied. Close previous chatbot windows and retry.' }
$chatbotUrl = "http://127.0.0.1:$chatbotPort"
Write-Host "Open your browser: $chatbotUrl" -ForegroundColor Green
Write-Host 'Keep this window open while using the chatbot. Press Ctrl+C to stop.'
# Open only after the actual Streamlit health endpoint becomes ready.
$browserJob = Start-Job -ArgumentList $chatbotUrl -ScriptBlock {
    param($address)
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        try {
            $response = Invoke-WebRequest -Uri ($address + '/_stcore/health') -UseBasicParsing -TimeoutSec 1
            if ($response.StatusCode -eq 200) { Start-Process $address; return }
        } catch { }
        Start-Sleep -Seconds 1
    }
}
try {
    & $pythonPath -m streamlit run (Join-Path $projectRoot 'app.py') --global.developmentMode false --server.address 127.0.0.1 --server.port $chatbotPort --server.headless true
} finally {
    Stop-Job -Job $browserJob -ErrorAction SilentlyContinue
    Remove-Job -Job $browserJob -Force -ErrorAction SilentlyContinue
}
exit $LASTEXITCODE
