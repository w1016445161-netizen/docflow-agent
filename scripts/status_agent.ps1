# DocFlow Agent status script
# Check FastAPI backend and Vue frontend status safely

$ErrorActionPreference = "Continue"

Write-Host "========================================"
Write-Host "DocFlow Agent Status"
Write-Host "========================================"

$Backend = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
$Frontend = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1

if ($Backend) {
    Write-Host "Backend FastAPI: RUNNING" -ForegroundColor Green
    Write-Host "Backend URL: http://127.0.0.1:8000"
    Write-Host "API Docs: http://127.0.0.1:8000/docs"
    Write-Host "PID: $($Backend.OwningProcess)"
} else {
    Write-Host "Backend FastAPI: STOPPED" -ForegroundColor Red
}

Write-Host ""

if ($Frontend) {
    Write-Host "Frontend Vue: RUNNING" -ForegroundColor Green
    Write-Host "Frontend URL: http://localhost:5173"
    Write-Host "PID: $($Frontend.OwningProcess)"
} else {
    Write-Host "Frontend Vue: STOPPED" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================"