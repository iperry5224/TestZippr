#!/usr/bin/env python3
"""
Export SOPRA remediation scripts for presentation.
Generates a folder of .ps1 files (PowerShell) - the actual runnable scripts
SOPRA uses to remediate failed security controls.
"""
import os
from sopra_controls import ALL_CONTROLS, get_remediation_script

OUTPUT_DIR = "sopra_remediation_scripts"
INDEX_FILE = "00_INDEX.txt"

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    index_lines = ["SOPRA REMEDIATION SCRIPTS - Export Index", "=" * 60, ""]

    for ctrl_id, control in sorted(ALL_CONTROLS.items()):
        script = get_remediation_script(ctrl_id, "powershell")
        if not script.strip():
            continue  # Skip controls with no PowerShell steps
        fname = f"{ctrl_id.replace('-', '_')}.ps1"
        path = os.path.join(OUTPUT_DIR, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(script)
        index_lines.append(f"{ctrl_id:12} {control.name[:55]:<55} -> {fname}")

    index_lines.extend(["", "=" * 60, f"Total: {len([c for c in ALL_CONTROLS.values() if get_remediation_script(c.id)])} controls with PowerShell remediation steps"])
    with open(os.path.join(OUTPUT_DIR, INDEX_FILE), "w", encoding="utf-8") as f:
        f.write("\n".join(index_lines))

    print(f"Exported to ./{OUTPUT_DIR}/")
    print(f"  - {INDEX_FILE} (index)")
    print(f"  - *.ps1 (PowerShell remediation scripts)")
    print("\nThese are the actual scripts SOPRA generates to fix failed controls.")

if __name__ == "__main__":
    main()
