# SOPRA Assessment Script: AD-004 - Password Policy Enforcement
# Category: Active Directory Security
# Run on target machine; outputs CSV row for SOPRA import
# Correlates to remediation script: AD_004.ps1

$ErrorActionPreference = "SilentlyContinue"
$STATUS = "Not Assessed"
$SEVERITY = ""
$EVIDENCE = "Check not run"
$NOTES = ""

$category = "Active Directory Security"
$control_id = "AD-004"
$control_name = "Password Policy Enforcement"

$pol = Get-ADDefaultDomainPasswordPolicy -ErrorAction SilentlyContinue
if (-not $pol) { $STATUS='Failed'; $SEVERITY='High'; $EVIDENCE="Could not read domain password policy" }
elseif ($pol.MinPasswordLength -lt 14) { $STATUS='Failed'; $SEVERITY='High'; $EVIDENCE="Min password length $($pol.MinPasswordLength) (recommend 14+)" }
elseif ($pol.PasswordHistoryCount -lt 24) { $STATUS='Failed'; $SEVERITY='Medium'; $EVIDENCE="Password history $($pol.PasswordHistoryCount) (recommend 24+)" }
else { $STATUS='Passed'; $SEVERITY=''; $EVIDENCE="MinLength=$($pol.MinPasswordLength), History=$($pol.PasswordHistoryCount)" }

$date = Get-Date -Format "yyyy-MM-dd"
$assessedBy = $env:USERNAME + "@" + $env:COMPUTERNAME
function ToCsv($v) { $s = ($v -replace '"','""'); if ($s -match '[,"\n]') { return "`"$s`"" } else { return $s } }
$line = (ToCsv $category) + "," + (ToCsv $control_id) + "," + (ToCsv $control_name) + "," + (ToCsv $STATUS) + "," + (ToCsv $SEVERITY) + "," + (ToCsv $EVIDENCE) + "," + (ToCsv $NOTES) + "," + (ToCsv $assessedBy) + "," + $date
$outFile = Join-Path $PSScriptRoot "sopra_assessment_results.csv"
if (-not (Test-Path $outFile)) { "category,control_id,control_name,status,severity,evidence,notes,assessed_by,assessment_date" | Out-File $outFile -Encoding UTF8 }
Add-Content -Path $outFile -Value $line -Encoding UTF8
Write-Host "[$control_id] $STATUS - $EVIDENCE"
