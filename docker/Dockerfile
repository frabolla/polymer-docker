# check=skip=FromPlatformFlagConstDisallowed
# Polymer + interfaccia grafica web, in un unico container.
#
# NOTA LICENZA: questa immagine NON deve essere ridistribuita (LICENCE.TXT, Sez. 2).
# Ogni utente la costruisce in locale a partire da questo repository.
#
# Build (dalla radice del repository):
#   docker compose -f docker/docker-compose.yml build
#
# L'ambiente Python e' ricreato dal lock conda-forge del repo (environment.yml).
# I moduli Cython di Polymer vengono compilati qui.  I dati ausiliari statici NON
# sono inclusi: si scaricano al primo avvio dentro un volume montato.

# environment.yml e' un lock conda per linux-64: l'immagine e' quindi solo amd64.
# Su Mac Apple Silicon viene eseguita in emulazione (piu' lenta, ma funziona).
FROM --platform=linux/amd64 mambaorg/micromamba:1.5-jammy

# --- pacchetti di sistema (git serve per le dipendenze pip da GitHub) ---
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
        git ca-certificates curl tini make build-essential \
    && rm -rf /var/lib/apt/lists/*

# --- ambiente conda "polymer" dal lock del repo ---
COPY environment.yml /tmp/environment.yml
# L'ambiente e' scelto con -n (la riga "name:" vuota del file viene ignorata).
RUN micromamba create -y -n polymer -f /tmp/environment.yml \
    && micromamba run -n polymer pip install --no-cache-dir "streamlit>=1.36" \
    && micromamba clean -y --all

ENV MAMBA_DEFAULT_ENV=polymer \
    ENV_NAME=polymer \
    PATH=/opt/conda/envs/polymer/bin:$PATH \
    PYTHONPATH=/opt/polymer \
    PYTHONUNBUFFERED=1

# I dati (input/output/auxdata/ancillary/config) vivono qui, su volumi montati.
# Le variabili e le cartelle devono esistere gia' in fase di build: importando
# polymer, params.py risolve queste directory tramite core.env.getdir, che SOLLEVA
# un'eccezione se la cartella non esiste.  DIR_DATA e' il fallback comune e va
# impostato anche lui (viene valutato sempre, pure quando le altre var sono definite).
ENV DIR_DATA=/data \
    DIR_POLYMER_AUXDATA=/data/auxdata/static \
    DIR_POLYMER_ANCILLARY=/data/ancillary \
    HOME=/data/config \
    OMP_NUM_THREADS=1
RUN mkdir -p /data/input /data/output /data/auxdata/static /data/ancillary /data/config

# --- sorgente di Polymer + compilazione dei moduli Cython ---
WORKDIR /opt/polymer
COPY polymer/     ./polymer/
COPY meson.build makefile pyproject.toml ./
COPY tools/       ./tools/
RUN micromamba run -n polymer make \
    && micromamba run -n polymer python -c "import polymer.polymer_main, polymer.water, polymer.clut, polymer.neldermead, polymer.polymer_minimizer; print('moduli Cython OK')"

# --- interfaccia grafica + licenza (mostrata nell'app) ---
COPY docker/app/  /app/
COPY LICENCE.TXT  /app/LICENCE.TXT
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8501
ENTRYPOINT ["/usr/bin/tini", "--", "/entrypoint.sh"]
