@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion
title GVIC Seller Intelligence Hub

:: 색상 설정
color 0A

:MENU
cls
echo.
echo  ╔══════════════════════════════════════════════════════════════╗
echo  ║                                                              ║
echo  ║     ██████╗ ██╗   ██╗██╗ ██████╗    ██╗  ██╗██╗   ██╗██████╗ ║
echo  ║    ██╔════╝ ██║   ██║██║██╔════╝    ██║  ██║██║   ██║██╔══██╗║
echo  ║    ██║  ███╗██║   ██║██║██║         ███████║██║   ██║██████╔╝║
echo  ║    ██║   ██║╚██╗ ██╔╝██║██║         ██╔══██║██║   ██║██╔══██╗║
echo  ║    ╚██████╔╝ ╚████╔╝ ██║╚██████╗    ██║  ██║╚██████╔╝██████╔╝║
echo  ║     ╚═════╝   ╚═══╝  ╚═╝ ╚═════╝    ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ║
echo  ║                                                              ║
echo  ║            Seller Intelligence Hub v4.0.0                    ║
echo  ║                                                              ║
echo  ╚══════════════════════════════════════════════════════════════╝
echo.
echo   ┌─────────────────────────────────────────────────────────────┐
echo   │                        메인 메뉴                            │
echo   ├─────────────────────────────────────────────────────────────┤
echo   │                                                             │
echo   │    [1] 🚀 전체 시작 (백엔드 + 프론트엔드)                   │
echo   │                                                             │
echo   │    [2] ⚙️  백엔드만 시작                                     │
echo   │                                                             │
echo   │    [3] 🖥️  프론트엔드만 시작                                 │
echo   │                                                             │
echo   │    [4] 🛑 전체 중지                                         │
echo   │                                                             │
echo   │    [5] 📊 서비스 상태 확인                                  │
echo   │                                                             │
echo   │    [6] 🔧 초기 설치 (최초 1회)                              │
echo   │                                                             │
echo   │    [7] 🌐 브라우저에서 열기                                 │
echo   │                                                             │
echo   │    [8] 📝 로그 보기                                         │
echo   │                                                             │
echo   │    [9] 🍃 MongoDB 시작                                       │
echo   │                                                             │
echo   │    [0] ❌ 종료                                              │
echo   │                                                             │
echo   └─────────────────────────────────────────────────────────────┘
echo.
set /p choice="  선택하세요 [0-8]: "

if "%choice%"=="1" goto START_ALL
if "%choice%"=="2" goto START_BACKEND
if "%choice%"=="3" goto START_FRONTEND
if "%choice%"=="4" goto STOP_ALL
if "%choice%"=="5" goto CHECK_STATUS
if "%choice%"=="6" goto INSTALL
if "%choice%"=="7" goto OPEN_BROWSER
if "%choice%"=="8" goto VIEW_LOGS
if "%choice%"=="0" goto EXIT
goto MENU

:START_ALL
cls
echo.
echo  ════════════════════════════════════════════════════════════════
echo    GVIC 전체 서비스 시작
echo  ════════════════════════════════════════════════════════════════
echo.

:: MongoDB 확인
echo  [1/3] MongoDB 연결 확인 중...
mongod --version > nul 2>&1
if errorlevel 1 (
    echo        ! MongoDB가 설치되지 않았습니다.
    echo        ! MongoDB Atlas 또는 로컬 MongoDB를 설정해주세요.
) else (
    echo        ✓ MongoDB 발견
)

