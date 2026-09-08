#!/usr/bin/env bash
# Container startup: prepare the data folders, link the credentials and launch
# the Polymer web interface.
set -euo pipefail

echo "==> Preparing data folders in /data ..."
mkdir -p /data/input /data/output /data/auxdata/static /data/config \
         /data/ancillary /data/ancillary/METEO || true
chmod 700 /data/config 2>/dev/null || true

# Credentials (.netrc for NASA Earthdata, .cdsapirc for Copernicus CDS) are saved
# by the interface into /data/config and must be visible from $HOME.
export HOME=/data/config
for f in .netrc .cdsapirc; do
    if [ -f "/data/config/$f" ]; then
        chmod 600 "/data/config/$f" || true
        echo "==> Found credentials: $f"
    fi
done

# Make sure the Cython modules were compiled into the image.
if ! micromamba run -n polymer python -c "import polymer.polymer_main" 2>/dev/null; then
    echo "ERROR: Polymer's compiled modules are not available." >&2
    echo "       Rebuild the image with:  docker compose build --no-cache" >&2
    exit 1
fi

# Run from /app so Streamlit reads /app/.streamlit/config.toml (theme, etc.).
cd /app

echo "==> Interface available at http://localhost:8501"
exec micromamba run -n polymer streamlit run /app/streamlit_app.py \
    --server.port=8501 \
    --server.address=0.0.0.0
