$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$manifestPath = Join-Path $projectRoot '.run\software-esquadrias-processes.json'
if (-not (Test-Path -LiteralPath $manifestPath)) {
    Write-Host 'Nenhum processo iniciado pelo launcher foi registrado.'
    exit 0
}
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ($manifest.root -ne $projectRoot) { Write-Error 'Registro de processos pertence a outro projeto.'; exit 1 }
foreach ($name in @('web','api')) {
    $record = $manifest.$name
    if (-not $record) { continue }
    $process = Get-CimInstance Win32_Process -Filter "ProcessId = $($record.pid)" -ErrorAction SilentlyContinue
    if (-not $process) { continue }
    $started = ([datetime]$process.CreationDate).ToUniversalTime()
    $expected = [datetime]::Parse($record.started_utc).ToUniversalTime()
    $matchesTime = [math]::Abs(($started - $expected).TotalSeconds) -lt 3
    $matchesCommand = if ($name -eq 'api') { $process.CommandLine -like '*api.app.main:app*' } else { $process.CommandLine -like '*vite*' -and $process.CommandLine -like '*--strictPort*' }
    if (-not $matchesTime -or -not $matchesCommand) {
        Write-Warning "PID $($record.pid) não corresponde ao $name iniciado; preservado."
        continue
    }
    & taskkill.exe /PID $record.pid /T /F | Out-Host
    if ($LASTEXITCODE -ne 0) { Write-Warning "Não foi possível encerrar $name (PID $($record.pid))." }
}
Remove-Item -LiteralPath $manifestPath -Force
Write-Host 'Processos registrados pelo launcher foram encerrados.'
