param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$webRoot = Join-Path $projectRoot 'web'
$runRoot = Join-Path $projectRoot '.run'
$manifestPath = Join-Path $runRoot 'software-esquadrias-processes.json'
$apiPort = 8000
$webPort = 5173
$apiUrl = "http://127.0.0.1:$apiPort"
$webUrl = "http://127.0.0.1:$webPort"
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
$vitePath = Join-Path $webRoot 'node_modules\vite\bin\vite.js'

function Test-ApiReady {
    try {
        $reply = Invoke-RestMethod -Uri "$apiUrl/health" -TimeoutSec 2
        return $reply.status -eq 'ok' -and $reply.engines -contains 'MX_ENGINE_0.3.0'
    } catch { return $false }
}
function Test-WebReady {
    try {
        $reply = Invoke-WebRequest -Uri $webUrl -TimeoutSec 2 -UseBasicParsing
        return $reply.StatusCode -eq 200 -and $reply.Content.Contains('<title>Software Esquadrias</title>')
    } catch { return $false }
}
function Test-PortBusy([int]$port) {
    $client = New-Object Net.Sockets.TcpClient
    try {
        $attempt = $client.BeginConnect('127.0.0.1', $port, $null, $null)
        return $attempt.AsyncWaitHandle.WaitOne(300)
    } catch { return $false }
    finally { $client.Close() }
}
function Wait-Ready([scriptblock]$probe, [Diagnostics.Process]$process, [string]$name) {
    $deadline = (Get-Date).AddSeconds(60)
    do {
        if (& $probe) { return }
        if ($process.HasExited) { throw "$name encerrou antes de ficar pronto (exit code $($process.ExitCode)). Consulte .run\$name.err.log." }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)
    throw "$name não respondeu em 60 segundos. Consulte os logs em .run."
}

try {
    if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) { throw "Python virtual não encontrado: $pythonPath. Crie .venv e instale api\requirements.txt." }
    $node = Get-Command node.exe -ErrorAction SilentlyContinue
    $npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if (-not $node -or -not $npm) { throw 'Node.js e npm.cmd devem estar instalados e disponíveis no PATH.' }
    & $pythonPath -c 'import uvicorn, fastapi'
    if ($LASTEXITCODE -ne 0) { throw 'Dependências Python ausentes. Execute .venv\Scripts\python.exe -m pip install -r api\requirements.txt.' }
    if (-not (Test-Path -LiteralPath $vitePath -PathType Leaf)) {
        Write-Host 'Instalando dependências Web pelo lockfile (npm ci)...'
        & $npm.Source ci --prefix $webRoot
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $vitePath -PathType Leaf)) { throw 'npm ci falhou; veja a mensagem acima.' }
    }
    New-Item -ItemType Directory -Path $runRoot -Force | Out-Null
    $manifest = @{ root = $projectRoot; api = $null; web = $null }
    if (Test-Path -LiteralPath $manifestPath) {
        $prior = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
        if ($prior.root -eq $projectRoot) { $manifest.api = $prior.api; $manifest.web = $prior.web }
    }

    if (Test-ApiReady) { Write-Host "API já está pronta em $apiUrl." }
    else {
        if (Test-PortBusy $apiPort) { throw "Porta $apiPort ocupada por outro serviço; a API não será duplicada." }
        Write-Host 'Iniciando API local...'
        $apiProcess = Start-Process -FilePath $pythonPath -ArgumentList @('-m','uvicorn','api.app.main:app','--reload','--host','127.0.0.1','--port',"$apiPort") -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runRoot 'api.out.log') -RedirectStandardError (Join-Path $runRoot 'api.err.log') -PassThru
        $manifest.api = @{ pid = $apiProcess.Id; started_utc = $apiProcess.StartTime.ToUniversalTime().ToString('o') }
        $manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
        Wait-Ready { Test-ApiReady } $apiProcess 'api'
    }

    if (Test-WebReady) { Write-Host "Web já está pronta em $webUrl." }
    else {
        if (Test-PortBusy $webPort) { throw "Porta $webPort ocupada por outro serviço; a Web não será duplicada." }
        Write-Host 'Iniciando interface Web local...'
        $previousApiUrl = $env:VITE_API_URL
        $env:VITE_API_URL = $apiUrl
        try {
            $webProcess = Start-Process -FilePath $node.Source -ArgumentList @($vitePath,'--host','127.0.0.1','--port',"$webPort",'--strictPort') -WorkingDirectory $webRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runRoot 'web.out.log') -RedirectStandardError (Join-Path $runRoot 'web.err.log') -PassThru
        } finally { $env:VITE_API_URL = $previousApiUrl }
        $manifest.web = @{ pid = $webProcess.Id; started_utc = $webProcess.StartTime.ToUniversalTime().ToString('o') }
        $manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
        Wait-Ready { Test-WebReady } $webProcess 'web'
    }

    Write-Host "Software Esquadrias pronto: $webUrl"
    if (-not $NoBrowser) { Start-Process $webUrl }
    exit 0
} catch {
    Write-Error $_.Exception.Message
    exit 1
}
