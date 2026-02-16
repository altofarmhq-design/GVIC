@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ========================================
echo   GVIC Seller Intelligence Hub 설치
echo ========================================
echo.

set "INSTALL_DIR=%~dp0"
echo 설치 경로: %INSTALL_DIR%
echo.

:: 필수 프로그램 확인
echo [1/7] 필수 프로그램 확인 중...
echo.

:: Python 확인
python --version > nul 2>&1
if errorlevel 1 (
    echo   [오류] Python이 설치되어 있지 않습니다.
    echo   Python 3.10 이상을 설치해주세요: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
echo   [OK] Python %PYTHON_VER%

:: Node.js 확인
node --version > nul 2>&1
if errorlevel 1 (
    echo   [오류] Node.js가 설치되어 있지 않습니다.
    echo   Node.js 18 이상을 설치해주세요: https://nodejs.org/
    echo.
    pause
    exit /b 1
)
for /f %%i in ('node --version') do set NODE_VER=%%i
echo   [OK] Node.js %NODE_VER%

:: MongoDB 확인
echo.
echo [2/7] MongoDB 확인 중...
mongod --version > nul 2>&1
if errorlevel 1 (
    echo   [경고] MongoDB가 설치되어 있지 않습니다.
    echo.
    echo   두 가지 옵션이 있습니다:
    echo   1. MongoDB 로컬 설치: https://www.mongodb.com/try/download/community
    echo   2. MongoDB Atlas 클라우드 사용 (무료): https://www.mongodb.com/atlas
    echo.
    echo   Atlas 사용 시 backend/.env 파일의 MONGO_URL을 수정하세요.
    echo.
) else (
    echo   [OK] MongoDB 발견
)

:: 백엔드 가상환경 생성
echo.
echo [3/7] 백엔드 가상환경 생성 중...
cd /d "%INSTALL_DIR%backend"
if not exist "venv" (
    python -m venv venv
    if errorlevel 1 (
        echo   [오류] 가상환경 생성 실패
        pause
        exit /b 1
    )
    echo   [OK] 가상환경 생성됨
) else (
    echo   [OK] 가상환경이 이미 존재함
)

:: 백엔드 패키지 설치
echo.
echo [4/7] 백엔드 패키지 설치 중... (2-3분 소요)
call venv\Scripts\activate.bat
pip install --upgrade pip > nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo   [오류] 백엔드 패키지 설치 실패
    pause
    exit /b 1
)
echo   [OK] 백엔드 패키지 설치 완료

:: 프론트엔드 패키지 설치
echo.
echo [5/7] 프론트엔드 패키지 설치 중... (3-5분 소요)
cd /d "%INSTALL_DIR%frontend"
call npm install
if errorlevel 1 (
    echo   npm 실패, yarn 시도 중...
    call yarn install
)
echo   [OK] 프론트엔드 패키지 설치 완료

:: 환경변수 파일 생성
echo.
echo [6/7] 환경변수 파일 생성 중...

cd /d "%INSTALL_DIR%backend"
if not exist ".env" (
    (
        echo MONGO_URL=mongodb://localhost:27017
        echo DB_NAME=gvic_database
        echo CORS_ORIGINS=http://localhost:3000
        echo JWT_SECRET_KEY=gvic-local-secret-key-change-in-production
        echo STRIPE_API_KEY=sk_test_your_stripe_key
    ) > .env
    echo   [OK] backend/.env 생성됨
) else (
    echo   [OK] backend/.env 이미 존재함
)

cd /d "%INSTALL_DIR%frontend"
if not exist ".env" (
    echo REACT_APP_BACKEND_URL=http://localhost:8001> .env
    echo   [OK] frontend/.env 생성됨
) else (
    echo   [OK] frontend/.env 이미 존재함
)

:: MongoDB 초기 데이터 생성
echo.
echo [7/7] MongoDB 초기 데이터 설정...
cd /d "%INSTALL_DIR%backend"
call venv\Scripts\activate.bat
python init_db.py
if errorlevel 1 (
    echo   [경고] MongoDB 초기화 실패 - MongoDB가 실행 중인지 확인하세요
) else (
    echo   [OK] MongoDB 초기 데이터 생성 완료
)

:: 완료
echo.
echo ========================================
echo   설치가 완료되었습니다!
echo ========================================
echo.
echo 다음 단계:
echo.
echo 1. MongoDB 시작 (로컬 사용 시):
echo    mongod --dbpath "C:\data\db"
echo.
echo 2. gvicrun.bat 실행하여 서비스 시작
echo.
echo 3. 브라우저에서 http://localhost:3000 접속
echo.
echo 테스트 계정:
echo   Email:    admin@gvic.com
echo   Password: gvicgvic!
echo.
echo ========================================
echo.

cd /d "%INSTALL_DIR%"
echo 아무 키나 누르면 종료됩니다...
pause > nul
