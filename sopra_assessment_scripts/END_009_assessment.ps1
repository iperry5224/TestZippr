# SOPRA Assessment Script: END-009 - Secure Boot Configuration
# Category: Endpoint Security
# Run on target machine; outputs CSV row for SOPRA import
# Correlates to remediation script: END_009.ps1

$ErrorActionPreference = "SilentlyContinue"
$STATUS = "Not Assessed"
$SEVERITY = ""
$EVIDENCE = "Check not run"
$NOTES = ""

$category = "Endpoint Security"
$control_id = "END-009"
$control_name = "Secure Boot Configuration"

# Discovery only - manual review required
try {
    $out = Invoke-Expression 'Confirm-SecureBootUEFI'
    $STATUS = "Manual Review"
    $SEVERITY = ""
    $EVIDENCE = "Discovery completed - review output above and update CSV manually"
} catch {
    $STATUS = "Failed"
    $SEVERITY = "Medium"
    $EVIDENCE = "Discovery failed: $($_.Exception.Message)"
}

$date = Get-Date -Format "yyyy-MM-dd"
$assessedBy = $env:USERNAME + "@" + $env:COMPUTERNAME
function ToCsv($v) { $s = ($v -replace '"','""'); if ($s -match '[,"\n]') { return "`"$s`"" } else { return $s } }
$line = (ToCsv $category) + "," + (ToCsv $control_id) + "," + (ToCsv $control_name) + "," + (ToCsv $STATUS) + "," + (ToCsv $SEVERITY) + "," + (ToCsv $EVIDENCE) + "," + (ToCsv $NOTES) + "," + (ToCsv $assessedBy) + "," + $date
$outFile = Join-Path $PSScriptRoot "sopra_assessment_results.csv"
if (-not (Test-Path $outFile)) { "category,control_id,control_name,status,severity,evidence,notes,assessed_by,assessment_date" | Out-File $outFile -Encoding UTF8 }
Add-Content -Path $outFile -Value $line -Encoding UTF8
Write-Host "[$control_id] $STATUS - $EVIDENCE"
