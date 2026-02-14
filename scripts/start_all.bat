@echo off
chcp 65001 > nul
title GVIC Engine - 전체 시스템 시작

echo ================================================
echo     GVIC Engine 시스템 시작
echo ================================================
echo.

:: 프로젝트 루트 경로 설정
set PROJECT_ROOT=C:\GVIC

:: MongoDB 실행 확인
echo [1/3] MongoDB 연결 확인 중...
mongosh --eval "db.adminCommand('ping')" > nul 2>&1
if %errorlevel% neq 0 (
    echo [경고] MongoDB가 실행되지 않았습니다.
    echo MongoDB를 먼저 시작해주세요.
    echo.
    echo MongoDB 시작 방법:
    echo   1. MongoDB Compass 실행
    echo   2. 또는 'net start MongoDB' 명령 실행 (관리자 권한 필요)
    echo.
    pause
    exit /b 1
)
echo [OK] MongoDB 연결 성공!
echo.

:: 백엔드 서버 시작 (새 창에서)
echo [2/3] 백엔드 서버 시작 중...
start "GVIC Backend" cmd /k "cd /d %PROJECT_ROOT%\backend && call venv\Scripts\activate && python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload"
timeout /t 3 > nul
echo [OK] 백엔드 서버 시작됨 (http://localhost:8001)
echo.

:: 프론트엔드 서버 시작 (새 창에서)
echo [3/3] 프론트엔드 서버 시작 중...
start "GVIC Frontend" cmd /k "cd /d %PROJECT_ROOT%\frontend && yarn start"
timeout /t 3 > nul
echo [OK] 프론트엔드 서버 시작됨 (http://localhost:3000)
echo.

echo ================================================
echo     모든 서비스가 시작되었습니다!
echo ================================================
echo.
echo   - 프론트엔드: http://localhost:3000
echo   - 백엔드 API: http://localhost:8001
echo   - API 문서:   http://localhost:8001/docs
echo.
echo [참고] 서버를 종료하려면 각 창을 닫으세요.
echo.
pause
