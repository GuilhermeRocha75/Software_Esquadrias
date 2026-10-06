param(
    [Parameter(Mandatory = $true)][string]$WorkbookPath,
    [Parameter(Mandatory = $true)][int[]]$OrcsRows
)
# Read-only Excel oracle. Customer/name/location fields are never copied or printed.
$ErrorActionPreference = 'Stop'
$expectedHash = '96514D7818BCBBC1DB86F94F86D8ED0239675E9F8D3A6B64DF651F30FD90C160'
if ((Get-FileHash -LiteralPath $WorkbookPath -Algorithm SHA256).Hash -ne $expectedHash) {
    throw 'Workbook is not the official parity source.'
}
$excel = $null
$book = $null
$sheet = $null
$orcs = $null
$stage = 'create Excel'

# Excel may temporarily reject COM calls while opening or recalculating this
# large legacy workbook. Retry only the two documented "server busy" HRESULTs;
# all other failures remain immediate and visible.
function Test-RetryableExcelComError($exception) {
    while ($exception) {
        if ($exception.HResult -in @(-2147418111, -2147417846)) {
            return $true # RPC_E_CALL_REJECTED / RPC_E_SERVERCALL_RETRYLATER
        }
        $exception = $exception.InnerException
    }
    return $false
}

function Invoke-ExcelComRetry([scriptblock]$Action, [int]$Attempts = 120) {
    for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
        try {
            & $Action | Out-Null
            return
        } catch {
            if (-not (Test-RetryableExcelComError $_.Exception) -or $attempt -eq $Attempts) {
                throw
            }
            Start-Sleep -Milliseconds 500
        }
    }
}

function Get-Cell($ws, [string]$address) {
    for ($attempt = 1; $attempt -le 120; $attempt++) {
        $cell = $null
        try {
            $cell = $ws.Range($address)
            return $cell.Value2
        } catch {
            if (-not (Test-RetryableExcelComError $_.Exception) -or $attempt -eq 120) {
                throw
            }
            Start-Sleep -Milliseconds 500
        } finally {
            if ($cell) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell) }
        }
    }
}
function Set-Cell($ws, [string]$address, $value) {
    for ($attempt = 1; $attempt -le 120; $attempt++) {
        $cell = $null
        try {
            $cell = $ws.Range($address)
            if ($null -eq $value -or $value -is [DBNull]) {
                $cell.ClearContents()
            } else {
                $cell.Value2 = $value
            }
            return
        } catch {
            if (-not (Test-RetryableExcelComError $_.Exception) -or $attempt -eq 120) {
                throw
            }
            Start-Sleep -Milliseconds 500
        } finally {
            if ($cell) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell) }
        }
    }
}
try {
    $excel = New-Object -ComObject Excel.Application
    $stage = 'configure Excel'
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    $excel.AutomationSecurity = 3
    # The official workbook has large volatile/legacy sheets. Disable global
    # automatic recalculation before opening; recalculate GR explicitly below.
    $blank = $excel.Workbooks.Add()
    $excel.Calculation = -4135 # xlCalculationManual
    $blank.Close($false)
    $stage = 'open workbook'
    $book = $excel.Workbooks.Open($WorkbookPath, 0, $true)
    Start-Sleep -Seconds 10
    $stage = 'get worksheets'
    for ($attempt = 1; $attempt -le 120; $attempt++) {
        try {
            $sheet = $book.Worksheets.Item('GR')
            break
        } catch {
            if (-not (Test-RetryableExcelComError $_.Exception) -or $attempt -eq 120) { throw }
            Start-Sleep -Milliseconds 500
        }
    }
    for ($attempt = 1; $attempt -le 120; $attempt++) {
        try {
            $orcs = $book.Worksheets.Item('ORCS')
            break
        } catch {
            if (-not (Test-RetryableExcelComError $_.Exception) -or $attempt -eq 120) { throw }
            Start-Sleep -Milliseconds 500
        }
    }
    $output = @()
    $columns = @('D','E','F','G','H','I','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','AA','AB','AC','AD','AE','AF','AG','AH','AI','AJ','AK')
    foreach ($row in $OrcsRows) {
        $stage = "copy ORCS row $row"
        if ((Get-Cell $orcs "X$row") -ne 'GR') { throw "ORCS row $row is not GR" }
        foreach ($col in $columns) {
            $stage = "copy ORCS row $row column $col"
            $value = Get-Cell $orcs "$col$row"
            Set-Cell $sheet "${col}2" $value
        }
        Set-Cell $sheet 'C2' 1
        $stage = "recalculate ORCS row $row"
        Invoke-ExcelComRetry { $sheet.Calculate() }
        $stage = "collect ORCS row $row"
        $cells = [ordered]@{}
        foreach ($address in @('D8','E8','G8','D9','E9','G9','B10','C10','D10','E10','G10','D11','E11','G11','D12','G12','D13','G13','D14','G14','D15','G15','D16','G16','D17','G17','D18','G18','D19','G19','D58','G58','D59','G59','D60','G60','D61','G61','D68','E68','G68','I68','G83','I83','I56','I65','I71','I74','I81','I103','I120','I122','AO2')) {
            $cells[$address] = Get-Cell $sheet $address
        }
        $bom = @()
        foreach ($bomRow in @(8..55 + 58..64 + 68..70 + 73 + 76..80 + 83..102 + 104..119)) {
            $qty = Get-Cell $sheet "G$bomRow"
            $numeric = 0.0
            if ([double]::TryParse([string]$qty, [Globalization.NumberStyles]::Float,
                    [Globalization.CultureInfo]::InvariantCulture, [ref]$numeric) -and $numeric -gt 0) {
                $bom += ,@($bomRow, (Get-Cell $sheet "C$bomRow"), (Get-Cell $sheet "D$bomRow"), (Get-Cell $sheet "E$bomRow"), $numeric, (Get-Cell $sheet "H$bomRow"), (Get-Cell $sheet "I$bomRow"))
            }
        }
        $output += [ordered]@{ orcs_row = $row; cells = $cells; bom = $bom }
    }
    $output | ConvertTo-Json -Depth 10
} catch {
    throw "GR Excel oracle failed at stage '$stage': $($_.Exception.Message)"
} finally {
    if ($book) { try { $book.Close($false) } catch { } }
    if ($excel) { try { $excel.Quit() } catch { } }
    foreach ($obj in @($orcs, $sheet, $book, $excel)) {
        if ($obj) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($obj) }
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
