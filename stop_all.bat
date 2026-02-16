@echo off
chcp 65001 > nul
echo ========================================
echo   GVIC 서비스 중지
echo ========================================
echo.

:: 포트 8001 (백엔드) 프로세스 종료
echo 백엔드 서버 종료 중...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001') do (
    taskkill /PID %%a /F > nul 2>&1
)

:: 포트 3000 (프론트엔드) 프로세스 종료
echo 프론트엔드 서버 종료 중...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do (
    taskkill /PID %%a /F > nul 2>&1
)

echo.
echo 모든 서비스가 종료되었습니다.
echo.
pause
