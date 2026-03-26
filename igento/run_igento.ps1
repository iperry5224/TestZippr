# Run Igento - Starts the MCP server and browser bridge, then opens http://localhost:8080
# Usage: .\run_igento.ps1   or   run igento (via run.cmd in project root)

$IgentoDir = $PSScriptRoot
$ServerScript = Join-Path $IgentoDir "igento_server.py"
$BridgeScript = Join-Path $IgentoDir "igento_browser_bridge.py"

# Stop any existing Igento or bridge on our ports
foreach ($port in @(2323, 8080)) {
    $conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($conn) {
        Write-Host "Stopping existing process on port $port (PID $($conn.OwningProcess))..."
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
    }
}

# Start Igento MCP server (port 2323)
Write-Host "Starting Igento MCP server on port 2323..."
$serverProc = Start-Process -FilePath "python" -ArgumentList $ServerScript, "--transport", "streamable-http", "--port", "2323" -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 3

# Start browser bridge (port 8080)
Write-Host "Starting Igento Browser Bridge on port 8080..."
$bridgeProc = Start-Process -FilePath "python" -ArgumentList $BridgeScript -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 2

# Open browser
Write-Host "Opening http://localhost:8080 in your browser..."
Start-Process "http://localhost:8080"

Write-Host ""
Write-Host "Igento is running. Open http://localhost:8080 in your browser."
Write-Host "To stop: Close the browser, then run: Stop-Process -Id $($serverProc.Id),$($bridgeProc.Id) -Force -ErrorAction SilentlyContinue"
Write-Host ""
