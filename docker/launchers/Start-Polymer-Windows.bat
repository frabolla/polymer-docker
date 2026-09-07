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
timeout /t 8 /nobreak >nul
start "" "http://localhost:8501"

echo.
echo Polymer is running at http://localhost:8501
echo To stop it:  docker compose -f docker/docker-compose.yml down
echo.
pause
