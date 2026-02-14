@echo off
chcp 65001 > nul
title GVIC Engine - 상태 확인

echo ================================================
echo     GVIC Engine 시스템 상태 확인
echo ================================================
echo.

:: MongoDB 상태 확인
echo [1/3] MongoDB 상태 확인...
mongosh --eval "db.adminCommand('ping')" > nul 2>&1
if %errorlevel% equ 0 (
    echo   [실행중] MongoDB가 정상 작동 중입니다.
) else (
    echo   [중지됨] MongoDB가 실행되지 않았습니다.
)
echo.

:: 백엔드 상태 확인
echo [2/3] 백엔드 서버 상태 확인...
curl -s http://localhost:8001/ > nul 2>&1
if %errorlevel% equ 0 (
    echo   [실행중] 백엔드 서버 (http://localhost:8001)
) else (
    echo   [중지됨] 백엔드 서버가 응답하지 않습니다.
)
echo.

:: 프론트엔드 상태 확인
echo [3/3] 프론트엔드 서버 상태 확인...
curl -s http://localhost:3000/ > nul 2>&1
if %errorlevel% equ 0 (
    echo   [실행중] 프론트엔드 서버 (http://localhost:3000)
) else (
    echo   [중지됨] 프론트엔드 서버가 응답하지 않습니다.
)
echo.

echo ================================================
echo     상태 확인 완료
echo ================================================
echo.

:: 포트 사용 현황
echo [추가 정보] 포트 사용 현황:
echo ------------------------------------------------
netstat -ano | findstr ":8001 :3000 :27017" 2>nul
echo.

pause
