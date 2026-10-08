# Run tests for Geospatial File Measurement API
# This script activates the virtual environment and runs pytest

Write-Host "🧪 Running tests..." -ForegroundColor Cyan
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

# Run tests
Write-Host "✓ Running pytest..." -ForegroundColor Green
Write-Host ""

pytest -v

Write-Host ""
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ All tests passed!" -ForegroundColor Green
} else {
    Write-Host "❌ Some tests failed" -ForegroundColor Red
}
