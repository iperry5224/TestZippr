# SOPRA Assessment Script: VM-003 - Asset Discovery & Inventory
# Category: Vulnerability Management
# Run on target machine; outputs CSV row for SOPRA import
# Correlates to remediation script: VM_003.ps1

$ErrorActionPreference = "SilentlyContinue"
$STATUS = "Not Assessed"
$SEVERITY = ""
$EVIDENCE = "Check not run"
$NOTES = ""

$category = "Vulnerability Management"
$control_id = "VM-003"
$control_name = "Asset Discovery & Inventory"

# Discovery only - manual review required
try {
    $out = Invoke-Expression 'Install-WindowsFeature -Name NPAS; Enable-NetFirewallRule -DisplayGroup ''Network Discovery'''
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