:: 백엔드 시작
echo.
echo  [2/3] 백엔드 서버 시작 중...
cd /d "%~dp0backend"
if exist "venv\Scripts\activate.bat" (
    start "GVIC-Backend" cmd /c "call venv\Scripts\activate.bat && python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload"
    echo        ✓ 백엔드 시작됨 (http://localhost:8001)
) else (
    echo        ✗ 가상환경이 없습니다. [6]번 설치를 먼저 실행하세요.
    pause
    goto MENU
)

:: 잠시 대기
timeout /t 3 /nobreak > nul

:: 프론트엔드 시작
echo.
echo  [3/3] 프론트엔드 서버 시작 중...
cd /d "%~dp0frontend"
start "GVIC-Frontend" cmd /c "npm start"
echo        ✓ 프론트엔드 시작됨 (http://localhost:3000)

echo.
echo  ════════════════════════════════════════════════════════════════
echo    모든 서비스가 시작되었습니다!
echo  ════════════════════════════════════════════════════════════════
echo.
echo    • 프론트엔드: http://localhost:3000
echo    • 백엔드 API: http://localhost:8001
echo    • API 문서:   http://localhost:8001/docs
echo.
echo    테스트 계정:
echo      Email:    admin@gvic.com
echo      Password: gvicgvic!
echo.

timeout /t 5 /nobreak > nul
start http://localhost:3000

echo  아무 키나 누르면 메뉴로 돌아갑니다...
pause > nul
goto MENU

:START_BACKEND
cls
echo.
echo  ════════════════════════════════════════════════════════════════
echo    백엔드 서버 시작
echo  ════════════════════════════════════════════════════════════════
echo.
cd /d "%~dp0backend"
if exist "venv\Scripts\activate.bat" (
    start "GVIC-Backend" cmd /c "call venv\Scripts\activate.bat && python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload"
    echo    ✓ 백엔드 서버가 새 창에서 시작되었습니다.
    echo    • URL: http://localhost:8001
    echo    • API 문서: http://localhost:8001/docs
) else (
    echo    ✗ 가상환경이 없습니다. [6]번 설치를 먼저 실행하세요.
)
echo.
pause
goto MENU

:START_FRONTEND
cls
echo.
echo  ════════════════════════════════════════════════════════════════
echo    프론트엔드 서버 시작
echo  ════════════════════════════════════════════════════════════════
echo.
cd /d "%~dp0frontend"
start "GVIC-Frontend" cmd /c "npm start"
echo    ✓ 프론트엔드 서버가 새 창에서 시작되었습니다.
echo    • URL: http://localhost:3000
echo.
pause
goto MENU

:STOP_ALL
cls
echo.
echo  ════════════════════════════════════════════════════════════════
echo    모든 서비스 중지
echo  ════════════════════════════════════════════════════════════════
echo.
echo    백엔드 서버 종료 중...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr :8001 ^| findstr LISTENING') do (
    taskkill /PID %%a /F > nul 2>&1
    echo    ✓ 백엔드 (PID: %%a) 종료됨
)

echo    프론트엔드 서버 종료 중...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr :3000 ^| findstr LISTENING') do (
    taskkill /PID %%a /F > nul 2>&1
    echo    ✓ 프론트엔드 (PID: %%a) 종료됨
)

:: node 프로세스 정리
taskkill /IM node.exe /F > nul 2>&1

echo.
echo    ✓ 모든 서비스가 중지되었습니다.
echo.
pause
goto MENU

:CHECK_STATUS
cls
echo.
echo  ════════════════════════════════════════════════════════════════
echo    서비스 상태 확인
echo  ════════════════════════════════════════════════════════════════
echo.

:: 백엔드 확인
echo    [백엔드 서버 - Port 8001]
netstat -ano 2>nul | findstr :8001 | findstr LISTENING > nul
if errorlevel 1 (
    echo      상태: ❌ 중지됨
) else (
    echo      상태: ✅ 실행 중
    curl -s http://localhost:8001/health > nul 2>&1
    if errorlevel 1 (
        echo      헬스: ⚠️ 응답 없음
    ) else (
        echo      헬스: ✅ 정상
    )
)
echo.

:: 프론트엔드 확인
echo    [프론트엔드 서버 - Port 3000]
netstat -ano 2>nul | findstr :3000 | findstr LISTENING > nul
if errorlevel 1 (
    echo      상태: ❌ 중지됨
) else (
    echo      상태: ✅ 실행 중
)
echo.

:: MongoDB 확인
echo    [MongoDB - Port 27017]
netstat -ano 2>nul | findstr :27017 | findstr LISTENING > nul
if errorlevel 1 (
    echo      상태: ❌ 중지됨 (또는 Atlas 사용 중)
) else (
    echo      상태: ✅ 실행 중
)
echo.
pause
goto MENU

