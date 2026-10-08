@echo off
echo ========================================
echo  Running Tests
echo ========================================
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo ERROR: Virtual environment not found!
    echo Please create it with: python -m venv .venv
    pause
    exit /b 1
)

echo [1/2] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [2/2] Running pytest...
echo.

pytest -v

echo.
if errorlevel 1 (
    echo ========================================
    echo  Some tests FAILED
    echo ========================================
) else (
    echo ========================================
    echo  All tests PASSED!
    echo ========================================
)
echo.
pause
