@echo off
REM Double-click to start Polymer with its graphical interface (Windows).
setlocal

cd /d "%~dp0\.."
for %%I in ("%cd%\..") do set "REPO_ROOT=%%~fI"
cd /d "%REPO_ROOT%"

echo ======================================================
echo   Polymer - starting the container
echo   Folder: %REPO_ROOT%
echo ======================================================
echo.

where docker >nul 2>&1
if errorlevel 1 (
  echo Docker is not installed. Download it from:
  echo   https://www.docker.com/products/docker-desktop/
  echo.
  pause
  exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
  echo Docker is installed but not running.
  echo Open "Docker Desktop", wait until it is ready, then try again.
  echo.
  pause
  exit /b 1
)

if not exist data\input      mkdir data\input
if not exist data\output     mkdir data\output
if not exist data\auxdata    mkdir data\auxdata
if not exist data\ancillary  mkdir data\ancillary
if not exist data\config     mkdir data\config

REM Let the interface show the folder paths as they are on this computer.
set "POLYMER_HOST_DIR=%REPO_ROOT%\data"

echo.
echo Building / starting. The FIRST run takes 10-20 minutes.
echo.
docker compose -f docker/docker-compose.yml up -d --build
if errorlevel 1 (
  echo.
  echo Startup failed. Check the messages above.
  pause
  exit /b 1
)

echo.
echo Waiting for the interface to be ready...
set /a _tries=0
:waitloop
for /f "tokens=*" %%h in ('docker inspect -f "{{.State.Health.Status}}" polymer-gui 2^>nul') do set "_hs=%%h"
if "%_hs%"=="healthy" goto ready
set /a _tries+=1
if %_tries% geq 90 goto ready
timeout /t 2 /nobreak >nul
goto waitloop
:ready
start "" "http://localhost:8501"

echo.
echo Polymer is running at http://localhost:8501
echo To stop it:  docker compose -f docker/docker-compose.yml down
echo.
pause
