# DocFlow Agent start script
# Start FastAPI backend and Vue frontend

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$RuntimeDir = Join-Path $ProjectRoot ".runtime"

$BackendPidFile = Join-Path $RuntimeDir "backend.pid"
$FrontendPidFile = Join-Path $RuntimeDir "frontend.pid"

Write-Host "========================================"
Write-Host "Starting DocFlow Agent..."
Write-Host "Project root: $ProjectRoot"
Write-Host "========================================"

if (!(Test-Path $RuntimeDir)) {
    New-Item -ItemType Directory -Force $RuntimeDir | Out-Null
}

$VenvActivate = Join-Path $ProjectRoot ".venv\Scripts\Activate.ps1"
if (!(Test-Path $VenvActivate)) {
    Write-Host "ERROR: Python venv not found: $VenvActivate" -ForegroundColor Red
    exit 1
}

$EnvFile = Join-Path $ProjectRoot ".env"
if (!(Test-Path $EnvFile)) {
    Write-Host "ERROR: .env file not found: $EnvFile" -ForegroundColor Red
    exit 1
}

$FrontendDir = Join-Path $ProjectRoot "frontend"
if (!(Test-Path $FrontendDir)) {
    Write-Host "ERROR: frontend directory not found: $FrontendDir" -ForegroundColor Red
    exit 1
}

$NodeModules = Join-Path $FrontendDir "node_modules"
if (!(Test-Path $NodeModules)) {
    Write-Host "frontend node_modules not found. Running npm install..."
    Push-Location $FrontendDir
    npm install
    Pop-Location
}

Write-Host ""
Write-Host "Starting backend: http://127.0.0.1:8000"

$BackendCommand = "cd `"$ProjectRoot`"; Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; . `"$VenvActivate`"; python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000"

$BackendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", $BackendCommand -PassThru
$BackendProcess.Id | Out-File -Encoding ascii $BackendPidFile

Start-Sleep -Seconds 2

Write-Host "Starting frontend: http://localhost:5173"

$FrontendCommand = "cd `"$FrontendDir`"; npm run dev"

$FrontendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", $FrontendCommand -PassThru
$FrontendProcess.Id | Out-File -Encoding ascii $FrontendPidFile

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "DocFlow Agent started successfully." -ForegroundColor Green
Write-Host "Backend: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "API Docs: http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend PID: $($BackendProcess.Id)"
Write-Host "Frontend PID: $($FrontendProcess.Id)"
Write-Host ""
Write-Host "Open this URL in browser:"
Write-Host "http://localhost:5173"
