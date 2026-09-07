#!/usr/bin/env bash
# Avvio del container: prepara le cartelle dati, collega le credenziali e lancia
# l'interfaccia web di Polymer.
set -euo pipefail

echo "==> Preparazione cartelle dati in /data ..."
mkdir -p /data/input /data/output /data/auxdata/static /data/ancillary /data/config

# Le credenziali (.netrc per NASA Earthdata, .cdsapirc per Copernicus CDS) sono
# salvate dall'interfaccia in /data/config e devono essere visibili in $HOME.
export HOME=/data/config
for f in .netrc .cdsapirc; do
    if [ -f "/data/config/$f" ]; then
        chmod 600 "/data/config/$f" || true
        echo "==> Credenziali trovate: $f"
    fi
done

# Verifica che i moduli Cython siano stati compilati nell'immagine.
if ! micromamba run -n polymer python -c "import polymer.polymer_main" 2>/dev/null; then
    echo "ERRORE: i moduli compilati di Polymer non sono disponibili." >&2
    echo "        Ricostruisci l'immagine con:  docker compose build --no-cache" >&2
    exit 1
fi

echo "==> Interfaccia disponibile su http://localhost:8501"
exec micromamba run -n polymer streamlit run /app/streamlit_app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false \
    --server.fileWatcherType=none
