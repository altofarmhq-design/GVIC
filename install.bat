@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ========================================
echo   GVIC Seller Intelligence Hub 설치
echo ========================================
echo.

set "INSTALL_DIR=%~dp0"
set "LOG_FILE=%INSTALL_DIR%install_log.txt"

echo 설치 시작: %date% %time% > "%LOG_FILE%"
echo 설치 경로: %INSTALL_DIR% >> "%LOG_FILE%"
echo.

echo 설치 경로: %INSTALL_DIR%
echo 로그 파일: %LOG_FILE%
echo.

:: ========================================
:: 1. Python 확인
:: ========================================
echo [1/7] Python 확인 중...
echo [1/7] Python 확인 >> "%LOG_FILE%"

where python > nul 2>&1
if errorlevel 1 (
    echo   [오류] Python이 설치되어 있지 않습니다!
    echo   [오류] Python 미설치 >> "%LOG_FILE%"
    echo.
    echo   Python 설치 방법:
    echo   1. https://www.python.org/downloads/ 접속
    echo   2. "Download Python 3.x" 클릭
    echo   3. 설치 시 "Add Python to PATH" 반드시 체크!
    echo.
    goto ERROR_END
)

python --version 2>> "%LOG_FILE%"
for /f "tokens=2" %%i in ('python --version 2^>^&1') do (
    echo   [OK] Python %%i
    echo   [OK] Python %%i >> "%LOG_FILE%"
)

:: ========================================
:: 2. Node.js 확인
:: ========================================
echo.
echo [2/7] Node.js 확인 중...
echo [2/7] Node.js 확인 >> "%LOG_FILE%"

where node > nul 2>&1
if errorlevel 1 (
    echo   [오류] Node.js가 설치되어 있지 않습니다!
    echo   [오류] Node.js 미설치 >> "%LOG_FILE%"
    echo.
    echo   Node.js 설치 방법:
    echo   1. https://nodejs.org/ 접속
    echo   2. LTS 버전 다운로드
    echo   3. 설치 진행
    echo.
    goto ERROR_END
)

node --version 2>> "%LOG_FILE%"
for /f %%i in ('node --version 2^>^&1') do (
    echo   [OK] Node.js %%i
    echo   [OK] Node.js %%i >> "%LOG_FILE%"
)

:: ========================================
:: 3. MongoDB 확인 (경고만)
:: ========================================
echo.
echo [3/7] MongoDB 확인 중...
echo [3/7] MongoDB 확인 >> "%LOG_FILE%"

where mongod > nul 2>&1
if errorlevel 1 (
    echo   [경고] MongoDB가 설치되어 있지 않습니다.
    echo   [경고] MongoDB 미설치 >> "%LOG_FILE%"
    echo.
    echo   MongoDB 설치 후 진행하거나, MongoDB Atlas를 사용하세요.
    echo   https://www.mongodb.com/try/download/community
    echo.
) else (
    echo   [OK] MongoDB 발견
    echo   [OK] MongoDB 발견 >> "%LOG_FILE%"
)

:: ========================================
:: 4. 백엔드 가상환경 생성
:: ========================================
echo.
echo [4/7] 백엔드 가상환경 생성 중...
echo [4/7] 백엔드 가상환경 생성 >> "%LOG_FILE%"

cd /d "%INSTALL_DIR%backend"
if errorlevel 1 (
    echo   [오류] backend 폴더를 찾을 수 없습니다!
    echo   [오류] backend 폴더 없음 >> "%LOG_FILE%"
    goto ERROR_END
)

if not exist "venv" (
    echo   가상환경 생성 중...
    python -m venv venv 2>> "%LOG_FILE%"
    if errorlevel 1 (
        echo   [오류] 가상환경 생성 실패!
        echo   [오류] venv 생성 실패 >> "%LOG_FILE%"
        goto ERROR_END
    )
    echo   [OK] 가상환경 생성됨
    echo   [OK] 가상환경 생성됨 >> "%LOG_FILE%"
) else (
    echo   [OK] 가상환경이 이미 존재함
    echo   [OK] 가상환경 존재 >> "%LOG_FILE%"
)

