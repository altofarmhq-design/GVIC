@echo off
chcp 65001 > nul
echo ========================================
echo   GVIC Backend Server 시작
echo ========================================
echo.

cd /d "%~dp0backend"

:: 가상환경 활성화
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo 가상환경 활성화됨
) else (
    echo [경고] 가상환경이 없습니다. install.bat을 먼저 실행하세요.
    pause
    exit /b 1
)

echo.
echo 백엔드 서버 시작 중...
echo URL: http://localhost:8001
echo API 문서: http://localhost:8001/docs
echo.
echo 종료하려면 Ctrl+C를 누르세요.
echo ========================================
echo.

:: uvicorn 실행
python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload

pause
