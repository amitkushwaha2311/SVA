<#
.SYNOPSIS
Starts the SVA development environment (Backend + Frontend).

.DESCRIPTION
This script activates the backend virtual environment, starts the FastAPI backend server on port 8000, 
and concurrently starts the Next.js frontend development server on port 3000.
The frontend is already configured to proxy /api requests to the backend.

.EXAMPLE
.\start-dev.ps1
#>

$ErrorActionPreference = "Stop"

Write-Host "Starting SVA Development Environment..." -ForegroundColor Cyan

# Check if we're in the right directory
if (-not (Test-Path "backend") -or -not (Test-Path "frontend")) {
    Write-Host "Error: Must be run from the SVA root directory containing 'backend' and 'frontend'." -ForegroundColor Red
    exit 1
}

# 1. Start Backend
Write-Host "Starting FastAPI Backend (Port 8000)..." -ForegroundColor Green
$BackendProcess = Start-Process -NoNewWindow -PassThru -FilePath "powershell.exe" -ArgumentList "-Command `"cd backend; .\`.venv\Scripts\Activate.ps1; uvicorn app.api.main:app --host 127.0.0.1 --port 8000 --reload`""

# 2. Start Frontend
Write-Host "Starting Next.js Frontend (Port 3000)..." -ForegroundColor Green
$FrontendProcess = Start-Process -NoNewWindow -PassThru -FilePath "powershell.exe" -ArgumentList "-Command `"cd frontend; npm run dev`""

Write-Host "`nDevelopment servers are starting in the background!" -ForegroundColor Cyan
Write-Host "-> Backend:  http://127.0.0.1:8000 (API Docs: http://127.0.0.1:8000/docs)"
Write-Host "-> Frontend: http://localhost:3000"
Write-Host "`nPress Ctrl+C to stop both servers." -ForegroundColor Yellow

try {
    # Keep the script running so we can capture Ctrl+C
    while ($true) {
        Start-Sleep -Seconds 1
        
        # If both processes somehow exit on their own, stop the script
        if ($BackendProcess.HasExited -and $FrontendProcess.HasExited) {
            Write-Host "Both servers have exited."
            break
        }
    }
}
finally {
    Write-Host "`nStopping servers..." -ForegroundColor Cyan
    if (-not $BackendProcess.HasExited) {
        Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if (-not $FrontendProcess.HasExited) {
        Stop-Process -Id $FrontendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "Servers stopped." -ForegroundColor Green
}
