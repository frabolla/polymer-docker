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

REM The interface can move the input/output folders; it saves the choice here.
set "COMPOSE_ENV="
if exist data\config\dirs.env (
  set "COMPOSE_ENV=--env-file data\config\dirs.env"
  echo Using custom input/output folders ^(data\config\dirs.env^).
)

REM Pre-download the base image. BuildKit only allows 10 s to reach Docker Hub
REM and fails the whole build on a slow network ("load metadata for
REM docker.io/mambaorg/micromamba ..."). `docker pull` waits longer and retries.
echo.
echo Checking the base image download (needs internet)...
set /a _p=0
:pullloop
set /a _p+=1
docker pull mambaorg/micromamba:1.5-jammy
if not errorlevel 1 goto pulldone
if %_p% geq 3 goto pullfailed
echo   Attempt %_p% failed. Waiting 15 seconds and retrying...
timeout /t 15 /nobreak >nul
goto pullloop
:pullfailed
echo.
echo Could not download the base image "mambaorg/micromamba:1.5-jammy".
echo This is almost always a temporary network problem:
echo   1. Make sure this computer is online.
echo   2. If you use a VPN or a company proxy, disconnect it (or allow
echo      access to hub.docker.com / registry-1.docker.io), then retry.
echo   3. Open Docker Desktop, wait until it shows "Engine running".
echo   4. Wait a minute and double-click this launcher again.
pause
exit /b 1
:pulldone

echo.
echo Building / starting. The FIRST run takes 10-20 minutes.
echo.
set /a _b=0
:buildloop
set /a _b+=1
docker compose %COMPOSE_ENV% -f docker/docker-compose.yml up -d --build
if not errorlevel 1 goto builddone
if %_b% geq 2 goto buildfailed
echo.
echo That attempt failed. Waiting 15 seconds and retrying once...
timeout /t 15 /nobreak >nul
goto buildloop
:buildfailed
echo.
echo Startup failed. Check the messages above. If it mentions "load metadata"
echo or a network / TLS error, see the network steps printed earlier.
pause
exit /b 1
:builddone

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
