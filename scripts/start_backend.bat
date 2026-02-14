@echo off
chcp 65001 > nul
title GVIC Engine - 백엔드 서버

echo ================================================
echo     GVIC Engine 백엔드 서버 시작
echo ================================================
echo.

:: 프로젝트 경로 설정
set PROJECT_ROOT=C:\GVIC
set BACKEND_PATH=%PROJECT_ROOT%\backend

:: 백엔드 폴더로 이동
cd /d %BACKEND_PATH%
if %errorlevel% neq 0 (
    echo [오류] 백엔드 폴더를 찾을 수 없습니다: %BACKEND_PATH%
    pause
    exit /b 1
)

:: 가상환경 활성화
echo [1/2] Python 가상환경 활성화 중...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate
    echo [OK] 가상환경 활성화 완료!
) else (
    echo [경고] 가상환경이 없습니다. 전역 Python을 사용합니다.
)
echo.

:: 서버 시작
echo [2/2] 백엔드 서버 시작 중...
echo.
echo   서버 주소: http://localhost:8001
echo   API 문서:  http://localhost:8001/docs
echo.
echo   종료하려면 Ctrl+C를 누르세요.
echo ================================================
echo.

python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload

pause
