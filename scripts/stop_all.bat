@echo off
chcp 65001 >nul

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║        GVIC 엔진 - 모든 서비스 종료                       ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

:: 백엔드 종료 (포트 8001)
echo [1/3] 백엔드 종료 중...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
    echo        백엔드 종료됨 (PID: %%a) ✓
)

:: 프론트엔드 종료 (포트 3000)
echo [2/3] 프론트엔드 종료 중...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
    echo        프론트엔드 종료됨 (PID: %%a) ✓
)

:: Node 프로세스 전체 종료
taskkill /f /im node.exe >nul 2>&1

:: Python uvicorn 종료
taskkill /f /im python.exe /fi "WINDOWTITLE eq GVIC Backend*" >nul 2>&1

echo [3/3] 창 정리 중...
:: 창 제목으로 종료
taskkill /f /fi "WINDOWTITLE eq GVIC*" >nul 2>&1

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║              모든 서비스가 종료되었습니다                  ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

pause
