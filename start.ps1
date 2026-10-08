# Start Geospatial File Measurement API
# This script activates the virtual environment and starts the server

Write-Host "🚀 Starting Geospatial File Measurement API..." -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host "✓ Activating virtual environment..." -ForegroundColor Green
& .venv\Scripts\Activate.ps1

# Check if geopandas is installed
Write-Host "✓ Checking dependencies..." -ForegroundColor Green
$geopandas = python -m pip list | Select-String "geopandas"
if (-not $geopandas) {
    Write-Host "❌ Dependencies not installed!" -ForegroundColor Red
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

Write-Host ""
Write-Host "✓ All checks passed!" -ForegroundColor Green
Write-Host ""
Write-Host "📡 Starting API server..." -ForegroundColor Cyan
Write-Host "   API will be available at: http://127.0.0.1:8000" -ForegroundColor White
Write-Host "   Documentation: http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Press CTRL+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the server
uvicorn app.main:app --reload
