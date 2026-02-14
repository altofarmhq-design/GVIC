@echo off
set PROJECT_ROOT=C:\GVIC

echo Starting GVIC Engine...
echo.

if not exist "%PROJECT_ROOT%\backend" (
    echo ERROR: Backend folder not found at %PROJECT_ROOT%\backend
    pause
    exit /b 1
)

echo [1/2] Starting Backend...
start "Backend" cmd /k "cd /d %PROJECT_ROOT%\backend && venv\Scripts\activate && python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload"

timeout /t 5 /nobreak >nul

echo [2/2] Starting Frontend...
start "Frontend" cmd /k "cd /d %PROJECT_ROOT%\frontend && yarn start"

echo.
echo ========================================
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:8001
echo ========================================
echo.
pause
