# start.ps1
# Script to launch the Causalyn Full-stack Acausal Runtime
param(
    [int]$port = 8000,
    [string]$hostAddress = "127.0.0.1",
    [switch]$reload
)

$scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
$backendDir = Join-Path $scriptDir "backend"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   CAUSALYN ACAUSAL RUNTIME SUPERVISOR" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Resolve Python interpreter with uvicorn support
$candidates = @(
    (Join-Path $scriptDir ".venv\Scripts\python.exe"),
    (Join-Path $scriptDir "venv\Scripts\python.exe"),
    (Join-Path $scriptDir "env\Scripts\python.exe")
)

if ($env:VIRTUAL_ENV) {
    $candidates += (Join-Path $env:VIRTUAL_ENV "Scripts\python.exe")
    $candidates += (Join-Path $env:VIRTUAL_ENV "bin\python")
}

# Add system runtime paths
$knownCore = "C:\Users\vaish\AppData\Local\Python\pythoncore-3.14-64\python.exe"
if (Test-Path $knownCore) {
    $candidates += $knownCore
}

$systemPy = (Get-Command python -ErrorAction SilentlyContinue)
if ($systemPy) {
    $candidates += $systemPy.Source
}

$systemPy3 = (Get-Command python3 -ErrorAction SilentlyContinue)
if ($systemPy3) {
    $candidates += $systemPy3.Source
}

$selectedPython = $null
foreach ($cand in $candidates) {
    if ($cand -and (Test-Path $cand)) {
        & $cand -c "import uvicorn" 2>$null
        if ($LASTEXITCODE -eq 0) {
            $selectedPython = $cand
            break
        }
    }
}

if (-not $selectedPython) {
    Write-Host "[ERROR] Could not find a Python interpreter with 'uvicorn' installed." -ForegroundColor Red
    Write-Host "Searched candidates:" -ForegroundColor Yellow
    foreach ($cand in $candidates) {
        if ($cand -and (Test-Path $cand)) {
            Write-Host "  - Found $cand (missing uvicorn module)" -ForegroundColor Yellow
        }
    }
    
    $venvPy = Join-Path $scriptDir ".venv\Scripts\python.exe"
    if (Test-Path $venvPy) {
        Write-Host "`nAttempting auto-repair: Installing dependencies into .venv..." -ForegroundColor Cyan
        & (Join-Path $scriptDir ".venv\Scripts\pip.exe") install uvicorn fastapi
        if ($LASTEXITCODE -eq 0) {
            $selectedPython = $venvPy
        }
    }
    
    if (-not $selectedPython) {
        Write-Host "`nPlease activate the environment and install requirements:" -ForegroundColor Yellow
        Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor White
        Write-Host "  pip install -r requirements.txt`n" -ForegroundColor White
        exit 1
    }
}

Write-Host "Python: $selectedPython" -ForegroundColor Green

# 2. Check for existing processes on port $port
Write-Host "Checking for existing processes on port $port..." -ForegroundColor Cyan
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

# 3. Launch uvicorn
Write-Host "Starting Causalyn Acausal Runtime on http://${hostAddress}:$port..." -ForegroundColor Cyan
Push-Location $backendDir
try {
    $uvicornArgs = @("-m", "uvicorn", "app:app", "--host", $hostAddress, "--port", "$port")
    if ($reload) {
        $uvicornArgs += "--reload"
    }
    & $selectedPython $uvicornArgs
} finally {
    Pop-Location
}
