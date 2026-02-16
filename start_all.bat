@echo off
chcp 65001 > nul
echo ========================================
echo   GVIC 전체 서비스 시작
echo ========================================
echo.

:: 백엔드를 새 창에서 시작
start "GVIC Backend" cmd /k "cd /d %~dp0 && start_backend.bat"

:: 3초 대기
timeout /t 3 /nobreak > nul

:: 프론트엔드를 새 창에서 시작
start "GVIC Frontend" cmd /k "cd /d %~dp0 && start_frontend.bat"

echo.
echo 백엔드와 프론트엔드가 별도 창에서 시작되었습니다.
echo.
echo 잠시 후 브라우저에서 http://localhost:3000 으로 접속하세요.
echo.

:: 5초 후 브라우저 열기
timeout /t 5 /nobreak > nul
start http://localhost:3000

echo 이 창은 닫아도 됩니다.
pause
