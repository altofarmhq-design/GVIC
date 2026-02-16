@echo off
echo ========================================
echo   GVIC Backend Server
echo ========================================
echo.

cd /d "%~dp0backend"

if not exist "venv\Scripts\activate.bat" (
    echo ERROR: venv not found. Run install.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
echo Starting backend on http://localhost:8001
echo Press Ctrl+C to stop
echo.

python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload

pause
