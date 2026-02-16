@echo off
chcp 65001 > nul
title GVIC Engine - 의존성 설치

echo ================================================
echo     GVIC Engine 의존성 설치
echo ================================================
echo.

:: 프로젝트 경로 설정 (스크립트 위치 기반 자동 설정)
set "PROJECT_ROOT=%~dp0.."

echo [단계 1/4] 백엔드 Python 가상환경 생성...
echo ------------------------------------------------
cd /d %PROJECT_ROOT%\backend

if exist "venv" (
    echo [정보] 가상환경이 이미 존재합니다. 건너뜁니다.
) else (
    echo 가상환경 생성 중...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [오류] 가상환경 생성 실패
        pause
        exit /b 1
    )
    echo [OK] 가상환경 생성 완료!
)
echo.

echo [단계 2/4] 백엔드 Python 패키지 설치...
echo ------------------------------------------------
call venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [경고] 일부 패키지 설치에 실패했을 수 있습니다.
    echo 오류 메시지를 확인해주세요.
) else (
    echo [OK] 백엔드 패키지 설치 완료!
)
echo.

echo [단계 3/4] 프론트엔드 폴더로 이동...
echo ------------------------------------------------
cd /d %PROJECT_ROOT%\frontend
if %errorlevel% neq 0 (
    echo [오류] 프론트엔드 폴더를 찾을 수 없습니다.
    pause
    exit /b 1
)
echo.

echo [단계 4/4] 프론트엔드 Node.js 패키지 설치...
echo ------------------------------------------------
echo (이 과정은 몇 분이 소요될 수 있습니다)
echo.
yarn install
if %errorlevel% neq 0 (
    echo [경고] 패키지 설치 중 오류가 발생했습니다.
    echo npm을 사용해 재시도합니다...
    npm install
)
echo.

echo ================================================
echo     설치 완료!
echo ================================================
echo.
echo 다음 단계:
echo   1. MongoDB가 실행 중인지 확인하세요.
echo   2. start_all.bat 를 실행하여 시스템을 시작하세요.
echo.
pause
