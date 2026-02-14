@echo off
title GVIC Engine - Start All Services

echo ================================================
echo     GVIC Engine System Startup
echo ================================================
echo.

REM Set project root path - CHANGE THIS IF NEEDED
set PROJECT_ROOT=C:\GVIC

REM Check if project folder exists
if not exist "%PROJECT_ROOT%" (
    echo [ERROR] Project folder not found: %PROJECT_ROOT%
    echo Please check the PROJECT_ROOT path setting.
    pause
    exit /b 1
)

REM Start Backend Server in new window
echo [1/2] Starting Backend Server...
start "GVIC Backend" cmd /k "cd /d %PROJECT_ROOT%\backend && call venv\Scripts\activate && python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload"
timeout /t 5 /nobreak > nul
echo [OK] Backend server starting... (http://localhost:8001)
echo.

REM Start Frontend Server in new window
echo [2/2] Starting Frontend Server...
start "GVIC Frontend" cmd /k "cd /d %PROJECT_ROOT%\frontend && yarn start"
timeout /t 3 /nobreak > nul
echo [OK] Frontend server starting... (http://localhost:3000)
echo.

echo ================================================
echo     All services are starting!
echo ================================================
echo.
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:8001
echo   API Docs: http://localhost:8001/docs
echo.
echo To stop servers, close each command window.
echo.
pause
