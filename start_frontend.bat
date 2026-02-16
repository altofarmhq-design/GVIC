@echo off
echo ========================================
echo   GVIC Frontend Server
echo ========================================
echo.

cd /d "%~dp0frontend"

echo Starting frontend on http://localhost:3000
echo Press Ctrl+C to stop
echo.

npm start

pause
