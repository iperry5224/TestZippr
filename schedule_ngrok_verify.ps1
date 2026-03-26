# Schedule ngrok tunnel verification to run every 24 hours
# Run this script once to set up the task

$TaskName = "Verify-SAELAR-SOPRA-ngrok"
$ScriptPath = "C:\Users\iperr\TestZippr\verify_ngrok_tunnels.py"
$PythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $PythonPath) { $PythonPath = "python" }

$Action = New-ScheduledTaskAction -Execute $PythonPath -Argument "`"$ScriptPath`"" -WorkingDirectory "C:\Users\iperr\TestZippr"
$Trigger = New-ScheduledTaskTrigger -Daily -At 6:00AM
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Force | Out-Null
Write-Host "Scheduled task '$TaskName' created. Runs every 24 hours (first run at 6:00 AM)."
Write-Host "To run now: Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "To view: Get-ScheduledTask -TaskName '$TaskName'"
Write-Host "To remove: Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"