:: ========================================
:: 5. 백엔드 패키지 설치
:: ========================================
echo.
echo [5/7] 백엔드 패키지 설치 중... (2-3분 소요)
echo [5/7] 백엔드 패키지 설치 >> "%LOG_FILE%"

call venv\Scripts\activate.bat 2>> "%LOG_FILE%"
if errorlevel 1 (
    echo   [오류] 가상환경 활성화 실패!
    echo   [오류] venv 활성화 실패 >> "%LOG_FILE%"
    goto ERROR_END
)

pip install --upgrade pip >> "%LOG_FILE%" 2>&1
pip install -r requirements.txt >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo   [오류] 백엔드 패키지 설치 실패!
    echo   [오류] pip install 실패 >> "%LOG_FILE%"
    echo.
    echo   로그 파일을 확인하세요: %LOG_FILE%
    goto ERROR_END
)
echo   [OK] 백엔드 패키지 설치 완료
echo   [OK] 백엔드 패키지 설치 완료 >> "%LOG_FILE%"

:: ========================================
:: 6. 프론트엔드 패키지 설치
:: ========================================
echo.
echo [6/7] 프론트엔드 패키지 설치 중... (3-5분 소요)
echo [6/7] 프론트엔드 패키지 설치 >> "%LOG_FILE%"

cd /d "%INSTALL_DIR%frontend"
if errorlevel 1 (
    echo   [오류] frontend 폴더를 찾을 수 없습니다!
    echo   [오류] frontend 폴더 없음 >> "%LOG_FILE%"
    goto ERROR_END
)

:: npm 시도
call npm install >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo   npm 실패, yarn 시도 중...
    call yarn install >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        echo   [오류] 프론트엔드 패키지 설치 실패!
        echo   [오류] npm/yarn install 실패 >> "%LOG_FILE%"
        goto ERROR_END
    )
)
echo   [OK] 프론트엔드 패키지 설치 완료
echo   [OK] 프론트엔드 패키지 설치 완료 >> "%LOG_FILE%"

:: ========================================
:: 7. 환경변수 파일 생성
:: ========================================
echo.
echo [7/7] 환경변수 파일 생성 중...
echo [7/7] 환경변수 파일 생성 >> "%LOG_FILE%"

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
    echo   [OK] backend/.env 생성 >> "%LOG_FILE%"
) else (
    echo   [OK] backend/.env 이미 존재함
)

cd /d "%INSTALL_DIR%frontend"
if not exist ".env" (
    echo REACT_APP_BACKEND_URL=http://localhost:8001> .env
    echo   [OK] frontend/.env 생성됨
    echo   [OK] frontend/.env 생성 >> "%LOG_FILE%"
) else (
    echo   [OK] frontend/.env 이미 존재함
)

:: ========================================
:: 완료!
:: ========================================
echo.
echo ========================================
echo   설치가 완료되었습니다!
echo ========================================
echo 완료: %date% %time% >> "%LOG_FILE%"
echo.
echo 다음 단계:
echo.
echo 1. gvicrun.bat 실행
echo 2. [9] MongoDB 시작
echo 3. [1] 전체 시작
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
exit /b 0

:ERROR_END
echo.
echo ========================================
echo   [오류] 설치 중 문제가 발생했습니다!
echo ========================================
echo.
echo 로그 파일: %LOG_FILE%
echo.
echo 로그 파일 내용을 확인하시거나,
echo 아래 사항을 점검해주세요:
echo.
echo 1. Python이 PATH에 등록되어 있는지
echo 2. Node.js가 설치되어 있는지
echo 3. 인터넷 연결이 정상인지
echo.
echo ========================================
echo.
echo 아무 키나 누르면 종료됩니다...
pause > nul
exit /b 1
