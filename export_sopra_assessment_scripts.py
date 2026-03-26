#!/usr/bin/env python3
"""
Export SOPRA assessment scripts - 1:1 with remediation scripts.
System admins run these on target machines; output CSV goes to SOPRA for import.
"""
import os
from sopra_controls import ALL_CONTROLS
from sopra_assessment_checks import get_assessment_check

OUTPUT_DIR = "sopra_assessment_scripts"


def ps1_header(control_id, control_name, category):
    return f"""# SOPRA Assessment Script: {control_id} - {control_name}
# Category: {category}
# Run on target machine; outputs CSV row for SOPRA import
# Correlates to remediation script: {control_id.replace('-','_')}.ps1

$ErrorActionPreference = "SilentlyContinue"
$STATUS = "Not Assessed"
$SEVERITY = ""
$EVIDENCE = "Check not run"
$NOTES = ""

"""


def ps1_footer(control_id, control_name, category):
    return r"""
$date = Get-Date -Format "yyyy-MM-dd"
$assessedBy = $env:USERNAME + "@" + $env:COMPUTERNAME
function ToCsv($v) { $s = ($v -replace '"','""'); if ($s -match '[,"\n]') { return "`"$s`"" } else { return $s } }
$line = (ToCsv $category) + "," + (ToCsv $control_id) + "," + (ToCsv $control_name) + "," + (ToCsv $STATUS) + "," + (ToCsv $SEVERITY) + "," + (ToCsv $EVIDENCE) + "," + (ToCsv $NOTES) + "," + (ToCsv $assessedBy) + "," + $date
$outFile = Join-Path $PSScriptRoot "sopra_assessment_results.csv"
if (-not (Test-Path $outFile)) { "category,control_id,control_name,status,severity,evidence,notes,assessed_by,assessment_date" | Out-File $outFile -Encoding UTF8 }
Add-Content -Path $outFile -Value $line -Encoding UTF8
Write-Host "[$control_id] $STATUS - $EVIDENCE"
"""


def generate_for_control(ctrl_id, control):
    category = control.category
    name = control.name
    check = get_assessment_check(ctrl_id)

    script = ps1_header(ctrl_id, name, category)
    script += f'$category = "{category}"\n$control_id = "{ctrl_id}"\n$control_name = "{name}"\n\n'

    if check:
        script += check.script.strip() + "\n"
    else:
        first_cmd = None
        for s in control.remediation_steps:
            if s.command and s.script_type == "powershell":
                first_cmd = s.command
                break
        if first_cmd:
            escaped = first_cmd.replace("'", "''")
            script += f"""# Discovery only - manual review required
try {{
    $out = Invoke-Expression '{escaped}'
    $STATUS = "Manual Review"
    $SEVERITY = ""
    $EVIDENCE = "Discovery completed - review output above and update CSV manually"
}} catch {{
    $STATUS = "Failed"
    $SEVERITY = "Medium"
    $EVIDENCE = "Discovery failed: $($_.Exception.Message)"
}}
"""
        else:
            script += '$STATUS = "Manual Review"; $EVIDENCE = "No automated check - assess manually"\n'

    script += ps1_footer(ctrl_id, name, category)
    return script


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    runner_lines = [
        "# SOPRA Assessment - Run All",
        "# Execute on target machine with appropriate permissions (Domain Admin for AD, etc.)",
        "# Output: sopra_assessment_results.csv - import into SOPRA",
        "",
        "$ScriptDir = $PSScriptRoot",
        "if (Test-Path (Join-Path $ScriptDir 'sopra_assessment_results.csv')) { Remove-Item (Join-Path $ScriptDir 'sopra_assessment_results.csv') }",
        "'category,control_id,control_name,status,severity,evidence,notes,assessed_by,assessment_date' | Out-File (Join-Path $ScriptDir 'sopra_assessment_results.csv') -Encoding UTF8",
        ""
    ]

    for ctrl_id, control in sorted(ALL_CONTROLS.items()):
        script = generate_for_control(ctrl_id, control)
        fname = f"{ctrl_id.replace('-', '_')}_assessment.ps1"
        path = os.path.join(OUTPUT_DIR, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(script)
        runner_lines.append(f"& (Join-Path $ScriptDir '{fname}')")

    runner_lines.append("")
    runner_lines.append("Write-Host ''")
    runner_lines.append("Write-Host 'Done. Import sopra_assessment_results.csv into SOPRA.'")

    with open(os.path.join(OUTPUT_DIR, "Run-All-Assessments.ps1"), "w", encoding="utf-8") as f:
        f.write("\n".join(runner_lines))

    print(f"Exported to ./{OUTPUT_DIR}/")
    print(f"  - Run-All-Assessments.ps1 (runs all checks)")
    print(f"  - *_assessment.ps1 (one per control, 1:1 with remediation)")
    print(f"  - Output: sopra_assessment_results.csv -> import into SOPRA")


if __name__ == "__main__":
    main()
