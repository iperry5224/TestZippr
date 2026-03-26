# SOPRA Assessment Script: AD-009 - Replication Security
# Category: Active Directory Security
# Run on target machine; outputs CSV row for SOPRA import
# Correlates to remediation script: AD_009.ps1

$ErrorActionPreference = "SilentlyContinue"
$STATUS = "Not Assessed"
$SEVERITY = ""
$EVIDENCE = "Check not run"
$NOTES = ""

$category = "Active Directory Security"
$control_id = "AD-009"
$control_name = "Replication Security"

$cutoff = (Get-Date).AddDays(-90)
$stale = (Get-ADUser -Filter {Enabled -eq $true} -Properties LastLogonDate -ErrorAction SilentlyContinue | Where-Object { $_.LastLogonDate -lt $cutoff -or $null -eq $_.LastLogonDate }).Count
if ($stale -gt 10) { $STATUS='Failed'; $SEVERITY='Medium'; $EVIDENCE="$stale enabled accounts inactive >90 days" }
else { $STATUS='Passed'; $SEVERITY=''; $EVIDENCE="$stale stale accounts (threshold 10)" }

$date = Get-Date -Format "yyyy-MM-dd"
$assessedBy = $env:USERNAME + "@" + $env:COMPUTERNAME
function ToCsv($v) { $s = ($v -replace '"','""'); if ($s -match '[,"\n]') { return "`"$s`"" } else { return $s } }
$line = (ToCsv $category) + "," + (ToCsv $control_id) + "," + (ToCsv $control_name) + "," + (ToCsv $STATUS) + "," + (ToCsv $SEVERITY) + "," + (ToCsv $EVIDENCE) + "," + (ToCsv $NOTES) + "," + (ToCsv $assessedBy) + "," + $date
$outFile = Join-Path $PSScriptRoot "sopra_assessment_results.csv"
if (-not (Test-Path $outFile)) { "category,control_id,control_name,status,severity,evidence,notes,assessed_by,assessment_date" | Out-File $outFile -Encoding UTF8 }
Add-Content -Path $outFile -Value $line -Encoding UTF8
Write-Host "[$control_id] $STATUS - $EVIDENCE"
