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
function Get-Cell($ws, [string]$address) {
    $cell = $ws.Range($address)
    try { return $cell.Value2 }
    finally { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell) }
}
function Set-Cell($ws, [string]$address, $value) {
    $cell = $ws.Range($address)
    try { $cell.Value2 = $value }
    finally { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell) }
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
    $stage = 'get worksheets'
    $sheet = $book.Worksheets.Item('GR')
    $orcs = $book.Worksheets.Item('ORCS')
    $output = @()
    $columns = @('D','E','F','G','H','I','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','AA','AB','AC','AD','AE','AF','AG','AH','AI','AJ','AK')
    foreach ($row in $OrcsRows) {
        $stage = "copy ORCS row $row"
        if ((Get-Cell $orcs "X$row") -ne 'GR') { throw "ORCS row $row is not GR" }
        foreach ($col in $columns) {
            $value = Get-Cell $orcs "$col$row"
            Set-Cell $sheet "${col}2" $value
        }
        Set-Cell $sheet 'C2' 1
        $stage = "recalculate ORCS row $row"
        $sheet.Calculate()
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
