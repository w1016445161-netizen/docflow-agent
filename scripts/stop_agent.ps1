# DocFlow Agent stop script
# Stop FastAPI backend and Vue frontend safely

$ErrorActionPreference = "Continue"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$RuntimeDir = Join-Path $ProjectRoot ".runtime"

$BackendPidFile = Join-Path $RuntimeDir "backend.pid"
$FrontendPidFile = Join-Path $RuntimeDir "frontend.pid"

Write-Host "========================================"
Write-Host "Stopping DocFlow Agent..."
Write-Host "========================================"

function Stop-ProcessTreeByPidFile {
    param (
        [string]$PidFile,
        [string]$ProcessName
    )

    if (Test-Path $PidFile) {
        $PidText = Get-Content $PidFile -ErrorAction SilentlyContinue

        if ($PidText) {
            $PidNumber = [int]$PidText

            if ($PidNumber -gt 4) {
                Write-Host "Stopping $ProcessName. PID: $PidNumber"
                taskkill /PID $PidNumber /T /F | Out-Null
                Write-Host "$ProcessName stopped."
            } else {
                Write-Host "$ProcessName PID is system PID $PidNumber. Skipped."
            }

            Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
        }
    } else {
        Write-Host "$ProcessName PID file not found. Skipped."
    }
}

function Stop-PortListener {
    param (
        [int]$Port,
        [string]$Name
    )

    $Connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue

    if (!$Connections) {
        Write-Host "$Name port $Port is not listening."
        return
    }

    foreach ($Connection in $Connections) {
        $PidNumber = $Connection.OwningProcess

        if ($PidNumber -gt 4) {
            Write-Host "$Name port $Port is still listening. Killing PID: $PidNumber"
            taskkill /PID $PidNumber /T /F | Out-Null
        } else {
            Write-Host "$Name port $Port is owned by system PID $PidNumber. Skipped."
        }
    }
}

Stop-ProcessTreeByPidFile -PidFile $BackendPidFile -ProcessName "Backend FastAPI"
Stop-ProcessTreeByPidFile -PidFile $FrontendPidFile -ProcessName "Frontend Vue"

Write-Host ""
Write-Host "Checking listening ports..."

Stop-PortListener -Port 8000 -Name "Backend"
Stop-PortListener -Port 5173 -Name "Frontend"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "DocFlow Agent stopped." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
