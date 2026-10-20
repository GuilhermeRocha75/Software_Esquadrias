$ErrorActionPreference = 'Stop'
$launcherPath = Join-Path $PSScriptRoot 'iniciar_software.ps1'
$parseTokens = $null
$parseErrors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile($launcherPath, [ref]$parseTokens, [ref]$parseErrors)
if ($parseErrors.Count -gt 0) { throw "Launcher syntax errors: $parseErrors" }
$portFunction = $ast.Find({
    param($node)
    $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Test-PortBusy'
}, $true)
if (-not $portFunction) { throw 'Test-PortBusy was not found.' }
# Load only the probe, never start the full launcher or modify user processes.
. ([scriptblock]::Create($portFunction.Extent.Text))

$listener = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, 0)
try {
    $listener.Start()
    $port = $listener.LocalEndpoint.Port
    if (-not (Test-PortBusy $port)) { throw "Listening port $port was reported free." }
    $listener.Stop()
    if (Test-PortBusy $port) { throw "Closed port $port was reported busy." }
    Write-Host 'PASS: listening port is busy; refused connection is free; launcher syntax is valid.'
} finally { $listener.Stop() }
