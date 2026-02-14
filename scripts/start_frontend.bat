@echo off
chcp 65001 > nul
title GVIC Engine - 프론트엔드 서버

echo ================================================
echo     GVIC Engine 프론트엔드 서버 시작
echo ================================================
echo.

:: 프로젝트 경로 설정
set PROJECT_ROOT=C:\GVIC
set FRONTEND_PATH=%PROJECT_ROOT%\frontend

:: 프론트엔드 폴더로 이동
cd /d %FRONTEND_PATH%
if %errorlevel% neq 0 (
    echo [오류] 프론트엔드 폴더를 찾을 수 없습니다: %FRONTEND_PATH%
    pause
    exit /b 1
)

:: Node.js 확인
echo [1/2] Node.js 확인 중...
node --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [오류] Node.js가 설치되지 않았습니다.
    echo https://nodejs.org 에서 설치해주세요.
    pause
    exit /b 1
)
echo [OK] Node.js 확인 완료!
echo.

:: 서버 시작
echo [2/2] 프론트엔드 서버 시작 중...
echo.
echo   서버 주소: http://localhost:3000
echo.
echo   종료하려면 Ctrl+C를 누르세요.
echo ================================================
echo.

yarn start

pause
