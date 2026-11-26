param([Parameter(Mandatory=$true)][string]$WorkbookPath)
$ErrorActionPreference = 'Stop'
$taskWorkbookPath = (Resolve-Path -LiteralPath $WorkbookPath).Path
$taskVerificationPath = Join-Path (Split-Path -Parent $taskWorkbookPath) 'native_excel_verification.json'
$taskExcel = $null
$taskBook = $null
try {
    $taskExcel = New-Object -ComObject Excel.Application
    $taskExcel.Visible = $false
    $taskExcel.DisplayAlerts = $false
    $taskBook = $taskExcel.Workbooks.Open($taskWorkbookPath, 0, $false)
    $taskExcel.CalculateFullRebuild()
    $taskForecast = $taskBook.Worksheets.Item('Forecast')
    $taskAssumptions = $taskBook.Worksheets.Item('Assumptions')
    $taskActualRevenue = [double]$taskBook.Worksheets.Item('Actuals').Range('D6').Value2
    $taskBaseRevenue = [double]$taskForecast.Range('E8').Value2
    if ([Math]::Abs($taskBaseRevenue - $taskActualRevenue * 1.1) -gt 0.01) { throw 'Base forecast mismatch in Excel' }
    $taskAssumptions.Range('D4').Value2 = 2
    $taskExcel.CalculateFullRebuild()
    $taskDownsideRevenue = [double]$taskForecast.Range('E8').Value2
    if ([Math]::Abs($taskDownsideRevenue - $taskActualRevenue * 1.04) -gt 0.01) { throw 'Downside switch did not recalculate' }
    $taskAssumptions.Range('D4').Value2 = 1
    $taskAssumptions.Range('G9').Value2 = 0.2
    $taskExcel.CalculateFullRebuild()
    $taskLaterPeriodRevenue = [double]$taskForecast.Range('G8').Value2
    if ([Math]::Abs($taskLaterPeriodRevenue - [double]$taskForecast.Range('F8').Value2 * 1.2) -gt 0.01) { throw 'Later-period driver did not recalculate' }
    $taskAssumptions.Range('G9').Value2 = 0.1
    $taskPricing = $taskBook.Worksheets.Item('AI Pricing')
    $taskOriginalAccounts = [double]$taskPricing.Range('D7').Value2
    $taskPricing.Range('D7').Value2 = 0
    $taskExcel.CalculateFullRebuild()
    if ($taskPricing.Range('D29').Value2 -ne 'n.a.') { throw 'Zero-adopter boundary did not return n.a.' }
    $taskPricing.Range('D7').Value2 = $taskOriginalAccounts
    $taskExcel.CalculateFullRebuild()
    $taskBook.Save()
    $taskResult = @{status='passed'; engine='Microsoft Excel COM'; version=$taskExcel.Version; checked_at=[DateTime]::UtcNow.ToString('o'); base_revenue=$taskBaseRevenue; downside_revenue=$taskDownsideRevenue; later_period_revenue=$taskLaterPeriodRevenue; checks=@('full_recalculation','case_selector','later_period_driver','zero_adopter_boundary','inputs_restored_and_saved')}
    $taskResult | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $taskVerificationPath -Encoding utf8
    $taskResult | ConvertTo-Json -Depth 5
} catch {
    @{status='unavailable_or_failed'; engine='Microsoft Excel COM'; error=$_.Exception.Message} | ConvertTo-Json | Set-Content -LiteralPath $taskVerificationPath -Encoding utf8
    throw
} finally {
    if ($null -ne $taskBook) { $taskBook.Close($false) }
    if ($null -ne $taskExcel) { $taskExcel.Quit(); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($taskExcel) }
}
