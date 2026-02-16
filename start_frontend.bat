@echo off
chcp 65001 > nul
echo ========================================
echo   GVIC Frontend Server 시작
echo ========================================
echo.

cd /d "%~dp0frontend"

echo 프론트엔드 서버 시작 중...
echo URL: http://localhost:3000
echo.
echo 종료하려면 Ctrl+C를 누르세요.
echo ========================================
echo.

:: npm 또는 yarn으로 실행
npm start

pause
