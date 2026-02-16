@echo off
echo ========================================
echo   GVIC Install
echo ========================================
echo.

set "INSTALL_DIR=%~dp0"
echo Install path: %INSTALL_DIR%
echo.

echo [1/5] Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found
    pause
    exit /b 1
)

echo.
echo [2/5] Checking Node.js...
node --version
if errorlevel 1 (
    echo ERROR: Node.js not found
    pause
    exit /b 1
)

echo.
echo [3/5] Creating Python venv...
cd /d "%INSTALL_DIR%backend"
if not exist "venv" (
    python -m venv venv
    echo venv created
) else (
    echo venv already exists
)

echo.
echo [4/5] Installing backend packages... (2-3 min)
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: pip install failed
    pause
    exit /b 1
)
echo Backend packages installed

echo.
echo [5/5] Installing frontend packages... (3-5 min)
cd /d "%INSTALL_DIR%frontend"
call npm install
if errorlevel 1 (
    echo Trying yarn...
    call yarn install
)
echo Frontend packages installed

echo.
echo Creating .env files...
cd /d "%INSTALL_DIR%backend"
if not exist ".env" (
    echo MONGO_URL=mongodb://localhost:27017> .env
    echo DB_NAME=gvic_database>> .env
    echo CORS_ORIGINS=http://localhost:3000>> .env
    echo JWT_SECRET_KEY=gvic-secret-key>> .env
    echo backend/.env created
)

cd /d "%INSTALL_DIR%frontend"
if not exist ".env" (
    echo REACT_APP_BACKEND_URL=http://localhost:8001> .env
    echo frontend/.env created
)

echo.
echo ========================================
echo   Install Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Run start_backend.bat
echo 2. Run start_frontend.bat
echo 3. Open http://localhost:3000
echo.
echo Test account:
echo   Email: admin@gvic.com
echo   Password: gvicgvic!
echo.
cd /d "%INSTALL_DIR%"
pause
