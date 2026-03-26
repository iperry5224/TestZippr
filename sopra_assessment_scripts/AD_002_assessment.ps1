# SOPRA Assessment Script: AD-002 - Service Account Management
# Category: Active Directory Security
# Run on target machine; outputs CSV row for SOPRA import
# Correlates to remediation script: AD_002.ps1

$ErrorActionPreference = "SilentlyContinue"
$STATUS = "Not Assessed"
$SEVERITY = ""
$EVIDENCE = "Check not run"
$NOTES = ""

$category = "Active Directory Security"
$control_id = "AD-002"
$control_name = "Service Account Management"

try { $gmsa = (Get-ADServiceAccount -Filter * -ErrorAction SilentlyContinue).Count }
catch { $gmsa = 0 }
$users = Get-ADUser -Filter {ServicePrincipalName -ne '$null'} -Properties PasswordLastSet -ErrorAction SilentlyContinue
$old = ($users | Where-Object { $_.PasswordLastSet -lt (Get-Date).AddDays(-90) }).Count
if ($old -gt 0) { $STATUS='Failed'; $SEVERITY='High'; $EVIDENCE="$old service accounts with password older than 90 days" }
else { $STATUS='Passed'; $SEVERITY=''; $EVIDENCE="Service accounts within password age policy" }

$date = Get-Date -Format "yyyy-MM-dd"
$assessedBy = $env:USERNAME + "@" + $env:COMPUTERNAME
function ToCsv($v) { $s = ($v -replace '"','""'); if ($s -match '[,"\n]') { return "`"$s`"" } else { return $s } }
$line = (ToCsv $category) + "," + (ToCsv $control_id) + "," + (ToCsv $control_name) + "," + (ToCsv $STATUS) + "," + (ToCsv $SEVERITY) + "," + (ToCsv $EVIDENCE) + "," + (ToCsv $NOTES) + "," + (ToCsv $assessedBy) + "," + $date
$outFile = Join-Path $PSScriptRoot "sopra_assessment_results.csv"
if (-not (Test-Path $outFile)) { "category,control_id,control_name,status,severity,evidence,notes,assessed_by,assessment_date" | Out-File $outFile -Encoding UTF8 }
Add-Content -Path $outFile -Value $line -Encoding UTF8
Write-Host "[$control_id] $STATUS - $EVIDENCE"
