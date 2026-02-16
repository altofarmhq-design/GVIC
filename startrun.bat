@echo off
echo ========================================
echo   GVIC Startup Menu
echo ========================================
echo.
echo   [1] Start All (Backend + Frontend)
echo   [2] Start Backend only
echo   [3] Start Frontend only
echo   [4] Stop All Services
echo   [5] Check Status
echo   [6] Install Missing Packages
echo   [7] Open Browser (localhost:3000)
echo   [0] Exit
echo.
echo ========================================
set /p choice="Select [0-7]: "

if "%choice%"=="1" goto START_ALL
if "%choice%"=="2" goto START_BACKEND
if "%choice%"=="3" goto START_FRONTEND
if "%choice%"=="4" goto STOP_ALL
if "%choice%"=="5" goto CHECK_STATUS
if "%choice%"=="6" goto INSTALL_PACKAGES
if "%choice%"=="7" goto OPEN_BROWSER
if "%choice%"=="0" goto EXIT
goto :eof

:START_ALL
echo.
echo Starting Backend...
start "GVIC-Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\activate && python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload"
timeout /t 3 /nobreak > nul
echo Starting Frontend...
start "GVIC-Frontend" cmd /k "cd /d %~dp0frontend && npm start"
echo.
echo ========================================
echo   Services Started!
echo   Backend:  http://localhost:8001
echo   Frontend: http://localhost:3000
echo ========================================
timeout /t 5 /nobreak > nul
start http://localhost:3000
pause
goto :eof

:START_BACKEND
echo.
echo Starting Backend...
start "GVIC-Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\activate && python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload"
echo Backend started: http://localhost:8001
pause
goto :eof

:START_FRONTEND
echo.
echo Starting Frontend...
start "GVIC-Frontend" cmd /k "cd /d %~dp0frontend && npm start"
echo Frontend started: http://localhost:3000
pause
goto :eof

:STOP_ALL
echo.
echo Stopping services...
taskkill /FI "WINDOWTITLE eq GVIC-Backend*" /F > nul 2>&1
taskkill /FI "WINDOWTITLE eq GVIC-Frontend*" /F > nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr :8001 ^| findstr LISTENING') do taskkill /PID %%a /F > nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr :3000 ^| findstr LISTENING') do taskkill /PID %%a /F > nul 2>&1
echo All services stopped.
pause
goto :eof

:CHECK_STATUS
echo.
echo Checking services...
echo.
echo [Backend - Port 8001]
netstat -ano | findstr :8001 | findstr LISTENING > nul
if errorlevel 1 (echo   Status: STOPPED) else (echo   Status: RUNNING)
echo.
echo [Frontend - Port 3000]
netstat -ano | findstr :3000 | findstr LISTENING > nul
if errorlevel 1 (echo   Status: STOPPED) else (echo   Status: RUNNING)
echo.
pause
goto :eof

:INSTALL_PACKAGES
echo.
echo Installing missing packages...
cd /d %~dp0backend
call venv\Scripts\activate
pip install motor email-validator
echo.
echo Done!
pause
goto :eof

:OPEN_BROWSER
start http://localhost:3000
goto :eof

:EXIT
exit /b 0
