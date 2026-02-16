@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║        GVIC 엔진 - 모든 서비스 시작                       ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

set "ROOT_DIR=%~dp0.."
cd /d "%ROOT_DIR%"

:: ==================== MongoDB 시작 ====================
echo [1/3] MongoDB 시작 중...

:: MongoDB 서비스 확인
sc query MongoDB >nul 2>&1
if %errorlevel% equ 0 (
    net start MongoDB >nul 2>&1
    echo        MongoDB 서비스 시작됨 ✓
) else (
    :: 서비스가 없으면 직접 실행
    tasklist /fi "imagename eq mongod.exe" | find /i "mongod.exe" >nul 2>&1
    if %errorlevel% neq 0 (
        echo        MongoDB 직접 시작 중...
        start "MongoDB" mongod --dbpath "%ROOT_DIR%\data\db"
        timeout /t 3 /nobreak >nul
    ) else (
        echo        MongoDB 이미 실행 중 ✓
    )
)
echo.

:: ==================== 백엔드 시작 ====================
echo [2/3] 백엔드 시작 중...
cd /d "%ROOT_DIR%\backend"

:: 기존 백엔드 프로세스 확인
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING 2^>nul') do (
    echo        포트 8001 사용 중 (PID: %%a) - 종료 중...
    taskkill /PID %%a /F >nul 2>&1
)

:: 가상환경 활성화 및 서버 시작
start "GVIC Backend" cmd /c "call venv\Scripts\activate.bat && python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload"
echo        백엔드 시작됨 (http://localhost:8001) ✓

cd /d "%ROOT_DIR%"
timeout /t 3 /nobreak >nul
echo.

:: ==================== 프론트엔드 시작 ====================
echo [3/3] 프론트엔드 시작 중...
cd /d "%ROOT_DIR%\frontend"

:: 기존 프론트엔드 프로세스 확인
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING 2^>nul') do (
    echo        포트 3000 사용 중 (PID: %%a) - 종료 중...
    taskkill /PID %%a /F >nul 2>&1
)

:: 프론트엔드 시작
start "GVIC Frontend" cmd /c "npm start"
echo        프론트엔드 시작됨 (http://localhost:3000) ✓

cd /d "%ROOT_DIR%"
echo.

:: ==================== 완료 ====================
echo ╔════════════════════════════════════════════════════════════╗
echo ║                   모든 서비스 시작 완료!                   ║
echo ╠════════════════════════════════════════════════════════════╣
echo ║                                                            ║
echo ║  서비스 URL:                                               ║
echo ║  • 프론트엔드: http://localhost:3000                      ║
echo ║  • 백엔드 API: http://localhost:8001/api                  ║
echo ║  • API 문서:   http://localhost:8001/docs                 ║
echo ║                                                            ║
echo ║  종료하려면: scripts\stop_all.bat 실행                    ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

:: 브라우저 자동 열기 (5초 후)
echo 5초 후 브라우저에서 http://localhost:3000 이 열립니다...
timeout /t 5 /nobreak >nul
start http://localhost:3000

pause
