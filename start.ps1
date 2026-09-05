# start.ps1
# Script to launch the Causalyn Full-stack Acausal Runtime

$port = 8000
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $scriptDir "backend"

Write-Host "Checking for existing processes on port $port..." -ForegroundColor Cyan

# Find any process listening on the specified port
try {
    $conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conn) {
        $pidToKill = $conn.OwningProcess | Select-Object -First 1
        $proc = Get-Process -Id $pidToKill -ErrorAction SilentlyContinue
        if ($proc -and $proc.ProcessName -ne "powershell" -and $proc.ProcessName -ne "pwsh" -and $proc.ProcessName -ne "Code") {
            Write-Host "Found $($proc.ProcessName) (PID: $pidToKill) listening on port $port. Freeing port..." -ForegroundColor Yellow
            Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 1
        }
    } else {
        Write-Host "Port $port is free." -ForegroundColor Green
    }
} catch {
    Write-Host "Port check completed." -ForegroundColor Green
}

Write-Host "Starting Causalyn Acausal Runtime on http://127.0.0.1:$port..." -ForegroundColor Cyan
Push-Location $backendDir
try {
    python -m uvicorn app:app --host 127.0.0.1 --port $port
} finally {
    Pop-Location
}

