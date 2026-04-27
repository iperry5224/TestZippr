# Build a timestamped SLyK deploy zip (slyk folder only) for CloudShell / other machines.
# Usage: .\package_slyk_zip.ps1
# Output: slyk-53-aws-tenant-<yyyyMMdd-HHmmss>.zip in this directory

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$slykDir = Join-Path $root "slyk_deploy_extract\slyk"
if (-not (Test-Path $slykDir)) {
    Write-Error "Not found: $slykDir"
}
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
$out = Join-Path $root "slyk-53-aws-tenant-$ts.zip"
if (Test-Path $out) { Remove-Item $out -Force }
Compress-Archive -Path $slykDir -DestinationPath $out -Force
$item = Get-Item $out
Write-Host "Created: $($item.FullName)"
Write-Host "Size:    $($item.Length) bytes"
Write-Host "Time:    $($item.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'))"
