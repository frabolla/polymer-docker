#!/usr/bin/env bash
# Double-click to start Polymer with its graphical interface (macOS / Linux).
# On macOS: if you see "unidentified developer", right-click > Open the first time.

set -e
cd "$(dirname "$0")/.."          # -> docker/ folder
REPO_ROOT="$(cd .. && pwd)"
cd "$REPO_ROOT"

echo "======================================================"
echo "  Polymer - starting the container"
echo "  Folder: $REPO_ROOT"
echo "======================================================"

if ! command -v docker >/dev/null 2>&1; then
  echo
  echo "Docker is not installed. Download it from:"
  echo "  https://www.docker.com/products/docker-desktop/"
  echo
  read -r -p "Press Enter to close." _
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo
  echo "Docker is installed but not running."
  echo "Open 'Docker Desktop', wait until it is ready, then try again."
  echo
  read -r -p "Press Enter to close." _
  exit 1
fi

mkdir -p data/input data/output data/auxdata data/ancillary data/config

echo
echo "Building / starting. The FIRST run takes 10-20 minutes."
echo
docker compose -f docker/docker-compose.yml up -d --build

echo
echo "Waiting for the interface to be ready..."
for _ in $(seq 1 60); do
  if curl -sf http://localhost:8501 >/dev/null 2>&1; then break; fi
  sleep 2
done

URL="http://localhost:8501"
echo "Opening $URL in the browser."
if command -v open >/dev/null 2>&1; then open "$URL"
elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL"
fi

echo
echo "Polymer is running. To stop it:"
echo "  docker compose -f docker/docker-compose.yml down"
echo
read -r -p "Press Enter to close this window (the container keeps running)." _
