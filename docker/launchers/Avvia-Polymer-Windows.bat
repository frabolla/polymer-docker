@echo off
REM Doppio clic per avviare Polymer con interfaccia grafica (Windows).
setlocal

cd /d "%~dp0\.."
for %%I in ("%cd%\..") do set "REPO_ROOT=%%~fI"
cd /d "%REPO_ROOT%"

echo ======================================================
echo   Polymer - avvio del container
echo   Cartella: %REPO_ROOT%
echo ======================================================
echo.

where docker >nul 2>&1
if errorlevel 1 (
  echo Docker non e' installato. Scaricalo da:
  echo   https://www.docker.com/products/docker-desktop/
  echo.
  pause
  exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
  echo Docker e' installato ma non e' in esecuzione.
  echo Apri "Docker Desktop", aspetta che sia pronto, poi riprova.
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
echo Costruzione/avvio in corso. La PRIMA volta richiede 10-20 minuti.
echo.
docker compose -f docker/docker-compose.yml up -d --build
if errorlevel 1 (
  echo.
  echo Avvio fallito. Controlla i messaggi qui sopra.
  pause
  exit /b 1
)

echo.
echo Attendo che l'interfaccia sia pronta...
timeout /t 8 /nobreak >nul
start "" "http://localhost:8501"

echo.
echo Polymer e' avviato su http://localhost:8501
echo Per fermarlo:  docker compose -f docker/docker-compose.yml down
echo.
pause
