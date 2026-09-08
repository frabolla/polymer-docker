#!/usr/bin/env bash
# Double-click to start Polymer with its graphical interface (macOS / Linux).
#
# macOS, one-time unlock for a launcher taken from a downloaded ZIP (Gatekeeper
# quarantines it and drops its +x flag). In Terminal, once:
#   xattr -dr com.apple.quarantine  <project folder>
#   chmod +x  <project folder>/docker/launchers/Start-Polymer-macOS-Linux.command
# Then double-click. If still blocked: right-click > Open > Open, or
# System Settings > Privacy & Security > Open Anyway. Not needed with `git clone`.

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

# Let the interface show the folder paths as they are on this computer.
export POLYMER_HOST_DIR="$REPO_ROOT/data"

# The interface can move the input/output folders; it saves the choice here.
COMPOSE_ENV=""
if [ -f data/config/dirs.env ]; then
  COMPOSE_ENV="--env-file data/config/dirs.env"
  echo "Using custom input/output folders (data/config/dirs.env)."
fi

# Pre-download the base image. BuildKit only allows ~10 s to reach Docker Hub
# and fails the whole build on a slow network ("load metadata for
# docker.io/mambaorg/micromamba ..."). `docker pull` waits longer and retries.
echo
echo "Checking the base image download (needs internet)..."
set +e
pull_ok=0
for attempt in 1 2 3; do
  if docker pull mambaorg/micromamba:1.5-jammy; then pull_ok=1; break; fi
  echo "  Attempt $attempt failed. Waiting 15 s and retrying..."
  sleep 15
done
if [ "$pull_ok" -ne 1 ]; then
  echo
  echo 'Could not download the base image "mambaorg/micromamba:1.5-jammy".'
  echo "This is almost always a temporary network problem:"
  echo "  1. Make sure this computer is online."
  echo "  2. If you use a VPN or a company proxy, disconnect it (or allow"
  echo "     access to hub.docker.com / registry-1.docker.io), then retry."
  echo "  3. Open Docker Desktop, wait until it shows 'Engine running'."
  echo "  4. Wait a minute and double-click this launcher again."
  echo
  read -r -p "Press Enter to close." _
  exit 1
fi

echo
echo "Building / starting. The FIRST run takes 10-20 minutes."
echo
build_ok=0
for attempt in 1 2; do
  if docker compose $COMPOSE_ENV -f docker/docker-compose.yml up -d --build; then build_ok=1; break; fi
  echo
  echo "That attempt failed. Waiting 15 s and retrying once..."
  sleep 15
done
if [ "$build_ok" -ne 1 ]; then
  echo
  echo "Startup failed. Check the messages above. If it mentions 'load metadata'"
  echo "or a network / TLS error, see the network steps printed earlier."
  echo
  read -r -p "Press Enter to close." _
  exit 1
fi
set -e

echo
echo "Waiting for the interface to be ready..."
for _ in $(seq 1 90); do
  hs=$(docker inspect -f '{{.State.Health.Status}}' polymer-gui 2>/dev/null || echo "")
  if [ "$hs" = "healthy" ]; then break; fi
  if curl -sf http://localhost:8501/_stcore/health >/dev/null 2>&1; then break; fi
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
