@echo off
chcp 65001 > nul
echo ========================================
echo   GVIC 진단 도구
echo ========================================
echo.

echo 진단 결과를 D:\gvic\diagnostic.txt 에 저장합니다.
echo.

(
    echo ========================================
    echo   GVIC 진단 결과
    echo   %date% %time%
    echo ========================================
    echo.
    
    echo [1] Python 확인:
    python --version 2>&1
    where python 2>&1
    echo.
    
    echo [2] Node.js 확인:
    node --version 2>&1
    where node 2>&1
    echo.
    
    echo [3] npm 확인:
    npm --version 2>&1
    echo.
    
    echo [4] MongoDB 확인:
    mongod --version 2>&1
    where mongod 2>&1
    echo.
    
    echo [5] 폴더 구조 확인:
    echo D:\gvic 폴더 내용:
    dir /b D:\gvic 2>&1
    echo.
    
    echo D:\gvic\backend 폴더:
    dir /b D:\gvic\backend 2>&1
    echo.
    
    echo D:\gvic\frontend 폴더:
    dir /b D:\gvic\frontend 2>&1
    echo.
    
    echo [6] .env 파일 확인:
    echo backend\.env:
    if exist D:\gvic\backend\.env (
        type D:\gvic\backend\.env
    ) else (
        echo 파일 없음
    )
    echo.
    
    echo frontend\.env:
    if exist D:\gvic\frontend\.env (
        type D:\gvic\frontend\.env
    ) else (
        echo 파일 없음
    )
    echo.
    
    echo [7] venv 폴더 확인:
    if exist D:\gvic\backend\venv (
        echo backend\venv 존재함
    ) else (
        echo backend\venv 없음
    )
    echo.
    
    echo [8] node_modules 폴더 확인:
    if exist D:\gvic\frontend\node_modules (
        echo frontend\node_modules 존재함
    ) else (
        echo frontend\node_modules 없음
    )
    echo.
    
    echo ========================================
    echo   진단 완료
    echo ========================================
) > D:\gvic\diagnostic.txt 2>&1

echo.
echo ========== 진단 결과 ==========
echo.
type D:\gvic\diagnostic.txt
echo.
echo ================================
echo.
echo 위 내용이 D:\gvic\diagnostic.txt 에 저장되었습니다.
echo.
echo 아무 키나 누르면 종료됩니다...
pause > nul
