@echo off
echo ========================================
echo  Starting Geospatial API
echo ========================================
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo ERROR: Virtual environment not found!
    echo Please create it with: python -m venv .venv
    pause
    exit /b 1
)

echo [1/3] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [2/3] Checking geopandas installation...
python -c "import geopandas; print('  ✓ geopandas found!')" 2>nul
if errorlevel 1 (
    echo ERROR: geopandas not found!
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo [3/3] Starting API server...
echo.
echo ========================================
echo  API will be available at:
echo  http://127.0.0.1:8000
echo.
echo  Documentation:
echo  http://127.0.0.1:8000/docs
echo ========================================
echo.
echo Press CTRL+C to stop the server
echo.

uvicorn app.main:app --reload
