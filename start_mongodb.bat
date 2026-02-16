@echo off
chcp 65001 > nul
title GVIC - MongoDB 시작

echo ========================================
echo   MongoDB 시작
echo ========================================
echo.

:: 데이터 폴더 생성
if not exist "C:\data\db" (
    echo 데이터 폴더 생성 중...
    mkdir "C:\data\db"
)

:: MongoDB 실행
echo MongoDB 서버 시작 중...
echo 이 창을 닫지 마세요!
echo.
echo 종료하려면 Ctrl+C를 누르세요.
echo ========================================
echo.

mongod --dbpath "C:\data\db"

pause
