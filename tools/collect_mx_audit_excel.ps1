param(
    [Parameter(Mandatory = $true)][string]$WorkbookPath,
    [Parameter(Mandatory = $true)][string]$CasesPath
)
# Read-only Excel oracle. No macros, links, saving, customer fields or ORCS text output.
$ErrorActionPreference = 'Stop'
$expectedHash = '96514D7818BCBBC1DB86F94F86D8ED0239675E9F8D3A6B64DF651F30FD90C160'
if ((Get-FileHash -LiteralPath $WorkbookPath -Algorithm SHA256).Hash -ne $expectedHash) {
    throw 'Workbook is not the official parity source.'
}
$excel = $null
$book = $null
$sheet = $null
function Set-MxCell($Address, $Value) {
    $cell = $sheet.Range($Address)
    try {
        if ($Value -is [string]) { $cell.Value2 = [string]$Value }
        else { $cell.Value2 = [double]$Value }
    } finally { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell) }
}
function Get-MxCell($Address) {
    $cell = $sheet.Range($Address)
    try { return $cell.Value2 }
    finally { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell) }
}
try {
    $cases = (Get-Content -LiteralPath $CasesPath -Raw -Encoding UTF8 | ConvertFrom-Json).cases
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    $excel.AutomationSecurity = 3
    $book = $excel.Workbooks.Open($WorkbookPath, 0, $true)
    $sheet = $book.Worksheets.Item('MX')
    $output = @()
    foreach ($case in $cases) {
        $c = $case.input
        $range = $sheet.Range('A2:AK2')
        $range.ClearContents()
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($range)
        Set-MxCell 'C2' 1
        Set-MxCell 'D2' $c.width_mm
        Set-MxCell 'E2' $c.height_mm
        Set-MxCell 'F2' $c.quantity
        Set-MxCell 'G2' "$($c.leaf_count) FOLHAS"
        $system = if ($c.leaf_system -eq 'PRIME_WINDOW_42x63') { 'FOLHA DE JANELA 42X63MM - PRIME' } else { 'FOLHA DE JANELA 60X78MM - DESIGN' }
        Set-MxCell 'H2' $system
        Set-MxCell 'I2' $c.orientation
        Set-MxCell 'K2' $c.glass_description
        $screen = if ($c.screen_enabled) { 'COM TELA MOSQUITEIRA' } else { 'SEM TELA MOSQUITEIRA' }
        Set-MxCell 'O2' $screen
        Set-MxCell 'P2' $c.closure_mode
        if ($c.cremona_description) { Set-MxCell 'Q2' $c.cremona_description }
        $reinforcement = if ($c.structural_reinforcement.material_code -eq 'ALUM10238') { 'REFORÇO 102X50MM' } elseif ($c.structural_reinforcement.material_code -eq 'ALUM15338') { 'REFORÇO 138X50MM' } else { 'SEM REFORÇO EXTRUTURAL' }
        Set-MxCell 'R2' $reinforcement
        Set-MxCell 'S2' 'GUARNIÇÃO DE 70MM'
        Set-MxCell 'T2' 'BARRA CHATA DE 30MM'
        Set-MxCell 'U2' $c.module_mode
        foreach ($column in @('V','W','X','Y','Z','AA','AB','AC','AD','AE','AF','AG','AH','AI','AJ','AK')) { Set-MxCell "${column}2" 0 }
        if ($c.bottom_fixed_panel) {
            Set-MxCell 'AA2' $c.bottom_fixed_panel.height_mm
            Set-MxCell 'AH2' $c.bottom_fixed_panel.vertical_transoms
            Set-MxCell 'AI2' $c.bottom_fixed_panel.horizontal_transoms
        }
        if ($c.top_fixed_panel) {
            Set-MxCell 'AB2' $c.top_fixed_panel.height_mm
            Set-MxCell 'AJ2' $c.top_fixed_panel.vertical_transoms
            Set-MxCell 'AK2' $c.top_fixed_panel.horizontal_transoms
        }
        $excel.CalculateFullRebuild()
        $cells = [ordered]@{}
        foreach ($address in @('D10','D11','D12','D13','D14','G14','D16','D17','G16','D18','D19','G18','D24','D25','D30','D31','D59','E59','G59','D60','E60','G60','D61','E61','G61','G67','G68','G69','I67','I68','I69','G72','I72','I40','I56','I62','I65','I70','I74','I80','I82','I85','B32','C32','D32','G32','H32','I32','U3','I48','I49','I52','I53')) {
            $cells[$address] = Get-MxCell $address
        }
        $bom = @()
        foreach ($row in @(8..38 + 42..55 + 59..61 + 64 + 67..69 + 72..73 + 76..81)) {
            $q = Get-MxCell "G$row"
            $number = 0.0
            if ([double]::TryParse([string]$q, [Globalization.NumberStyles]::Float,
                                  [Globalization.CultureInfo]::InvariantCulture,
                                  [ref]$number) -and $number -gt 0) {
                $bom += ,@($row, (Get-MxCell "C$row"), (Get-MxCell "D$row"), (Get-MxCell "E$row"), $number, (Get-MxCell "H$row"), (Get-MxCell "I$row"))
            }
        }
        $output += [ordered]@{ id = $case.id; cells = $cells; bom = $bom }
    }
    $output | ConvertTo-Json -Depth 12 -Compress
} catch {
    throw "MX oracle failed at $($case.id), line $($_.InvocationInfo.ScriptLineNumber): $($_.Exception.Message)"
} finally {
    if ($book) { $book.Close($false) }
    if ($excel) { $excel.Quit() }
    foreach ($obj in @($sheet, $book, $excel)) {
        if ($obj) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($obj) }
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
