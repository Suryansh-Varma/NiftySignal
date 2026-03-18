# Quick Start Script for NiftySignal
# Run this with: .\start_all_services.ps1

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "  NiftySignal - Starting All Services" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "[ERROR] Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please create it first with: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host "[1/4] Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Start Backend API (port 8000)
Write-Host "[2/4] Starting Backend API (port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\.venv\Scripts\Activate.ps1; python -m uvicorn app.api_server.main:app --reload --port 8000"

# Wait for backend to start
Start-Sleep -Seconds 5

# Start Frontend (port 3000)
Write-Host "[3/4] Starting Frontend (port 3000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\frontend'; npm run dev"

# Wait for frontend to start
Start-Sleep -Seconds 8

# Verify all services
Write-Host "[4/4] Verifying services..." -ForegroundColor Yellow
Write-Host ""

# Check Backend
try {
    $backend = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -UseBasicParsing -TimeoutSec 3
    Write-Host "✓ Backend API: http://localhost:8000 - RUNNING" -ForegroundColor Green
} catch {
    Write-Host "✗ Backend API: http://localhost:8000 - NOT RUNNING" -ForegroundColor Red
}

# Check Frontend
try {
    $frontend = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 3
    Write-Host "✓ Frontend: http://localhost:3000 - RUNNING" -ForegroundColor Green
} catch {
    Write-Host "✗ Frontend: http://localhost:3000 - NOT RUNNING" -ForegroundColor Red
}

Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "  All Services Started!" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Open your browser and go to: http://localhost:3000" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C in each terminal window to stop services." -ForegroundColor Gray
