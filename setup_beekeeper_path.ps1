# Add TestZippr to user PATH so "run beekeeper" works from any folder
$projectPath = (Resolve-Path (Split-Path -Parent $MyInvocation.MyCommand.Path)).Path
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$projectPath*") {
    [Environment]::SetEnvironmentVariable("Path", $userPath + ";$projectPath", "User")
    Write-Host "Added $projectPath to your user PATH."
    Write-Host "Restart your terminal, then type: run beekeeper"
} else {
    Write-Host "Path already configured. Type: run beekeeper"
}
