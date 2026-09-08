param(
    [Parameter(Mandatory = $true)]
    [string]$WorkbookPath,
    [string]$ScenarioId = '',
    [switch]$IncludeBom,
    [switch]$SummaryOnly
)

$ErrorActionPreference = 'Stop'
$excel = $null
$workbook = $null
$sheet = $null
$currentScenario = 'startup'
$currentAddress = ''

function Set-CellValue {
    param($Worksheet, [string]$Address, $Value)
    $script:currentAddress = $Address
    $cell = $Worksheet.Range($Address)
    if ($Value -is [byte] -or $Value -is [int16] -or $Value -is [int32] -or $Value -is [int64] -or $Value -is [single] -or $Value -is [double] -or $Value -is [decimal]) {
        $cell.Value2 = [double]$Value
    }
    else {
        $cell.Value2 = [string]$Value
    }
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell)
}

function Get-CellValue {
    param($Worksheet, [string]$Address)
    $value = $Worksheet.Range($Address).Value2
    if ($null -eq $value) { return $null }
    return $value
}

try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    $excel.AutomationSecurity = 3
    $workbook = $excel.Workbooks.Open($WorkbookPath, 0, $true)
    $sheet = $workbook.Worksheets.Item('CR')

    $scenarios = @(
        @{ id = 'T26_PRIME_H1'; width = 2000; height = 2000; leaves = 2; system = 'FOLHA DE JANELA 42X66MM - PRIME'; AF = 1 },
        @{ id = 'T26_DESIGN_H2'; width = 2400; height = 2200; leaves = 4; system = 'FOLHA DE PORTA 60X111MM - DESIGN'; AF = 2 },
        @{ id = 'T27_PRIME_V1'; width = 2000; height = 2000; leaves = 2; system = 'FOLHA DE PORTA 42X88MM - PRIME'; AG = 1 },
        @{ id = 'T27_DESIGN_V2'; width = 2400; height = 2200; leaves = 4; system = 'FOLHA DE PORTA 60X111MM - DESIGN'; AG = 2 },
        @{ id = 'T28_BOTTOM'; width = 2200; height = 2400; leaves = 2; system = 'FOLHA DE JANELA 42X66MM - PRIME'; AA = 400 },
        @{ id = 'T28B_BOTTOM_GRID'; width = 2200; height = 2600; leaves = 2; system = 'FOLHA DE PORTA 60X111MM - DESIGN'; AA = 600; AH = 1; AI = 1 },
        @{ id = 'T29_TOP'; width = 2200; height = 2400; leaves = 2; system = 'FOLHA DE JANELA 42X66MM - PRIME'; AB = 400 },
        @{ id = 'T29B_TOP_GRID'; width = 2200; height = 2600; leaves = 2; system = 'FOLHA DE PORTA 60X111MM - DESIGN'; AB = 600; AJ = 1; AK = 1 },
        @{ id = 'T34_NO_STRUCTURAL'; width = 2400; height = 2800; leaves = 4; system = 'FOLHA DE JANELA 42X66MM - PRIME'; AA = 400; AB = 450 },
        @{ id = 'T34_WITH_STRUCTURAL'; width = 2400; height = 2800; leaves = 4; system = 'FOLHA DE JANELA 42X66MM - PRIME'; AA = 400; AB = 450; reinforcement = 'PERFIL EXTRUTURAL ALUMINIO 102X50MM' },
        @{ id = 'COMBINED_DESIGN_QTY2'; width = 3000; height = 3000; quantity = 2; leaves = 4; system = 'FOLHA DE PORTA 60X111MM - DESIGN'; AF = 1; AG = 1; AA = 450; AB = 500; AH = 1; AI = 1; AJ = 2; AK = 1 },
        @{ id = 'MANUAL_DIMENSIONS'; width = 2400; height = 2200; leaves = 2; system = 'FOLHA DE JANELA 42X66MM - PRIME'; AF = 2; AG = 2; W = 650; X = 700; Y = 600; Z = 650; AC = 650 }
    )

    $addresses = @(
        'D8','E8','G8','D9','E9','G9','D10','E10','G10','D11','E11','G11',
        'D14','G14','D15','G15','D16','G16','D17','G17','D18','G18','D19','G19',
        'D26','G26','D27','G27','D28','G28','D29','G29',
        'D37','E37','G37','D38','E38','G38','D39','G39','D40','G40','D41','G41','D42','G42',
        'D43','E43','G43','D44','E44','G44','D45','G45','D46','G46','D47','G47','D48','G48',
        'B53','C53','D53','G53','D65','G65','D66','G66','D67','G67','D68','G68',
        'D69','G69','D70','G70','D71','G71','D72','G72','D73','G73','D74','G74',
        'D75','G75','D76','G76','D77','G77','D78','G78','D79','G79','D80','G80',
        'D84','E84','G84','D85','E85','G85','D86','E86','G86','D87','E87','G87',
        'D88','E88','G88','D89','E89','G89','D90','E90','G90','D91','E91','G91',
        'D92','E92','G92','D93','E93','G93','D94','E94','G94',
        'G108','G109','G110','G116','G117','G118','G119','G145','I63','I81','I95','I106','I114','I137','I147','I149'
    )
    if ($SummaryOnly) {
        $addresses = @(
            'D9','D10','D11','D14','G14','D17','G17','D26','G26','D29','G29',
            'D37','D38','D39','G39','D40','G40','D41','D42','G41','D43','D44',
            'D45','G45','D46','G46','D47','D48','G47','D53','G53','D84','E84',
            'G84','D93','E93','G93','D94','E94','G94','G108','G117','G118','G145','I149'
        )
    }

    $results = @()
    foreach ($scenario in $scenarios) {
        if ($ScenarioId -and $scenario.id -ne $ScenarioId) { continue }
        $currentScenario = $scenario.id
        $sheet.Range('A2:AK2').ClearContents()
        Set-CellValue $sheet 'C2' 1
        Set-CellValue $sheet 'D2' $scenario.width
        Set-CellValue $sheet 'E2' $scenario.height
        Set-CellValue $sheet 'F2' $(if ($scenario.quantity) { $scenario.quantity } else { 1 })
        Set-CellValue $sheet 'G2' "$($scenario.leaves) FOLHAS"
        Set-CellValue $sheet 'H2' $scenario.system
        Set-CellValue $sheet 'I2' 'JANELA'
        Set-CellValue $sheet 'K2' '04mm FLOAT INCOLOR'
        Set-CellValue $sheet 'L2' 'SEM PERSIANA'
        Set-CellValue $sheet 'O2' 'SEM TELA MOSQUITEIRA'
        $cedilla = [char]0x00C7
        Set-CellValue $sheet 'P2' "MA${cedilla}ANETA COM CREMONA + FECHO OCULTO"
        Set-CellValue $sheet 'Q2' 'CREMONA 1 PONTO'
        Set-CellValue $sheet 'R2' 'ROLDANA 30KG'
        Set-CellValue $sheet 'S2' 'BARRA CHATA DE 30MM'
        Set-CellValue $sheet 'T2' 'BARRA CHATA DE 30MM'
        Set-CellValue $sheet 'U2' $(if ($scenario.reinforcement) { $scenario.reinforcement } else { "SEM REFOR${cedilla}O EXTRUTURAL" })

        foreach ($column in @('V','W','X','Y','Z','AA','AB','AC','AD','AE','AF','AG','AH','AI','AJ','AK')) {
            $value = if ($scenario.ContainsKey($column)) { $scenario[$column] } else { 0 }
            Set-CellValue $sheet "${column}2" $value
        }

        $excel.CalculateFullRebuild()
        $cells = [ordered]@{}
        foreach ($address in $addresses) {
            $currentAddress = $address
            $cells[$address] = Get-CellValue $sheet $address
        }

        $bom = @()
        if ($IncludeBom) {
            foreach ($row in @(8..60 + 65..80 + 84..94 + 97..105 + 108..113 + 116..119 + 139..146)) {
                $currentAddress = "row $row"
                $quantity = Get-CellValue $sheet "G$row"
                if ($null -ne $quantity -and $quantity -is [double] -and $quantity -gt 0) {
                    $bom += [ordered]@{
                        row = $row
                        description = Get-CellValue $sheet "B$row"
                        code = Get-CellValue $sheet "C$row"
                        length_or_width_mm = Get-CellValue $sheet "D$row"
                        cut_or_height_mm = Get-CellValue $sheet "E$row"
                        quantity_per_unit = $quantity
                        unit_price = Get-CellValue $sheet "H$row"
                        cost_per_unit = Get-CellValue $sheet "I$row"
                    }
                }
            }
        }

        $results += [ordered]@{
            id = $scenario.id
            inputs = $scenario
            cells = $cells
            bom = $bom
        }
    }

    $results | ConvertTo-Json -Depth 8
}
catch {
    Write-Error "Excel collection failed at scenario '$currentScenario', address '$currentAddress', line $($_.InvocationInfo.ScriptLineNumber): $($_.Exception.Message)"
    throw
}
finally {
    if ($null -ne $workbook) { $workbook.Close($false) }
    if ($null -ne $excel) { $excel.Quit() }
    if ($null -ne $sheet) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($sheet) }
    if ($null -ne $workbook) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($workbook) }
    if ($null -ne $excel) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel) }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
