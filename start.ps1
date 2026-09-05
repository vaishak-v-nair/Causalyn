# start.ps1
# Script to launch the Causalyn Full-stack AI Tool

$port = 8000

Write-Host "Checking for existing processes on port $port..." -ForegroundColor Cyan

# Find any process listening on the specified port
$netstatOutput = netstat -ano | Select-String ":$port\s+.*LISTENING"

if ($netstatOutput) {
    # Extract PID from the first matching line
    if ($netstatOutput.Line -match '\s+(\d+)$') {
        $pidToKill = $matches[1]
        Write-Host "Found process $pidToKill listening on port $port. Terminating it to free the port..." -ForegroundColor Yellow
        Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }
} else {
    Write-Host "Port $port is free." -ForegroundColor Green
}

Write-Host "Starting Causalyn AI Tool on http://127.0.0.1:8000..." -ForegroundColor Cyan
python app.py
