@echo off
echo ===============================================
echo    Genealogy Tree Creator - Full Stack Startup
echo ===============================================
echo.

echo Checking Docker installation...
docker --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Docker is not installed or not running.
    echo Please install Docker Desktop and make sure it's running.
    pause
    exit /b 1
)

echo Checking Docker Compose installation...
docker-compose --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Docker Compose is not installed.
    echo Please install Docker Compose.
    pause
    exit /b 1
)

echo.
echo Building and starting all services...
echo This may take a few minutes on first run...
echo.

REM Build and start all services
docker-compose up --build

echo.
echo ===============================================
echo Services should now be running on:
echo ===============================================
echo Frontend:           http://localhost:3000
echo Family Tree API:     http://localhost:8000
echo Language Tree API:   http://localhost:8001
echo Species Tree API:    http://localhost:8002
echo ===============================================

pause
