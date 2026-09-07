#!/usr/bin/env bash
# Doppio clic per avviare Polymer con interfaccia grafica (macOS / Linux).
# Su macOS: se compare "autore non identificato", tasto destro > Apri la prima volta.

set -e
cd "$(dirname "$0")/.."          # -> cartella docker/
REPO_ROOT="$(cd .. && pwd)"
cd "$REPO_ROOT"

echo "======================================================"
echo "  Polymer — avvio del container"
echo "  Cartella: $REPO_ROOT"
echo "======================================================"

if ! command -v docker >/dev/null 2>&1; then
  echo
  echo "Docker non è installato. Scaricalo da:"
  echo "  https://www.docker.com/products/docker-desktop/"
  echo
  read -r -p "Premi Invio per chiudere." _
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo
  echo "Docker è installato ma non è in esecuzione."
  echo "Apri 'Docker Desktop', aspetta che sia pronto, poi riprova."
  echo
  read -r -p "Premi Invio per chiudere." _
  exit 1
fi

mkdir -p data/input data/output data/auxdata data/ancillary data/config

echo
echo "Costruzione/avvio in corso. La PRIMA volta richiede 10-20 minuti."
echo
docker compose -f docker/docker-compose.yml up -d --build

echo
echo "Attendo che l'interfaccia sia pronta..."
for _ in $(seq 1 60); do
  if curl -sf http://localhost:8501 >/dev/null 2>&1; then break; fi
  sleep 2
done

URL="http://localhost:8501"
echo "Apro $URL nel browser."
if command -v open >/dev/null 2>&1; then open "$URL"
elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL"
fi

echo
echo "Polymer è avviato. Per fermarlo:"
echo "  docker compose -f docker/docker-compose.yml down"
echo
read -r -p "Premi Invio per chiudere questa finestra (il container resta attivo)." _