:INSTALL
cls
echo.
echo  ════════════════════════════════════════════════════════════════
echo    GVIC 초기 설치
echo  ════════════════════════════════════════════════════════════════
echo.

:: Python 확인
echo  [1/5] Python 확인 중...
python --version > nul 2>&1
if errorlevel 1 (
    echo        ✗ Python이 설치되어 있지 않습니다.
    echo          https://www.python.org/downloads/ 에서 설치하세요.
    pause
    goto MENU
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo        ✓ Python %%i

:: Node.js 확인
echo  [2/5] Node.js 확인 중...
node --version > nul 2>&1
if errorlevel 1 (
    echo        ✗ Node.js가 설치되어 있지 않습니다.
    echo          https://nodejs.org/ 에서 설치하세요.
    pause
    goto MENU
)
for /f %%i in ('node --version') do echo        ✓ Node.js %%i

:: 백엔드 가상환경 생성
echo.
echo  [3/5] 백엔드 가상환경 생성 중...
cd /d "%~dp0backend"
if not exist "venv" (
    python -m venv venv
    echo        ✓ 가상환경 생성됨
) else (
    echo        ! 가상환경이 이미 존재함
)

:: 백엔드 패키지 설치
echo.
echo  [4/5] 백엔드 패키지 설치 중... (2-3분 소요)
call venv\Scripts\activate.bat
pip install --upgrade pip > nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo        ✗ 백엔드 패키지 설치 실패
    pause
    goto MENU
)
echo        ✓ 백엔드 패키지 설치 완료

:: 프론트엔드 패키지 설치
echo.
echo  [5/5] 프론트엔드 패키지 설치 중... (3-5분 소요)
cd /d "%~dp0frontend"
call npm install
if errorlevel 1 (
    echo        ✗ 프론트엔드 패키지 설치 실패
    pause
    goto MENU
)
echo        ✓ 프론트엔드 패키지 설치 완료

:: 환경변수 설정
echo.
echo  환경변수 파일 생성 중...
cd /d "%~dp0backend"
if not exist ".env" (
    (
        echo MONGO_URL=mongodb://localhost:27017
        echo DB_NAME=gvic_database
        echo CORS_ORIGINS=http://localhost:3000
        echo JWT_SECRET_KEY=change-this-secret-key-in-production
        echo STRIPE_API_KEY=sk_test_your_stripe_key
    ) > .env
    echo        ✓ backend/.env 생성됨
)

cd /d "%~dp0frontend"
if not exist ".env" (
    echo REACT_APP_BACKEND_URL=http://localhost:8001> .env
    echo        ✓ frontend/.env 생성됨
)

echo.
echo  ════════════════════════════════════════════════════════════════
echo    ✓ 설치가 완료되었습니다!
echo  ════════════════════════════════════════════════════════════════
echo.
echo    [1]번을 눌러 서비스를 시작하세요.
echo.
pause
goto MENU

:OPEN_BROWSER
start http://localhost:3000
goto MENU

:VIEW_LOGS
cls
echo.
echo  ════════════════════════════════════════════════════════════════
echo    로그 보기
echo  ════════════════════════════════════════════════════════════════
echo.
echo    [1] 백엔드 로그 (새 창)
echo    [2] 백엔드 API 문서 열기
echo    [0] 메뉴로 돌아가기
echo.
set /p logchoice="  선택하세요 [0-2]: "

if "%logchoice%"=="1" (
    cd /d "%~dp0backend"
    if exist "logs" (
        start notepad logs\app.log
    ) else (
        echo    로그 파일이 없습니다.
        pause
    )
)
if "%logchoice%"=="2" start http://localhost:8001/docs
goto MENU

:EXIT
cls
echo.
echo  ════════════════════════════════════════════════════════════════
echo    GVIC를 종료합니다. 감사합니다!
echo  ════════════════════════════════════════════════════════════════
echo.
timeout /t 2 /nobreak > nul
exit /b 0
