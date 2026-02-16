@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ========================================
echo   GVIC Seller Intelligence Hub 설치
echo   로컬 환경 설정 스크립트
echo ========================================
echo.

:: 설치 경로 확인
set "INSTALL_DIR=%~dp0"
echo 설치 경로: %INSTALL_DIR%
echo.

:: 필수 프로그램 확인
echo [1/6] 필수 프로그램 확인 중...
echo.

:: Python 확인
python --version > nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되어 있지 않습니다.
    echo Python 3.10 이상을 설치해주세요: https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
echo   ✓ Python %PYTHON_VER% 발견

:: Node.js 확인
node --version > nul 2>&1
if errorlevel 1 (
    echo [오류] Node.js가 설치되어 있지 않습니다.
    echo Node.js 18 이상을 설치해주세요: https://nodejs.org/
    pause
    exit /b 1
)
for /f %%i in ('node --version') do set NODE_VER=%%i
echo   ✓ Node.js %NODE_VER% 발견

:: MongoDB 확인 (선택사항)
mongod --version > nul 2>&1
if errorlevel 1 (
    echo   ! MongoDB가 설치되어 있지 않습니다.
    echo     MongoDB를 설치하거나 MongoDB Atlas를 사용하세요.
    echo     https://www.mongodb.com/try/download/community
) else (
    echo   ✓ MongoDB 발견
)
echo.

:: 백엔드 설정
echo [2/6] 백엔드 의존성 설치 중...
cd "%INSTALL_DIR%backend"

:: 가상환경 생성
if not exist "venv" (
    echo   가상환경 생성 중...
    python -m venv venv
)

:: 가상환경 활성화 및 패키지 설치
call venv\Scripts\activate.bat
echo   패키지 설치 중... (약 2-3분 소요)
pip install --upgrade pip > nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo [오류] 백엔드 패키지 설치 실패
    pause
    exit /b 1
)
echo   ✓ 백엔드 의존성 설치 완료
echo.

:: 프론트엔드 설정
echo [3/6] 프론트엔드 의존성 설치 중...
cd "%INSTALL_DIR%frontend"
echo   패키지 설치 중... (약 3-5분 소요)
call npm install
if errorlevel 1 (
    call yarn install
)
echo   ✓ 프론트엔드 의존성 설치 완료
echo.

:: 환경변수 설정
echo [4/6] 환경변수 설정 중...

:: 백엔드 .env
cd "%INSTALL_DIR%backend"
if not exist ".env" (
    echo MONGO_URL=mongodb://localhost:27017> .env
    echo DB_NAME=gvic_database>> .env
    echo CORS_ORIGINS=http://localhost:3000>> .env
    echo JWT_SECRET_KEY=your-secret-key-change-in-production>> .env
    echo # Stripe 테스트 키 (실제 키로 교체 필요)>> .env
    echo STRIPE_API_KEY=sk_test_your_stripe_key>> .env
    echo # 한국 결제 (선택사항)>> .env
    echo # KAKAOPAY_ADMIN_KEY=your_kakaopay_key>> .env
    echo # NAVERPAY_CLIENT_ID=your_naverpay_id>> .env
    echo # TOSS_CLIENT_KEY=your_toss_key>> .env
    echo   ✓ backend/.env 생성됨
) else (
    echo   ! backend/.env 이미 존재함
)

:: 프론트엔드 .env
cd "%INSTALL_DIR%frontend"
if not exist ".env" (
    echo REACT_APP_BACKEND_URL=http://localhost:8001> .env
    echo   ✓ frontend/.env 생성됨
) else (
    echo   ! frontend/.env 이미 존재함
)
echo.

:: 데이터 디렉토리 생성
echo [5/6] 데이터 디렉토리 생성 중...
cd "%INSTALL_DIR%backend"
if not exist "data" mkdir data
if not exist "config" mkdir config
echo   ✓ 디렉토리 생성 완료
echo.

:: 완료
echo [6/6] 설치 완료!
echo.
echo ========================================
echo   설치가 완료되었습니다!
echo ========================================
echo.
echo 다음 단계:
echo.
echo 1. MongoDB 시작 (로컬 MongoDB 사용 시)
echo    mongod --dbpath "C:\data\db"
echo.
echo 2. 백엔드 시작: start_backend.bat 실행
echo 3. 프론트엔드 시작: start_frontend.bat 실행
echo.
echo 4. 브라우저에서 접속: http://localhost:3000
echo.
echo 테스트 계정:
echo   Email: admin@gvic.com
echo   Password: gvicgvic!
echo.
echo ========================================
echo.

cd "%INSTALL_DIR%"
pause
