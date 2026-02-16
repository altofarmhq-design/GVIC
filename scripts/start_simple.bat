@echo off
echo.
echo === GVIC Engine Start All Services ===
echo.

set "ROOT_DIR=%~dp0.."

echo [1/3] Starting MongoDB...
start "MongoDB" mongod --dbpath "%ROOT_DIR%\data\db"
timeout /t 3 /nobreak >nul
echo MongoDB started.
echo.

echo [2/3] Starting Backend...
cd /d "%ROOT_DIR%\backend"
start "GVIC-Backend" cmd /c "call venv\Scripts\activate.bat && python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload"
timeout /t 3 /nobreak >nul
echo Backend started at http://localhost:8001
echo.

echo [3/3] Starting Frontend...
cd /d "%ROOT_DIR%\frontend"
start "GVIC-Frontend" cmd /c "npm start"
echo Frontend started at http://localhost:3000
echo.

cd /d "%ROOT_DIR%"
echo.
echo === All services started! ===
echo.
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:8001
echo.
timeout /t 5 /nobreak >nul
start http://localhost:3000
pause
