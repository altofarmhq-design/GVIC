@echo off
chcp 65001 > nul
title GVIC Engine - 시스템 종료

echo ================================================
echo     GVIC Engine 시스템 종료
echo ================================================
echo.

echo [1/2] Node.js 프로세스 종료 중...
taskkill /f /im node.exe > nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Node.js 프로세스 종료됨
) else (
    echo [정보] 실행 중인 Node.js 프로세스 없음
)
echo.

echo [2/2] Python/Uvicorn 프로세스 종료 중...
taskkill /f /im python.exe > nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Python 프로세스 종료됨
) else (
    echo [정보] 실행 중인 Python 프로세스 없음
)
echo.

echo ================================================
echo     모든 서비스가 종료되었습니다.
echo ================================================
echo.
pause
