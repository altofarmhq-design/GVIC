@echo off
echo.
echo === GVIC Engine Stop All Services ===
echo.

echo Stopping Backend (port 8001)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo Stopping Frontend (port 3000)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
)

taskkill /f /im node.exe >nul 2>&1

echo.
echo === All services stopped ===
echo.
pause
