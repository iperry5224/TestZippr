# SOPRA Assessment Script: AD-005 - Kerberos Configuration
# Category: Active Directory Security
# Run on target machine; outputs CSV row for SOPRA import
# Correlates to remediation script: AD_005.ps1

$ErrorActionPreference = "SilentlyContinue"
$STATUS = "Not Assessed"
$SEVERITY = ""
$EVIDENCE = "Check not run"
$NOTES = ""

$category = "Active Directory Security"
$control_id = "AD-005"
$control_name = "Kerberos Configuration"

$kerberoast = (Get-ADUser -Filter {ServicePrincipalName -ne '$null' -and DoesNotRequirePreAuth -eq $true} -ErrorAction SilentlyContinue).Count
if ($kerberoast -gt 0) { $STATUS='Failed'; $SEVERITY='High'; $EVIDENCE="$kerberoast accounts vulnerable to Kerberoasting (pre-auth disabled)" }
else { $STATUS='Passed'; $SEVERITY=''; $EVIDENCE="No Kerberoastable accounts found" }

$date = Get-Date -Format "yyyy-MM-dd"
$assessedBy = $env:USERNAME + "@" + $env:COMPUTERNAME
function ToCsv($v) { $s = ($v -replace '"','""'); if ($s -match '[,"\n]') { return "`"$s`"" } else { return $s } }
$line = (ToCsv $category) + "," + (ToCsv $control_id) + "," + (ToCsv $control_name) + "," + (ToCsv $STATUS) + "," + (ToCsv $SEVERITY) + "," + (ToCsv $EVIDENCE) + "," + (ToCsv $NOTES) + "," + (ToCsv $assessedBy) + "," + $date
$outFile = Join-Path $PSScriptRoot "sopra_assessment_results.csv"
if (-not (Test-Path $outFile)) { "category,control_id,control_name,status,severity,evidence,notes,assessed_by,assessment_date" | Out-File $outFile -Encoding UTF8 }
Add-Content -Path $outFile -Value $line -Encoding UTF8
Write-Host "[$control_id] $STATUS - $EVIDENCE"
