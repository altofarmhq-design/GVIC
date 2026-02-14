@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║     GVIC 엔진 대시보드 - 전체 설치 스크립트              ║
echo ║     Version: 2026-02-14                                    ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

:: 현재 디렉토리 확인
set "ROOT_DIR=%~dp0.."
cd /d "%ROOT_DIR%"
echo [INFO] 프로젝트 루트: %ROOT_DIR%
echo.

:: ==================== 사전 요구사항 확인 ====================
echo [1/6] 사전 요구사항 확인 중...

:: Python 확인
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python이 설치되지 않았습니다.
    echo         https://www.python.org/downloads/ 에서 설치하세요.
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
echo        Python: %PYTHON_VER% ✓

:: Node.js 확인
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js가 설치되지 않았습니다.
    echo         https://nodejs.org/ 에서 설치하세요.
    pause
    exit /b 1
)
for /f %%i in ('node --version') do set NODE_VER=%%i
echo        Node.js: %NODE_VER% ✓

:: MongoDB 확인
mongod --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] MongoDB가 PATH에 없습니다. 수동으로 시작해야 할 수 있습니다.
) else (
    echo        MongoDB: 설치됨 ✓
)

echo.

:: ==================== 백엔드 설치 ====================
echo [2/6] 백엔드 설치 중...
cd /d "%ROOT_DIR%\backend"

:: 가상환경 생성
if not exist "venv" (
    echo        가상환경 생성 중...
    python -m venv venv
)

:: 가상환경 활성화 및 패키지 설치
echo        패키지 설치 중...
call venv\Scripts\activate.bat

:: pip 업그레이드
python -m pip install --upgrade pip >nul 2>&1

:: emergentintegrations 설치 (특수 인덱스)
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/ >nul 2>&1

:: 나머지 패키지 설치
pip install -r requirements.txt >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 백엔드 패키지 설치 실패
    pause
    exit /b 1
)
echo        백엔드 패키지 설치 완료 ✓

:: .env 파일 확인
if not exist ".env" (
    echo        .env 파일 생성 중...
    (
        echo MONGO_URL=mongodb://localhost:27017
        echo DB_NAME=gvic_engine
        echo EMERGENT_LLM_KEY=your_emergent_llm_key_here
    ) > .env
    echo [WARN] backend/.env 파일에 EMERGENT_LLM_KEY를 설정하세요!
)

cd /d "%ROOT_DIR%"
echo.

:: ==================== 프론트엔드 설치 ====================
echo [3/6] 프론트엔드 설치 중...
cd /d "%ROOT_DIR%\frontend"

:: node_modules 확인
if not exist "node_modules" (
    echo        npm 패키지 설치 중... (시간이 걸릴 수 있습니다)
    call npm install >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] 프론트엔드 패키지 설치 실패
        pause
        exit /b 1
    )
) else (
    echo        node_modules 존재 - 스킵
)

:: .env 파일 확인
if not exist ".env" (
    echo        .env 파일 생성 중...
    echo REACT_APP_BACKEND_URL=http://localhost:8001 > .env
)

echo        프론트엔드 패키지 설치 완료 ✓

cd /d "%ROOT_DIR%"
echo.

:: ==================== MongoDB 데이터 디렉토리 ====================
echo [4/6] MongoDB 데이터 디렉토리 확인...
if not exist "C:\data\db" (
    echo        C:\data\db 생성 중...
    mkdir "C:\data\db" 2>nul
)
echo        MongoDB 데이터 디렉토리 준비 완료 ✓
echo.

:: ==================== 한글 폰트 확인 ====================
echo [5/6] PDF 한글 폰트 확인...
set "FONT_DIR=%ROOT_DIR%\backend\fonts"
if not exist "%FONT_DIR%" mkdir "%FONT_DIR%"

if not exist "%FONT_DIR%\NanumGothic.ttf" (
    echo [WARN] 한글 폰트가 없습니다. PDF에서 한글이 깨질 수 있습니다.
    echo        NanumGothic.ttf를 %FONT_DIR%에 복사하세요.
) else (
    echo        한글 폰트 확인 완료 ✓
)
echo.

:: ==================== 설치 완료 ====================
echo [6/6] 설치 완료!
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                    설치가 완료되었습니다!                  ║
echo ╠════════════════════════════════════════════════════════════╣
echo ║                                                            ║
echo ║  다음 단계:                                                ║
echo ║  1. backend\.env 파일에 EMERGENT_LLM_KEY 설정             ║
echo ║  2. scripts\start_all.bat 실행                            ║
echo ║  3. 브라우저에서 http://localhost:3000 접속               ║
echo ║                                                            ║
echo ║  기본 계정: admin@gvic.com / password                     ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
pause
